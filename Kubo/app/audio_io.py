"""Bounded microphone/playback buffers. Headphones avoid acoustic feedback."""
from array import array
import queue
import threading

import sounddevice as sd

from protocol import RATE, BLOCK


class PCMBuffer:
    def __init__(self, max_bytes=RATE * 2 * 3):
        self.data = bytearray()
        self.lock = threading.Lock()
        self.max_bytes = max_bytes

    def put(self, data):
        with self.lock:
            if len(self.data) + len(data) > self.max_bytes:
                raise BufferError('Playback fell behind. Reconnect and check the audio device.')
            self.data.extend(data)

    def take(self, size):
        with self.lock:
            result = bytes(self.data[:size])
            del self.data[:size]
        return result + bytes(size - len(result))

    def try_put(self, data):
        with self.lock:
            if len(self.data) + len(data) > self.max_bytes:
                return False
            self.data.extend(data)
            return True

    def clear(self):
        with self.lock:
            self.data.clear()


class AudioIO:
    def __init__(self, input_device=None, output_device=None):
        self.input_device = input_device
        self.output_device = output_device
        self.microphone = queue.Queue(maxsize=25)
        self.playback = PCMBuffer()
        self.muted = threading.Event()
        self.suppress_output = threading.Event()
        self.stream = None
        self.level = 0.0
        self.failure = None

    def set_muted(self, muted):
        if muted:
            self.muted.set()
        else:
            self.muted.clear()
        while True:
            try:
                self.microphone.get_nowait()
            except queue.Empty:
                break

    def callback(self, incoming, outgoing, frames, timing, status):
        # Never perform network, UI, or blocking work on PortAudio's thread.
        # PortAudio can report a transient underrun while priming a device.
        # Bounded application queues below detect sustained transport backlog.
        pcm = bytes(frames * 2) if self.muted.is_set() else bytes(incoming)
        try:
            self.microphone.put_nowait(pcm)
        except queue.Full:
            self.failure = 'The connection cannot keep up with microphone audio. Reconnect.'
        played = self.playback.take(frames * 2)
        if self.suppress_output.is_set():
            played = bytes(len(played))
        outgoing[:] = played
        samples = array('h', played)
        self.level = min(1.0, (sum(x*x for x in samples) / max(1, len(samples))) ** .5 / 5000)

    def open(self):
        sd.check_input_settings(device=self.input_device, channels=1, dtype='int16', samplerate=RATE)
        sd.check_output_settings(device=self.output_device, channels=1, dtype='int16', samplerate=RATE)
        self.stream = sd.RawStream(
            device=(self.input_device, self.output_device), samplerate=RATE,
            blocksize=BLOCK, channels=1, dtype='int16', callback=self.callback,
        )

    def start(self):
        self.stream.start()

    def close(self):
        if self.stream:
            self.stream.abort()
            self.stream.close()
            self.stream = None
        self.playback.clear()
        self.level = 0.0
