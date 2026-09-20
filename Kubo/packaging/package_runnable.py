"""Assemble complete runnable distribution package in local-package/Kubo.

Supports clean path separation between repository root, dev source assets, and output package.
Can run in verification mode (--check-paths / --dry-run) without copying or modifying files on disk.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def log(msg: str):
    try:
        print(f"[RUNNABLE-PACK] {msg}", flush=True)
    except Exception:
        clean = msg.encode('ascii', 'replace').decode('ascii')
        print(f"[RUNNABLE-PACK] {clean}", flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def require_file(path: Path, description: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(
            f"Thiếu tệp bắt buộc [{description}]: {path}\n"
            f"Vui lòng kiểm tra lại cấu hình --dev-root hoặc xem hướng dẫn tại docs/ASSETS.md."
        )
    return path


def require_dir(path: Path, description: str) -> Path:
    if not path.is_dir():
        raise FileNotFoundError(
            f"Thiếu thư mục bắt buộc [{description}]: {path}\n"
            f"Vui lòng kiểm tra lại cấu hình --dev-root hoặc xem hướng dẫn tại docs/ASSETS.md."
        )
    return path


def get_git_revision_info(repo_dir: Path, override_commit: str | None = None) -> dict:
    """Detect git commit, branch, and dirty state dynamically without hardcoded guesses."""
    info = {
        "commit": "unknown",
        "short_commit": "unknown",
        "branch": "unknown",
        "is_dirty": False,
        "dirty_files": [],
        "revision_string": "unknown"
    }

    if override_commit:
        info["commit"] = override_commit
        info["short_commit"] = override_commit[:7]
        info["revision_string"] = info["short_commit"]
        return info

    env_commit = os.environ.get("KUBO_GIT_COMMIT")
    if env_commit:
        info["commit"] = env_commit
        info["short_commit"] = env_commit[:7]
        info["revision_string"] = info["short_commit"]
        return info

    if not (repo_dir / '.git').exists():
        return info

    try:
        res = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=True
        )
        info["commit"] = res.stdout.strip()
        info["short_commit"] = info["commit"][:7]
    except Exception as e:
        info["commit_error"] = str(e)

    try:
        res_b = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=True
        )
        info["branch"] = res_b.stdout.strip()
    except Exception:
        pass

    try:
        res_s = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=True
        )
        lines = [l for l in res_s.stdout.splitlines() if l.strip()]
        # Ignore local-package path changes from dirty detection
        dirty = [l for l in lines if 'local-package' not in l]
        if dirty:
            info["is_dirty"] = True
            info["dirty_files"] = dirty
            info["revision_string"] = f"{info['short_commit']}-dirty"
        else:
            info["is_dirty"] = False
            info["revision_string"] = info["short_commit"]
    except Exception:
        info["revision_string"] = info["short_commit"]

    return info


def copy_tree_fast(src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            s_file = Path(root) / f
            d_file = target_dir / f
            if not d_file.exists() or d_file.stat().st_mtime < s_file.stat().st_mtime or d_file.stat().st_size != s_file.stat().st_size:
                shutil.copy2(s_file, d_file)


def resolve_all_paths(args):
    """Resolve REPO_ROOT, DEV_ROOT, DEST_DIR, and derived component paths with clear separation."""
    script_file = Path(__file__).resolve()
    
    # 1. Detect REPO_ROOT
    if (script_file.parents[2] / '.git').is_dir() or script_file.parents[2].name == 'Kubo-github':
        repo_root = script_file.parents[2]
    elif (script_file.parents[1] / '.git').is_dir():
        repo_root = script_file.parents[1]
    else:
        repo_root = script_file.parents[2]

    # 2. Detect DEV_ROOT (source of models, work/rvc, virtual environments, release reference)
    if args.dev_root:
        dev_root = Path(args.dev_root).resolve()
    elif os.environ.get("KUBO_DEV_ROOT"):
        dev_root = Path(os.environ["KUBO_DEV_ROOT"]).resolve()
    elif (repo_root / 'work').is_dir() and (repo_root / 'Kubo' / 'app' / '.venv').is_dir():
        dev_root = repo_root
    elif (repo_root.parent / 'work').is_dir() and (repo_root.parent / 'Kubo' / 'app' / '.venv').is_dir():
        dev_root = repo_root.parent
    else:
        dev_root = repo_root.parent if repo_root.name == 'Kubo-github' else repo_root

    # 3. Detect DEST_DIR (Never duplicate Kubo-github/Kubo-github)
    if args.output_dir:
        dest_dir = Path(args.output_dir).resolve()
    elif os.environ.get("KUBO_LOCAL_PACKAGE"):
        dest_dir = Path(os.environ["KUBO_LOCAL_PACKAGE"]).resolve()
    elif os.environ.get("KUBO_OUTPUT_DIR"):
        dest_dir = Path(os.environ["KUBO_OUTPUT_DIR"]).resolve()
    elif repo_root.name == 'Kubo-github':
        dest_dir = repo_root / 'local-package' / 'Kubo'
    elif (repo_root / 'Kubo-github').is_dir():
        dest_dir = repo_root / 'Kubo-github' / 'local-package' / 'Kubo'
    else:
        dest_dir = repo_root / 'local-package' / 'Kubo'

    # 4. Component paths
    app_dir = (repo_root / 'Kubo' / 'app') if (repo_root / 'Kubo' / 'app').is_dir() else (dev_root / 'Kubo' / 'app')
    packaging_dir = (repo_root / 'Kubo' / 'packaging') if (repo_root / 'Kubo' / 'packaging').is_dir() else (dev_root / 'Kubo' / 'packaging')
    build_dir = (repo_root / 'Kubo' / 'build') if not args.staging_dir else (Path(args.staging_dir).resolve() / 'build')
    
    # Media assets & Persona: check repo_root first, fallback to dev_root
    assets_dir = (repo_root / 'Kubo' / 'app' / 'assets') if (repo_root / 'Kubo' / 'app' / 'assets' / 'kubo-atlas.png').is_file() else (dev_root / 'Kubo' / 'app' / 'assets')
    persona_file = (repo_root / 'Kubo' / 'app' / 'kubo-persona.md') if (repo_root / 'Kubo' / 'app' / 'kubo-persona.md').is_file() else (dev_root / 'Kubo' / 'app' / 'kubo-persona.md')

    release_ref = (dev_root / 'Kubo' / 'release' / 'Kubo') if (dev_root / 'Kubo' / 'release' / 'Kubo').is_dir() else (dev_root / 'release' / 'Kubo')
    voice_model_dir = dev_root / 'Kubo' / 'voice' / 'NagisaKubo' / 'Nagisa Kubo'
    work_dir = dev_root / 'work'
    rvc_dir = work_dir / 'rvc'
    rvc_env = work_dir / 'rvc-env'
    app_env = (dev_root / 'Kubo' / 'app' / '.venv') if (dev_root / 'Kubo' / 'app' / '.venv').is_dir() else (dev_root / '.venv')

    paths = {
        "REPO_ROOT": repo_root,
        "DEV_ROOT": dev_root,
        "DEST_DIR": dest_dir,
        "APP_DIR": app_dir,
        "ASSETS_DIR": assets_dir,
        "PERSONA_FILE": persona_file,
        "PACKAGING_DIR": packaging_dir,
        "BUILD_DIR": build_dir,
        "RELEASE_REF": release_ref,
        "VOICE_MODEL_DIR": voice_model_dir,
        "WORK_DIR": work_dir,
        "RVC_DIR": rvc_dir,
        "RVC_ENV": rvc_env,
        "APP_ENV": app_env,
    }
    return paths


def check_all_requirements(paths: dict, verbose: bool = True) -> list[str]:
    """Verify presence of all mandatory files and directories without making any changes."""
    missing = []
    
    checklist = [
        # (type, path, description)
        ("file", paths["APP_DIR"] / 'app.py', "Mã nguồn ứng dụng GUI app.py"),
        ("file", paths["APP_DIR"] / 'kubo_worker.py', "Mã nguồn worker kubo_worker.py"),
        ("file", paths["APP_DIR"] / 'paths.py', "Mô-đun định tuyến đường dẫn paths.py"),
        ("file", paths["PERSONA_FILE"], "Hồ sơ nhân vật kubo-persona.md"),
        ("file", paths["ASSETS_DIR"] / 'kubo-atlas.png', "Avatar Kubo atlas"),
        ("file", paths["ASSETS_DIR"] / 'angry.png', "Biểu cảm angry.png"),
        ("file", paths["ASSETS_DIR"] / 'kubo-plus6.wav', "Mẫu giọng kubo-plus6.wav"),
        ("file", paths["VOICE_MODEL_DIR"] / 'NagisaKubo_e300_s1500.pth', "Trọng số RVC Nagisa Kubo 300 epochs"),
        ("file", paths["VOICE_MODEL_DIR"] / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index', "Chỉ mục RVC Feature Index"),
        ("file", paths["RVC_DIR"] / 'assets' / 'rmvpe' / 'rmvpe.pt', "Mô hình nhận diện cao độ RMVPE"),
        ("file", paths["RVC_DIR"] / 'assets' / 'hubert_base' / 'pytorch_model.bin', "Trọng số HuBERT Base"),
        ("file", paths["RVC_DIR"] / 'assets' / 'hubert_base' / 'config.json', "Cấu hình HuBERT Base"),
        ("file", paths["RVC_DIR"] / 'ffmpeg.exe', "FFmpeg executable"),
        ("dir", paths["RELEASE_REF"] / 'voice-engine' / 'runtime', "Môi trường runtime Python cô lập"),
    ]

    if verbose:
        log("Kiểm tra sự hiện diện của các tài nguyên bắt buộc:")
    
    for kind, p, desc in checklist:
        exists = p.is_file() if kind == "file" else p.is_dir()
        status_mark = "OK" if exists else "MISSING"
        if verbose:
            log(f"  [{status_mark:7s}] {desc}: {p}")
        if not exists:
            missing.append(f"{desc} ({p})")

    return missing


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Đóng gói trọn vẹn bản phân phối cục bộ Nagisa Kubo (local-package/Kubo)."
    )
    parser.add_argument(
        "--dev-root",
        type=str,
        default=None,
        help="Thư mục gốc chứa môi trường dev (work/, release/, models, app .venv). Tự động nhận diện nếu để trống."
    )
    parser.add_argument(
        "--output-dir", "--dest-dir",
        dest="output_dir",
        type=str,
        default=None,
        help="Thư mục đích để xuất gói. Mặc định: <repo_root>/local-package/Kubo."
    )
    parser.add_argument(
        "--staging-dir",
        type=str,
        default=None,
        help="Thư mục staging tạm thời trước khi xuất gói."
    )
    parser.add_argument(
        "--clean", "--rebuild",
        action="store_true",
        help="Xóa build/dist và build/work trước đó, buộc PyInstaller biên dịch lại GUI Kubo.exe."
    )
    parser.add_argument(
        "--clean-dest",
        action="store_true",
        help="Xóa các tệp mồ côi trong thư mục đích nếu không thuộc gói phát hành."
    )
    parser.add_argument(
        "--git-commit",
        type=str,
        default=None,
        help="Ghi đè giá trị commit git nguồn ghi vào manifest.json."
    )
    parser.add_argument(
        "--check-paths", "--dry-run",
        dest="check_paths",
        action="store_true",
        help="Chỉ kiểm tra tính hợp lệ của đường dẫn, git info và tài nguyên bắt buộc; không ghi đĩa hay sao chép file."
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    paths = resolve_all_paths(args)
    git_info = get_git_revision_info(paths["REPO_ROOT"], args.git_commit)

    log("=" * 70)
    log("NAGISA KUBO - TRÌNH ĐÓNG GÓI BẢN PHÂN PHỐI CỤC BỘ (LOCAL PACKAGE)")
    log("=" * 70)
    log(f"Repository Root : {paths['REPO_ROOT']}")
    log(f"Dev Source Root : {paths['DEV_ROOT']}")
    log(f"Destination Dir : {paths['DEST_DIR']}")
    log(f"Git Commit      : {git_info['commit']} (branch: {git_info['branch']}, dirty: {git_info['is_dirty']})")
    log(f"Revision String : {git_info['revision_string']}")
    log("=" * 70)

    # 1. Validate paths & mandatory assets
    missing_assets = check_all_requirements(paths, verbose=True)
    if missing_assets:
        log("LỖI: Phát hiện thiếu tài nguyên bắt buộc:")
        for item in missing_assets:
            log(f"  - {item}")
        log("Xem hướng dẫn chuẩn bị tại docs/ASSETS.md hoặc truyền đúng --dev-root.")
        sys.exit(1)

    if args.check_paths:
        log("-" * 70)
        log("CHẾ ĐỘ KIỂM TRA ĐƯỜNG DẪN (--check-paths / --dry-run):")
        log("Tất cả đường dẫn nguồn, đích và tài nguyên bắt buộc đều CHÍNH XÁC VÀ ĐẦY ĐỦ.")
        log("Không có tệp nào được ghi hoặc sao chép trong lượt kiểm tra này.")
        log("-" * 70)
        sys.exit(0)

    # 2. Execution phase (only if not check-paths)
    start_time = time.monotonic()
    dest_dir = paths["DEST_DIR"]
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Build GUI Kubo.exe if requested or if missing or if source changed
    gui_dist = paths["BUILD_DIR"] / 'dist' / 'Kubo'
    exe_target = gui_dist / 'Kubo.exe'
    
    needs_build = args.clean or not exe_target.is_file()
    if not needs_build and exe_target.is_file():
        # Check if any .py file in APP_DIR is newer than Kubo.exe
        exe_mtime = exe_target.stat().st_mtime
        for py_file in paths["APP_DIR"].glob('*.py'):
            if py_file.stat().st_mtime > exe_mtime:
                log(f"Phát hiện mã nguồn mới hơn EXE ({py_file.name}). Yêu cầu biên dịch lại.")
                needs_build = True
                break

    if needs_build:
        log("Biên dịch GUI với PyInstaller...")
        if paths["BUILD_DIR"].is_dir():
            shutil.rmtree(paths["BUILD_DIR"] / 'work', ignore_errors=True)
            shutil.rmtree(paths["BUILD_DIR"] / 'dist', ignore_errors=True)

        spec_file = paths["PACKAGING_DIR"] / 'kubo_gui.spec'
        require_file(spec_file, "PyInstaller Spec file")
        python_exe = paths["APP_ENV"] / 'Scripts' / 'python.exe'
        require_file(python_exe, "Virtualenv Python compiler")

        cmd = [
            str(python_exe),
            '-m', 'PyInstaller',
            '--distpath', str(paths["BUILD_DIR"] / 'dist'),
            '--workpath', str(paths["BUILD_DIR"] / 'work'),
            '--clean', '-y',
            str(spec_file)
        ]
        subprocess.run(cmd, check=True, cwd=str(paths["PACKAGING_DIR"]))

    log("Sao chép Kubo.exe và _internal...")
    shutil.copy2(gui_dist / 'Kubo.exe', dest_dir / 'Kubo.exe')
    copy_tree_fast(gui_dist / '_internal', dest_dir / '_internal')

    # Copy data/
    log("Sao chép dữ liệu data (avatars, samples, persona, models)...")
    data_dir = dest_dir / 'data'
    
    # Avatars
    avatars_dir = data_dir / 'avatars'
    avatars_dir.mkdir(parents=True, exist_ok=True)
    for name in ('kubo-atlas.png', 'angry.png', 'mirai-atlas.png'):
        src_f = paths["ASSETS_DIR"] / name
        if src_f.is_file():
            shutil.copy2(src_f, avatars_dir / name)

    # Samples
    samples_dir = data_dir / 'samples'
    samples_dir.mkdir(parents=True, exist_ok=True)
    for name in ('kubo-plus6.wav', 'kubo-plus4.wav', 'kubo-plus5.wav'):
        src_f = paths["ASSETS_DIR"] / name
        if src_f.is_file():
            shutil.copy2(src_f, samples_dir / name)

    # Persona
    persona_dir = data_dir / 'persona'
    persona_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(require_file(paths["PERSONA_FILE"], "Persona markdown"), persona_dir / 'kubo-persona.md')

    # Models
    models_dir = data_dir / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(require_file(paths["VOICE_MODEL_DIR"] / 'NagisaKubo_e300_s1500.pth', "RVC PTH"), models_dir / 'NagisaKubo_e300_s1500.pth')
    shutil.copy2(require_file(paths["VOICE_MODEL_DIR"] / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index', "RVC Index"), models_dir / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index')
    shutil.copy2(require_file(paths["RVC_DIR"] / 'assets' / 'rmvpe' / 'rmvpe.pt', "RMVPE pt"), models_dir / 'rmvpe.pt')
    
    hubert_dest = models_dir / 'hubert_base'
    hubert_dest.mkdir(parents=True, exist_ok=True)
    for name in ('config.json', 'preprocessor_config.json', 'pytorch_model.bin'):
        src_f = paths["RVC_DIR"] / 'assets' / 'hubert_base' / name
        if src_f.is_file():
            shutil.copy2(src_f, hubert_dest / name)

    # Voice Engine
    log("Sao chép voice-engine...")
    ve_dir = dest_dir / 'voice-engine'
    ve_dir.mkdir(parents=True, exist_ok=True)

    # Launcher
    launcher_src = paths["PACKAGING_DIR"] / 'kubo_voice_launcher.c'
    launcher_exe = ve_dir / 'KuboVoice.exe'
    gcc_exe = None
    for cand in (r"C:\Program Files (x86)\cpeditor\mingw64\bin\gcc.exe", r"C:\MinGW\bin\gcc.exe", shutil.which("gcc")):
        if cand and Path(cand).is_file():
            gcc_exe = cand
            break
    if gcc_exe and launcher_src.is_file():
        log(f"Biên dịch native launcher với Job Object bằng {gcc_exe}...")
        cmd = [gcc_exe, '-O2', '-municode', '-o', str(launcher_exe), str(launcher_src)]
        subprocess.run(cmd, check=True)
    elif (paths["RELEASE_REF"] / 'voice-engine' / 'KuboVoice.exe').is_file():
        shutil.copy2(paths["RELEASE_REF"] / 'voice-engine' / 'KuboVoice.exe', launcher_exe)
    else:
        raise FileNotFoundError("Không tìm thấy compiler GCC lẫn KuboVoice.exe có sẵn.")

    # Bin (ffmpeg)
    bin_dir = ve_dir / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(require_file(paths["RVC_DIR"] / 'ffmpeg.exe', "ffmpeg.exe"), bin_dir / 'ffmpeg.exe')
    if (paths["RVC_DIR"] / 'ffprobe.exe').is_file():
        shutil.copy2(paths["RVC_DIR"] / 'ffprobe.exe', bin_dir / 'ffprobe.exe')

    # Configs
    copy_tree_fast(require_dir(paths["RVC_DIR"] / 'configs', "configs"), ve_dir / 'configs')

    # Engine source
    engine_dir = ve_dir / 'engine'
    engine_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(require_file(paths["APP_DIR"] / 'kubo_worker.py', "worker"), engine_dir / 'kubo_worker.py')
    shutil.copy2(require_file(paths["APP_DIR"] / 'paths.py', "paths"), engine_dir / 'paths.py')
    for d in ('infer', 'configs', 'i18n', 'tools'):
        src_d = paths["RVC_DIR"] / d
        if src_d.is_dir():
            copy_tree_fast(src_d, engine_dir / d)

    # Runtime
    log("Đồng bộ runtime cách ly...")
    runtime_src = require_dir(paths["RELEASE_REF"] / 'voice-engine' / 'runtime', "Release runtime")
    copy_tree_fast(runtime_src, ve_dir / 'runtime')

    # Licenses & Documentation
    log("Sao chép bản quyền và tài liệu...")
    lic_dir = dest_dir / 'licenses'
    lic_dir.mkdir(parents=True, exist_ok=True)
    
    if (paths["RELEASE_REF"] / 'licenses').is_dir():
        copy_tree_fast(paths["RELEASE_REF"] / 'licenses', lic_dir)
        
    credits_file = paths["REPO_ROOT"] / 'CREDITS.md'
    if not credits_file.is_file() and (paths["DEV_ROOT"] / 'CREDITS.md').is_file():
        credits_file = paths["DEV_ROOT"] / 'CREDITS.md'
    if credits_file.is_file():
        shutil.copy2(credits_file, lic_dir / 'CREDITS-VOICE.md')

    if (paths["RELEASE_REF"] / 'README.txt').is_file():
        shutil.copy2(paths["RELEASE_REF"] / 'README.txt', dest_dir / 'README.txt')

    # Manifest.json
    log("Tạo manifest.json với checksums và metadata Git động...")
    all_files = [f for f in dest_dir.rglob('*') if f.is_file() and f.name != 'manifest.json']
    total_bytes = sum(f.stat().st_size for f in all_files)

    manifest = {
        "name": "Nagisa Kubo Desktop Companion",
        "version": "1.0.0",
        "platform": "windows-x64",
        "source_git_commit": git_info["revision_string"],
        "git_info": {
            "commit": git_info["commit"],
            "short_commit": git_info["short_commit"],
            "branch": git_info["branch"],
            "is_dirty": git_info["is_dirty"],
            "uncommitted_files_count": len(git_info["dirty_files"])
        },
        "build_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "release_status": "development-machine-verified-runnable-package",
        "verified_hardware": "Windows 11 x64, NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM)",
        "package_type": "full-local-runnable-bundle",
        "bundle_metrics": {
            "total_files": len(all_files) + 1,
            "total_bytes": total_bytes,
            "total_size_gib": round(total_bytes / (1024**3), 2),
            "total_size_mib": round(total_bytes / (1024**2), 1)
        },
        "components": {
            "python": "3.12.14",
            "pyside6": "6.11.2",
            "pytorch": "2.7.1+cu118",
            "voice_conversion": "RVC v2 (Pitch +6, RMVPE, Nagisa Kubo 300 epochs)",
            "voice_worker_launcher": "KuboVoice.exe (Win32 Job Object Kill-on-Close)",
            "voice_credit": "Nagisa Kubo voice pack by Discord ID 416975678542446592 (Kuma6/Nagisa-Kubo on Hugging Face)"
        },
        "checksums_sha256": {
            "Kubo.exe": sha256_file(dest_dir / 'Kubo.exe'),
            "voice-engine/KuboVoice.exe": sha256_file(dest_dir / 'voice-engine' / 'KuboVoice.exe'),
            "data/models/NagisaKubo_e300_s1500.pth": sha256_file(dest_dir / 'data' / 'models' / 'NagisaKubo_e300_s1500.pth'),
            "data/models/added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index": sha256_file(dest_dir / 'data' / 'models' / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index'),
            "data/models/rmvpe.pt": sha256_file(dest_dir / 'data' / 'models' / 'rmvpe.pt'),
            "data/models/hubert_base/pytorch_model.bin": sha256_file(dest_dir / 'data' / 'models' / 'hubert_base' / 'pytorch_model.bin'),
        }
    }
    (dest_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    log("manifest.json đã được tạo thành công.")

    # Security Audit
    log("Rà soát bảo mật và rò rỉ secret trong các tệp văn bản...")
    leakages = []
    key_pattern = re.compile(r'(?:sk-proj-[a-zA-Z0-9_-]{20,}|OPENAI_API_KEY\s*=\s*[\'"][a-zA-Z0-9_-]{10,}[\'"])')
    for f in all_files:
        low = f.name.lower()
        if low == '.env' or (low.startswith('.env.') and not low.endswith('.example')):
            leakages.append(str(f))
        if f.suffix in ('.txt', '.json', '.md', '.py'):
            if 'site-packages' in f.parts:
                continue
            try:
                txt = f.read_text(encoding='utf-8', errors='ignore')
                if key_pattern.search(txt) and '.env.example' not in str(f):
                    leakages.append(f"{f} contains API key pattern")
            except Exception:
                pass
    if leakages:
        raise ValueError(f"Phát hiện rò rỉ bí mật: {leakages}")
    log("Kiểm toán bảo mật đạt: 0 secret được tìm thấy.")

    duration = time.monotonic() - start_time
    log("=" * 70)
    log(f"GÓI HOÀN TẤT TRONG {duration:.1f}s")
    log(f"Đích xuất gói: {dest_dir}")
    log(f"Tổng số tệp: {manifest['bundle_metrics']['total_files']}")
    log(f"Dung lượng  : {manifest['bundle_metrics']['total_size_gib']} GiB ({manifest['bundle_metrics']['total_size_mib']} MiB)")
    log("=" * 70)


if __name__ == '__main__':
    main()
