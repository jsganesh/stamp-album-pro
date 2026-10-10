"""
Stamp shape geometry shared by every renderer: HTML preview, PDF (ReportLab),
PNG (Pillow), SVG export, and the stamp frames (frames.py).
No drawing calls — pure data + coordinate math.

Page borders live in page_border.py.
"""

from __future__ import annotations

import math

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

def polygon_points(shape_name: str, x: float, y: float, w: float, h: float) -> list[tuple[float, float]]:
    """Vertices of a stamp shape fitted to the box (x, y, w, h), top-left origin, y down.

    Single source of truth: the canvas, the HTML preview and every export use
    the same 100x100 outlines (SHAPE_POLYGON_VIEWBOX), so shapes match everywhere.
    Returns [] for shapes that are not polygons (rectangle, oval).
    """
    spec = SHAPE_POLYGON_VIEWBOX.get(shape_name)
    if not spec:
        return []
    pts = []
    for pair in spec.split():
        px, py = pair.split(",")
        pts.append((x + float(px) / 100.0 * w, y + float(py) / 100.0 * h))
    return pts


SHAPE_POLYGON_NAMES: dict[str, str] = {
    "TRIANGLE": "TRIANGLE",
    "TRIANGLE_INV": "TRIANGLE_INV",
    "DIAMOND": "DIAMOND",
    "HEXAGON": "HEXAGON",
    "OCTAGON": "OCTAGON",
    "PENTAGON": "PENTAGON",
}

