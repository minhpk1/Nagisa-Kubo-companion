"""Assemble complete runnable distribution package in Kubo-github/local-package/Kubo."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / 'Kubo' / 'app'
PACKAGING_DIR = PROJECT_ROOT / 'Kubo' / 'packaging'
BUILD_DIR = PROJECT_ROOT / 'Kubo' / 'build'
RELEASE_REF = PROJECT_ROOT / 'Kubo' / 'release' / 'Kubo'
VOICE_MODEL_DIR = PROJECT_ROOT / 'Kubo' / 'voice' / 'NagisaKubo' / 'Nagisa Kubo'
WORK_DIR = PROJECT_ROOT / 'work'
RVC_DIR = WORK_DIR / 'rvc'
RVC_ENV = WORK_DIR / 'rvc-env'
APP_ENV = APP_DIR / '.venv'

DEST_DIR = Path(os.environ.get("KUBO_LOCAL_PACKAGE", PROJECT_ROOT / 'Kubo-github' / 'local-package' / 'Kubo')).resolve()
GIT_COMMIT = "0c4a8ad"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def log(msg: str):
    print(f"[RUNNABLE-PACK] {msg}", flush=True)


def copy_file_if_exists(src: Path, dst: Path):
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    return False


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


def main():
    start_time = time.monotonic()
    log(f"Assembling runnable package into: {DEST_DIR}")
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Kubo.exe & _internal/
    gui_dist = BUILD_DIR / 'dist' / 'Kubo'
    if not (gui_dist / 'Kubo.exe').is_file():
        log("Building GUI with PyInstaller...")
        spec_file = PACKAGING_DIR / 'kubo_gui.spec'
        cmd = [
            str(APP_ENV / 'Scripts' / 'python.exe'),
            '-m', 'PyInstaller',
            '--distpath', str(BUILD_DIR / 'dist'),
            '--workpath', str(BUILD_DIR / 'work'),
            '--clean', '-y',
            str(spec_file)
        ]
        subprocess.run(cmd, check=True, cwd=str(PACKAGING_DIR))

    log("Copying Kubo.exe and _internal...")
    shutil.copy2(gui_dist / 'Kubo.exe', DEST_DIR / 'Kubo.exe')
    copy_tree_fast(gui_dist / '_internal', DEST_DIR / '_internal')

    # 2. Data directory: avatars, samples, persona, models
    log("Copying data directory (avatars, samples, persona, models)...")
    data_dir = DEST_DIR / 'data'
    
    # Avatars
    avatars_dir = data_dir / 'avatars'
    avatars_dir.mkdir(parents=True, exist_ok=True)
    for name in ('kubo-atlas.png', 'angry.png', 'mirai-atlas.png'):
        copy_file_if_exists(APP_DIR / 'assets' / name, avatars_dir / name)
        
    # Samples
    samples_dir = data_dir / 'samples'
    samples_dir.mkdir(parents=True, exist_ok=True)
    for name in ('kubo-plus6.wav', 'kubo-plus4.wav', 'kubo-plus5.wav'):
        copy_file_if_exists(APP_DIR / 'assets' / name, samples_dir / name)
        
    # Persona
    persona_dir = data_dir / 'persona'
    persona_dir.mkdir(parents=True, exist_ok=True)
    copy_file_if_exists(APP_DIR / 'kubo-persona.md', persona_dir / 'kubo-persona.md')

    # Models
    models_dir = data_dir / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)
    copy_file_if_exists(VOICE_MODEL_DIR / 'NagisaKubo_e300_s1500.pth', models_dir / 'NagisaKubo_e300_s1500.pth')
    copy_file_if_exists(VOICE_MODEL_DIR / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index', models_dir / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index')
    copy_file_if_exists(RVC_DIR / 'assets' / 'rmvpe' / 'rmvpe.pt', models_dir / 'rmvpe.pt')
    
    hubert_dest = models_dir / 'hubert_base'
    hubert_dest.mkdir(parents=True, exist_ok=True)
    for name in ('config.json', 'preprocessor_config.json', 'pytorch_model.bin'):
        copy_file_if_exists(RVC_DIR / 'assets' / 'hubert_base' / name, hubert_dest / name)

    # 3. Voice Engine
    log("Copying voice-engine...")
    ve_dir = DEST_DIR / 'voice-engine'
    ve_dir.mkdir(parents=True, exist_ok=True)

    # Launcher
    launcher_src = PACKAGING_DIR / 'kubo_voice_launcher.c'
    launcher_exe = ve_dir / 'KuboVoice.exe'
    gcc_exe = None
    for cand in (r"C:\Program Files (x86)\cpeditor\mingw64\bin\gcc.exe", r"C:\MinGW\bin\gcc.exe", shutil.which("gcc")):
        if cand and Path(cand).is_file():
            gcc_exe = cand
            break
    if gcc_exe and launcher_src.is_file():
        log(f"Compiling native launcher with Job Object using {gcc_exe}...")
        cmd = [gcc_exe, '-O2', '-municode', '-o', str(launcher_exe), str(launcher_src)]
        subprocess.run(cmd, check=True)
    elif (RELEASE_REF / 'voice-engine' / 'KuboVoice.exe').is_file():
        shutil.copy2(RELEASE_REF / 'voice-engine' / 'KuboVoice.exe', launcher_exe)

    # Bin (ffmpeg)
    bin_dir = ve_dir / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    copy_file_if_exists(RVC_DIR / 'ffmpeg.exe', bin_dir / 'ffmpeg.exe')
    copy_file_if_exists(RVC_DIR / 'ffprobe.exe', bin_dir / 'ffprobe.exe')

    # Configs
    copy_tree_fast(RVC_DIR / 'configs', ve_dir / 'configs')

    # Engine source
    engine_dir = ve_dir / 'engine'
    engine_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(APP_DIR / 'kubo_worker.py', engine_dir / 'kubo_worker.py')
    shutil.copy2(APP_DIR / 'paths.py', engine_dir / 'paths.py')
    for d in ('infer', 'configs', 'i18n', 'tools'):
        if (RVC_DIR / d).is_dir():
            copy_tree_fast(RVC_DIR / d, engine_dir / d)

    # Runtime (copy from reference release or assemble)
    log("Synchronizing isolated runtime...")
    if (RELEASE_REF / 'voice-engine' / 'runtime').is_dir():
        copy_tree_fast(RELEASE_REF / 'voice-engine' / 'runtime', ve_dir / 'runtime')
    else:
        log("ERROR: Reference runtime not found in release bundle.")
        sys.exit(1)

    # 4. Licenses & Documentation
    log("Copying licenses and documentation...")
    lic_dir = DEST_DIR / 'licenses'
    lic_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy from RELEASE_REF licenses if present
    if (RELEASE_REF / 'licenses').is_dir():
        copy_tree_fast(RELEASE_REF / 'licenses', lic_dir)
        
    # Copy CREDITS-VOICE.md
    credits_file = PROJECT_ROOT / 'Kubo-github' / 'CREDITS.md'
    if not credits_file.is_file():
        credits_file = PROJECT_ROOT / 'CREDITS.md'
    if credits_file.is_file():
        shutil.copy2(credits_file, lic_dir / 'CREDITS-VOICE.md')

    # README.txt
    if (RELEASE_REF / 'README.txt').is_file():
        shutil.copy2(RELEASE_REF / 'README.txt', DEST_DIR / 'README.txt')

    # 5. Manifest.json
    log("Generating manifest.json with checksums...")
    all_files = [f for f in DEST_DIR.rglob('*') if f.is_file() and f.name != 'manifest.json']
    total_bytes = sum(f.stat().st_size for f in all_files)

    manifest = {
        "name": "Nagisa Kubo Desktop Companion",
        "version": "1.0.0",
        "platform": "windows-x64",
        "source_git_commit": GIT_COMMIT,
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
            "Kubo.exe": sha256_file(DEST_DIR / 'Kubo.exe'),
            "voice-engine/KuboVoice.exe": sha256_file(DEST_DIR / 'voice-engine' / 'KuboVoice.exe'),
            "data/models/NagisaKubo_e300_s1500.pth": sha256_file(DEST_DIR / 'data' / 'models' / 'NagisaKubo_e300_s1500.pth'),
            "data/models/added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index": sha256_file(DEST_DIR / 'data' / 'models' / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index'),
            "data/models/rmvpe.pt": sha256_file(DEST_DIR / 'data' / 'models' / 'rmvpe.pt'),
            "data/models/hubert_base/pytorch_model.bin": sha256_file(DEST_DIR / 'data' / 'models' / 'hubert_base' / 'pytorch_model.bin'),
        }
    }
    (DEST_DIR / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    log("manifest.json generated successfully.")

    # 6. Security Audit
    log("Running security and secret audit...")
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
                if key_pattern.search(txt) and not '.env.example' in str(f):
                    leakages.append(f"{f} contains API key pattern")
            except Exception:
                pass
    if leakages:
        raise ValueError(f"Secret leak detected: {leakages}")
    log("Security audit passed: 0 secrets found.")

    duration = time.monotonic() - start_time
    log("=" * 60)
    log(f"PACKAGE COMPLETED in {duration:.1f}s")
    log(f"Destination: {DEST_DIR}")
    log(f"Total files: {manifest['bundle_metrics']['total_files']}")
    log(f"Total size: {manifest['bundle_metrics']['total_size_gib']} GiB ({manifest['bundle_metrics']['total_size_mib']} MiB)")
    log("=" * 60)


if __name__ == '__main__':
    main()
