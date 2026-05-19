# StampAlbum Pro

A modern stamp album typesetter with live preview and advanced typography.

## Overview

StampAlbum Pro is a desktop application for creating professional stamp album pages for display and competition use. It generates high-quality PDF output from a declarative text-based configuration format.

## Features

- **Text-based DSL**: Define albums using a simple, readable command language
- **PDF output**: High-quality PDF generation via WeasyPrint
- **Rich typography**: Full font support including TrueType and OpenType
- **Color control**: RGB and named colors for all elements
- **Stamp shapes**: Rectangle, triangle, diamond, oval, hexagon, octagon, pentagon
- **Decorative borders**: Line borders and image-based decorative borders
- **Headers & footers**: Page numbers, dates, custom text
- **Column layouts**: Single or two-column page layouts
- **Grid patterns**: Quadrille/graph paper support
- **Command groups**: Reusable page templates
- **Conditional compilation**: $DEFINE, $IFDEF, $INCLUDE support

## Installation

```bash
# Clone the repository
git clone https://github.com/jsganesh/stamp-album-pro.git
cd stamp-album-pro

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Generate a PDF from an album file
python -m stamp_album examples/sample.txt -o output.pdf

# Generate with HTML preview
python -m stamp_album examples/sample.txt -p
```

## DSL Syntax

### Basic Album Structure

```
# Document metadata
ALBUM_TITLE ("My Album")
ALBUM_AUTHOR ("Author Name")

# Page setup
ALBUM_PAGES_SIZE (210.0 297.0)          # A4 size in mm
ALBUM_PAGES_MARGINS (20.0 15.0 15.0 15.0)  # left, right, top, bottom
ALBUM_PAGES_BORDER (0.1 0.5 0.1 1.0)    # triple line border
ALBUM_PAGES_SPACING (6.0 6.0)           # horizontal, vertical spacing

# Page title
ALBUM_PAGES_TITLE (TB 16 "Album Title")

# Define pages
PAGE_START

PAGE_TEXT_CENTRE (HS 12 "Section Heading")

ROW_START_FS (HN 8 0.5 6.0)             # font, size, spacing, width
STAMP_ADD (32.0 37.0 "Description" "sg 1" "" "sacc 1")
STAMP_ADD (32.0 37.0 "Description" "sg 2" "" "sacc 2")
```

### Commands

| Command | Description |
|---------|-------------|
| `ALBUM_TITLE` | Set album title |
| `ALBUM_PAGES_SIZE` | Set page dimensions (mm) |
| `ALBUM_PAGES_MARGINS` | Set page margins (mm) |
| `ALBUM_PAGES_BORDER` | Set line border |
| `ALBUM_PAGES_TITLE` | Set page title |
| `PAGE_START` | Begin a new page |
| `PAGE_TEXT` | Add left-aligned text |
| `PAGE_TEXT_CENTRE` | Add centered text |
| `PAGE_TEXT_RIGHT` | Add right-aligned text |
| `PAGE_RULE_H` | Add horizontal rule |
| `ROW_START_FS` | Start fixed-space row |
| `ROW_START_ES` | Start equal-space row |
| `ROW_START_JS` | Start justified-space row |
| `STAMP_ADD` | Add rectangular stamp |
| `STAMP_ADD_TRIANGLE` | Add triangle stamp |
| `STAMP_ADD_DIAMOND` | Add diamond stamp |
| `STAMP_ADD_OVAL` | Add oval stamp |
| `STAMP_HEADING` | Add heading to stamp |
| `COLOUR_*` | Set element colors |

### Font Identifiers

| ID | Font |
|----|------|
| CN, CB, CI, CS | Courier variants |
| TN, TB, TI, TS | Times variants |
| HN, HB, HI, HS | Helvetica variants |

Define custom fonts with `ALBUM_DEFINE_FONT (ID "Font Name")`.

## Development

```bash
# Run tests
pytest

# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

## Architecture

```
src/stamp_album/
├── core/           # Data models and parser
│   ├── models.py   # Album data structures
│   └── parser.py   # DSL parser (Lark)
├── engines/        # Generation engines
│   ├── pdf_generator.py  # WeasyPrint PDF generation
│   ├── font_manager.py   # Font discovery/validation
│   └── layout_engine.py  # Auto-layout algorithms
├── ui/             # PyQt6 interface (coming soon)
└── plugins/        # Extension system (coming soon)
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.
