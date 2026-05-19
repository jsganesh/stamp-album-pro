# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for StampAlbum Pro.

Usage:
    pyinstaller stamp_album.spec

This creates a macOS .app bundle in the dist/ directory.
"""

import os
from pathlib import Path

block_cipher = None

# Get the project root directory (spec file location)
project_root = Path(os.getcwd())

a = Analysis(
    [str(project_root / "src" / "stamp_album" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(project_root / "assets" / "templates"), "assets/templates"),
    ],
    hiddenimports=[
        "stamp_album.ui.main_window",
        "stamp_album.ui.editor",
        "stamp_album.ui.preview_panel",
        "stamp_album.ui.visual_builder",
        "stamp_album.ui.config_dialog",
        "stamp_album.ui.template_gallery",
        "stamp_album.ui.syntax_highlighter",
        "stamp_album.core.parser",
        "stamp_album.core.models",
        "stamp_album.engines.pdf_generator",
        "stamp_album.engines.layout_engine",
        "stamp_album.engines.font_manager",
        "weasyprint",
        "weasyprint.text",
        "weasyprint.text.fonts",
        "weasyprint.formatting_structure",
        "weasyprint.draw",
        "weasyprint.pdf",
        "PIL",
        "lark",
        "yaml",
        "fontTools",
        "fontTools.ttLib",
        "fontTools.subset",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "email",
        "http",
        "xml",
        "pydoc",
    ],
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
    name="stamp-album",
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
    name="stamp-album",
)

app = BUNDLE(
    coll,
    name="StampAlbum Pro.app",
    icon=None,
    bundle_identifier="com.stampalbum.pro",
    version="0.1.0",
    info_plist={
        "NSPrincipalClass": "NSApplication",
        "NSHighResolutionCapable": "True",
        "CFBundleName": "StampAlbum Pro",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "CFBundleExecutable": "stamp-album",
        "CFBundleIdentifier": "com.stampalbum.pro",
    },
)
