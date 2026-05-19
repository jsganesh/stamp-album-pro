"""
Core data models for stamp album definitions.

This module defines the data structures that represent a stamp album,
including pages, stamps, rows, text elements, and styling information.
All models are pure Python data classes with no UI dependencies.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class PageSize(enum.Enum):
    """Standard page sizes."""

    A3 = (297.0, 420.0)
    A4 = (210.0, 297.0)
    A5 = (148.0, 210.0)
    LETTER = (215.9, 279.4)
    LEGAL = (215.9, 355.6)
    CUSTOM = (0.0, 0.0)


class TextAlignment(enum.Enum):
    """Text alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"
    TOP = "top"
    BOTTOM = "bottom"


class RowStyle(enum.Enum):
    """Row layout styles."""

    EQUAL_SPACE = "equal_space"
    FIXED_SPACE = "fixed_space"
    JUSTIFIED_SPACE = "justified_space"
    ROTATED = "rotated"


class RowAlignment(enum.Enum):
    """Vertical alignment of stamps within a row."""

    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class StampShape(enum.Enum):
    """Stamp box shapes."""

    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"
    TRIANGLE_INV = "triangle_inverted"
    RIGHT_TRIANGLE = "right_triangle"
    DIAMOND = "diamond"
    OVAL = "oval"
    HEXAGON = "hexagon"
    OCTAGON = "octagon"
    PENTAGON = "pentagon"


class BorderStyle(enum.Enum):
    """Border line styles."""

    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    BLANK = "blank"


class Position(enum.Enum):
    """Horizontal position on page."""

    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    LEFT_RIGHT = "left_right"
    RIGHT_LEFT = "right_left"
    NONE = "none"


class DateFormat(enum.Enum):
    """Date format options."""

    YMD = "%Y-%m-%d"
    DMY = "%d-%m-%Y"
    MDY = "%m-%d-%Y"


class ColumnMode(enum.Enum):
    """Column layout mode."""

    NONE = "none"
    TWO_COLUMN = "two_column"


# ---------------------------------------------------------------------------
# Color
# ---------------------------------------------------------------------------


