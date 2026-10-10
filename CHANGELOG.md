# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **Frame size in Properties**: a selected stamp shows its frame and stamp sizes, for example "Frame 32.4 × 42.4 mm, 1 mm clear all round the stamp (30 × 40 mm, dashed)". On the canvas a faint dashed line marks the stamp's own size inside the frame; it is never printed
- **Frame warnings**: a stamp whose frame runs past the page border (the page edge when there is no border) or into another item gets the amber "!" badge, as captions do
- **Caption warnings** in the editor: a stamp whose captions run into another item, or past the page border (the page edge when there is no border), gets an amber "!" badge and tinted captions, with the reason in its tooltip and for screen readers. It updates as stamps are moved or edited
- **Album themes** in the page bar: Exhibition (black, the default), Green, Maroon, Navy and Brown. A theme colours the page border and headings marked as headings, in the editor and in every export; everything else stays black. An older album with its own border colour shows as Custom until a theme is chosen. Changing the theme or page border is one undo step and is kept in the draft
- **Mark as heading** for text items in Properties; the palette's Heading item is marked already. Saved as a `PAGE_TEXT_ROLE("heading")` line after the text
- Page borders in two groups, Plain (None, Single, Double) and Decorative (Classic, Victorian, Art Deco, Greek Key, Rope, Laurel, Gothic, Filigree, Dashed, Dotted), with a "Decorative: not for competition" note when one of the latter is chosen
- Keyboard access to items on the page (UI and UX audit, item 4): every stamp, text and image is a tab stop named for screen readers (for example "Rectangle stamp, Penny Black, 40 × 30 mm at 20, 25 mm"); focusing one selects it. Arrow keys move the selected item one grid step (1 mm with the grid off), Shift+arrow 10 mm, each press one undo step; Enter jumps to its properties; Delete moves focus to the next item. Listed under View › Keyboard shortcuts
- Accessibility pass (UI and UX audit, item 4): every Properties and wizard field is tied to its label, with clear spoken names such as "Border width" and "Fill opacity"; icon and emoji buttons have word names ("Close the wizard", "Remove image"); Images-panel tiles, file-list rows, page dots, template cards, the section and panel toggles, Upload image and the preview's Export menu are real buttons that work with Tab, Enter and Space, with a visible focus ring. Headings and landmarks for screen-reader navigation; toasts are announced
- Automated axe-core scan of the editor and its dialogs in the browser tests (`test_accessibility.py`, via `axe-playwright-python` in the dev extra), so new markup without a label or name fails CI
- Palette click-to-add (UI and UX audit, item 3): clicking a palette item, or pressing Enter or Space on it, adds it at the centre of the page. Each repeat steps 10 mm right and down so items don't stack, staying on the grid and inside the page. Tapping on a touch screen does the same; clicking an image in the Images panel also adds it at the centre. Palette items are now keyboard-focusable buttons named "Add …"
- A short palette hint ("Click an item to add it to the page, or drag it where you want it") that hides after the first item is added and comes back when the user seems stuck: 20 seconds without input on an empty page, a palette drag let go away from the page, or three clicks on an empty page within 4 seconds
- Page setup dialog (the **Page** button above the canvas, which now shows the size, for example "A4 · Landscape"): change the open album's paper size and orientation without starting a new album. Elements that would fall outside the new page are moved inside it as a group, keeping their arrangement; their sizes never change, so mounts still match the stamps. The dialog says beforehand how many elements will move and warns if some will overlap or are larger than the page. Applying is one undo step
- Playwright in the dev extra; CI installs Chromium and runs the browser tests (they fail instead of skipping there)
- Browser smoke test (`test_ui_smoke.py`; skipped locally without Playwright, required in CI)

