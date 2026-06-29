# CONTEXT.md — stamp-album-pro

## What this project is
A web-based stamp album designer with an InDesign-like free-form page layout feel. Stamp collectors design and print album pages with visual canvas interaction as the primary mode, and a DSL (Domain Specific Language) as an advanced toggle. Built with Python FastAPI backend and a browser-based frontend.

## Owner / developer profile
- Stamp collector — thinks in collector workflows: grid layouts, free-form stamp positioning, direct text input
- Wants an InDesign-like feel: drag, drop, resize, annotate freely on a page canvas
- Prefers iterative refinement over big-bang rewrites
- Batches medium-complexity items in one session and commits at natural boundaries

## Tech stack
- Backend: Python / FastAPI
- Frontend: Browser-based visual canvas (SVG shapes, contentEditable text)
- PDF generation: PyMuPDF direct drawing (branch `v2-pymupdf`) — no WeasyPrint
- Entry point: `stamp-album` (opens in browser, downloads go to Downloads folder)
- Desktop mode: `stamp-album --desktop` (pywebview window, opt-in)
- Auto-reload: `STAMP_ALBUM_RELOAD=1 stamp-album` (dev mode)
- Tests: 211 tests (maintain this coverage — do not break existing tests)
- DSL: advanced toggle, not the default mode
- Branches: `main`/`master` (stable, WeasyPrint), `v2-pymupdf` (PyMuPDF, current dev)

## Current version state (v2-pymupdf)
- PDF generation rewritten: PyMuPDF direct drawing replaces WeasyPrint entirely
- No native library dependencies (Pango/Cairo/GLib) — pure Python PDF generation
- System fonts embedded by scanning `/Library/Fonts`, `~/Library/Fonts`, `/System/Library/Fonts`
- Font resolution: font IDs (HN, HB, TN, etc.) → system .ttf/.ttc files via `fitz.Font(fontfile=...)`
- Stamp shapes: rectangle, oval, diamond, triangle, hexagon, octagon, pentagon
- HTMLRenderer: renders both DSL-based rows and canvas drag-and-drop stamps
- Column layout support: `PAGE_COLUMN_START` → `column-container cols-N` with gap styling
- Text formatting: bold, italic, strikethrough, code, superscript, subscript
- Typography preview: drop caps, text shadow, outline, gradient fill
- SVG shape rendering on canvas
- contentEditable text elements (direct inline editing)
- Collapsible panels in the UI
- Grid fill tool for batch stamp placement
- Visual canvas is the default; DSL is an advanced opt-in

## Key conventions
- Visual-first: all new features default to canvas interaction, not DSL
- Free-form positioning is a first-class feature — do not regress to row-based or grid-forced layouts
- `stamp-album` is the browser entry point — test by opening this, not via unit tests alone
- Default export UX: browser download to Downloads folder (not native dialog)
- Run the full test suite (`pytest` or equivalent) before committing any change
- Commit at logical boundaries, not mid-feature
- Two PDF backends exist: keep `main`/`master` (WeasyPrint) stable, develop on `v2-pymupdf`

## PDF architecture (v2-pymupdf)
- `src/stamp_album/engines/pdf_generator.py` — single file containing:
  - `PDFGenerator` — direct PyMuPDF drawing for PDF/PNG/SVG export
  - `HTMLRenderer` — HTML/CSS preview from Album/Page/Stamp models
- PNG export: `generate_to_bytes()` → `fitz.open()` → `get_pixmap()`
- SVG export: `generate_to_bytes()` → `fitz.open()` → `get_svg_image()`
- Font map: `_BUILTIN_FONT_MAP` for standard 12 PDF fonts, `_resolve_font()` for system fonts
- Stamp model has no `border_color`/`fill_color` — colors come from `album.color_stamp_border` / `album.color_stamp_background`

## Web dev debug patterns (critical — check these before assuming a bug)
1. Browser tool may be stale — hard-refresh before reporting a bug (Cmd+Shift+R)
2. Verify static files with `curl`, not the browser, to bypass cache
3. `nosniff` header + wrong `Content-Type` = browser silently refuses `.js` files
4. Same-named JS functions overwrite each other via hoisting — use IIFEs to isolate scope
5. CodeMirror 5 drag-and-drop: use `editor.on("drop", ...) + CodeMirror.e_stop(e)`
6. Inline `<script>` blocks may not execute if loaded late — prefer external `<script src="...">`
7. `DOMContentLoaded` may have already fired for late-injected scripts — check `document.readyState` first

## Hermes-specific instructions
- Start every session: `read README.md and list any open TODOs or known issues`
- Before any JS change, check for same-named functions that could conflict (hoisting trap)
- After each feature batch is committed, ask Hermes to create a skill summarising what was built
- Use local Qwen 3.5 4B for: bug investigation, reading existing code, small isolated fixes
- Escalate to owl-alpha for: FastAPI architectural changes, complex canvas/SVG logic, test suite design
- Preferred workflow: discuss change → confirm → implement → test in browser → commit
- Never auto-commit — always show the diff and ask for confirmation first
