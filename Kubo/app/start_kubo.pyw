"""Console-free entry point, with persistent startup diagnostics."""
import ctypes
import os
import sys
import traceback
from pathlib import Path

import paths

LOGS = paths.get_logs_dir()
LOGS.mkdir(parents=True, exist_ok=True)
os.chdir(paths.get_bundle_dir())

if __name__ == '__main__':
    log_file = LOGS / 'app.log'
    with log_file.open('a', encoding='utf-8', buffering=1) as log:
        sys.stdout = sys.stderr = log
        try:
            from app import main
            main()
        except SystemExit:
            raise
        except Exception:
            traceback.print_exc()
            ctypes.windll.user32.MessageBoxW(None,
                f'Không mở được Kubo. Xem nhật ký {log_file} để biết lỗi.',
                'Kubo — lỗi khởi động', 0x10)
            sys.exit(1)
