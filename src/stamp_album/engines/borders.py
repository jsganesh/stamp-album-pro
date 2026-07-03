"""
Shared geometry data for stamp album page rendering.

Single source of truth for shapes, ornaments, and edge patterns used by
all renderers: HTML preview, PDF (ReportLab), PNG (Pillow), SVG export.
No drawing calls — pure data + coordinate math.
"""

from __future__ import annotations

import math

# ── Style constants ──

ORNAMENTAL_STYLES: set[str] = {
    "classic", "victorian", "artdeco", "laurel", "gothic", "filigree",
}

EDGE_STYLES: set[str] = {"greek_key", "rope"}

ORNAMENT_BBOX: dict[str, tuple[float, float]] = {
    "classic": (62, 82),
    "victorian": (42, 87),
    "artdeco": (43, 85),
    "laurel": (22, 62),
    "gothic": (32, 85),
    "filigree": (65, 65),
}

BORDER_STYLE_META: dict[str, dict] = {
    "none": {"name": "None", "description": "No border"},
    "solid": {"name": "Solid", "description": "Simple solid line"},
    "double": {"name": "Double", "description": "Double-line rule"},
    "dashed": {"name": "Dashed", "description": "Dashed line border"},
    "dotted": {"name": "Dotted", "description": "Dotted line border"},
    "classic": {
        "name": "Classic Ornate",
        "description": "Victorian-style corner flourishes with double rule",
        "corners": True,
        "pattern": "double",
        "color": "#8B0000",
    },
    "victorian": {
        "name": "Victorian Filigree",
        "description": "Elaborate Victorian scrollwork corners",
        "corners": True,
        "pattern": "ornate",
        "color": "#4A3728",
    },
    "artdeco": {
        "name": "Art Deco",
        "description": "Geometric 1920s-style stepped corners",
        "corners": True,
        "pattern": "geometric",
        "color": "#1A3A6B",
    },
    "greek_key": {
        "name": "Greek Key",
        "description": "Meander / Greek key pattern along edges",
        "corners": False,
        "pattern": "meander",
        "color": "#2C2C2C",
    },
    "rope": {
        "name": "Rope Twist",
        "description": "Twisted rope border pattern",
        "corners": False,
        "pattern": "rope",
        "color": "#6B4423",
    },
    "laurel": {
        "name": "Laurel Wreath",
        "description": "Leaf and berry corner ornaments",
        "corners": True,
        "pattern": "laurel",
        "color": "#2D5016",
    },
    "gothic": {
        "name": "Gothic Arch",
        "description": "Gothic cathedral-inspired pointed arches",
        "corners": True,
        "pattern": "gothic",
        "color": "#333",
    },
    "filigree": {
        "name": "Filigree Gold",
        "description": "Delicate gold filigree with corner rosettes",
        "corners": True,
        "pattern": "filigree",
        "color": "#B8860B",
    },
}


# ── Shape geometry ──

def regular_polygon_vertices(
    cx: float, cy: float, rx: float, ry: float, n: int
) -> list[tuple[float, float]]:
    """Generate (x, y) vertices for a regular n-gon centered at (cx, cy)."""
    pts: list[tuple[float, float]] = []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        pts.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
    return pts


# SVG viewBox polygon point strings for a 100×100 grid (used by HTMLRenderer).
SHAPE_POLYGON_VIEWBOX: dict[str, str] = {
    "TRIANGLE": "50,0 100,100 0,100",
    "TRIANGLE_INV": "0,0 100,0 50,100",
    "DIAMOND": "50,0 100,50 50,100 0,50",
    "HEXAGON": "25,0 75,0 100,50 75,100 25,100 0,50",
    "OCTAGON": "30,0 70,0 100,30 100,70 70,100 30,100 0,70 0,30",
    "PENTAGON": "50,0 100,38 82,100 18,100 0,38",
}

SHAPE_POLYGON_NAMES: dict[str, str] = {
    "TRIANGLE": "TRIANGLE",
    "TRIANGLE_INV": "TRIANGLE_INV",
    "DIAMOND": "DIAMOND",
    "HEXAGON": "HEXAGON",
    "OCTAGON": "OCTAGON",
    "PENTAGON": "PENTAGON",
}


# ── Ornament segment data ──
#
# Each ornament style is a list of segments.  Segments are tuples:
#   ("L", x1, y1, x2, y2)            — line
#   ("Q", x1, y1, cx, cy, x2, y2)    — quadratic bezier
#   ("C", x1, y1, cp1x, cp1y, cp2x, cp2y, x2, y2) — cubic bezier
#   ("circle", cx, cy, r, fill?)      — circle (fill=True/False)
#   ("rect", x, y, w, h, fill?)       — filled rectangle
#   ("ellipse", cx, cy, rx, ry, fill?) — ellipse (fill=True/False)
#
# Coordinates are in a local space (~0–85 range).  Renderers apply
# their own position/scale/flip transforms.

