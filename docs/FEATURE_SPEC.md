# StampAlbum Pro - Feature Specification

## Overview
A modern web application for creating professional stamp album pages for display and competition use. Generates high-quality PDF output from a declarative configuration format, with a live preview that updates as you type.

---

## Phase 1: Core Features (Complete)

### 1.1 Page Layout System
- **Page sizes**: A4, US Letter, A3, custom dimensions
- **Margins**: Independent left/right/top/bottom, odd/even page mirroring
- **Borders**: Single, double, triple line borders with configurable thickness and spacing
- **Decorative borders**: Image-based border elements (corners, edges)
- **Spacing**: Horizontal and vertical spacing controls
- **Crop marks**: Configurable crop marks for professional printing
- **Quadrilles**: Grid/graph paper patterns

### 1.2 Stamp Display
- **Stamp boxes**: Rectangle, triangle, diamond, oval, hexagon, octagon, pentagon
- **Image support**: PNG, JPG with stretch/center options
- **Image effects**: Grayscale, hide/show
- **Row layouts**: Equal-width, justified, fixed-width, rotated
- **Row alignment**: Top, middle, bottom
- **Stamp headings**: With padding and vertical alignment
- **Stamp footer text**: With alignment options
- **Border styles**: Solid, dashed, dotted, custom for stamp boxes
- **Inner borders**: Offset inner border within stamp box
- **Color control**: Border, inner border, heading, text, background

### 1.3 Typography
- **Font system**: PDF Base-14 fonts + TrueType/OpenType fonts
- **Font definition**: User-defined font identifiers mapped to system fonts
- **Text elements**: Page text, headers, footers, margin text, titles
- **Text alignment**: Left, center, right, justified
- **Text formatting**: Font, size, color per element
- **Paragraph support**: Multi-line paragraphs with leading
- **Horizontal rules**: Configurable thickness and spacing
- **Character spacing**: Custom tracking/kerning
- **Line leading**: Custom line spacing

### 1.4 Page Elements
- **Headers**: Page numbers, dates, custom text with position control
- **Footers**: Page numbers, dates, custom text with position control
- **Margin text**: Vertical text in left/right margins
- **Columns**: Single or two-column layouts
- **Background images**: Full-page background images
- **Vertical spacing**: Custom vspace between elements

### 1.5 Advanced Features
- **Command groups**: Reusable page templates with parameter substitution
- **Conditional compilation**: $DEFINE, $UNDEFINE, $IFDEF, $ELSEIF, $ELSE, $ENDIF
- **File includes**: $INCLUDE for modular album files
- **Page count substitution**: $PAGES$ token for total page count
- **Stamp settings save/restore**: Push/pop stamp configuration state
- **Stamp box size adjust**: Global size adjustment
- **Image aspect ratio**: Fixed or free aspect ratio control
- **Image sizing**: Percentage-based or absolute spacing

### 1.6 Color System
- **RGB color control**: For all album elements
- **Named colors**: Standard HTML color names
- **Per-element colors**: Border, decorative border, footer, header, margin text, title, rules, quadrille, page text, stamp border, stamp inner border, stamp heading, stamp text, stamp background
- **Both spellings**: COLOUR and COLOR accepted

---

## Phase 2: Web Application (Complete)

### 2.1 Web Interface
- **Split view**: Editor and live preview panels
- **Toolbar**: New, Open, Save, Export PDF actions
- **Status bar**: File name, save status, operation feedback
- **Keyboard shortcuts**: Ctrl+S (save), Ctrl+O (open), Ctrl+N (new), Ctrl+E (export)

### 2.2 Text Editor
- **CodeMirror**: Syntax highlighting, line numbers, dark theme
- **Auto-save**: Debounced file saving
- **Undo/Redo**: Full edit history
- **File change detection**: Modified indicator

### 2.3 Live Preview
- **Auto-refresh**: Debounced preview update (400ms after last edit)
- **HTML rendering**: Accurate preview matching PDF output
- **Error display**: Parse errors shown inline in preview panel
- **Toggle**: Show/hide preview panel

