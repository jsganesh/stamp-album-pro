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

from stamp_album.core.models import Album, Color, Stamp, StampShape
from stamp_album.engines.borders import (
    EDGE_STYLES,
    ORNAMENTAL_STYLES,
    get_ornament_segments,
    edge_pattern_segments,
    regular_polygon_vertices,
)
from stamp_album.engines import text_layout
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


def _draw_stamp_shape(
    c: canvas.Canvas,
    x: float, y: float, w: float, h: float,
    shape: StampShape,
    border_rgb: tuple[float, float, float],
    fill_rgb: tuple[float, float, float],
):
    """Draw a stamp shape outline on a ReportLab canvas.

    Coordinates are in PDF points (y-up from bottom).
    """
    c.setStrokeColorRGB(*border_rgb)
    c.setFillColorRGB(*fill_rgb)
    c.setLineWidth(0.5)

    if shape == StampShape.OVAL:
        cx = x + w / 2
        cy = y + h / 2
        rx = w / 2
        ry = h / 2
        c.saveState()
        c.translate(cx, cy)
        c.scale(1, ry / rx)
        c.circle(0, 0, rx, fill=1, stroke=1)
        c.restoreState()

    elif shape == StampShape.DIAMOND:
        cx, cy = x + w / 2, y + h / 2
        pts = [(cx, y), (x + w, cy), (cx, y + h), (x, cy)]
        p = c.beginPath()
        p.moveTo(*pts[0])
        for pt in pts[1:]:
            p.lineTo(*pt)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    elif shape == StampShape.TRIANGLE:
        pts = [(x + w / 2, y), (x + w, y + h), (x, y + h)]
        p = c.beginPath()
        p.moveTo(*pts[0])
        for pt in pts[1:]:
            p.lineTo(*pt)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    elif shape in (StampShape.HEXAGON, StampShape.OCTAGON, StampShape.PENTAGON):
        n_map = {StampShape.HEXAGON: 6, StampShape.OCTAGON: 8, StampShape.PENTAGON: 5}
        n = n_map[shape]
        verts = regular_polygon_vertices(x + w / 2, y + h / 2, w / 2, h / 2, n)
        p = c.beginPath()
        p.moveTo(*verts[0])
        for v in verts[1:]:
            p.lineTo(*v)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    else:  # RECTANGLE (default)
        c.rect(x, y, w, h, fill=1, stroke=1)


def _draw_multiline_text(
    c: canvas.Canvas,
    x: float, y: float, w: float, h: float,
    text: str,
    font_name: str,
    font_size: float,
    center: bool = False,
):
    """Draw text inside a rect splitting on newlines.

    ReportLab origin is bottom-left, so *y* is the bottom edge of the rect.
    """
    if not text:
        return
    lines = text.split("\n")
    line_height = font_size * 1.3
    total_height = len(lines) * line_height
    # y is bottom of rect, so start_y is the top of text adjusted for centering
    start_y = y + max(2, (h - total_height) / 2) + font_size
    c.setFont(font_name, font_size)
    c.setFillColorRGB(0.2, 0.2, 0.2)

    for i, line in enumerate(lines):
        line_y = start_y - i * line_height
        if center and line.strip():
            tw = c.stringWidth(line, font_name, font_size)
            line_x = x + max(2, (w - tw) / 2)
        else:
            line_x = x + 2
        c.drawString(line_x, line_y, line)


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

    _draw_stamp_shape(c, x, y, w, h, stamp.shape, border_rgb, fill_rgb)

    # Embed image if present
    if stamp.image_path:
        img_fp = _resolve_image_path(stamp.image_path)
        if img_fp:
            try:
                c.drawImage(str(img_fp), x, y, w, h, preserveAspectRatio=True, mask="auto")
            except Exception:
                pass

    # Label text (skip if image)
    if stamp.description and not stamp.image_path:
        font_name = _resolve_reportlab_font(stamp.font_id or "HN", c)
        font_size = (stamp.font_size or 12) * 0.9
        _draw_multiline_text(c, x, y, w, h, stamp.description, font_name, font_size, center=True)

    # Philatelic data: heading above stamp
    if stamp.heading and stamp.heading.text:
        hdg_font = _resolve_reportlab_font(stamp.heading.font_id or "HN", c)
        hdg_size = stamp.heading.size or 9
        hdg_y = y + h + _mm_to_pt(1)
        c.setFont(hdg_font, hdg_size)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        tw = c.stringWidth(stamp.heading.text, hdg_font, hdg_size)
        c.drawString(x + (w - tw) / 2, hdg_y, stamp.heading.text)

    # Catalog references below stamp
    if stamp.catalog_refs:
        cat_font = _resolve_reportlab_font("HN", c)
        cat_size = 8
        cat_text = " · ".join(stamp.catalog_refs)
        cat_y = y - _mm_to_pt(3.5)
        c.setFont(cat_font, cat_size)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        tw = c.stringWidth(cat_text, cat_font, cat_size)
        c.drawString(x + (w - tw) / 2, cat_y, cat_text)

    # Footer (denomination + condition + perforation)
    if stamp.footer_text:
        ft_font = _resolve_reportlab_font("HN", c)
        ft_size = 8
        ft_y = y - _mm_to_pt(1.5)
        c.setFont(ft_font, ft_size)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        tw = c.stringWidth(stamp.footer_text, ft_font, ft_size)
        c.drawString(x + (w - tw) / 2, ft_y, stamp.footer_text)


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
    c.setFillColorRGB(0.2, 0.2, 0.2)
    for i, line in enumerate(lines):
        if line:
            lx = text_layout.line_x(x, w, measure(line), stamp.text_align, pad)
            c.drawString(lx, base - i * lh, line)