_ORNAMENT_CLASSIC: list[tuple] = [
    ("Q", 5, 80, 5, 20, 20, 20),
    ("Q", 40, 20, 45, 5, 50, 0),
    ("L", 50, 0, 60, 0),
    ("Q", 5, 60, 5, 15, 15, 10),
    ("Q", 30, 5, 35, 2, 35, 2),
    ("circle", 8, 8, 2, True),
    ("circle", 20, 5, 1.2, True),
]

_ORNAMENT_VICTORIAN: list[tuple] = [
    ("C", 0, 85, 10, 85, 15, 70, 25, 60),
    ("C", 35, 50, 30, 35, 20, 25, 20, 25),
    ("C", 15, 20, 10, 15, 5, 10, 5, 10),
    ("C", 10, 12, 15, 18, 25, 22, 25, 22),
    ("C", 35, 26, 40, 20, 35, 10, 35, 10),
    ("C", 0, 75, 8, 75, 12, 65, 20, 58),
    ("C", 28, 51, 25, 40, 18, 32, 18, 32),
    ("C", 14, 28, 10, 24, 8, 18, 8, 18),
    ("circle", 5, 5, 2.5, True),
    ("circle", 15, 12, 1.5, True),
    ("circle", 25, 8, 1, True),
]

_ORNAMENT_ARTDECO: list[tuple] = [
    ("rect", 0, 60, 40, 3, True),
    ("rect", 0, 50, 30, 3, True),
    ("rect", 0, 40, 20, 3, True),
    ("rect", 0, 30, 10, 3, True),
    ("rect", 40, 60, 3, 25, True),
    ("rect", 30, 50, 3, 15, True),
    ("rect", 20, 40, 3, 5, True),
]

_ORNAMENT_LAUREL: list[tuple] = [
    ("Q", 5, 80, 15, 60, 10, 40),
    ("Q", 8, 30, 15, 20, 15, 20),
    ("ellipse", 12, 35, 4, 2.5, True),
    ("ellipse", 8, 45, 4, 2.5, True),
    ("ellipse", 15, 55, 4, 2.5, True),
    ("ellipse", 18, 28, 3.5, 2, True),
    ("circle", 14, 22, 1.5, True),
    ("circle", 10, 50, 1.2, True),
]

_ORNAMENT_GOTHIC: list[tuple] = [
    ("L", 0, 85, 0, 40),
    ("Q", 0, 40, 0, 20, 15, 10),
    ("Q", 25, 3, 30, 0, 30, 0),
    ("L", 5, 85, 5, 45),
    ("Q", 5, 45, 5, 28, 18, 18),
    ("Q", 25, 12, 28, 8, 28, 8),
    ("Q", 15, 0, 20, 5, 22, 12),
]

_ORNAMENT_FILIGREE: list[tuple] = [
    ("circle", 20, 20, 15, False),
    ("circle", 20, 20, 10, False),
    ("circle", 20, 20, 5, False),
    ("circle", 20, 20, 2, True),
    ("Q", 20, 35, 25, 50, 30, 65),
    ("Q", 35, 20, 50, 25, 65, 30),
    ("circle", 30, 30, 1.5, True),
    ("circle", 35, 35, 1, True),
]

_ORNAMENT_SEGMENTS: dict[str, list[tuple]] = {
    "classic": _ORNAMENT_CLASSIC,
    "victorian": _ORNAMENT_VICTORIAN,
    "artdeco": _ORNAMENT_ARTDECO,
    "laurel": _ORNAMENT_LAUREL,
    "gothic": _ORNAMENT_GOTHIC,
    "filigree": _ORNAMENT_FILIGREE,
}


def get_ornament_segments(style: str) -> list[tuple]:
    """Return ornament path segments for a given style.

    Coordinate system: local (~0–85 range).  Renderers apply
    position/scale/flip transforms.
    """
    return _ORNAMENT_SEGMENTS.get(style, [])


# ── Edge pattern generators ──

