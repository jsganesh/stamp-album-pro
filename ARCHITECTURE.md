# StampAlbum Pro — Architecture Map

> **Status:** written for the v2 PyMuPDF pipeline. The newer ReportLab, Pillow and SVG engines in `src/stamp_album/engines/` (`pdf.py`, `raster.py`, `svg_export.py`) and the shared `borders.py` and `layout.py` are not described here, and the test counts and file statistics are out of date. Check the code before relying on the rendering sections.

## 1. Overview

**What it is:** A web-based stamp album designer with InDesign-like free-form page layout. Stamp collectors design and print album pages. Visual canvas interaction is the primary mode; a DSL (Domain Specific Language) is an advanced toggle.

**Tech stack:**
- **Backend:** Python 3.10+ / FastAPI (uvicorn)
- **Frontend:** Vanilla JS (no framework), SVG + contentEditable, single HTML file
- **PDF generation:** PyMuPDF direct drawing (replaced WeasyPrint in v2)
- **Font system:** fonttools for discovery, PyMuPDF for embedding
- **Desktop (optional):** pywebview or legacy PyQt6
- **Tests:** pytest (~209 tests)

**Project stats (source):**
| Layer | Files | Lines |
|-------|-------|-------|
| Backend Python | ~15 | ~7,000 |
| Frontend JS/CSS/HTML | 14 | ~4,500 |
| Tests | 18 | ~2,500 |
| Templates | 1 | ~1,283 |
| Total | ~48 | ~19,600 |

---

