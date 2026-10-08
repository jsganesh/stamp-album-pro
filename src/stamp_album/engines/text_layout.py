"""Shared layout for free-form text elements.

Every export engine (PDF, PNG, SVG) and the HTML preview must place text the
same way: wrapped to the box width, top-anchored, with the element's
alignment. The engines supply a ``measure(text) -> width`` function in the
unit they draw in; this module returns lines and x offsets in that unit.
"""

from __future__ import annotations

from typing import Callable

LINE_HEIGHT = 1.3      # line box height as a multiple of the font size
PAD_MM = 1.0           # inner padding of a text box (matches the HTML preview)
FIRST_BASELINE = 1.0   # first baseline below the padded top edge, in font sizes
PT_PER_MM = 72.0 / 25.4


def normalize_align(align: str | None) -> str:
    a = (align or "left").lower()
    if a in ("centre", "middle"):
        a = "center"
    return a if a in ("left", "center", "right", "justify") else "left"


def wrap_lines(text: str, max_width: float, measure: Callable[[str], float]) -> list[str]:
    """Greedy word wrap. Honours explicit newlines and breaks over-long words."""
    out: list[str] = []
    for para in (text or "").split("\n"):
        if not para.strip():
            out.append("")
            continue
        line = ""
        for word in para.split(" "):
            candidate = word if not line else line + " " + word
            if measure(candidate) <= max_width or not line:
                line = candidate
            else:
                out.append(line)
                line = word
            # a single word wider than the box: split it by characters
            while measure(line) > max_width and len(line) > 1:
                cut = len(line) - 1
                while cut > 1 and measure(line[:cut]) > max_width:
                    cut -= 1
                out.append(line[:cut])
                line = line[cut:]
        out.append(line)
    return out


def line_x(box_x: float, box_w: float, text_w: float, align: str, pad: float) -> float:
    """Left x of a line of width *text_w* inside a box with inner padding *pad*."""
    align = normalize_align(align)
    if align == "center":
        return box_x + (box_w - text_w) / 2
    if align == "right":
        return box_x + box_w - pad - text_w
    return box_x + pad
