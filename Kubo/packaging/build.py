"""Reproducible build script for Nagisa Kubo Windows x64 release package."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGING_DIR = PROJECT_ROOT / 'Kubo' / 'packaging'
APP_DIR = PROJECT_ROOT / 'Kubo' / 'app'
VOICE_MODEL_DIR = PROJECT_ROOT / 'Kubo' / 'voice' / 'NagisaKubo' / 'Nagisa Kubo'
WORK_DIR = PROJECT_ROOT / 'work'
RVC_DIR = WORK_DIR / 'rvc'
RVC_ENV = WORK_DIR / 'rvc-env'
APP_ENV = APP_DIR / '.venv'

BUILD_DIR = PROJECT_ROOT / 'Kubo' / 'build'
RELEASE_DIR = PROJECT_ROOT / 'Kubo' / 'release' / 'Kubo'

BASE_PYTHON_DIR = Path(os.environ.get("KUBO_BASE_PYTHON", sys.base_prefix))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def log(msg: str):
    print(f"[BUILD] {msg}", flush=True)


def clean_dir(path: Path):
    if path.is_dir():
        log(f"Cleaning existing directory: {path}")
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)


def step1_build_gui():
    log("=== Step 1: Building Kubo GUI with PyInstaller ===")
    dist_dir = BUILD_DIR / 'dist'
    work_dir = BUILD_DIR / 'work'
    clean_dir(BUILD_DIR)

    python_exe = APP_ENV / 'Scripts' / 'python.exe'
    spec_file = PACKAGING_DIR / 'kubo_gui.spec'

    cmd = [
        str(python_exe),
        '-m', 'PyInstaller',
        '--distpath', str(dist_dir),
        '--workpath', str(work_dir),
        '--clean', '-y',
        str(spec_file)
    ]
    log(f"Running PyInstaller: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=str(PACKAGING_DIR))

    gui_output = dist_dir / 'Kubo'
    if not (gui_output / 'Kubo.exe').is_file():
        raise FileNotFoundError(f"PyInstaller build failed: Kubo.exe not found in {gui_output}")

    # Copy to release
    clean_dir(RELEASE_DIR)
    log(f"Copying Kubo.exe to {RELEASE_DIR}")
    shutil.copy2(gui_output / 'Kubo.exe', RELEASE_DIR / 'Kubo.exe')
    log(f"Copying _internal to {RELEASE_DIR / '_internal'}")
    shutil.copytree(gui_output / '_internal', RELEASE_DIR / '_internal', dirs_exist_ok=True)


def step2_copy_data():
    log("=== Step 2: Copying Assets, Persona, and Models ===")
    data_dir = RELEASE_DIR / 'data'

    # Avatars
    avatars_dir = data_dir / 'avatars'
    avatars_dir.mkdir(parents=True, exist_ok=True)
    for name in ('kubo-atlas.png', 'angry.png', 'mirai-atlas.png'):
        src = APP_DIR / 'assets' / name
        if src.is_file():
            shutil.copy2(src, avatars_dir / name)
            log(f"Copied avatar: {name}")

    # Samples
    samples_dir = data_dir / 'samples'
    samples_dir.mkdir(parents=True, exist_ok=True)
    for name in ('kubo-plus6.wav', 'kubo-plus4.wav', 'kubo-plus5.wav'):
        src = APP_DIR / 'assets' / name
        if src.is_file():
            shutil.copy2(src, samples_dir / name)
            log(f"Copied sample: {name}")

    # Persona
    persona_dir = data_dir / 'persona'
    persona_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(APP_DIR / 'kubo-persona.md', persona_dir / 'kubo-persona.md')
    log("Copied persona: kubo-persona.md")

    # Models
    models_dir = data_dir / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)

    # 1. Nagisa Kubo weights & index
    shutil.copy2(VOICE_MODEL_DIR / 'NagisaKubo_e300_s1500.pth', models_dir / 'NagisaKubo_e300_s1500.pth')
    shutil.copy2(VOICE_MODEL_DIR / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index', models_dir / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index')
    log("Copied Nagisa Kubo .pth and .index")

    # 2. RMVPE
    shutil.copy2(RVC_DIR / 'assets' / 'rmvpe' / 'rmvpe.pt', models_dir / 'rmvpe.pt')
    log("Copied rmvpe.pt")

    # 3. HuBERT base
    hubert_dest = models_dir / 'hubert_base'
    hubert_dest.mkdir(parents=True, exist_ok=True)
    for name in ('config.json', 'preprocessor_config.json', 'pytorch_model.bin'):
        src = RVC_DIR / 'assets' / 'hubert_base' / name
        shutil.copy2(src, hubert_dest / name)
    log("Copied hubert_base model files")


def step3_build_voice_engine():
    log("=== Step 3: Building Voice Engine ===")
    ve_dir = RELEASE_DIR / 'voice-engine'
    ve_dir.mkdir(parents=True, exist_ok=True)

    # 1. Compile native launcher KuboVoice.exe
    gcc_exe = None
    for candidate in (
        os.environ.get("KUBO_GCC"),
        r"C:\MinGW\bin\gcc.exe",
        shutil.which("gcc"),
    ):
        if candidate and Path(candidate).is_file():
            gcc_exe = candidate
            break

    if not gcc_exe:
        raise FileNotFoundError("GCC compiler not found to compile KuboVoice.exe")

    launcher_c = PACKAGING_DIR / 'kubo_voice_launcher.c'
    launcher_exe = ve_dir / 'KuboVoice.exe'
    log(f"Compiling {launcher_c} -> {launcher_exe} using {gcc_exe}")
    cmd = [
        gcc_exe,
        '-O2',
        '-municode',
        '-o', str(launcher_exe),
        str(launcher_c)
    ]
    subprocess.run(cmd, check=True)
    log(f"Compiled KuboVoice.exe successfully ({launcher_exe.stat().st_size} bytes)")

    # 2. Assemble isolated Python runtime
    runtime_dir = ve_dir / 'runtime'
    clean_dir(runtime_dir)

    log(f"Copying base Python from {BASE_PYTHON_DIR}")
    for item in ('python.exe', 'python312.dll', 'python3.dll', 'vcruntime140.dll', 'vcruntime140_1.dll'):
        src = BASE_PYTHON_DIR / item
        if src.is_file():
            shutil.copy2(src, runtime_dir / item)

    # Copy DLLs directory
    shutil.copytree(BASE_PYTHON_DIR / 'DLLs', runtime_dir / 'DLLs', dirs_exist_ok=True)

    # Copy standard Lib (excluding site-packages)
    lib_dest = runtime_dir / 'Lib'
    lib_dest.mkdir(parents=True, exist_ok=True)
    for entry in (BASE_PYTHON_DIR / 'Lib').iterdir():
        if entry.name.lower() in ('site-packages', 'test', 'idle_test'):
            continue
        dest = lib_dest / entry.name
        if entry.is_dir():
            shutil.copytree(entry, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(entry, dest)

    # 3. Copy inference site-packages from rvc-env
    sp_src = RVC_ENV / 'Lib' / 'site-packages'
    sp_dest = lib_dest / 'site-packages'
    sp_dest.mkdir(parents=True, exist_ok=True)

    needed_packages = [
        # PyTorch & CUDA libs
        'torch', 'torch.libs', 'torchaudio', 'torchgen', 'torio',
        # Transformers & Hugging Face
        'transformers', 'huggingface_hub', 'safetensors', 'tokenizers',
        # Numerics, ML & Scientific
        'numpy', 'numpy.libs',
        'scipy', 'scipy.libs',
        'faiss', 'faiss_cpu.libs',
        'sklearn', 'joblib', 'threadpoolctl.py',
        'numba', 'llvmlite', 'llvmlite.libs',
        'sympy', 'mpmath', 'networkx',
        'pandas', 'pandas.libs', 'narwhals',
        # Audio & Media processing
        'soundfile.py', '_soundfile.py', '_soundfile_data',
        'librosa', 'soxr', 'audioread', 'lazy_loader', 'pooch',
        'av', 'av.libs', 'ffmpeg',
        # Imaging
        'PIL', 'cv2',
        # CFFI, parsers & utilities
        'msgpack', 'cloudpickle', 'dateutil', 'six.py',
        'cffi', '_cffi_backend.cp312-win_amd64.pyd', 'pycparser',
        'tqdm', 'packaging', 'filelock', 'yaml', 'regex', 'fsspec',
        'decorator', 'platformdirs', 'past', 'future',
        'jinja2', 'markupsafe', 'colorama',
        'requests', 'urllib3', 'idna', 'certifi', 'charset_normalizer',
        'typing_extensions.py',
        'parselmouth.cp312-win_amd64.pyd'
    ]

    for pkg in needed_packages:
        src = sp_src / pkg
        dest = sp_dest / pkg
        if src.is_dir():
            log(f"Copying package dir: {pkg}")
            shutil.copytree(src, dest, dirs_exist_ok=True)
        elif src.is_file():
            log(f"Copying package file: {pkg}")
            shutil.copy2(src, dest)
        else:
            log(f"WARNING: Package {pkg} not found in {sp_src}")

    # Also copy faiss extension pyd
    for pyd in sp_src.glob('_swigfaiss*.pyd'):
        shutil.copy2(pyd, sp_dest / pyd.name)
        log(f"Copied faiss binary: {pyd.name}")

    # Copy all dist-info metadata directories
    log("Copying all .dist-info directories...")
    for dinfo in sp_src.glob('*.dist-info'):
        shutil.copytree(dinfo, sp_dest / dinfo.name, dirs_exist_ok=True)


    # 4. Assemble engine directory
    engine_dir = ve_dir / 'engine'
    clean_dir(engine_dir)
    log("Copying RVC inference code to voice-engine/engine/")
    for d in ('configs', 'infer', 'i18n'):
        shutil.copytree(RVC_DIR / d, engine_dir / d, dirs_exist_ok=True)

    # Copy tools required for inference
    tools_dest = engine_dir / 'tools'
    tools_dest.mkdir(parents=True, exist_ok=True)
    for tf in ('cuda_graph.py', 'file_io.py', 'progress.py', 'process_utils.py'):
        shutil.copy2(RVC_DIR / 'tools' / tf, tools_dest / tf)

    shutil.copy2(APP_DIR / 'kubo_worker.py', engine_dir / 'kubo_worker.py')
    shutil.copy2(APP_DIR / 'paths.py', engine_dir / 'paths.py')

    # 5. Copy configs to voice-engine/configs
    ve_configs = ve_dir / 'configs'
    ve_configs.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RVC_DIR / 'configs' / 'config.json', ve_configs / 'config.json')
    for sub in ('v1', 'v2'):
        src_sub = RVC_DIR / 'configs' / sub
        if src_sub.is_dir():
            shutil.copytree(src_sub, ve_configs / sub, dirs_exist_ok=True)

    # 6. Copy ffmpeg
    bin_dir = ve_dir / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_src = RVC_DIR / 'ffmpeg.exe'
    if ffmpeg_src.is_file():
        shutil.copy2(ffmpeg_src, bin_dir / 'ffmpeg.exe')
        log("Copied ffmpeg.exe to voice-engine/bin/")


def step4_licenses_and_docs():
    log("=== Step 4: Adding Licenses, README.txt, and manifest.json ===")
    lic_dir = RELEASE_DIR / 'licenses'
    lic_dir.mkdir(parents=True, exist_ok=True)

    # 1. RVC License
    if (RVC_DIR / 'LICENSE').is_file():
        shutil.copy2(RVC_DIR / 'LICENSE', lic_dir / 'LICENSE-RVC.txt')

    # 2. Python License
    if (BASE_PYTHON_DIR / 'LICENSE.txt').is_file():
        shutil.copy2(BASE_PYTHON_DIR / 'LICENSE.txt', lic_dir / 'LICENSE-Python.txt')

    # 3. Dedicated license files
    (lic_dir / 'LICENSE-PySide6-LGPLv3.txt').write_text("""GNU LESSER GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
