# StampAlbum Pro

Web-based stamp album page designer with a free-form canvas, like InDesign. Python FastAPI backend, vanilla-JS browser frontend. The installed Mac and Windows apps are the same code frozen with PyInstaller and shown in a pywebview window. Version 0.7.1 (alpha). Python 3.11+.

## Commands
```sh
uv sync --extra dev          # set up .venv
make test                    # .venv/bin/python -m pytest src/tests/ -q
make run                     # browser mode
make dev                     # browser mode with auto-reload (STAMP_ALBUM_RELOAD=1)
uv run stamp-album --desktop # own window
.venv/bin/ruff check src     # lint (line length 100)
make app                     # PyInstaller build, smoke test, zip (see docs/BUILD.md)
```
- `src/tests/` holds Python tests and a few `.mjs` tests run through Node. Browser tests use Playwright Chromium (`python -m playwright install chromium`). CI sets `STAMP_ALBUM_REQUIRE_BROWSER=1`, so a missing browser fails the run instead of skipping.
- Run the full suite before committing. Do not drop existing tests.

## CI
- `ci.yml` (push to main, every PR): pytest on macOS (Python 3.11, 3.13), Windows (3.11, 3.13), Ubuntu (3.11), installed with `uv sync --frozen` from `uv.lock`. Then `ruff check src`. A `package` job builds the wheel and checks it contains the web UI and no test code.
- `app.yml`: PyInstaller build of the Mac app and the Windows folder, plus `packaging/smoke_test.py`. Runs when packaging, `pyproject.toml`, `uv.lock`, `__main__.py`, `desktop.py` or `serve.py` change. Pushing a `v*` tag creates a draft GitHub release with both zips; notes come from that version's CHANGELOG section (`tools/release_notes.py`).
- Workflow tokens are read-only except the release job.

## Layout
```
src/stamp_album/
  api.py, serve.py, desktop.py, __main__.py   FastAPI app and entry points
  core/        models.py, parser.py (DSL to Album), serializer.py, themes.py
  engines/     pdf.py, raster.py, svg_export.py, html_renderer.py, layout*.py, borders.py, frames.py, font_manager.py ...
  web/         index.html and plain JS (no framework), shared namespace window.StampAlbum
  ui/, locales/, storage.py, templates.py, version_history.py
src/tests/     pytest + .mjs tests, snapshots/
packaging/     PyInstaller spec, entitlements, smoke_test.py
docs/          BUILD.md, DSL_SPEC.md, FEATURE_SPEC.md, screenshots/
```

## Constraints
- Exports use ReportLab, Pillow and SVG only. No WeasyPrint, no PyMuPDF, no native Pango/Cairo libraries.
- A test fails the build if a GPL or AGPL library is added. Every build ships `THIRD_PARTY_LICENSES.txt`.
- The visual canvas is the default mode; the DSL is an advanced opt-in. Free-form positioning is first-class. Do not regress to row-based layouts.
- The server listens on this computer only. It serves editor files by looking the name up in the folder's file list, never by building a path from the request address (security fix, 0.7.1).
- System fonts are found by scanning `/Library/Fonts`, `~/Library/Fonts`, `/System/Library/Fonts`. Font IDs (HN, HB, TN ...) resolve to .ttf/.ttc in `engines/pdf.py`.
- Mac builds match the build machine's processor. Release builds are signed and notarised through `./build.sh` with `CODESIGN_IDENTITY` and `NOTARY_PROFILE` (steps in `docs/BUILD.md`).
- Update `CHANGELOG.md` (Keep a Changelog format, `[Unreleased]` section) with user-visible changes.

## Frontend traps (check before assuming a bug)
- Same-named JS functions overwrite each other through hoisting. Check for name clashes before adding one. Use an IIFE to isolate scope.
- A `nosniff` header with the wrong `Content-Type` makes the browser refuse a `.js` file silently.
- Hard-refresh (Cmd+Shift+R) before reporting a bug. Check static files with `curl` to bypass the cache.
- Inline `<script>` blocks may not run if loaded late. `DOMContentLoaded` may have fired already; check `document.readyState`.
- CodeMirror 5 drag-and-drop: `editor.on("drop", ...)` plus `CodeMirror.e_stop(e)`.

## Docs and their state
- `docs/BUILD.md`: build and release. Current.
- `ARCHITECTURE.md`: written for the removed PyMuPDF pipeline. Its rendering sections, test counts and file stats are out of date. Check the code first.
- `CONTEXT.md`: owner notes. Its "PDF architecture" section is history, its test count is outdated, and its Hermes section is for a different assistant and does not apply.
- `.10x/status.md`, `.10x/handoff.md`: project status notes.
- `SECURITY.md`: vulnerability reporting.