@dataclass
class Color:
    """RGB color representation."""

    r: float = 0.0
    g: float = 0.0
    b: float = 0.0

    @classmethod
    def from_name(cls, name: str) -> Color:
        """Create a Color from an HTML color name."""
        color_map = {
            "black": (0.0, 0.0, 0.0),
            "white": (1.0, 1.0, 1.0),
            "red": (1.0, 0.0, 0.0),
            "green": (0.0, 0.5, 0.0),
            "blue": (0.0, 0.0, 1.0),
            "yellow": (1.0, 1.0, 0.0),
            "cyan": (0.0, 1.0, 1.0),
            "magenta": (1.0, 0.0, 1.0),
            "gray": (0.5, 0.5, 0.5),
            "grey": (0.5, 0.5, 0.5),
            "lime": (0.0, 1.0, 0.0),
            "maroon": (0.5, 0.0, 0.0),
            "navy": (0.0, 0.0, 0.5),
            "olive": (0.5, 0.5, 0.0),
            "purple": (0.5, 0.0, 0.5),
            "silver": (0.75, 0.75, 0.75),
            "teal": (0.0, 0.5, 0.5),
            "crimson": (0.86, 0.08, 0.24),
            "gold": (1.0, 0.84, 0.0),
            "hotpink": (1.0, 0.41, 0.71),
            "seagreen": (0.18, 0.55, 0.34),
            "royalblue": (0.25, 0.41, 0.88),
            "ghostwhite": (0.97, 0.97, 0.99),
            "lemonchiffon": (1.0, 0.98, 0.8),
            "lawngreen": (0.49, 0.99, 0.0),
            "springgreen": (0.0, 1.0, 0.5),
            "chartreuse": (0.5, 1.0, 0.0),
            "deeppink": (1.0, 0.08, 0.58),
            "lightsteelblue": (0.69, 0.77, 0.87),
            "lightgrey": (0.83, 0.83, 0.83),
            "lightgray": (0.83, 0.83, 0.83),
            # Extended colors
            "darkred": (0.55, 0.0, 0.0),
            "darkblue": (0.0, 0.0, 0.55),
            "darkgreen": (0.0, 0.39, 0.0),
            "darkgray": (0.66, 0.66, 0.66),
            "darkgrey": (0.66, 0.66, 0.66),
            "darkorange": (1.0, 0.55, 0.0),
            "darkyellow": (0.8, 0.8, 0.0),
            "darkpurple": (0.3, 0.0, 0.3),
            "lightblue": (0.68, 0.85, 0.9),
            "lightgreen": (0.56, 0.93, 0.56),
            "lightyellow": (1.0, 1.0, 0.88),
            "lightred": (1.0, 0.6, 0.6),
            "orange": (1.0, 0.65, 0.0),
            "pink": (1.0, 0.75, 0.8),
            "brown": (0.65, 0.16, 0.16),
            "coral": (1.0, 0.5, 0.31),
            "indigo": (0.29, 0.0, 0.51),
            "violet": (0.93, 0.51, 0.93),
            "turquoise": (0.25, 0.88, 0.82),
            "wheat": (0.96, 0.87, 0.7),
            "salmon": (0.98, 0.5, 0.45),
            "khaki": (0.94, 0.9, 0.55),
            "plum": (0.87, 0.63, 0.87),
            "beige": (0.96, 0.96, 0.86),
            "ivory": (1.0, 1.0, 0.94),
            "lavender": (0.9, 0.9, 0.98),
            "mint": (0.6, 1.0, 0.6),
            "peach": (1.0, 0.85, 0.73),
            "tan": (0.82, 0.71, 0.55),
            "skyblue": (0.53, 0.81, 0.92),
            "slategray": (0.44, 0.5, 0.56),
            "slategrey": (0.44, 0.5, 0.56),
            "steelblue": (0.27, 0.51, 0.71),
            "tomato": (1.0, 0.39, 0.28),
            "aquamarine": (0.5, 1.0, 0.83),
            "azure": (0.0, 0.5, 1.0),
            "bisque": (1.0, 0.89, 0.77),
            "blanchedalmond": (1.0, 0.92, 0.8),
            "blueviolet": (0.54, 0.17, 0.89),
            "burlywood": (0.87, 0.72, 0.53),
            "cadetblue": (0.37, 0.62, 0.63),
            "chocolate": (0.82, 0.41, 0.12),
            "cornflowerblue": (0.39, 0.58, 0.93),
            "cornsilk": (1.0, 0.97, 0.86),
            "darkcyan": (0.0, 0.55, 0.55),
            "darkgoldenrod": (0.72, 0.53, 0.04),
            "darkkhaki": (0.74, 0.72, 0.42),
            "darkmagenta": (0.55, 0.0, 0.55),
            "darkolivegreen": (0.33, 0.42, 0.18),
            "darkorchid": (0.6, 0.2, 0.8),
            "darksalmon": (0.91, 0.59, 0.48),
            "darkseagreen": (0.56, 0.74, 0.56),
            "darkslateblue": (0.28, 0.24, 0.55),
            "darkslategray": (0.18, 0.31, 0.31),
            "darkslategrey": (0.18, 0.31, 0.31),
            "darkturquoise": (0.0, 0.81, 0.82),
            "darkviolet": (0.58, 0.0, 0.83),
            "deepskyblue": (0.0, 0.75, 1.0),
            "dimgray": (0.41, 0.41, 0.41),
            "dimgrey": (0.41, 0.41, 0.41),
            "dodgerblue": (0.12, 0.56, 1.0),
            "firebrick": (0.7, 0.13, 0.13),
            "floralwhite": (1.0, 0.98, 0.94),
            "forestgreen": (0.13, 0.55, 0.13),
            "fuchsia": (1.0, 0.0, 1.0),
            "gainsboro": (0.86, 0.86, 0.86),
            "goldenrod": (0.85, 0.65, 0.13),
            "greenyellow": (0.68, 1.0, 0.18),
            "honeydew": (0.94, 1.0, 0.94),
            "indianred": (0.8, 0.36, 0.36),
            "lightcoral": (0.94, 0.5, 0.5),
            "lightcyan": (0.88, 1.0, 1.0),
            "lightgoldenrodyellow": (0.98, 0.98, 0.82),
            "lightpink": (1.0, 0.71, 0.76),
            "lightsalmon": (1.0, 0.63, 0.48),
            "lightseagreen": (0.13, 0.7, 0.67),
            "lightskyblue": (0.53, 0.81, 0.98),
            "lightslategray": (0.47, 0.53, 0.6),
            "lightslategrey": (0.47, 0.53, 0.6),
            "limegreen": (0.2, 0.8, 0.2),
            "linen": (0.98, 0.94, 0.9),
            "mediumaquamarine": (0.4, 0.8, 0.67),
            "mediumblue": (0.0, 0.0, 0.8),
            "mediumorchid": (0.73, 0.33, 0.83),
            "mediumpurple": (0.58, 0.44, 0.86),
            "mediumseagreen": (0.24, 0.7, 0.44),
            "mediumslateblue": (0.48, 0.41, 0.93),
            "mediumspringgreen": (0.0, 0.98, 0.6),
            "mediumturquoise": (0.28, 0.82, 0.8),
            "mediumvioletred": (0.78, 0.08, 0.52),
            "midnightblue": (0.1, 0.1, 0.44),
            "mistyrose": (1.0, 0.89, 0.88),
            "moccasin": (1.0, 0.89, 0.71),
            "navajowhite": (1.0, 0.87, 0.68),
            "oldlace": (0.99, 0.96, 0.9),
            "olivedrab": (0.42, 0.56, 0.14),
            "orangered": (1.0, 0.27, 0.0),
            "orchid": (0.85, 0.44, 0.84),
            "palegoldenrod": (0.93, 0.91, 0.67),
            "palegreen": (0.6, 0.98, 0.6),
            "paleturquoise": (0.69, 0.93, 0.93),
            "palevioletred": (0.86, 0.44, 0.58),
            "papayawhip": (1.0, 0.94, 0.84),
            "powderblue": (0.69, 0.88, 0.9),
            "rosybrown": (0.74, 0.56, 0.56),
            "saddlebrown": (0.55, 0.27, 0.07),
            "sandybrown": (0.96, 0.64, 0.38),
            "seashell": (1.0, 0.96, 0.93),
            "sienna": (0.63, 0.32, 0.18),
            "snow": (1.0, 0.98, 0.98),
            "thistle": (0.85, 0.75, 0.85),
            "yellowgreen": (0.6, 0.8, 0.2),
        }
        lower = name.lower()
        if lower in color_map:
            rgb = color_map[lower]
            return cls(r=rgb[0], g=rgb[1], b=rgb[2])
        # Fallback: try to parse as hex or return black
        try:
            return cls.from_hex(name)
        except ValueError:
            # Return black for unknown colors instead of crashing
            return cls(r=0.0, g=0.0, b=0.0)

    @classmethod
    def from_rgb(cls, r: float, g: float, b: float) -> Color:
        """Create a Color from RGB values (0-255 range)."""
        return cls(r=r / 255.0, g=g / 255.0, b=b / 255.0)

    @classmethod
    def from_hex(cls, hex_str: str) -> Color:
        """Create a Color from a hex string like '#RRGGBB'."""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color: {hex_str}")
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return cls(r=r, g=g, b=b)

    def to_tuple(self) -> tuple[float, float, float]:
        """Return RGB as a tuple."""
        return (self.r, self.g, self.b)


