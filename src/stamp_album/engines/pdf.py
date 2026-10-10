"""
ReportLab-based PDF generation engine.

Replaced the former PyMuPDF-based engine, which has been removed.
Uses borders.py for shared geometry data.
"""

from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from stamp_album.core.models import Album, Color, Stamp
from stamp_album.engines import caption_layout, frames, page_border, text_layout
from stamp_album.engines.layout import layout_rows


# ── Font resolution ──

_BUILTIN_FONT_MAP = {
    "CN": "Courier",
    "CB": "Courier-Bold",
    "CI": "Courier-Oblique",
    "CS": "Courier-BoldOblique",
    "TN": "Times-Roman",
    "TB": "Times-Bold",
    "TI": "Times-Italic",
    "TS": "Times-BoldItalic",
    "HN": "Helvetica",
    "HB": "Helvetica-Bold",
    "HI": "Helvetica-Oblique",
    "HS": "Helvetica-BoldOblique",
}


def _get_system_font_dirs():
    import platform
    system = platform.system()
    if system == "Darwin":
        return [
            Path("/Library/Fonts"),
            Path.home() / "Library/Fonts",
            Path("/System/Library/Fonts"),
        ]
    return [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".fonts"]


def _resolve_reportlab_font(font_id: str, c: canvas.Canvas) -> str:
    """Resolve a font ID to a ReportLab registered font name."""
    if font_id in _BUILTIN_FONT_MAP:
        return _BUILTIN_FONT_MAP[font_id]
    # Try to find and register a TTF
    for d in _get_system_font_dirs():
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if f.suffix.lower() in (".ttf", ".ttc", ".otf"):
                stem = f.stem.lower().replace(" ", "")
                fid = font_id.lower()
                if fid in stem or stem in fid:
                    try:
                        name = f"F{font_id}"
                        pdfmetrics.registerFont(TTFont(name, str(f)))
                        return name
                    except Exception:
                        continue
    return "Helvetica"


def _mm_to_pt(value: float) -> float:
    return value * 72.0 / 25.4


def _color_to_rgb(color: Optional[Color]) -> tuple[float, float, float]:
    if color is None:
        return (0, 0, 0)
    return (max(0, min(1, color.r)), max(0, min(1, color.g)), max(0, min(1, color.b)))


def _resolve_image_path(image_path: Optional[str]) -> Optional[Path]:
    if not image_path:
        return None
    fname = image_path.split("/")[-1].split("\\")[-1]
    p = Path.home() / "StampAlbum" / "images" / fname
    return p if p.is_file() else None


# ── Drawing helpers ──

def _set_color(c: canvas.Canvas, rgb: tuple[float, float, float], alpha: float = 1.0):
    c.setFillColorRGB(rgb[0], rgb[1], rgb[2], alpha)
    c.setStrokeColorRGB(rgb[0], rgb[1], rgb[2], alpha)


def _pdf_outline(c: canvas.Canvas, kind: str, geom, page_h: float, fill: int, stroke: int):
    """Draw a frames.outline() shape (mm, y down) on the PDF canvas (points, y up)."""
    pt = _mm_to_pt
    if kind == "ellipse":
        cx, cy, rx, ry = geom
        c.ellipse(pt(cx - rx), page_h - pt(cy + ry), pt(cx + rx), page_h - pt(cy - ry),
                  fill=fill, stroke=stroke)
    elif kind == "polygon":
        p = c.beginPath()
        p.moveTo(pt(geom[0][0]), page_h - pt(geom[0][1]))
        for vx, vy in geom[1:]:
            p.lineTo(pt(vx), page_h - pt(vy))
        p.close()
        c.drawPath(p, fill=fill, stroke=stroke)
    else:
        rx, ry, rw, rh = geom
        c.rect(pt(rx), page_h - pt(ry + rh), pt(rw), pt(rh), fill=fill, stroke=stroke)