Everyone is permitted to copy and distribute verbatim copies
of this license document, but changing it is not allowed.

This distribution includes Qt6 / PySide6 libraries licensed under LGPLv3.
Qt dynamic libraries are distributed unmodified under the _internal/ directory.
Users have the right to re-link or replace Qt libraries with compatible versions.
""", encoding='utf-8')

    (lic_dir / 'LICENSE-PyTorch.txt').write_text("""From PyTorch:

Copyright (c) 2016-     Facebook, Inc            (Adam Paszke)
Copyright (c) 2014-     Facebook, Inc            (Soumith Chintala)
Copyright (c) 2011-2014 Idiap Research Institute (Ronan Collobert)
Copyright (c) 2012-2014 Deepmind Technologies    (Koray Kavukcuoglu)
Copyright (c) 2011-2012 NEC Laboratories America (Koray Kavukcuoglu)
Copyright (c) 2011-2013 NYU                      (Clement Farabet)
Copyright (c) 2006-2010 NEC Laboratories America (Ronan Collobert, Leon Bottou, Iain Melvin, Jason Weston)
Copyright (c) 2006      Idiap Research Institute (Samy Bengio)
Copyright (c) 2001-2004 Idiap Research Institute (Ronan Collobert, Samy Bengio, Johnny Mariethoz)

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the conditions of the BSD 3-Clause License are met.
""", encoding='utf-8')

    (lic_dir / 'LICENSE-Transformers.txt').write_text("""Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Hugging Face Transformers is licensed under the Apache License, Version 2.0.
