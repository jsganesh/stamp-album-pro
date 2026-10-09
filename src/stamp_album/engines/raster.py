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
    polygon_points,
)
from stamp_album.engines import caption_layout, text_layout
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


# Font files tried (in order) for the built-in PDF base-14 families. Pillow's
# truetype() searches the OS font directories, so bare file names work.
_FONT_FILE_CANDIDATES = {
    "H": {
        "N": ["Helvetica.ttc", "Arial.ttf", "arial.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf"],
        "B": ["Arial Bold.ttf", "arialbd.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"],
        "I": ["Arial Italic.ttf", "ariali.ttf", "LiberationSans-Italic.ttf", "DejaVuSans-Oblique.ttf"],
        "S": ["Arial Bold Italic.ttf", "arialbi.ttf", "LiberationSans-BoldItalic.ttf", "DejaVuSans-BoldOblique.ttf"],
    },
    "T": {
        "N": ["Times New Roman.ttf", "times.ttf", "LiberationSerif-Regular.ttf", "DejaVuSerif.ttf"],
        "B": ["Times New Roman Bold.ttf", "timesbd.ttf", "LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"],
        "I": ["Times New Roman Italic.ttf", "timesi.ttf", "LiberationSerif-Italic.ttf", "DejaVuSerif.ttf"],
        "S": ["Times New Roman Bold Italic.ttf", "timesbi.ttf", "LiberationSerif-BoldItalic.ttf", "DejaVuSerif-Bold.ttf"],
    },
    "C": {
        "N": ["Courier New.ttf", "cour.ttf", "LiberationMono-Regular.ttf", "DejaVuSansMono.ttf"],
        "B": ["Courier New Bold.ttf", "courbd.ttf", "LiberationMono-Bold.ttf", "DejaVuSansMono-Bold.ttf"],
        "I": ["Courier New Italic.ttf", "couri.ttf", "LiberationMono-Italic.ttf", "DejaVuSansMono.ttf"],
        "S": ["Courier New Bold Italic.ttf", "courbi.ttf", "LiberationMono-BoldItalic.ttf", "DejaVuSansMono-Bold.ttf"],
    },
}


def _default_font(size: float):
    """Last-resort font that still honours *size* (load_default ignores it on old Pillow)."""
    for name in ("DejaVuSans.ttf", "Arial.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _resolve_pillow_font(font_id: str, size: float) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Resolve font ID to a Pillow ImageFont of the requested pixel size."""
    if font_id in _BUILTIN_FONT_MAP_NAMES:
        family, style = font_id[0], font_id[1]
        for name in _FONT_FILE_CANDIDATES.get(family, {}).get(style, []):
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        return _default_font(size)
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
    return _default_font(size)


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
    elif polygon_points(shape.name, x, y, w, h):
        draw.polygon(polygon_points(shape.name, x, y, w, h), fill=fill_rgb, outline=border_rgb)
    else:  # RECTANGLE
        draw.rectangle([x, y, x + w, y + h], fill=fill_rgb, outline=border_rgb, width=1)


def _draw_stamp(draw: ImageDraw.ImageDraw, stamp: Stamp, album: Album, px_per_mm: float):
    """Draw a single stamp on Pillow (stamp geometry already in pixels).

    Captions are placed by caption_layout, like every other view.
    """
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
                # Fit inside the box keeping the aspect ratio, centred (like the PDF).
                fit = min(w / img.width, h / img.height)
                nw, nh = max(1, int(img.width * fit)), max(1, int(img.height * fit))
                img = img.resize((nw, nh), Image.LANCZOS)
                ox, oy = int(x + (w - nw) / 2), int(y + (h - nh) / 2)
                draw._image.paste(img, (ox, oy), img)
            except Exception:
                pass

    _draw_captions(draw, stamp, px_per_mm)


def _draw_captions(draw: ImageDraw.ImageDraw, stamp: Stamp, px_per_mm: float):
    """Heading above the box; description, details and catalogue below (see caption_layout).

    The stamp geometry is in pixels here; the layout works in mm.
    """
    pt_px = px_per_mm * 25.4 / 72.0
    fonts: dict = {}

    def font(font_id: str, size: float):
        key = (font_id, size)
        if key not in fonts:
            fonts[key] = _resolve_pillow_font(font_id, size * pt_px)
        return fonts[key]

    def measure(text: str, font_id: str, size: float) -> float:
        return draw.textlength(text, font=font(font_id, size)) / px_per_mm

    s = px_per_mm
    rgb = tuple(int(round(v * 255)) for v in caption_layout.COLOR_RGB)
    for line in caption_layout.layout(stamp, stamp.abs_x / s, stamp.abs_y / s,
                                      stamp.width / s, stamp.height / s, measure):
        draw.text((line.x * s, line.baseline * s), line.text, fill=rgb,
                  font=font(line.font_id, line.size_pt), anchor="ls")


def _draw_text_element(draw: ImageDraw.ImageDraw, stamp: Stamp, px_per_mm: float):
    """Draw a free-form text element (stamp geometry already in pixels).

    Font sizes are points, so convert to pixels at this image's resolution.
    """
    if not stamp.description:
        return
    size_px = (stamp.font_size or 12) * px_per_mm * 25.4 / 72.0
    font = _resolve_pillow_font(stamp.font_id or "HN", size_px)
    pad = text_layout.PAD_MM * px_per_mm

    def measure(s: str) -> float:
        return draw.textlength(s, font=font)

    lines = text_layout.wrap_lines(stamp.description, max(1.0, stamp.width - 2 * pad), measure)
    lh = size_px * text_layout.LINE_HEIGHT
    top = stamp.abs_y + pad + size_px * (text_layout.LINE_HEIGHT - 1) / 2
    # A marked heading takes the theme colour
    colour = _color_to_rgb(stamp.text_color) if stamp.text_color else (51, 51, 51)
    for i, line in enumerate(lines):
        if line:
            lx = text_layout.line_x(stamp.abs_x, stamp.width, measure(line), stamp.text_align, pad)
            draw.text((lx, top + i * lh), line, fill=colour, font=font)


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
                    _draw_stamp(draw, stamp, album, scale)
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
                        _draw_text_element(draw, stamp, scale)
                    else:
                        _draw_stamp(draw, stamp, album, scale)
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
