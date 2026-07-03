"""
Pillow-based PNG generation engine.

Direct rendering from Album model — no PDF intermediate.
Top-left Y-down coordinate system (matches canvas/HTML/SVG).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from stamp_album.core.models import Album, Color, Stamp, StampShape
from stamp_album.engines.borders import (
    EDGE_STYLES,
    ORNAMENTAL_STYLES,
    get_ornament_segments,
    edge_pattern_segments,
    regular_polygon_vertices,
)
from stamp_album.engines.layout import layout_rows


# ── Font resolution ──

_BUILTIN_FONT_MAP_NAMES = {
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


def _resolve_pillow_font(font_id: str, size: float) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Resolve font ID to a Pillow ImageFont."""
    if font_id in _BUILTIN_FONT_MAP_NAMES:
        name = _BUILTIN_FONT_MAP_NAMES[font_id]
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    for d in _get_system_font_dirs():
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if f.suffix.lower() in (".ttf", ".ttc", ".otf"):
                stem = f.stem.lower().replace(" ", "")
                fid = font_id.lower()
                if fid in stem or stem in fid:
                    try:
                        return ImageFont.truetype(str(f), size)
                    except Exception:
                        continue
    return ImageFont.load_default()


def _resolve_image_path(image_path: Optional[str]) -> Optional[Path]:
    if not image_path:
        return None
    fname = image_path.split("/")[-1].split("\\")[-1]
    p = Path.home() / "StampAlbum" / "images" / fname
    return p if p.is_file() else None


def _color_to_rgb(color: Optional[Color]) -> tuple[int, int, int]:
    if color is None:
        return (0, 0, 0)
    return (max(0, min(255, int(color.r * 255))),
            max(0, min(255, int(color.g * 255))),
            max(0, min(255, int(color.b * 255))))


# ── Drawing ──

def _draw_shape(draw: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float,
                shape: StampShape, border_rgb: tuple, fill_rgb: tuple):
    """Draw a stamp shape on a Pillow ImageDraw (top-left origin)."""
    if shape == StampShape.OVAL:
        draw.ellipse([x, y, x + w, y + h], fill=fill_rgb, outline=border_rgb, width=1)
    elif shape == StampShape.DIAMOND:
        pts = [(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)]
        draw.polygon(pts, fill=fill_rgb, outline=border_rgb)
    elif shape == StampShape.TRIANGLE:
        pts = [(x + w / 2, y), (x + w, y + h), (x, y + h)]
        draw.polygon(pts, fill=fill_rgb, outline=border_rgb)
    elif shape in (StampShape.HEXAGON, StampShape.OCTAGON, StampShape.PENTAGON):
        n_map = {StampShape.HEXAGON: 6, StampShape.OCTAGON: 8, StampShape.PENTAGON: 5}
        verts = regular_polygon_vertices(x + w / 2, y + h / 2, w / 2, h / 2, n_map[shape])
        draw.polygon(verts, fill=fill_rgb, outline=border_rgb)
    else:  # RECTANGLE
        draw.rectangle([x, y, x + w, y + h], fill=fill_rgb, outline=border_rgb, width=1)


def _draw_multiline_text(draw: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float,
                         text: str, font, font_size: float, center: bool = False):
    """Draw text inside rect, splitting on newlines (top-left origin)."""
    if not text:
        return
    lines = text.split("\n")
    line_height = font_size * 1.3
    total_height = len(lines) * line_height
    start_y = y + max(2, (h - total_height) / 2)
    for i, line in enumerate(lines):
        _, _, tw, _ = draw.textbbox((0, 0), line, font=font)
        line_x = x + max(2, (w - tw) / 2) if center and line.strip() else x + 2
        draw.text((line_x, start_y + i * line_height), line, fill=(51, 51, 51), font=font)