def _draw_stamp_shape(
    c: canvas.Canvas,
    stamp: Stamp,
    x: float, y: float, w: float, h: float,
    page_h: float,
    border_rgb: tuple[float, float, float],
    fill_rgb: tuple[float, float, float],
):
    """Fill the stamp's own outline, then draw its frame outside it (see frames.py).

    (x, y, w, h) are mm from the page's top-left corner; *page_h* is the page height in points.
    """
    shape = stamp.shape.name if stamp.shape else "RECTANGLE"
    c.saveState()
    c.setFillColorRGB(*fill_rgb)
    _pdf_outline(c, *frames.outline(shape, x, y, w, h), page_h, fill=1, stroke=0)
    c.setStrokeColorRGB(*border_rgb)
    c.setLineJoin(0)  # mitred corners, as the outline is mitred
    for ln in frames.lines(stamp):
        c.setLineWidth(_mm_to_pt(ln.width))
        _pdf_outline(c, *frames.outline(shape, x, y, w, h, ln.offset), page_h, fill=0, stroke=1)
    c.restoreState()


def _draw_stamp(c: canvas.Canvas, stamp: Stamp, album: Album,
                pos_x: float | None = None, pos_y: float | None = None):
    """Draw a single stamp (shape + image + text).

    Uses *pos_x* / *pos_y* when provided (row stamps); falls back to
    ``stamp.abs_x`` / ``stamp.abs_y`` for absolute-position stamps.
    """
    ps = album.page_setup
    page_h_pt = _mm_to_pt(ps.height)
    sx = pos_x if pos_x is not None else stamp.abs_x
    sy = pos_y if pos_y is not None else stamp.abs_y
    x = _mm_to_pt(sx)
    y = page_h_pt - _mm_to_pt(sy + stamp.height)  # bottom of stamp in PDF (y-up)
    w = _mm_to_pt(stamp.width)
    h = _mm_to_pt(stamp.height)

    border_rgb = _color_to_rgb(
        getattr(stamp, "border_color", None) or
        getattr(album, "color_stamp_border", None) or
        Color(r=0.5, g=0.5, b=0.5)
    )
    fill_rgb = _color_to_rgb(
        getattr(stamp, "fill_color", None) or
        getattr(album, "color_stamp_background", None) or
        Color(r=1, g=1, b=1)
    )

    _draw_stamp_shape(c, stamp, sx, sy, stamp.width, stamp.height, page_h_pt, border_rgb, fill_rgb)

    # Embed image if present
    if stamp.image_path:
        img_fp = _resolve_image_path(stamp.image_path)
        if img_fp:
            try:
                c.drawImage(str(img_fp), x, y, w, h, preserveAspectRatio=True, mask="auto")
            except Exception:
                pass

    _draw_captions(c, stamp, sx, sy, page_h_pt)


def _draw_captions(c: canvas.Canvas, stamp: Stamp, sx: float, sy: float, page_h_pt: float):
    """Heading above the box; description, details and catalogue below (see caption_layout)."""
    def measure(text: str, font_id: str, size: float) -> float:
        return c.stringWidth(text, _resolve_reportlab_font(font_id, c), size) / _mm_to_pt(1)

    c.setFillColorRGB(*caption_layout.COLOR_RGB)
    for line in caption_layout.layout(stamp, sx, sy, stamp.width, stamp.height, measure):
        c.setFont(_resolve_reportlab_font(line.font_id, c), line.size_pt)
        c.drawString(_mm_to_pt(line.x), page_h_pt - _mm_to_pt(line.baseline), line.text)


def _draw_text_element(c: canvas.Canvas, stamp: Stamp, page_h_pt: float):
    """Draw a free-form text element: wrapped to its box, top-anchored, aligned."""
    if not stamp.description:
        return
    x = _mm_to_pt(stamp.abs_x)
    top = page_h_pt - _mm_to_pt(stamp.abs_y)
    w = _mm_to_pt(stamp.width)
    font_name = _resolve_reportlab_font(stamp.font_id or "HN", c)
    font_size = stamp.font_size or 12
    pad = _mm_to_pt(text_layout.PAD_MM)

    def measure(s: str) -> float:
        return c.stringWidth(s, font_name, font_size)

    lines = text_layout.wrap_lines(stamp.description, max(1.0, w - 2 * pad), measure)
    lh = font_size * text_layout.LINE_HEIGHT
    base = top - pad - font_size * text_layout.FIRST_BASELINE
    c.setFont(font_name, font_size)
    tc = stamp.text_color  # a marked heading takes the theme colour
    c.setFillColorRGB(*((tc.r, tc.g, tc.b) if tc else (0.2, 0.2, 0.2)))
    for i, line in enumerate(lines):
        if line:
            lx = text_layout.line_x(x, w, measure(line), stamp.text_align, pad)
            c.drawString(lx, base - i * lh, line)


