"""
Parser for the StampAlbum Pro DSL.

Uses a simple line-by-line parsing approach rather than a full Lark grammar.
This avoids grammar ambiguity issues while remaining clear and maintainable.
"""

from __future__ import annotations

import re
from typing import Optional

from stamp_album.core.models import (
    Album,
    Color,
    CropMarkSettings,
    FontDefinition,
    FormattedText,
    MarginTextItem,
    Page,
    Paragraph,
    Position,
    QuadrilleSettings,
    Row,
    RowAlignment,
    RowStyle,
    Stamp,
    StampHeading,
    StampShape,
    TextAlignment,
)


# ---------------------------------------------------------------------------
# Parse Error
# ---------------------------------------------------------------------------


class ParseError(Exception):
    """Raised when the DSL parser encounters invalid syntax."""

    def __init__(self, message: str, line_number: int | None = None, line_text: str | None = None):
        self.line_number = line_number
        self.line_text = line_text
        parts = [message]
        if line_number is not None:
            parts.append(f"at line {line_number}")
        if line_text is not None:
            parts.append(f": {line_text!r}")
        super().__init__(" ".join(parts))


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------


def tokenize(text: str) -> list[str]:
    """
    Split a line of DSL into tokens.
    Handles quoted strings, parentheses, and whitespace.
    """
    tokens = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text[i] == '"':
            # Quoted string
            j = i + 1
            while j < len(text):
                if text[j] == "\\" and j + 1 < len(text):
                    j += 2
                elif text[j] == '"':
                    j += 1
                    break
                else:
                    j += 1
            tokens.append(text[i:j])
            i = j
        elif text[i] in "()":
            tokens.append(text[i])
            i += 1
        else:
            # Regular token
            j = i
            while j < len(text) and not text[j].isspace() and text[j] not in '()"':
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def parse_params(token_list: list[str]) -> list[str]:
    """Extract parameters from between parentheses."""
    params = []
    in_parens = False
    for token in token_list:
        if token == "(":
            in_parens = True
        elif token == ")":
            in_parens = False
        elif in_parens:
            params.append(token)
    return params


def unquote(s: str) -> str:
    """Remove quotes and process escape sequences.

    Handles multiple adjacent quoted strings (from line continuation).
    """
    import re

    # Find all quoted strings and concatenate their contents
    parts = re.findall(r'"([^"]*(?:\\.[^"]*)*)"', s)
    if parts:
        result = "".join(parts)
    else:
        # Fallback: just strip outer quotes
        result = s.strip('"')

    result = result.replace("\\n", "\n")
    result = result.replace("\\\\", "\\")
    return result


