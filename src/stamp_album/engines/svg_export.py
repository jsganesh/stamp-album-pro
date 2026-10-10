"""
SVG document writer — renders Album model to standalone SVG.

Uses borders.py for shared geometry data.
Uses mm units natively (SVG supports mm without px conversion).
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

from stamp_album.core.models import Album, Color, Stamp
from stamp_album.engines import caption_layout, frames, page_border
from stamp_album.engines.layout import layout_rows


def _color_hex(color: Optional[Color], fallback: str = "#333") -> str:
    if color is None:
        return fallback
    return f"#{int(color.r * 255):02x}{int(color.g * 255):02x}{int(color.b * 255):02x}"


def _resolve_image_path(image_path: Optional[str]) -> Optional[str]:
    if not image_path:
        return None
    fname = image_path.split("/")[-1].split("\\")[-1]
    return fname


def _build_shape_svg(stamp: Stamp, x: float, y: float, w: float, h: float,
                     border_hex: str, fill_hex: str) -> str:
    """The stamp's fill and its frame, drawn outside it (mm units; see frames.py)."""
    return frames.svg_fragment(stamp, x, y, w, h, border_hex, fill_hex)


def _draw_text_element_svg(stamp: Stamp) -> str:
    """SVG for a free-form text element (user units are mm, font size is pt)."""
    from reportlab.pdfbase import pdfmetrics
    from stamp_album.engines import text_layout

    text = stamp.description or ""
    if not text:
        return ""
    size_mm = (stamp.font_size or 12) / text_layout.PT_PER_MM
    pad = text_layout.PAD_MM

    def measure(s: str) -> float:  # Helvetica metrics approximate Arial
        return pdfmetrics.stringWidth(s, "Helvetica", size_mm)

    lines = text_layout.wrap_lines(text, max(0.1, stamp.width - 2 * pad), measure)
    lh = size_mm * text_layout.LINE_HEIGHT
    base = stamp.abs_y + pad + size_mm * text_layout.FIRST_BASELINE
    align = text_layout.normalize_align(stamp.text_align)
    anchor = {"left": "start", "center": "middle", "right": "end"}.get(align, "start")
    x = {"start": stamp.abs_x + pad, "middle": stamp.abs_x + stamp.width / 2,
         "end": stamp.abs_x + stamp.width - pad}[anchor]
    tc = stamp.text_color  # a marked heading takes the theme colour
    rgb = (round(tc.r * 255), round(tc.g * 255), round(tc.b * 255)) if tc else None
    fill = ("#%02X%02X%02X" % rgb) if rgb else "#333"
    parts = []
    for i, line in enumerate(lines):
        if line:
            parts.append(
                f'<text x="{x:.2f}" y="{base + i * lh:.2f}" font-size="{size_mm:.2f}" '
                f'text-anchor="{anchor}" fill="{fill}" font-family="Arial,Helvetica,sans-serif">'
                f'{_xml_escape(line)}</text>'
            )
    return "\n".join(parts)


_SVG_FAMILY = {"H": "Arial,Helvetica,sans-serif", "T": "'Times New Roman',Times,serif",
               "C": "'Courier New',Courier,monospace"}
def _captions_svg(stamp: Stamp, x: float, y: float, w: float, h: float) -> str:
    """Heading above the box; description, details and catalogue below (see caption_layout)."""
    out = []
    for line in caption_layout.layout(stamp, x, y, w, h, caption_layout.metrics_measure):
        style = (' font-weight="bold"' if line.bold else "")
        style += ' font-style="italic"' if line.italic else ""
        size = line.size_pt * caption_layout.MM_PER_PT
        out.append(
            f'<text class="caption caption-{line.kind}" x="{x + w / 2:.2f}" '
            f'y="{line.baseline:.2f}" font-size="{size:.2f}" text-anchor="middle"{style} '
            f'fill="{caption_layout.COLOR_HEX}" '
            f'font-family="{_SVG_FAMILY[line.font_id[0]]}">'
            f'{_xml_escape(line.text)}</text>'
        )
    return "\n".join(out)



def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── SVGExporter ──