# ---------------------------------------------------------------------------
# Text Elements
# ---------------------------------------------------------------------------


@dataclass
class TextShadow:
    """Text shadow effect."""

    offset_x: float = 1.0  # mm
    offset_y: float = -1.0  # mm
    blur: float = 0.5  # mm
    color: Color = field(default_factory=lambda: Color(r=0.0, g=0.0, b=0.0))
    opacity: float = 0.5


@dataclass
class TextOutline:
    """Text outline/stroke effect."""

    width: float = 0.3  # mm
    color: Color = field(default_factory=lambda: Color(r=0.0, g=0.0, b=0.0))


@dataclass
class GradientStop:
    """A single stop in a gradient."""

    offset: float  # 0.0 to 1.0
    color: Color


@dataclass
class GradientFill:
    """Gradient fill for text."""

    direction: str = "horizontal"  # horizontal, vertical, diagonal
    stops: list[GradientStop] = field(default_factory=list)


@dataclass
class FormattedText:
    """Text with formatting information."""

    font_id: str = "HN"
    size: float = 10.0
    content: str = ""
    alignment: TextAlignment = TextAlignment.LEFT
    color: Optional[Color] = None
    vspace: float = 0.0
    left_padding: float = 0.0
    right_padding: float = 0.0
    char_spacing: float = 0.0
    line_leading: float = 0.0
    # Phase 4: Advanced typography
    shadow: Optional[TextShadow] = None
    outline: Optional[TextOutline] = None
    gradient: Optional[GradientFill] = None
    weight: str = "normal"  # normal, bold, bolder, light, etc.
    style: str = "normal"  # normal, italic, oblique