def parse_color(val: str) -> Color:
    """Parse a color value."""
    if val.startswith("#"):
        return Color.from_hex(val)
    if val.lower().startswith("rgb"):
        match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", val)
        if match:
            return Color.from_rgb(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return Color.from_name(val)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class AlbumParser:
    """
    Parses StampAlbum Pro DSL source files into Album models.

    Uses a line-by-line parsing approach for clarity and to avoid
    grammar ambiguity issues.
    """

    def __init__(self):
        pass

    def parse(self, source_text: str, source_path: Optional[str] = None) -> Album:
        """Parse a DSL source string into an Album model."""
        album = Album(source_path=source_path)
        current_page: Optional[Page] = None
        current_row: Optional[Row] = None
        current_stamp: Optional[Stamp] = None
        # Paragraph ended
        paragraph: Optional[Paragraph] = None
        ifdef_stack: list[bool] = [True]
        # Pending row alignment (applied when next row is created)
        pending_row_alignment: Optional[RowAlignment] = None

        # Join continuation lines
        lines = source_text.split("\n")
        joined_lines = []
        current_line = ""
        for line in lines:
            stripped = line.rstrip()
            if stripped.endswith("\\"):
                current_line += stripped[:-1] + " "
            else:
                current_line += stripped
                joined_lines.append(current_line)
                current_line = ""
        if current_line:
            joined_lines.append(current_line)

        for _line_idx, line in enumerate(joined_lines):
            line_number = _line_idx + 1
            # Remove comments (but not # inside quoted strings or hex colors)
            in_string = False
            comment_pos = -1
            i = 0
            while i < len(line):
                ch = line[i]
                if ch == '"':
                    in_string = not in_string
                elif ch == "#" and not in_string:
                    # Check if it's a hex color (preceded by space/paren and followed by hex digits)
                    if i > 0 and line[i - 1] in " (," and i + 7 <= len(line):
                        potential_hex = line[i : i + 7]
                        if re.match(r"#[0-9a-fA-F]{6}", potential_hex):
                            i += 7
                            continue
                    comment_pos = i
                    break
                i += 1
            if comment_pos >= 0:
                line = line[:comment_pos]

            line = line.strip()
            if not line:
                continue

            tokens = tokenize(line)
            if not tokens:
                continue

            # Check ifdef stack - but always process conditional commands
            if not ifdef_stack[-1]:
                if tokens[0] not in (
                    "$DEFINE",
                    "$UNDEFINE",
                    "$IFDEF",
                    "$ELSEIF",
                    "$ELSE",
                    "$ENDIF",
                ):
                    continue

            params = parse_params(tokens)
            cmd = tokens[0]

            # -- Conditional commands --
            if cmd == "$DEFINE":
                album.defines.add(params[0])
                continue
            elif cmd == "$UNDEFINE":
                album.defines.discard(params[0])
                continue
            elif cmd == "$IFDEF":
                ifdef_stack.append(params[0] in album.defines)
                continue
            elif cmd == "$ELSEIF":
                if ifdef_stack and not ifdef_stack[-1]:
                    ifdef_stack[-1] = params[0] in album.defines
                continue
            elif cmd == "$ELSE":
                if ifdef_stack:
                    ifdef_stack[-1] = not ifdef_stack[-1]
                continue
            elif cmd == "$ENDIF":
                if ifdef_stack:
                    ifdef_stack.pop()
                continue

            # -- Document commands --
            if cmd == "ALBUM_TITLE":
                album.title = unquote(params[0])
            elif cmd == "ALBUM_AUTHOR":
                album.author = unquote(params[0])

            # -- Page setup commands --
            elif cmd == "ALBUM_PAGES_SIZE":
                album.page_setup.width = float(params[0])
                album.page_setup.height = float(params[1])
            elif cmd == "ALBUM_PAGES_MARGINS":
                ps = album.page_setup
                ps.margin_left = float(params[0])
                ps.margin_right = float(params[1])
                ps.margin_top = float(params[2])
                ps.margin_bottom = float(params[3])
                if ps.mirror_margins:
                    ps.even_margin_left = float(params[1])
                    ps.even_margin_right = float(params[0])
            elif cmd == "ALBUM_PAGES_MARGINSE":
                ps = album.page_setup
                ps.even_margin_left = float(params[0])
                ps.even_margin_right = float(params[1])
                ps.even_margin_top = float(params[2])
                ps.even_margin_bottom = float(params[3])
                ps.mirror_margins = True
            elif cmd == "ALBUM_PAGES_BORDER":
                ps = album.page_setup
                ps.has_border = True
                if len(params) == 4:
                    ps.border_outer = float(params[0])
                    ps.border_inner1 = float(params[1])
                    ps.border_inner2 = float(params[2])
                    ps.border_spacing = float(params[3])
                elif len(params) == 3:
                    ps.border_outer = float(params[0])
                    ps.border_inner1 = float(params[1])
                    ps.border_inner2 = float(params[2])
                    ps.border_spacing = float(params[2])
            elif cmd == "ALBUM_PAGES_DECORATIVE_BORDER":
                album.page_setup.decorative_border_file = unquote(params[0])
            elif cmd == "ALBUM_PAGES_SPACING":
                album.page_setup.hspace = float(params[0])
                album.page_setup.vspace = float(params[1])
            elif cmd == "ALBUM_PAGES_TITLE":
                vspace = float(params[3]) if len(params) > 3 else 0.0
                album.page_setup.title = FormattedText(
                    font_id=unquote(params[0]),
                    size=float(params[1]),
                    content=unquote(params[2]),
                    alignment=TextAlignment.CENTER,
                    color=album.color_title,
                    vspace=vspace,
                )
            elif cmd == "ALBUM_PAGES_FOOTER":
                album.page_setup.footer_text = FormattedText(
                    font_id=unquote(params[0]),
                    size=float(params[1]),
                    content=unquote(params[3]),
                    alignment=TextAlignment.LEFT,
                    color=album.color_footer,
                )
            elif cmd == "ALBUM_PAGES_HEADER":
                album.page_setup.header_text = FormattedText(
                    font_id=unquote(params[0]),
                    size=float(params[1]),
                    content=unquote(params[3]),
                    alignment=TextAlignment.LEFT,
                    color=album.color_header,
                )
            elif cmd in ("ALBUM_PAGES_FOOTER_NUMBER", "ALBUM_PAGES_HEADER_NUMBER"):
                before = unquote(params[4]) if len(params) > 4 else ""
                after = unquote(params[5]) if len(params) > 5 else ""
                ft = FormattedText(
                    font_id=unquote(params[0]),
                    size=float(params[1]),
                    content=f"{before}$PAGE${after}",
                    alignment=TextAlignment.LEFT,
                )
                if cmd == "ALBUM_PAGES_FOOTER_NUMBER":
                    album.page_setup.footer_page_num = ft
                else:
                    album.page_setup.header_page_num = ft
            elif cmd in ("ALBUM_PAGES_FOOTER_DATE", "ALBUM_PAGES_HEADER_DATE"):
                before = unquote(params[5]) if len(params) > 5 else ""
                after = unquote(params[6]) if len(params) > 6 else ""
                ft = FormattedText(
                    font_id=unquote(params[0]),
                    size=float(params[1]),
                    content=f"{before}$DATE${after}",
                    alignment=TextAlignment.LEFT,
                )
                if cmd == "ALBUM_PAGES_FOOTER_DATE":
                    album.page_setup.footer_date = ft
                else:
                    album.page_setup.header_date = ft
            elif cmd == "ALBUM_PAGES_FOOTER_PAD":
                album.page_setup.footer_padding = float(params[0])
            elif cmd == "ALBUM_PAGES_HEADER_PAD":
                album.page_setup.header_padding = float(params[0])
            elif cmd == "ALBUM_PAGES_MARGIN_TXT_PAD":
                album.page_setup.margin_text_padding = float(params[0])
            elif cmd == "ALBUM_PAGES_CROP_MARKS":
                defaults = [0.1, 1.0, 1.0, 5.0]
                for i in range(min(len(params), 4)):
                    defaults[i] = float(params[i])
                album.page_setup.crop_marks = CropMarkSettings(
                    line_width=defaults[0],
                    hpad=defaults[1],
                    vpad=defaults[2],
                    arms=defaults[3],
                )
            elif cmd == "ALBUM_PAGES_MARGIN_TXT":
                align = TextAlignment.CENTER
                direction = "up"
                if len(params) > 5:
                    # Check if params[4] is alignment or direction
                    if params[4].upper() in (
                        "LEFT",
                        "CENTER",
                        "CENTRE",
                        "RIGHT",
                        "JUSTIFY",
                        "TOP",
                        "BOTTOM",
                    ):
                        align_map = {
                            "LEFT": TextAlignment.LEFT,
                            "CENTER": TextAlignment.CENTER,
                            "CENTRE": TextAlignment.CENTER,
                            "RIGHT": TextAlignment.RIGHT,
                            "JUSTIFY": TextAlignment.JUSTIFY,
                            "TOP": TextAlignment.TOP,
                            "BOTTOM": TextAlignment.BOTTOM,
                        }
                        align = align_map.get(params[4].upper(), TextAlignment.CENTER)
                        if len(params) > 5:
                            direction = params[5].lower()
                    else:
                        direction = params[4].lower()
                album.page_setup.margin_texts.append(
                    MarginTextItem(
                        font_id=unquote(params[0]),
                        size=float(params[1]),
                        text=unquote(params[2]),
                        position=self._parse_position(params[3]),
                        alignment=align,
                        direction=direction,
                    )
                )
            elif cmd == "ALBUM_DEFINE_FONT":
                album.fonts.append(FontDefinition(font_id=unquote(params[0]), font_name=unquote(params[1])))
            elif cmd == "ALBUM_DEFINE_VARIABLE_FONT":
                # ALBUM_DEFINE_VARIABLE_FONT (ID "FontName" axis_tag min max default)
                # e.g., ALBUM_DEFINE_VARIABLE_FONT (VF "My Font" wght 100 900 400)
                axes = []
                i = 2
                while i + 3 < len(params):
                    axes.append({
                        'tag': params[i],
                        'min': float(params[i+1]),
                        'max': float(params[i+2]),
                        'default': float(params[i+3]),
                    })
                    i += 4
                album.fonts.append(FontDefinition(
                    font_id=unquote(params[0]),
                    font_name=unquote(params[1]),
                    is_variable=True,
                    variable_axes=axes,
                ))

            # -- Color commands --
            elif cmd in ("COLOUR_ALBUM_BORDER", "COLOR_ALBUM_BORDER"):
                album.color_album_border = parse_color(params[0])
            elif cmd in ("COLOUR_ALBUM_DECORATIVE_BORDER", "COLOR_ALBUM_DECORATIVE_BORDER"):
                album.color_decorative_border = parse_color(params[0])
            elif cmd in ("COLOUR_ALBUM_FOOTER", "COLOR_ALBUM_FOOTER"):
                album.color_footer = parse_color(params[0])
            elif cmd in ("COLOUR_ALBUM_HEADER", "COLOR_ALBUM_HEADER"):
                album.color_header = parse_color(params[0])
            elif cmd in ("COLOUR_ALBUM_MARGIN_TXT", "COLOR_ALBUM_MARGIN_TXT"):
                album.color_margin_text = parse_color(params[0])
            elif cmd in ("COLOUR_ALBUM_TITLE", "COLOR_ALBUM_TITLE"):
                album.color_title = parse_color(params[0])
            elif cmd in ("COLOUR_PAGE_RULE_H", "COLOR_PAGE_RULE_H"):
                album.color_h_rule = parse_color(params[0])
            elif cmd in ("COLOUR_PAGE_TEXT", "COLOR_PAGE_TEXT"):
                album.color_page_text = parse_color(params[0])
            elif cmd in ("COLOUR_STAMP_BORDER", "COLOR_STAMP_BORDER"):
                album.color_stamp_border = parse_color(params[0])
            elif cmd in ("COLOUR_STAMP_INNER_BORDER", "COLOR_STAMP_INNER_BORDER"):
                album.color_stamp_inner_border = parse_color(params[0])
            elif cmd in ("COLOUR_STAMP_HEADING", "COLOR_STAMP_HEADING"):
                album.color_stamp_heading = parse_color(params[0])
            elif cmd in ("COLOUR_STAMP_TEXT", "COLOR_STAMP_TEXT"):
                album.color_stamp_text = parse_color(params[0])
            elif cmd in ("COLOUR_STAMP_BACKGROUND", "COLOR_STAMP_BACKGROUND"):
                album.color_stamp_background = parse_color(params[0])
            elif cmd in ("COLOUR_PAGE_QUADRILLE", "COLOR_PAGE_QUADRILLE"):
                album.color_quadrille_grid = parse_color(params[0])
                album.color_quadrille_border = parse_color(params[1])
                album.color_quadrille_major = parse_color(params[2])

            # -- Page commands --
            elif cmd == "PAGE_START":
                current_page = Page()
                album.pages.append(current_page)
                current_row = None
                current_stamp = None
            elif cmd == "PAGE_START_VAR":
                current_page = Page()
                album.pages.append(current_page)
                current_row = None
            elif cmd in ("PAGE_TEXT", "PAGE_TEXT_CENTRE", "PAGE_TEXT_CENTER", "PAGE_TEXT_RIGHT"):
                if current_page is None:
                    raise ParseError("PAGE_TEXT command outside of PAGE_START block", line_number, line)
                alignment = TextAlignment.LEFT
                if cmd in ("PAGE_TEXT_CENTRE", "PAGE_TEXT_CENTER"):
                    alignment = TextAlignment.CENTER
                elif cmd == "PAGE_TEXT_RIGHT":
                    alignment = TextAlignment.RIGHT
                # Find vspace: last parameter if it's numeric, otherwise 0.0
                vspace = 0.0
                text_end_idx = len(params)
                if len(params) > 2:
                    last_param = params[-1]
                    try:
                        vspace = float(last_param)
                        text_end_idx = len(params) - 1
                    except ValueError:
                        vspace = 0.0
                # Concatenate all string parameters from index 2 to text_end_idx
                text_content = ""
                for p in params[2:text_end_idx]:
                    if p.startswith('"'):
                        text_content += unquote(p)
                    else:
                        text_content += p
                current_page.text_elements.append(
                    FormattedText(
                        font_id=unquote(params[0]),
                        size=float(params[1]),
                        content=text_content,
                        alignment=alignment,
                        color=album.color_page_text,
                        vspace=vspace,
                    )
                )
                current_page.content_flow.append(("text", current_page.text_elements[-1]))
            elif cmd == "PAGE_VSPACE":
                if current_page:
                    vspace_val = float(params[0])
                    current_page.vspace = vspace_val
                    current_page.content_flow.append(("vspace", vspace_val))
            elif cmd == "PAGE_SET_VERTICAL_POS":
                if current_page:
                    current_page.absolute_vpos = float(params[0])
            elif cmd == "PAGE_BACKGROUND_IMG":
                if current_page:
                    current_page.background_image = unquote(params[0])
            elif cmd == "PAGE_ADD_BOX":
                if current_page:
                    current_page.boxes.append(
                        (
                            float(params[0]),
                            float(params[1]),
                            float(params[2]),
                            float(params[3]),
                        )
                    )
            elif cmd == "PAGE_RULE_H":
                if current_page:
                    current_page.h_rules.append(
                        (
                            float(params[0]),
                            float(params[1]),
                            float(params[2]),
                        )
                    )
            elif cmd == "PAGE_QUADRILLE":
                if current_page:
                    current_page.quadrille = QuadrilleSettings(
                        width=float(params[0]),
                        height=float(params[1]),
                        grid_size=float(params[2]),
                    )
            elif cmd == "PAGE_TEXT_PARAGRAPH_START":
                # Parse paragraph parameters: (font_id size alignment)
                paragraph = Paragraph()
                if len(params) >= 2:
                    paragraph.font_id = params[0]
                    paragraph.size = float(params[1])
                if len(params) >= 3:
                    align_map = {
                        "Left": TextAlignment.LEFT,
                        "Center": TextAlignment.CENTER,
                        "Centre": TextAlignment.CENTER,
                        "Right": TextAlignment.RIGHT,
                        "Justified": TextAlignment.JUSTIFY,
                        "Justify": TextAlignment.JUSTIFY,
                    }
                    paragraph.alignment = align_map.get(params[2], TextAlignment.LEFT)
            elif cmd == "PAGE_TEXT_PARAGRAPH_END":
                # Paragraph ended
                if paragraph and current_page:
                    current_page.paragraphs.append(paragraph)
                    current_page.content_flow.append(("paragraph", paragraph))
                paragraph = None
            elif cmd == "PAGE_COLUMN_START":
                if current_page:
                    from stamp_album.core.models import ColumnMode

                    num_cols = int(float(params[0])) if params else 2
                    if num_cols == 1:
                        current_page.column_mode = ColumnMode.ONE
                    elif num_cols == 2:
                        current_page.column_mode = ColumnMode.TWO
                    elif num_cols == 3:
                        current_page.column_mode = ColumnMode.THREE
                    else:
                        current_page.column_mode = ColumnMode.NONE
                    current_page.column_gap = float(params[1]) if len(params) > 1 else 10.0
            elif cmd == "PAGE_COLUMN_NEXT":
                # Column break marker - no-op, content flows to next column automatically in CSS grid
                pass
            elif cmd == "PAGE_COLUMN_STOP":
                if current_page:
                    from stamp_album.core.models import ColumnMode

                    current_page.column_mode = ColumnMode.NONE

            # -- Row commands --
            elif cmd in ("ROW_START_ES", "ROW_START_FS", "ROW_START_JS", "ROW_START_ROTATE"):
                if current_page is None:
                    raise ParseError("ROW_START command outside of PAGE_START block", line_number, line)
                style_map = {
                    "ROW_START_ES": RowStyle.EQUAL_SPACE,
                    "ROW_START_FS": RowStyle.FIXED_SPACE,
                    "ROW_START_JS": RowStyle.JUSTIFIED_SPACE,
                    "ROW_START_ROTATE": RowStyle.ROTATED,
                }
                current_row = Row(
                    style=style_map[cmd],
                    font_id=unquote(params[0]),
                    size=float(params[1]),
                    spacing=float(params[2]),
                    width=float(params[3]),
                )
                if pending_row_alignment is not None:
                    current_row.alignment = pending_row_alignment
                current_page.rows.append(current_row)
                current_page.content_flow.append(("row", current_row))
            elif cmd == "ROW_ALIGN_TOP":
                pending_row_alignment = RowAlignment.TOP
                if current_row:
                    current_row.alignment = RowAlignment.TOP
            elif cmd == "ROW_ALIGN_MIDDLE":
                pending_row_alignment = RowAlignment.MIDDLE
                if current_row:
                    current_row.alignment = RowAlignment.MIDDLE
            elif cmd == "ROW_ALIGN_BOTTOM":
                pending_row_alignment = RowAlignment.BOTTOM
                if current_row:
                    current_row.alignment = RowAlignment.BOTTOM

            # -- Stamp commands --
            elif cmd == "STAMP_ADD":
                if current_page is None:
                    raise ParseError("STAMP_ADD command outside of PAGE_START block", line_number, line)
                if current_row is None:
                    # Auto-create row if none exists
                    current_row = Row(style=RowStyle.FIXED_SPACE, spacing=album.page_setup.hspace)
                    current_page.rows.append(current_row)
                    current_page.content_flow.append(("row", current_row))
                catalog_refs = []
                for i in range(3, min(len(params), 6)):
                    catalog_refs.append(unquote(params[i]))
                while len(catalog_refs) < 3:
                    catalog_refs.append("")
                stamp = Stamp(
                    width=float(params[0]),
                    height=float(params[1]),
                    description=unquote(params[2]),
                    catalog_refs=catalog_refs,
                    shape=StampShape.RECTANGLE,
                )
                current_row.stamps.append(stamp)
                current_stamp = stamp
            elif cmd == "STAMP_ADD_AT":
                # STAMP_ADD_AT (x y width height "description" "catalog1" "catalog2" "catalog3")
                if current_page is None:
                    raise ParseError("STAMP_ADD_AT command outside of PAGE_START block", line_number, line)
                description = unquote(params[4]) if len(params) > 4 else ""
                catalog_refs = []
                for j in range(5, min(len(params), 8)):
                    catalog_refs.append(unquote(params[j]))
                while len(catalog_refs) < 3:
                    catalog_refs.append("")
                stamp = Stamp(
                    abs_x=float(params[0]),
                    abs_y=float(params[1]),
                    width=float(params[2]),
                    height=float(params[3]),
                    description=description,
                    catalog_refs=catalog_refs,
                    shape=StampShape.RECTANGLE,
                )
                if not hasattr(current_page, "absolute_stamps"):
                    current_page.absolute_stamps = []
                current_page.absolute_stamps.append(stamp)
                current_stamp = stamp
            elif cmd == "STAMP_ADD_BLANK":
                if current_row is None:
                    raise ParseError("STAMP_ADD_BLANK command outside of ROW_START block", line_number, line)
                current_row.stamps.append(
                    Stamp(
                        width=float(params[0]),
                        height=float(params[1]),
                        shape=StampShape.RECTANGLE,
                    )
                )
            elif cmd == "STAMP_ADD_IMG":
                if current_row is None:
                    raise ParseError("STAMP_ADD_IMG command outside of ROW_START block", line_number, line)
                catalog_refs = []
                for i in range(4, min(len(params), 7)):
                    catalog_refs.append(unquote(params[i]))
                while len(catalog_refs) < 3:
                    catalog_refs.append("")
                stamp = Stamp(
                    width=float(params[0]),
                    height=float(params[1]),
                    description=unquote(params[3]),
                    catalog_refs=catalog_refs,
                    image_path=unquote(params[2]),
                    shape=StampShape.RECTANGLE,
                )
                current_row.stamps.append(stamp)
                current_stamp = stamp
            elif cmd in (
                "STAMP_ADD_TRIANGLE",
                "STAMP_ADD_DIAMOND",
                "STAMP_ADD_OVAL",
                "STAMP_ADD_HEXAGON",
                "STAMP_ADD_OCTAGON",
                "STAMP_ADD_PENTAGON",
            ):
                if current_row is None:
                    raise ParseError("STAMP_ADD shape command outside of ROW_START block", line_number, line)
                shape_map = {
                    "STAMP_ADD_TRIANGLE": StampShape.TRIANGLE,
                    "STAMP_ADD_DIAMOND": StampShape.DIAMOND,
                    "STAMP_ADD_OVAL": StampShape.OVAL,
                    "STAMP_ADD_HEXAGON": StampShape.HEXAGON,
                    "STAMP_ADD_OCTAGON": StampShape.OCTAGON,
                    "STAMP_ADD_PENTAGON": StampShape.PENTAGON,
                }
                stamp = Stamp(
                    width=float(params[0]),
                    height=float(params[1]),
                    description=unquote(params[2]),
                    catalog_refs=[unquote(params[3]), unquote(params[4]), unquote(params[5])],
                    shape=shape_map[cmd],
                )
                current_row.stamps.append(stamp)
                current_stamp = stamp
            elif cmd == "STAMP_HEADING":
                if current_stamp:
                    current_stamp.heading = StampHeading(
                        font_id=unquote(params[0]),
                        size=float(params[1]),
                        text=unquote(params[2]),
                    )
            elif cmd == "STAMP_HEADING_VA":
                if current_stamp:
                    align_map = {
                        "LEFT": TextAlignment.LEFT,
                        "CENTER": TextAlignment.CENTER,
                        "CENTRE": TextAlignment.CENTER,
                        "RIGHT": TextAlignment.RIGHT,
                        "TOP": TextAlignment.TOP,
                        "BOTTOM": TextAlignment.BOTTOM,
                    }
                    # Format: (font_id size alignment text) or (font_id size text)
                    if len(params) >= 4:
                        v_align = align_map.get(params[2].upper(), TextAlignment.CENTER)
                        text = unquote(params[3])
                    else:
                        v_align = TextAlignment.CENTER
                        text = unquote(params[2])
                    current_stamp.heading = StampHeading(
                        font_id=unquote(params[0]),
                        size=float(params[1]),
                        text=text,
                        vertical_alignment=v_align,
                    )
            elif cmd == "STAMP_HEADING_PADDING":
                album.page_setup.heading_padding = float(params[0])
            elif cmd == "STAMP_BORDER_STYLE":
                corners = int(float(params[1])) if len(params) > 1 else 0
                album.page_setup.stamp_border_settings.style = self._parse_border_style(params[0])
                album.page_setup.stamp_border_settings.corners = corners
            elif cmd == "STAMP_INNER_BORDER_STYLE":
                corners = int(float(params[1])) if len(params) > 1 else 0
                album.page_setup.stamp_border_settings.inner_style = self._parse_border_style(
                    params[0]
                )
                album.page_setup.stamp_border_settings.inner_corners = corners
            elif cmd == "STAMP_INNER_BORDER":
                album.page_setup.stamp_border_settings.inner_offset = float(params[0])
                album.page_setup.stamp_border_settings.inner_width = float(params[1])
            elif cmd == "STAMP_FOOTER_TXT_PAD":
                album.page_setup.stamp_border_settings.footer_padding = float(params[0])
            elif cmd == "STAMP_FOOTER_TXT_ALIGN":
                align_map = {
                    "LEFT": TextAlignment.LEFT,
                    "CENTER": TextAlignment.CENTER,
                    "CENTRE": TextAlignment.CENTER,
                    "RIGHT": TextAlignment.RIGHT,
                }
                album.page_setup.stamp_border_settings.footer_alignment = align_map.get(
                    params[0].upper(), TextAlignment.CENTER
                )
            elif cmd == "STAMP_BOXES_SIZE_ADJUST":
                album.page_setup.stamp_box_adjust = float(params[0])
            elif cmd in (
                "ALBUM_STAMP_IMG_SETTING",
                "ALBUM_STAMP_IMG_NEW_SETTING",
                "ALBUM_STAMP_NEW_IMG_SETTING",
            ):
                album.page_setup.stamp_image_settings.hspace = float(params[0])
                album.page_setup.stamp_image_settings.vspace = float(params[1])
                album.page_setup.stamp_image_settings.stretch = params[2].lower() == "true"
            elif cmd == "ALBUM_STAMP_IMG_NEW_SETTING_PCNT":
                album.page_setup.stamp_image_settings.hspace = float(params[0])
                album.page_setup.stamp_image_settings.vspace = float(params[1])
                album.page_setup.stamp_image_settings.stretch = params[2].lower() == "true"
                album.page_setup.stamp_image_settings.use_percent = True
            elif cmd == "ALBUM_STAMP_IMG_ASPECT_RATIO":
                album.page_setup.stamp_image_settings.fixed_aspect_ratio = (
                    params[0].lower() == "true"
                )
            elif cmd in ("ALBUM_STAMP_IMG_GREYSCALE_ON", "ALBUM_STAMP_IMG_GRAYSCALE_ON"):
                album.page_setup.stamp_image_settings.grayscale = True
            elif cmd in ("ALBUM_STAMP_IMG_GREYSCALE_OFF", "ALBUM_STAMP_IMG_GRAYSCALE_OFF"):
                album.page_setup.stamp_image_settings.grayscale = False
            elif cmd == "ALBUM_STAMP_IMG_HIDE":
                album.page_setup.stamp_image_settings.hidden = True
            elif cmd == "ALBUM_STAMP_IMG_SHOW":
                album.page_setup.stamp_image_settings.hidden = False

            # -- Text settings --
            elif cmd == "TEXT_CHAR_SPACING":
                album.page_setup.text_char_spacing = float(params[0])
            elif cmd == "TEXT_LINE_LEADING":
                album.page_setup.text_line_leading = float(params[0])
            elif cmd == "TEXT_SHADOW":
                # TEXT_SHADOW (offset_x offset_y blur color opacity)
                from stamp_album.core.models import TextShadow

                shadow = TextShadow()
                vals = params if params else tokens[1:]
                if len(vals) >= 2:
                    shadow.offset_x = float(vals[0])
                    shadow.offset_y = float(vals[1])
                if len(vals) >= 3:
                    shadow.blur = float(vals[2])
                if len(vals) >= 4:
                    shadow.color = Color.from_name(vals[3].strip("()"))
                if len(vals) >= 5:
                    shadow.opacity = float(vals[4])
                album.page_setup.default_text_shadow = shadow
            elif cmd == "TEXT_OUTLINE":
                # TEXT_OUTLINE (width color)
                from stamp_album.core.models import TextOutline

                outline = TextOutline()
                vals = params if params else tokens[1:]
                if len(vals) >= 1:
                    outline.width = float(vals[0])
                if len(vals) >= 2:
                    outline.color = Color.from_name(vals[1].strip("()"))
                album.page_setup.default_text_outline = outline
            elif cmd == "TEXT_GRADIENT":
                # TEXT_GRADIENT (direction color1 offset1 color2 offset2 ...)
                from stamp_album.core.models import GradientFill, GradientStop

                gradient = GradientFill()
                vals = params if params else tokens[1:]
                if len(vals) >= 1:
                    gradient.direction = vals[0]
                i = 1
                while i + 1 < len(vals):
                    color = Color.from_name(vals[i].strip("()"))
                    offset = float(vals[i + 1])
                    gradient.stops.append(GradientStop(offset=offset, color=color))
                    i += 2
                album.page_setup.default_text_gradient = gradient if gradient.stops else None
            elif cmd == "TEXT_WEIGHT":
                if params:
                    album.page_setup.default_text_weight = params[0]
                elif len(tokens) > 1:
                    album.page_setup.default_text_weight = tokens[1]
            elif cmd == "TEXT_STYLE":
                if params:
                    album.page_setup.default_text_style = params[0]
                elif len(tokens) > 1:
                    album.page_setup.default_text_style = tokens[1]
            elif cmd == "PAGE_TEXT_DROP_CAP":
                # PAGE_TEXT_DROP_CAP (font_id size lines "text")
                # lines = number of lines the drop cap spans (default 2)
                if current_page is None:
                    raise ParseError("PAGE_TEXT_DROP_CAP command outside of PAGE_START block", line_number, line)
                drop_lines = int(float(params[2])) if len(params) > 2 else 2
                text_content = unquote(params[3]) if len(params) > 3 else unquote(params[2])
                ft = FormattedText(
                    font_id=unquote(params[0]),
                    size=float(params[1]),
                    content=text_content,
                    alignment=TextAlignment.LEFT,
                    color=album.color_page_text,
                    drop_cap_lines=drop_lines,
                )
                current_page.text_elements.append(ft)
                current_page.content_flow.append(("text", current_page.text_elements[-1]))
            elif paragraph is not None:
                # Unquote if it's a quoted string, otherwise use as-is
                content = unquote(line) if line.startswith('"') else line
                paragraph.lines.append(content)

        return album

    def parse_file(self, file_path: str) -> Album:
        """Parse a DSL source file into an Album model."""
        with open(file_path, "r", encoding="utf-8-sig") as f:
            source_text = f.read()
        return self.parse(source_text, source_path=file_path)

    def _parse_position(self, val: str) -> Position:
        """Parse a position value."""
        pos_map = {
            "L": Position.LEFT,
            "R": Position.RIGHT,
            "C": Position.CENTER,
            "LR": Position.LEFT_RIGHT,
            "RL": Position.RIGHT_LEFT,
            "NONE": Position.NONE,
        }
        return pos_map.get(val.upper(), Position.NONE)

    def _parse_border_style(self, val: str):
        """Parse a border style value."""
        from stamp_album.core.models import BorderStyle

        style_map = {
            "SOLID": BorderStyle.SOLID,
            "DASHED": BorderStyle.DASHED,
            "DOTTED": BorderStyle.DOTTED,
            "BLANK": BorderStyle.BLANK,
        }
        return style_map.get(val.upper(), BorderStyle.SOLID)

    def validate(self, album: Album) -> list[str]:
        """
        Validate a parsed album for common issues.

        Returns a list of warning messages (empty if no issues).
        """
        warnings: list[str] = []

        if not album.pages:
            warnings.append("Album has no pages — add PAGE_START to create pages")

        for page_idx, page in enumerate(album.pages):
            prefix = f"Page {page_idx + 1}"

            if not page.text_elements and not page.rows:
                warnings.append(f"{prefix}: empty page (no text or stamps)")

            for row_idx, row in enumerate(page.rows):
                row_prefix = f"{prefix}, Row {row_idx + 1}"

                if not row.stamps:
                    warnings.append(f"{row_prefix}: row has no stamps")
                    continue

                for stamp_idx, stamp in enumerate(row.stamps):
                    stamp_prefix = f"{row_prefix}, Stamp {stamp_idx + 1}"

                    if stamp.width <= 0 and stamp.height <= 0:
                        warnings.append(
                            f"{stamp_prefix}: zero-size stamp "
                            f"(width={stamp.width}, height={stamp.height}) — "
                            f"stamp will be invisible in output"
                        )
                    elif stamp.width <= 0:
                        warnings.append(
                            f"{stamp_prefix}: zero width ({stamp.width}) — "
                            f"stamp will be invisible in output"
                        )
                    elif stamp.height <= 0:
                        warnings.append(
                            f"{stamp_prefix}: zero height ({stamp.height}) — "
                            f"stamp will be invisible in output"
                        )

        return warnings