def _draw_stamp(draw: ImageDraw.ImageDraw, stamp: Stamp, album: Album, font_size_pt: float):
    """Draw a single stamp on Pillow."""
    scale = font_size_pt / 12.0  # approximate, caller sets this
    x = stamp.abs_x
    y = stamp.abs_y
    w = stamp.width
    h = stamp.height

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

    _draw_shape(draw, x, y, w, h, stamp.shape, border_rgb, fill_rgb)

    if stamp.image_path:
        img_fp = _resolve_image_path(stamp.image_path)
        if img_fp:
            try:
                img = Image.open(img_fp).convert("RGBA")
                img = img.resize((int(w), int(h)), Image.LANCZOS)
                if img.mode == "RGBA":
                    draw._image.paste(img, (int(x), int(y)), img)
                else:
                    draw._image.paste(img, (int(x), int(y)))
            except Exception:
                pass

    if stamp.description and not stamp.image_path:
        font = _resolve_pillow_font(stamp.font_id or "HN", (stamp.font_size or 12) * 0.9)
        _draw_multiline_text(draw, x, y, w, h, stamp.description, font,
                             (stamp.font_size or 12) * 0.9, center=True)

    # Philatelic data: heading above stamp
    if stamp.heading and stamp.heading.text:
        hdg_font = _resolve_pillow_font(stamp.heading.font_id or "HN", stamp.heading.size or 9)
        hdg_size = stamp.heading.size or 9
        hdg_y = y + h + int(hdg_size * 0.4)
        _, _, tw, _ = draw.textbbox((0, 0), stamp.heading.text, font=hdg_font)
        draw.text((x + (w - tw) / 2, hdg_y), stamp.heading.text, fill=(51, 51, 51), font=hdg_font)

    # Catalog references below stamp
    if stamp.catalog_refs:
        cat_font = _resolve_pillow_font("HN", 8)
        cat_text = " · ".join(stamp.catalog_refs)
        cat_y = y + h - h + int(-3.5 * 2.83)  # ~3.5mm below stamp bottom
        # Calculate from bottom of stamp
        cat_y = y + h + 4
        _, _, tw, _ = draw.textbbox((0, 0), cat_text, font=cat_font)
        draw.text((x + (w - tw) / 2, cat_y), cat_text, fill=(102, 102, 102), font=cat_font)

    # Footer (denomination + condition + perforation)
    if stamp.footer_text:
        ft_font = _resolve_pillow_font("HN", 8)
        ft_y = y + h + 2
        _, _, tw, _ = draw.textbbox((0, 0), stamp.footer_text, font=ft_font)
        draw.text((x + (w - tw) / 2, ft_y), stamp.footer_text, fill=(77, 77, 77), font=ft_font)


def _draw_text_element(draw: ImageDraw.ImageDraw, stamp: Stamp):
    """Draw a free-form text element."""
    if not stamp.description:
        return
    font = _resolve_pillow_font(stamp.font_id or "HN", stamp.font_size or 12)
    _draw_multiline_text(draw, stamp.abs_x, stamp.abs_y, stamp.width, stamp.height,
                         stamp.description, font, stamp.font_size or 12)


def _draw_page_border(draw: ImageDraw.ImageDraw, album: Album, page_w_mm: float, page_h_mm: float, scale: float):
    """Draw decorative page border."""
    ps = album.page_setup
    if not ps.has_border:
        return

    color_rgb = _color_to_rgb(album.color_album_border) if album.color_album_border else (51, 51, 51)

    bl = ps.margin_left * scale
    bt = ps.margin_top * scale
    bw = (ps.width - ps.margin_left - ps.margin_right) * scale
    bh = (ps.height - ps.margin_top - ps.margin_bottom) * scale

    if ps.border_outer > 0:
        ow = ps.border_outer * scale
        draw.rectangle([bl, bt, bl + bw, bt + bh], outline=color_rgb, width=max(1, int(ow)))

    if ps.border_inner1 > 0:
        off = (ps.border_outer + ps.border_spacing) * scale
        iw = ps.border_inner1 * scale
        draw.rectangle([bl + off, bt + off, bl + bw - off, bt + bh - off],
                       outline=color_rgb, width=max(1, int(iw)))

    if ps.border_inner2 > 0:
        off = (ps.border_outer + ps.border_spacing + ps.border_inner1 + ps.border_spacing) * scale
        draw.rectangle([bl + off, bt + off, bl + bw - off, bt + bh - off],
                       outline=color_rgb, width=max(1, int(ps.border_inner2 * scale)))

    if ps.border_style in ORNAMENTAL_STYLES:
        _draw_corner_ornaments(draw, ps.border_style, color_rgb, bl, bt, bw, bh)
    elif ps.border_style in EDGE_STYLES:
        _draw_edge_patterns(draw, ps.border_style, color_rgb, bl, bt, bw, bh)