@dataclass
class Paragraph:
    """Multi-line paragraph."""

    lines: list[str] = field(default_factory=list)
    font_id: str = "HN"
    size: float = 10.0
    alignment: TextAlignment = TextAlignment.LEFT
    color: Optional[Color] = None
    # Phase 4: Advanced typography
    shadow: Optional[TextShadow] = None
    outline: Optional[TextOutline] = None
    gradient: Optional[GradientFill] = None
    weight: str = "normal"
    style: str = "normal"


# ---------------------------------------------------------------------------
# Stamp Elements
# ---------------------------------------------------------------------------


@dataclass
class StampHeading:
    """Heading text for a stamp."""

    font_id: str = "HN"
    size: float = 10.0
    text: str = ""
    padding: float = 0.0
    vertical_alignment: TextAlignment = TextAlignment.CENTER


@dataclass
class StampImageSettings:
    """Settings for stamp image rendering."""

    hspace: float = 0.0
    vspace: float = 0.0
    stretch: bool = True
    use_percent: bool = False
    fixed_aspect_ratio: bool = False
    grayscale: bool = False
    hidden: bool = False


@dataclass
class StampBorderSettings:
    """Settings for stamp box borders."""

    style: BorderStyle = BorderStyle.SOLID
    corners: int = 0
    edges: int = 0xF  # All edges by default
    inner_style: BorderStyle = BorderStyle.SOLID
    inner_corners: int = 0
    inner_edges: int = 0xF
    inner_offset: float = 0.0
    inner_width: float = 0.0
    footer_padding: float = 0.0
    footer_alignment: TextAlignment = TextAlignment.CENTER


@dataclass
class Stamp:
    """A single stamp element."""

    width: float = 0.0
    height: float = 0.0
    description: str = ""
    catalog_refs: list[str] = field(default_factory=list)
    shape: StampShape = StampShape.RECTANGLE
    image_path: Optional[str] = None
    heading: Optional[StampHeading] = None
    footer_text: str = ""


# ---------------------------------------------------------------------------
# Row Elements
# ---------------------------------------------------------------------------


@dataclass
class Row:
    """A row of stamps."""

    style: RowStyle = RowStyle.FIXED_SPACE
    font_id: str = "HN"
    size: float = 10.0
    spacing: float = 0.0
    width: float = 0.0
    alignment: RowAlignment = RowAlignment.TOP
    stamps: list[Stamp] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Page Elements
# ---------------------------------------------------------------------------


@dataclass
class QuadrilleSettings:
    """Grid/quadrille pattern settings."""

    width: float = 0.0
    height: float = 0.0
    grid_size: float = 0.0
    major_interval: int = 5
    grid_color: Optional[Color] = None
    border_color: Optional[Color] = None
    major_color: Optional[Color] = None


@dataclass
class CropMarkSettings:
    """Crop mark settings."""

    line_width: float = 0.1
    hpad: float = 1.0
    vpad: float = 1.0
    arms: float = 5.0


@dataclass
class MarginTextItem:
    """Vertical margin text."""

    font_id: str = "HN"
    size: float = 10.0
    text: str = ""
    position: Position = Position.LEFT
    alignment: TextAlignment = TextAlignment.CENTER
    direction: str = "up"  # "up" or "down"


