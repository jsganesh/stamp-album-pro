"""The legacy PyQt6 editor is gone (pending item 11).

Nothing in the package may import PyQt, the ``ui`` subpackage must not come
back, and the old ``--qt`` / ``--legacy-qt`` flags must say the editor was
removed instead of starting something else.
"""

import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "src" / "stamp_album"


def test_no_ui_subpackage():
    # A clone that ran the old code keeps an untracked ui/__pycache__ folder,
    # so look for source files, not the folder.
    assert not list((PKG / "ui").glob("*.py"))


def test_nothing_imports_pyqt():
    offenders = []
    for path in PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(n.split(".")[0] in ("PyQt6", "PyQt5", "PySide6") for n in names):
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
            if any(n.startswith("stamp_album.ui") for n in names):
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert offenders == []


def test_no_legacy_extra():
    # Text check: tomllib needs Python 3.11 and CI also runs 3.10.
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "legacy = [" not in text
    assert "qt" not in text.lower()


def test_qt_flags_say_removed():
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    for flag in ("--qt", "--legacy-qt"):
        result = subprocess.run(
            [sys.executable, "-m", "stamp_album", flag],
            capture_output=True,
            encoding="utf-8",
            env=env,
            timeout=60,
        )
        assert result.returncode == 1, flag
        assert "PyQt6 editor was removed" in result.stderr, flag
