"""HTML preview renderer.

Builds the HTML/CSS shown in the live preview from Album, Page and Stamp models.
PDF, PNG and SVG export live in pdf.py, raster.py and svg_export.py.
"""

from __future__ import annotations

from stamp_album.core.models import (
    Album,
    FormattedText,
    Page,
    StampShape,
)
from stamp_album.engines.borders import (
    EDGE_STYLES,
    ORNAMENTAL_STYLES,
    SHAPE_POLYGON_VIEWBOX,
    corner_ornament_svg,
    edge_pattern_svg,
)
from stamp_album.engines.layout import layout_rows


def _xml_escape(s: str) -> str:
    """Escape special XML characters."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


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
            if ps.border_style in ORNAMENTAL_STYLES:
                ornament_svg = corner_ornament_svg(ps.border_style, color)
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
            elif ps.border_style in EDGE_STYLES:
                epw = round(bw * px, 1)
                eph = round(bh * px, 1)
                top_svg = edge_pattern_svg(ps.border_style, "top", epw, eph, color)
                bottom_svg = edge_pattern_svg(ps.border_style, "bottom", epw, eph, color)
                left_svg = edge_pattern_svg(ps.border_style, "left", eph, epw, color)
                right_svg = edge_pattern_svg(ps.border_style, "right", eph, epw, color)
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
            StampShape.TRIANGLE: SHAPE_POLYGON_VIEWBOX["TRIANGLE"],
            StampShape.TRIANGLE_INV: SHAPE_POLYGON_VIEWBOX["TRIANGLE_INV"],
            StampShape.DIAMOND: SHAPE_POLYGON_VIEWBOX["DIAMOND"],
            StampShape.HEXAGON: SHAPE_POLYGON_VIEWBOX["HEXAGON"],
            StampShape.OCTAGON: SHAPE_POLYGON_VIEWBOX["OCTAGON"],
            StampShape.PENTAGON: SHAPE_POLYGON_VIEWBOX["PENTAGON"],
        }
        row_layout = layout_rows(self.album)
        page_idx = self._page_counter - 1
        if page_idx < len(row_layout):
            for x, y, stamp in row_layout[page_idx]:
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

        if has_columns:
            parts.append('</div>')  # close column-container

        parts.append('</div>')  # close page-content

        # Absolutely positioned stamps (drag-and-drop) — outside page-content
        # so their coordinates are page-absolute (not offset by padding)
        for stamp in page.absolute_stamps:
            x, y, w, h = stamp.abs_x, stamp.abs_y, stamp.width, stamp.height
            desc = (stamp.description or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            font_size = stamp.font_size or 12

            if stamp.is_text_element:
                font_family = _font_id_to_css(stamp.font_id) if stamp.font_id else "Helvetica,Arial,sans-serif"
                parts.append(
                    f'<div class="text-el" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;'
                    f'font-size:{font_size}pt;line-height:1.3;font-family:{font_family};padding:1mm;word-wrap:break-word;">{desc}</div>'
                )
            else:
                stamp_bc = getattr(stamp, 'border_color', None) or getattr(self.album, 'color_stamp_border', None)
                stamp_fc = getattr(stamp, 'fill_color', None) or getattr(self.album, 'color_stamp_background', None)
                border_color = _color_to_rgb(stamp_bc) if stamp_bc else (0, 0, 0)
                bg_color = _color_to_rgb(stamp_fc) if stamp_fc else (1, 1, 1)
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

                # Philatelic: heading above stamp
                if stamp.heading and stamp.heading.text:
                    hdg_sz = stamp.heading.size or 9
                    parts.append(
                        f'<div style="position:absolute;left:{x}mm;top:{y - 2.5}mm;'
                        f'width:{w}mm;text-align:center;font-size:{hdg_sz}pt;'
                        f'font-weight:600;color:#333;overflow:hidden;'
                        f'white-space:nowrap;text-overflow:ellipsis;">'
                        f'{_xml_escape(stamp.heading.text)}</div>'
                    )

                # Philatelic: catalog references below stamp
                if stamp.catalog_refs:
                    cat_text = " · ".join(stamp.catalog_refs)
                    parts.append(
                        f'<div style="position:absolute;left:{x}mm;top:{y + h + 1}mm;'
                        f'width:{w}mm;text-align:center;font-size:8pt;color:#666;">'
                        f'{_xml_escape(cat_text)}</div>'
                    )

                # Philatelic: footer (denom · cond · perf)
                if stamp.footer_text:
                    parts.append(
                        f'<div style="position:absolute;left:{x}mm;top:{y + h + 0.2}mm;'
                        f'width:{w}mm;text-align:center;font-size:8pt;color:#555;">'
                        f'{_xml_escape(stamp.footer_text)}</div>'
                    )

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


_FONT_CSS_MAP = {
    "CN": "Courier,monospace",
    "CB": "Courier,monospace",
    "CI": "Courier,monospace",
    "CS": "Courier,monospace",
    "TN": "'Times New Roman',Times,serif",
    "TB": "'Times New Roman',Times,serif",
    "TI": "'Times New Roman',Times,serif",
    "TS": "'Times New Roman',Times,serif",
    "HN": "Helvetica,Arial,sans-serif",
    "HB": "Helvetica,Arial,sans-serif",
    "HI": "Helvetica,Arial,sans-serif",
    "HS": "Helvetica,Arial,sans-serif",
}


def _font_id_to_css(font_id: str) -> str:
    return _FONT_CSS_MAP.get(font_id, "Helvetica,Arial,sans-serif")


def _color_to_rgb(color) -> tuple:
    """Convert a Color object to RGB tuple (0-1 range)."""
    if color is None:
        return (0, 0, 0)
    return (max(0, min(1, color.r)), max(0, min(1, color.g)), max(0, min(1, color.b)))
