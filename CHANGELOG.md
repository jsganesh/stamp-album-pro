# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- File › Title and plan page… (also in the right panel, under Exhibit): a form for an exhibit's first page as FIP judges expect it: the title and a line under it, Purpose, Scope, a plan of chapters and sections (numbered for you: 1, 1.1, 2), Important items, Research and References. It makes the page from your answers (on page 1 if that is empty, otherwise as a new first page), says when the page is too long, and is one Undo step. Opening it again shows the page's own text, including anything you changed on the page, and Update the page replaces only the parts it made
- Album files mark those parts with `PAGE_TEXT_PART("…")` after each text item; older versions skip the line

### Changed
- The Title page template follows the FIP guidelines for an exhibit's first page: Purpose, Scope, a plan in numbered chapters and sections (not a list of pages), how important items are shown (a double frame), Research and References
- Page setup says how an FIP sheet hangs in an exhibition frame: 4 to a row and 16 to a frame for 23 cm sheets, 3 and 12 for 31 cm, 2 and 8 for 46 cm (GREX 2026 Art. 6.1)
### Fixed
- **Fonts on this computer print as they show.** A text item set in a font such as Georgia or Palatino showed in the editor but came out in Helvetica in the PDF, PNG, SVG and HTML exports. One font finder now reads each font's own name, looks in the font folders and their subfolders (on a Mac most fonts are in a subfolder) on macOS, Windows and Linux, and serves every export: the PDF and PNG draw with the font, and the SVG and HTML carry the letters used, as the captions do. Print preview shows it too.
  - The Font list's "Fonts on this computer" now comes from the app rather than from the browser guessing, so every font offered prints. Fonts that can't be put into a PDF (OpenType outlines or a licence that forbids it) are not offered. The "Web Safe" group, whose fonts didn't print either, is gone.
  - A font an album uses that this computer doesn't have shows as "Zapfino (not on this computer)", and the export message names the fonts that printed in Helvetica instead.
  - Longer messages stay on screen longer.
- **Words typed in the right panel are kept when you move on.** A stamp's Name, Heading, a picture's Caption and the optional details (Value, Condition, Perforation, Catalogue no.) used to be saved only when the field was left with Tab or Enter: clicking the next stamp, the empty page, or closing the phone's Properties sheet dropped what had been typed. Now the words are saved as they are typed and drawn on the page straight away. Leaving the field or choosing another item records them as one step to undo. A number half typed in Position, Size or Font size is kept the same way, and goes to the item it was typed for. Save and Export count a field still being typed in.
- **A click that only selects an item is no longer a step to undo**, so Undo always undoes something you can see.

## [0.5.0] - 2026-10-18

The last of the UI review: a phone layout with a bar along the bottom, pictures of the pages beside the page, one Stamp tile at the size you used last, Print preview one page at a time, a template gallery with pictures and four more templates, stamp mounts and FIP exhibit sheets, and safer saving.

### Known issues
- The macOS app and the Windows folder are not signed, so macOS and Windows warn the first time they are opened (on a Mac: right-click › Open; on Windows: More info › Run anyway)
- The macOS app is built for Apple silicon only
- The Windows app is built and checked in CI but has not been tried by hand
- The launch scripts in `launcher/` have not been tested for this release
- Dependency licences have not been audited
- Only English is shipped; the phrase lists are ready for other languages
- The tutorial describes the computer layout (the left and right panels); on a phone its words don't match the bar along the bottom
- AlbumEasy albums (`.txt`) open as a blank page: there is no importer. Saving never writes over the `.txt`

