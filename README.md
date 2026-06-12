# StampAlbum Pro

A modern stamp album typesetter with live preview, a web-based editor, and advanced typography.

## Overview

StampAlbum Pro is a web application for creating professional stamp album pages for display and competition use. It generates high-quality PDF output from a declarative text-based configuration format, with a live preview that updates as you type.

## Features

- **Web-based editor**: CodeMirror-powered DSL editor with dark theme, live preview, and file management
- **Live preview**: Auto-renders HTML preview 400ms after you stop typing
- **File management**: Create, open, save, and delete `.slbum` album files from the browser sidebar
- **PDF export**: One-click PDF generation and download
- **Text-based DSL**: Define albums using a simple, readable command language
- **Rich typography**: Full font support including TrueType and OpenType
- **Color control**: RGB and named colors for all elements
- **Stamp shapes**: Rectangle, triangle, diamond, oval, hexagon, octagon, pentagon
- **Decorative borders**: Line borders and image-based decorative borders
- **Headers & footers**: Page numbers, dates, custom text
- **Column layouts**: Single or two-column page layouts
- **Grid patterns**: Quadrille/graph paper support
- **Conditional compilation**: $DEFINE, $IFDEF, $INCLUDE support
- **REST API**: FastAPI backend with `/render`, `/parse`, `/export`, and `/visual-update` endpoints

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

### macOS Native Dependencies

WeasyPrint requires native libraries for PDF rendering. Install them with Homebrew:

```bash
brew install pango glib gdk-pixbuf libffi harfbuzz fribidi cairo
```

## Quick Start

### Run the app (recommended — works on Windows, macOS, Linux)

```bash
stamp-album
```

This starts the app and **opens it automatically in your default web browser**.
No native GUI toolkit needed — it just works everywhere. Press `Ctrl+C` in the
terminal to stop it.

Alternative commands:

```bash
stamp-album-web        # same as above (explicit)
stamp-album --desktop  # open in a native desktop window (pywebview)
stamp-album --legacy-qt  # old PyQt6 desktop editor (legacy)
```

Environment overrides:

```bash
STAMP_ALBUM_PORT=9000 stamp-album       # use a specific port
STAMP_ALBUM_NO_BROWSER=1 stamp-album    # start server without opening a browser
```

### Run directly from source

```bash
python -m stamp_album            # browser (default)
python -m stamp_album.serve      # browser (explicit)
python -m stamp_album.api        # server only, then open http://localhost:8080
```

### Command Line

```bash
# Generate a PDF from an album file
python -m stamp_album -c examples/sample.txt -o output.pdf

# Generate with HTML preview
python -m stamp_album -c examples/sample.txt -p
```

### Desktop App (macOS)

```bash
# Build the macOS app bundle
./build.sh

# Run the app
open "dist/StampAlbum Pro.app"
```

## Web App Screenshots

The web interface features:

| Component | Description |
|-----------|-------------|
| **Toolbar** | New, Open, Save, Export PDF with keyboard shortcuts |
| **Editor** | CodeMirror with dark theme, line numbers, auto-save |
| **Preview** | Live HTML preview with auto-refresh on edit |
| **Sidebar** | File browser for managing album files |
| **Status bar** | Current file, save status, operation feedback |

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

## API Reference

The FastAPI server provides these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web application |
| `GET` | `/docs` | Interactive API documentation (Swagger UI) |
| `GET` | `/files` | List all `.slbum` files |
| `GET` | `/files/{name}` | Read a file |
| `POST` | `/files/{name}` | Save a file |
| `DELETE` | `/files/{name}` | Delete a file |
| `POST` | `/render` | Render DSL to HTML preview |
| `POST` | `/parse` | Parse DSL to JSON model |
| `POST` | `/visual-update` | Update stamp position (visual builder) |
| `POST` | `/export` | Generate and download PDF |

## Architecture

```
src/stamp_album/
├── api.py              # FastAPI web server
├── __main__.py         # CLI entry point (desktop mode)
├── core/
│   ├── models.py       # Album data structures
│   ├── parser.py       # DSL parser
│   └── serializer.py   # Model-to-DSL round-trip
├── engines/
│   ├── pdf_generator.py    # WeasyPrint PDF generation
│   ├── font_manager.py     # Font discovery/validation
│   └── layout_engine.py    # Auto-layout algorithms
├── ui/                 # PyQt6 desktop interface
│   ├── main_window.py
│   ├── editor.py
│   ├── preview_panel.py
│   └── visual_builder.py
└── web/                # Web application frontend
    ├── index.html
    ├── style.css
    └── app.js
```

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

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.
