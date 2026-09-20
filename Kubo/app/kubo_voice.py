"""Bounded RVC conversion outside GUI, socket and PortAudio threads."""
import os
import queue
import struct
import subprocess
import sys
import threading
from pathlib import Path

import paths
from kubo_worker import read_exact


class KuboVoice:
    def __init__(self, playback):
        self.playback = playback
        self.pending = queue.Queue(maxsize=600)  # At most 12 seconds in 20ms blocks.
        self.stopped = threading.Event()
        self.ready = threading.Event()
        self.failure = None
        self.process = None
        self.thread = None

    def start(self):
        if self.stopped.is_set():
            return
        executable = paths.get_voice_engine_executable()
        if not executable.is_file():
            if paths.is_frozen():
                raise FileNotFoundError('Không tìm thấy voice-engine/KuboVoice.exe trong bộ phát hành.')
            raise FileNotFoundError('Không tìm thấy môi trường RVC trong work/rvc-env.')
        if paths.is_frozen():
            cmd = [str(executable)]
        else:
            cmd = [str(executable), str(Path(__file__).with_name('kubo_worker.py'))]
        env = paths.clean_subprocess_env()
        log = paths.get_logs_dir() / 'chatbot-rvc.log'
        with log.open('wb') as error_log:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error_log, env=env,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            )
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if self.stopped.is_set():
            self.cancel()
        if not self.ready.wait(90):
            self.close()
            raise TimeoutError(f'Nạp giọng Kubo quá lâu. Kiểm tra nhật ký {log}.')
        if self.failure:
            self.close()
            raise RuntimeError(self.failure)

    def put(self, pcm):
        if len(pcm) % 2:
            raise ValueError('PCM16 không đủ mẫu.')
        if self.stopped.is_set():
            return
        for offset in range(0, len(pcm), 960):
            try:
                self.pending.put_nowait(pcm[offset:offset+960])
            except queue.Full:
                raise BufferError('RVC không theo kịp hội thoại. Hãy ngắt và kết nối lại.')

    def _run(self):
        try:
            if read_exact(self.process.stdout, 5) != b'READY':
                raise RuntimeError('RVC startup failed')
            self.ready.set()
            chunk = bytearray()
            while not self.stopped.is_set():
                try:
                    chunk.extend(self.pending.get(timeout=.25))
                    if len(chunk) < 72000:  # 1.5 seconds; flush short tails after idle.
                        continue
                except queue.Empty:
                    if not chunk:
                        continue
                self.process.stdin.write(struct.pack('<I', len(chunk))+chunk)
                self.process.stdin.flush()
                size = struct.unpack('<I', read_exact(self.process.stdout, 4))[0]
                if size != len(chunk):
                    raise ValueError('RVC output length mismatch')
                output = read_exact(self.process.stdout, size)
                chunk.clear()
                for offset in range(0, len(output), 960):
                    part = output[offset:offset+960]
                    while not self.stopped.is_set():
                        if self.playback.try_put(part):
                            break
                        self.stopped.wait(.01)
                    if self.stopped.is_set():
                        return
        except Exception:
            if not self.stopped.is_set():
                err_detail = ""
                try:
                    log_file = paths.get_logs_dir() / "chatbot-rvc.log"
                    if log_file.is_file():
                        lines = log_file.read_text(encoding='utf-8', errors='replace').strip().splitlines()
                        for line in reversed(lines[-15:]):
                            if any(k in line for k in ('FileNotFoundError', 'Error:', 'Không tìm thấy', 'Exception')):
                                err_detail = f"\nChi tiết: {line.strip()}"
                                break
                except Exception:
                    pass
                self.failure = f'Không thể chuyển giọng Kubo.{err_detail}\nXem nhật ký tại {paths.get_logs_dir() / "chatbot-rvc.log"}.'
        finally:
            self.ready.set()

    def _kill_process_tree(self):
        if not self.process:
            return
        pid = self.process.pid
        if self.process.poll() is None:
            if sys.platform == 'win32':
                try:
                    subprocess.run(
                        ['taskkill', '/F', '/T', '/PID', str(pid)],
                        capture_output=True,
                        timeout=3
                    )
                except Exception:
                    pass
            try:
                self.process.terminate()
            except Exception:
                pass
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    self.process.kill()
                    self.process.wait(timeout=2)
                except Exception:
                    pass

    def cancel(self):
        self.stopped.set()
        self._kill_process_tree()

    def close(self):
        self.cancel()
        if self.thread:
            self.thread.join(timeout=3)
        if self.process:
            try:
                self.process.stdin.close()
            except Exception:
                pass
            try:
                self.process.stdout.close()
            except Exception:
                pass
        self.playback.clear()