def _draw_border_primitives(c: canvas.Canvas, prims: list, color_rgb, page_h: float):
    """Draw page_border primitives (page mm, y down) on the PDF (points, y up)."""
    c.saveState()
    c.setStrokeColorRGB(*color_rgb)
    c.setFillColorRGB(*color_rgb)
    c.setLineJoin(0)
    c.setLineCap(0)
    for p in prims:
        path = c.beginPath()
        path.moveTo(_mm_to_pt(p.points[0][0]), page_h - _mm_to_pt(p.points[0][1]))
        for x, y in p.points[1:]:
            path.lineTo(_mm_to_pt(x), page_h - _mm_to_pt(y))
        if isinstance(p, page_border.Fill):
            path.close()
            c.drawPath(path, fill=1, stroke=0)
        else:
            if p.closed:
                path.close()
            c.setLineWidth(_mm_to_pt(p.width))
            c.drawPath(path, fill=0, stroke=1)
    c.restoreState()


def _draw_page_border(c: canvas.Canvas, album: Album):
    """Draw decorative page border."""
    ps = album.page_setup
    if not ps.has_border:
        return

    color_rgb = _color_to_rgb(album.color_album_border) if album.color_album_border else (0.2, 0.2, 0.2)
    page_h = _mm_to_pt(ps.height)

    # The editor's border styles: one drawing for every view (see page_border.py)
    prims = page_border.page_primitives(album)
    if prims:
        _draw_border_primitives(c, prims, color_rgb, page_h)
        return

    bl = _mm_to_pt(ps.margin_left)
    bt = _mm_to_pt(ps.margin_top)
    bw = _mm_to_pt(ps.width - ps.margin_left - ps.margin_right)
    bh = _mm_to_pt(ps.height - ps.margin_top - ps.margin_bottom)

    # Convert from top-left to bottom-left for ReportLab
    bt_rl = page_h - bt - bh

    c.setStrokeColorRGB(*color_rgb)
    c.setFillColorRGB(*color_rgb)

    if ps.border_outer > 0:
        c.setLineWidth(_mm_to_pt(ps.border_outer))
        c.rect(bl, bt_rl, bw, bh, fill=0, stroke=1)

    if ps.border_inner1 > 0:
        off = _mm_to_pt(ps.border_outer + ps.border_spacing)
        c.setLineWidth(_mm_to_pt(ps.border_inner1))
        c.rect(bl + off, bt_rl + off, bw - off * 2, bh - off * 2, fill=0, stroke=1)

    if ps.border_inner2 > 0:
        off = _mm_to_pt(ps.border_outer + ps.border_spacing + ps.border_inner1 + ps.border_spacing)
        c.setLineWidth(_mm_to_pt(ps.border_inner2))
        c.rect(bl + off, bt_rl + off, bw - off * 2, bh - off * 2, fill=0, stroke=1)

    # Ornaments / edge patterns


# ── PDFGenerator ──

class PDFGenerator:
    """Generate PDF output using ReportLab."""

    def generate(self, album: Album, output_path: str, base_url: str = None) -> None:
        """Generate a PDF from an Album model."""
        ps = album.page_setup
        page_w = _mm_to_pt(ps.width)
        page_h = _mm_to_pt(ps.height)
        c = canvas.Canvas(output_path, pagesize=(page_w, page_h))

        row_layout = layout_rows(album)
        for pi, page_data in enumerate(album.pages):
            _draw_page_border(c, album)
            for x, y, stamp in row_layout[pi]:
                _draw_stamp(c, stamp, album, pos_x=x, pos_y=y)
            for stamp in page_data.absolute_stamps:
                if stamp.is_text_element:
                    _draw_text_element(c, stamp, page_h)
                else:
                    _draw_stamp(c, stamp, album)
            c.showPage()

        c.save()

    def generate_to_bytes(self, album: Album) -> bytes:
        """Generate a PDF and return as bytes."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.close()
            try:
                self.generate(album, tmp.name)
                with open(tmp.name, "rb") as f:
                    return f.read()
            finally:
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass
