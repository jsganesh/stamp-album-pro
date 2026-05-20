from __future__ import annotations

from typing import Optional

from stamp_album.core.models import (
    Album,
    RowStyle,
    Stamp,
    StampShape,
    TextAlignment,
)
from stamp_album.core.parser import AlbumParser


class AlbumSerializer:
    def __init__(self):
        self.parser = AlbumParser()

    def _format_color(self, color) -> str:
        if color is None:
            return ""
        return f"#{color.to_hex()}"

    def _format_text_alignment(self, alignment: TextAlignment) -> str:
        align_map = {
            TextAlignment.LEFT: "",
            TextAlignment.CENTER: "_CENTER",
            TextAlignment.RIGHT: "_RIGHT",
        }
        return align_map.get(alignment, "")

    def _format_row_style(self, style: RowStyle) -> str:
        style_map = {
            RowStyle.FIXED_SPACE: "FS",
            RowStyle.EQUAL_SPACE: "ES",
            RowStyle.JUSTIFIED_SPACE: "JS",
            RowStyle.ROTATED: "ROTATE",
        }
        return style_map.get(style, "FS")

    def _format_stamp_shape(self, stamp: Stamp) -> str:
        shape_map = {
            StampShape.RECTANGLE: "STAMP_ADD",
            StampShape.TRIANGLE: "STAMP_ADD_TRIANGLE",
            StampShape.DIAMOND: "STAMP_ADD_DIAMOND",
            StampShape.OVAL: "STAMP_ADD_OVAL",
            StampShape.HEXAGON: "STAMP_ADD_HEXAGON",
            StampShape.OCTAGON: "STAMP_ADD_OCTAGON",
            StampShape.PENTAGON: "STAMP_ADD_PENTAGON",
        }
        return shape_map.get(stamp.shape, "STAMP_ADD")

    def _escape_string(self, s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    def to_dsl(self, album: Album) -> str:
        lines = []

        if album.title:
            lines.append(f'ALBUM_TITLE("{self._escape_string(album.title)}")')
        if album.author:
            lines.append(f'ALBUM_AUTHOR("{self._escape_string(album.author)}")')

        ps = album.page_setup
        lines.append(f"ALBUM_PAGES_SIZE({ps.width} {ps.height})")
        lines.append(
            f"ALBUM_PAGES_MARGINS({ps.margin_left} {ps.margin_right} "
            f"{ps.margin_top} {ps.margin_bottom})"
        )

        if ps.has_border:
            lines.append(
                f"ALBUM_PAGES_BORDER({ps.border_outer} {ps.border_inner1} "
                f"{ps.border_inner2} {ps.border_spacing})"
            )

        for font in album.fonts:
            lines.append(
                f'ALBUM_DEFINE_FONT("{self._escape_string(font.font_id)}" '
                f'"{self._escape_string(font.font_name)}")'
            )

        for page in album.pages:
            lines.append("PAGE_START")

            if page.background_image:
                lines.append(
                    f'PAGE_BACKGROUND_IMG("{self._escape_string(page.background_image)}")'
                )

            for text in page.text_elements:
                align_suffix = self._format_text_alignment(text.alignment)
                content = self._escape_string(text.content)
                if text.vspace:
                    lines.append(
                        f'PAGE_TEXT{align_suffix}("{text.font_id}" {text.size} '
                        f'"{content}" {text.vspace})'
                    )
                else:
                    lines.append(
                        f'PAGE_TEXT{align_suffix}("{text.font_id}" {text.size} "{content}")'
                    )

            if page.vspace:
                lines.append(f"PAGE_VSPACE({page.vspace})")

            for row in page.rows:
                style_code = self._format_row_style(row.style)
                line = (
                    f'ROW_START_{style_code}("{row.font_id}" {row.size} '
                    f"{row.spacing} {row.width})"
                )
                lines.append(line)

                for stamp in row.stamps:
                    cmd = self._format_stamp_shape(stamp)
                    if stamp.image_path:
                        desc = self._escape_string(stamp.description)
                        img = self._escape_string(stamp.image_path)
                        lines.append(
                            f'STAMP_ADD_IMG({stamp.width} {stamp.height} '
                            f'"{img}" "{desc}")'
                        )
                    elif stamp.shape == StampShape.RECTANGLE:
                        if stamp.description:
                            desc = self._escape_string(stamp.description)
                            lines.append(
                                f'STAMP_ADD({stamp.width} {stamp.height} "{desc}")'
                            )
                        else:
                            lines.append(
                                f"STAMP_ADD_BLANK({stamp.width} {stamp.height})"
                            )
                    else:
                        desc = self._escape_string(stamp.description)
                        lines.append(
                            f'{cmd}({stamp.width} {stamp.height} '
                            f'"{desc}" "" "" "")'
                        )

                    if stamp.heading:
                        lines.append(
                            f'STAMP_HEADING("{stamp.heading.font_id}" '
                            f'{stamp.heading.size} '
                            f'"{self._escape_string(stamp.heading.text)}")'
                        )

            lines.append("")

        return "\n".join(lines)

    def update_stamp_position(
        self,
        dsl: str,
        page_idx: int,
        row_idx: int,
        stamp_idx: int,
        new_width: float,
        new_height: float,
        source_path: Optional[str] = None,
    ) -> str:
        album = self.parser.parse(dsl, source_path)
        if page_idx < len(album.pages):
            page = album.pages[page_idx]
            if row_idx < len(page.rows):
                row = page.rows[row_idx]
                if stamp_idx < len(row.stamps):
                    stamp = row.stamps[stamp_idx]
                    stamp.width = new_width
                    stamp.height = new_height
        return self.to_dsl(album)

