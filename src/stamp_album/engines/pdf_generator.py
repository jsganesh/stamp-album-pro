"""
PDF generation engine using direct PyMuPDF drawing + HTML preview renderer.

Replaces WeasyPrint with a lightweight, native approach:
- Draws stamps, text, and shapes directly to PDF pages
- No HTML/CSS intermediate layer for PDF
- No native library dependencies (Pango, Cairo, etc.)
- System fonts loaded by file path
- All stamp shapes supported
- HTMLRenderer kept for live preview (generates HTML, not PDF)
"""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import fitz

from stamp_album.core.models import (
    Album, Color, FormattedText, Page, Stamp, StampShape,
    TextShadow, TextOutline, GradientFill,
)


# ── HTML Renderer (for live preview) ──

class HTMLRenderer:
    """Renders an Album model to HTML/CSS for live preview."""

    def __init__(self, album: Album, font_manager=None):
        self.album = album
        self.font_manager = font_manager
        self._page_counter = 0

    def render(self) -> str:
        """Render the entire album to HTML."""
        parts = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'>",
            self._render_styles(),
            "</head><body>",
        ]
        for page in self.album.pages:
            self._page_counter += 1
            parts.append(self._render_page(page))
        parts.extend(["</body>", "</html>"])
        return "\n".join(parts)

    def _border_color_css(self) -> str:
        c = self.album.color_album_border
        if c:
            return f"rgb({int(c.r*255)},{int(c.g*255)},{int(c.b*255)})"
        return "#333"

    def _render_styles(self) -> str:
        ps = self.album.page_setup
        w_mm = round(ps.width, 2)
        h_mm = round(ps.height, 2)
        ml = round(ps.margin_left, 2)
        mr = round(ps.margin_right, 2)
        mt = round(ps.margin_top, 2)
        mb = round(ps.margin_bottom, 2)
        content_height = round(ps.height - ps.margin_top - ps.margin_bottom, 2)
        return f"""
        <style>
        @page {{ size: {w_mm}mm {h_mm}mm; margin: 0; }}
        body {{ margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; }}
        .page {{ position: relative; width: {w_mm}mm; min-height: {h_mm}mm; page-break-after: always; box-sizing: border-box; }}
        .page:last-child {{ page-break-after: auto; }}
        .page-content {{ position: relative; z-index: 1; width: 100%; box-sizing: border-box; padding: {mt}mm {mr}mm {mb}mm {ml}mm; min-height: {content_height}mm; }}
        .stamp {{ position: absolute; display: flex; align-items: center; justify-content: center; text-align: center; overflow: hidden; box-sizing: border-box; }}
        .text-el {{ position: absolute; overflow: hidden; box-sizing: border-box; }}
        .stamp-box {{ box-sizing: border-box; }}

        </style>"""

    def _render_page(self, page: Page) -> str:
        ps = self.album.page_setup
        parts = [f'<div class="page">']

        # Page border
        if ps.has_border:
            color = self._border_color_css()
            bl = ps.margin_left
            bt = ps.margin_top
            bw = round(ps.width - ps.margin_left - ps.margin_right, 2)
            bh = round(ps.height - ps.margin_top - ps.margin_bottom, 2)
            if ps.border_outer > 0:
                parts.append(
                    f'<div style="position:absolute;top:{bt}mm;left:{bl}mm;'
                    f'width:{bw}mm;height:{bh}mm;'
                    f'border:{ps.border_outer}mm solid {color};"></div>'
                )
            if ps.border_inner1 > 0:
                off = ps.border_outer + ps.border_spacing
                parts.append(
                    f'<div style="position:absolute;top:{bt + off}mm;left:{bl + off}mm;'
                    f'width:{bw - off*2}mm;height:{bh - off*2}mm;'
                    f'border:{ps.border_inner1}mm solid {color};"></div>'
                )
            if ps.border_inner2 > 0:
                off = ps.border_outer + ps.border_spacing + ps.border_inner1 + ps.border_spacing
                parts.append(
                    f'<div style="position:absolute;top:{bt + off}mm;left:{bl + off}mm;'
                    f'width:{bw - off*2}mm;height:{bh - off*2}mm;'
                    f'border:{ps.border_inner2}mm solid {color};"></div>'
                )

            # Corner ornaments for ornamental border styles
            px = 96.0 / 25.4  # CSS pixels per mm
            bl_px = round(bl * px, 1)
            bt_px = round(bt * px, 1)
            bw_px = round(bw * px, 1)
            bh_px = round(bh * px, 1)
            if ps.border_style in _ORNAMENTAL_STYLES:
                ornament_svg = _corner_ornament_svg(ps.border_style, color)
                parts.append(
                    f'<svg style="position:absolute;top:0;left:0;width:100%;height:100%;'
                    f'pointer-events:none;overflow:visible;">'
                    f'<g transform="translate({bl_px},{bt_px})">{ornament_svg}</g>'
                    f'<g transform="translate({bl_px + bw_px},{bt_px}) scale(-1,1)">{ornament_svg}</g>'
                    f'<g transform="translate({bl_px + bw_px},{bt_px + bh_px}) scale(-1,-1)">{ornament_svg}</g>'
                    f'<g transform="translate({bl_px},{bt_px + bh_px}) scale(1,-1)">{ornament_svg}</g>'
                    f'</svg>'
                )
            # Edge patterns for greek_key / rope
            elif ps.border_style in _EDGE_STYLES:
                epw = round(bw * px, 1)
                eph = round(bh * px, 1)
                top_svg = _edge_pattern_svg(ps.border_style, "top", epw, eph, color)
                bottom_svg = _edge_pattern_svg(ps.border_style, "bottom", epw, eph, color)
                left_svg = _edge_pattern_svg(ps.border_style, "left", eph, epw, color)
                right_svg = _edge_pattern_svg(ps.border_style, "right", eph, epw, color)
                parts.append(
                    f'<svg style="position:absolute;top:0;left:0;width:100%;height:100%;'
                    f'pointer-events:none;overflow:visible;">'
                    f'<g transform="translate({bl_px},{bt_px})">{top_svg}</g>'
                    f'<g transform="translate({bl_px},{bt_px + bh_px}) scale(1,-1)">{bottom_svg}</g>'
                    f'<g transform="translate({bl_px},{bt_px})">{left_svg}</g>'
                    f'<g transform="translate({bl_px + bw_px},{bt_px}) scale(-1,1)">{right_svg}</g>'
                    f'</svg>'
                )

        parts.append(f'<div class="page-content">')

        # Boxes
        for x, y, w, h in page.boxes:
            parts.append(
                f'<div style="position: absolute; left: {x}mm; top: {y}mm; '
                f'width: {w}mm; height: {h}mm; border: 0.5pt solid black;"></div>'
            )

        # Row-based stamps (DSL layout)
        # Check if page has column mode
        col_mode = getattr(page, 'column_mode', None)
        col_gap = getattr(page, 'column_gap', 10.0) or 10.0
        has_columns = col_mode is not None and col_mode.name != 'NONE'

        if has_columns:
            _col_map = {'ONE': 1, 'TWO': 2, 'THREE': 3}
            col_count = _col_map.get(col_mode.name, 2)
            parts.append(
                f'<div class="column-container cols-{col_count}" '
                f'style="display:flex;gap: {col_gap}mm;flex-wrap:wrap;">'
            )

        shape_polygons = {
            StampShape.TRIANGLE: "50,0 100,100 0,100",
            StampShape.TRIANGLE_INV: "0,0 100,0 50,100",
            StampShape.DIAMOND: "50,0 100,50 50,100 0,50",
            StampShape.HEXAGON: "25,0 75,0 100,50 75,100 25,100 0,50",
            StampShape.OCTAGON: "30,0 70,0 100,30 100,70 70,100 30,100 0,70 0,30",
            StampShape.PENTAGON: "50,0 100,38 82,100 18,100 0,38",
        }
        _Y_POS = 20  # Starting Y position in mm
        for row in page.rows:
            _X_POS = 0
            for stamp in row.stamps:
                x, y = _X_POS, _Y_POS
                w, h = stamp.width, stamp.height
                desc = (stamp.description or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                font_size = stamp.font_size or 10
                if stamp.shape == StampShape.OVAL:
                    shape_html = (
                        f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 100 100" style="position:absolute;top:0;left:0;">'
                        f'<ellipse cx="50" cy="50" rx="50" ry="50" fill="#fff" stroke="#666" stroke-width="0.3"/>'
                        f'</svg>'
                    )
                elif stamp.shape in shape_polygons:
                    pts = shape_polygons[stamp.shape]
                    shape_html = (
                        f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 100 100" style="position:absolute;top:0;left:0;">'
                        f'<polygon points="{pts}" fill="#fff" stroke="#666" stroke-width="0.3"/>'
                        f'</svg>'
                    )
                else:
                    shape_html = ""
                parts.append(
                    f'<div class="stamp" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;">'
                    f'{shape_html}'
                    f'<div style="font-size:{font_size}pt;padding:1mm;text-align:center;">{desc}</div>'
                    f'</div>'
                )
                _X_POS += w + row.spacing
            _Y_POS += 30  # Next row

        if has_columns:
            parts.append('</div>')  # close column-container

        # Absolutely positioned stamps (drag-and-drop)
        for stamp in page.absolute_stamps:
            x, y, w, h = stamp.abs_x, stamp.abs_y, stamp.width, stamp.height
            desc = (stamp.description or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            font_size = stamp.font_size or 12

            if stamp.is_text_element:
                parts.append(
                    f'<div class="text-el" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;'
                    f'font-size:{font_size}pt;padding:1mm;word-wrap:break-word;">{desc}</div>'
                )
            else:
                border_color = _color_to_rgb(getattr(stamp, 'border_color', None)) if getattr(stamp, 'border_color', None) else (0.5, 0.5, 0.5)
                bg_color = _color_to_rgb(getattr(stamp, 'fill_color', None)) if getattr(stamp, 'fill_color', None) else (1, 1, 1)
                bc = f"rgb({int(border_color[0]*255)},{int(border_color[1]*255)},{int(border_color[2]*255)})"
                bg = f"rgb({int(bg_color[0]*255)},{int(bg_color[1]*255)},{int(bg_color[2]*255)})"
                desc_font_size = round(font_size * 0.9, 1)
                if stamp.shape == StampShape.OVAL:
                    shape_html = (
                        f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 100 100" style="position:absolute;top:0;left:0;">'
                        f'<ellipse cx="50" cy="50" rx="50" ry="50" fill="{bg}" stroke="{bc}" stroke-width="0.3"/>'
                        f'</svg>'
                    )
                elif stamp.shape in shape_polygons:
                    pts = shape_polygons[stamp.shape]
                    shape_html = (
                        f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 100 100" style="position:absolute;top:0;left:0;">'
                        f'<polygon points="{pts}" fill="{bg}" stroke="{bc}" stroke-width="0.3"/>'
                        f'</svg>'
                    )
                else:
                    shape_html = (
                        f'<div style="position:absolute;top:0;left:0;width:{w}mm;height:{h}mm;'
                        f'border:0.5pt solid {bc};background-color:{bg};"></div>'
                    )
                img_html = ""
                if stamp.image_path:
                    img_html = f'<img src="{stamp.image_path}" style="position:absolute;top:0;left:0;width:100%;height:100%;object-fit:contain;pointer-events:none;z-index:1;">'
                parts.append(
                    f'<div class="stamp" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;">'
                    f'{shape_html}'
                    f'{img_html}'
                    f'<div style="font-size:{desc_font_size}pt;padding:1mm 2mm;text-align:center;line-height:1.3;">{desc}</div>'
                    f'</div>'
                )

        parts.append("</div>")  # close page-content
        parts.append("</div>")  # close page
        return "\n".join(parts)

    def _render_text_element(self, ft: FormattedText) -> str:
        """Render a FormattedText to HTML (for live preview of typography)."""
        parts = []
        style_parts = [f"font-size: {ft.size}pt"]

        # Drop cap
        if ft.drop_cap_lines and ft.drop_cap_lines > 0:
            dc_size = ft.size * ft.drop_cap_lines
            parts.append(
                f'<span style="float: left; font-size: {dc_size}pt; line-height: 0.8; '
                f'padding-right: 2pt; font-weight: bold">{ft.content[:1]}</span>'
            )
            rest = ft.content[1:]
        else:
            rest = ft.content

        # Text shadow
        if ft.shadow:
            c = ft.shadow.color
            rgba = f"rgba({int(c.r*255)}, {int(c.g*255)}, {int(c.b*255)}, {ft.shadow.opacity})"
            style_parts.append(
                f"text-shadow: {ft.shadow.offset_x}px {ft.shadow.offset_y}px "
                f"{ft.shadow.blur}px {rgba}"
            )

        # Text outline
        if ft.outline:
            c = ft.outline.color
            rgb = f"rgb({int(c.r*255)}, {int(c.g*255)}, {int(c.b*255)})"
            style_parts.append(f"-webkit-text-stroke: {ft.outline.width}pt {rgb}")

        # Gradient fill
        gradient_style = ""
        if ft.gradient:
            stops = ft.gradient.stops
            if stops:
                direction = "to right" if ft.gradient.direction == "horizontal" else "180deg"
                stop_strs = []
                for s in stops:
                    c = s.color
                    stop_strs.append(
                        f"rgb({int(c.r*255)}, {int(c.g*255)}, {int(c.b*255)}) {s.offset*100}%"
                    )
                gradient = f"linear-gradient({direction}, {', '.join(stop_strs)})"
                gradient_style = (
                    f"background: {gradient}; -webkit-background-clip: text; "
                    f"-webkit-text-fill-color: transparent"
                )

        style_str = "; ".join(style_parts)
        if gradient_style:
            parts.append(f'<span style="{style_str}; {gradient_style}">{rest}</span>')
        else:
            parts.append(f'<span style="{style_str}">{rest}</span>')

        return " ".join(parts)

    def _parse_inline_formatting(self, text: str) -> str:
        """Parse inline markdown-like formatting into HTML.

        Supports: **bold**, __bold__, *italic*, _italic_, ~~strike~~,
        `code`, ^superscript^, ~subscript~, \\* escaped markers.
        """
        import re

        # HTML escape first
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Escaped markers: \* → literal *
        text = re.sub(r'\\\*', '\x00AST\x00', text)
        text = re.sub(r'\\\_', '\x00US\x00', text)
        text = re.sub(r'\\~', '\x00TIL\x00', text)

        # Bold+italic: ***text***
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
        # Bold: **text** or __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        # Italic: *text* or _text_
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'(?<!<)_(.+?)_(?!>)', r'<em>\1</em>', text)
        # Strikethrough: ~~text~~
        text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
        # Code: `text`
        text = re.sub(r'`(.+?)`', r'<code style="font-family:monospace;background:rgba(0,0,0,0.05);padding:1px 3px;border-radius:2px">\1</code>', text)
        # Superscript: ^text^
        text = re.sub(r'\^(.+?)\^', r'<sup>\1</sup>', text)
        # Subscript: ~text~
        text = re.sub(r'(?<!<)~(.+?)~(?!>)', r'<sub>\1</sub>', text)

        # Restore escaped markers
        text = text.replace('\x00AST\x00', '*').replace('\x00US\x00', '_').replace('\x00TIL\x00', '~')

        return text

    def _format_text(self, text: str) -> str:
        """Format text with inline formatting and newline handling."""
        if not text:
            return ""
        result = self._parse_inline_formatting(text)
        result = result.replace("\n", "<br>")
        return result


# ── Font resolution ──

# Built-in PDF fonts (always available in any PDF viewer)
_BUILTIN_FONT_MAP = {
    "CN": "cour",   # Courier
    "CB": "cobo",   # Courier-Bold
    "CI": "cour",   # Courier-Oblique (fallback)
    "CS": "cobo",   # Courier-BoldOblique (fallback)
    "TN": "tiro",   # Times-Roman
    "TB": "tibo",   # Times-Bold
    "TI": "tiro",   # Times-Italic (fallback)
    "TS": "tibo",   # Times-BoldItalic (fallback)
    "HN": "helv",   # Helvetica
    "HB": "hebo",   # Helvetica-Bold
    "HI": "helv",   # Helvetica-Oblique (fallback)
    "HS": "hebo",   # Helvetica-BoldOblique (fallback)
}


def _get_system_font_dirs() -> list[Path]:
    system = platform.system()
    if system == "Darwin":
        return [d for d in [
            Path("/Library/Fonts"),
            Path.home() / "Library/Fonts",
            Path("/System/Library/Fonts"),
        ] if d.exists()]
    elif system == "Linux":
        return [d for d in [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
        ] if d.exists()]
    return []


def _resolve_font(font_id: str) -> tuple:
    """
    Resolve a font ID to a fitz.Font object.
    Returns (font_obj, is_builtin) or (None, True) for fallback.
    """
    if font_id in _BUILTIN_FONT_MAP:
        try:
            return (fitz.Font(_BUILTIN_FONT_MAP[font_id]), True)
        except Exception:
            pass

    # Scan system fonts for matching name
    font_id_lower = font_id.lower()
    for d in _get_system_font_dirs():
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith((".ttf", ".ttc", ".otf")):
                    stem = Path(f).stem.lower()
                    if font_id_lower in stem or stem in font_id_lower:
                        try:
                            return (fitz.Font(fontfile=str(Path(root) / f)), False)
                        except Exception:
                            continue

    # Fallback to Helvetica
    try:
        return (fitz.Font("helv"), True)
    except Exception:
        return (None, True)


def _mm_to_pt(mm: float) -> float:
    """Convert millimeters to PDF points (1 inch = 25.4 mm = 72 pt)."""
    return mm * 72.0 / 25.4


def _color_to_rgb(color) -> tuple:
    """Convert a Color object to RGB tuple (0-1 range)."""
    if color is None:
        return (0, 0, 0)
    return (max(0, min(1, color.r)), max(0, min(1, color.g)), max(0, min(1, color.b)))


# ── Image resolution ──

_IMAGES_DIR = Path.home() / "StampAlbum" / "images"

def _resolve_image_path(image_path: Optional[str]) -> Optional[Path]:
    """Convert a URL path like '/images/photo.png' to a filesystem Path."""
    if not image_path:
        return None
    filename = Path(urlparse(image_path).path).name
    fp = _IMAGES_DIR / filename
    return fp if fp.exists() else None


# ── Shape helpers ──

def _regular_polygon(cx: float, cy: float, rx: float, ry: float, n: int) -> list:
    """Generate points for a regular polygon centered at (cx, cy)."""
    import math
    points = []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        points.append(fitz.Point(cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
    return points


# ── Drawing ──

def _draw_stamp(
    page: fitz.Page,
    stamp: Stamp,
    album: Album,
) -> None:
    """Draw a single stamp (box + label) on the page."""
    x = _mm_to_pt(stamp.abs_x)
    y = _mm_to_pt(stamp.abs_y)
    w = _mm_to_pt(stamp.width)
    h = _mm_to_pt(stamp.height)

    # Resolve colors: stamp-level → album-level → defaults
    border_color = _color_to_rgb(
        getattr(stamp, 'border_color', None) or
        getattr(album, 'color_stamp_border', None) or
        Color(r=0.5, g=0.5, b=0.5)
    )
    fill_color = _color_to_rgb(
        getattr(stamp, 'fill_color', None) or
        getattr(album, 'color_stamp_background', None) or
        Color(r=1, g=1, b=1)
    )

    rect = fitz.Rect(x, y, x + w, y + h)
    shape = stamp.shape

    if shape == StampShape.OVAL:
        page.draw_oval(rect, color=border_color, fill=fill_color, width=0.5)

    elif shape == StampShape.DIAMOND:
        cx, cy = x + w / 2, y + h / 2
        pts = [fitz.Point(cx, y), fitz.Point(x + w, cy), fitz.Point(cx, y + h), fitz.Point(x, cy)]
        s = page.new_shape()
        s.draw_polyline(pts + [pts[0]])
        s.finish(fill=fill_color, color=border_color, width=0.5)
        s.commit()

    elif shape == StampShape.TRIANGLE:
        pts = [fitz.Point(x + w / 2, y), fitz.Point(x + w, y + h), fitz.Point(x, y + h)]
        s = page.new_shape()
        s.draw_polyline(pts + [pts[0]])
        s.finish(fill=fill_color, color=border_color, width=0.5)
        s.commit()

    elif shape == StampShape.HEXAGON:
        pts = _regular_polygon(x + w / 2, y + h / 2, w / 2, h / 2, 6)
        s = page.new_shape()
        s.draw_polyline(pts + [pts[0]])
        s.finish(fill=fill_color, color=border_color, width=0.5)
        s.commit()

    elif shape == StampShape.OCTAGON:
        pts = _regular_polygon(x + w / 2, y + h / 2, w / 2, h / 2, 8)
        s = page.new_shape()
        s.draw_polyline(pts + [pts[0]])
        s.finish(fill=fill_color, color=border_color, width=0.5)
        s.commit()

    elif shape == StampShape.PENTAGON:
        pts = _regular_polygon(x + w / 2, y + h / 2, w / 2, h / 2, 5)
        s = page.new_shape()
        s.draw_polyline(pts + [pts[0]])
        s.finish(fill=fill_color, color=border_color, width=0.5)
        s.commit()

    else:  # RECTANGLE (default)
        page.draw_rect(rect, color=border_color, fill=fill_color, width=0.5)

    # Insert stamp image if present
    img_fp = _resolve_image_path(stamp.image_path)
    if img_fp:
        try:
            page.insert_image(rect, filename=str(img_fp))
        except Exception:
            pass

    # Draw label text
    if stamp.description:
        font_obj, _ = _resolve_font(stamp.font_id or "HN")
        fontsize = (stamp.font_size or 12) * 0.9
        text = stamp.description

        if font_obj:
            tw = fitz.TextWriter(page.rect)
            tw.append(rect.tl, text, font=font_obj, fontsize=fontsize)
            text_rect = tw.text_rect
            dx = max(0, (rect.width - text_rect.width) / 2)
            dy = max(0, (rect.height - text_rect.height) / 2)
            tw = fitz.TextWriter(page.rect)
            tw.append(fitz.Point(rect.x0 + dx, rect.y0 + dy + fontsize), text, font=font_obj, fontsize=fontsize)
            tw.write_text(page, color=(0.2, 0.2, 0.2))


def _draw_text_element(page: fitz.Page, stamp: Stamp) -> None:
    """Draw a free-form text element."""
    if not stamp.description:
        return

    x = _mm_to_pt(stamp.abs_x)
    y = _mm_to_pt(stamp.abs_y)
    w = _mm_to_pt(stamp.width)
    h = _mm_to_pt(stamp.height)

    font_obj, _ = _resolve_font(stamp.font_id or "HN")
    fontsize = stamp.font_size or 12
    text = stamp.description

    if font_obj:
        rect = fitz.Rect(x, y, x + w, y + h)
        tw = fitz.TextWriter(page.rect)
        tw.append(fitz.Point(rect.x0 + 2, rect.y0 + fontsize + 3), text, font=font_obj, fontsize=fontsize)
        tw.write_text(page, color=(0.2, 0.2, 0.2))


# ── Ornamental border data (ported from borders.js) ──

_ORNAMENTAL_STYLES = {"classic", "victorian", "artdeco", "laurel", "gothic", "filigree"}
_EDGE_STYLES = {"greek_key", "rope"}

_ORNAMENT_BBOX = {
    "classic": (62, 82),
    "victorian": (42, 87),
    "artdeco": (43, 85),
    "laurel": (22, 62),
    "gothic": (32, 85),
    "filigree": (65, 65),
}

def _pdraw(page, color, segments, width=0.8):
    """Draw path segments (bezier/line) on a PyMuPDF page."""
    for seg in segments:
        cmd = seg[0]
        pts = seg[1:]
        if cmd == "L":
            page.draw_line(pts[0], pts[1], color=color, width=width)
        elif cmd == "Q":
            # Quadratic bezier as cubic: CP1 = P0 + 2/3*(C - P0), CP2 = P1 + 2/3*(C - P1)
            p0, c, p1 = pts[0], pts[1], pts[2]
            cp1 = fitz.Point(p0.x + 2/3 * (c.x - p0.x), p0.y + 2/3 * (c.y - p0.y))
            cp2 = fitz.Point(p1.x + 2/3 * (c.x - p1.x), p1.y + 2/3 * (c.y - p1.y))
            page.draw_bezier(p0, cp1, cp2, p1, color=color, width=width)
        elif cmd == "C":
            page.draw_bezier(pts[0], pts[1], pts[2], pts[3], color=color, width=width)


def _corner_ornament_svg(style: str, color: str = "#333") -> str:
    """Generate SVG for a corner ornament (TL orientation)."""
    if style == "classic":
        return (
            '<path d="M5,80 Q5,20 20,20 Q40,20 45,5 Q50,0 60,0" fill="none" stroke="' + color + '" stroke-width="1.2"/>'
            '<path d="M5,60 Q5,15 15,10 Q30,5 35,2" fill="none" stroke="' + color + '" stroke-width="0.8"/>'
            '<circle cx="8" cy="8" r="2" fill="' + color + '"/>'
            '<circle cx="20" cy="5" r="1.2" fill="' + color + '"/>'
        )
    if style == "victorian":
        return (
            '<path d="M0,85 C10,85 15,70 25,60 C35,50 30,35 20,25 C15,20 10,15 5,10 C10,12 15,18 25,22 C35,26 40,20 35,10" fill="none" stroke="' + color + '" stroke-width="1.2"/>'
            '<path d="M0,75 C8,75 12,65 20,58 C28,51 25,40 18,32 C14,28 10,24 8,18" fill="none" stroke="' + color + '" stroke-width="0.7"/>'
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
            '<path d="M5,80 Q15,60 10,40 Q8,30 15,20" fill="none" stroke="' + color + '" stroke-width="1"/>'
            '<ellipse cx="12" cy="35" rx="4" ry="2.5" fill="' + color + '" transform="rotate(-30 12 35)"/>'
            '<ellipse cx="8" cy="45" rx="4" ry="2.5" fill="' + color + '" transform="rotate(-20 8 45)"/>'
            '<ellipse cx="15" cy="55" rx="4" ry="2.5" fill="' + color + '" transform="rotate(-40 15 55)"/>'
            '<ellipse cx="18" cy="28" rx="3.5" ry="2" fill="' + color + '" transform="rotate(-45 18 28)"/>'
            '<circle cx="14" cy="22" r="1.5" fill="' + color + '"/>'
            '<circle cx="10" cy="50" r="1.2" fill="' + color + '"/>'
        )
    if style == "gothic":
        return (
            '<path d="M0,85 L0,40 Q0,20 15,10 Q25,3 30,0" fill="none" stroke="' + color + '" stroke-width="1.5"/>'
            '<path d="M5,85 L5,45 Q5,28 18,18 Q25,12 28,8" fill="none" stroke="' + color + '" stroke-width="0.8"/>'
            '<path d="M15,0 Q20,5 22,12" fill="none" stroke="' + color + '" stroke-width="0.6"/>'
        )
    if style == "filigree":
        return (
            '<circle cx="20" cy="20" r="15" fill="none" stroke="' + color + '" stroke-width="0.8"/>'
            '<circle cx="20" cy="20" r="10" fill="none" stroke="' + color + '" stroke-width="0.5"/>'
            '<circle cx="20" cy="20" r="5" fill="none" stroke="' + color + '" stroke-width="0.5"/>'
            '<circle cx="20" cy="20" r="2" fill="' + color + '"/>'
            '<path d="M20,35 Q25,50 30,65" fill="none" stroke="' + color + '" stroke-width="0.6"/>'
            '<path d="M35,20 Q50,25 65,30" fill="none" stroke="' + color + '" stroke-width="0.6"/>'
            '<circle cx="30" cy="30" r="1.5" fill="' + color + '"/>'
            '<circle cx="35" cy="35" r="1" fill="' + color + '"/>'
        )
    return ""


def _edge_pattern_svg(style: str, edge: str, w: float, h: float, color: str) -> str:
    """Generate SVG for an edge pattern (greek_key or rope)."""
    svg = ""
    if style == "greek_key":
        step = 12
        count = int(w / step)
        is_v = edge in ("left", "right")
        for i in range(count):
            if is_v:
                svg += f'<path d="M0,{i*step} l0,3 l3,0 l0,6 l-3,0 l0,3" fill="none" stroke="{color}" stroke-width="0.8"/>'
            else:
                svg += f'<path d="M{i*step},0 l3,0 l0,3 l6,0 l0,-3 l3,0" fill="none" stroke="{color}" stroke-width="0.8"/>'
    elif style == "rope":
        rstep = 8
        count = int(w / rstep)
        is_v = edge in ("left", "right")
        for j in range(count):
            if is_v:
                svg += f'<circle cx="2" cy="{j * rstep + rstep/2}" r="2" fill="none" stroke="{color}" stroke-width="0.7"/>'
            else:
                svg += f'<circle cx="{j * rstep + rstep/2}" cy="2" r="2" fill="none" stroke="{color}" stroke-width="0.7"/>'
    return svg


def _draw_edge_patterns(fitz_page: fitz.Page, album: Album, rect: fitz.Rect) -> None:
    """Draw edge patterns (greek_key, rope) on all 4 sides."""
    ps = album.page_setup
    style = ps.border_style
    if style not in _EDGE_STYLES:
        return
    color = _color_to_rgb(album.color_album_border) if album.color_album_border else (0.2, 0.2, 0.2)
    x0, y0 = rect.x0, rect.y0
    rw, rh = rect.width, rect.height

    # Scale: CSS pixel → PDF point (96dpi → 72dpi)
    pw = 0.75  # points per CSS pixel

    if style == "greek_key":
        step = 12 * pw
        count_w = int(rw / step)
        count_h = int(rh / step)
        # Top edge
        for i in range(count_w):
            x = x0 + i * step
            y = y0
            fitz_page.draw_line(fitz.Point(x, y + 3 * pw), fitz.Point(x + 3 * pw, y + 3 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 3 * pw, y + 3 * pw), fitz.Point(x + 3 * pw, y + 6 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 3 * pw, y + 6 * pw), fitz.Point(x + 9 * pw, y + 6 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 9 * pw, y + 6 * pw), fitz.Point(x + 9 * pw, y + 3 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 9 * pw, y + 3 * pw), fitz.Point(x + step, y + 3 * pw), color=color, width=0.6)
        # Bottom edge (mirrored)
        for i in range(count_w):
            x = x0 + i * step
            y = y0 + rh
            fitz_page.draw_line(fitz.Point(x, y - 3 * pw), fitz.Point(x + 3 * pw, y - 3 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 3 * pw, y - 3 * pw), fitz.Point(x + 3 * pw, y - 6 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 3 * pw, y - 6 * pw), fitz.Point(x + 9 * pw, y - 6 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 9 * pw, y - 6 * pw), fitz.Point(x + 9 * pw, y - 3 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 9 * pw, y - 3 * pw), fitz.Point(x + step, y - 3 * pw), color=color, width=0.6)
        # Left edge
        for i in range(count_h):
            x = x0
            y = y0 + i * step
            fitz_page.draw_line(fitz.Point(x + 3 * pw, y), fitz.Point(x + 3 * pw, y + 3 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 3 * pw, y + 3 * pw), fitz.Point(x + 6 * pw, y + 3 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 6 * pw, y + 3 * pw), fitz.Point(x + 6 * pw, y + 9 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 6 * pw, y + 9 * pw), fitz.Point(x + 3 * pw, y + 9 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x + 3 * pw, y + 9 * pw), fitz.Point(x + 3 * pw, y + step), color=color, width=0.6)
        # Right edge (mirrored)
        for i in range(count_h):
            x = x0 + rw
            y = y0 + i * step
            fitz_page.draw_line(fitz.Point(x - 3 * pw, y), fitz.Point(x - 3 * pw, y + 3 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x - 3 * pw, y + 3 * pw), fitz.Point(x - 6 * pw, y + 3 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x - 6 * pw, y + 3 * pw), fitz.Point(x - 6 * pw, y + 9 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x - 6 * pw, y + 9 * pw), fitz.Point(x - 3 * pw, y + 9 * pw), color=color, width=0.6)
            fitz_page.draw_line(fitz.Point(x - 3 * pw, y + 9 * pw), fitz.Point(x - 3 * pw, y + step), color=color, width=0.6)

    elif style == "rope":
        rstep = 8 * pw
        count_w = int(rw / rstep)
        count_h = int(rh / rstep)
        r = 1.5  # circle radius in pt
        # Top edge
        for j in range(count_w):
            cx = x0 + j * rstep + rstep / 2
            cy = y0 + 1.5
            fitz_page.draw_circle(fitz.Point(cx, cy), r, color=color)
        # Bottom edge
        for j in range(count_w):
            cx = x0 + j * rstep + rstep / 2
            cy = y0 + rh - 1.5
            fitz_page.draw_circle(fitz.Point(cx, cy), r, color=color)
        # Left edge
        for j in range(count_h):
            cx = x0 + 1.5
            cy = y0 + j * rstep + rstep / 2
            fitz_page.draw_circle(fitz.Point(cx, cy), r, color=color)
        # Right edge
        for j in range(count_h):
            cx = x0 + rw - 1.5
            cy = y0 + j * rstep + rstep / 2
            fitz_page.draw_circle(fitz.Point(cx, cy), r, color=color)


def _draw_corner_ornaments(fitz_page: fitz.Page, album: Album, rect: fitz.Rect) -> None:
    """Draw corner ornaments for ornamental border styles."""
    ps = album.page_setup
    style = ps.border_style
    if style not in _ORNAMENTAL_STYLES:
        return
    color = _color_to_rgb(album.color_album_border) if album.color_album_border else (0.2, 0.2, 0.2)
    x0 = rect.x0
    y0 = rect.y0
    w = rect.width
    h = rect.height

    # Corner positions (TL, TR, BR, BL) with flip flags
    corners = [
        (x0, y0, False, False),        # TL: as-is
        (x0 + w, y0, True, False),     # TR: flip x
        (x0 + w, y0 + h, True, True),  # BR: flip x,y
        (x0, y0 + h, False, True),     # BL: flip y
    ]

    # Helper: transform ornament local (dx,dy) to page coords
    def pt(cx, cy, flip_x, flip_y, dx, dy):
        x = cx + (-dx if flip_x else dx)
        y = cy + (-dy if flip_y else dy)
        return fitz.Point(x, y)

    for cx, cy, fx, fy in corners:
        if style == "classic":
            _pdraw(fitz_page, color, [
                ("Q", pt(cx,cy,fx,fy,5,80), pt(cx,cy,fx,fy,5,20), pt(cx,cy,fx,fy,20,20), pt(cx,cy,fx,fy,20,20)),
                ("Q", pt(cx,cy,fx,fy,40,20), pt(cx,cy,fx,fy,45,5), pt(cx,cy,fx,fy,50,0), pt(cx,cy,fx,fy,60,0)),
            ])
            _pdraw(fitz_page, color, [
                ("Q", pt(cx,cy,fx,fy,5,60), pt(cx,cy,fx,fy,5,15), pt(cx,cy,fx,fy,15,10), pt(cx,cy,fx,fy,15,10)),
                ("Q", pt(cx,cy,fx,fy,30,5), pt(cx,cy,fx,fy,35,2), pt(cx,cy,fx,fy,35,2), pt(cx,cy,fx,fy,35,2)),
            ])
            fitz_page.draw_circle(pt(cx,cy,fx,fy,8,8), 2, color=color, fill=color)
            fitz_page.draw_circle(pt(cx,cy,fx,fy,20,5), 1.2, color=color, fill=color)

        elif style == "victorian":
            _pdraw(fitz_page, color, [
                ("C", pt(cx,cy,fx,fy,0,85), pt(cx,cy,fx,fy,10,85), pt(cx,cy,fx,fy,15,70), pt(cx,cy,fx,fy,25,60)),
                ("C", pt(cx,cy,fx,fy,35,50), pt(cx,cy,fx,fy,30,35), pt(cx,cy,fx,fy,20,25), pt(cx,cy,fx,fy,20,25)),
                ("C", pt(cx,cy,fx,fy,15,20), pt(cx,cy,fx,fy,10,15), pt(cx,cy,fx,fy,5,10), pt(cx,cy,fx,fy,5,10)),
            ])
            _pdraw(fitz_page, color, [
                ("C", pt(cx,cy,fx,fy,0,75), pt(cx,cy,fx,fy,8,75), pt(cx,cy,fx,fy,12,65), pt(cx,cy,fx,fy,20,58)),
                ("C", pt(cx,cy,fx,fy,28,51), pt(cx,cy,fx,fy,25,40), pt(cx,cy,fx,fy,18,32), pt(cx,cy,fx,fy,18,32)),
                ("C", pt(cx,cy,fx,fy,14,28), pt(cx,cy,fx,fy,10,24), pt(cx,cy,fx,fy,8,18), pt(cx,cy,fx,fy,8,18)),
            ])
            fitz_page.draw_circle(pt(cx,cy,fx,fy,5,5), 2.5, color=color, fill=color)
            fitz_page.draw_circle(pt(cx,cy,fx,fy,15,12), 1.5, color=color, fill=color)
            fitz_page.draw_circle(pt(cx,cy,fx,fy,25,8), 1, color=color, fill=color)

        elif style == "artdeco":
            fitz_page.draw_rect(fitz.Rect(pt(cx,cy,fx,fy,0,60), pt(cx,cy,fx,fy,40,63)), color=color, fill=color)
            fitz_page.draw_rect(fitz.Rect(pt(cx,cy,fx,fy,0,50), pt(cx,cy,fx,fy,30,53)), color=color, fill=color)
            fitz_page.draw_rect(fitz.Rect(pt(cx,cy,fx,fy,0,40), pt(cx,cy,fx,fy,20,43)), color=color, fill=color)
            fitz_page.draw_rect(fitz.Rect(pt(cx,cy,fx,fy,0,30), pt(cx,cy,fx,fy,10,33)), color=color, fill=color)
            fitz_page.draw_rect(fitz.Rect(pt(cx,cy,fx,fy,40,60), pt(cx,cy,fx,fy,43,85)), color=color, fill=color)
            fitz_page.draw_rect(fitz.Rect(pt(cx,cy,fx,fy,30,50), pt(cx,cy,fx,fy,33,65)), color=color, fill=color)
            fitz_page.draw_rect(fitz.Rect(pt(cx,cy,fx,fy,20,40), pt(cx,cy,fx,fy,23,45)), color=color, fill=color)

        elif style == "laurel":
            _pdraw(fitz_page, color, [
                ("Q", pt(cx,cy,fx,fy,5,80), pt(cx,cy,fx,fy,15,60), pt(cx,cy,fx,fy,10,40), pt(cx,cy,fx,fy,10,40)),
                ("Q", pt(cx,cy,fx,fy,8,30), pt(cx,cy,fx,fy,15,20), pt(cx,cy,fx,fy,15,20), pt(cx,cy,fx,fy,15,20)),
            ])
            fitz_page.draw_circle(pt(cx,cy,fx,fy,14,22), 1.5, color=color, fill=color)
            fitz_page.draw_circle(pt(cx,cy,fx,fy,10,50), 1.2, color=color, fill=color)

        elif style == "gothic":
            _pdraw(fitz_page, color, [
                ("L", pt(cx,cy,fx,fy,0,85), pt(cx,cy,fx,fy,0,40)),
                ("Q", pt(cx,cy,fx,fy,0,40), pt(cx,cy,fx,fy,0,20), pt(cx,cy,fx,fy,15,10), pt(cx,cy,fx,fy,15,10)),
                ("Q", pt(cx,cy,fx,fy,15,10), pt(cx,cy,fx,fy,25,3), pt(cx,cy,fx,fy,30,0), pt(cx,cy,fx,fy,30,0)),
            ])
            _pdraw(fitz_page, color, [
                ("L", pt(cx,cy,fx,fy,5,85), pt(cx,cy,fx,fy,5,45)),
                ("Q", pt(cx,cy,fx,fy,5,45), pt(cx,cy,fx,fy,5,28), pt(cx,cy,fx,fy,18,18), pt(cx,cy,fx,fy,18,18)),
                ("Q", pt(cx,cy,fx,fy,18,18), pt(cx,cy,fx,fy,25,12), pt(cx,cy,fx,fy,28,8), pt(cx,cy,fx,fy,28,8)),
            ])
            _pdraw(fitz_page, color, [
                ("Q", pt(cx,cy,fx,fy,15,0), pt(cx,cy,fx,fy,20,5), pt(cx,cy,fx,fy,22,12), pt(cx,cy,fx,fy,22,12)),
            ])

        elif style == "filigree":
            fitz_page.draw_circle(pt(cx,cy,fx,fy,20,20), 15, color=color)
            fitz_page.draw_circle(pt(cx,cy,fx,fy,20,20), 10, color=color)
            fitz_page.draw_circle(pt(cx,cy,fx,fy,20,20), 5, color=color)
            fitz_page.draw_circle(pt(cx,cy,fx,fy,20,20), 2, color=color, fill=color)
            _pdraw(fitz_page, color, [
                ("Q", pt(cx,cy,fx,fy,20,35), pt(cx,cy,fx,fy,25,50), pt(cx,cy,fx,fy,30,65), pt(cx,cy,fx,fy,30,65)),
            ])
            _pdraw(fitz_page, color, [
                ("Q", pt(cx,cy,fx,fy,35,20), pt(cx,cy,fx,fy,50,25), pt(cx,cy,fx,fy,65,30), pt(cx,cy,fx,fy,65,30)),
            ])
            fitz_page.draw_circle(pt(cx,cy,fx,fy,30,30), 1.5, color=color, fill=color)
            fitz_page.draw_circle(pt(cx,cy,fx,fy,35,35), 1, color=color, fill=color)


# ── Page border ──

def _draw_page_border(fitz_page: fitz.Page, album: Album) -> None:
    """Draw decorative page border."""
    ps = album.page_setup
    if not ps.has_border:
        return

    color = _color_to_rgb(album.color_album_border) if album.color_album_border else (0.2, 0.2, 0.2)

    border_left = _mm_to_pt(ps.margin_left)
    border_top = _mm_to_pt(ps.margin_top)
    border_w = _mm_to_pt(ps.width - ps.margin_left - ps.margin_right)
    border_h = _mm_to_pt(ps.height - ps.margin_top - ps.margin_bottom)

    if ps.border_outer > 0:
        r = fitz.Rect(border_left, border_top, border_left + border_w, border_top + border_h)
        fitz_page.draw_rect(r, color=color, width=_mm_to_pt(ps.border_outer))

    if ps.border_inner1 > 0:
        off = _mm_to_pt(ps.border_outer + ps.border_spacing)
        r = fitz.Rect(border_left + off, border_top + off,
                       border_left + border_w - off, border_top + border_h - off)
        fitz_page.draw_rect(r, color=color, width=_mm_to_pt(ps.border_inner1))

    if ps.border_inner2 > 0:
        off = _mm_to_pt(ps.border_outer + ps.border_spacing +
                        ps.border_inner1 + ps.border_spacing)
        r = fitz.Rect(border_left + off, border_top + off,
                       border_left + border_w - off, border_top + border_h - off)
        fitz_page.draw_rect(r, color=color, width=_mm_to_pt(ps.border_inner2))

    # Draw corner ornaments for ornamental border styles
    border_rect = fitz.Rect(border_left, border_top,
                             border_left + border_w, border_top + border_h)
    if ps.border_style in _ORNAMENTAL_STYLES:
        _draw_corner_ornaments(fitz_page, album, border_rect)
    elif ps.border_style in _EDGE_STYLES:
        _draw_edge_patterns(fitz_page, album, border_rect)


# ── Main generator ──

class PDFGenerator:
    """Generates PDF files from Album data models using direct PyMuPDF drawing."""

    def generate(self, album: Album, output_path: str, base_url: str = None) -> None:
        """Generate a PDF from an Album model."""
        doc = fitz.open()

        for page_data in album.pages:
            ps = album.page_setup
            page_w = _mm_to_pt(ps.width)
            page_h = _mm_to_pt(ps.height)
            page = doc.new_page(width=page_w, height=page_h)

            _draw_page_border(page, album)

            # Draw stamps and text elements
            for stamp in page_data.absolute_stamps:
                if stamp.is_text_element:
                    _draw_text_element(page, stamp)
                else:
                    _draw_stamp(page, stamp, album)

        doc.save(output_path)
        doc.close()

    def generate_to_bytes(self, album: Album) -> bytes:
        """Generate a PDF and return as bytes."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            self.generate(album, tmp.name)
            with open(tmp.name, "rb") as f:
                data = f.read()
            os.unlink(tmp.name)
            return data

    def get_html_preview(self, album: Album) -> str:
        """
        Get HTML representation for live preview.
        Kept for compatibility with the web UI preview panel.
        """
        parts = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'><style>",
            "body{margin:0;padding:20px;background:#f5f5f5;font-family:Arial,sans-serif}",
            ".page{position:relative;background:#fff;margin:0 auto;box-shadow:0 2px 8px rgba(0,0,0,0.15);overflow:hidden}",
            ".stamp{position:absolute;border:0.5pt solid #666;display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden;box-sizing:border-box}",
            ".text-el{position:absolute;overflow:hidden;box-sizing:border-box}",
            "</style></head><body>",
        ]

        for page_data in album.pages:
            ps = album.page_setup
            parts.append(f'<div class="page" style="width:{ps.width}mm;height:{ps.height}mm">')

            # Page border
            if ps.has_border:
                c = album.color_album_border
                color_css = f"rgb({int(c.r*255)},{int(c.g*255)},{int(c.b*255)})" if c else "#333"
                bl = ps.margin_left
                bt = ps.margin_top
                bw = round(ps.width - ps.margin_left - ps.margin_right, 2)
                bh = round(ps.height - ps.margin_top - ps.margin_bottom, 2)
                if ps.border_outer > 0:
                    parts.append(
                        f'<div style="position:absolute;top:{bt}mm;left:{bl}mm;'
                        f'width:{bw}mm;height:{bh}mm;border:{ps.border_outer}mm solid {color_css};"></div>'
                    )
                if ps.border_inner1 > 0:
                    off = ps.border_outer + ps.border_spacing
                    parts.append(
                        f'<div style="position:absolute;top:{bt+off}mm;left:{bl+off}mm;'
                        f'width:{bw-off*2}mm;height:{bh-off*2}mm;border:{ps.border_inner1}mm solid {color_css};"></div>'
                    )

            for stamp in page_data.absolute_stamps:
                x, y, w, h = stamp.abs_x, stamp.abs_y, stamp.width, stamp.height
                if stamp.is_text_element:
                    parts.append(
                        f'<div class="text-el" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;'
                        f'font-size:{stamp.font_size or 12}pt;padding:1mm">'
                        f'{(stamp.description or "").replace("<", "&lt;").replace(">", "&gt;")}</div>'
                    )
                else:
                    parts.append(
                        f'<div class="stamp" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;'
                        f'font-size:{(stamp.font_size or 12) * 0.9}pt">'
                        f'{(stamp.description or "").replace("<", "&lt;").replace(">", "&gt;")}</div>'
                    )

            parts.append("</div>")

        parts.append("</body></html>")
        return "\n".join(parts)