### Changed
- **Tutorial** rewritten for the current editor, with a picture for each step: adding stamps at their catalogue size, frames and captions, theme, page border and Page setup, and preview and export. The first-run sample album is now an exhibition-style page with three 1840–41 stamps at 19 × 22 mm (StampWorld 1 to 3). The pictures and the README screenshots are made by `tools/screenshots.py` (`make screenshots`)
- **Page borders look the same in every view.** The editor's drawing is the reference: `engines/page_border.py` ports `renderPageBorder`, its corner ornaments and edge patterns from `web/borders.js`, and the preview, PDF, PNG and SVG all draw its lines from it. Plain borders print at the editor's weights (Single 0.4 mm, was 0.5 mm). Greek key and Rope no longer have a plain rectangle under them in exports (the editor never drew one), and in the editor they take the theme colour like every other border (Rope was brown)
- **Stamp frames are drawn outside the stamp** in the editor, preview, PDF, PNG and SVG, from one geometry (`engines/frames.py` and `frameLines` / `shapeOutline` in `web/dsl_core.js`). A stamp's W and H are its size from the catalogue; the frame leaves 1 mm clear all round, then draws its line or lines: Thin 0.5 pt, Medium 1 pt, Double two 0.5 pt lines 1 pt apart. Shaped stamps keep the 1 mm on every side. Captions, and their warnings, are measured from the frame's outer edge. Albums made before this keep their stored sizes, so their frames grow by the clearance
- **Stamp captions** have one layout in the editor, preview, PDF, PNG and SVG (shared by `engines/caption_layout.py` and `captionLayout` in `web/dsl_core.js`): the heading above the box in bold 9 pt; below it the description (8 pt), the details line ("1/2D · Used · Imperforate") and the catalogue number, both 8 pt italic. The nearest line is 2 mm from the frame, lines are centred and wrapped to the stamp's width, and captions are black. The description now always sits below the box (it used to be drawn inside a box without an image). In the editor the captions are drawn where they print and the description is edited in place below the box; shaped stamps show their captions too. Pictures have no captions
- Stamp frames follow exhibition practice: always black, with a single **Frame** choice in Properties (None, Thin 0.5 pt, Medium 1 pt, Double) in place of border style, colour, width, fill colour and opacity. Albums made before this open with the nearest black frame and no fill. The page bar's page-border colour and stamp-fill pickers are replaced by the theme. On screen, frames are drawn at fixed widths (Thin 1 px, Medium 2 px) so they can be told apart; exports use the point widths
- Toolbar regrouped into **File**, **Edit** and **View** menus, with Undo, Redo, Preview and Export kept on the bar (UI and UX audit, item 2). Align, Duplicate, Grid fill and Delete appear in the page bar only while a stamp is selected. The toolbar now fits 1440 and 1024 px windows and phone width without sideways scrolling; buttons use line icons and are labelled for screen readers. Wizard is now File › New from wizard; Reset app moved to the bottom of the View menu; View › Show tutorial again is new
- The page bar's **Border** sets the page border only (it used to change the default border of new stamps too); it is labelled Page border and shows the loaded album's border
- **Snap** is one control: the grid (Off, 5 mm, 10 mm) in the page bar, and View › Snap to guides
- The wizard is now the **New Album Wizard** and asks "Discard unsaved changes?" before replacing an album with unsaved changes, like **New**
- Undo now covers the whole album (all pages and the page size), so adding or deleting a page and Page setup can be undone

### Removed
- Columns and Gap controls (albums that use columns keep them when opened and saved), and Distribute and Match size, which always failed because only one stamp can be selected
- Dead `canvas.js` (not loaded) and `events.js` (loaded but never run), both superseded by `render.js` and `init.js`

