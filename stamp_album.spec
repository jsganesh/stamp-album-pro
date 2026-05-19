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

# WeasyPrint native dependencies (Homebrew paths on Apple Silicon macOS)
HOMEBREW_LIB = "/opt/homebrew/lib"
WEASYPRINT_LIBS = [
    "libgobject-2.0.0.dylib",
    "libglib-2.0.0.dylib",
    "libpango-1.0.0.dylib",
    "libpangocairo-1.0.0.dylib",
    "libcairo.2.dylib",
    "libgdk_pixbuf-2.0.0.dylib",
    "libgio-2.0.0.dylib",
    "libgmodule-2.0.0.dylib",
    "libintl.8.dylib",
    "libfribidi.0.dylib",
    "libharfbuzz.0.dylib",
    "libgraphite2.3.2.1.dylib",
    "libpixman-1.0.dylib",
    "libfontconfig.1.dylib",
    "libfreetype.6.dylib",
    "libpng16.16.dylib",
    "libbz2.1.0.8.dylib",
    "liblzma.5.dylib",
    "libz.1.3.1.zlib.dylib",
    "libffi.8.dylib",
    "libpcre2-8.0.dylib",
    "libiconv.2.dylib",
]

# Build datas list for dylibs that exist
weasyprint_datas = []
for lib in WEASYPRINT_LIBS:
    lib_path = os.path.join(HOMEBREW_LIB, lib)
    if os.path.exists(lib_path):
        weasyprint_datas.append((lib_path, "."))

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

# Build TOC for WeasyPrint dylibs
from PyInstaller.building.datastruct import TOC

weasyprint_toc = TOC()
for lib in WEASYPRINT_LIBS:
    lib_path = os.path.join(HOMEBREW_LIB, lib)
    if os.path.exists(lib_path):
        weasyprint_toc.append((lib, lib_path, "BINARY"))

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    weasyprint_toc,
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

# Post-build: bundle dylibs and create wrapper script
import subprocess
import shutil

def post_build():
    """Bundle WeasyPrint native libraries and create wrapper script."""
    app_path = Path("dist/StampAlbum Pro.app")
    macos_path = app_path / "Contents" / "MacOS"

    # Rename the PyInstaller binary
    binary_path = macos_path / "stamp-album"
    real_binary = macos_path / "stamp-album-bin"
    if binary_path.exists() and not real_binary.exists():
        shutil.move(str(binary_path), str(real_binary))

    # Copy required dylibs from Homebrew
    copied_libs = []
    for lib in WEASYPRINT_LIBS:
        src = Path(HOMEBREW_LIB) / lib
        if src.exists():
            dst = macos_path / lib
            if not dst.exists():
                shutil.copy2(str(src), str(dst))
                copied_libs.append(lib)

    # Create wrapper script
    wrapper = macos_path / "stamp-album"
    wrapper.write_text('''#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
export DYLD_FALLBACK_LIBRARY_PATH="$DIR"
exec "$DIR/stamp-album-bin" "$@"
''')
    wrapper.chmod(0o755)

    # Fix library IDs for bundled dylibs
    for lib_file in macos_path.glob("*.dylib"):
        subprocess.run(
            ["install_name_tool", "-id", f"@executable_path/{lib_file.name}", str(lib_file)],
            capture_output=True
        )

    # Fix library references in the main binary
    for lib in copied_libs:
        subprocess.run(
            ["install_name_tool", "-change",
             f"{HOMEBREW_LIB}/{lib}",
             f"@executable_path/{lib}",
             str(real_binary)],
            capture_output=True
        )

    print(f"Bundled {len(copied_libs)} native libraries")

post_build()
