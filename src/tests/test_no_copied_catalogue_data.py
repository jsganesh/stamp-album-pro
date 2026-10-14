"""No catalogue publisher's or website's numbering is shipped with the app.

The sample album, the starter templates, the sample DSL file and the docs used to
carry StampWorld's numbers (Great Britain 1 to 3), copied without permission.
Collectors add their own catalogue's numbers; the app ships none.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHIPPED = [ROOT / "src" / "stamp_album", ROOT / "assets", ROOT / "docs", ROOT / "README.md"]
TEXT = {".py", ".js", ".html", ".css", ".json", ".txt", ".md", ".slbum"}
COPIED = ["stampworld"]


def _files():
    for base in SHIPPED:
        paths = [base] if base.is_file() else base.rglob("*")
        for p in paths:
            if p.is_file() and p.suffix in TEXT and "__pycache__" not in p.parts:
                yield p


def test_no_copied_catalogue_numbering_is_shipped():
    found = []
    for p in _files():
        text = p.read_text(encoding="utf-8", errors="replace").lower()
        found += [f"{p.relative_to(ROOT)}: {name}" for name in COPIED if name in text]
    assert not found, found