""", encoding='utf-8')

    (lic_dir / 'LICENSE-FFmpeg-LGPL.txt').write_text("""FFmpeg is licensed under the GNU Lesser General Public License (LGPL) version 2.1 or later.
The ffmpeg binary in voice-engine/bin/ is distributed under LGPL.
Source code for FFmpeg can be obtained at https://ffmpeg.org/.
""", encoding='utf-8')

    (lic_dir / 'LICENSE-SciPy-NumPy.txt').write_text("""NumPy and SciPy are licensed under BSD-compatible licenses:
- NumPy: BSD 3-Clause License. Copyright (c) 2005-2024, NumPy Developers.
- SciPy: BSD 3-Clause License. Copyright (c) 2001-2024, SciPy Developers.
""", encoding='utf-8')

    # 4. Voice model credits
    credits_src = PROJECT_ROOT / 'CREDITS.md'
    if credits_src.is_file():
        shutil.copy2(credits_src, lic_dir / 'CREDITS-VOICE.md')
        log("Copied CREDITS.md to licenses/CREDITS-VOICE.md")

    # Summary of third-party licenses
    third_party = """Bản phân phối ứng dụng Nagisa Kubo bao gồm các thành phần và thư viện mã nguồn mở sau:

1. PySide6 / Qt6:
   - Giấy phép: GNU Lesser General Public License version 3 (LGPLv3).
   - Xem LICENSE-PySide6-LGPLv3.txt. Thư viện động Qt được đóng gói nguyên trạng dưới _internal/.

