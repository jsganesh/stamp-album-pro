# StampAlbum Pro - DSL Specification

## Overview
The StampAlbum Pro DSL (Domain Specific Language) is a declarative text format for defining stamp album pages. It uses a command-based syntax with parameters in parentheses.

---

## Syntax Rules

### Comments
```
# This is a comment - everything after # is ignored
```

### Commands
```
COMMAND_NAME (parameter1 parameter2 "string parameter")
```

### String Literals
```
"Text in quotes can contain spaces and special characters"
"Escape sequences: \n for newline, \\ for backslash"
```

### Line Continuation
```
COMMAND_NAME (param1 param2 \
              param3 param4)
```

### Parameters
- Numeric values: `25.0`, `37`, `0.1`
- String values: `"text"`, `"A4"`
- Identifiers: `HN`, `TB`, `CN` (font codes)
- Keywords: `L`, `R`, `C`, `LR`, `RL` (positions)

---

## Command Reference

### Document Commands
```
ALBUM_TITLE ("Document Title")
ALBUM_AUTHOR ("Author Name")
```

### Page Setup Commands (Global)
```
ALBUM_PAGES_SIZE (width_mm height_mm)
ALBUM_PAGES_MARGINS (left right top bottom)
ALBUM_PAGES_MARGINSE (left right top bottom)  # Even pages
ALBUM_PAGES_BORDER (outer inner1 inner2 spacing)
ALBUM_PAGES_DECORATIVE_BORDER ("filename.txt")
ALBUM_PAGES_SPACING (horizontal vertical)
ALBUM_PAGES_TITLE (FontID size "Title Text" [vspace])
ALBUM_PAGES_HEADER (FontID size position "Text")
ALBUM_PAGES_FOOTER (FontID size position "Text")
ALBUM_PAGES_HEADER_NUMBER (FontID size position start "before" "after")
ALBUM_PAGES_FOOTER_NUMBER (FontID size position start "before" "after")
ALBUM_PAGES_HEADER_DATE (FontID size position format "separator" "before" "after")
ALBUM_PAGES_FOOTER_DATE (FontID size position format "separator" "before" "after")
ALBUM_PAGES_HEADER_PAD (padding_mm)
ALBUM_PAGES_FOOTER_PAD (padding_mm)
ALBUM_PAGES_MARGIN_TXT_PAD (padding_mm)
ALBUM_PAGES_CROP_MARKS ([line] [hpad] [vpad] [arms])
ALBUM_DEFINE_FONT (FontID "FontName")
```

### Page Commands
```
PAGE_START
PAGE_START_VAR (hspace vspace)
PAGE_START_INFO (info_text)
PAGE_TEXT (FontID size "Text" [vspace] [lpadding] [rpadding])
PAGE_TEXT_CENTRE (FontID size "Text" ...)
PAGE_TEXT_RIGHT (FontID size "Text" ...)
PAGE_VSPACE (space_mm)
PAGE_SET_VERTICAL_POS (position_mm)
PAGE_BACKGROUND_IMG ("filename.png")
PAGE_ADD_BOX (x y width height)
PAGE_RULE_H (line_mm spacing_mm margin_mm)
PAGE_QUADRILLE (width height grid_major [color1] [color2] [color3])
PAGE_TEXT_PARAGRAPH_START
PAGE_TEXT_PARAGRAPH_END
```

### Column Commands
```
PAGE_COLUMN_START (gap_mm)
PAGE_COLUMN_NEXT
PAGE_COLUMN_STOP
```

### Row Commands
```
ROW_START_ES (FontID size spacing width)   # Equal space
ROW_START_FS (FontID size spacing width)   # Fixed space
ROW_START_JS (FontID size spacing width)   # Justified space
ROW_START_ROTATE (FontID size spacing width)
ROW_ALIGN_TOP
ROW_ALIGN_MIDDLE
ROW_ALIGN_BOTTOM
```

### Stamp Commands
```
STAMP_ADD (width height "description" "catalog1" "catalog2" "catalog3")
STAMP_ADD_BLANK (width height)
STAMP_ADD_IMG (width height "image_file" "description" ...)
STAMP_ADD_TRIANGLE (width height ...)
STAMP_ADD_DIAMOND (width height ...)
STAMP_ADD_OVAL (width height ...)
STAMP_ADD_HEXAGON (width height ...)
STAMP_ADD_OCTAGON (width height ...)
STAMP_ADD_PENTAGON (width height ...)

STAMP_HEADING (FontID size "Heading Text")
STAMP_HEADING_VA (FontID size align "Heading Text")
STAMP_HEADING_PADDING (padding_mm)

STAMP_BORDER_STYLE (style [corners])
STAMP_INNER_BORDER_STYLE (style [corners])
STAMP_INNER_BORDER (offset_mm width_mm)
STAMP_FOOTER_TXT_PAD (padding_mm)
STAMP_FOOTER_TXT_ALIGN (align)

STAMP_BOXES_SIZE_ADJUST (adjust_mm)
STAMP_IMG_SETTING (hspace vspace stretch)
STAMP_IMG_NEW_SETTING (hspace_mm vspace_mm stretch)
STAMP_IMG_NEW_SETTING_PCNT (hspace% vspace% stretch)
STAMP_IMG_ASPECT_RATIO (fixed)
STAMP_IMG_GREYSCALE_ON / STAMP_IMG_GREYSCALE_OFF
STAMP_IMG_HIDE / STAMP_IMG_SHOW
STAMP_SETTINGS_SAVE
STAMP_SETTINGS_RESTORE
```

