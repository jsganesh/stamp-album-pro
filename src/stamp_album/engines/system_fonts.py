"""Fonts installed on this computer, for text items (ADR-001).

One place finds a font by the name shown in the Font list ("Georgia", "Times New Roman")
and hands it to every export, so what the editor shows is what prints:

- ``available()``: the Font list (``GET /api/fonts``), the curated names below that are
  installed here and can be embedded.
- ``reportlab_name()`` for the PDF, ``pillow_font()`` for the PNG, ``font_face()`` (an
  embedded subset) for the SVG and HTML, and ``css_family()`` for Print preview.

Only the regular face of each family is used. A face counts when it has TrueType outlines
(ReportLab can embed nothing else) and its licence allows embedding. The OS font folders
are searched with their subfolders: macOS keeps most fonts in
``/System/Library/Fonts/Supplemental``.
"""

from __future__ import annotations

import os
import platform
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# The names offered in the Font list when installed (the list the editor used to try).
CANDIDATES = (
    "American Typewriter", "Andale Mono", "Apple Chancery", "Arial", "Arial Black",
    "Arial Narrow", "Avant Garde", "Baskerville", "Bookman Old Style", "Brush Script MT",
    "Calibri", "Cambria", "Candara", "Century Gothic", "Chalkduster", "Comic Sans MS",
    "Consolas", "Copperplate", "Courier New", "Didot", "Franklin Gothic", "Futura",
    "Garamond", "Georgia", "Gill Sans", "Goudy", "Helvetica", "Herculanum", "Impact",
    "Lucida Console", "Lucida Sans", "Luminari", "Marker Felt", "Microsoft Sans Serif",
    "Noteworthy", "Optima", "Palatino", "Papyrus", "Perpetua", "Rockwell", "Segoe UI",
    "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana", "Zapfino",
)

# Style names that mean the plain face of a family
_REGULAR = {"regular", "roman", "normal", "book", "plain", "standard", "medium"}
_FONT_EXTS = (".ttf", ".ttc", ".otf")


@dataclass(frozen=True)
class Face:
    """One font face: its file, and its number inside a .ttc collection (0 otherwise)."""

    family: str
    path: Path
    index: int = 0


def font_dirs() -> list[Path]:
    """The folders this OS keeps fonts in (each searched with its subfolders)."""
    system = platform.system()
    home = Path.home()
    if system == "Darwin":
        dirs = [Path("/System/Library/Fonts"), Path("/Library/Fonts"), home / "Library/Fonts"]
    elif system == "Windows":
        dirs = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"]
        local = os.environ.get("LOCALAPPDATA")
        if local:
            dirs.append(Path(local) / "Microsoft/Windows/Fonts")
    else:
        dirs = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"),
                home / ".fonts", home / ".local/share/fonts"]
    return [d for d in dirs if d.is_dir()]


def _names(tt) -> list[tuple[str, str]]:
    """(family, style) pairs a face goes by: its legacy and its typographic names."""
    name = tt["name"]
    out = []
    for fam_id, style_id in ((1, 2), (16, 17)):
        fam = name.getDebugName(fam_id)
        if fam:
            out.append((fam.strip(), (name.getDebugName(style_id) or "Regular").strip()))
    return out


def _usable(tt) -> bool:
    """TrueType outlines, and a licence that allows embedding in a document."""
    if "glyf" not in tt:
        return False
    os2 = tt.get("OS/2")
    fs_type = getattr(os2, "fsType", 0) if os2 is not None else 0
    return not (fs_type & 0x0002 or fs_type & 0x0200)  # restricted, or bitmap only


def _faces_in(path: Path) -> list[Face]:
    from fontTools.ttLib import TTCollection, TTFont

    try:
        if path.suffix.lower() == ".ttc":
            with TTCollection(str(path), lazy=True) as coll:
                count = len(coll.fonts)
        else:
            count = 1
        faces = []
        for i in range(count):
            kw = {"fontNumber": i} if path.suffix.lower() == ".ttc" else {}
            with TTFont(str(path), lazy=True, **kw) as tt:
                if not _usable(tt):
                    continue
                for family, style in _names(tt):
                    if style.lower() in _REGULAR:
                        faces.append(Face(family, path, i))
        return faces
    except Exception:  # a damaged or unusual font file is skipped
        return []


