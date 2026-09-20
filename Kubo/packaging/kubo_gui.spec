# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

block_cipher = None

app_dir = Path('../app').resolve()

datas = [
    (str(app_dir / 'kubo-persona.md'), '.'),
    (str(app_dir / 'assets' / 'kubo-atlas.png'), 'assets'),
    (str(app_dir / 'assets' / 'angry.png'), 'assets'),
    (str(app_dir / 'assets' / 'kubo-plus6.wav'), 'assets'),
]
datas += collect_data_files('sounddevice')

binaries = collect_dynamic_libs('sounddevice')

hiddenimports = [
    'PySide6.QtMultimedia',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'PySide6.QtCore',
    '_cffi_backend',
    'dotenv',
]
hiddenimports += collect_submodules('websockets')

a = Analysis(
    [str(app_dir / 'start_kubo.pyw')],
    pathex=[str(app_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'torch', 'scipy', 'numpy', 'transformers', 'faiss'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Kubo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Kubo',
)