## 2. Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                       │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  index.html (SPA shell, 309 lines)                   │ │
│  │                                                      │ │
│  │  window.StampAlbum (S) — JS namespace                │ │
│  │  ┌──────────┬──────────┬──────────┬──────────────┐  │ │
│  │  │ app.js   │ init.js  │ render.js│ undo.js       │  │ │
│  │  │ (state,  │ (event   │ (canvas  │ (undo/redo    │  │ │
│  │  │ utils)   │ wiring)  │ render)  │ stacks)       │  │ │
│  │  ├──────────┼──────────┼──────────┼──────────────┤  │ │
│  │  │ dsl.js   │ files.js │ export.js│ borders.js    │  │ │
│  │  │ (DSL     │ (file    │ (preview,│ (SVG border    │  │ │
│  │  │ roundtrip)│ CRUD)   │ export)  │ ornaments)    │  │ │
│  │  ├──────────┼──────────┼──────────┼──────────────┤  │ │
│  │  │ wizard.js│ events.js│ canvas.js│ tutorial.js   │  │ │
│  │  │ (setup   │ (dead —  │ (dead —  │ (onboarding)  │  │ │
│  │  │ wizard)  │ see §5.3)│ see §5.3)│               │  │ │
│  │  └──────────┴──────────┴──────────┴──────────────┘  │ │
│  │                    style.css (382 lines)              │ │
│  └──────────────┬──────────────────────────────────────┘ │
│                 │  HTTP / WebSocket                       │
├─────────────────┼────────────────────────────────────────┤
│                 ▼                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  FastAPI Server  (api.py, 1,092 lines)               │ │
│  │                                                      │ │
│  │  Static Routes     Files/Images    Render/Export     │ │
│  │  ─────────────     ────────────    ─────────────     │ │
│  │  GET  /            GET/POST/DELETE  POST /render     │ │
│  │  GET  /app.js      /files/{name}   POST /export      │ │
│  │  GET  /style.css   GET/POST/DELETE  POST /parse       │ │
│  │  GET  /{static}    /images         POST /validate    │ │
│  │                                                      │ │
│  │  Canvas State       Collection CRUD   Auth/Sharing   │ │
│  │  ────────────       ──────────────   ────────────    │ │
│  │  POST /render-from  GET/POST/PUT     POST /auth/*    │ │
│  │  -state             /api/stamps      POST /api/share │ │
│  │  POST /export-from  POST /api/stamps WS /ws/preview  │ │
│  │  -state             /import(CSV,XLSX)                 │ │
│  │                     GET /auto-layout                  │ │
│  └──────────────┬──────────────────────────────────────┘ │
│                 ▼                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Core Model Layer                                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │ │
│  │  │ models.py    │  │ parser.py    │  │serializer │  │ │
│  │  │ (dataclasses,│◄─│ (DSL → Album)│  │.py        │  │ │
│  │  │ enums)       │  │ tokenize /   │  │(Album →   │  │ │
│  │  │              │  │ unquote      │  │ DSL)      │  │ │
│  │  └──────────────┘  └──────────────┘  └───────────┘  │ │
│  └──────────────┬──────────────────────────────────────┘ │
│                 ▼                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Engines (Rendering & Layout)                        │ │
│  │  ┌──────────────────┐  ┌─────────────────────────┐  │ │
│  │  │ pdf_generator.py │  │ layout_engine.py        │  │ │
│  │  │ ├─ PDFGenerator  │  │ ├─ LayoutEngine         │  │ │
│  │  │ │  (PDF drawing) │  │ │  (5 layout strategies)│  │ │
│  │  │ ├─ HTMLRenderer  │  │ └─ LayoutSuggestion     │  │ │
│  │  │ │  (HTML preview)│  └─────────────────────────┘  │ │
│  │  │ └─ helpers       │  ┌─────────────────────────┐  │ │
│  │  │   (borders,      │  │ font_manager.py         │  │ │
│  │  │    ornaments,    │  │ ├─ FontManager           │  │ │
│  │  │    multiline)    │  │ │  (discovery, caching) │  │ │
│  │  └──────────────────┘  │ └─ FontInfo dataclass    │  │ │
│  │                        └─────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Supporting Services                                 │ │
│  │  ┌──────────────┐ ┌────────────────┐ ┌───────────┐  │ │
│  │  │ cloud_sync   │ │ version_history│ │ collection│  │ │
│  │  │ .py          │ │ .py            │ │ .py       │  │ │
│  │  │ (auth,       │ │ (snapshot-based│ │ (CRUD +   │  │ │
│  │  │ sharing)     │ │ versioning)    │ │ CSV/XLSX) │  │ │
│  │  └──────────────┘ └────────────────┘ └───────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

---

## 3. Entry Points

### `stamp-album` (CLI, `__main__.py`)
```
stamp-album
  ├── (no args)     → serve_main() → uvicorn on :8080 + open browser
  ├── --browser     → serve_main() (explicit browser mode)
  ├── --desktop     → pywebview window
  ├── --legacy-qt   → PyQt6 MainWindow
  ├── -c file.txt   → CLI: parse → PDFGenerator → PDF file
  └── --dev         → STAMP_ALBUM_RELOAD=1 + serve_main()
```

### `serve.py` (browser mode)
```
main()
  1. Pick port (env STAMP_ALBUM_PORT or 8080)
  2. Kill existing process on that port
  3. Launch _wait_for_server() thread (polls until 200)
  4. uvicorn.run(api.app, reload=RELOAD, watch_dirs=["web/"])
```

### `api.py` (FastAPI application)
- Single `FastAPI()` instance with security headers middleware
- Static file serving for `/web/*` (index.html, app.js, style.css, etc.)
- All routes defined with Pydantic request/response models

---

## 4. Data Flow (Two Parallel Pipelines)

### Pipeline A: DSL-based (legacy / advanced mode)

```
User writes DSL text in editor
        │
        ▼
POST /render  ──→  AlbumParser.parse()  ──→  Album model
POST /export         tokenize()                │
                     unquote()                 │
                     command dispatch          ├── HTMLRenderer.render()
                                               │     → HTML preview
                                               │
                                               └── PDFGenerator.generate()
                                                     → PDF bytes
                                                     → PNG/SVG (via fitz.open())
        │
        ▼
User sees preview in iframe or downloads PDF
```

**DSL format** (see `parser.py` line 1-1009 for full command list):
```
ALBUM_TITLE ("My Album")
ALBUM_PAGES_SIZE (210.0 297.0)
PAGE_START
PAGE_TEXT_CENTRE ("HS" 14 "Section Title")
ROW_START_FS ("HN" 8 0.5 6.0)
STAMP_ADD (32.0 37.0 "Description" "sg 1")
```

### Pipeline B: Canvas-based (default / visual mode)

```
User drags stamps onto canvas in browser
        │
        ▼
S.E (in-memory element array in window.StampAlbum)
        │
        ├── buildDSL() ──→ DSL text (for save, .slbum files)
        │
        ├── POST /render-from-state  ──→  _canvas_state_to_album()
        │       CanvasStateRequest              │
        │         {elements[], pages,            ├── HTMLRenderer.render()
        │          page_width, page_height,       │     → HTML preview
        │          scale, ...}                    │
        │                                        └── PDFGenerator.generate()
        │                                              → PDF bytes
        │
        └── POST /export-from-state  ──→  same path → PDF/PNG/SVG/HTML
```

**Canvas element format** (see `api.py` `CanvasElementState`):
```json
{
  "id": "el42",
  "t": "stamp",          // "stamp", "text", "image", "freehand"
  "s": "rectangle",      // shape
  "x": 100, "y": 200,    // position (px)
  "w": 80, "h": 100,     // size (px)
  "lbl": "SG 123",       // text / description
  "font": "HN", "fs": 12,
  "align": "left",
  "bdr": "solid", "bdrC": "#666", "bdrW": 1,
  "fill": "#fff", "fillA": 100,
  "img": "",             // image filename
  "hdg": "", "cat": "", "denom": "", "cond": "", "perf": ""
}
```

---

## 5. Core Data Model (`models.py`, 646 lines)

### Enums
| Enum | Values | Used In |
|------|--------|---------|
| `PageSize` | A3, A4, A5, LETTER, LEGAL, CUSTOM | Page setup |
| `TextAlignment` | LEFT, CENTER, RIGHT, JUSTIFY, TOP, BOTTOM | FormattedText, Page |
| `RowStyle` | EQUAL_SPACE, FIXED_SPACE, JUSTIFIED_SPACE, ROTATED | Row |
| `RowAlignment` | TOP, MIDDLE, BOTTOM | Row |
| `StampShape` | RECTANGLE, TRIANGLE, DIAMOND, OVAL, HEXAGON, OCTAGON, PENTAGON (+inv/right variants) | Stamp |
| `BorderStyle` | SOLID, DASHED, DOTTED, BLANK | StampBorderSettings |
| `Position` | LEFT, RIGHT, CENTER, LEFT_RIGHT, RIGHT_LEFT, NONE | MarginTextItem |
| `ColumnMode` | NONE, ONE, TWO, THREE | Album / Page |

### Primary Dataclasses (hierarchy)

```
Album
  ├── title: str
  ├── author: str
  ├── source_path: Optional[str]
  ├── page_setup: PageSetup
  │     ├── width, height: float (mm)
  │     ├── margins (left, right, top, bottom, with even-page mirroring)
  │     ├── has_border: bool
  │     ├── border_outer, border_inner1, border_inner2, border_spacing: float
  │     ├── border_style: str ("solid", "double", "classic", "victorian", etc.)
  │     ├── stamp_box_adjust: float
  │     ├── heading_padding: float
  │     ├── text_char_spacing, text_line_leading: float
  │     ├── stamp_image_settings: StampImageSettings
  │     ├── stamp_border_settings: StampBorderSettings
  │     ├── text_shadow: TextShadow (optional)
  │     ├── text_outline: TextOutline (optional)
  │     ├── text_gradient: GradientFill (optional)
  │     ├── text_weight, text_style: str
  │     ├── crop_marks: CropMarkSettings (optional)
  │     └── title, footer, header: FormattedText (optional)
  │
  ├── fonts: list[FontDefinition]
  ├── color_*: Optional[Color] (15 fields: border, decorative_border, footer, header,
  │     margin_text, title, h_rule, quadrille_grid/border/major, page_text,
  │     stamp_border/inner_border/heading/text/background)
  ├── margin_texts: list[MarginTextItem]
  ├── command_groups: dict[str, CommandGroup]
  ├── defines: set[str]
  │
  └── pages: list[Page]
        ├── title, header, footer: Optional[FormattedText]
        ├── text_elements: list[FormattedText]
        ├── paragraphs: list[Paragraph]
        ├── rows: list[Row]
        │     └── stamps: list[Stamp]
        │           ├── width, height: float
        │           ├── description: str
        │           ├── catalog_refs: list[str] (up to 3)
        │           ├── shape: StampShape
        │           ├── image_path: Optional[str]
        │           ├── heading: Optional[StampHeading]
        │           ├── footer_text: str
        │           ├── is_text_element: bool (canvas text)
        │           ├── font_id, font_size: str, float
        │           └── abs_x, abs_y: float (for absolute positioning)
        │
        ├── absolute_stamps: list[Stamp] (canvas drag-and-drop)
        ├── h_rules: list[tuple]
        ├── quadrille: Optional[QuadrilleSettings]
        ├── background_image: Optional[str]
        ├── column_mode: ColumnMode
        ├── column_gap: float
        ├── vspace: float
        ├── absolute_vpos: float
        ├── boxes: list[tuple]
        └── content_flow: list[tuple(str, Any)]
```

### Supporting Types
- **`FormattedText`** — font_id, size, content, alignment, color, vspace, shadow, outline, gradient, drop_cap_lines, etc.
- **`StampHeading`** — font_id, size, text, padding, vertical_alignment
- **`StampImageSettings`** — hspace, vspace, stretch, aspect_ratio, grayscale, hidden
- **`StampBorderSettings`** — style, corners, edges, inner border styles
- **`Color`** — r,g,b (0-1). Methods: `from_name`, `from_rgb`, `from_hex`, `to_hex`, `to_tuple`. Hashable.
- **`TextShadow`** / **`TextOutline`** / **`GradientFill`** / **`GradientStop`** — typography effects

---

## 6. Backend Services

### 6a. `api.py` — Route Map (1,092 lines)

| Method | Path | Purpose | Key Logic |
|--------|------|---------|-----------|
| GET | `/` | Serve SPA | Returns `index.html` with cache busting |
| GET | `/files` | List albums | Scans `~/StampAlbum/*.slbum` |
| POST | `/files/{name}` | Save album | Writes DSL text |
| GET | `/files/{name}` | Open album | Returns DSL text |
| DELETE | `/files/{name}` | Delete album | Removes file |
| GET | `/images` | List images | Scans `~/StampAlbum/images/*` |
| POST | `/images` | Upload image | Multipart, validates ext, saves |
| POST | `/render` | DSL → HTML | Parser → HTMLRenderer |
| POST | `/parse` | DSL → JSON model | Parser → Album → JSON |
| POST | `/validate` | DSL validation | Parser + AlbumValidator |
| POST | `/export` | DSL → file | Parser → PDFGenerator (PDF/PNG/SVG) |
| POST | `/render-from-state` | Canvas → HTML | `_canvas_state_to_album()` → HTMLRenderer |
| POST | `/export-from-state` | Canvas → file | `_canvas_state_to_album()` → PDFGenerator |
| POST | `/visual-update` | Recalculate DSL | Parser → serializer.update_stamp_position() |
| POST | `/api/auto-layout` | Auto-arrange | LayoutEngine with strategy selection |
| WS | `/ws/preview` | Real-time preview | WebSocket: render/ping/validate messages |
| GET | `/api/templates` | List templates | Returns TEMPLATES metadata list |
| GET | `/api/templates/{id}` | Get template DSL | Returns full template DSL content |
| POST | `/api/stamps/import` | CSV import | Parses CSV → collection DB |
| POST | `/api/stamps/import-excel` | XLSX import | openpyxl → collection DB |
| CRUD | `/api/stamps` | Collection mgmt | JSON file-backed stamp database |
| CRUD | `/api/version/*` | Version history | Snapshot-based, max 50 per file |
| POST | `/api/auth/*` | Auth | PBKDF2, session tokens |
| POST | `/api/share` | File sharing | Owner → user permission records |

### 6b. `parser.py` — DSL to Album (1,009 lines)

**Entry:** `AlbumParser.parse(source_text) → Album`

**Token flow:**
1. Join continuation lines (backslash-newline)
2. Strip comments (`#`) with hex-color detection
3. Per line: `tokenize()` → `parse_params()` → command dispatch on `tokens[0]`

**Key helper functions:**
- `tokenize(text)` — token parser with quoted string handling
- `parse_params(tokens)` — extracts parenthesized parameters
- `unquote(s)` — strips quotes, handles `\n` and `\\` escape sequences
- `parse_color(val)` — parses hex/rgb/named colors

**Command dispatch handles ~60+ commands** across categories:
- Conditional: `$DEFINE`, `$IFDEF`, `$ELSE`, `$ENDIF`
- Metadata: `ALBUM_TITLE`, `ALBUM_AUTHOR`
- Page setup: size, margins, border, spacing, fonts, colors
- Page content: text, rows, stamps (shapes, images, headings), boxes, rules
- Typography: shadow, outline, gradient, weight, style
- Compatibility (legacy): various aliases for renamed commands

### 6c. `serializer.py` — Album to DSL (200 lines)

**Entry:** `AlbumSerializer.to_dsl(album) → str`

Serializes Album → DSL text, covering: title, author, page setup, fonts, colors, each page's text elements, rows, stamps with shapes/headings, absolute stamps.

Also provides `update_stamp_position()` for the visual builder (parse → mutate → serialize round-trip).

### 6d. `pdf_generator.py` — Rendering Engine (1,024 lines)

Two classes + many helper functions.

**`HTMLRenderer` (line 31–366):** Full-featured HTML preview with SVG shapes, corner ornaments, edge patterns, inline formatting (bold, italic, code, superscript, subscript, strikethrough), typography effects (drop caps, text shadow, outline, gradient fill), column layout support.

**`PDFGenerator` (line 932–1024):** Direct PyMuPDF drawing engine.

Key methods:
- `generate(album, output_path)` — creates PDF page by page
- `generate_to_bytes(album)` → bytes (for in-memory/PNG/SVG)
- `get_html_preview(album)` → str (simple HTML preview)

Drawing architecture:
```
generate()
  │
  ├── doc = fitz.open()
  │
  └── for each Page in album.pages:
        ├── doc.new_page(width=mm→pt, height=mm→pt)
        ├── _draw_page_border(page, album)
        │     ├── 1-3 concentric rectangle borders
        │     ├── _draw_corner_ornaments() (classic/victorian/etc.)
        │     └── _draw_edge_patterns() (greek_key/rope)
        │
        └── for each stamp in page.absolute_stamps:
              ├── if is_text_element → _draw_text_element()
              │     └── _draw_multiline_text()  ← splits on \n
              │
              └── _draw_stamp()
                    ├── shape drawing (rect/oval/polygon via PyMuPDF)
                    ├── image embedding (page.insert_image)
                    └── _draw_multiline_text(center=True)  ← splits on \n
```

Font resolution: `_resolve_font(font_id)` → checks built-in map (14 PDF standard fonts) → walks system font directories → falls back to Helvetica.

Page border styles: `solid`, `double`, `dashed`, `dotted`, `classic`, `victorian`, `artdeco`, `greek_key`, `rope`, `laurel`, `gothic`, `filigree`.

### 6e. `layout_engine.py` — Auto-Layout (563 lines)

**`LayoutEngine`** with 5 strategies for automatic stamp arrangement:
- `ROW_FIRST` — fill rows LTR, wrap
- `COLUMN_FIRST` — fill columns TTB, wrap
- `GRID` — uniform grid by average stamp size
- `PACKING` — sort by height descending, then row-first
- `BALANCED` — target row widths based on estimate

Scoring: 0.4 × space utilization + 0.6 × row uniformity (coefficient of variation).

### 6f. `font_manager.py` — Font System (324 lines)

**`FontManager`** discovers system and bundled fonts:
- Platform-specific paths: macOS (`/Library/Fonts`, `~/Library/Fonts`, `/System/Library/Fonts`), Linux, Windows
- Parses TTF/TTC/OTF via `fonttools`
- Caches valid/invalid font files
- `find_font(name)` — case-insensitive linear search
- `validate_font(file_path)` — checks font file integrity

---

## 7. Frontend Architecture

### 7a. Module Organization

All JS files are IIFEs that attach to `window.StampAlbum` (aliased as `S`). Load order is critical:

```
index.html script loading order:
  1. CodeMirror CDN (external)
  2. app.js       —  S defined, state vars, utility functions
  3. render.js    —  S.render(), S.add(), S.select(), S.getShapePath()
  4. undo.js      —  S.pushUndo(), S.undo(), S.redo()
  5. dsl.js       —  S.buildDSL(), S.parseDSL()
  6. files.js     —  S.saveFile(), S.loadFileList(), S.uploadImageFile()
  7. tutorial.js  —  S.initTutorial(), S._wireTutorialEvents()
  8. events.js    —  S.init()  ★ OVERWRITTEN by init.js
  9. borders.js   —  S.renderPageBorder(), S.getBorderStyles()
  10. init.js     —  S.init()  ← THE REAL INITIALIZER (overwrites line 8)
```

### 7b. `window.StampAlbum` Shared State

**State variables (closure-private in app.js, exposed via `Object.defineProperties`):**

| Variable | Type | Description |
|----------|------|-------------|
| `S.E` | Array | Current page elements |
| `S.sel` | String/null | Currently selected element ID |
| `S.nid` | Number | Auto-incrementing ID counter |
| `S._sc` | Number | Pixel scale factor (2.5 px/mm) |
| `S._sn` | Number | Snap grid size in mm (0 = off) |
| `S._pw`, `S._ph` | Number | Page dimensions in pixels |
| `S._pages` | Array of Arrays | All pages (`S._pages[i]` = elements on page i) |
| `S._currentPage` | Number | Active page index |
| `S._colMode` | Number | Column mode (1-3) |
| `S._colGap` | Number | Column gap in mm |
| `S._pageBorder` | String | Page border style ("solid", "double", "classic", etc.) |
| `S._pageBorderC` | String | Border color hex |
| `S._dirty` | Boolean | Unsaved changes flag |
| `S._undoStack` | Array | Undo snapshots (max 50, JSON-stringified `S.E`) |
| `S._redoStack` | Array | Redo snapshots |
| `S._currentFile` | String/null | Current filename |
| `S._snapTarget` | Object | Alignment guide snap target (set by drawAlignmentGuides) |

### 7c. Key Functions by File

| File | Functions on `S` | Purpose |
|------|------------------|---------|
| **app.js** | `$(id)`, `mm(px)`, `px(mm)`, `showToast()`, `fontCSS()` | Utilities |
| | `switchPage()`, `addPage()`, `deletePage()`, `renderPageDots()` | Page management |
| | `saveDraft()` / `loadDraft()` / `clearDraft()` | localStorage auto-save (500ms debounce) |
| | `buildCanvasState()`, `refreshPreview()`, `exportPDF()` | Render/export API calls |
| | `alignSelected()`, `distributeSelected()`, `matchSize()` | Alignment toolbox |
| **render.js** | `render()` | Main canvas render (clears + rebuilds all `.cel` divs) |
| | `add(p)` | Create new element, push to `S.E`, render |
| | `select(id)` | Fill properties panel, handle philatelic fields |
| | `drawAlignmentGuides(el)` | Guide lines + snap targets during drag |
| | `getShapePath(shape, w, h)` | SVG path data for shapes |
| | `populateFonts()`, `updateStatusBar()` | UI population |
| **dsl.js** | `buildDSL()` | S.E → DSL text (all pages) |
| | `parseDSL(dsl)` | DSL text → S.E, S._pages, S._currentPage |
| **undo.js** | `pushUndo()`, `undo()`, `redo()` | Stack-based undo/redo |
| | `loadElements(arr)`, `loadElementsNoPush(arr)` | Restore element state |
| **files.js** | `saveFile()`, `loadFileList()` | File CRUD via HTTP |
| | `uploadImageFile()`, `loadImageList()` | Image management via HTTP |
| **borders.js** | `renderPageBorder(style)` | SVG decorative border overlay |
| | `cornerOrnament(style, corner)` | Corner ornament SVG paths |
| | `edgePattern(style, edge, w, h)` | Edge pattern SVG paths |
| **wizard.js** | `applyWizard()` | Build DSL from wizard form, call parseDSL |
| **init.js** | `init()` | Wire ALL DOM events, keyboard shortcuts, touch support |

### 7d. UI Layout (index.html)

```
+──────────────────────────────────────────────────────────+
| Toolbar (#tb) — New/Open/Save | Dup/Grid | Undo/Redo/Del | Align | Wizard/Preview/Export/DSL | Large Text | Reset | Help |
+──────┬─────────────────────────────────────┬──────────────+
|      |                                     |              |
| Sidebar| Canvas (#ca)                      | Right Panel  |
| (#sb) |  +── Page size / Grid / Border ──+ | (#rp)        |
| 240px |  |                                | | 300px        |
|       |  |  +─────────────────────────+  | | Position     |
| Shapes |  |  │   .page (centered)     │  | | (x,y,w,h)   |
| Text   |  |  │   SVG #grid-overlay    │  | | Border       |
| Images |  |  │   .cel elements        │  | | (style/color/|
| Files  |  |  │   .guide-lines         │  | |  width)     |
| Import |  |  │   border ornament SVG  │  | | Fill         |
|        |  |  +─────────────────────────+  | | (color/alpha)|
|        |  |                                | | Text         |
|        |  |  #page-wrap (scrollable)       | | (label/font/ |
|        |  |                                | |  size)       |
|        |  |  #zoom-controls                | | Philatelic  |
|        |  |                                | | (heading/cat/|
|        |  +────────────────────────────────+ | denom/cond/ |
|        |                                     |  perf)      |
+────────+─────────────────────────────────────+──────────────+
| Status bar (#status-bar) — Page N of M | N elements | Selection | Dirty | Zoom |
+──────────────────────────────────────────────────────────────────────────────+

Slide-up panels (toggle with .open class):
  ┌─────────────────────────────────────────────────────────────┐
  │ Wizard Panel (#wizard-panel)                                 │
  │ Quick Setup: Title * Author * Page Size * Border * Template │
  └─────────────────────────────────────────────────────────────┘
  ┌─────────────────────────────────────────────────────────────┐
  │ DSL Panel (#dsl-panel) — CodeMirror 6 editor                 │
  │ [Apply] [Close]                                              │
  └─────────────────────────────────────────────────────────────┘

Overlays:
  ┌─────────────────────────────────────────────────────────────┐
  │ Preview (#preview-overlay) — iframe fullscreen with close   │
  │ Help (#help-overlay)    — keyboard shortcuts reference      │
  │ Tutorial (#tutorial-overlay) — first-run step-through       │
  │ Template Gallery (#template-gallery-panel) — card grid       │
  └─────────────────────────────────────────────────────────────┘
```

### 7e. Canvas Element Rendering (render.js)

Each element in `S.E` becomes a `.cel` div with:
- `position: absolute` with `left/top/width/height` in pixels
- SVG shape overlay for non-rectangle stamps (oval, diamond, triangle, etc.)
- `.stamp-mount` for rectangular stamps (inset box-shadow border + inner content area)
- `.elbl` contentEditable `<span>` with `white-space: pre-wrap` for text/labels
- 8 resize handles (`.rh.nw`, `.rh.ne`, `.rh.se`, `.rh.sw`, `.rh.n`, `.rh.s`, `.rh.e`, `.rh.w`)
- Selected element has `.selected` class and dimension label overlay
- Drag behavior: mousedown on element → select + start tracking mousemove → draw alignment guides → snap to guides → mouseup → commit position + pushUndo

### 7f. Canvas Border System (borders.js + style.css)

`renderPageBorder(style)` creates an SVG `<svg id="page-border">` overlay:
- `solid` — single `<rect>` with border color
- `double` — two nested `<rect>`s with spacing
- `dashed` / `dotted` — with `stroke-dasharray`
- Ornamental (`classic`, `victorian`, `artdeco`, `laurel`, `gothic`, `filigree`) — double rect + 4 corner ornaments positioned at margins with flip transforms
- Edge patterns (`greek_key`, `rope`) — 4 edge SVG `<g>` groups with transforms

Corner ornaments use `scale(-1,1)` / `scale(1,-1)` transforms for each corner.

---

## 8. Data Flow: Save/Load Cycle

### Save Flow (Canvas → DSL → File)
```
User clicks Save
  │
  ├── buildDSL()
  │     ├── Snapshot all pages (S._pages + current S.E)
  │     ├── Emit ALBUM_PAGES_BORDER, ALBUM_PAGES_SIZE, etc.
  │     └── For each page:
  │           ├── PAGE_START
  │           ├── For each element:
  │           │     ├── stamp   → STAMP_ADD_AT(x y w h "lbl" "shape" "bdr" "fill")
  │           │     ├── text    → PAGE_TEXT_AT(x y w h "font" size "text" "align")
  │           │     ├── image   → STAMP_ADD_IMG(x y w h "img" "lbl")
  │           │     └── freehand→ STAMP_ADD_AT(x y w h "lbl" "freehand" "bdr" "fill")
  │           └── PAGE_COLUMN_STOP (if column mode)
  │
  └── POST /files/{name} (DSL text saved to ~/StampAlbum/)


### Load Flow (File → DSL → Canvas)

User opens file
  │
  ├── GET /files/{name} → returns DSL text
  │
  └── parseDSL(dsl)
        ├── S.E = [], S._pages = [[]], S._currentPage = 0
        ├── Parse line by line:
        │     ├── ALBUM_PAGES_SIZE → S._pw, S._ph
        │     ├── ALBUM_PAGES_BORDER → S._pageBorder
        │     ├── COLOUR_ALBUM_BORDER → S._pageBorderC
        │     ├── PAGE_START → save current S.E to S._pages, create new page
        │     ├── PAGE_COLUMN_START → S._colMode, S._colGap
        │     ├── STAMP_ADD_AT → create stamp element with x/y/w/h in px
        │     ├── PAGE_TEXT_AT → create text element with font/size/align
        │     ├── STAMP_ADD_IMG → create image element
        │     └── PAGE_TEXT/... → row-based text (fallback)
        │
        ├── S.E = S._pages[S._currentPage]
        └── render() + updateProps() + updateGrid() + updateTitle()
```

### Render/Export Flow (Canvas → Album → PDF/HTML)

```
User clicks Preview / Export
  │
  └── POST /render-from-state or /export-from-state
        │
        └── _canvas_state_to_album(request)
              ├── Computes mm = px / SCALE (2.5)
              ├── Sets page dimensions, border style/color
              ├── Maps canvas elements to Stamp objects with shape, position, font
              ├── Handles heading/catalog/denom/condition/perf metadata
              └── Returns Album model
        │
        ├──→ HTMLRenderer.render(Album) → HTML string → preview overlay
        │
        └──→ PDFGenerator.generate(Album) → PDF file → download
              Or: generate_to_bytes() → fitz.open() → get_pixmap() (PNG)
                                                   → get_svg_image() (SVG)
```

---

## 9. Test Architecture (18 files, ~209 tests)

| File | Tests | What it covers |
|------|-------|----------------|
| `test_parser.py` | ~26 | All DSL commands: metadata, page setup, fonts, colors, rows, stamps, shapes, conditionals |
| `test_models.py` | ~18 | Dataclass defaults, Color methods, Stamp, Row, Page, Album, PageSetup construction |
| `test_roundtrip.py` | ~15 | parse → serialize → compare DSL (identity round-trip) |
| `test_column_layout.py` | ~9 | Column start/stop/next commands, default/custom gaps |
| `test_column_rendering.py` | ~4 | HTML rendered output for column layouts |
| `test_drag_drop.py` | ~5 | STAMP_ADD_AT parsing, absolute positioning, mixed row+absolute |
| `test_inline_formatting.py` | ~13 | Markdown-to-HTML (bold/italic/code/strikethrough/sup/sub) |
| `test_typography.py` | ~9 | Drop caps, text shadow, text outline, gradient fill HTML output |
| `test_auto_layout.py` | ~7 | Auto-layout API: row-first, balanced, grid, error cases |
| `test_build_items.py` | ~7 | Canvas element → DSL round-trip, shape dispatch, text elements |
| `test_collection.py` | ~14 | Stamp CRUD, search, CSV import, pagination, sorting |
| `test_cloud_sync.py` | ~11 | Registration, login, logout, file sharing |
| `test_desktop_and_export.py` | ~6 | PDF/PNG/SVG export, DPI, binary magic bytes |
| `test_validation.py` | ~15 | ParseError, validation warnings, error line numbers |
| `test_version_history.py` | ~7 | Version save/list/get/delete, pruning |
| `test_websocket.py` | ~7 | WebSocket messages: render, ping, validate |
| `test_low_complexity.py` | ~2 | Excel import error cases |

---

## 10. Key Design Decisions

1. **Single-file PDF engine** — `pdf_generator.py` contains all PDF drawing, HTML preview, border rendering, and font resolution. This is convenient but the file has grown to 1,024 lines.

2. **Two parallel pipelines** — DSL-based and canvas-based rendering both generate the same `Album` model, but use different entry points. The canvas bypass (`_canvas_state_to_album`) directly maps JSON to models without the DSL parser.

3. **No frontend framework** — Vanilla JS with a single global namespace (`window.StampAlbum`). All state is closure-private in `app.js` and exposed via property descriptors.

4. **Undo via full snapshots** — `pushUndo()` stores `JSON.stringify(S.E)` (max 50). Simple but memory-intensive for large albums.

5. **DSL as internal format** — The DSL is both a user-facing text format (advanced mode) and the internal serialization format for `.slbum` files. This means any DSL change affects both.

6. **Fonts via ID system** — Font IDs (`HN`, `HB`, `TN`, `TB` etc.) map to system fonts by substring matching. The PDF uses PyMuPDF built-in fonts for standard 14 and walks system directories for custom fonts.

7. **ContentEditable for text editing** — Canvas text uses `contentEditable` spans with `white-space: pre-wrap`. Newlines are stored as literal `\n` in element `lbl` values.

8. **JSON file storage** — User data (stamp collection, cloud sync) uses flat JSON files in `~/StampAlbum/`. No database.

9. **Page border system** — Borders are defined as named styles with separate SVG renderers on the canvas and PyMuPDF drawing functions in the PDF. The ornamental styles (6 styles) and edge patterns (2 styles) each have SVG path data in `borders.js` and equivalent PyMuPDF path drawing code in `pdf_generator.py`.

---

## 11. Technical Debt / Known Issues

### Dead Code (unused files / functions)

| File | Status | Reason |
|------|--------|--------|
| `canvas.js` | Dead (300 lines) | All functions overwritten by `render.js` |
| `events.js` | Dead (344 lines) | `S.init` overwritten by `init.js` (loads last) |
| `export.js` | Mostly dead (120 lines) | `app.js` has duplicate `buildCanvasState`/`openPreview`/`exportPDF` that are used instead |

The JS load order means `events.js` and `canvas.js` are loaded but their code never runs. `export.js` exports to `S` but `init.js` calls the `app.js` versions.

### Architecture Notes

| Issue | Detail |
|-------|--------|
| `pdf_generator.py` size | 1,024 lines with two classes + many helpers. Consider splitting into `pdf.py`, `html_preview.py`, `borders.py`. |
| Double `S.init` | Both `events.js` and `init.js` define `S.init`. The load order makes `init.js`'s version the real one. |
| Duplicate functions | `buildCanvasState`/`openPreview`/`exportPDF` defined in both `app.js` and `export.js`. |
| Undo/memory | Full element snapshots via `JSON.stringify(S.E)` — for albums with hundreds of stamps this could use significant memory. |
| Canvas bypass | `_canvas_state_to_album()` duplicates shape-mapping and element-construction logic that exists in the parser. |
| Border style duplication | Both `borders.js` (SVG) and `pdf_generator.py` (PyMuPDF) define equivalent ornamental/edge path data — change one, must change both. |
| DSL line count | The DSL generated by `buildDSL()` produces one line per element. Large albums generate very long DSL files. |
| No database | Collection CRUD and cloud sync use flat JSON files. No concurrency protection. |
| `font_manager.py` vs `_resolve_font` | Independent font resolution systems: `FontManager` uses fonttools, `_resolve_font` in pdf_generator walks directories directly. |
| Test count drift | CONTEXT.md says 211 tests; pending tasks show 209. Tests should be audited. |

---

## 12. Environment & Configuration

**Storage locations:**
- Albums: `~/StampAlbum/*.slbum`
- Images: `~/StampAlbum/images/*`
- Stamp collection DB: `~/StampAlbum/.collection.json`
- Auth/sharing: `~/StampAlbum/.users.json`, `.sessions.json`, `.shares.json`
- Version history: `~/StampAlbum/.versions/{hash}_{name}/*`
- Draft auto-save: `localStorage` (browser)

**Environment variables:**
| Variable | Default | Purpose |
|----------|---------|---------|
| `STAMP_ALBUM_PORT` | `8080` | HTTP server port |
| `STAMP_ALBUM_HOST` | `127.0.0.1` | Bind address |
| `STAMP_ALBUM_NO_BROWSER` | (unset) | Skip auto-open browser |
| `STAMP_ALBUM_RELOAD` | (unset) | Enable uvicorn auto-reload |

**Font directories (macOS):** `/Library/Fonts`, `~/Library/Fonts`, `/System/Library/Fonts`

**Build formats:**
- PDF: direct PyMuPDF `doc.save()`
- PNG: `doc.get_pixmap()` (via fitz.open(pdf_bytes))
- SVG: `doc.get_svg_image()` (via fitz.open(pdf_bytes))
- HTML: `get_html_preview()` or `HTMLRenderer.render()`

---

*Generated: 2026-07-03. Based on codebase analysis of stamp-album-pro at commit `ba79de4`.*