class SVGExporter:
    """Generate standalone SVG documents from an Album model."""

    def generate(self, album: Album, output_path: str) -> None:
        """Generate an SVG file from an Album model."""
        svg = self.generate_to_string(album)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)

    def generate_to_bytes(self, album: Album) -> bytes:
        """Generate SVG and return as bytes."""
        return self.generate_to_string(album).encode("utf-8")

    def generate_to_string(self, album: Album) -> str:
        """Generate SVG and return as string."""
        ps = album.page_setup
        w_mm = ps.width
        h_mm = ps.height
        color_border_hex = _color_hex(album.color_album_border, "#333")
        gap = 10  # mm gap between pages

        if not album.pages:
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_mm}mm" height="{h_mm}mm"'
                f' viewBox="0 0 {w_mm} {h_mm}"></svg>'
            )

        total_h = h_mm * len(album.pages) + gap * (len(album.pages) - 1)

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_mm}mm" height="{total_h}mm"'
            f' viewBox="0 0 {w_mm} {total_h}">',
            '<defs>',
            '<style>text{font-family:Arial,Helvetica,sans-serif}</style>',
            '</defs>',
        ]

        row_layout = layout_rows(album)
        y_offset = 0
        for pi, page_data in enumerate(album.pages):
            parts.append(f'<g transform="translate(0,{y_offset})">')

            # Page background
            parts.append(
                f'<rect x="0" y="0" width="{w_mm}" height="{h_mm}" '
                f'fill="#fff" stroke="#ccc" stroke-width="0.1"/>'
            )

            # Page border: the editor's styles share one drawing (see page_border.py)
            border = page_border.page_primitives(album)
            if border:
                lines = page_border.svg_elements(border, color_border_hex)
                parts.append(f'<g class="page-border">{lines}</g>')
            elif ps.has_border:
                bl = ps.margin_left
                bt = ps.margin_top
                bw = w_mm - ps.margin_left - ps.margin_right
                bh = h_mm - ps.margin_top - ps.margin_bottom

                if ps.border_outer > 0:
                    parts.append(
                        f'<rect x="{bl}" y="{bt}" width="{bw}" height="{bh}" '
                        f'fill="none" stroke="{color_border_hex}" stroke-width="{ps.border_outer}"/>'
                    )
                if ps.border_inner1 > 0:
                    off = ps.border_outer + ps.border_spacing
                    parts.append(
                        f'<rect x="{bl + off}" y="{bt + off}" width="{bw - off * 2}" height="{bh - off * 2}" '
                        f'fill="none" stroke="{color_border_hex}" stroke-width="{ps.border_inner1}"/>'
                    )


            # Row stamps (position from shared layout)
            for rx, ry, stamp in row_layout[pi]:
                x, y, w, h = rx, ry, stamp.width, stamp.height
                border_hex = _color_hex(
                    getattr(stamp, "border_color", None) or
                    getattr(album, "color_stamp_border", None),
                    "#999"
                )
                fill_hex = _color_hex(
                    getattr(stamp, "fill_color", None) or
                    getattr(album, "color_stamp_background", None),
                    "#fff"
                )
                parts.append(_build_shape_svg(stamp, x, y, w, h, border_hex, fill_hex))

                if stamp.image_path:
                    fname = _resolve_image_path(stamp.image_path)
                    if fname:
                        parts.append(
                            f'<image x="{x}" y="{y}" width="{w}" height="{h}" '
                            f'href="{fname}" preserveAspectRatio="xMidYMid meet"/>'
                        )

                parts.append(_captions_svg(stamp, x, y, w, h))

            # Absolute stamps (canvas drag-and-drop)
            for stamp in page_data.absolute_stamps:
                x, y, w, h = stamp.abs_x, stamp.abs_y, stamp.width, stamp.height

                if stamp.is_text_element:
                    parts.append(_draw_text_element_svg(stamp))
                else:
                    border_hex = _color_hex(
                        getattr(stamp, "border_color", None) or
                        getattr(album, "color_stamp_border", None),
                        "#999"
                    )
                    fill_hex = _color_hex(
                        getattr(stamp, "fill_color", None) or
                        getattr(album, "color_stamp_background", None),
                        "#fff"
                    )
                    parts.append(_build_shape_svg(stamp, x, y, w, h, border_hex, fill_hex))

                    if stamp.image_path:
                        fname = _resolve_image_path(stamp.image_path)
                        if fname:
                            parts.append(
                                f'<image x="{x}" y="{y}" width="{w}" height="{h}" '
                                f'href="{fname}" preserveAspectRatio="xMidYMid meet"/>'
                            )

                    parts.append(_captions_svg(stamp, x, y, w, h))

            parts.append('</g>')  # close page group
            y_offset += h_mm + gap

        parts.append("</svg>")
        return "\n".join(parts)
