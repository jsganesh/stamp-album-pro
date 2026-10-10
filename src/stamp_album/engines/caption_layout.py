"""Shared layout for stamp captions.

Every view (editor, HTML preview, PDF, PNG, SVG) places a stamp's captions the
same way:

* the heading sits above the box, bold, 9 pt;
* below the box, in order: the description (8 pt), the details line
  ("1/2D · Used · Imperforate", 8 pt italic) and the catalogue number
  (8 pt italic);
* the nearest line box is ``GAP_MM`` from the frame's outer edge on each side
  (the frame is drawn outside the stamp: see ``frames.py``);
* lines are centred on the frame and wrapped to its width;
* captions are black.

Keep in step with ``captionLayout`` in ``web/dsl_core.js``.

Engines supply ``measure(text, font_id, size_pt) -> width_mm``. All positions
are returned in millimetres from the page's top-left corner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from stamp_album.engines import text_layout

GAP_MM = 2.0  # space between the frame and the nearest caption line box
HEADING_PT = 9.0  # heading size: the only caption that stands out
CAPTION_PT = 8.0  # description, details and catalogue
LINE_HEIGHT = text_layout.LINE_HEIGHT
FIRST_BASELINE = text_layout.FIRST_BASELINE
MM_PER_PT = 25.4 / 72.0
COLOR_RGB = (0.0, 0.0, 0.0)  # captions are black
COLOR_HEX = "#000000"

Measure = Callable[[str, str, float], float]


@dataclass
class CaptionLine:
    """One line of caption text, positioned on the page (mm)."""

    text: str
    kind: str  # "heading" | "description" | "details" | "catalogue"
    font_id: str  # built-in font id, e.g. "HB", "HN", "HI"
    size_pt: float
    top: float  # top of the line box
    bottom: float  # bottom of the line box
    baseline: float
    width: float  # measured text width
    x: float  # left edge of the centred text

    @property
    def bold(self) -> bool:
        return self.font_id[1:] in ("B", "S")

    @property
    def italic(self) -> bool:
        return self.font_id[1:] in ("I", "S")


def _family(font_id: Optional[str]) -> str:
    """The family letter (H, T or C) of a built-in font id; Helvetica otherwise."""
    f = (font_id or "H")[:1].upper()
    return f if f in ("H", "T", "C") and len(font_id or "H") <= 2 else "H"


def catalogue_text(refs) -> str:
    return " · ".join(r.strip() for r in (refs or []) if r and r.strip())


def caption_parts(stamp) -> tuple[list, list]:
    """(above, below) as lists of (kind, text, font_id, size_pt), empty parts dropped."""
    above, below = [], []
    if getattr(stamp, "is_picture", False):  # pictures have no captions
        return above, below
    heading = getattr(stamp, "heading", None)
    if heading is not None and (heading.text or "").strip():
        above.append(("heading", heading.text, _family(heading.font_id) + "B", HEADING_PT))
    fam = _family(getattr(stamp, "font_id", None))
    desc = (getattr(stamp, "description", "") or "").strip()
    if desc:
        below.append(("description", desc, fam + "N", CAPTION_PT))
    details = (getattr(stamp, "footer_text", "") or "").strip()
    if details:
        below.append(("details", details, fam + "I", CAPTION_PT))
    cat = catalogue_text(getattr(stamp, "catalog_refs", None))
    if cat:
        below.append(("catalogue", cat, fam + "I", CAPTION_PT))
    return above, below


def layout(stamp, x: float, y: float, w: float, h: float, measure: Measure) -> list[CaptionLine]:
    """Caption lines for a stamp at (x, y, w, h) mm, top to bottom.

    (x, y, w, h) is the stamp's own size; the captions are placed around its frame.
    """
    from stamp_album.engines import frames

    x, y, w, h = frames.outer_box(stamp, x, y, w, h)
    above, below = caption_parts(stamp)

    def wrapped(parts):
        rows = []
        for kind, text, fid, size in parts:
            for line in text_layout.wrap_lines(text, max(1.0, w), lambda s: measure(s, fid, size)):
                if line.strip():
                    rows.append((kind, line, fid, size))
        return rows

    def place(kind, text, fid, size, top):
        lh = size * LINE_HEIGHT * MM_PER_PT
        tw = measure(text, fid, size)
        return CaptionLine(
            text,
            kind,
            fid,
            size,
            top,
            top + lh,
            top + size * FIRST_BASELINE * MM_PER_PT,
            tw,
            x + (w - tw) / 2,
        )

    out: list[CaptionLine] = []
    rows = wrapped(above)
    top = y - GAP_MM - sum(r[3] * LINE_HEIGHT * MM_PER_PT for r in rows)
    for r in rows:
        line = place(*r, top)
        out.append(line)
        top = line.bottom
    top = y + h + GAP_MM
    for r in wrapped(below):
        line = place(*r, top)
        out.append(line)
        top = line.bottom
    return out


_PDF_FONT = {
    "HN": "Helvetica",
    "HB": "Helvetica-Bold",
    "HI": "Helvetica-Oblique",
    "TN": "Times-Roman",
    "TB": "Times-Bold",
    "TI": "Times-Italic",
    "CN": "Courier",
    "CB": "Courier-Bold",
    "CI": "Courier-Oblique",
}


def metrics_measure(text: str, font_id: str, size_pt: float) -> float:
    """Width in mm from the standard PDF font metrics (close to Arial/Times/Courier).

    Used by the SVG export and the HTML preview, which have no font engine of their own.
    """
    from reportlab.pdfbase import pdfmetrics

    return pdfmetrics.stringWidth(text, _PDF_FONT.get(font_id, "Helvetica"), size_pt) * MM_PER_PT


def bounds(lines: list[CaptionLine]) -> Optional[tuple[float, float, float, float]]:
    """(left, top, right, bottom) of the inked caption area, or None."""
    if not lines:
        return None
    return (
        min(ln.x for ln in lines),
        min(ln.top for ln in lines),
        max(ln.x + ln.width for ln in lines),
        max(ln.bottom for ln in lines),
    )