### Color Commands
```
COLOUR_ALBUM_BORDER (color)
COLOUR_ALBUM_DECORATIVE_BORDER (color)
COLOUR_ALBUM_FOOTER (color)
COLOUR_ALBUM_HEADER (color)
COLOUR_ALBUM_MARGIN_TXT (color)
COLOUR_ALBUM_TITLE (color)
COLOUR_PAGE_RULE_H (color)
COLOUR_PAGE_QUADRILLE (color1 color2 color3)
COLOUR_PAGE_TEXT (color)
COLOUR_STAMP_BORDER (color)
COLOUR_STAMP_INNER_BORDER (color)
COLOUR_STAMP_HEADING (color)
COLOUR_STAMP_TEXT (color)
COLOUR_STAMP_BACKGROUND (color)
```

### Text Formatting Commands
```
TEXT_CHAR_SPACING (spacing)
TEXT_LINE_LEADING (leading)
```

### Command Group Commands
```
PAGE_START_GROUP_BEGIN (group_name)
PAGE_START_GROUP_END
```

### Conditional Commands
```
$DEFINE name
$UNDEFINE name
$IFDEF name
$ELSEIF name
$ELSE
$ENDIF
$INCLUDE "filename.txt"
```

---

## Font Identifiers

### Base-14 PDF Fonts
| ID | Font |
|----|------|
| CN | Courier |
| CB | Courier-Bold |
| CI | Courier-Oblique |
| CS | Courier-BoldOblique |
| TN | Times-Roman |
| TB | Times-Bold |
| TI | Times-Italic |
| TS | Times-BoldItalic |
| HN | Helvetica |
| HB | Helvetica-Bold |
| HI | Helvetica-Oblique |
| HS | Helvetica-BoldOblique |

### User-Defined Fonts
```
ALBUM_DEFINE_FONT (MY "My Custom Font")
```

---

## Position Values
| Value | Meaning |
|-------|---------|
| L | Left |
| R | Right |
| C | Center |
| LR | Left on odd, Right on even |
| RL | Right on odd, Left on even |

---

## Date Formats
| Format | Example |
|--------|---------|
| YMD | 2024-01-15 |
| DMY | 15-01-2024 |
| MDY | 01-15-2024 |

---

## Border Styles
| Style | Description |
|-------|-------------|
| SOLID | Solid line |
| DASHED | Dashed line |
| DOTTED | Dotted line |
| BLANK | No border |

---

## Stamp Box Shapes
| Command | Shape |
|---------|-------|
| STAMP_ADD | Rectangle |
| STAMP_ADD_TRIANGLE | Triangle |
| STAMP_ADD_DIAMOND | Diamond |
| STAMP_ADD_OVAL | Oval |
| STAMP_ADD_HEXAGON | Hexagon |
| STAMP_ADD_OCTAGON | Octagon |
| STAMP_ADD_PENTAGON | Pentagon |

---

## Example Album
```
# Union of South Africa Album
ALBUM_PAGES_SIZE (215.9 279.4)
ALBUM_PAGES_MARGINS (25.0 12.0 15.0 15.0)
ALBUM_PAGES_BORDER (0.1 0.5 0.1 1.0)
ALBUM_PAGES_TITLE (TB 16 "Union of South Africa")
ALBUM_PAGES_SPACING (6.0 6.0)

PAGE_START

PAGE_TEXT (HN 10 "The Cape of Good Hope, Natal, the Orange Free State and "\
                 "Transvaal were united on the 31st of May 1910...")

PAGE_TEXT_CENTRE (HS 12 "4 November 1910\nInauguration of The Union Parliament.")

ROW_START_FS (HN 6 0.1 6.0)
STAMP_ADD (32.0 37.0 "2 1/2d \n deep blue \n blue surface" "sg 1" "" "sacc 1")
STAMP_ADD (32.0 37.0 "2 1/2d \n blue \n white surface" "sg 2" "" "sacc 1a")
```