### 2.4 File Management
- **File browser**: Sidebar listing all `.slbum` files
- **Upload**: Import `.slbum` files from disk
- **Save**: Persist files to user directory (`~/StampAlbum/`)
- **Delete**: Remove files with confirmation
- **Auto-detect**: Files saved from desktop app are visible in web app

### 2.5 PDF Export
- **One-click export**: Generate and download PDF
- **Browser download**: PDF opens in browser or downloads
- **Error handling**: Generation errors shown as toast notifications

### 2.6 REST API
- **FastAPI server**: `/render`, `/parse`, `/export`, `/visual-update` endpoints
- **Swagger UI**: Interactive API documentation at `/docs`
- **File endpoints**: `/files` for CRUD operations
- **CORS-ready**: Configured for frontend integration

---

## Phase 3: Desktop Application (Complete)

### 3.1 PyQt6 Desktop App
- **Main window**: Split editor + preview layout
- **Menu system**: File, Edit, View, Tools, Help menus
- **Toolbar**: Quick access to common actions
- **Status bar**: File path, cursor position, operation feedback

### 3.2 Desktop Editor
- **Syntax highlighting**: DSL command highlighting
- **Line numbers**: With current line tracking
- **Find/Replace**: Search text in editor
- **Undo/Redo**: Full edit history

### 3.3 Desktop Preview
- **WeasyPrint rendering**: Accurate page preview as images
- **Page navigation**: Multi-page album support
- **Zoom controls**: 50% to 200% zoom levels
- **Toggle**: Show/hide preview panel

### 3.4 Visual Builder
- **Canvas**: Visual representation of page layout
- **Property panel**: Edit stamp properties
- **Auto-arrange**: Row-first, grid, packing, balanced layouts
- **Dialog**: Visual builder modal for page editing

### 3.5 macOS App Bundle
- **PyInstaller**: Self-contained `.app` bundle
- **Bundled dylibs**: WeasyPrint native libraries included
- **No brew required**: Works without Homebrew on target machines
- **Build script**: `./build.sh` for reproducible builds

---

## Phase 4: Serializer & Round-Trip (Complete)

### 4.1 DSL Serializer
- **Model-to-DSL**: Convert Album models back to DSL text
- **All commands**: Supports all DSL commands and variants
- **String escaping**: Proper quote and backslash handling
- **Stamp shapes**: Rectangle, triangle, diamond, oval, etc.
- **Text alignment**: Correct PAGE_TEXT variants

### 4.2 Visual Builder Bridge
- **`/visual-update` API**: Update stamp position via API
- **Round-trip**: Parse DSL → modify model → serialize back to DSL
- **Editor sync**: Visual changes reflected in text editor

---

## Technical Requirements

### Input Format
- Text-based DSL with custom command syntax
- Comments with # character
- Line continuation with backslash
- Parameter groups in parentheses
- String literals in quotes

### Output Format
- PDF generation via WeasyPrint
- Measurements in millimeters
- Font sizes in points
- HTML preview rendering

### Platform Support
- **Web**: Any modern browser (Chrome, Firefox, Safari, Edge)
- **macOS**: ARM64 (Apple Silicon), Intel
- **Linux**: 64-bit (web app)
- **Windows**: 64-bit (web app)

---

## Future Enhancements

### Visual Builder (Web)
- Drag-and-drop stamp placement on preview
- React-based visual canvas overlay
- Real-time DSL sync via WebSocket

### Advanced Typography
- Inline text formatting (bold, italic, etc.)
- Drop caps
- Text shadows and outlines
- Gradient text fills
- Variable font support

### Smart Features
- Auto-layout engine
- CSV/Excel import
- Font pairing suggestions
- Color palette generation

### Export Options
- High-res PNG
- SVG
- HTML/CSS web gallery
- EPUB

### Collaboration
- Multi-user editing
- Version history
- Cloud sync
