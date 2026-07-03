"""
SVG document writer — renders Album model to standalone SVG.

Uses borders.py for shared geometry data.
Uses mm units natively (SVG supports mm without px conversion).
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

from stamp_album.core.models import Album, Color, Stamp, StampShape
from stamp_album.engines.borders import (
    EDGE_STYLES,
    ORNAMENTAL_STYLES,
    SHAPE_POLYGON_VIEWBOX,
    corner_ornament_svg,
    edge_pattern_svg,
    regular_polygon_vertices,
)


def _color_hex(color: Optional[Color], fallback: str = "#333") -> str:
    if color is None:
        return fallback
    return f"#{int(color.r * 255):02x}{int(color.g * 255):02x}{int(color.b * 255):02x}"


def _resolve_image_path(image_path: Optional[str]) -> Optional[str]:
    if not image_path:
        return None
    fname = image_path.split("/")[-1].split("\\")[-1]
    return fname


def _build_shape_svg(x: float, y: float, w: float, h: float,
                     shape: StampShape, border_hex: str, fill_hex: str) -> str:
    """Build SVG element for a stamp shape (in mm units)."""
    if shape == StampShape.OVAL:
        cx, cy = x + w / 2, y + h / 2
        return (
            f'<ellipse cx="{cx}" cy="{cy}" rx="{w / 2}" ry="{h / 2}" '
            f'fill="{fill_hex}" stroke="{border_hex}" stroke-width="0.3"/>'
        )
    elif shape in (StampShape.TRIANGLE, StampShape.TRIANGLE_INV,
                   StampShape.DIAMOND, StampShape.HEXAGON,
                   StampShape.OCTAGON, StampShape.PENTAGON):
        shape_name = shape.name
        if shape_name in SHAPE_POLYGON_VIEWBOX:
            pts = SHAPE_POLYGON_VIEWBOX[shape_name]
            # SVG polygon with viewBox scaling
            return (
                f'<svg x="{x}mm" y="{y}mm" width="{w}mm" height="{h}mm" '
                f'viewBox="0 0 100 100" style="overflow:visible">'
                f'<polygon points="{pts}" fill="{fill_hex}" stroke="{border_hex}" stroke-width="0.3"/>'
                f'</svg>'
            )
    # Rectangle (default)
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'fill="{fill_hex}" stroke="{border_hex}" stroke-width="0.3"/>'
    )


def _draw_multiline_text_svg(x: float, y: float, w: float, h: float,
                              text: str, font_size: float, center: bool = False) -> str:
    """Build SVG <text> element for multiline text."""
    if not text:
        return ""
    lines = text.split("\n")
    line_height = font_size * 1.3
    total_height = len(lines) * line_height
    start_y = y + max(2, (h - total_height) / 2) + font_size
    parts = []
    for i, line in enumerate(lines):
        line_y = start_y + i * line_height
        anchor = "middle" if center and line.strip() else "start"
        x_pos = f'x="{x + w / 2}"' if anchor == "middle" else f'x="{x + 2}"'
        parts.append(
            f'<text {x_pos} y="{line_y}" font-size="{font_size}pt" '
            f'text-anchor="{anchor}" fill="#333" font-family="Arial,Helvetica,sans-serif">'
            f'{_xml_escape(line)}</text>'
        )
    return "\n".join(parts)


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

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_mm}mm" height="{h_mm}mm"'
            f' viewBox="0 0 {w_mm} {h_mm}">',
            '<defs>',
            '<style>text{font-family:Arial,Helvetica,sans-serif}</style>',
            '</defs>',
        ]

        for page_data in album.pages:
            # Page border
            if ps.has_border:
                bl = ps.margin_left
                bt = ps.margin_top
                bw = ps.width - ps.margin_left - ps.margin_right
                bh = ps.height - ps.margin_top - ps.margin_bottom

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

                # Ornaments / edge patterns
                if ps.border_style in ORNAMENTAL_STYLES:
                    orn = corner_ornament_svg(ps.border_style, color_border_hex)
                    parts.append(
                        f'<g transform="translate({bl},{bt})">{orn}</g>'
                        f'<g transform="translate({bl + bw},{bt}) scale(-1,1)">{orn}</g>'
                        f'<g transform="translate({bl + bw},{bt + bh}) scale(-1,-1)">{orn}</g>'
                        f'<g transform="translate({bl},{bt + bh}) scale(1,-1)">{orn}</g>'
                    )
                elif ps.border_style in EDGE_STYLES:
                    top_svg = edge_pattern_svg(ps.border_style, "top", bw, bh, color_border_hex)
                    bottom_svg = edge_pattern_svg(ps.border_style, "bottom", bw, bh, color_border_hex)
                    left_svg = edge_pattern_svg(ps.border_style, "left", bh, bw, color_border_hex)
                    right_svg = edge_pattern_svg(ps.border_style, "right", bh, bw, color_border_hex)
                    parts.append(
                        f'<g transform="translate({bl},{bt})">{top_svg}</g>'
                        f'<g transform="translate({bl},{bt + bh}) scale(1,-1)">{bottom_svg}</g>'
                        f'<g transform="translate({bl},{bt})">{left_svg}</g>'
                        f'<g transform="translate({bl + bw},{bt}) scale(-1,1)">{right_svg}</g>'
                    )

            # Stamps and text elements
            for stamp in page_data.absolute_stamps:
                x, y, w, h = stamp.abs_x, stamp.abs_y, stamp.width, stamp.height

                if stamp.is_text_element:
                    font_s = stamp.font_size or 12
                    parts.append(_draw_multiline_text_svg(
                        x, y, w, h, stamp.description or "", font_s, center=False
                    ))
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
                    parts.append(_build_shape_svg(x, y, w, h, stamp.shape, border_hex, fill_hex))

                    if stamp.image_path:
                        fname = _resolve_image_path(stamp.image_path)
                        if fname:
                            parts.append(
                                f'<image x="{x}" y="{y}" width="{w}" height="{h}" '
                                f'href="{fname}" preserveAspectRatio="xMidYMid meet"/>'
                            )

                    if stamp.description and not stamp.image_path:
                        font_s = (stamp.font_size or 12) * 0.9
                        parts.append(_draw_multiline_text_svg(
                            x, y, w, h, stamp.description, font_s, center=True
                        ))

        parts.append("</svg>")
        return "\n".join(parts)
