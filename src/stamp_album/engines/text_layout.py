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

# The built-in font ids: a family letter (H Helvetica, T Times, C Courier) and a face
# (N regular, B bold, I italic, S bold italic). The editor's fontCSS() in app.js draws
# the same families and faces; the PDF and PNG use the matching built-in fonts.
_CSS_FAMILY = {
    "H": "Helvetica,Arial,sans-serif",
    "T": "'Times New Roman',Times,serif",
    "C": "Courier,monospace",
}
_FACE = {"N": ("normal", "normal"), "B": ("bold", "normal"),
         "I": ("normal", "italic"), "S": ("bold", "italic")}


def css_font(font_id: str | None) -> tuple[str, str, str]:
    """``(family, weight, style)`` for a text element's font id, for CSS and SVG.

    Any other id is a font on this computer ("Georgia"), drawn in its regular face; one
    that isn't installed (or can't be embedded) draws as regular Helvetica, as in the PDF.
    """
    fid = font_id or "HN"
    if len(fid) == 2 and fid[0] in _CSS_FAMILY and fid[1] in _FACE:
        return (_CSS_FAMILY[fid[0]], *_FACE[fid[1]])
    from stamp_album.engines import system_fonts

    if system_fonts.find(fid):
        return (system_fonts.css_family(fid), "normal", "normal")
    return (_CSS_FAMILY["H"], "normal", "normal")


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
