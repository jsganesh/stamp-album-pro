# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for StampAlbum Pro: the web app in its own window (pywebview).

Build from the project root:

    pyinstaller packaging/stamp_album.spec --clean --noconfirm

Output:
    macOS    dist/StampAlbum Pro.app
    Windows  dist/StampAlbumPro/StampAlbumPro.exe   (zip the folder to ship)
    Linux    dist/StampAlbumPro/StampAlbumPro       (not shipped; used for checks)

Opened with no arguments, the app opens its own window. The bundle also
accepts the usual flags: --cli (headless PDF), --web (browser mode).
`packaging/smoke_test.py` checks a built app.
"""

import os
import re
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).parent  # noqa: F821 (SPECPATH is set by PyInstaller)
SRC = ROOT / "src"
PKG = SRC / "stamp_album"

APP_NAME = "StampAlbumPro"
DISPLAY_NAME = "StampAlbum Pro"
BUNDLE_ID = "com.stampalbum.pro"
VERSION = re.search(
    r'__version__\s*=\s*"([^"]+)"', (PKG / "__init__.py").read_text(encoding="utf-8")
).group(1)

# THIRD_PARTY_LICENSES.txt is written fresh for this platform's installed libraries.
sys.path.insert(0, str(ROOT / "tools"))
import third_party_licenses  # noqa: E402

NOTICES = third_party_licenses.write(ROOT / "build" / "THIRD_PARTY_LICENSES.txt")

# Everything the browser UI loads: HTML, JS, CSS, tutorial pictures, the
# caption fonts (and OFL.txt), CodeMirror. Served from stamp_album/web.
datas = [(str(PKG / "web"), "stamp_album/web"), (str(NOTICES), ".")]

hiddenimports = (
    collect_submodules("stamp_album")
    # uvicorn picks its loop, protocol and lifespan modules by name at run time.
    + collect_submodules("uvicorn")
    + collect_submodules("websockets")
    + ["multipart", "python_multipart"]
)

# GUI toolkits pywebview could use on Linux; macOS uses Cocoa, Windows WebView2.
# mypy comes in only through pydantic's mypy plugin, which the app never loads:
# about 6 MB and 70 compiled modules that would each need signing.
excludes = ["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "mypy", "mypyc"]
if sys.platform.startswith("linux"):
    excludes = ["tkinter", "mypy", "mypyc"]

# macOS signing: unset gives PyInstaller's ad-hoc signature (runs only on the
# Mac that built it without a Gatekeeper warning). A "Developer ID Application:
# …" identity gives the hardened runtime that notarisation needs (build.sh).
CODESIGN_IDENTITY = os.environ.get("CODESIGN_IDENTITY") or None
ENTITLEMENTS = str(ROOT / "packaging" / "entitlements.plist") if CODESIGN_IDENTITY else None

# Rendered from packaging/icon/StampAlbum.svg by tools/make_icon.py.
ICON = ROOT / "packaging" / "icon"

a = Analysis(
    [str(PKG / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ICON / "StampAlbum.ico") if sys.platform == "win32" else None,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=CODESIGN_IDENTITY,
    entitlements_file=ENTITLEMENTS,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{DISPLAY_NAME}.app",
        icon=str(ICON / "StampAlbum.icns"),
        bundle_identifier=BUNDLE_ID,
        version=VERSION,
        info_plist={
            "CFBundleName": DISPLAY_NAME,
            "CFBundleDisplayName": DISPLAY_NAME,
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "LSMinimumSystemVersion": "11.0",
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,
        },
    )
