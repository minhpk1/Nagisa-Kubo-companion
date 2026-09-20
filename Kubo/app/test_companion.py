import asyncio
import base64
import json
import queue
import threading
import unittest

from audio_io import PCMBuffer
from live_client import run_session
from protocol import audio_event, start_event


class FakeAudio:
    def __init__(self):
        self.microphone = queue.Queue()
        self.microphone.put(b'\x01\x00' * 480)
        self.playback = PCMBuffer()
        self.failure = None
        self.started = False
        self.closed = False
        self.muted = False

    def start(self): self.started = True
    def close(self): self.closed = True
    def set_muted(self, value): self.muted = value


class Socket:
    def __init__(self, confirm_close=True):
        self.incoming = asyncio.Queue()
        self.sent = []
        self.confirm_close = confirm_close

    async def send(self, message):
        event = json.loads(message)
        self.sent.append(event)
        if event['type'] == 'session.close' and self.confirm_close:
            self.incoming.put_nowait(json.dumps({'type':'session.closed','usage':{}}))

    async def recv(self): return await self.incoming.get()

    def feed(self, event): self.incoming.put_nowait(json.dumps(event))


class SessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_handshake_audio_and_clean_close(self):
        ws, audio, stop, mute = Socket(), FakeAudio(), threading.Event(), threading.Event()
        events = []
        task = asyncio.create_task(run_session(ws,audio,stop,mute,lambda *x:events.append(x),{}))
        await asyncio.sleep(.03)
        self.assertEqual([e['type'] for e in ws.sent],['session.start'])
        self.assertFalse(audio.started)
        ws.feed({'type':'session.started'})
        ws.feed({'type':'session.output_audio.delta','delta':base64.b64encode(b'\x02\x00').decode()})
        await asyncio.sleep(.04)
        self.assertTrue(audio.started)
        self.assertEqual(audio.playback.take(4),b'\x02\x00\x00\x00')
        self.assertTrue(any(e['type']=='session.input_audio.append' for e in ws.sent))
        stop.set()
        await asyncio.wait_for(task,1)
        self.assertTrue(audio.closed)
        self.assertEqual(ws.sent[-1]['type'],'session.close')
        self.assertIn(('usage',{}),events)

    async def test_mute_sends_silence_and_control(self):
        ws, audio, stop, mute = Socket(), FakeAudio(), threading.Event(), threading.Event()
        mute.set()
        ws.feed({'type':'session.started'})
        task = asyncio.create_task(run_session(ws,audio,stop,mute,lambda *x:None,{}))
        await asyncio.sleep(.04)
        self.assertTrue(audio.muted)
        self.assertIn('session.input_audio.mute',[e['type'] for e in ws.sent])
        sent = next(e for e in ws.sent if e['type']=='session.input_audio.append')
        self.assertEqual(base64.b64decode(sent['audio']),bytes(960))
        mute.clear()
        await asyncio.sleep(.03)
        self.assertIn('session.input_audio.unmute',[e['type'] for e in ws.sent])
        stop.set(); await asyncio.wait_for(task,1)

    async def test_error_closes_session_and_surfaces_message(self):
        ws, audio = Socket(), FakeAudio()
        ws.feed({'type':'error','error':{'message':'Model access denied'}})
        with self.assertRaisesRegex(RuntimeError,'Model access denied'):
            await run_session(ws,audio,threading.Event(),threading.Event(),lambda *x:None,{})
        self.assertTrue(audio.closed)
        self.assertFalse(audio.started)
        self.assertEqual(ws.sent[-1]['type'],'session.start')

    async def test_missing_close_ack_times_out_and_releases_audio(self):
        ws, audio, stop = Socket(False), FakeAudio(), threading.Event()
        ws.feed({'type':'session.started'})
        stop.set()
        with self.assertRaisesRegex(TimeoutError,'close was not confirmed'):
            await run_session(ws,audio,stop,threading.Event(),lambda *x:None,{},close_timeout=.03)
        self.assertTrue(audio.closed)

    async def test_stop_during_startup_never_opens_microphone(self):
        ws, audio, stop = Socket(), FakeAudio(), threading.Event()
        stop.set()
        task = asyncio.create_task(run_session(ws,audio,stop,threading.Event(),lambda *x:None,{}))
        await asyncio.sleep(.03)
        self.assertEqual([e['type'] for e in ws.sent],['session.start'])
        ws.feed({'type':'session.started'})
        await asyncio.wait_for(task,1)
        self.assertFalse(audio.started)
        self.assertTrue(audio.closed)

    async def test_playback_overflow_ends_session(self):
        ws, audio = Socket(), FakeAudio()
        audio.playback = PCMBuffer(max_bytes=2)
        ws.feed({'type':'session.started'})
        ws.feed({'type':'session.output_audio.delta','delta':base64.b64encode(bytes(4)).decode()})
        with self.assertRaises(BufferError):
            await run_session(ws,audio,threading.Event(),threading.Event(),lambda *x:None,{})
        self.assertTrue(audio.closed)


class BufferTests(unittest.TestCase):
    def test_preserves_order_and_pads_underrun(self):
        buffer = PCMBuffer(8)
        buffer.put(b'ab'); buffer.put(b'cd')
        self.assertEqual(buffer.take(3),b'abc')
        self.assertEqual(buffer.take(3),b'd\x00\x00')

    def test_bounded_queue_does_not_silently_drop_speech(self):
        buffer = PCMBuffer(2)
        buffer.put(b'ab')
        with self.assertRaises(BufferError): buffer.put(b'cd')
        self.assertEqual(buffer.take(2),b'ab')

    def test_pcm_alignment_and_model(self):
        with self.assertRaises(ValueError): audio_event(b'a')
        self.assertEqual(start_event()['session']['model'],'gpt-live-1')


if __name__ == '__main__': unittest.main()
