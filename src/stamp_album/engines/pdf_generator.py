"""
PDF generation engine using WeasyPrint.

Converts Album data models into HTML/CSS and renders to PDF.
This approach provides rich typography, CSS layouts, and modern
text rendering without manual coordinate calculations.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from weasyprint import HTML

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
    "CN": ("Courier", "monospace"),
    "CB": ("Courier", "monospace", "bold"),
    "CI": ("Courier", "monospace", "normal", "italic"),
    "CS": ("Courier", "monospace", "bold", "italic"),
    "TN": ("Times New Roman", "serif"),
    "TB": ("Times New Roman", "serif", "bold"),
    "TI": ("Times New Roman", "serif", "normal", "italic"),
    "TS": ("Times New Roman", "serif", "bold", "italic"),
    "HN": ("Helvetica", "Arial", "sans-serif"),
    "HB": ("Helvetica", "Arial", "sans-serif", "bold"),
    "HI": ("Helvetica", "Arial", "sans-serif", "normal", "italic"),
    "HS": ("Helvetica", "Arial", "sans-serif", "bold", "italic"),
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
        width_mm = ps.width
        height_mm = ps.height

        # Margins
        ml = ps.margin_left
        mr = ps.margin_right
        mt = ps.margin_top
        mb = ps.margin_bottom

        styles = f"""
        <style>
        @page {{
            size: {width_mm}mm {height_mm}mm;
            margin: {mt}mm {mr}mm {mb}mm {ml}mm;
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
            padding: {mt}mm {mr}mm {mb}mm {ml}mm;
        }}

        .page:last-child {{
            page-break-after: auto;
        }}

        .page-border {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
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
            flex-wrap: wrap;
            gap: {ps.hspace}mm;
            margin-bottom: {ps.vspace}mm;
            align-items: flex-start;
        }}

        .stamp-row.align-middle {{
            align-items: center;
        }}

        .stamp-row.align-bottom {{
            align-items: flex-end;
        }}

        .stamp {{
            position: relative;
            box-sizing: border-box;
            text-align: center;
        }}

        .stamp-box {{
            border: 0.5pt solid black;
            box-sizing: border-box;
            margin: 0 auto;
        }}

        .stamp-box.shape-oval {{
            border-radius: 50%;
        }}

        .stamp-image {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}

        .stamp-heading {{
            text-align: center;
            margin-top: 1mm;
            font-weight: bold;
        }}

        .stamp-footer {{
            text-align: center;
            margin-top: 0.5mm;
            line-height: 1.2;
        }}

        .stamp-catalog {{
            text-align: center;
            margin-top: 0.5mm;
            font-size: 0.8em;
            color: #666;
        }}

        .h-rule {{
            border: none;
            border-top: 0.5pt solid black;
            margin: 2mm 0;
        }}

        .header {{
            margin-bottom: 2mm;
            font-size: 0.9em;
        }}

        .footer {{
            margin-top: 2mm;
            font-size: 0.9em;
        }}

        .margin-text {{
            position: absolute;
            writing-mode: vertical-rl;
            font-size: 0.8em;
        }}

        .margin-text.left {{
            left: 2mm;
        }}

        .margin-text.right {{
            right: 2mm;
        }}

        .quadrille {{
            background-image: linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px);
            background-size: 5mm 5mm;
        }}

        .column-container {{
            column-count: 2;
            column-gap: 10mm;
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

        # Decorative border
        if ps.decorative_border_file:
            parts.append(self._render_decorative_border(ps.decorative_border_file))

        # Line border
        if ps.has_border:
            parts.append(self._render_line_border())

        # Header
        if ps.header_text:
            parts.append(self._render_header_footer(ps.header_text, "header"))

        # Title
        if ps.title:
            parts.append(self._render_formatted_text(ps.title, "page-title"))

        # Margin text
        for margin_item in ps.margin_texts:
            parts.append(self._render_margin_text(margin_item))

        # Page content
        content_class = "column-container" if page.column_mode == ColumnMode.TWO_COLUMN else ""
        if content_class:
            parts.append(f'<div class="{content_class}">')

        # Quadrille
        if page.quadrille:
            parts.append(self._render_quadrille(page.quadrille))

        # Text elements
        for text_elem in page.text_elements:
            parts.append(self._render_text_element(text_elem))

        # Paragraphs
        for paragraph in page.paragraphs:
            parts.append(self._render_paragraph(paragraph))

        # Horizontal rules
        for line, spacing, margin in page.h_rules:
            parts.append(
                f'<hr class="h-rule" style="border-top-width: {line}pt; '
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

        if content_class:
            parts.append("</div>")

        # Footer
        if ps.footer_text:
            parts.append(self._render_header_footer(ps.footer_text, "footer"))

        parts.append("</div>")
        return "\n".join(parts)

    def _render_line_border(self) -> str:
        """Render page line border."""
        ps = self.album.page_setup
        color = self._color_to_css(self.album.color_album_border)

        parts = ['<div class="page-border">']

        if ps.border_outer > 0:
            parts.append(
                f'<div style="position: absolute; top: 0; left: 0; '
                f'right: 0; bottom: 0; border: {ps.border_outer}pt solid {color};"></div>'
            )

        if ps.border_inner1 > 0:
            offset = ps.border_outer + ps.border_spacing
            parts.append(
                f'<div style="position: absolute; top: {offset}pt; left: {offset}pt; '
                f"right: {offset}pt; bottom: {offset}pt; "
                f'border: {ps.border_inner1}pt solid {color};"></div>'
            )

        if ps.border_inner2 > 0:
            offset = ps.border_outer + ps.border_inner1 + ps.border_spacing * 2
            parts.append(
                f'<div style="position: absolute; top: {offset}pt; left: {offset}pt; '
                f"right: {offset}pt; bottom: {offset}pt; "
                f'border: {ps.border_inner2}pt solid {color};"></div>'
            )

        parts.append("</div>")
        return "\n".join(parts)

    def _render_decorative_border(self, border_file: str) -> str:
        """Render decorative border (placeholder)."""
        return f"<!-- Decorative border: {border_file} -->"

    def _render_header_footer(self, text: FormattedText, css_class: str) -> str:
        """Render header or footer text."""
        content = text.content
        # Substitute tokens
        content = content.replace("$PAGE$", str(self._page_counter))
        content = content.replace("$DATE$", date.today().strftime("%Y-%m-%d"))
        content = content.replace("$PAGES$", str(len(self.album.pages)))

        font_css = self._font_to_css(text.font_id, text.size)
        color_css = self._color_to_css(text.color or self.album.color_header)

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

    def _render_text_element(self, text: FormattedText) -> str:
        """Render a formatted text element."""
        align_class = ""
        if text.alignment == TextAlignment.CENTER:
            align_class = "center"
        elif text.alignment == TextAlignment.RIGHT:
            align_class = "right"
        elif text.alignment == TextAlignment.JUSTIFY:
            align_class = "justify"

        font_css = self._font_to_css(text.font_id, text.size)
        color_css = self._color_to_css(text.color or self.album.color_page_text)

        vspace = f"margin-bottom: {text.vspace}mm;" if text.vspace > 0 else ""

        return (
            f'<div class="page-text {align_class}" '
            f'style="{font_css}; color: {color_css}; {vspace}">'
            f"{self._format_text(text.content)}</div>"
        )

    def _render_paragraph(self, paragraph) -> str:
        """Render a paragraph."""
        font_css = self._font_to_css(paragraph.font_id, paragraph.size)
        color_css = self._color_to_css(paragraph.color or self.album.color_page_text)

        lines = "<br>".join(self._format_text(line) for line in paragraph.lines)

        return f'<div class="page-text" style="{font_css}; color: {color_css};">' f"{lines}</div>"

    def _render_row(self, row: Row) -> str:
        """Render a row of stamps."""
        align_class = ""
        if row.alignment.name == "MIDDLE":
            align_class = "align-middle"
        elif row.alignment.name == "BOTTOM":
            align_class = "align-bottom"

        parts = [f'<div class="stamp-row {align_class}">']

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

        border_color = self._color_to_css(self.album.color_stamp_border)
        bg_color = self._color_to_css(self.album.color_stamp_background)

        parts = [
            f'<div class="stamp" style="width: {width}mm;">',
            f'<div class="stamp-box {shape_class}" '
            f'style="width: {width}mm; height: {height}mm; '
            f"border-color: {border_color}; "
            f'background-color: {bg_color};">',
        ]

        # Stamp image
        if stamp.image_path and not ps.stamp_image_settings.hidden:
            parts.append(
                f'<img class="stamp-image" src="{stamp.image_path}" ' f'alt="{stamp.description}">'
            )

        parts.append("</div>")

        # Stamp heading
        if stamp.heading:
            heading_color = self._color_to_css(self.album.color_stamp_heading)
            font_css = self._font_to_css(stamp.heading.font_id, stamp.heading.size)
            parts.append(
                f'<div class="stamp-heading" style="{font_css}; color: {heading_color};">'
                f"{self._format_text(stamp.heading.text)}</div>"
            )

        # Stamp description
        if stamp.description:
            text_color = self._color_to_css(self.album.color_stamp_text)
            font_css = self._font_to_css(row.font_id, row.size)
            parts.append(
                f'<div class="stamp-footer" style="{font_css}; color: {text_color};">'
                f"{self._format_text(stamp.description)}</div>"
            )

        # Catalog references
        catalog_parts = [c for c in stamp.catalog_refs if c]
        if catalog_parts:
            text_color = self._color_to_css(self.album.color_stamp_text)
            font_css = self._font_to_css(row.font_id, row.size * 0.8)
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
            f"background-image: linear-gradient({color} 1px, transparent 1px), "
            f'linear-gradient(90deg, {color} 1px, transparent 1px);">'
            f"</div>"
        )

    def _format_text(self, text: str) -> str:
        """Format text for HTML output, handling newlines and special chars."""
        # Escape HTML special characters
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")

        # Convert newlines to <br>
        text = text.replace("\n", "<br>")

        return text

    def _font_to_css(self, font_id: str, size: float) -> str:
        """Convert a font ID to CSS font properties."""
        if font_id in BASE14_FONT_MAP:
            mapping = BASE14_FONT_MAP[font_id]
            family = (
                ", ".join(f'"{f}"' for f in mapping[:-1]) if len(mapping) > 1 else f'"{mapping[0]}"'
            )
            style = ""

            if len(mapping) >= 3:
                if mapping[2] == "bold":
                    style = "font-weight: bold;"
                if len(mapping) >= 4 and mapping[3] == "italic":
                    style += "font-style: italic;"

            return f"font-family: {family}; font-size: {size}pt; {style}"

        # User-defined font - try to resolve via font manager
        if self.font_manager:
            font_info = self.font_manager.find_font(font_id)
            if font_info:
                return f'font-family: "{font_info.name}"; ' f"font-size: {size}pt;"

        # Fallback
        return f"font-family: Arial, sans-serif; font-size: {size}pt;"

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

    def generate(self, album: Album, output_path: str) -> None:
        """
        Generate a PDF from an Album model.

        Args:
            album: The album data model
            output_path: Path to write the PDF file
        """
        renderer = HTMLRenderer(album, self.font_manager)
        html_content = renderer.render()

        # Write PDF
        HTML(string=html_content).write_pdf(output_path)

    def generate_to_bytes(self, album: Album) -> bytes:
        """
        Generate PDF as bytes (for preview or in-memory use).

        Args:
            album: The album data model

        Returns:
            PDF content as bytes
        """
        renderer = HTMLRenderer(album, self.font_manager)
        html_content = renderer.render()

        return HTML(string=html_content).write_pdf()

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
