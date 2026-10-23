# Architect: system-fonts

See ADR-001. Components:
- `engines/system_fonts.py` — `font_dirs()`, `index()` (cached family → Face(path, index)),
  `find(family)`, `available()`, `reportlab_name(family)`, `pillow_font(family, size)`,
  `font_face(family, chars)`, `css_family(family)`.
- `api.py` — `GET /api/fonts` → `{"fonts": [...]}`.
- `engines/pdf.py`, `raster.py`, `svg_export.py`, `html_renderer.py`, `text_layout.css_font` — use it.
- `web/app.js` — Font list from `/api/fonts` (no browser guessing); `web/render.js` — marks a font
  the album uses but this computer lacks; `web/export.js`/`app.js` — export warning.
Failure modes: unreadable/corrupt font files are skipped; a font forbidding embedding is not offered;
lookup failure at export → Helvetica (as before) with the warning.
