# StampAlbum Pro - Feature Specification

## Overview
A modern desktop application for creating professional stamp album pages for display and competition use. Generates high-quality PDF output from a declarative configuration format.

---

## Phase 1: Core Features

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

## Phase 2: UI Features

### 2.1 Main Interface
- **Split view**: Editor and status log
- **Toolbar**: File operations, generate, view, font, configure, wizard, help
- **Status bar**: Editor position, mode, encoding
- **Recent files**: Quick access to recently opened albums

### 2.2 Text Editor
- **Syntax highlighting**: Commands, strings, comments, parameters
- **Line numbers**: With current line highlighting
- **Bracket matching**: Visual bracket pair highlighting
- **Find/Replace**: Find, find next, find and replace
- **Undo/Redo**: Full edit history
- **File change detection**: Detect external modifications
- **Customizable shortcuts**: User-defined keyboard shortcuts
- **Print support**: Print source files

### 2.3 Configuration
- **General settings**: Work directory, recent files count
- **Editor settings**: Font, size, syntax colors, dark mode
- **Key map**: Custom keyboard shortcuts
- **Advanced settings**: Unicode mode, system fonts inclusion

### 2.4 Font Management
- **Font scanning**: System and bundled font directories
- **Font validation**: TTF/TTC compatibility checking
- **Font browser**: List available fonts with details
- **Bad font reporting**: List incompatible font files

### 2.5 Wizard
- **New album creation**: Step-by-step guided setup
- **Page configuration**: Size, margins, borders
- **Template generation**: Basic album structure with examples

### 2.6 Help System
- **Qt Help Engine**: Contents, index, search
- **Navigation**: Home, back, forward
- **Print support**: Print help topics

### 2.7 Additional Features
- **Tip of the day**: Startup tips
- **Dark mode**: Configurable dark theme
- **Console mode**: Command-line batch processing
- **Cross-platform**: macOS, Linux, Windows

---

## Technical Requirements

### Input Format
- Text-based DSL with custom command syntax
- Comments with # character
- Line continuation with backslash
- Parameter groups in parentheses
- String literals in quotes

### Output Format
- PDF generation via LibHaru
- Measurements in millimeters
- Font sizes in points
- 72 DPI rendering

### Platform Support
- **macOS**: ARM64 (Apple Silicon), Intel
- **Linux**: 64-bit
- **Windows**: 32-bit, 64-bit

---

## Future Enhancements (Not in Original)

### Live Preview
- Real-time PDF preview while editing
- Auto-refresh on file save

### Multi-Document Interface
- Tabbed editing for multiple albums
- Drag-and-drop tab reordering

### Visual Builder
- Drag-and-drop stamp placement
- Visual row/column configuration
- Template gallery with previews

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
