"""Shared layout for stamp captions.

Every view (editor, HTML preview, PDF, PNG, SVG) places a stamp's captions the
same way:

* the heading sits above the box, bold (or semibold, as the album chooses), 9 pt;
* below the box, in order: the description (8 pt), the details line
  ("1/2D · Used · Imperforate", 8 pt italic) and the catalogue number
  (8 pt italic);
* a picture has one caption below it, its own (8 pt italic), and nothing else;
* every caption is set in the bundled Source Serif 4 Caption (``caption_fonts``),
  whatever the stamp's own font;
* the nearest line box is ``GAP_MM`` from the frame's outer edge on each side
  (the frame is drawn outside the stamp: see ``frames.py``);
* stamps in a row put their headings on one line, ``GAP_MM`` above the row's highest
  frame (``heading_rows``), so mixed heights line up;
* lines are centred on the frame and wrapped to its width;
* captions are black.

Keep in step with ``captionLayout`` and ``captionRows`` in ``web/dsl_core.js``.

Every view measures with ``caption_fonts.measure`` (the default here), so the
lines break in the same places everywhere. All positions are returned in
millimetres from the page's top-left corner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from stamp_album.engines import caption_fonts, text_layout

GAP_MM = 2.0  # space between the frame and the nearest caption line box
HEADING_PT = 9.0  # heading size: the only caption that stands out
CAPTION_PT = 8.0  # description, details and catalogue
LINE_HEIGHT = text_layout.LINE_HEIGHT
FIRST_BASELINE = text_layout.FIRST_BASELINE
MM_PER_PT = 25.4 / 72.0
COLOR_RGB = (0.0, 0.0, 0.0)  # captions are black
COLOR_HEX = "#000000"
ROW_TOLERANCE_MM = 1.0  # frame bottoms this close count as one row

Measure = Callable[[str, str, float], float]


@dataclass
class CaptionLine:
    """One line of caption text, positioned on the page (mm)."""

    text: str
    kind: str  # "heading" | "description" | "details" | "catalogue" | "picture"
    font_id: str  # caption font id: "CapR", "CapI", "CapB" or "CapSB" (caption_fonts)
    size_pt: float
    top: float  # top of the line box
    bottom: float  # bottom of the line box
    baseline: float
    width: float  # measured text width
    x: float  # left edge of the centred text

    @property
    def weight(self) -> int:
        return caption_fonts.weight(self.font_id)

    @property
    def bold(self) -> bool:
        return self.weight >= 600

    @property
    def italic(self) -> bool:
        return caption_fonts.style(self.font_id) == "italic"


def catalogue_text(refs) -> str:
    return " · ".join(r.strip() for r in (refs or []) if r and r.strip())


def caption_parts(stamp, heading_weight: Optional[str] = None) -> tuple[list, list]:
    """(above, below) as lists of (kind, text, font_id, size_pt), empty parts dropped."""
    above, below = [], []
    if getattr(stamp, "is_picture", False):  # a picture: its own caption only
        text = (getattr(stamp, "picture_caption", "") or "").strip()
        if text:
            below.append(("picture", text, "CapI", CAPTION_PT))
        return above, below
    heading = getattr(stamp, "heading", None)
    if heading is not None and (heading.text or "").strip():
        font = caption_fonts.heading_font(heading_weight)
        above.append(("heading", heading.text, font, HEADING_PT))
    desc = (getattr(stamp, "description", "") or "").strip()
    if desc:
        below.append(("description", desc, "CapR", CAPTION_PT))
    details = (getattr(stamp, "footer_text", "") or "").strip()
    if details:
        below.append(("details", details, "CapI", CAPTION_PT))
    cat = catalogue_text(getattr(stamp, "catalog_refs", None))
    if cat:
        below.append(("catalogue", cat, "CapI", CAPTION_PT))
    return above, below


def heading_rows(items) -> list[Optional[float]]:
    """The top each item's heading sits above, for every item on a page.

    *items* are ``(x, y, w, h, has_heading)``: the item's outer edge in mm (a stamp's
    frame). A row is items with a heading whose bottoms are within ``ROW_TOLERANCE_MM``
    and that are neighbours left to right, with nothing else standing between them; items
    in the same line without a heading neither take part nor break the row.

    Returns the row's highest frame top (or the item's own) for items with a heading,
    None for the rest. Keep in step with ``captionRows`` in ``web/dsl_core.js``.
    """
    tol, eps = ROW_TOLERANCE_MM + 1e-9, 1e-6
    n = len(items)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def bottom(i):
        return items[i][1] + items[i][3]

    cand = [i for i in range(n) if items[i][4]]
    for i in cand:
        ax, ay, aw, _ah, _ = items[i]
        ar = ax + aw
        best = None
        for j in cand:
            bx = items[j][0]
            if j == i or abs(bottom(j) - bottom(i)) > tol or bx < ar - eps:
                continue
            if best is None or bx < items[best][0] - 1e-9 or (
                abs(bx - items[best][0]) <= 1e-9 and j < best
            ):
                best = j
        if best is None:
            continue
        bx, by = items[best][0], items[best][1]
        top, bot = min(ay, by), max(bottom(i), bottom(best))
        blocked = False
        for k in range(n):
            if k in (i, best) or abs(bottom(k) - bottom(i)) <= tol:  # same line
                continue
            cx, cy, cw, ch, _ = items[k]
            if cx < bx - eps and cx + cw > ar + eps and cy < bot - eps and cy + ch > top + eps:
                blocked = True
                break
        if not blocked:
            parent[find(i)] = find(best)

    row_top: dict[int, float] = {}
    for i in cand:
        r = find(i)
        row_top[r] = min(row_top.get(r, items[i][1]), items[i][1])
    return [row_top[find(i)] if items[i][4] else None for i in range(n)]


def page_row_tops(stamps) -> dict[int, float]:
    """``heading_rows`` for a page's absolute stamps, keyed by ``id(stamp)``.

    Text items stand in the way but have no captions; stamps, free shapes and pictures
    use their frame's outer edge. Positions are the stamps' own, in mm.
    """
    from stamp_album.engines import frames

    stamps = list(stamps)
    items = []
    for s in stamps:
        x, y, w, h = s.abs_x, s.abs_y, s.width, s.height
        if getattr(s, "is_text_element", False):
            items.append((x, y, w, h, False))
        else:
            items.append((*frames.outer_box(s, x, y, w, h), bool(caption_parts(s)[0])))
    tops = heading_rows(items)
    return {id(s): t for s, t in zip(stamps, tops) if t is not None}


def layout(stamp, x: float, y: float, w: float, h: float,
           measure: Measure = caption_fonts.measure,
           heading_weight: Optional[str] = None,
           row_top: Optional[float] = None) -> list[CaptionLine]:
    """Caption lines for a stamp at (x, y, w, h) mm, top to bottom.

    (x, y, w, h) is the stamp's own size; the captions are placed around its frame.
    *heading_weight* is the album's choice, "bold" (the default) or "semibold".
    *row_top* is the top of the row's highest frame (``heading_rows``); the heading sits
    ``GAP_MM`` above it instead of above the stamp's own frame.
    """
    from stamp_album.engines import frames

    x, y, w, h = frames.outer_box(stamp, x, y, w, h)
    above, below = caption_parts(stamp, heading_weight)

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
    head_top = y if row_top is None else min(y, row_top)
    top = head_top - GAP_MM - sum(r[3] * LINE_HEIGHT * MM_PER_PT for r in rows)
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
