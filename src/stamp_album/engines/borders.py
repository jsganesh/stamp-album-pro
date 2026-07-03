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


# ── SVG string builders (used by HTMLRenderer + SVG export) ──

def corner_ornament_svg(style: str, color: str = "#333") -> str:
    """Generate SVG fragment for a TL-oriented corner ornament."""
    if style == "classic":
        return (
            '<path d="M5,80 Q5,20 20,20 Q40,20 45,5 Q50,0 60,0" fill="none" stroke="'
            + color + '" stroke-width="1.2"/>'
            '<path d="M5,60 Q5,15 15,10 Q30,5 35,2" fill="none" stroke="'
            + color + '" stroke-width="0.8"/>'
            '<circle cx="8" cy="8" r="2" fill="' + color + '"/>'
            '<circle cx="20" cy="5" r="1.2" fill="' + color + '"/>'
        )
    if style == "victorian":
        return (
            '<path d="M0,85 C10,85 15,70 25,60 C35,50 30,35 20,25 '
            'C15,20 10,15 5,10 C10,12 15,18 25,22 C35,26 40,20 35,10" '
            'fill="none" stroke="' + color + '" stroke-width="1.2"/>'
            '<path d="M0,75 C8,75 12,65 20,58 C28,51 25,40 18,32 '
            'C14,28 10,24 8,18" fill="none" stroke="' + color + '" stroke-width="0.7"/>'
            '<circle cx="5" cy="5" r="2.5" fill="' + color + '"/>'
            '<circle cx="15" cy="12" r="1.5" fill="' + color + '"/>'
            '<circle cx="25" cy="8" r="1" fill="' + color + '"/>'
        )
    if style == "artdeco":
        return (
            '<rect x="0" y="60" width="40" height="3" fill="' + color + '"/>'
            '<rect x="0" y="50" width="30" height="3" fill="' + color + '"/>'
            '<rect x="0" y="40" width="20" height="3" fill="' + color + '"/>'
            '<rect x="0" y="30" width="10" height="3" fill="' + color + '"/>'
            '<rect x="40" y="60" width="3" height="25" fill="' + color + '"/>'
            '<rect x="30" y="50" width="3" height="15" fill="' + color + '"/>'
            '<rect x="20" y="40" width="3" height="5" fill="' + color + '"/>'
        )
    if style == "laurel":
        return (
            '<path d="M5,80 Q15,60 10,40 Q8,30 15,20" fill="none" stroke="'
            + color + '" stroke-width="1"/>'
            '<ellipse cx="12" cy="35" rx="4" ry="2.5" fill="' + color + '"'
            ' transform="rotate(-30 12 35)"/>'
            '<ellipse cx="8" cy="45" rx="4" ry="2.5" fill="' + color + '"'
            ' transform="rotate(-20 8 45)"/>'
            '<ellipse cx="15" cy="55" rx="4" ry="2.5" fill="' + color + '"'
            ' transform="rotate(-40 15 55)"/>'
            '<ellipse cx="18" cy="28" rx="3.5" ry="2" fill="' + color + '"'
            ' transform="rotate(-45 18 28)"/>'
            '<circle cx="14" cy="22" r="1.5" fill="' + color + '"/>'
            '<circle cx="10" cy="50" r="1.2" fill="' + color + '"/>'
        )
    if style == "gothic":
        return (
            '<path d="M0,85 L0,40 Q0,20 15,10 Q25,3 30,0" fill="none" stroke="'
            + color + '" stroke-width="1.5"/>'
            '<path d="M5,85 L5,45 Q5,28 18,18 Q25,12 28,8" fill="none" stroke="'
            + color + '" stroke-width="0.8"/>'
            '<path d="M15,0 Q20,5 22,12" fill="none" stroke="'
            + color + '" stroke-width="0.6"/>'
        )
    if style == "filigree":
        return (
            '<circle cx="20" cy="20" r="15" fill="none" stroke="'
            + color + '" stroke-width="0.8"/>'
            '<circle cx="20" cy="20" r="10" fill="none" stroke="'
            + color + '" stroke-width="0.5"/>'
            '<circle cx="20" cy="20" r="5" fill="none" stroke="'
            + color + '" stroke-width="0.5"/>'
            '<circle cx="20" cy="20" r="2" fill="' + color + '"/>'
            '<path d="M20,35 Q25,50 30,65" fill="none" stroke="'
            + color + '" stroke-width="0.6"/>'
            '<path d="M35,20 Q50,25 65,30" fill="none" stroke="'
            + color + '" stroke-width="0.6"/>'
            '<circle cx="30" cy="30" r="1.5" fill="' + color + '"/>'
            '<circle cx="35" cy="35" r="1" fill="' + color + '"/>'
        )
    return ""


def edge_pattern_svg(
    style: str, edge: str, w: float, h: float, color: str,
) -> str:
    """Generate SVG fragment for an edge pattern along one side."""
    svg = ""
    is_v = edge in ("left", "right")
    disp_len = h if is_v else w

    if style == "greek_key":
        step = 12
        count = int(disp_len / step)
        for i in range(count):
            offset = i * step
            if is_v:
                svg += (
                    f'<path d="M0,{offset} l0,3 l3,0 l0,6 l-3,0 l0,3"'
                    f' fill="none" stroke="{color}" stroke-width="0.8"/>'
                )
            else:
                svg += (
                    f'<path d="M{offset},0 l3,0 l0,3 l6,0 l0,-3 l3,0"'
                    f' fill="none" stroke="{color}" stroke-width="0.8"/>'
                )
    elif style == "rope":
        rstep = 8
        count = int(disp_len / rstep)
        for j in range(count):
            if is_v:
                svg += (
                    f'<circle cx="2" cy="{j * rstep + rstep / 2}" r="2"'
                    f' fill="none" stroke="{color}" stroke-width="0.7"/>'
                )
            else:
                svg += (
                    f'<circle cx="{j * rstep + rstep / 2}" cy="2" r="2"'
                    f' fill="none" stroke="{color}" stroke-width="0.7"/>'
                )
    return svg
