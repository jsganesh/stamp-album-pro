# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.0] - 2026-10-07

### Added
- New export engines (ReportLab, Pillow and SVG) with a multi-format export UI (PDF, PNG, SVG)
- Shared border and ornament geometry module (`engines/borders.py`)
- Shared row layout module (`engines/layout.py`) used by all renderers
- Edge patterns (greek key, rope) and ornamental corners in the preview and in PDF output
- Page delete button; A5 and Legal page sizes
- `border_style` DSL command
- Visual regression test with HTML and SVG snapshots; DSL round-trip tests
- `ARCHITECTURE.md`
- Dependabot configuration
- CI on macOS, Windows and Ubuntu, installing from `uv.lock`
- CI package checks: the wheel must contain the web UI, must contain no test code, and must import in a clean environment

### Changed
- All preview callers now go through `HTMLRenderer`; `get_html_preview` was removed
- Ornament and edge SVG generation is shared through `segments_to_svg_fragment()`
- Stamp borders, philatelic rendering, y-flip and preview alignment reworked; page border controls consolidated into the toolbar
- The DSL editor starts empty and reflects only what is on the canvas
- Removed the default "My Album" title from all entry points
- Removed the column layout option from the new-album wizard
- The built wheel now contains only the `stamp_album` package (it used to include a top-level `tests/` folder)
- `uv.lock` is now tracked in git
- `pytest-qt` moved from the `dev` extra to the optional `legacy` extra
- Repository tidy-up: stale notes moved to `docs/archive/`, PyInstaller specs moved to `packaging/`, notebook checkpoint files removed
- Old development branches were archived as `archive/*` tags; `main` is the only branch

### Fixed
- Silent data loss on save: absolute-positioned stamps and catalogue references are now saved
- State corruption after a partial failure in `raster.py`
- `NameError` in `svg_export.py` border handling
- Rectangle stamp colours now use the album defaults, text elements use `font_id`, and `applyState` makes a deep copy
- Default border, corner ornaments, DSL emission and draft save
- Special borders: double-line rendering in the preview and PDF, and DSL round-trip
- Multi-line text in PDF output, and text element positions after reload
- Uploaded images now render in the preview and in PDF output
- Missing runtime dependency `python-multipart`: the app failed to import in a clean install
- Fresh installs no longer flood the server log with WebSocket warnings or make the page flicker: `websockets` is now a declared dependency

### Known issues
- PyMuPDF (AGPL-3.0 or commercial) is a runtime dependency, and importing `fitz` prints a deprecation warning
- About 258 ruff findings remain; lint is advisory in CI
- PyInstaller specs in `packaging/` are stale (no web assets, no ReportLab), and there are no signed installers
- References to WeasyPrint remain in some comments, an error message and two test lines
- The legacy PyQt6 editor is still shipped in the wheel
- `docs/BUILD.md` describes an older architecture
