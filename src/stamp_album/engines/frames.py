"""Stamp frames: one geometry for every view.

A stamp's stored width and height are the stamp's own size, as given in the
catalogue. The frame is drawn outside it:

* ``CLEARANCE_MM`` of clear space all round between the stamp and the inside
  of the frame line (free shapes have none: their outline is the frame);
* then the line or lines: thin 0.5 pt, medium 1 pt, double two 0.5 pt lines
  ``DOUBLE_GAP_PT`` apart;
* stamps are framed in black.

Captions, overlap and border warnings measure from the frame's outer edge.

Keep in step with ``frameLines`` / ``frameOutset`` / ``offsetOutline`` in
``web/dsl_core.js``. Everything here is in millimetres, top-left origin, y down.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from stamp_album.engines.borders import polygon_points

CLEARANCE_MM = 1.0  # clear space between the stamp and the inside of its frame line
MM_PER_PT = 25.4 / 72.0
DOUBLE_GAP_PT = 1.0  # space between the two lines of a double frame
# Line widths in points, from the inside out
FRAME_LINES_PT: dict[str, tuple[float, ...]] = {
    "none": (),
    "thin": (0.5,),
    "medium": (1.0,),
    "double": (0.5, 0.5),
}


def frame_of(bdr: str | None, bdr_w: float | None) -> str:
    """The frame name for a border style and width (as ``frameOf`` in dsl_core.js)."""
    w = bdr_w or 0
    if bdr == "none" or (bdr != "double" and not w > 0):
        return "none"
    if bdr == "double":
        return "double"
    return "medium" if w > 0.75 else "thin"  # dashed and dotted frames from older albums too


@dataclass(frozen=True)
class FrameLine:
    offset: float  # mm, outward from the stamp edge to the centre of the line
    width: float  # mm


def _frame(stamp) -> str:
    return getattr(stamp, "frame", "thin") or "none"


def clearance(stamp) -> float:
    """Clear space between the stamp and its frame line (mm)."""
    if _frame(stamp) == "none" or getattr(stamp, "is_freehand", False):
        return 0.0
    return CLEARANCE_MM


def lines(stamp) -> list[FrameLine]:
    """The frame's lines, from the inside out."""
    out: list[FrameLine] = []
    edge = clearance(stamp)
    for i, w_pt in enumerate(FRAME_LINES_PT.get(_frame(stamp), FRAME_LINES_PT["thin"])):
        if i:
            edge += DOUBLE_GAP_PT * MM_PER_PT
        w = w_pt * MM_PER_PT
        out.append(FrameLine(edge + w / 2, w))
        edge += w
    return out


def outset(stamp) -> float:
    """Distance from the stamp edge to the frame's outer edge (mm); 0 with no frame."""
    ls = lines(stamp)
    return ls[-1].offset + ls[-1].width / 2 if ls else 0.0


def outer_box(stamp, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
    """(x, y, w, h) of the frame's outer edge, for a stamp at (x, y, w, h)."""
    o = outset(stamp)
    return x - o, y - o, w + 2 * o, h + 2 * o


def _offset_polygon(pts: list[tuple[float, float]], d: float) -> list[tuple[float, float]]:
    """A convex polygon moved outward by *d* on every side (mitred corners)."""
    if d == 0:
        return list(pts)
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    edges = []  # (point on the moved edge, direction)
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = dy / ln, -dx / ln
        if nx * ((ax + bx) / 2 - cx) + ny * ((ay + by) / 2 - cy) < 0:
            nx, ny = -nx, -ny
        edges.append(((ax + nx * d, ay + ny * d), (dx, dy)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = edges[i - 1], edges[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-12:
            out.append(p2)
            continue
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def outline(shape_name: str, x: float, y: float, w: float, h: float, d: float = 0.0):
    """The stamp's outline moved outward by *d* mm.

    Returns ("rect", (x, y, w, h)), ("ellipse", (cx, cy, rx, ry)) or ("polygon", [(x, y), ...]).
    """
    name = (shape_name or "RECTANGLE").upper()
    if name == "OVAL":
        return "ellipse", (x + w / 2, y + h / 2, w / 2 + d, h / 2 + d)
    pts = polygon_points(name, x, y, w, h)
    if pts:
        return "polygon", _offset_polygon(pts, d)
    return "rect", (x - d, y - d, w + 2 * d, h + 2 * d)


def _svg_shape(kind: str, geom, attrs: str) -> str:
    if kind == "ellipse":
        cx, cy, rx, ry = geom
        return f'<ellipse cx="{cx:.3f}" cy="{cy:.3f}" rx="{rx:.3f}" ry="{ry:.3f}" {attrs}/>'
    if kind == "polygon":
        pts = " ".join(f"{px:.3f},{py:.3f}" for px, py in geom)
        return f'<polygon points="{pts}" {attrs}/>'
    rx, ry, rw, rh = geom
    return f'<rect x="{rx:.3f}" y="{ry:.3f}" width="{rw:.3f}" height="{rh:.3f}" {attrs}/>'


def svg_fragment(
    stamp,
    x: float,
    y: float,
    w: float,
    h: float,
    color_hex: str = "#000000",
    fill_hex: str | None = "#ffffff",
) -> str:
    """SVG elements (user units = mm) for the stamp's fill and its frame lines."""
    shape = getattr(getattr(stamp, "shape", None), "name", "RECTANGLE")
    parts = []
    if fill_hex:
        kind, geom = outline(shape, x, y, w, h)
        parts.append(_svg_shape(kind, geom, f'class="stamp-fill" fill="{fill_hex}" stroke="none"'))
    for ln in lines(stamp):
        kind, geom = outline(shape, x, y, w, h, ln.offset)
        attrs = (
            f'class="frame-line" fill="none" stroke="{color_hex}" '
            f'stroke-width="{ln.width:.4f}" stroke-linejoin="miter"'
        )
        parts.append(_svg_shape(kind, geom, attrs))
    return "".join(parts)