### Added
- **Four more templates** in the Template gallery, drawn from the layouts of the owner's own AlbumEasy "First Issues" albums: **Introduction page** (spaces for a map, coat of arms and flag, a note on the postal history, then the first issue in rows), **Long set** (three rows of five low values, then the high values in a larger size), **Stamps with illustrations** (pictures of the overprint types above the stamps they explain, then a second printing with its own picture) and **Normal and varieties** (three rows, each a normal stamp followed by its shade, paper, watermark and perforation varieties, named above each one). Only the layouts are taken: no country, text or catalogue numbers. The picture spaces are labelled boxes (Map, Flag, Overprint type 1…) that print as plain boxes until a picture is attached. Like the other templates, they open as a new, unnamed album, and fit inside the margins with nothing running into anything else.
- **Stamp mounts**: under **Album and page**, **Mount overhang** (how far the mount shows beyond each stamp: None, 1, 1.5, 2, 2.5 or 3 mm) and **Gap to frame** (the space from the mount's edge to the frame line: 1 to 3 mm). Every stamp's frame is drawn their sum out from the stamp, the same in the editor, Preview, PDF, PNG and SVG; a note gives the total in words, and a selected stamp's panel says "mount 1.5 mm, then 1 mm to the frame line". In the editor the mount's edge shows as a faint dotted line between the stamp's dashed outline and its frame; it is never printed. Changing either moves every frame at once and can be undone. Free shapes and pictures are unchanged.
  - **New albums start at 1.5 + 1 = 2.5 mm** (File › New album, the new-album wizard, the templates and the tutorial's sample). **Albums made before this open at None + 1 mm**, so they print exactly as they did; choose a mount under Album and page to change one.
  - Stored as `ALBUM_MOUNT(overhang gap)` in the album file. Older versions of the app skip the line and draw 1 mm frames.
- **FIP exhibit sheets** in Page setup and the new-album wizard: 23 × 29.7 cm (an FIP frame holds 16), 31 × 29.7 cm and 46 × 29.7 cm (GREX 2026, Art. 6.1). They are used as listed, so Page setup hides Portrait and Landscape for them.

### Changed
- **A phone layout with a bar along the bottom** (UI review item 7): on a phone the bar has four buttons, each an icon above its name: **Add**, **Undo**, **Properties** and **Page**.
  - **Add** opens a sheet from the bottom with the stamp, the other shapes, the text items and Attach image. Tapping one puts it on the page and closes the sheet, ready to drag into place.
  - **Undo** takes back the last change at once.
  - **Properties** opens the selected item's settings, with **Duplicate** and **Delete** at the top. It opens only when tapped, so selecting and moving an item leaves the page in view.
  - **Page** opens the pages (tap a picture to go to it, **Add page**, and the ⋯ menu to move or delete one) and the album settings: paper, page border, theme, headings, stamp mounts and snap. With more than one page the button reads "Page 2", and a small **‹ Page 2 of 3 ›** floats over the page to change page without opening the sheet.
  - A sheet rises from just above the bar, so the bar stays in view, and covers at most two thirds of the screen. It closes with **Close**, a tap above it, Escape, or its button again.
  - Undo and Properties stay tappable when they have nothing to do and say why ("Nothing to undo yet", "Tap a stamp or some text on the page first").
  - The side panels and their ⋮ handles, the bar above the page, the page strip and the status bar no longer show on a phone, so the page has their room. **Not saved** now shows in the top bar, in place of the app name. Messages show under the top bar, clear of the bottom bar. The top bar's menus and Export are unchanged, and so is everything on a computer.
- **Template gallery with pictures** (UI review item 10): each template's card now shows a small drawing of its page above its name and description, in the same style as the page pictures beside the page (the border, each stamp in its own shape, grey lines where text sits), drawn from the template itself at its own paper size and stamp mounts. The cards are larger, two across on a computer and one across on a phone. The "Exhibition" line under each card is gone, as every template had it. A screen reader reads each card's name, then its description.
- **Print preview** (UI review item 8; was Preview): the toolbar button, View menu, F5 and the window are called **Print preview**. It shows **one page at a time**, whole and as large as the window allows (up to 200%, as in the editor), and opens on **the page you are working on**. **Page arrows** under the page ("Page 2 of 5"), or the ← → keys (Home and End for the first and last), go through the pages; they are hidden for a one-page album. Empty pages at the start or the end aren't printed, so they aren't shown either. **Refresh is gone**: the pages are drawn fresh each time the window opens, with a quiet "Drawing the page…" instead of the pop-up messages. **Export ▾** is now the one red button, Close a plain one; **Escape** closes the window and the focus goes back to where it was. While the window is open the editor's own shortcuts (Delete, Escape, ⌘D…) don't act on the page underneath. On a phone, Export and Close share one row. Nothing changes in the pages or the exports.
- **One Stamp tile in the left panel** (UI review item 3): the eight equal shape tiles are replaced by a **Stamp** tile at the top, which adds a rectangle at the stamp size you used last, shown on the tile ("25 × 30 mm" to begin with). Typing a stamp's **W** or **H**, or dragging one of its handles, sets the size for the next stamp; it is remembered on this computer. Opening a file, a template or the tutorial's sample doesn't change it. The other shapes (oval, diamond, triangle, hexagon, octagon, pentagon) fold under **Other shapes** below it and are added at the same size; **Free shape** keeps its own and is described as being for die-cut or irregular stamps. Other shapes start folded, then open or shut as you left them. The tutorial's first step now says to click Stamp. Nothing changes in the page, the exports or the album file.
- **Pages as pictures beside the page**: the numbered page buttons above the page are replaced by a column down the left edge of the canvas, with a small picture of each page (its border, each stamp drawn in its own shape, a box for each picture, grey lines where text sits) and its number underneath. The open page is outlined in red and its picture changes as you work. Click a picture to open that page, or use the arrow keys (Home and End for the first and last); **Add page** is at the end of the column. The column sits beside the page, so the page keeps its size when it fits the window. On a phone the pictures are in the **Page** sheet (see the phone layout above), in one row scrolling sideways.
- **Moving and deleting pages**: each picture has a **⋯** button with **Move earlier**, **Move later** and **Delete page**; all can be undone. Deleting a page that has anything on it now asks first, from this menu and from Edit › Delete page; an empty page is deleted straight away.

### Fixed
- **Save never writes over a `.txt` file.** An album opened from a `.txt` (an older album, or an AlbumEasy file, which the editor shows as a blank page for now) is saved under a new name: Save asks, suggesting the same name ending in `.slbum` (`tdc.txt` → `tdc.slbum`), and a typed `.txt` name is changed to `.slbum`. The `.txt` is left as it was. Before, Save wrote back to the `.txt`, so a blank page saved by mistake replaced the AlbumEasy album.
- **Save asks before replacing another album.** When the name typed is already a saved album, Save asks "An album called “album” is already saved. Replace it?"; No goes back to the name box. Before, a second new album saved under the suggested `album.slbum` silently replaced the first.
- **The server saves albums only under plain `.slbum` names** in the albums folder, and reads or deletes only plain album names: no folder separators (`/`, `\`), drive letters or leading dots. On Windows, a name with `..\` could have written outside the folder, which mattered when the app is opened to other devices on the network (`STAMP_ALBUM_HOST`) for the iPhone.
- Tests that save an album now write to a temporary folder, never the albums folder on the computer running them (the template gallery tests from #74 left a `mine.slbum` in `~/StampAlbum`).
- **Picking a template or finishing the new-album wizard no longer risks the album that was open.** Both now start a new album with no file name, shown as Not saved, so Save asks for a name; before, Save wrote the new pages over the file that had been open. Picking a template now asks first when there is unsaved work, as Open recent does (it used to replace it without asking), and the wizard asks only once even when it hands over to the gallery. Undo starts afresh with the new album.

## [0.4.0] - 2026-10-15

A clearer, easier-to-read editor for older collectors: larger text and controls with a Text size choice, plain names for captions, album settings in the right panel, File and Help menus, images that belong to their album, with captions of their own, and translation support.

### Known issues
- The macOS app and the Windows folder are not signed, so macOS and Windows warn the first time they are opened (on a Mac: right-click › Open; on Windows: More info › Run anyway)
- The macOS app is built for Apple silicon only
- The Windows app is built and checked in CI but has not been tried by hand
- The launch scripts in `launcher/` have not been tested for this release
- Dependency licences have not been audited
- Only English is shipped; the phrase lists are ready for other languages

### Added
- **A caption for an image**: select an image and type in **Caption** (or click its caption on the page to type there). It prints 2 mm below the image in 8 pt italic, centred and wrapped to the image's width, growing a line at a time; there is no box or frame round it. The same in the editor, Preview, PDF, PNG, SVG and HTML, and it gets the "!" warning when it runs past the page border. Duplicating an image keeps its caption. It is stored in the third quoted field of the image's `STAMP_ADD_IMG` line, empty in every older album, so they open unchanged. The image's label (its file name) is still never printed.
- **Security policy** (`SECURITY.md`): how to report a vulnerability privately (GitHub's Report a vulnerability, or email), the 7-day reply, which versions get fixes, and how the app is meant to run: on `127.0.0.1` by default, and only on a trusted network when `STAMP_ALBUM_HOST` opens it to other devices
- **Translation support**: every word the editor shows now comes from a phrase list, `src/stamp_album/locales/en.json` (408 phrases), so the editor can be translated without touching its code. English is the only language so far, and nothing changes in it.
  - `web/i18n.js` looks phrases up: `S.t("msg.page_added")` in the scripts, with `{name}` placeholders and plural forms chosen by the browser's plural rules (`{"one": …, "other": …}`, and `few`/`many` where a language has them); `data-i18n`, `data-i18n-attr` and `data-i18n-html` in `index.html`, which keeps its English for the moment before the script runs. A phrase's markup is limited to `<b>`, `<strong>`, `<i>`, `<em>`, `<kbd>` and `<br>`, built as elements rather than through `innerHTML`; anything else shows as text
  - The language is the one chosen in View › Language, else the computer's language when there is a phrase list for it, else English. A phrase another language hasn't translated shows in English. The Language menu appears only once there is a second language; a choice is remembered on the device and takes effect at once, without reloading
  - `python3 tools/locales.py` turns the phrase lists into `web/locales.js` (a test fails if it is out of date); `python3 tools/i18n_check.py` lists phrases the code uses that are missing, phrases nothing uses, English written straight into a script message, and placeholder mistakes in a translation
  - `?lang=pseudo` in the address shows every phrase accented and about a third longer (`[Ëxpört àš PÐF ·····]`), to find words not yet in the phrase list and layouts that break with longer words. The tests use it on every screen of the editor, at 1024 px and on a phone
  - Not yet translatable: the starter templates, the sample album, the tutorial pictures and the calibration page (page content, to be translated with each language's catalogue numbering), key names in Keyboard shortcuts, and the server's error messages

### Changed
- **File and Help menus; the left panel holds only things to add** (UI review item 6):
  - **File › Open recent** lists the ten newest saved albums, and **File › Manage saved albums…** opens or deletes any of them (deleting asks first; deleting the open album leaves it on screen, marked Not saved). They replace the Files list and its New album button in the left panel; File › New album stays.
  - **Help** is a menu: Show the tutorial, Keyboard shortcuts (still on the ? key) and Print calibration page… (moved from View and File). The separate Help button on the bar is gone.
  - Opening an album from Open recent, Saved albums or File › Open… (and ⌘O) now asks first when the open album has unsaved changes; the Files list replaced it without asking.
  - **Images** lists the images the open album uses, on any page, instead of every image ever uploaded. A new album says "Attach an image to place it on the page." **Attach image…** places the image on the current page, centred, selected and at its own shape; a thumbnail adds another copy. The × on thumbnails is gone (it deleted the file, which other albums may use): delete an image on the page instead, and Undo brings it back. An image whose file is missing says "Image not found".
  - Images are placed without a frame, as they print. Exports from the editor drew a thin frame round an image that the editor showed only as a grey line and that disappeared once the album was saved and reopened.
  - The right panel shows only fields that change the page: an image has no Label, Font or Size (they were never drawn) and names its file instead; a free shape keeps its Label (its caption) but not Font or Size; "Mark as heading" explains itself on its own line ("A heading is drawn in the album's theme colour.") instead of a stray "theme colour" beside the box.
  - Attaching a different image with a name already used saves it as "scan-2.jpg" instead of replacing the other album's image; attaching the same image again reuses its file. Uploaded names can no longer point outside the images folder.
- **Album and page settings in the right panel** (UI review item 5): with nothing selected, the right panel shows **Album and page**: Paper (opens Page setup), Page border, Theme, Headings and Snap, each with its note in words instead of a tooltip, where it used to say only "Select an element to edit". Click a stamp or text and the panel changes to it; Escape, undo, a page switch or opening a file bring the settings back. The bar above the page keeps only the pages and the selected item's tools, in one row on a laptop with or without a selection, so selecting no longer shrinks the page: the whole page fits at about 107% on a 14-inch MacBook (was 100%), 96% at 1440 × 900 (was 89%). Where that bar is narrow, the selected item's actions show as icons with their names spoken. On a phone the bar is one row instead of four, and the panel puts each name above its field. Page setup is still in the File menu while something is selected. The panel's heading names what it shows: Album and page, Stamp, Text, Image or Free shape
- **Plain names for a stamp's caption** (UI review B2): Properties for a stamp is Position and size, Frame, then **Caption**, with **Heading** (above the stamp) and **Name** (below it; it was "Label", with "Description" as its hint, the word that belongs to the paragraph text item). **Value**, **Condition**, **Perforation** and **Catalogue no.** are under **More details (optional)**, folded unless one is filled in, with a count of those filled in and a note that an empty field leaves nothing on the page. The fields have no placeholders (they were cut off and pale). Condition names its short forms ("Mint NH (never hinged)"). These are names on screen only: the file, the DSL and the exports are unchanged. Text items keep Text, Font, Size and Mark as heading; free shapes and pictures keep Label
- **Text items in the palette** say what they are for: **Heading** (16 pt, a page or section heading), **Label** (12 pt, a title above a paragraph) and **Description** (10 pt, a paragraph on what the page shows), in that order, without the font codes ("Label — HN 12pt"). Each is announced as "Add Heading" and so on, with its line read as its description
- Keyboard shortcuts: a long key name ("Ctrl+wheel") keeps its width instead of running into the words beside it
- The Exhibition page template's stamps are captioned "Name" instead of "Description"; a test keeps "Description" off every template's stamps. The tutorial's second and third steps describe Caption, Name and More details, and the settings in the right panel; their pictures, step 4's and the README screenshot are regenerated
- **Easier to read and to operate** (UI review items 4 and 9, first part), for collectors who find small grey text hard to read:
  - Text in the panels, menus and dialogs is 16 px, notes 14 px, and nothing is smaller (labels and section names were 11 to 13 px). Section names are bold ordinary letters instead of small grey capitals. Grey text has 10:1 contrast (was 6.3:1), and greyed-out buttons such as Redo stay readable at 5:1 (were about 2:1), with a dashed edge so they read as unavailable without relying on colour
  - Buttons and fields are at least 40 px tall (were 30 to 34 px); the page buttons are 40 px buttons instead of 14 px dots, and the add button says "Add page"
  - **View › Text size**: Standard, Large (125%) or Extra large (150%), remembered on each computer or phone. It replaces the Large text switch, which was forgotten on every restart. It scales the editor's text, buttons and panels; the album page, its captions and the exports keep their sizes. At Extra large the toolbar may take two rows instead of cutting anything off
  - One set of line icons replaces the emoji and the filled shape symbols (in the palette, the side panels, the file and image lists, the preview and the dialogs). Help has its word beside its icon like the other toolbar buttons. Red is kept for Export, the selection and the current page; the keyboard focus ring is blue, so it never reads as a selection
  - The app name, the welcome screen and dialog titles use the bundled Source Serif 4. "Not saved" shows in words beside the file name (it was a ● before the name)
  - The cost: the side panels are about 40 px wider each, and the bar above the page takes two rows on a laptop, so the whole page fits at about 100% on a 14-inch MacBook (was 109%) until item 5 moves the page settings out of that bar. On a phone that bar takes four rows instead of three until item 7 gives the phone its own layout
- **No copied catalogue numbers**: the first-run sample page, the Single stamp template, `assets/templates/sample_album.txt` and the example in `docs/DSL_SPEC.md` no longer carry StampWorld's numbers, which had been copied without permission. The app ships no catalogue's numbering; collectors add their own. The sample page's captions now give the year, the stamp's name and its condition only ("1840 / Penny Black / Used"): the stamp shows its value, and an imperforate stamp has no perforation to note. The Single stamp template shows the "Cat. no." placeholder like the other templates. A test fails if StampWorld text returns to the app, its assets or its docs. Tutorial pictures and the README screenshot regenerated
- **The page is bigger on a computer**: the editor now opens at **Fit whole page** on a computer, so all of the page is on screen, and the fits may enlarge the page up to 200% (they used to stop at 100%, leaving A4 525 px wide on any screen). A4 shows at about 109% on a 14-inch MacBook, 127% on a 16-inch and 171% on a 2560 × 1440 display. Phones and windows narrower than 700 px still open at Fit width. A zoom chosen in the View menu is still remembered on the device and wins over the default. Ctrl/⌘ + 0 and the status bar's percentage go back to the default fit. Only the drawing is scaled: positions, files and exports are unchanged
- **A quieter grid**: at rest the snap grid is a faint dot at each snap point, so the stamps and captions no longer compete with lines across the whole page. The lines come back while an item is dragged or resized, or a palette item is dragged over the page. Dots and lines keep their size on screen at any zoom, and the grid now lies on the snap points (multiples of 5 or 10 mm from the page's top left; the lines used to be half a step off). Snap Off still hides it, and it is never printed or exported
- On a phone, longer words no longer push the Export button off the screen: the app name gives way first. The status bar keeps to one line, shortening the selection with "…"; on a phone it leaves out the element count and the alignment readout, which had already pushed "Unsaved" past the edge of the screen in English
- Dependabot updates Python packages with its `uv` support, so `pyproject.toml` and `uv.lock` change together; the template's npm and Docker entries, for files this repository doesn't have, are removed

### Removed
- **CSV and Excel import**: it added rows to a hidden stamp list (`collection.json`) that nothing in the editor showed or placed on a page. Removed with the stamp-list server routes (`/api/stamps…`), `collection.py`, their tests and the `openpyxl` dependency. An existing `collection.json` is left where it is. Filling pages from a spreadsheet is on the ideas list.

### Fixed
- **Unsaved work from last time is shown when the editor opens.** It was loaded but not drawn: the page looked blank while the status bar counted the old items, adding a stamp brought them all back, and undo went back to the old work instead of a blank page. Now the old work is drawn at once and marked Not saved, with a note above the page: "This is the album you were working on last time. It has not been saved yet.", **Keep working on it** or **Start a new album** (which asks before discarding it). The note goes when the album is saved, another is opened or a new one started. Undo stops at the restored work

## [0.3.1] - 2026-10-14

Adds a print calibration page, and releases are now published from a tag.

### Known issues
- The macOS app and the Windows folder are not signed, so macOS and Windows warn the first time they are opened (on a Mac: right-click › Open; on Windows: More info › Run anyway)
- The macOS app is built for Apple silicon only
- The Windows app is built and checked in CI but has not been tried by hand
- The launch scripts in `launcher/` have not been tested for this release
- Dependency licences have not been audited

### Added
- **Print calibration page** (File › Print calibration page…): a one-page PDF to print at 100% and measure, to check that the printer prints 1 mm as 1 mm. It has a ruler across and a ruler down the page with 1 mm ticks, a 100 mm square (50 mm on A5), corner marks 5 mm and 10 mm from each edge that show the printer's unprintable margin, and three Penny Black-size stamps (19 × 22 mm) with the Thin, Medium and Double frames and their captions, drawn by the same code as the PDF export. The paper size (A3, A4, A5, Letter or Legal) starts as the album's. There is no correction factor: a page that measures wrong needs the print dialog's scaling changed. Served at `/calibration.pdf?paper=a4` (`engines/calibration.py`)
- **Releases from a tag**: pushing a `v*` tag now builds the macOS app and the Windows folder, checks them as before, and publishes a GitHub release with both zips attached. The notes are that version's section of this changelog (`tools/release_notes.py`), after a short Downloads section; 0.x versions go out as pre-releases. A tag whose version has no changelog section fails the release

## [0.3.0] - 2026-10-14

The editor is now the web app only, with app builds for macOS and Windows, exhibition-style stamp frames and captions, themes and page borders, and exports that match the editor.

### Known issues
- The macOS app and the Windows folder are not signed, so macOS and Windows warn the first time they are opened (on a Mac: right-click › Open; on Windows: More info › Run anyway)
- The macOS app is built for Apple silicon only
- The Windows app is built and checked in CI but has not been tried by hand
- The launch scripts in `launcher/` have not been tested for this release
- Dependency licences have not been audited

### Added
- **Acknowledgements** in the README: the page-description language follows AlbumEasy's command syntax, by Clive Levinson. The sample album (`assets/templates/sample_album.txt`), the example in `docs/DSL_SPEC.md` and a parser test now use new Great Britain 1840 to 1841 pages, the same stamps as the first-run sample, in place of an example adapted from AlbumEasy's own sample album
- **App build for macOS and Windows** (pending item 11): one PyInstaller spec, `packaging/stamp_album.spec`, builds the current app: the web editor in its own window (pywebview), with the editor files, caption fonts and every module it needs. Opened with no arguments, the built app opens its own window, and it falls back to the browser if the window can't open; `--cli` and `--web` work as from source. `make app` (or `./build.sh`) builds, checks and zips the macOS app. A new **App build** workflow builds the macOS app and a zipped Windows folder on GitHub, runs each built app (`packaging/smoke_test.py`: a CLI PDF, then the editor page, fonts and PDF/PNG exports from the built server), and keeps both zips as artifacts; it runs when packaging or start-up code changes, or on demand. The apps are not signed yet. `docs/BUILD.md` is rewritten for the current app
- **Pinch to zoom** (pending item 15): two fingers on the page zoom it in or out, from 25% to 400%, keeping the part of the page between the fingers under them; moving both fingers also pans. Only the canvas area stops the browser's own pinch, so iOS no longer zooms the whole app there, and the toolbar, panels and dialogs can still be zoomed for accessibility. A second finger during a stamp drag puts the stamp back where it was (no undo step) and pinches instead. On a desktop the same zoom comes from a trackpad pinch (including Safari and the Mac app), Ctrl/⌘ + scroll wheel at the pointer, Ctrl/⌘ + = and − (also View › Zoom in and Zoom out) and Ctrl/⌘ + 0 for Fit width. Near 100% it snaps to exactly 100%. A pinched zoom shows its percentage in the status bar, which goes back to Fit width when tapped; it lasts for the session only, and the next start uses the last fit mode
- **Zoom to fit** (pending item 5): on a phone, or any window too narrow for the page, the page is shrunk to fit the width of the canvas area, so all of it is on screen. View › **Fit width** (the default), **Fit whole page** and **Actual size (100%)** choose the zoom, and the status bar's percentage is a button that switches between Fit width and 100%. The fits never enlarge the page past 100%, so a wide window looks as before. The page refits when the window is resized, the phone is rotated, a side panel opens or closes, or the paper size changes. The choice is remembered on the device, not in the album. Zoom only changes how the page is shown: positions, sizes, saved files and exports are the same at every zoom. Resize handles and "!" badges keep their size on screen, and on a touch screen each handle has a 24 px touch area
- **Bold or Semibold caption headings**: a **Headings** choice in the page bar, beside Theme, sets the weight of the headings above every stamp in the album. Bold is the default; Semibold is saved as a `CAPTION_HEADING("semibold")` line (Bold albums are saved as before). Changing it is one undo step and is kept in the draft, the preview and every export
- **Fit prompt for old albums**: opening an album (File › Open or the Saved files list) whose stamps, text or pictures sit past any edge of the page asks "Move inside" or "Leave as they are". Nothing moves unless you choose to; moving uses Page setup's fit (same 15 mm margin, the arrangement kept, sizes never changed) and is one undo step, back to the album as opened. Leaving it asks again the next time the album is opened. Templates, the wizard, the tutorial sample and DSL Apply don't ask. Only the stamp box counts; frames and captions over the border keep their amber "!" badge
- **Test failures as CI annotations**: on GitHub Actions, each failed test, setup or teardown error and collection error is reported as an annotation on the job, with the test's name, where it failed and pytest's `E` lines (at most 10 per job, as GitHub allows; a 10th lists any others). Annotations can be read through the GitHub API, which job logs can't from a cloud session, and they also appear next to the code in a pull request. A pytest plugin in the test folder (`src/tests/gh_annotations.py`); local runs are unchanged
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
- **Lint clean-up, part C3, and lint now required** (pending item 11): the last 53 over-long lines are wrapped (E501), in the HTML and SVG exporters, the parser, the models, cloud sync and the command line's help, the same way as before. Three CSS rules in the HTML export now span two lines each, which changes only whitespace in the exported file (its test snapshot is updated). Ruff now finds nothing, so CI's ruff step no longer ignores failures: it runs after the tests on every runner, fails the job on any finding, and reports each finding as an annotation on the line. No change in behaviour. Ruff findings: 53 → 0
- **Lint clean-up, part C2** (pending item 11): the 23 over-long lines in `api.py` are wrapped (E501), the same way as the tests. Three CSS rules in the HTML gallery export now span two lines each, which changes only whitespace in the exported file. No change in behaviour. Ruff findings: 76 → 53
- **Lint clean-up, part C1** (pending item 11): the 88 over-long lines in the tests are wrapped (E501). Calls and literals were rewrapped with Black on just those lines; long strings are split into adjacent pieces, which Python joins back into the same value, and a few JavaScript snippets passed to the browser are broken over lines. No test changed what it checks. Ruff findings: 164 → 76
- **Lint clean-up, part B** (pending item 11): the findings ruff fixes by itself, applied with `ruff check --fix`. Imports are sorted (I001), 18 unused imports are removed (F401; none was used from another module, so nothing relied on them being re-exported), and 7 f-strings without placeholders are plain strings (F541). No change in behaviour. Ruff findings: 208 → 164, all line length (E501)
- **Lint clean-up, part A** (pending item 11): the 14 ruff findings that needed fixing by hand. The `Album` and `Stamp` type hints in `api.py` and `engines/layout.py` now name imported classes (F821); the second, identical `fonts` property in `engines/font_manager.py` is gone (F811); `api.py`'s imports for the collection, WebSocket, version-history and cloud-sync sections moved up to the top of the file (E402), and `import csv, io` is split into two lines (E401). No change in behaviour. Ruff findings: 228 → 208
- **Starter-template polish** (pending item 16). **Single stamp:** its two paragraphs now start at the same left edge and run the same width as on the other templates; "Imperforate" moved from the stamp's caption (where it wrapped onto a line of its own on the 19 mm stamp) into the note below; the cover is larger (140 × 85 mm), and the page now reaches the lower margin instead of stopping two-thirds down. **Set row:** the three sections are spread down the whole page. **Exhibition page:** every stamp and the cover have a heading, not just the first row, and the placeholder descriptions read "Description" instead of the stamp sizes; the cover is 100 × 56 mm to make room. Tests check that no template caption wraps, that text items share one left edge, and that pages of stamps reach the lower part of the page
- **Properties hides Font and Size for stamps** (pending item 13). A stamp's captions always use the caption font at fixed sizes, so the two fields did nothing for a stamp. A short note under the stamp's Label says so and points to Headings above the page for the heading weight. Text items, free shapes and images still show Font and Size. Albums are unchanged: any font or size already stored on a stamp stays in the file
- **Captions are set in Source Serif 4 Caption** (Adobe, SIL Open Font License), bundled with the app in `web/fonts` with its licence: Regular for the description, Italic for the details and catalogue number, Bold or Semibold for the heading. The Caption cut is drawn for small sizes such as the 8 pt captions. It is used whatever the stamp's own font, so the description no longer follows Helvetica, Times or Courier. The PDF embeds it; the SVG export and the HTML preview and export embed only the letters the album uses (a few KB per font); the PNG draws from the bundled files, so a machine's fonts make no difference
- **Captions now wrap the same way in every view** (pending item 6). The editor measured them with the browser's fonts and the exports with PDF metrics, so a line near the frame's width could wrap in one view and not another. Every view now measures with the bundled font's own advance widths, without kerning or ligatures, and draws the text that way too: the exports from `engines/caption_fonts.py`, the editor from `web/caption_metrics.js`, generated from the same files by `tools/caption_metrics.py` (a test fails if it is out of date). The Caption cut is set a little wider than Helvetica, so some captions take one more line than before (in the sample album, "Twopence Blue" on a 19 mm stamp)
- **Starter templates** replaced: the Template Gallery now has four exhibition-style pages, Single stamp, Set row, Title page and Exhibition page, in place of 33 templates that used the old row layout. Those opened as an empty page in the editor and exported with stamps and captions overlapping. The new ones are placed items at their own sizes, with headings, captions and details, inside the 15 mm margins and with nothing running into anything else. A test checks every template with the export engines' frame and caption geometry, exports each to PDF, PNG and SVG, and opens each in the editor to check for "!" badges
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
- **The legacy PyQt6 editor** (pending item 11): the old desktop editor in `stamp_album/ui/` (about 2,500 lines, unmaintained since the web app replaced it) and the `legacy` extra that installed PyQt6 and pytest-qt. `stamp-album --qt` and `--legacy-qt` now print that the editor was removed and exit; `stamp-album` opens the editor as before, and `--desktop` still opens it in its own window
- The second, stale PyInstaller spec (`packaging/stamp-album.spec`)
- The four `.slbum` starter albums in `templates/`, which the app never loaded; the starter templates are now in the Template Gallery
- Columns and Gap controls (albums that use columns keep them when opened and saved), and Distribute and Match size, which always failed because only one stamp can be selected
- Dead `canvas.js` (not loaded) and `events.js` (loaded but never run), both superseded by `render.js` and `init.js`

### Fixed
- The desktop window's start-up error blamed WeasyPrint, Pango and Cairo, which the app no longer uses; it now suggests `stamp-album --web` to see the server's own error
- **Bold and italic page text in the SVG and HTML.** A heading set in Helvetica Bold (such as a template's "Low values" or its page title) was drawn bold in the editor, the PDF and the PNG, but regular in the SVG export, the HTML export and the preview; italic text lost its slant the same way, and the SVG drew every text item in Arial whatever its font. Both now use the text's own family, weight and style, from one table shared with the editor's (`text_layout.css_font`). The SVG also wraps each line with that font's widths, as the PDF does, so a bold line no longer runs past its box
- `/export` with `format: "html"` failed with a 500 error every time ("cannot access local variable 'tempfile'"). The editor's own export uses `/export-from-state` and wasn't affected; the HTML gallery is now tested for each starter template
- An item added after opening an album, a template, the wizard's album, the tutorial sample or a restored draft could take the id of an item already on the page (on first run, the new stamp shared `el1` with the sample's title), so selecting, dragging or deleting it acted on the other item. Loading now moves the id counter past every `el<n>` id on every page (`S.syncNid()`), so new and duplicated items always get an id of their own
- The left side of a page wider than the canvas area could not be scrolled to (about 30 mm of an A4 page on an iPhone): the page was centred with `justify-content: center`, which pushes the overflow off the left edge. It is now centred with auto margins, which leave all of it reachable
- Dragging a stamp with a finger did nothing unless it was already selected: selecting it redraws the page, which removed the element the finger was on, and the rest of the touch then never reached the drag code. The drag now listens on that element for the whole touch. Page items also stop the browser treating a drag on them as a scroll of the canvas (`touch-action: none`); a finger on empty paper still scrolls
- A finger drag snapped to 5 px steps and ignored Snap Off; it now snaps to the grid in mm, as the mouse does
- Elements past the left or top edge of the page (a negative X or Y) were dropped when an album was opened in the editor, so saving it again lost them. The editor's reader now keeps them, as the Python reader already did
- Opening a file now starts a fresh undo history, so Undo can't step back into the album that was open before
- The "page size corrected" message for albums saved by v0.2.0 no longer counts elements past the edge; the fit prompt offers to move them instead
- Lines on the editor's page looked slightly soft: the page is centred and is a fractional number of pixels wide (A4 525 px, Letter 539.75 px), so its left edge often fell between screen pixels (457.5, 450.125 …). The page is now nudged onto whole device pixels whenever the window, a panel or the paper size changes. Its size and the exports are unchanged
- Images other than PNG were served by the app as `image/png`; SVG, JPEG and GIF files now have their own types
- The page-border and theme tests read pixels through a small helper that uses `get_flattened_data` where Pillow has it, since Pillow 14 (October 2027) removes `Image.getdata`. A `getdata` deprecation warning now fails the tests
- A quote typed in a label, description, heading, catalogue number or details line lost the whole stamp when the album was reopened. Every text field is now escaped when saved (quotes, backslashes and new lines) and read back exactly, by both the editor and the Python reader
- The Python reader's quoted-string handling took about 20 seconds on one long hostile line (a regex that was quadratic in the number of `\"`, flagged by CodeQL); it is now a single linear pass
- The Python album writer, used by the server's file routes, now writes items as the editor does: shape names the editor reads (`oval`, `triangle_inverted`), the theme, the page border by name, each stamp's details, text alignment and the heading mark. The Python reader now reads the editor's placed pictures (it stopped with an error) and text alignment, and the inverted triangle no longer reopens as a rectangle
- The DSL editor's CodeMirror is bundled with the app instead of loaded from a CDN, so it works offline and the app's security policy no longer allows any outside source
- The browser tests no longer wait with `wait_for_function("…")`, which the app's security policy blocks; it failed whenever the editor was not ready at once (Windows CI on `main`)
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