_lock = threading.Lock()


@lru_cache(maxsize=1)
def index() -> dict[str, Face]:
    """Every usable regular face here, by lower-case family name (the first one found wins)."""
    found: dict[str, Face] = {}
    for d in font_dirs():
        for root, _dirs, files in os.walk(d):
            for fn in sorted(files):
                if fn.lower().endswith(_FONT_EXTS):
                    for face in _faces_in(Path(root) / fn):
                        found.setdefault(face.family.lower(), face)
    return found


def find(family: str | None) -> Face | None:
    """The installed face for a Font-list name, or None."""
    if not family:
        return None
    with _lock:  # the first call scans; export threads wait for it rather than scan again
        idx = index()
    return idx.get(family.strip().lower())


def available() -> list[str]:
    """The Font list: the candidate names installed here, sorted."""
    return sorted(name for name in CANDIDATES if find(name))


def clear_cache() -> None:
    """Forget what was found (tests, or after fonts are installed while running)."""
    index.cache_clear()
    _font_face.cache_clear()
    _registered.clear()


# ── For each export ──

_registered: dict[str, str] = {}


def reportlab_name(family: str) -> str | None:
    """Register the family's face with ReportLab (once) and return its name, or None."""
    face = find(family)
    if face is None:
        return None
    key = face.family.lower()
    if key not in _registered:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        name = "SYS-" + face.family.replace(" ", "")
        try:
            pdfmetrics.registerFont(TTFont(name, str(face.path), subfontIndex=face.index))
        except Exception:
            return None
        _registered[key] = name
    return _registered[key]


def pillow_font(family: str, size: float):
    """A Pillow font of the family at *size* pixels, or None."""
    face = find(family)
    if face is None:
        return None
    from PIL import ImageFont

    try:
        return ImageFont.truetype(str(face.path), size, index=face.index)
    except Exception:
        return None


def _css_name(family: str) -> str:
    return family.replace("\\", "").replace("'", "").replace('"', "").replace(";", "")


def css_family(family: str) -> str:
    """A CSS font-family list for the family, falling back to Helvetica as the PDF does."""
    return f"'{_css_name(family)}',Helvetica,Arial,sans-serif"


def font_face(family: str, chars: str) -> str:
    """An @font-face rule embedding only *chars* of the family (SVG, HTML), or ""."""
    face = find(family)
    if face is None or not chars:
        return ""
    return _font_face(face, "".join(sorted(set(chars))))


@lru_cache(maxsize=32)
def _font_face(face: Face, chars: str) -> str:
    import base64
    import io

    from fontTools import subset
    from fontTools.ttLib import TTFont

    opts = subset.Options()
    opts.layout_features = []  # no kerning or ligatures: the PDF draws without them too
    opts.drop_tables += ["GPOS", "GSUB", "GDEF", "BASE"]
    opts.hinting = False
    opts.notdef_outline = True
    opts.name_IDs = ["*"]  # keep the font's names and its notices
    opts.name_languages = ["*"]
    import logging

    # Tables the subsetter doesn't know are dropped; that needs no warning.
    logging.getLogger("fontTools.subset").setLevel(logging.ERROR)
    try:
        kw = {"fontNumber": face.index} if face.path.suffix.lower() == ".ttc" else {}
        with TTFont(str(face.path), recalcTimestamp=False, **kw) as tt:
            sub = subset.Subsetter(opts)
            sub.populate(unicodes=[ord(c) for c in chars])
            sub.subset(tt)
            buf = io.BytesIO()
            tt.save(buf)
    except Exception:
        return ""
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return (
        f"@font-face{{font-family:'{_css_name(face.family)}';"
        f"src:url(data:font/ttf;base64,{data}) format('truetype');"
        f"font-weight:400;font-style:normal;}}"
    )