def _draw_corner_ornaments(draw, style, color_rgb, bl, bt, bw, bh):
    """Draw corner ornaments on Pillow (top-left origin)."""
    corners = [
        (bl, bt, False, False),          # TL
        (bl + bw, bt, True, False),      # TR: flip x
        (bl + bw, bt + bh, True, True),  # BR: flip x,y
        (bl, bt + bh, False, True),      # BL: flip y
    ]
    for cx, cy, fx, fy in corners:
        segments = get_ornament_segments(style)
        for seg in segments:
            cmd = seg[0]
            if cmd == "L":
                x1, y1, x2, y2 = seg[1:5]
                sx1 = cx + (-x1 if fx else x1)
                sy1 = cy + (-y1 if fy else y1)
                sx2 = cx + (-x2 if fx else x2)
                sy2 = cy + (-y2 if fy else y2)
                draw.line([sx1, sy1, sx2, sy2], fill=color_rgb, width=1)
            elif cmd == "Q":
                x1, y1, cx0, cy0, x2, y2 = seg[1:7]
                sx1 = cx + (-x1 if fx else x1)
                sy1 = cy + (-y1 if fy else y1)
                scx = cx + (-cx0 if fx else cx0)
                scy = cy + (-cy0 if fy else cy0)
                sx2 = cx + (-x2 if fx else x2)
                sy2 = cy + (-y2 if fy else y2)
                # Approximate quadratic bezier with line segments
                pts = []
                for t_int in range(21):
                    t = t_int / 20.0
                    px = (1 - t) ** 2 * sx1 + 2 * (1 - t) * t * scx + t ** 2 * sx2
                    py = (1 - t) ** 2 * sy1 + 2 * (1 - t) * t * scy + t ** 2 * sy2
                    pts.append((px, py))
                draw.line(pts, fill=color_rgb, width=1)
            elif cmd == "C":
                x1, y1, cp1x, cp1y, cp2x, cp2y, x2, y2 = seg[1:9]
                sx1 = cx + (-x1 if fx else x1)
                sy1 = cy + (-y1 if fy else y1)
                scp1x = cx + (-cp1x if fx else cp1x)
                scp1y = cy + (-cp1y if fy else cp1y)
                scp2x = cx + (-cp2x if fx else cp2x)
                scp2y = cy + (-cp2y if fy else cp2y)
                sx2 = cx + (-x2 if fx else x2)
                sy2 = cy + (-y2 if fy else y2)
                pts = []
                for t_int in range(21):
                    t = t_int / 20.0
                    px = (1 - t) ** 3 * sx1 + 3 * (1 - t) ** 2 * t * scp1x + 3 * (1 - t) * t ** 2 * scp2x + t ** 3 * sx2
                    py = (1 - t) ** 3 * sy1 + 3 * (1 - t) ** 2 * t * scp1y + 3 * (1 - t) * t ** 2 * scp2y + t ** 3 * sy2
                    pts.append((px, py))
                draw.line(pts, fill=color_rgb, width=1)
            elif cmd == "circle":
                cx0, cy0, r, fill = seg[1], seg[2], seg[3], seg[4]
                scx = cx + (-cx0 if fx else cx0)
                scy = cy + (-cy0 if fy else cy0)
                if fill:
                    draw.ellipse([scx - r, scy - r, scx + r, scy + r], fill=color_rgb, outline=color_rgb)
                else:
                    draw.ellipse([scx - r, scy - r, scx + r, scy + r], outline=color_rgb, width=1)
            elif cmd == "ellipse":
                cx0, cy0, rx, ry, fill = seg[1], seg[2], seg[3], seg[4], seg[5]
                scx = cx + (-cx0 if fx else cx0)
                scy = cy + (-cy0 if fy else cy0)
                if fill:
                    draw.ellipse([scx - rx, scy - ry, scx + rx, scy + ry], fill=color_rgb, outline=color_rgb)
                else:
                    draw.ellipse([scx - rx, scy - ry, scx + rx, scy + ry], outline=color_rgb, width=1)
            elif cmd == "rect":
                rx, ry, rw, rh, fill = seg[1], seg[2], seg[3], seg[4], seg[5]
                sx = cx + (-rx if fx else rx)
                sy = cy + (-ry if fy else ry)
                sw = -rw if fx else rw
                sh = -rh if fy else rh
                rr = [min(sx, sx + sw), min(sy, sy + sh), max(sx, sx + sw), max(sy, sy + sh)]
                if fill:
                    draw.rectangle(rr, fill=color_rgb, outline=color_rgb)
                else:
                    draw.rectangle(rr, outline=color_rgb, width=1)


