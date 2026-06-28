"""
Root conftest.py for stamp-album-pro.

Ensures:
1. The src/ directory is on sys.path so `from stamp_album import ...` works
   without needing PYTHONPATH=src or `pip install -e .`.
2. On macOS, DYLD_FALLBACK_LIBRARY_PATH includes Homebrew lib dirs
   so native libraries (fonttools, pymupdf) can be found.
3. pytest-qt warning about qt_api config is suppressed (legacy UI is optional).
"""
import os
import sys
from pathlib import Path

# Put src/ on the import path so tests can `import stamp_album`
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# macOS: ensure native libraries in Homebrew prefixes are findable
if sys.platform == "darwin":
    brew_prefixes = ["/opt/homebrew/lib", "/usr/local/lib"]
    existing = [p for p in brew_prefixes if Path(p).is_dir()]
    if existing:
        current = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        new_path = ":".join(existing)
        if current:
            new_path = new_path + ":" + current
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = new_path
