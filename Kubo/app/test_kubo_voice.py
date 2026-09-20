import asyncio
import base64
import threading
import unittest
from audio_io import PCMBuffer
from kubo_voice import KuboVoice
from live_client import run_session
from test_companion import Socket, FakeAudio


class ConversionTests(unittest.IsolatedAsyncioTestCase):
    async def test_original_voice_is_never_played_when_converter_enabled(self):
        class Converter:
            failure = None
            def __init__(self): self.received = []
            def put(self, pcm): self.received.append(pcm)
        converter = Converter()
        ws, audio, stop = Socket(), FakeAudio(), threading.Event()
        ws.feed({'type':'session.started'})
        ws.feed({'type':'session.output_audio.delta', 'delta':base64.b64encode(b'\x02\x00').decode()})
        task = asyncio.create_task(run_session(ws,audio,stop,threading.Event(),lambda *x:None,{},converter=converter))
        await asyncio.sleep(.06)
        self.assertEqual(converter.received, [b'\x02\x00'])
        self.assertEqual(audio.playback.take(2), b'\x00\x00')
        stop.set()
        await asyncio.wait_for(task, 1)

    async def test_conversion_failure_closes_session(self):
        class Converter:
            failure = None
            def put(self, pcm): self.failure = 'conversion failed'
        ws, audio = Socket(), FakeAudio()
        ws.feed({'type':'session.started'})
        ws.feed({'type':'session.output_audio.delta','delta':base64.b64encode(bytes(4)).decode()})
        with self.assertRaisesRegex(RuntimeError, 'conversion failed'):
            await asyncio.wait_for(run_session(ws,audio,threading.Event(),threading.Event(),lambda *x:None,{},converter=Converter()),1)
        self.assertTrue(audio.closed)


class QueueTests(unittest.TestCase):
    def test_large_delta_is_split_and_bounded(self):
        converter = KuboVoice(PCMBuffer())
        converter.put(bytes(48000))
        self.assertEqual(converter.pending.qsize(), 50)
        with self.assertRaises(BufferError): converter.put(bytes(960*601))
        self.assertEqual(converter.pending.qsize(), 600)
        converter.close()
        converter.put(bytes(960))
        self.assertEqual(converter.pending.qsize(), 600)

    def test_playback_backpressure_preserves_data(self):
        buffer = PCMBuffer(4)
        self.assertTrue(buffer.try_put(b'abcd'))
        self.assertFalse(buffer.try_put(b'ef'))
        self.assertEqual(buffer.take(2), b'ab')
        self.assertTrue(buffer.try_put(b'ef'))
        self.assertEqual(buffer.take(4), b'cdef')