def _draw_edge_patterns(draw, style, color_rgb, bl, bt, bw, bh):
    """Draw edge patterns (greek_key, rope) on Pillow (top-left origin)."""
    # Top
    for seg in edge_pattern_segments(style, "top", bw):
        if seg[0] == "L":
            draw.line([bl + seg[1], bt + seg[2], bl + seg[3], bt + seg[4]], fill=color_rgb, width=1)
        elif seg[0] == "circle":
            draw.ellipse([bl + seg[1] - seg[3], bt + seg[2] - seg[3],
                          bl + seg[1] + seg[3], bt + seg[2] + seg[3]],
                         outline=color_rgb, width=1)
    # Bottom (mirrored)
    for seg in edge_pattern_segments(style, "bottom", bw):
        if seg[0] == "L":
            draw.line([bl + seg[1], bt + bh - seg[2], bl + seg[3], bt + bh - seg[4]],
                      fill=color_rgb, width=1)
        elif seg[0] == "circle":
            draw.ellipse([bl + seg[1] - seg[3], bt + bh - seg[2] - seg[3],
                          bl + seg[1] + seg[3], bt + bh - seg[2] + seg[3]],
                         outline=color_rgb, width=1)
    # Left
    for seg in edge_pattern_segments(style, "left", bh):
        if seg[0] == "L":
            draw.line([bl + seg[2], bt + seg[1], bl + seg[4], bt + seg[3]], fill=color_rgb, width=1)
        elif seg[0] == "circle":
            draw.ellipse([bl + seg[2] - seg[3], bt + seg[1] - seg[3],
                          bl + seg[2] + seg[3], bt + seg[1] + seg[3]],
                         outline=color_rgb, width=1)
    # Right (mirrored)
    for seg in edge_pattern_segments(style, "right", bh):
        if seg[0] == "L":
            draw.line([bl + bw - seg[2], bt + seg[1], bl + bw - seg[4], bt + seg[3]],
                      fill=color_rgb, width=1)
        elif seg[0] == "circle":
            draw.ellipse([bl + bw - seg[2] - seg[3], bt + seg[1] - seg[3],
                          bl + bw - seg[2] + seg[3], bt + seg[1] + seg[3]],
                         outline=color_rgb, width=1)


# ── PNGGenerator ──

class PNGGenerator:
    """Generate PNG output using Pillow."""

    def generate(self, album: Album, output_path: str, dpi: float = 150) -> None:
        """Generate a PNG from an Album model. Multi-page albums stack vertically."""
        ps = album.page_setup
        scale = dpi / 25.4  # px per mm
        page_w_px = int(ps.width * scale)
        page_h_px = int(ps.height * scale)
        gap_px = int(10 * scale)  # 10 mm gap between pages

        if not album.pages:
            img = Image.new("RGB", (page_w_px, page_h_px), (255, 255, 255))
            img.save(output_path, dpi=(dpi, dpi))
            return

        total_h = page_h_px * len(album.pages) + gap_px * (len(album.pages) - 1)

        canvas_img = Image.new("RGB", (page_w_px, total_h), (255, 255, 255))
        y_offset = 0

        row_layout = layout_rows(album)
        for pi, page_data in enumerate(album.pages):
            pw_px = page_w_px
            ph_px = page_h_px

            # Draw onto a white page-sized tile, then paste into the canvas
            page_img = Image.new("RGB", (pw_px, ph_px), (255, 255, 255))
            draw = ImageDraw.Draw(page_img)

            _draw_page_border(draw, album, ps.width, ps.height, scale)

            # Row stamps (same temp-set trick as absolute stamps)
            for rx, ry, stamp in row_layout[pi]:
                orig_ax, orig_ay, orig_w, orig_h = stamp.abs_x, stamp.abs_y, stamp.width, stamp.height
                stamp.abs_x = rx * scale
                stamp.abs_y = ry * scale
                stamp.width = stamp.width * scale
                stamp.height = stamp.height * scale
                try:
                    _draw_stamp(draw, stamp, album, stamp.font_size or 12)
                finally:
                    stamp.abs_x, stamp.abs_y, stamp.width, stamp.height = orig_ax, orig_ay, orig_w, orig_h

            # Absolute stamps
            for stamp in page_data.absolute_stamps:
                x = stamp.abs_x * scale
                y = stamp.abs_y * scale
                w = stamp.width * scale
                h = stamp.height * scale

                orig_x, orig_y, orig_w, orig_h = stamp.abs_x, stamp.abs_y, stamp.width, stamp.height
                stamp.abs_x, stamp.abs_y, stamp.width, stamp.height = x, y, w, h
                try:
                    if stamp.is_text_element:
                        font = _resolve_pillow_font(stamp.font_id or "HN", stamp.font_size or 12)
                        _draw_multiline_text(draw, x, y, w, h, stamp.description, font, stamp.font_size or 12)
                    else:
                        _draw_stamp(draw, stamp, album, stamp.font_size or 12)
                finally:
                    stamp.abs_x, stamp.abs_y, stamp.width, stamp.height = orig_x, orig_y, orig_w, orig_h

            canvas_img.paste(page_img, (0, y_offset))
            y_offset += ph_px + gap_px

        canvas_img.save(output_path, dpi=(dpi, dpi))

    def generate_to_bytes(self, album: Album, dpi: float = 150) -> bytes:
        """Generate a PNG and return as bytes."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.close()
            try:
                self.generate(album, tmp.name, dpi=dpi)
                with open(tmp.name, "rb") as f:
                    return f.read()
            finally:
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass
