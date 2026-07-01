"""
PDF generation engine using WeasyPrint.

Converts Album data models into HTML/CSS and renders to PDF.
This approach provides rich typography, CSS layouts, and modern
text rendering without manual coordinate calculations.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from stamp_album.core.models import (
    Album,
    Color,
    ColumnMode,
    FormattedText,
    Page,
    Row,
    Stamp,
    StampShape,
    TextAlignment,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Base-14 PDF font equivalents mapped to web-safe fonts
BASE14_FONT_MAP = {
    "CN": {"family": "Courier, monospace", "weight": "normal", "style": "normal"},
    "CB": {"family": "Courier, monospace", "weight": "bold", "style": "normal"},
    "CI": {"family": "Courier, monospace", "weight": "normal", "style": "italic"},
    "CS": {"family": "Courier, monospace", "weight": "bold", "style": "italic"},
    "TN": {"family": "'Times New Roman', Times, serif", "weight": "normal", "style": "normal"},
    "TB": {"family": "'Times New Roman', Times, serif", "weight": "bold", "style": "normal"},
    "TI": {"family": "'Times New Roman', Times, serif", "weight": "normal", "style": "italic"},
    "TS": {"family": "'Times New Roman', Times, serif", "weight": "bold", "style": "italic"},
    "HN": {"family": "Helvetica, Arial, sans-serif", "weight": "normal", "style": "normal"},
    "HB": {"family": "Helvetica, Arial, sans-serif", "weight": "bold", "style": "normal"},
    "HI": {"family": "Helvetica, Arial, sans-serif", "weight": "normal", "style": "italic"},
    "HS": {"family": "Helvetica, Arial, sans-serif", "weight": "bold", "style": "italic"},
}


# ---------------------------------------------------------------------------
# HTML Renderer
# ---------------------------------------------------------------------------


class HTMLRenderer:
    """Renders an Album model to HTML/CSS for PDF generation."""

    def __init__(self, album: Album, font_manager=None):
        self.album = album
        self.font_manager = font_manager
        self._page_counter = 0

    def render(self) -> str:
        """Render the entire album to HTML."""
        parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="utf-8">',
            self._render_styles(),
            "</head>",
            "<body>",
        ]

        for page in self.album.pages:
            self._page_counter += 1
            parts.append(self._render_page(page))

        parts.extend(
            [
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(parts)

    def _render_styles(self) -> str:
        """Generate CSS styles for the album."""
        ps = self.album.page_setup

        # Page size in mm
        width_mm = round(ps.width, 2)
        height_mm = round(ps.height, 2)

        # Margins
        ml = round(ps.margin_left, 2)
        mr = round(ps.margin_right, 2)
        mt = round(ps.margin_top, 2)
        mb = round(ps.margin_bottom, 2)

        # Content area dimensions
        content_width = round(ps.width - ps.margin_left - ps.margin_right, 2)
        content_height = round(ps.height - ps.margin_top - ps.margin_bottom, 2)

        styles = f"""
        <style>
        @page {{
            size: {width_mm}mm {height_mm}mm;
            margin: 0;
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, Helvetica, sans-serif;
        }}

        .page {{
            position: relative;
            width: {width_mm}mm;
            height: {height_mm}mm;
            page-break-after: always;
            box-sizing: border-box;
        }}

        .page:last-child {{
            page-break-after: auto;
        }}

        .page-border {{
            position: absolute;
            top: 0;
            left: 0;
            width: {width_mm}mm;
            height: {height_mm}mm;
            pointer-events: none;
            z-index: 100;
        }}

        .page-content {{
            position: relative;
            z-index: 1;
            width: 100%;
            min-height: {content_height}mm;
            box-sizing: border-box;
            padding: {mt}mm {mr}mm {mb}mm {ml}mm;
        }}

        .page-title {{
            text-align: center;
            margin-bottom: {ps.vspace}mm;
            font-weight: bold;
        }}

        .page-text {{
            margin-bottom: {ps.vspace}mm;
            line-height: 1.4;
        }}

        .page-text.center {{
            text-align: center;
        }}

        .page-text.right {{
            text-align: right;
        }}

        .page-text.justify {{
            text-align: justify;
        }}

        .stamp-row {{
            display: flex;
            flex-wrap: nowrap;
            margin-bottom: {ps.vspace}mm;
            align-items: flex-start;
            width: 100%;
            box-sizing: border-box;
        }}

        .stamp-row.align-middle {{
            align-items: center;
        }}

        .stamp-row.align-bottom {{
            align-items: flex-end;
        }}

        .stamp {{
            display: flex;
            flex-direction: column;
            align-items: center;
            box-sizing: border-box;
        }}

        .stamp-box {{
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .stamp-box.shape-oval {{
            border-radius: 50%;
        }}

        .stamp-box.shape-triangle {{
            clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
        }}

        .stamp-box.shape-triangle-inv {{
            clip-path: polygon(0% 0%, 100% 0%, 50% 100%);
        }}

        .stamp-box.shape-diamond {{
            clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
        }}

        .stamp-box.shape-hexagon {{
            clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%);
        }}

        .stamp-box.shape-octagon {{
            clip-path: polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%);
        }}

        .stamp-box.shape-pentagon {{
            clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);
        }}

        .stamp-image {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}

        .stamp-heading {{
            text-align: center;
            margin-top: 1mm;
            margin-bottom: 0.5mm;
            font-weight: bold;
            line-height: 1.2;
        }}

        .stamp-footer {{
            text-align: center;
            margin-top: 0.5mm;
            line-height: 1.2;
            max-width: 100%;
            word-wrap: break-word;
        }}

        .stamp-catalog {{
            text-align: center;
            margin-top: 0.25mm;
            font-size: 0.8em;
            color: #666;
            line-height: 1.2;
            max-width: 100%;
            word-wrap: break-word;
        }}

        .h-rule {{
            border: none;
            border-top: 0.5pt solid black;
            margin: 2mm 0;
        }}

        .header {{
            position: absolute;
            top: 0;
            left: {ml}mm;
            right: {mr}mm;
            height: {mt}mm;
            font-size: 0.9em;
            display: flex;
            align-items: center;
        }}

        .footer {{
            position: absolute;
            bottom: 0;
            left: {ml}mm;
            right: {mr}mm;
            height: {mb}mm;
            font-size: 0.9em;
            display: flex;
            align-items: center;
        }}

        .margin-text {{
            position: absolute;
            writing-mode: vertical-rl;
            font-size: 0.8em;
            top: {mt}mm;
            bottom: {mb}mm;
            display: flex;
            align-items: center;
        }}

        .margin-text.left {{
            left: 0;
            width: {ml}mm;
            justify-content: flex-start;
            padding-left: 1mm;
        }}

        .margin-text.right {{
            right: 0;
            width: {mr}mm;
            justify-content: flex-end;
            padding-right: 1mm;
        }}

        .quadrille {{
            background-image: linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px);
            background-size: 5mm 5mm;
        }}

        .column-container {{
            display: grid;
            gap: 10mm;
        }}

        .column-container.cols-2 {{
            grid-template-columns: 1fr 1fr;
        }}

        .column-container.cols-3 {{
            grid-template-columns: 1fr 1fr 1fr;
        }}

        .background-image {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: -1;
            opacity: 0.3;
        }}

        .vspace {{
            height: 1mm;
        }}
        </style>
        """
        return styles

    def _render_page(self, page: Page) -> str:
        """Render a single page to HTML."""
        ps = self.album.page_setup
        parts = ['<div class="page">']

        # Background image
        if page.background_image:
            parts.append(f'<img class="background-image" src="{page.background_image}" alt="">')

        # Decorative border or line border
        if ps.decorative_border_file:
            parts.append(self._render_decorative_border(ps.decorative_border_file))
        elif ps.has_border:
            parts.append(self._render_line_border())

        # Header (in top margin)
        if ps.header_text:
            parts.append(self._render_header_footer(ps.header_text, "header"))

        # Margin text (in side margins)
        if hasattr(ps, "margin_texts"):
            for margin_item in ps.margin_texts:
                parts.append(self._render_margin_text(margin_item))

        # Content area (inside margins)
        parts.append('<div class="page-content">')

        # Title
        if ps.title:
            parts.append(self._render_text_element(ps.title, "title"))

        # Page content
        content_class = ""
        if page.column_mode == ColumnMode.TWO:
            content_class = "column-container cols-2"
        elif page.column_mode == ColumnMode.THREE:
            content_class = "column-container cols-3"
        if content_class:
            gap_mm = round(page.column_gap, 2) if page.column_gap > 0 else 10.0
            parts.append(f'<div class="{content_class}" style="gap: {gap_mm}mm;">')

        # Quadrille
        if page.quadrille:
            parts.append(self._render_quadrille(page.quadrille))

        # Render content in sequential order using content_flow
        if page.content_flow:
            for content_type, content_data in page.content_flow:
                if content_type == "text":
                    parts.append(self._render_text_element(content_data))
                elif content_type == "paragraph":
                    parts.append(self._render_paragraph(content_data))
                elif content_type == "row":
                    parts.append(self._render_row(content_data))
                elif content_type == "vspace":
                    vspace_val = content_data
                    if vspace_val != 0:
                        if vspace_val > 0:
                            parts.append(f'<div class="vspace" style="height: {vspace_val}mm;"></div>')
                        else:
                            # Negative vspace: use negative margin to pull content up
                            parts.append(f'<div class="vspace" style="margin-top: {vspace_val}mm;"></div>')
        else:
            # Fallback to legacy grouped rendering if content_flow is empty
            # Text elements
            for text_elem in page.text_elements:
                parts.append(self._render_text_element(text_elem))

            # Paragraphs
            for paragraph in page.paragraphs:
                parts.append(self._render_paragraph(paragraph))

            # Horizontal rules
            h_rule_color = self._color_to_css(
                self.album.color_h_rule or Color(r=0.0, g=0.0, b=0.0)
            )
            for line, spacing, margin in page.h_rules:
                parts.append(
                    f'<hr class="h-rule" style="border-top-width: {line}mm; '
                    f"border-top-color: {h_rule_color}; "
                    f'margin: {spacing}mm {margin}mm;">'
                )

            # VSpace
            if page.vspace > 0:
                parts.append(f'<div class="vspace" style="height: {page.vspace}mm;"></div>')

            # Stamp rows
            for row in page.rows:
                parts.append(self._render_row(row))

        # Boxes
        for x, y, w, h in page.boxes:
            parts.append(
                f'<div style="position: absolute; left: {x}mm; top: {y}mm; '
                f'width: {w}mm; height: {h}mm; border: 0.5pt solid black;"></div>'
            )

        # Absolutely positioned stamps (drag-and-drop)
        for stamp in page.absolute_stamps:
            if stamp.is_text_element:
                txt = (stamp.description or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                font_css = self._font_to_css(stamp.font_id, stamp.font_size)
                parts.append(
                    f'<div style="position:absolute;left:{stamp.abs_x}mm;top:{stamp.abs_y}mm;'
                    f'width:{stamp.width}mm;height:{stamp.height}mm;'
                    f'{font_css};'
                    f'color:#333;word-wrap:break-word;overflow:hidden;'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'text-align:center;white-space:pre-wrap;line-height:1.3;">'
                    f'{txt}</div>'
                )
                continue
            ps = self.album.page_setup
            width = stamp.width + ps.stamp_box_adjust
            height = stamp.height + ps.stamp_box_adjust
            border_color = self._color_to_css(self.album.color_stamp_border or Color(r=0.5, g=0.5, b=0.5))
            bg_color = self._color_to_css(self.album.color_stamp_background or Color(r=1.0, g=1.0, b=1.0))
            shape_class = ""
            if stamp.shape == StampShape.OVAL: shape_class = "shape-oval"
            elif stamp.shape == StampShape.TRIANGLE: shape_class = "shape-triangle"
            elif stamp.shape == StampShape.DIAMOND: shape_class = "shape-diamond"
            elif stamp.shape == StampShape.HEXAGON: shape_class = "shape-hexagon"
            elif stamp.shape == StampShape.OCTAGON: shape_class = "shape-octagon"
            elif stamp.shape == StampShape.PENTAGON: shape_class = "shape-pentagon"
            desc_font = self._font_to_css(stamp.font_id, round(stamp.font_size * 0.9, 1)) if stamp.font_id else ""
            desc = self._format_text(stamp.description) if stamp.description else ""
            if desc:
                desc = f'<div style="{desc_font};padding:1mm 2mm;text-align:center;line-height:1.3;">{desc}</div>'
            parts.append(
                f'<div class="stamp" style="position:absolute;left:{stamp.abs_x}mm;top:{stamp.abs_y}mm;width:{width}mm;">'
                f'<div class="stamp-box {shape_class}" style="width:{width}mm;height:{height}mm;'
                f'border:0.5pt solid {border_color};background-color:{bg_color};">'
                f'{desc}</div></div>'
            )

        if content_class:
            parts.append("</div>")

        parts.append("</div>")  # close page-content

        # Footer (in bottom margin)
        if ps.footer_text:
            parts.append(self._render_header_footer(ps.footer_text, "footer"))

        parts.append("</div>")
        return "\n".join(parts)

    def _render_line_border(self) -> str:
        """Render page line border using mm units consistently."""
        ps = self.album.page_setup
        color = self._color_to_css(self.album.color_album_border)

        # Border rectangle: positioned at margin boundary
        border_left = ps.margin_left
        border_top = ps.margin_top
        border_width = round(ps.width - ps.margin_left - ps.margin_right, 2)
        border_height = round(ps.height - ps.margin_top - ps.margin_bottom, 2)

        parts = ['<div class="page-border">']

        if ps.border_outer > 0:
            parts.append(
                f'<div style="position: absolute; '
                f"top: {border_top}mm; left: {border_left}mm; "
                f"width: {border_width}mm; height: {border_height}mm; "
                f'border: {ps.border_outer}mm solid {color};"></div>'
            )

        if ps.border_inner1 > 0:
            offset = ps.border_outer + ps.border_spacing
            parts.append(
                f'<div style="position: absolute; '
                f"top: {border_top + offset}mm; left: {border_left + offset}mm; "
                f"width: {round(border_width - offset * 2, 2)}mm; height: {round(border_height - offset * 2, 2)}mm; "
                f'border: {ps.border_inner1}mm solid {color};"></div>'
            )

        if ps.border_inner2 > 0:
            offset = ps.border_outer + ps.border_inner1 + ps.border_spacing * 2
            parts.append(
                f'<div style="position: absolute; '
                f"top: {border_top + offset}mm; left: {border_left + offset}mm; "
                f"width: {round(border_width - offset * 2, 2)}mm; height: {round(border_height - offset * 2, 2)}mm; "
                f'border: {ps.border_inner2}mm solid {color};"></div>'
            )

        parts.append("</div>")
        return "\n".join(parts)

    def _render_decorative_border(self, border_style: str) -> str:
        """Render decorative border using CSS/SVG."""
        ps = self.album.page_setup
        color = self._color_to_css(self.album.color_album_border)

        border_left = ps.margin_left
        border_top = ps.margin_top
        border_width = round(ps.width - ps.margin_left - ps.margin_right, 2)
        border_height = round(ps.height - ps.margin_top - ps.margin_bottom, 2)

        parts = ['<div class="page-border">']

        if border_style == "geometric":
            # Geometric: stepped corners with angular patterns
            parts.append(
                f'<div style="position: absolute; '
                f'top: {border_top}mm; left: {border_left}mm; '
                f'width: {border_width}mm; height: {border_height}mm; '
                f'border: 0.5mm solid {color};"></div>'
            )
            # Angular corner decorations - centered on border corners
            corner_size = 8
            half = corner_size / 2
            for cx, cy in [(border_left, border_top),
                           (border_left + border_width, border_top),
                           (border_left, border_top + border_height),
                           (border_left + border_width, border_top + border_height)]:
                parts.append(
                    f'<div style="position: absolute; '
                    f'top: {cy - half}mm; left: {cx - half}mm; '
                    f'width: {corner_size}mm; height: {corner_size}mm; '
                    f'border: 0.3mm solid {color};"></div>'
                )

        elif border_style == "vine":
            # Vine: organic curved corners with botanical elements
            parts.append(
                f'<div style="position: absolute; '
                f'top: {border_top}mm; left: {border_left}mm; '
                f'width: {border_width}mm; height: {border_height}mm; '
                f'border: 0.3mm solid {color};"></div>'
            )
            # Corner flourishes using SVG - centered on border corners
            svg_size = 12
            half = svg_size / 2
            svg_corner = f'''<svg width="{svg_size}mm" height="{svg_size}mm" viewBox="0 0 {svg_size} {svg_size}" style="position: absolute;">
                <path d="M{half},{half} Q{svg_size},{half} {svg_size},{svg_size} Q{svg_size},0 {half},0" fill="none" stroke="{color}" stroke-width="0.3"/>
                <circle cx="{half + 1}" cy="{half + 1}" r="1" fill="{color}"/>
                <circle cx="{svg_size - 1}" cy="{half + 1}" r="0.5" fill="{color}"/>
                <circle cx="{half + 1}" cy="{svg_size - 1}" r="0.5" fill="{color}"/>
            </svg>'''
            positions = [
                (border_left, border_top, ""),
                (border_left + border_width, border_top, "transform: scaleX(-1)"),
                (border_left, border_top + border_height, "transform: scaleY(-1)"),
                (border_left + border_width, border_top + border_height, "transform: scale(-1, -1)"),
            ]
            for x, y, transform in positions:
                parts.append(
                    f'<div style="position: absolute; top: {y - half}mm; left: {x - half}mm; {transform}">'
                    f'{svg_corner}</div>'
                )

        elif border_style == "elegant":
            # Elegant: smooth curved corners with inner frame
            parts.append(
                f'<div style="position: absolute; '
                f'top: {border_top}mm; left: {border_left}mm; '
                f'width: {border_width}mm; height: {border_height}mm; '
                f'border: 0.4mm solid {color}; border-radius: 2mm;"></div>'
            )
            # Inner decorative line
            inset = 2
            parts.append(
                f'<div style="position: absolute; '
                f'top: {border_top + inset}mm; left: {border_left + inset}mm; '
                f'width: {round(border_width - inset * 2, 2)}mm; height: {round(border_height - inset * 2, 2)}mm; '
                f'border: 0.2mm solid {color}; border-radius: 1.5mm;"></div>'
            )

        elif border_style == "accent":
            # Accent: decorative corners without connecting lines
            svg_size = 15
            half = svg_size / 2
            svg_corner = f'''<svg width="{svg_size}mm" height="{svg_size}mm" viewBox="0 0 {svg_size} {svg_size}" style="position: absolute;">
                <path d="M{half},{half} L{svg_size},{half} L{svg_size},{half + 3} L{half + 3},{half + 3} L{half + 3},{svg_size} L{half},{svg_size} Z" fill="none" stroke="{color}" stroke-width="0.4"/>
                <path d="M{half + 5},{half} Q{half + 8},{half + 3} {half + 5},{half + 6}" fill="none" stroke="{color}" stroke-width="0.3"/>
                <circle cx="{half + 2}" cy="{half + 2}" r="0.8" fill="{color}"/>
            </svg>'''
            positions = [
                (border_left, border_top, ""),
                (border_left + border_width, border_top, "transform: scaleX(-1)"),
                (border_left, border_top + border_height, "transform: scaleY(-1)"),
                (border_left + border_width, border_top + border_height, "transform: scale(-1, -1)"),
            ]
            for x, y, transform in positions:
                parts.append(
                    f'<div style="position: absolute; top: {y - half}mm; left: {x - half}mm; {transform}">'
                    f'{svg_corner}</div>'
                )

        elif border_style == "dashed":
            parts.append(
                f'<div style="position: absolute; '
                f'top: {border_top}mm; left: {border_left}mm; '
                f'width: {border_width}mm; height: {border_height}mm; '
                f'border: 0.5mm dashed {color};"></div>'
            )

        elif border_style == "dotted":
            parts.append(
                f'<div style="position: absolute; '
                f'top: {border_top}mm; left: {border_left}mm; '
                f'width: {border_width}mm; height: {border_height}mm; '
                f'border: 0.5mm dotted {color};"></div>'
            )

        elif border_style == "diamond":
            # Diamond: repeating diamond pattern border
            parts.append(
                f'<div style="position: absolute; '
                f'top: {border_top}mm; left: {border_left}mm; '
                f'width: {border_width}mm; height: {border_height}mm; '
                f'border: 0.4mm solid {color};"></div>'
            )
            # Diamond corner accents - centered on border corners
            svg_size = 10
            half = svg_size / 2
            svg_diamond = f'''<svg width="{svg_size}mm" height="{svg_size}mm" viewBox="0 0 {svg_size} {svg_size}" style="position: absolute;">
                <polygon points="{half},0 {svg_size},{half} {half},{svg_size} 0,{half}" fill="none" stroke="{color}" stroke-width="0.3"/>
                <polygon points="{half},2 {svg_size - 2},{half} {half},{svg_size - 2} 2,{half}" fill="{color}"/>
            </svg>'''
            positions = [
                (border_left, border_top, ""),
                (border_left + border_width, border_top, ""),
                (border_left, border_top + border_height, ""),
                (border_left + border_width, border_top + border_height, ""),
            ]
            for x, y, transform in positions:
                parts.append(
                    f'<div style="position: absolute; top: {y - half}mm; left: {x - half}mm; {transform}">'
                    f'{svg_diamond}</div>'
                )

        elif border_style == "greek":
            # Greek Key: meander pattern border
            parts.append(
                f'<div style="position: absolute; '
                f'top: {border_top}mm; left: {border_left}mm; '
                f'width: {border_width}mm; height: {border_height}mm; '
                f'border: 0.5mm solid {color};"></div>'
            )
            # Greek key corner elements - centered on border corners
            svg_size = 14
            half = svg_size / 2
            svg_greek = f'''<svg width="{svg_size}mm" height="{svg_size}mm" viewBox="0 0 {svg_size} {svg_size}" style="position: absolute;">
                <path d="M{half},{half} L{svg_size},{half} L{svg_size},{half + 4} L{half + 4},{half + 4} L{half + 4},{svg_size - 4} L{svg_size - 4},{svg_size - 4} L{svg_size - 4},{half + 6} L{half + 6},{half + 6} L{half + 6},{half + 8} L{half + 8},{half + 8} L{half + 8},{half + 4} L2,{half + 4} L2,{svg_size - 2} L{svg_size - 2},{svg_size - 2}" 
                      fill="none" stroke="{color}" stroke-width="0.4"/>
            </svg>'''
            positions = [
                (border_left, border_top, ""),
                (border_left + border_width, border_top, "transform: scaleX(-1)"),
                (border_left, border_top + border_height, "transform: scaleY(-1)"),
                (border_left + border_width, border_top + border_height, "transform: scale(-1, -1)"),
            ]
            for x, y, transform in positions:
                parts.append(
                    f'<div style="position: absolute; top: {y - half}mm; left: {x - half}mm; {transform}">'
                    f'{svg_greek}</div>'
                )

        elif border_style == "zigzag":
            # Zigzag: sawtooth pattern border
            parts.append(
                f'<div style="position: absolute; '
                f'top: {border_top}mm; left: {border_left}mm; '
                f'width: {border_width}mm; height: {border_height}mm; '
                f'border: 0.4mm solid {color};"></div>'
            )
            # Zigzag corner accents - centered on border corners
            svg_size = 12
            half = svg_size / 2
            svg_zigzag = f'''<svg width="{svg_size}mm" height="{svg_size}mm" viewBox="0 0 {svg_size} {svg_size}" style="position: absolute;">
                <polyline points="{half},{half} {half + 3},{half + 3} {half},{half + 6} {half + 3},{half + 9} {half},{svg_size - half}" fill="none" stroke="{color}" stroke-width="0.3"/>
                <polyline points="{svg_size - half},{half} {svg_size - half - 3},{half + 3} {svg_size - half},{half + 6} {svg_size - half - 3},{half + 9} {svg_size - half},{svg_size - half}" fill="none" stroke="{color}" stroke-width="0.3"/>
                <polyline points="{half},{half} {half + 3},{half} {half + 6},{half + 3} {half + 9},{half} {svg_size - half},{half}" fill="none" stroke="{color}" stroke-width="0.3"/>
            </svg>'''
            positions = [
                (border_left, border_top, ""),
                (border_left + border_width, border_top, "transform: scaleX(-1)"),
                (border_left, border_top + border_height, "transform: scaleY(-1)"),
                (border_left + border_width, border_top + border_height, "transform: scale(-1, -1)"),
            ]
            for x, y, transform in positions:
                parts.append(
                    f'<div style="position: absolute; top: {y - half}mm; left: {x - half}mm; {transform}">'
                    f'{svg_zigzag}</div>'
                )

        else:
            # Fallback to line border
            return self._render_line_border()

        parts.append("</div>")
        return "\n".join(parts)

    def _render_header_footer(self, text: FormattedText, css_class: str) -> str:
        """Render header or footer text."""
        content = text.content
        # Substitute tokens
        content = content.replace("$PAGE$", str(self._page_counter))
        content = content.replace("$DATE$", date.today().strftime("%Y-%m-%d"))
        content = content.replace("$PAGES$", str(len(self.album.pages)))

        font_css = self._font_to_css(text.font_id, text.size)
        elem_type = "header" if css_class == "header" else "footer"
        color_css = self._color_to_css(self._resolve_color(text.color, elem_type))

        return (
            f'<div class="{css_class}" style="{font_css}; color: {color_css};">'
            f"{self._format_text(content)}</div>"
        )

    def _render_margin_text(self, item) -> str:
        """Render vertical margin text."""
        font_css = self._font_to_css(item.font_id, item.size)
        color_css = self._color_to_css(self.album.color_margin_text)
        position_class = "left" if item.position.name in ("LEFT", "LEFT_RIGHT") else "right"

        return (
            f'<div class="margin-text {position_class}" '
            f'style="{font_css}; color: {color_css};">'
            f"{self._format_text(item.text)}</div>"
        )

    def _resolve_color(self, text_color, element_type="page_text"):
        """Resolve the effective color for a text element.

        Checks in order: element color, then album-level color for that element type.
        """
        if text_color is not None:
            return text_color

        color_map = {
            "title": self.album.color_title,
            "header": self.album.color_header,
            "footer": self.album.color_footer,
            "margin_text": self.album.color_margin_text,
            "page_text": self.album.color_page_text,
            "stamp_heading": self.album.color_stamp_heading,
            "stamp_text": self.album.color_stamp_text,
        }
        return color_map.get(element_type)

    def _render_text_element(self, text: FormattedText, element_type: str = "page_text") -> str:
        """Render a formatted text element."""
        align_class = ""
        if text.alignment == TextAlignment.CENTER:
            align_class = "center"
        elif text.alignment == TextAlignment.RIGHT:
            align_class = "right"
        elif text.alignment == TextAlignment.JUSTIFY:
            align_class = "justify"

        font_css = self._font_to_css(text.font_id, text.size)
        color_css = self._color_to_css(self._resolve_color(text.color, element_type))
        vspace = f"margin-bottom: {text.vspace}mm;" if text.vspace > 0 else ""

        # Phase 4: Advanced typography
        typography_css = self._build_typography_css(text)

        # Drop cap
        drop_cap_css = ""
        if hasattr(text, "drop_cap_lines") and text.drop_cap_lines > 0:
            drop_cap_css = "float: left; font-size: " + str(text.size * text.drop_cap_lines) + "pt; "

        return (
            f'<div class="page-text {align_class}" '
            f'style="{font_css}; color: {color_css}; {vspace}{typography_css}{drop_cap_css}">'
            f"{self._format_text(text.content)}</div>"
        )

    def _render_paragraph(self, paragraph) -> str:
        """Render a paragraph."""
        align_class = ""
        if paragraph.alignment.name == "CENTER":
            align_class = "center"
        elif paragraph.alignment.name == "RIGHT":
            align_class = "right"
        elif paragraph.alignment.name == "JUSTIFY":
            align_class = "justify"

        font_css = self._font_to_css(paragraph.font_id, paragraph.size)
        color_css = self._color_to_css(self._resolve_color(paragraph.color, "page_text"))

        # Phase 4: Advanced typography
        typography_css = self._build_typography_css(paragraph)

        lines = "<br>".join(self._format_text(line) for line in paragraph.lines)

        return (
            f'<div class="page-text {align_class}" style="{font_css}; color: {color_css};'
            f'{typography_css}">{lines}</div>'
        )

    def _build_typography_css(self, text) -> str:
        """Build CSS for advanced typography effects."""
        parts = []

        # Font weight and style
        if hasattr(text, "weight") and text.weight and text.weight != "normal":
            parts.append(f"font-weight: {text.weight};")
        if hasattr(text, "style") and text.style and text.style != "normal":
            parts.append(f"font-style: {text.style};")

        # Text shadow
        if hasattr(text, "shadow") and text.shadow:
            s = text.shadow
            color = self._color_to_css(s.color)
            opacity = s.opacity
            # Convert mm to px for CSS (1mm ≈ 3.78px)
            px_factor = 3.78
            x = s.offset_x * px_factor
            y = s.offset_y * px_factor
            blur = s.blur * px_factor
            # Use rgba for opacity
            r, g, b = int(s.color.r * 255), int(s.color.g * 255), int(s.color.b * 255)
            parts.append(f"text-shadow: {x}px {y}px {blur}px rgba({r}, {g}, {b}, {opacity});")

        # Text outline (using -webkit-text-stroke for WeasyPrint compatibility)
        if hasattr(text, "outline") and text.outline:
            o = text.outline
            color = self._color_to_css(o.color)
            width_pt = o.width * 2.835  # mm to pt
            parts.append(f"-webkit-text-stroke: {width_pt}pt {color};")

        # Gradient fill
        if hasattr(text, "gradient") and text.gradient and text.gradient.stops:
            g = text.gradient
            if g.direction == "horizontal":
                angle = "90deg"
            elif g.direction == "vertical":
                angle = "180deg"
            else:  # diagonal
                angle = "135deg"
            stops_css = ", ".join(
                f"{self._color_to_css(stop.color)} {stop.offset * 100}%" for stop in g.stops
            )
            parts.append(f"background: linear-gradient({angle}, {stops_css});")
            parts.append("-webkit-background-clip: text;")
            parts.append("-webkit-text-fill-color: transparent;")

        return " ".join(parts)

    def _render_row(self, row: Row) -> str:
        """Render a row of stamps."""
        align_class = ""
        justify_style = ""
        if row.alignment.name == "MIDDLE":
            align_class = "align-middle"
        elif row.alignment.name == "BOTTOM":
            align_class = "align-bottom"

        if row.style.name == "EQUAL_SPACE":
            justify_style = "justify-content: space-between;"
        elif row.style.name == "JUSTIFIED_SPACE":
            justify_style = "justify-content: space-between;"

        parts = [
            f'<div class="stamp-row {align_class}" style="gap: {row.spacing}mm; {justify_style}">'
        ]

        for stamp in row.stamps:
            parts.append(self._render_stamp(stamp, row))

        parts.append("</div>")
        return "\n".join(parts)

    def _render_stamp(self, stamp: Stamp, row: Row) -> str:
        """Render a single stamp."""
        ps = self.album.page_setup
        width = stamp.width
        height = stamp.height

        # Apply box adjust
        width += ps.stamp_box_adjust
        height += ps.stamp_box_adjust

        shape_class = ""
        if stamp.shape == StampShape.OVAL:
            shape_class = "shape-oval"
        elif stamp.shape == StampShape.TRIANGLE:
            shape_class = "shape-triangle"
        elif stamp.shape == StampShape.TRIANGLE_INV:
            shape_class = "shape-triangle-inv"
        elif stamp.shape == StampShape.DIAMOND:
            shape_class = "shape-diamond"
        elif stamp.shape == StampShape.HEXAGON:
            shape_class = "shape-hexagon"
        elif stamp.shape == StampShape.OCTAGON:
            shape_class = "shape-octagon"
        elif stamp.shape == StampShape.PENTAGON:
            shape_class = "shape-pentagon"

        border_color = self._color_to_css(
            self.album.color_stamp_border or Color(r=0.5, g=0.5, b=0.5)
        )
        bg_color = self._color_to_css(
            self.album.color_stamp_background or Color(r=1.0, g=1.0, b=1.0)
        )

        # Map border style
        border_style_map = {
            "SOLID": "solid",
            "DASHED": "dashed",
            "DOTTED": "dotted",
            "BLANK": "none",
        }
        border_style = border_style_map.get(
            ps.stamp_border_settings.style.name, "solid"
        )

        parts = [
            f'<div class="stamp" style="width: {width}mm;">',
            f'<div class="stamp-box {shape_class}" '
            f'style="width: {width}mm; height: {height}mm; '
            f"border: 0.5pt {border_style} {border_color}; "
            f'background-color: {bg_color};">',
        ]

        # Stamp image
        if stamp.image_path and not ps.stamp_image_settings.hidden:
            parts.append(
                f'<img class="stamp-image" src="{stamp.image_path}" alt="{stamp.description}">'
            )

        parts.append("</div>")

        # Stamp heading
        if stamp.heading:
            heading_color = self._color_to_css(
                self._resolve_color(None, "stamp_heading")
            )
            font_css = self._font_to_css(stamp.heading.font_id, stamp.heading.size)
            parts.append(
                f'<div class="stamp-heading" style="{font_css}; color: {heading_color};">'
                f"{self._format_text(stamp.heading.text)}</div>"
            )

        # Stamp description
        if stamp.description:
            text_color = self._color_to_css(
                self._resolve_color(None, "stamp_text")
            )
            font_css = self._font_to_css(row.font_id, row.size)
            parts.append(
                f'<div class="stamp-footer" style="{font_css}; color: {text_color};">'
                f"{self._format_text(stamp.description)}</div>"
            )

        # Catalog references
        catalog_parts = [c for c in stamp.catalog_refs if c]
        if catalog_parts:
            text_color = self._color_to_css(
                self._resolve_color(None, "stamp_text")
            )
            font_css = self._font_to_css(row.font_id, round(row.size * 0.8, 1))
            catalog_text = " | ".join(catalog_parts)
            parts.append(
                f'<div class="stamp-catalog" style="{font_css}; color: {text_color};">'
                f"{catalog_text}</div>"
            )

        parts.append("</div>")
        return "\n".join(parts)

    def _render_quadrille(self, quadrille) -> str:
        """Render quadrille/grid pattern."""
        grid_size = quadrille.grid_size
        color = self._color_to_css(quadrille.grid_color or Color(r=0.8, g=0.8, b=0.8))

        return (
            f'<div class="quadrille" style="width: {quadrille.width}mm; '
            f"height: {quadrille.height}mm; "
            f"background-size: {grid_size}mm {grid_size}mm; "
            f"background-image: linear-gradient({color} 0.1mm, transparent 0.1mm), "
            f'linear-gradient(90deg, {color} 0.1mm, transparent 0.1mm);">'
            f"</div>"
        )

    def _format_text(self, text: str) -> str:
        """Format text for HTML output, handling newlines, special chars, and inline formatting."""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = self._parse_inline_formatting(text)
        text = text.replace("\n", "<br>")
        return text

    def _parse_inline_formatting(self, text: str) -> str:
        """Parse inline formatting markers: **bold**, *italic*, _underline_, ~~strikethrough~~, `code`, ^sup^, ~sub~"""
        import re
        text = re.sub(r'\\\*', '\x00AST\x00', text)
        text = re.sub(r'\\\_', '\x00US\x00', text)
        text = re.sub(r'\\\~', '\x00TIL\x00', text)
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'(?<!\\)_(.+?)_(?!_)', r'<em>\1</em>', text)
        text = re.sub(r'`(.+?)`', r'<code style="font-family:monospace;background:rgba(0,0,0,0.05);padding:1px 3px;border-radius:2px">\1</code>', text)
        text = re.sub(r'\^(.+?)\^', r'<sup>\1</sup>', text)
        text = re.sub(r'(?<!<)~(.+?)~(?!>)', r'<sub>\1</sub>', text)
        text = text.replace('\x00AST\x00', '*').replace('\x00US\x00', '_').replace('\x00TIL\x00', '~')
        return text

    def _font_to_css(self, font_id: str, size: float) -> str:
        """Convert a font ID to CSS font properties."""
        if font_id in BASE14_FONT_MAP:
            mapping = BASE14_FONT_MAP[font_id]
            parts = [f"font-family: {mapping['family']}", f"font-size: {size}pt"]
            if mapping["weight"] != "normal":
                parts.append(f"font-weight: {mapping['weight']}")
            if mapping["style"] != "normal":
                parts.append(f"font-style: {mapping['style']}")
            return "; ".join(parts)

        # User-defined font - try to resolve via font manager
        if self.font_manager:
            font_info = self.font_manager.find_font(font_id)
            if font_info:
                return f"font-family: '{font_info.name}'; font-size: {size}pt"

        # Fallback — use the font_id as a family name with system fallback
        safe_name = font_id.replace("'", "\\'")
        return f"font-family: '{safe_name}', Helvetica, Arial, sans-serif; font-size: {size}pt"

    def _color_to_css(self, color: Optional[Color]) -> str:
        """Convert a Color object to CSS color string."""
        if color is None:
            return "black"

        r = int(color.r * 255)
        g = int(color.g * 255)
        b = int(color.b * 255)
        return f"rgb({r}, {g}, {b})"


# ---------------------------------------------------------------------------
# PDF Generator
# ---------------------------------------------------------------------------


class PDFGenerator:
    """
    Generates PDF files from Album models using WeasyPrint.

    Converts the album data to HTML/CSS, then renders to PDF.
    """

    def __init__(self, font_manager=None):
        self.font_manager = font_manager

    def generate(self, album: Album, output_path: str, base_url: str = None) -> None:
        """
        Generate a PDF from an Album model.

        Args:
            album: The album data model
            output_path: Path to write the PDF file
            base_url: Base URL for resolving relative image paths
        """
        from weasyprint import HTML
        import re

        renderer = HTMLRenderer(album, self.font_manager)
        html_content = renderer.render()

        # Replace image paths with absolute URLs if base_url provided
        if base_url:
            html_content = re.sub(
                r'src="([^"/][^"]*\.(?:png|jpg|jpeg|gif|bmp|tiff|tif|webp))"',
                rf'src="{base_url}/images/\1"',
                html_content
            )

        # Write PDF
        HTML(string=html_content, base_url=base_url).write_pdf(output_path)

    def generate_to_bytes(self, album: Album, base_url: str = None) -> bytes:
        """
        Generate PDF as bytes (for preview or in-memory use).

        Args:
            album: The album data model
            base_url: Base URL for resolving relative image paths

        Returns:
            PDF content as bytes
        """
        from weasyprint import HTML
        import re

        renderer = HTMLRenderer(album, self.font_manager)
        html_content = renderer.render()

        # Replace image paths with absolute URLs if base_url provided
        if base_url:
            html_content = re.sub(
                r'src="([^"/][^"]*\.(?:png|jpg|jpeg|gif|bmp|tiff|tif|webp))"',
                rf'src="{base_url}/images/\1"',
                html_content
            )

        return HTML(string=html_content, base_url=base_url).write_pdf()

    def get_html_preview(self, album: Album) -> str:
        """
        Get HTML representation for live preview.

        Args:
            album: The album data model

        Returns:
            HTML string
        """
        renderer = HTMLRenderer(album, self.font_manager)
        return renderer.render()