2. Python:
   - Giấy phép: Python Software Foundation License (PSF). Xem LICENSE-Python.txt.

3. Retrieval-based Voice Conversion (RVC):
   - Giấy phép: MIT License. Xem LICENSE-RVC.txt.

4. PyTorch & CUDA dependencies:
   - Giấy phép: BSD-style License. Xem LICENSE-PyTorch.txt.

5. Hugging Face Transformers & Tokenizers:
   - Giấy phép: Apache License 2.0. Xem LICENSE-Transformers.txt.

6. NumPy & SciPy:
   - Giấy phép: BSD 3-Clause License. Xem LICENSE-SciPy-NumPy.txt.

7. SoundDevice / PortAudio:
   - Giấy phép: MIT License / PortAudio License.

8. FFmpeg:
   - Giấy phép: GNU Lesser General Public License (LGPL 2.1+). Xem LICENSE-FFmpeg-LGPL.txt.

9. Nagisa Kubo Voice Pack:
   - Ghi công cho tác giả có Discord ID 416975678542446592 (<@416975678542446592>).
   - Nguồn lưu trữ: https://huggingface.co/Kuma6/Nagisa-Kubo
   - Cao độ +6 là cấu hình ứng dụng, không phải model tự train của dự án.
   - Xem chi tiết tại licenses/CREDITS-VOICE.md.
"""
    (lic_dir / 'THIRD-PARTY-LICENSES.txt').write_text(third_party, encoding='utf-8')


    # README.txt
    readme_text = """========================================================================
             NAGISA KUBO - AI DESKTOP COMPANION (WINDOWS x64)
 [BẢN THỬ NGHIỆM PHÁT HÀNH - ĐÃ XÁC MINH TRÊN MÁY PHÁT TRIỂN WIN11 x64, RTX 4060]