def _draw_page_border(c: canvas.Canvas, album: Album):
    """Draw decorative page border."""
    ps = album.page_setup
    if not ps.has_border:
        return

    color_rgb = _color_to_rgb(album.color_album_border) if album.color_album_border else (0.2, 0.2, 0.2)
    page_h = _mm_to_pt(ps.height)

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
    border_rect_rl = (bl, bt_rl, bw, bh)
    if ps.border_style in ORNAMENTAL_STYLES:
        _draw_corner_ornaments(c, ps.border_style, color_rgb, border_rect_rl, page_h)
    elif ps.border_style in EDGE_STYLES:
        _draw_edge_patterns(c, ps.border_style, color_rgb, border_rect_rl, page_h)


def _draw_corner_ornaments(c, style, color_rgb, border_rect, page_h):
    """Draw corner ornaments using ReportLab path operations."""
    bl, bt_rl, bw, bh = border_rect
    # PDF is y-up.  Ornament +dy is inward (down in CSS, up in PDF).
    # TL: +dy inward = -y in PDF → flip_y=True
    # TR: +dy inward = -y, +dx inward = -x → flip_x=True, flip_y=True
    # BR: +dy inward = +y, +dx inward = -x → flip_x=True, flip_y=False
    # BL: +dy inward = +y → flip_y=False
    corners_pdf = [
        (bl, bt_rl + bh, False, True),   # TL
        (bl + bw, bt_rl + bh, True, True),  # TR
        (bl + bw, bt_rl, True, False),    # BR
        (bl, bt_rl, False, False),        # BL
    ]
    c.setStrokeColorRGB(*color_rgb)
    c.setFillColorRGB(*color_rgb)
    c.setLineWidth(0.8)

    for cx, cy, fx, fy in corners_pdf:
        segments = get_ornament_segments(style)
        # We draw segments using ReportLab path operations
        p = c.beginPath()
        first = True
        for seg in segments:
            cmd = seg[0]
            if cmd == "L":
                x1, y1, x2, y2 = seg[1], seg[2], seg[3], seg[4]
                sx1 = cx + (-x1 if fx else x1)
                sy1 = cy + (-y1 if fy else y1)
                sx2 = cx + (-x2 if fx else x2)
                sy2 = cy + (-y2 if fy else y2)
                if first:
                    p.moveTo(sx1, sy1)
                    first = False
                p.lineTo(sx2, sy2)
            elif cmd == "Q":
                x1, y1, cx0, cy0, x2, y2 = seg[1], seg[2], seg[3], seg[4], seg[5], seg[6]
                sx1 = cx + (-x1 if fx else x1)
                sy1 = cy + (-y1 if fy else y1)
                scx = cx + (-cx0 if fx else cx0)
                scy = cy + (-cy0 if fy else cy0)
                sx2 = cx + (-x2 if fx else x2)
                sy2 = cy + (-y2 if fy else y2)
                if first:
                    p.moveTo(sx1, sy1)
                    first = False
                # ReportLab doesn't have quadratic curves natively;
                # convert to cubic: CP1 = P0 + 2/3*(C-P0), CP2 = P1 + 2/3*(C-P1)
                cp1x = sx1 + 2/3 * (scx - sx1)
                cp1y = sy1 + 2/3 * (scy - sy1)
                cp2x = sx2 + 2/3 * (scx - sx2)
                cp2y = sy2 + 2/3 * (scy - sy2)
                p.curveTo(cp1x, cp1y, cp2x, cp2y, sx2, sy2)
            elif cmd == "C":
                x1, y1, c1x, c1y, c2x, c2y, x2, y2 = seg[1:]
                sx1 = cx + (-x1 if fx else x1)
                sy1 = cy + (-y1 if fy else y1)
                sc1x = cx + (-c1x if fx else c1x)
                sc1y = cy + (-c1y if fy else c1y)
                sc2x = cx + (-c2x if fx else c2x)
                sc2y = cy + (-c2y if fy else c2y)
                sx2 = cx + (-x2 if fx else x2)
                sy2 = cy + (-y2 if fy else y2)
                if first:
                    p.moveTo(sx1, sy1)
                    first = False
                p.curveTo(sc1x, sc1y, sc2x, sc2y, sx2, sy2)
            elif cmd == "circle":
                cx0, cy0, r, fill = seg[1], seg[2], seg[3], seg[4]
                scx = cx + (-cx0 if fx else cx0)
                scy = cy + (-cy0 if fy else cy0)
                if fill:
                    c.circle(scx, scy, r, fill=1, stroke=0)
                else:
                    c.circle(scx, scy, r, fill=0, stroke=1)
            elif cmd == "rect":
                rx, ry, rw, rh, fill = seg[1], seg[2], seg[3], seg[4], seg[5]
                sx = cx + (-rx if fx else rx)
                sy = cy + (-ry if fy else ry)
                sw = -rw if fx else rw
                sh = -rh if fy else rh
                if fill:
                    c.rect(min(sx, sx + sw if sw < 0 else sx), min(sy, sy + sh if sh < 0 else sy), abs(sw), abs(sh), fill=1, stroke=0)
                else:
                    c.rect(min(sx, sx + sw if sw < 0 else sx), min(sy, sy + sh if sh < 0 else sy), abs(sw), abs(sh), fill=0, stroke=1)
        if not first:
            c.drawPath(p, fill=0, stroke=1)


