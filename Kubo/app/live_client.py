"""Live socket runs off the GUI thread; stop and mute are thread-safe."""
import asyncio
import base64
import json
import queue
import threading
import time

from PySide6.QtCore import QThread, Signal
from websockets.asyncio.client import connect

from audio_io import AudioIO
from protocol import URL, audio_event, start_event


async def run_session(ws, audio, stop, muted, emit, config, close_timeout=10, converter=None, agent=None):
    """Own all writes and reads on one loop; keep receiving during finalization."""
    await ws.send(json.dumps(start_event(**config)))
    ready = False
    closing = False
    sent_mute = False
    deadline = time.monotonic() + 20
    receiver = asyncio.create_task(ws.recv())
    failure = None
    try:
        while True:
            now = time.monotonic()
            if converter and converter.failure:
                failure = RuntimeError(converter.failure)
            if failure and not ready:
                raise failure
            if ready and (stop.is_set() or failure) and not closing:
                if agent:
                    await agent.close()
                audio.close()
                await ws.send(json.dumps({'type': 'session.close'}))
                closing = True
                deadline = now + close_timeout
                emit('state', 'Closing')
            if (not ready or closing) and now > deadline:
                raise TimeoutError('Session close was not confirmed.' if closing else 'Session startup timed out.')
            done, _ = await asyncio.wait({receiver}, timeout=.01)
            if done:
                event = json.loads(receiver.result())
                kind = event.get('type', '')
                if kind == 'session.started' and not closing:
                    ready = True
                    audio.set_muted(muted.is_set())
                    if not stop.is_set():
                        try:
                            audio.start()
                        except Exception as exc:
                            failure = RuntimeError(f'Cannot start microphone: {exc}')
                        if not failure:
                            emit('state', 'Connected')
                elif kind == 'response.event' and agent and not closing and not stop.is_set():
                    agent.event(event)
                elif kind == 'session.output_audio.delta' and not closing:
                    try:
                        (converter or audio.playback).put(base64.b64decode(event['delta'], validate=True))
                    except (ValueError, BufferError) as exc:
                        failure = exc
                elif kind in ('session.input_transcript.delta', 'session.output_transcript.delta'):
                    emit('transcript', ('You' if 'input_' in kind else 'Kubo', event.get('delta', '')))
                elif kind == 'error':
                    failure = RuntimeError(event.get('error', {}).get('message', 'Live API rejected the request.'))
                elif kind == 'session.closed':
                    emit('usage', event.get('usage', {}))
                    if failure:
                        raise failure
                    return
                receiver = asyncio.create_task(ws.recv())
            if ready and not closing and not failure and not stop.is_set():
                if agent:
                    while not agent.outbox.empty():
                        await ws.send(json.dumps(agent.outbox.get_nowait()))
                current_mute = muted.is_set()
                if current_mute != sent_mute:
                    audio.set_muted(current_mute)
                    await ws.send(json.dumps({'type': 'session.input_audio.' + ('mute' if current_mute else 'unmute')}))
                    sent_mute = current_mute
                if audio.failure:
                    failure = RuntimeError(audio.failure)
                    continue
                # Drain at most one 20ms block per loop; callback supplies the clock.
                try:
                    pcm = audio.microphone.get_nowait()
                except queue.Empty:
                    continue
                if current_mute:
                    pcm = bytes(len(pcm))
                await ws.send(json.dumps(audio_event(pcm)))
    finally:
        if agent:
            await agent.close()
        receiver.cancel()
        await asyncio.gather(receiver, return_exceptions=True)
        audio.close()


class LiveWorker(QThread):
    state = Signal(str)
    transcript = Signal(str, str)
    error = Signal(str)
    usage = Signal(object)
    tool_status = Signal(str)
    tool_ui = Signal(object)

    def __init__(self, key, config, input_device=None, output_device=None, roots=None, apps=None, editor=None):
        super().__init__()
        self.key = key
        self.config = config
        self.stop_event = threading.Event()
        self.mute_event = threading.Event()
        self.audio = AudioIO(input_device, output_device)
        self.converter = None
        self.roots = roots
        self.apps, self.editor = apps, editor
        self.agent = None

    def stop(self):
        self.stop_event.set()
        if self.agent:
            self.agent.tools.stop.set()
        self.audio.set_muted(True)
        if self.converter:
            self.converter.cancel()

    def mute(self, value):
        self.mute_event.set() if value else self.mute_event.clear()
        self.audio.set_muted(value)

    def emit_event(self, kind, value):
        if kind == 'transcript':
            self.transcript.emit(*value)
        else:
            getattr(self, kind).emit(value)

    async def serve(self):
        from kubo_voice import KuboVoice
        from agent_tools import LocalTools
        from agent_session import AgentSession
        agent = AgentSession(LocalTools(self.roots, ui=self.tool_ui.emit, apps=self.apps, editor=self.editor), self.tool_status.emit) if self.config.get('agent_enabled') else None
        self.agent = agent
        self.converter = KuboVoice(self.audio.playback)
        try:
            self.state.emit('Đang nạp giọng Kubo +6…')
            await asyncio.to_thread(self.converter.start)
            if self.stop_event.is_set():
                return
            self.audio.open()  # Validate devices before creating a billable session.
            async with connect(URL, additional_headers={'Authorization': f'Bearer {self.key}'},
                               open_timeout=10, close_timeout=3, max_size=4*1024*1024,
                               ping_interval=20, ping_timeout=20) as ws:
                await run_session(ws, self.audio, self.stop_event, self.mute_event,
                                  self.emit_event, self.config, converter=self.converter, agent=agent)
        finally:
            await asyncio.to_thread(self.converter.close)
            self.audio.close()

    def run(self):
        try:
            asyncio.run(self.serve())
        except Exception as exc:
            # Never expose an API key in a displayed exception.
            if not self.stop_event.is_set():
                self.error.emit(str(exc).replace(self.key, '[redacted]'))
        finally:
            self.key = ''