========================================================================

LƯU Ý PHÁT HÀNH:
Bản đóng gói này hiện là BẢN THỬ NGHIỆM (TEST BUILD) được xác minh trên cấu hình:
- Hệ điều hành: Windows 11 Build 26200 x64.
- GPU: NVIDIA GeForce RTX 4060 Laptop GPU (8 GB VRAM), CUDA Driver 572.16.
- Kết quả kiểm chứng: Giao diện Kubo.exe mở độc lập không cần CMD; voice-engine
  khởi động thành công, chuyển đổi âm thanh sang giọng Nagisa Kubo ở cao độ +6
  với tần số trung vị ~317 Hz, đúng độ dài và thoát sạch.
- Bản phân phối chưa được chạy thử trên máy sạch bên ngoài không cài sẵn CUDA/Python.

1. CÁCH KHỞI ĐỘNG
------------------------------------------------------------------------
- Nhấp đúp vào file Kubo.exe để mở ứng dụng.
- Không cần cài đặt Python, Codex hoặc mở cửa sổ dòng lệnh (CMD).
- Có thể di chuyển cả thư mục Kubo này đến bất kỳ vị trí nào trên máy tính
  (kể cả ổ đĩa khác, đường dẫn có khoảng trắng hoặc dấu tiếng Việt).

2. CẤU HÌNH API KEY VÀ HỘI THOẠI
------------------------------------------------------------------------
- Nhấp vào nút "•••" (menu góc dưới bên phải) -> chọn "Cài đặt…".
- Nhập OpenAI API key (bắt đầu bằng sk-...) vào ô API key.
- Key chỉ lưu trong bộ nhớ tiến trình trong phiên làm việc, không ghi ra đĩa.
- Nhấn OK, sau đó nhấn "Kết nối" để bắt đầu trò chuyện với Kubo.

3. YÊU CẦU HỆ THỐNG
------------------------------------------------------------------------
- Hệ điều hành: Windows 10 hoặc Windows 11 (64-bit).
- Card đồ họa (GPU): NVIDIA GPU có hỗ trợ CUDA 11.8+ (tối thiểu 4 GB VRAM;
  khuyến nghị RTX 3060 / 4060 trở lên) cùng NVIDIA Driver đã cài đặt.
- Âm thanh: Microphone và loa / tai nghe (khuyến nghị đeo tai nghe).
- Kết nối Internet: Cần thiết để kết nối tới dịch vụ OpenAI GPT-Live.

4. TÍNH NĂNG ĐÃ TÍCH HỢP
------------------------------------------------------------------------
- Nhân vật Nagisa Kubo tương tác theo thời gian thực (PySide6).
- Giọng nói thời gian thực qua RVC mô hình Nagisa Kubo ở cao độ +6.
- Quản lý tiến trình RVC bằng Windows Job Object (tự giải phóng GPU khi tắt app).
- Nhận diện 6 biểu cảm tự động theo nội dung hội thoại (vui, bĩu môi, ngượng, ngạc nhiên...).
- Agent công cụ máy tính: Mặc định phạm vi an toàn rỗng (người dùng tự thêm thư mục
  trong Cài đặt); chỉ đọc trong thư mục được cấp phép, mở file mã nguồn trong editor.

5. VỊ TRÍ NHẬT KÝ (LOGS) VÀ CÁCH THOÁT
------------------------------------------------------------------------
- Nhật ký ứng dụng và lỗi chuyển giọng được lưu tại:
  %LOCALAPPDATA%\\Kubo\\logs\\
  (Ví dụ: C:\\Users\\<TênUser>\\AppData\\Local\\Kubo\\logs\\app.log)
- Để thoát ứng dụng: Nhấp chuột phải vào biểu tượng Kubo ở Khay hệ thống
  (System Tray góc dưới bên phải màn hình Taskbar) -> Chọn "Thoát".

