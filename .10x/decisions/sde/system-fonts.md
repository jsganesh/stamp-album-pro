# SDE: system-fonts

**Date:** 2026-10-24 · **Branch:** fix/system-fonts · **ADR:** 001

## What was built
- `engines/system_fonts.py` (new): `font_dirs`, cached `index` (family → Face(path, index)),
  `find`, `available`, `reportlab_name`, `pillow_font`, `css_family`, `font_face`, `clear_cache`.
  `CANDIDATES` is the 46-name list that used to live in `web/app.js`.
- `pdf.py` / `raster.py`: their file-name guessing and per-module font folder lists removed;
  non-built-in ids go through the finder (Helvetica / Pillow default if not found).
- `svg_export.py`: text measured with the PDF's font; subset `@font-face` added beside the
  caption font's. `html_renderer.py`: same embedding; `text_layout.css_font` names an
  installed family (print preview, HTML).
- `api.py`: `GET /api/fonts` (sync def: the first scan runs in the thread pool).
- Web: `app.js` `loadSystemFonts()` replaces browser `detectFonts()`; `missingFonts()`,
  `missingFontsNote()` appended to the export message; toasts stay `max(3 s, 60 ms/char)`.
  `render.js` `showFont()` marks a missing font; "Web Safe" group removed.
- Phrases: `msg.fonts_system` → "Fonts on this computer"; `msg.fonts_web_safe` removed;
  `msg.font_not_on_this_computer`, `msg.fonts_not_here_print_helvetica` added.

## Deviations
- `engines/font_manager.py` was not reused (see ADR-001 alternatives); it stays unused.

## Tech debt
- `font_manager.py` is dead code; remove in a later clean-up PR (owner to confirm).
- Text items use only a family's regular face (as before); bold/italic system faces not offered.

## Tests
`test_system_fonts.py` (10), `test_font_list_ui.py` (4).
