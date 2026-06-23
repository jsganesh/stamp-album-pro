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

    def _render_styles(self) -> str:
        ps = self.album.page_setup
        w_mm = round(ps.width, 2)
        h_mm = round(ps.height, 2)
        ml = round(ps.margin_left, 2)
        mr = round(ps.margin_right, 2)
        mt = round(ps.margin_top, 2)
        mb = round(ps.margin_bottom, 2)
        return f"""
        <style>
        @page {{ size: {w_mm}mm {h_mm}mm; margin: 0; }}
        body {{ margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; }}
        .page {{ position: relative; width: {w_mm}mm; height: {h_mm}mm; page-break-after: always; box-sizing: border-box; }}
        .page:last-child {{ page-break-after: auto; }}
        .page-content {{ position: relative; z-index: 1; width: 100%; box-sizing: border-box; padding: {mt}mm {mr}mm {mb}mm {ml}mm; overflow: hidden; }}
        .stamp {{ position: absolute; display: flex; align-items: center; justify-content: center; text-align: center; overflow: hidden; box-sizing: border-box; }}
        .text-el {{ position: absolute; overflow: hidden; box-sizing: border-box; }}
        .stamp-box {{ box-sizing: border-box; }}
        </style>"""

    def _render_page(self, page: Page) -> str:
        ps = self.album.page_setup
        parts = [f'<div class="page">', f'<div class="page-content">']

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

        _Y_POS = 20  # Starting Y position in mm
        for row in page.rows:
            _X_POS = 0
            for stamp in row.stamps:
                x, y = _X_POS, _Y_POS
                w, h = stamp.width, stamp.height
                desc = (stamp.description or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                font_size = stamp.font_size or 10
                shape_class = ""
                if stamp.shape == StampShape.OVAL: shape_class = "shape-oval"
                elif stamp.shape == StampShape.TRIANGLE: shape_class = "shape-triangle"
                elif stamp.shape == StampShape.DIAMOND: shape_class = "shape-diamond"
                elif stamp.shape == StampShape.HEXAGON: shape_class = "shape-hexagon"
                elif stamp.shape == StampShape.OCTAGON: shape_class = "shape-octagon"
                elif stamp.shape == StampShape.PENTAGON: shape_class = "shape-pentagon"
                parts.append(
                    f'<div class="stamp" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;">'
                    f'<div class="stamp-box {shape_class}" style="width:{w}mm;height:{h}mm;'
                    f'border:0.5pt solid #666;background-color:#fff;">'
                    f'<div style="font-size:{font_size}pt;padding:1mm;text-align:center;">{desc}</div>'
                    f'</div></div>'
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
                shape_class = ""
                if stamp.shape == StampShape.OVAL: shape_class = "shape-oval"
                elif stamp.shape == StampShape.TRIANGLE: shape_class = "shape-triangle"
                elif stamp.shape == StampShape.DIAMOND: shape_class = "shape-diamond"
                elif stamp.shape == StampShape.HEXAGON: shape_class = "shape-hexagon"
                elif stamp.shape == StampShape.OCTAGON: shape_class = "shape-octagon"
                elif stamp.shape == StampShape.PENTAGON: shape_class = "shape-pentagon"
                desc_font_size = round(font_size * 0.9, 1)
                parts.append(
                    f'<div class="stamp" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;">'
                    f'<div class="stamp-box {shape_class}" style="width:{w}mm;height:{h}mm;'
                    f'border:0.5pt solid {bc};background-color:{bg};">'
                    f'<div style="font-size:{desc_font_size}pt;padding:1mm 2mm;text-align:center;line-height:1.3;">{desc}</div>'
                    f'</div></div>'
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