@dataclass
class Page:
    """A single album page."""

    title: Optional[FormattedText] = None
    header: Optional[FormattedText] = None
    footer: Optional[FormattedText] = None
    margin_texts: list[MarginTextItem] = field(default_factory=list)
    text_elements: list[FormattedText] = field(default_factory=list)
    paragraphs: list[Paragraph] = field(default_factory=list)
    rows: list[Row] = field(default_factory=list)
    h_rules: list[tuple[float, float, float]] = field(default_factory=list)
    quadrille: Optional[QuadrilleSettings] = None
    background_image: Optional[str] = None
    column_mode: ColumnMode = ColumnMode.NONE
    column_gap: float = 0.0
    vspace: float = 0.0
    absolute_vpos: Optional[float] = None
    boxes: list[tuple[float, float, float, float]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Album Configuration
# ---------------------------------------------------------------------------


@dataclass
class PageSetup:
    """Global page setup configuration."""

    width: float = 210.0
    height: float = 297.0
    margin_left: float = 20.0
    margin_right: float = 15.0
    margin_top: float = 15.0
    margin_bottom: float = 15.0
    even_margin_left: float = 20.0
    even_margin_right: float = 15.0
    even_margin_top: float = 15.0
    even_margin_bottom: float = 15.0
    mirror_margins: bool = False
    hspace: float = 6.0
    vspace: float = 6.0
    border_outer: float = 0.0
    border_inner1: float = 0.0
    border_inner2: float = 0.0
    border_spacing: float = 1.0
    has_border: bool = False
    decorative_border_file: Optional[str] = None
    title: Optional[FormattedText] = None
    header_page_num: Optional[FormattedText] = None
    footer_page_num: Optional[FormattedText] = None
    header_date: Optional[FormattedText] = None
    footer_date: Optional[FormattedText] = None
    header_text: Optional[FormattedText] = None
    footer_text: Optional[FormattedText] = None
    header_padding: float = 2.0
    footer_padding: float = 0.5
    margin_text_padding: float = 2.0
    crop_marks: Optional[CropMarkSettings] = None
    stamp_image_settings: StampImageSettings = field(default_factory=StampImageSettings)
    stamp_border_settings: StampBorderSettings = field(default_factory=StampBorderSettings)
    stamp_box_adjust: float = 0.0
    heading_padding: float = 0.0
    text_char_spacing: float = 0.0
    text_line_leading: float = 0.0
    # Phase 4: Default typography settings
    default_text_shadow: Optional[TextShadow] = None
    default_text_outline: Optional[TextOutline] = None
    default_text_gradient: Optional[GradientFill] = None
    default_text_weight: str = "normal"
    default_text_style: str = "normal"


@dataclass
class FontDefinition:
    """User-defined font mapping."""

    font_id: str
    font_name: str


@dataclass
class CommandGroup:
    """Reusable page template."""

    name: str
    lines: list[str] = field(default_factory=list)


@dataclass
class Album:
    """Complete album definition."""

    title: str = ""
    author: str = ""
    page_setup: PageSetup = field(default_factory=PageSetup)
    fonts: list[FontDefinition] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)
    command_groups: dict[str, CommandGroup] = field(default_factory=dict)
    defines: set[str] = field(default_factory=set)
    source_path: Optional[str] = None

    # Color settings
    color_album_border: Optional[Color] = None
    color_decorative_border: Optional[Color] = None
    color_footer: Optional[Color] = None
    color_header: Optional[Color] = None
    color_margin_text: Optional[Color] = None
    color_title: Optional[Color] = None
    color_h_rule: Optional[Color] = None
    color_quadrille_grid: Optional[Color] = None
    color_quadrille_border: Optional[Color] = None
    color_quadrille_major: Optional[Color] = None
    color_page_text: Optional[Color] = None
    color_stamp_border: Optional[Color] = None
    color_stamp_inner_border: Optional[Color] = None
    color_stamp_heading: Optional[Color] = None
    color_stamp_text: Optional[Color] = None
    color_stamp_background: Optional[Color] = None