def edge_pattern_segments(
    style: str, edge: str, length: float,
) -> list[tuple]:
    """Generate segments for an edge pattern along one side.

    *style* — ``"greek_key"`` or ``"rope"``
    *edge*  — ``"top"``, ``"bottom"``, ``"left"``, ``"right"``
    *length* — available length in the pattern's local coordinate space
               (CSS pixels for SVG, points for ReportLab, etc.)

    Returns list of ``(cmd, *args)`` segments.
    """
    is_v = edge in ("left", "right")
    segments: list[tuple] = []

    if style == "greek_key":
        step = 12
        count = int(length / step)
        for i in range(count):
            offset = i * step
            if is_v:
                segments.append(
                    ("L", 0, offset, 0, offset + 3)
                )
                segments.append(
                    ("L", 0, offset + 3, 3, offset + 3)
                )
                segments.append(
                    ("L", 3, offset + 3, 3, offset + 9)
                )
                segments.append(
                    ("L", 3, offset + 9, 0, offset + 9)
                )
                segments.append(
                    ("L", 0, offset + 9, 0, offset + 12)
                )
            else:
                segments.append(
                    ("L", offset, 0, offset + 3, 0)
                )
                segments.append(
                    ("L", offset + 3, 0, offset + 3, 3)
                )
                segments.append(
                    ("L", offset + 3, 3, offset + 9, 3)
                )
                segments.append(
                    ("L", offset + 9, 3, offset + 9, 0)
                )
                segments.append(
                    ("L", offset + 9, 0, offset + 12, 0)
                )

    elif style == "rope":
        rstep = 8
        count = int(length / rstep)
        for j in range(count):
            if is_v:
                segments.append(
                    ("circle", 2, j * rstep + rstep / 2, 2, False)
                )
            else:
                segments.append(
                    ("circle", j * rstep + rstep / 2, 2, 2, False)
                )

    return segments


# ── SVG fragment builder from segments ──

def segments_to_svg_fragment(
    segments: list[tuple], color: str, stroke_width: float = 1.0
) -> str:
    """Convert segment tuples to SVG fragment string.

    Each segment is an independent drawing operation.  Path commands (L/Q/C)
    are accumulated into ``<path d="…">`` elements, inserting a move-to (M)
    whenever a segment's start does not match the previous segment's end.
    Shape primitives (circle / rect / ellipse) flush the current path and
    emit their own element.
    """
    parts: list[str] = []
    path_cmds: list[str] = []

    def flush_path():
        if path_cmds:
            d = " ".join(path_cmds)
            parts.append(
                f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{stroke_width}"/>'
            )
            path_cmds.clear()

    prev_end: tuple[float, float] | None = None

    def maybe_move(x: float, y: float) -> str:
        nonlocal prev_end
        gap = prev_end is None or abs(x - prev_end[0]) > 0.01 or abs(y - prev_end[1]) > 0.01
        return f"M{x},{y}" if gap else ""

    for seg in segments:
        cmd = seg[0]
        if cmd == "L":
            _, x1, y1, x2, y2 = seg
            m = maybe_move(x1, y1)
            path_cmds.append(f"{m}L{x2},{y2}")
            prev_end = (x2, y2)
        elif cmd == "Q":
            _, x1, y1, cx, cy, x2, y2 = seg
            m = maybe_move(x1, y1)
            path_cmds.append(f"{m}Q{cx},{cy} {x2},{y2}")
            prev_end = (x2, y2)
        elif cmd == "C":
            _, x1, y1, c1x, c1y, c2x, c2y, x2, y2 = seg
            m = maybe_move(x1, y1)
            path_cmds.append(f"{m}C{c1x},{c1y} {c2x},{c2y} {x2},{y2}")
            prev_end = (x2, y2)
        else:
            flush_path()
            prev_end = None
            if cmd == "circle":
                _, cx, cy, r, fill = seg
                f = color if fill else "none"
                parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{f}" '
                    f'stroke="{color}" stroke-width="{stroke_width}"/>'
                )
            elif cmd == "rect":
                _, x, y, w, h, fill = seg
                f = color if fill else "none"
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{f}" '
                    f'stroke="{color}" stroke-width="{stroke_width}"/>'
                )
            elif cmd == "ellipse":
                _, cx, cy, rx, ry, fill = seg
                f = color if fill else "none"
                parts.append(
                    f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{f}" '
                    f'stroke="{color}" stroke-width="{stroke_width}"/>'
                )

    flush_path()
    return "".join(parts)


# ── SVG string builders (used by HTMLRenderer + SVG export) ──

def corner_ornament_svg(style: str, color: str = "#333") -> str:
    """Generate SVG fragment for a TL-oriented corner ornament from segment data."""
    segments = get_ornament_segments(style)
    if not segments:
        return ""
    return segments_to_svg_fragment(segments, color, stroke_width=1.0)


def edge_pattern_svg(
    style: str, edge: str, w: float, h: float, color: str,
) -> str:
    """Generate SVG fragment for an edge pattern along one side from segment data."""
    length = h if edge in ("left", "right") else w
    segments = edge_pattern_segments(style, edge, length)
    if not segments:
        return ""
    return segments_to_svg_fragment(segments, color, stroke_width=0.8)
