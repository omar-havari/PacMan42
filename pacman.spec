# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — one-folder build of the Pac-Man game.
# Rebuild with:  pyinstaller pacman.spec

block_cipher = None

a = Analysis(
    ['pac-man.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),        # fonts + images
        ('config.json', '.'),        # default config
        ('CONTROLS.txt', '.'),       # in-package instructions
    ],
    hiddenimports=[
        'mazegenerator',
        'mazegenerator.mazegenerator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='pacman',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # GUI game: no black terminal window
    disable_windowed_traceback=False,
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
    upx=True,
    upx_exclude=[],
    name='pacman',           # final output: dist\pacman\
)
