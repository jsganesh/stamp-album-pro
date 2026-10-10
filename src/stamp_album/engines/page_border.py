"""Page borders: one drawing for every view.

The editor draws the page border (``renderPageBorder`` in ``web/borders.js``) as
SVG in canvas units, 2.5 per mm, so one unit is ``UNIT_MM``. This module builds
the same SVG (``page_border_markup`` ports ``renderPageBorder``,
``cornerOrnament`` and ``edgePattern`` line for line), then turns it into
primitives in page millimetres that every export draws the same way:

* ``Stroke(points, width, closed, dash)``: a line through points, ``width`` mm;
* ``Fill(points)``: a filled polygon.

Curves and circles are flattened, and dashes are cut into separate strokes
(``strokes_with_dashes``), so PDF, PNG, SVG and the preview draw identical
geometry. Keep the markup in step with ``web/borders.js``; a browser test
compares the two.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

UNITS_PER_MM = 2.5  # the editor's canvas scale
UNIT_MM = 1 / UNITS_PER_MM  # one editor canvas unit, 0.4 mm
MARGIN_U = 12  # page edge to the border, in units (4.8 mm)
INNER_U = 4  # outer rule to inner rule of a double border, in units

PLAIN_STYLES = ("solid", "double", "dashed", "dotted")
CORNER_STYLES = ("classic", "victorian", "artdeco", "laurel", "gothic", "filigree")
EDGE_STYLES = ("greek_key", "rope")
STYLES = PLAIN_STYLES + CORNER_STYLES + EDGE_STYLES


# ── The editor's drawing, ported from web/borders.js ──


def _n(v: float) -> str:
    """A number as JavaScript prints it (12, 718.5)."""
    return str(int(v)) if float(v).is_integer() else repr(float(v))


_CORNERS: dict[str, str] = {
    "classic": (
        '<path d="M5,80 Q5,20 20,20 Q40,20 45,5 Q50,0 60,0" fill="none" stroke="COLOR" '
        'stroke-width="1.2"/>'
        '<path d="M5,60 Q5,15 15,10 Q30,5 35,2" fill="none" stroke="COLOR" stroke-width="0.8"/>'
        '<circle cx="8" cy="8" r="2" fill="COLOR"/>'
        '<circle cx="20" cy="5" r="1.2" fill="COLOR"/>'
    ),
    "victorian": (
        '<path d="M0,85 C10,85 15,70 25,60 C35,50 30,35 20,25 C15,20 10,15 5,10 C10,12 15,18 25,22 '
        'C35,26 40,20 35,10" fill="none" stroke="COLOR" stroke-width="1.2"/>'
        '<path d="M0,75 C8,75 12,65 20,58 C28,51 25,40 18,32 C14,28 10,24 8,18" fill="none" '
        'stroke="COLOR" stroke-width="0.7"/>'
        '<circle cx="5" cy="5" r="2.5" fill="COLOR"/>'
        '<circle cx="15" cy="12" r="1.5" fill="COLOR"/>'
        '<circle cx="25" cy="8" r="1" fill="COLOR"/>'
    ),
    "artdeco": (
        '<rect x="0" y="60" width="40" height="3" fill="COLOR"/>'
        '<rect x="0" y="50" width="30" height="3" fill="COLOR"/>'
        '<rect x="0" y="40" width="20" height="3" fill="COLOR"/>'
        '<rect x="0" y="30" width="10" height="3" fill="COLOR"/>'
        '<rect x="40" y="60" width="3" height="25" fill="COLOR"/>'
        '<rect x="30" y="50" width="3" height="15" fill="COLOR"/>'
        '<rect x="20" y="40" width="3" height="5" fill="COLOR"/>'
    ),
    "laurel": (
        '<path d="M5,80 Q15,60 10,40 Q8,30 15,20" fill="none" stroke="COLOR" stroke-width="1"/>'
        '<ellipse cx="12" cy="35" rx="4" ry="2.5" fill="COLOR" transform="rotate(-30 12 35)"/>'
        '<ellipse cx="8" cy="45" rx="4" ry="2.5" fill="COLOR" transform="rotate(-20 8 45)"/>'
        '<ellipse cx="15" cy="55" rx="4" ry="2.5" fill="COLOR" transform="rotate(-40 15 55)"/>'
        '<ellipse cx="18" cy="28" rx="3.5" ry="2" fill="COLOR" transform="rotate(-45 18 28)"/>'
        '<circle cx="14" cy="22" r="1.5" fill="COLOR"/>'
        '<circle cx="10" cy="50" r="1.2" fill="COLOR"/>'
    ),
    "gothic": (
        '<path d="M0,85 L0,40 Q0,20 15,10 Q25,3 30,0" fill="none" stroke="COLOR" '
        'stroke-width="1.5"/>'
        '<path d="M5,85 L5,45 Q5,28 18,18 Q25,12 28,8" fill="none" stroke="COLOR" '
        'stroke-width="0.8"/>'
        '<path d="M15,0 Q20,5 22,12" fill="none" stroke="COLOR" stroke-width="0.6"/>'
    ),
    "filigree": (
        '<circle cx="20" cy="20" r="15" fill="none" stroke="COLOR" stroke-width="0.8"/>'
        '<circle cx="20" cy="20" r="10" fill="none" stroke="COLOR" stroke-width="0.5"/>'
        '<circle cx="20" cy="20" r="5" fill="none" stroke="COLOR" stroke-width="0.5"/>'
        '<circle cx="20" cy="20" r="2" fill="COLOR"/>'
        '<path d="M20,35 Q25,50 30,65" fill="none" stroke="COLOR" stroke-width="0.6"/>'
        '<path d="M35,20 Q50,25 65,30" fill="none" stroke="COLOR" stroke-width="0.6"/>'
        '<circle cx="30" cy="30" r="1.5" fill="COLOR"/>'
        '<circle cx="35" cy="35" r="1" fill="COLOR"/>'
    ),
}
_CORNER_TRANSFORMS = {"tl": "", "tr": "scale(-1,1)", "br": "scale(-1,-1)", "bl": "scale(1,-1)"}


def corner_ornament(style: str, corner: str) -> str:
    """``cornerOrnament`` in borders.js."""
    body = _CORNERS.get(style)
    if body is None:
        return ""
    return f'<g transform="{_CORNER_TRANSFORMS.get(corner, "")}">{body}</g>'


def edge_pattern(style: str, edge: str, w: float, color: str) -> str:
    """``edgePattern`` in borders.js (``w`` is the length along the edge, in units)."""
    out = []
    vertical = edge in ("left", "right")
    if style == "greek_key":
        step = 12
        for i in range(int(math.floor(w / step))):
            o = i * step
            if vertical:
                d = f"M0,{_n(o)} l0,3 l3,0 l0,6 l-3,0 l0,3"
            else:
                d = f"M{_n(o)},0 l3,0 l0,3 l6,0 l0,-3 l3,0"
            out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="0.8"/>')
    elif style == "rope":
        step = 8
        for j in range(int(math.floor(w / step))):
            c = _n(j * step + step / 2)
            cx, cy = ("2", c) if vertical else (c, "2")
            out.append(
                f'<circle cx="{cx}" cy="{cy}" r="2" fill="none" stroke="{color}" '
                'stroke-width="0.7"/>'
            )
    return "".join(out)


def _rect(x, y, w, h, color, width, dash=None) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" fill="none" '
        f'stroke="{color}" stroke-width="{width}"{extra}/>'
    )


def page_border_markup(style: str, w: float, h: float, color: str) -> str:
    """``renderPageBorder`` in borders.js: SVG for a page ``w`` x ``h`` units."""
    m = MARGIN_U
    if style == "solid":
        return _rect(m, m, w - m * 2, h - m * 2, color, "1")
    if style == "double" or style in CORNER_STYLES:
        out = _rect(m, m, w - m * 2, h - m * 2, color, "1.2") + _rect(
            m + INNER_U, m + INNER_U, w - m * 2 - 2 * INNER_U, h - m * 2 - 2 * INNER_U, color, "0.5"
        )
        if style in CORNER_STYLES:
            corners = {"tl": (m, m), "tr": (w - m, m), "br": (w - m, h - m), "bl": (m, h - m)}
            for c in ("tl", "tr", "br", "bl"):
                orn = corner_ornament(style, c).replace("COLOR", color)
                out += (
                    f'<g transform="translate({_n(corners[c][0])},{_n(corners[c][1])})">{orn}</g>'
                )
        return out
    if style == "dashed":
        return _rect(m, m, w - m * 2, h - m * 2, color, "1", "6,3")
    if style == "dotted":
        return _rect(m, m, w - m * 2, h - m * 2, color, "1.2", "2,3")
    if style in EDGE_STYLES:
        ew, eh = w - m * 2, h - m * 2
        top = edge_pattern(style, "top", ew, color)
        bottom = edge_pattern(style, "bottom", ew, color)
        left = edge_pattern(style, "left", eh, color)
        right = edge_pattern(style, "right", eh, color)
        return (
            f'<g transform="translate({_n(m)},{_n(m)})">{top}</g>'
            f'<g transform="translate({_n(m)},{_n(h - m)}) scale(1,-1)">{bottom}</g>'
            f'<g transform="translate({_n(m)},{_n(m)})">{left}</g>'
            f'<g transform="translate({_n(w - m)},{_n(m)}) scale(-1,1)">{right}</g>'
        )
    return ""


# ── Primitives ──


@dataclass
class Stroke:
    points: list[tuple[float, float]]
    width: float  # mm
    closed: bool = False
    dash: tuple[float, ...] = field(default_factory=tuple)  # on, off, … in mm


@dataclass
class Fill:
    points: list[tuple[float, float]]


Matrix = tuple[float, float, float, float, float, float]  # a b c d e f, as in SVG
_IDENTITY: Matrix = (1, 0, 0, 1, 0, 0)


def _mul(m: Matrix, n: Matrix) -> Matrix:
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (
        a * a2 + c * b2,
        b * a2 + d * b2,
        a * c2 + c * d2,
        b * c2 + d * d2,
        a * e2 + c * f2 + e,
        b * e2 + d * f2 + f,
    )


def _apply(m: Matrix, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f


def _parse_transform(text: str | None) -> Matrix:
    m = _IDENTITY
    for name, args in re.findall(r"(\w+)\(([^)]*)\)", text or ""):
        v = [float(t) for t in re.split(r"[\s,]+", args.strip()) if t]
        if name == "translate":
            n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            n = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate":
            r = math.radians(v[0])
            cx, cy = (v[1], v[2]) if len(v) > 2 else (0.0, 0.0)
            n = _mul(
                _mul(
                    (1, 0, 0, 1, cx, cy),
                    (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0),
                ),
                (1, 0, 0, 1, -cx, -cy),
            )
        else:
            continue
        m = _mul(m, n)
    return m


def _path_points(d: str) -> list[list[tuple[float, float]]]:
    """Flatten an SVG path (M, L, Q, C and their relative forms) into polylines."""
    tokens = re.findall(r"[MLQCmlqc]|-?\d*\.?\d+(?:e-?\d+)?", d)
    lines: list[list[tuple[float, float]]] = []
    x = y = 0.0
    i, cmd = 0, "M"
    steps = 16
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
        rel = cmd.islower()
        need = {"m": 2, "l": 2, "q": 4, "c": 6}[cmd.lower()]
        v = [float(t) for t in tokens[i : i + need]]
        i += need
        if rel:
            v = [t + (x if k % 2 == 0 else y) for k, t in enumerate(v)]
        if cmd.lower() == "m":
            x, y = v
            lines.append([(x, y)])
            cmd = "l" if rel else "L"  # extra pairs after a move are lines
            continue
        pts = lines[-1]
        if cmd.lower() == "l":
            x, y = v
            pts.append((x, y))
        elif cmd.lower() == "q":
            (cx, cy, ex, ey), (sx, sy) = v, (x, y)
            for s in range(1, steps + 1):
                t = s / steps
                pts.append(
                    (
                        (1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t * t * ex,
                        (1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t * t * ey,
                    )
                )
            x, y = ex, ey
        else:
            (c1x, c1y, c2x, c2y, ex, ey), (sx, sy) = v, (x, y)
            for s in range(1, steps + 1):
                t = s / steps
                u = 1 - t
                pts.append(
                    (
                        u**3 * sx + 3 * u * u * t * c1x + 3 * u * t * t * c2x + t**3 * ex,
                        u**3 * sy + 3 * u * u * t * c1y + 3 * u * t * t * c2y + t**3 * ey,
                    )
                )
            x, y = ex, ey
    return lines


def _ellipse_points(cx: float, cy: float, rx: float, ry: float, n: int = 48):
    return [
        (cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n))
        for k in range(n)
    ]


def markup_primitives(markup: str, unit_mm: float = UNIT_MM) -> list:
    """Strokes and fills (page mm) for SVG markup in editor units."""
    root = ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{markup}</svg>')
    out: list = []

    def walk(el, m: Matrix):
        m = _mul(m, _parse_transform(el.get("transform")))
        tag = el.tag.split("}")[-1]
        shapes: list[tuple[list, bool]] = []  # (points, closed)
        if tag == "path":
            shapes = [(p, False) for p in _path_points(el.get("d", ""))]
        elif tag == "circle":
            r = float(el.get("r", 0))
            shapes = [(_ellipse_points(float(el.get("cx", 0)), float(el.get("cy", 0)), r, r), True)]
        elif tag == "ellipse":
            shapes = [
                (
                    _ellipse_points(
                        float(el.get("cx", 0)),
                        float(el.get("cy", 0)),
                        float(el.get("rx", 0)),
                        float(el.get("ry", 0)),
                    ),
                    True,
                )
            ]
        elif tag == "rect":
            x, y = float(el.get("x", 0)), float(el.get("y", 0))
            w, h = float(el.get("width", 0)), float(el.get("height", 0))
            shapes = [([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True)]
        for pts, closed in shapes:
            page = [(px * unit_mm, py * unit_mm) for px, py in (_apply(m, *p) for p in pts)]
            fill = el.get("fill", "none")
            if fill not in ("none", "transparent") and closed:
                out.append(Fill(page))
            stroke = el.get("stroke", "none")
            if stroke not in ("none", "transparent"):
                dash = el.get("stroke-dasharray")
                out.append(
                    Stroke(
                        page,
                        float(el.get("stroke-width", 1)) * unit_mm,
                        closed,
                        tuple(float(t) * unit_mm for t in re.split(r"[\s,]+", dash.strip()))
                        if dash
                        else (),
                    )
                )
        for child in el:
            walk(child, m)

    for child in root:
        walk(child, _IDENTITY)
    return out


def primitives(style: str, page_w_mm: float, page_h_mm: float) -> list:
    """The page border for *style* on a page ``page_w_mm`` x ``page_h_mm``, in page mm."""
    if style not in STYLES:
        return []
    w, h = page_w_mm * UNITS_PER_MM, page_h_mm * UNITS_PER_MM
    return markup_primitives(page_border_markup(style, w, h, "#000"))


def strokes_with_dashes(prims: list) -> list:
    """Primitives with every dashed stroke cut into its dashes (open strokes)."""
    out: list = []
    for p in prims:
        if not isinstance(p, Stroke) or not p.dash:
            out.append(p)
            continue
        pts = p.points + ([p.points[0]] if p.closed else [])
        pattern, k, left, on = p.dash, 0, p.dash[0], True
        current = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            seg = math.hypot(bx - ax, by - ay)
            pos = 0.0
            while seg - pos > left:
                pos += left
                pt = (ax + (bx - ax) * pos / seg, ay + (by - ay) * pos / seg)
                if on:
                    current.append(pt)
                    out.append(Stroke(current, p.width))
                else:
                    current = [pt]
                on = not on
                k = (k + 1) % len(pattern)
                left = pattern[k]
            left -= seg - pos
            if on:
                current.append((bx, by))
        if on and len(current) > 1:
            out.append(Stroke(current, p.width))
    return out


def page_primitives(album) -> list:
    """The album's page border with dashes cut, or [] when it has none of the shared styles."""
    ps = album.page_setup
    if not ps.has_border or ps.border_style not in STYLES:
        return []
    return strokes_with_dashes(primitives(ps.border_style, ps.width, ps.height))


def svg_elements(prims: list, color: str) -> str:
    """SVG (user units = mm) for primitives, as the SVG export and the preview draw them."""
    out = []
    for p in prims:
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in p.points)
        if isinstance(p, Fill):
            out.append(f'<polygon points="{pts}" fill="{color}" stroke="none"/>')
        else:
            tag = "polygon" if p.closed else "polyline"
            out.append(
                f'<{tag} points="{pts}" fill="none" stroke="{color}" stroke-width="{p.width:.4f}" '
                f'stroke-linejoin="miter" stroke-linecap="butt"/>'
            )
    return "".join(out)