def _draw_edge_patterns(c, style, color_rgb, border_rect, page_h):
    """Draw edge patterns (greek_key, rope) on all 4 sides."""
    bl, bt_rl, bw, bh = border_rect
    pw = 0.75  # scale: CSS pixel → pt

    c.setStrokeColorRGB(*color_rgb)
    c.setFillColorRGB(*color_rgb)
    c.setLineWidth(0.6)

    # Top edge (y = bt_rl + bh in PDF coords)
    top_y = bt_rl + bh
    segments_top = edge_pattern_segments(style, "top", bw / pw)
    for seg in segments_top:
        if seg[0] == "L":
            x1, y1, x2, y2 = seg[1], seg[2], seg[3], seg[4]
            c.line(bl + x1 * pw, top_y - y1 * pw, bl + x2 * pw, top_y - y2 * pw)
        elif seg[0] == "circle":
            cx0, cy0, r, _ = seg[1], seg[2], seg[3], seg[4]
            c.circle(bl + cx0 * pw, top_y - cy0 * pw, r * pw, fill=0, stroke=1)

    # Bottom edge (y = bt_rl in PDF coords, mirrored)
    bot_y = bt_rl
    segments_bot = edge_pattern_segments(style, "bottom", bw / pw)
    for seg in segments_bot:
        if seg[0] == "L":
            x1, y1, x2, y2 = seg[1], seg[2], seg[3], seg[4]
            c.line(bl + x1 * pw, bot_y + y1 * pw, bl + x2 * pw, bot_y + y2 * pw)
        elif seg[0] == "circle":
            cx0, cy0, r, _ = seg[1], seg[2], seg[3], seg[4]
            c.circle(bl + cx0 * pw, bot_y + cy0 * pw, r * pw, fill=0, stroke=1)

    # Left edge (y increases downward in segments)
    segments_left = edge_pattern_segments(style, "left", bh / pw)
    for seg in segments_left:
        if seg[0] == "L":
            x1, y1, x2, y2 = seg[1], seg[2], seg[3], seg[4]
            c.line(bl + x1 * pw, bt_rl + bh - y1 * pw, bl + x2 * pw, bt_rl + bh - y2 * pw)
        elif seg[0] == "circle":
            cx0, cy0, r, _ = seg[1], seg[2], seg[3], seg[4]
            c.circle(bl + cx0 * pw, bt_rl + bh - cy0 * pw, r * pw, fill=0, stroke=1)

    # Right edge (mirrored horizontally)
    right_x = bl + bw
    segments_right = edge_pattern_segments(style, "right", bh / pw)
    for seg in segments_right:
        if seg[0] == "L":
            x1, y1, x2, y2 = seg[1], seg[2], seg[3], seg[4]
            c.line(right_x - x1 * pw, bt_rl + bh - y1 * pw, right_x - x2 * pw, bt_rl + bh - y2 * pw)
        elif seg[0] == "circle":
            cx0, cy0, r, _ = seg[1], seg[2], seg[3], seg[4]
            c.circle(right_x - cx0 * pw, bt_rl + bh - cy0 * pw, r * pw, fill=0, stroke=1)


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