### Fixed
- The DSL editor's scrolling area could not be reached from the keyboard once the album was long enough to scroll (flagged by the accessibility scan). CodeMirror now takes typing in the text itself (`inputStyle: "contenteditable"`), which also reads better with screen readers
- Page borders differed from view to view because each drew the shared patterns at its own scale. PNG drew Greek key, Rope and the corner ornaments about a third of their size with 1-pixel lines; the preview and PDF drew them at two thirds; SVG drew Greek key and Rope about two and a half times too big. The PDF Classic corner came out as a loop because the Python copy of the ornaments had been transcribed wrongly. Dashed and Dotted printed as solid lines everywhere except the editor
- Typing a size or position into W, H, X or Y in Properties stored the wrong value: 19 mm became 3.04 mm (the field's millimetres were converted as if they were canvas pixels). Sizes and positions read from a file were also rounded to 0.4 mm steps, so a 19 mm stamp opened as 19.2 mm; they are now kept to 0.004 mm
- Exports ignored the stamp's frame: the PDF, PNG and preview drew every frame as one thin line and the SVG as a 0.3 mm line, whatever was chosen. The album file's frame style and width were dropped on loading, and the Python serializer wrote every frame as solid 1 pt without the shape name, so the fields shifted when read back
- The preview clipped the right and bottom edges of stamp frames
- Stamp captions overlapped in exports: the PDF details line ran into the frame and the catalogue number into the details; the preview heading overlapped the box; the editor drew the heading below the box and showed only the denomination
- SVG captions were drawn about three times too large (sizes in points inside a millimetre drawing)
- Decorative page borders (Classic, Greek Key and the others) reopened as plain Single or Double; the style is now saved by name
- Exports made from a saved file drew the page border black whatever its colour (the quoted colour was not read)
- Text at a fractional size such as 10.5 pt vanished when the album was reopened
- The first-run sample album's third stamp ran past the page border
- Saving an album to a file lost each stamp's heading, catalogue number, denomination, condition and perforation, and a rectangle stamp's border settings (they survived a browser reload but not Save and Open). They are now written to the file; older versions of the app skip the new lines
- Exports made from a saved file printed empty catalogue fields ("SG 10 ·  · sacc 10")
- A browser reload dropped the page border
- Every opened album gained a blank first page and opened on its last page; the first-run sample showed "Page 2 of 2"
- Toasts stacked when two messages came close together; a new one now replaces the one showing
- The Properties panel ran past its right edge at 1440 px with an element selected
- The Keyboard shortcuts dialog listed keys that did nothing (Ctrl+P, Ctrl+N, Ctrl+L/E/R; in a browser these hit the address bar, open a window or reload) and missed Ctrl+D; F5 is now listed once, as Preview
- Backspace while editing a stamp's label on the page asked to delete the whole stamp
- The Import section's ▼ toggle did nothing
- A collapsed sidebar or Properties panel left its controls reachable by Tab while hidden; the handle that reopens it can now be reached from the keyboard
- An image's delete button never showed on touch screens
- Dropping a palette item on the page by touch ignored the grid setting, and with the grid off placed it at an invalid position
- An element added at the very left or top edge (x or y of 0) was moved to 50 px
- Dragging with Snap set to Off lost the stamp's position (the step was divided by zero)
- Snap grid steps were pixels while the grid drawn was millimetres; dragging now moves in whole 5 or 10 mm steps that match the grid
- Snap to guides never snapped: the guide lines were drawn but the stamp was not moved onto them. The button also showed "on" at start while snapping was off
- Albums with columns lost them on the next save: loading treated `PAGE_COLUMN_STOP` as turning columns off
- The Help button opened and immediately closed the shortcuts overlay (two handlers each toggled it)
- An empty album lost its page size and orientation when saved: the album header is now written even with no elements
- The browser draft did not keep the page size, so a landscape album reopened as portrait after a reload
- The first-run sample album replaced a restored draft for anyone who had not finished the tutorial
- Undo skipped a step after the first undo, and the first edit after start-up could not be undone
- Tests: `STAMP_ALBUM_REQUIRE_BROWSER=1` now fails the browser tests when Playwright is not installed; before, the whole browser test file was skipped silently
- Canvas: text and image elements loaded from a saved album were invisible. The parser gives them a transparent fill with alpha 0, and the canvas applied that alpha as the whole element's opacity. Fill alpha now affects only the fill
- Preview: a stamp that has an image no longer shows its label (the file name) on top of the image, matching the exports
- Canvas text now matches the printed page: font sizes are typographic points converted at the canvas scale (a size of 40 was about 13% larger on screen than in the PDF), stamp labels use the same 0.9 factor as the exports, and text elements are top-anchored, 1 mm padded and aligned left/centre/right per their alignment (the canvas always centred them)
- PNG export no longer stretches images: they are fitted inside their box and centred, like the PDF and preview
- Stamp shapes are now identical in the canvas, preview, PDF, PNG and SVG: the PDF and PNG used a different "regular polygon" outline (the octagon looked 7-sided); one shared outline definition (`polygon_points`) is used everywhere. The PDF triangle was drawn upside down and is now apex-up
- PNG stamp labels, headings, catalogue references and footers were drawn about 3x too small (points used as pixels); they are now point-based and placed like the PDF (heading above, catalogue and footer below)
- Preview: stamp labels were hidden behind the stamp shape; ovals and other shapes were squeezed into a square instead of filling their box; shape outlines were hairline-thin and are now a constant 0.5 pt like the PDF
- PDF export: images with transparency (for example a coat of arms PNG) no longer get a solid black background
- Text elements in exports: alignment (left/centre/right) is now honoured in PDF, PNG, SVG and the preview; text wraps inside its box; text is anchored to the top of its box instead of overflowing upwards (the PDF clipped large headings at the page top)
- PNG text was drawn about 3x too small (point sizes were used as pixels) and fell back to a fixed 10 px bitmap font when Helvetica/Arial was not found
- SVG text used `pt` font sizes inside a millimetre viewBox
- Albums saved by v0.2.0 and earlier with the oversized page (for example A4 saved as 238 x 336.8 mm) are corrected to the real paper size on load, with a notice; landscape is handled too
- The new-album wizard did nothing: `wizard.js` was never loaded by `index.html`
- Landscape and custom-size albums displayed as portrait A4: the on-screen page is now sized from the album's millimetre size (`S.applyPageSize`) when loading DSL, using the wizard, or changing the page-size dropdown
- Wizard paper sizes now match the page-size dropdown (Letter 215.9x279.4, Legal 215.9x355.6)

## [0.2.1] - 2026-10-08

### Fixed
- Exported pages were about 13% larger than the paper size chosen in the editor (A4 came out at 238.0 × 336.8 mm, A5 at 168 × 238 mm). The editor's paper table held PDF points where millimetres were needed. PDF, SVG and PNG exports now match A3, A4, A5, Letter and Legal exactly.

### Known issues
- Albums saved before this fix store the old, oversized page size. Open them and re-select the paper size; content may then extend past the page edge.
- Starter templates (the row-based files in `templates/`) export to PDF with stamps outside the page margins and without their headings. The row and column DSL commands are legacy and are being retired.
- Text elements export left-aligned and without their box borders, so centring and borders shown in the editor are not reproduced in PDF, SVG or PNG.
- The PNG export draws the octagon vertex-up, unlike the editor, SVG and PDF, and the HTML preview differs from the exports for some shapes.

### Changed
- `engines/pdf_generator.py` is now `engines/html_renderer.py` and contains only the HTML preview renderer
- Startup no longer prints the PyMuPDF `fitz` deprecation warning

### Removed
- The PyMuPDF dependency (AGPL-3.0 or commercial) and the legacy PyMuPDF PDF engine. PDF, PNG and SVG export were already served by the ReportLab, Pillow and SVG engines.

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
