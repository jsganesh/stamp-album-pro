"""
Root conftest.py — sets DYLD_FALLBACK_LIBRARY_PATH so WeasyPrint can find
Homebrew native libraries (Pango, Cairo, etc.) when running under pytest.

Without this, WeasyPrint raises:
    OSError: cannot load library 'libgobject-2.0-0'

The path covers both Apple Silicon (/opt/homebrew) and Intel (/usr/local).
"""
import os
import sys
from pathlib import Path

# Only needed on macOS
if sys.platform == "darwin":
    brew_prefixes = ["/opt/homebrew/lib", "/usr/local/lib"]
    existing = [p for p in brew_prefixes if Path(p).is_dir()]
    if existing:
        current = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        new_path = ":".join(existing)
        if current:
            new_path = new_path + ":" + current
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = new_path
