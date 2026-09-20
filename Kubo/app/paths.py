"""Central path management and environment isolation for source and frozen modes."""
import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Return True if running inside a PyInstaller frozen bundle."""
    return getattr(sys, 'frozen', False)


def get_bundle_dir() -> Path:
    """Return the application root directory (where Kubo.exe or app.py lives)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]  # Kubo directory


def get_project_root() -> Path:
    """Return the repository root in source mode, or bundle directory in frozen mode."""
    if is_frozen():
        return get_bundle_dir()
    return Path(__file__).resolve().parents[2]


def get_user_data_dir() -> Path:
    """Return the writable user data directory under LOCALAPPDATA."""
    local_app_data = os.environ.get('LOCALAPPDATA')
    if local_app_data:
        base = Path(local_app_data)
    else:
        base = Path.home() / 'AppData' / 'Local'
    user_dir = base / 'Kubo'
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_logs_dir() -> Path:
    """Return the writable logs directory."""
    logs = get_user_data_dir() / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    return logs


def get_avatars_dir() -> Path:
    """Return directory containing avatar atlases and reaction images."""
    if is_frozen():
        candidate = get_bundle_dir() / 'data' / 'avatars'
        if candidate.is_dir():
            return candidate
        # Fallback to _internal/assets if bundled there
        internal_candidate = get_bundle_dir() / '_internal' / 'assets'
        if internal_candidate.is_dir():
            return internal_candidate
    return Path(__file__).resolve().parent / 'assets'


def get_samples_dir() -> Path:
    """Return directory containing preview audio samples."""
    if is_frozen():
        candidate = get_bundle_dir() / 'data' / 'samples'
        if candidate.is_dir():
            return candidate
        internal_candidate = get_bundle_dir() / '_internal' / 'assets'
        if internal_candidate.is_dir():
            return internal_candidate
    return Path(__file__).resolve().parent / 'assets'


def get_persona_file() -> Path:
    """Return path to kubo-persona.md."""
    if is_frozen():
        candidate = get_bundle_dir() / 'data' / 'persona' / 'kubo-persona.md'
        if candidate.is_file():
            return candidate
        internal_candidate = get_bundle_dir() / '_internal' / 'kubo-persona.md'
        if internal_candidate.is_file():
            return internal_candidate
    return Path(__file__).resolve().parent / 'kubo-persona.md'


def get_models_dir() -> Path:
    """Return path to models directory."""
    if is_frozen():
        return get_bundle_dir() / 'data' / 'models'
    return get_project_root() / 'work' / 'rvc' / 'assets'


def get_voice_engine_dir() -> Path:
    """Return voice engine directory."""
    if is_frozen():
        return get_bundle_dir() / 'voice-engine'
    return get_project_root() / 'work' / 'rvc'


def get_voice_engine_executable() -> Path:
    """Return executable used to launch voice engine."""
    if is_frozen():
        return get_bundle_dir() / 'voice-engine' / 'KuboVoice.exe'
    return get_project_root() / 'work' / 'rvc-env' / 'Scripts' / 'python.exe'


def get_default_allowed_roots() -> list[str]:
    """Return safe default allowed roots for Agent file access."""
    if is_frozen():
        return []
    return [str(get_project_root().resolve())]


def clean_subprocess_env(extra_env: dict | None = None, keep_internal_path: bool = False) -> dict[str, str]:
    """Return a clean copy of environment variables preventing PyInstaller leakage."""
    env = os.environ.copy()
    # Strip PyInstaller and Python isolation variables
    for key in (
        'PYTHONPATH', 'PYTHONHOME', '_MEIPASS', '_MEIPASS2',
        'PYINSTALLER_STRICT_UNPACK_PROCESS',
        'OPENAI_API_KEY', 'FISH_API_KEY'
    ):
        env.pop(key, None)

    env['PYTHONSAFEPATH'] = '1'
    env['PYTHONNOUSERSITE'] = '1'

    # Clean PATH from _internal and all its subdirectories if launching external programs
    if is_frozen() and not keep_internal_path:
        bundle_internal = (get_bundle_dir() / '_internal').resolve()
        meipass_raw = getattr(sys, '_MEIPASS', None)
        meipass = Path(meipass_raw).resolve() if meipass_raw else bundle_internal

        cleaned_paths = []
        for p in env.get('PATH', '').split(os.pathsep):
            if not p.strip():
                continue
            try:
                rp = Path(p).resolve()
                if rp == bundle_internal or rp == meipass:
                    continue
                if rp.is_relative_to(bundle_internal) or rp.is_relative_to(meipass):
                    continue
            except (ValueError, RuntimeError, OSError):
                pass
            cleaned_paths.append(p)
        env['PATH'] = os.pathsep.join(cleaned_paths)

    if extra_env:
        env.update(extra_env)

    return env