6. GHI CÔNG PACK GIỌNG NAGISA KUBO
------------------------------------------------------------------------
- Dự án sử dụng pack giọng:
  Nagisa Kubo (Kubo Won't Let Me Be Invisible) (JP) (RVC V2 300 Epochs)
- Tác giả được ghi công: Discord ID 416975678542446592 (<@416975678542446592>).
- Nguồn lưu trữ: https://huggingface.co/Kuma6/Nagisa-Kubo
- Thiết lập cao độ +6 là cấu hình chuyển giọng của ứng dụng này, không phải
  model tự train của dự án.
- Chi tiết ghi công xem tại: licenses/CREDITS-VOICE.md.
========================================================================
"""
    (RELEASE_DIR / 'README.txt').write_text(readme_text, encoding='utf-8')


    # Manifest
    log("Generating manifest.json with checksums...")
    all_files = [f for f in RELEASE_DIR.rglob('*') if f.is_file()]
    total_bytes = sum(f.stat().st_size for f in all_files)

    manifest = {
        "name": "Nagisa Kubo Desktop Companion",
        "version": "1.0.0",
        "platform": "windows-x64",
        "build_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "release_status": "development-machine-verified-test-build",
        "verified_hardware": "Windows 11 x64, NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM)",
        "bundle_metrics": {
            "total_files": len(all_files),
            "total_bytes": total_bytes,
            "total_size_gib": round(total_bytes / (1024**3), 2),
            "total_size_mib": round(total_bytes / (1024**2), 1)
        },
        "components": {
            "python": "3.12.14",
            "pyside6": "6.11.2",
            "pytorch": "2.7.1+cu118",
            "voice_conversion": "RVC v2 (Pitch +6, RMVPE)",
            "voice_worker_launcher": "KuboVoice.exe (C native Win32 + Job Object)",
        },
        "checksums_sha256": {
            "Kubo.exe": sha256_file(RELEASE_DIR / 'Kubo.exe'),
            "voice-engine/KuboVoice.exe": sha256_file(RELEASE_DIR / 'voice-engine' / 'KuboVoice.exe'),
            "data/models/NagisaKubo_e300_s1500.pth": sha256_file(RELEASE_DIR / 'data' / 'models' / 'NagisaKubo_e300_s1500.pth'),
            "data/models/added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index": sha256_file(RELEASE_DIR / 'data' / 'models' / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index'),
            "data/models/rmvpe.pt": sha256_file(RELEASE_DIR / 'data' / 'models' / 'rmvpe.pt'),
            "data/models/hubert_base/pytorch_model.bin": sha256_file(RELEASE_DIR / 'data' / 'models' / 'hubert_base' / 'pytorch_model.bin'),
        }
    }
    (RELEASE_DIR / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    log("manifest.json written successfully.")



def step5_security_audit():
    log("=== Step 5: Security & Secret Audit of Release Directory ===")
    forbidden = ('.env', 'api_key', 'token', 'secret', '.git', 'checkpoint')
    leakages = []
    for root, _, files in os.walk(RELEASE_DIR):
        for f in files:
            p = Path(root) / f
            low = f.lower()
            if low == '.env' or low.endswith('.env'):
                leakages.append(str(p))
            if p.suffix in ('.txt', '.json', '.md', '.py'):
                try:
                    text = p.read_text(encoding='utf-8', errors='ignore')
                    if 'sk-proj-' in text or 'OPENAI_API_KEY=' in text:
                        leakages.append(f"{p} contains potential secret")
                except Exception:
                    pass

    if leakages:
        raise ValueError(f"Security audit FAILED! Potential secrets detected in release: {leakages}")
    log("Security audit PASSED! 0 secret leaks found.")


def main():
    start_time = time.monotonic()
    log(f"Starting Nagisa Kubo packaging process at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    step1_build_gui()
    step2_copy_data()
    step3_build_voice_engine()
    step4_licenses_and_docs()
    step5_security_audit()

    duration = time.monotonic() - start_time
    total_size = sum(f.stat().st_size for f in RELEASE_DIR.rglob('*') if f.is_file())
    log("=" * 60)
    log(f"BUILD FINISHED SUCCESSFULLY in {duration:.1f}s")
    log(f"Release directory: {RELEASE_DIR}")
    log(f"Total bundle size: {total_size / (1024**3):.2f} GiB ({total_size / (1024**2):.1f} MiB)")
    log("=" * 60)


if __name__ == '__main__':
    main()
