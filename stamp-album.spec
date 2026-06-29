# StampAlbum Pro — PyInstaller spec file
# Build with: pyinstaller stamp-album.spec

block_cipher = None

a = Analysis(
    ['src/stamp_album/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/stamp_album/web', 'stamp_album/web'),
        ('src/stamp_album/templates.py', 'stamp_album'),
    ],
    hiddenimports=[
        'stamp_album',
        'stamp_album.api',
        'stamp_album.core',
        'stamp_album.engines',
        'stamp_album.web',
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
    name='StampAlbumPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='StampAlbumPro',
)

app = BUNDLE(
    coll,
    name='StampAlbum Pro.app',
    icon=None,
    bundle_identifier='com.stampalbum.pro',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '0.1.0',
        'NSRequiresAquaSystemAppearance': 'No',
    },
)
