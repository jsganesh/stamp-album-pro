# ruff: noqa: E501  (each DSL command is one line, as the editor writes it)
"""Starter templates for the Template Gallery.

Eight pages, written in the editor's own format (placed items with
``STAMP_ADD_AT`` and ``PAGE_TEXT_AT``, mm from the page's top-left corner), so they
open in the editor and export exactly as shown.

* Stamps are at their own size; the frame adds 1 mm clearance round them.
* Rows are centred across the page and aligned on the frames' bottoms, so captions line up.
* Everything stays inside the 15 mm margins and nothing runs into anything else:
  ``src/tests/test_starter_templates.py`` checks this with the export engines' geometry.

The first four are exhibition-style pages. The other four follow the layouts of the owner's
own AlbumEasy "First Issues" albums (an introduction page; a long set; stamps with pictures
of their overprints; a normal stamp and its varieties), with no country, text or catalogue
numbers taken from them. Their picture spaces are free shapes labelled Map, Flag and so on,
printed as plain boxes until a picture is attached.

Each template has: id, name, description, category, content (the DSL).
"""

TEMPLATES = [
    {
        "id": "single_stamp",
        "name": "Single stamp",
        "description": "One important stamp in the middle of the page, with a note above and below, and room for a cover.",
        "category": "Exhibition",
        "content": r"""ALBUM_PAGES_BORDER(0.5 0 0 1)
ALBUM_PAGES_BORDER_STYLE("solid")
COLOUR_ALBUM_BORDER("#000000")
ALBUM_THEME("exhibition")
ALBUM_TITLE("Single stamp")
ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)
ALBUM_MOUNT(1.5 1)
PAGE_START
PAGE_TEXT_AT(20.0 18.0 170.0 10.0 "HB" 16 "Great Britain: The Penny Black" "center")
PAGE_TEXT_ROLE("heading")
PAGE_TEXT_AT(20.0 29.0 170.0 7.0 "HN" 10 "The world's first adhesive postage stamp, 1840" "center")
PAGE_TEXT_AT(20.0 44.0 170.0 12.0 "HN" 9 "Put one important item at the centre of the page, with a short note on why it matters. Replace this text with your own: what the stamp is, when and how it was printed, and what makes this example worth showing." "left")
STAMP_ADD_AT(95.5 84.0 19.0 22.0 "Penny Black" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "1840")
STAMP_DETAILS("" "Used" "")
PAGE_TEXT_AT(20.0 134.0 170.0 11.0 "HN" 9 "Issued on 6 May 1840, printed imperforate in sheets of 240 by Perkins, Bacon & Petch. The check letters in the lower corners give each stamp's position in the sheet." "left")
STAMP_ADD_AT(35.0 174.0 140.0 85.0 "Penny Black on cover" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Use on cover")
STAMP_DETAILS("" "Posted" "")
""",
    },
    {
        "id": "set_row",
        "name": "Set row",
        "description": "A set laid out in rows by value, low values then high values, with a row for shades and varieties.",
        "category": "Exhibition",
        "content": r"""ALBUM_PAGES_BORDER(0.5 0 0 1)
ALBUM_PAGES_BORDER_STYLE("solid")
COLOUR_ALBUM_BORDER("#000000")
ALBUM_THEME("exhibition")
ALBUM_TITLE("Set row")
ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)
ALBUM_MOUNT(1.5 1)
PAGE_START
PAGE_TEXT_AT(20.0 18.0 170.0 10.0 "HB" 16 "Set title, year of issue" "center")
PAGE_TEXT_ROLE("heading")
PAGE_TEXT_AT(20.0 29.0 170.0 7.0 "HN" 10 "Printer · printing method · perforation" "center")
PAGE_TEXT_AT(20.0 48.0 170.0 8.0 "HB" 11 "Low values" "left")
STAMP_ADD_AT(31.7 66.0 19.0 22.0 "Value 1" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Unused" "")
STAMP_ADD_AT(63.6 66.0 19.0 22.0 "Value 2" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Unused" "")
STAMP_ADD_AT(95.5 66.0 19.0 22.0 "Value 3" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Unused" "")
STAMP_ADD_AT(127.4 66.0 19.0 22.0 "Value 4" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Unused" "")
STAMP_ADD_AT(159.3 66.0 19.0 22.0 "Value 5" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Unused" "")
PAGE_TEXT_AT(20.0 130.0 170.0 8.0 "HB" 11 "High values" "left")
STAMP_ADD_AT(34.9 148.0 36.0 25.0 "Value 6" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Unused" "")
STAMP_ADD_AT(87.0 148.0 36.0 25.0 "Value 7" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Unused" "")
STAMP_ADD_AT(139.1 148.0 36.0 25.0 "Value 8" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Unused" "")
PAGE_TEXT_AT(20.0 215.0 170.0 8.0 "HB" 11 "Shades and varieties" "left")
STAMP_ADD_AT(38.1 233.0 19.0 22.0 "Shade 1" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(76.4 233.0 19.0 22.0 "Shade 2" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(114.6 233.0 19.0 22.0 "Shade 3" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(152.9 233.0 19.0 22.0 "Shade 4" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
""",
    },
    {
        "id": "title_page",
        "name": "Title page",
        "description": "The first page of an exhibit: title, introduction, plan, important items, research and references.",
        "category": "Exhibition",
        "content": r"""ALBUM_PAGES_BORDER(0.5 0 0 1)
ALBUM_PAGES_BORDER_STYLE("solid")
COLOUR_ALBUM_BORDER("#000000")
ALBUM_THEME("exhibition")
ALBUM_TITLE("Title page")
ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)
ALBUM_MOUNT(1.5 1)
PAGE_START
PAGE_TEXT_AT(20.0 48.0 170.0 13.0 "HB" 22 "Exhibit Title" "center")
PAGE_TEXT_ROLE("heading")
PAGE_TEXT_AT(20.0 62.0 170.0 8.0 "HN" 11 "A traditional exhibit by Your Name" "center")
PAGE_TEXT_AT(20.0 91.0 170.0 8.0 "HB" 11 "Introduction" "left")
PAGE_TEXT_AT(20.0 100.0 170.0 12.0 "HN" 10 "Say in a few sentences what the exhibit shows and why it is worth showing: the subject, the period it covers, and what the viewer should take away from it." "left")
PAGE_TEXT_AT(20.0 123.0 170.0 8.0 "HB" 11 "Plan of the exhibit" "left")
PAGE_TEXT_AT(20.0 132.0 170.0 21.0 "HN" 10 "1. First chapter · pages 1 to 4\n2. Second chapter · pages 5 to 8\n3. Third chapter · pages 9 to 12\n4. Fourth chapter · pages 13 to 16" "left")
PAGE_TEXT_AT(20.0 164.0 170.0 8.0 "HB" 11 "Important items" "left")
PAGE_TEXT_AT(20.0 173.0 170.0 7.0 "HN" 10 "Mark the key items in the exhibit, for example with a thin frame on their pages, and list them here." "left")
PAGE_TEXT_AT(20.0 191.0 170.0 8.0 "HB" 11 "Research" "left")
PAGE_TEXT_AT(20.0 200.0 170.0 7.0 "HN" 10 "Note any original research or new findings the exhibit presents." "left")
PAGE_TEXT_AT(20.0 218.0 170.0 8.0 "HB" 11 "References" "left")
PAGE_TEXT_AT(20.0 227.0 170.0 7.0 "HN" 10 "List the catalogues, handbooks and articles you used." "left")
""",
    },
    {
        "id": "exhibition_page",
        "name": "Exhibition page",
        "description": "A chapter page: heading, a short explanation, two rows of stamps of mixed sizes and a cover, each with a heading.",
        "category": "Exhibition",
        "content": r"""ALBUM_PAGES_BORDER(0.5 0 0 1)
ALBUM_PAGES_BORDER_STYLE("solid")
COLOUR_ALBUM_BORDER("#000000")
ALBUM_THEME("exhibition")
ALBUM_TITLE("Exhibition page")
ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)
ALBUM_MOUNT(1.5 1)
PAGE_START
PAGE_TEXT_AT(20.0 18.0 170.0 10.0 "HB" 16 "Chapter title" "center")
PAGE_TEXT_ROLE("heading")
PAGE_TEXT_AT(20.0 29.0 170.0 8.0 "HN" 11 "Section title" "center")
PAGE_TEXT_AT(20.0 41.0 170.0 11.0 "HN" 9 "A short explanation of what this page shows. Keep it brief: a sentence or two on the issue, then let the stamps and their captions do the rest." "left")
STAMP_ADD_AT(39.4 72.0 25.0 30.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Heading")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(85.0 72.0 40.0 30.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Heading")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(145.6 72.0 25.0 30.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Heading")
STAMP_DETAILS("Value" "Used" "")
PAGE_TEXT_AT(20.0 124.0 170.0 7.0 "HN" 9 "A second group, for example a later printing or a variety." "left")
STAMP_ADD_AT(31.3 143.0 36.0 25.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Heading")
STAMP_DETAILS("Value" "Unused" "")
STAMP_ADD_AT(79.8 146.0 19.0 22.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Heading")
STAMP_DETAILS("Value" "Unused" "")
STAMP_ADD_AT(111.2 146.0 19.0 22.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Heading")
STAMP_DETAILS("Value" "Unused" "")
STAMP_ADD_AT(142.7 143.0 36.0 25.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Heading")
STAMP_DETAILS("Value" "Unused" "")
PAGE_TEXT_AT(20.0 190.0 170.0 7.0 "HN" 9 "A cover or a block, to show the stamps in use." "left")
STAMP_ADD_AT(55.0 208.0 100.0 56.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Heading")
STAMP_DETAILS("Value" "Posted" "")
""",
    },
    {
        "id": "introduction_page",
        "name": "Introduction page",
        "description": "The first page of a country: its map, coat of arms and flag, a short note on its postal history, then the first issue in rows.",
        "category": "Album",
        "content": r"""ALBUM_PAGES_BORDER(0.5 0 0 1)
ALBUM_PAGES_BORDER_STYLE("solid")
COLOUR_ALBUM_BORDER("#000000")
ALBUM_THEME("exhibition")
ALBUM_TITLE("Introduction page")
ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)
ALBUM_MOUNT(1.5 1)
PAGE_START
PAGE_TEXT_AT(20.0 18.0 170.0 10.0 "HB" 16 "Country: first issues" "center")
PAGE_TEXT_ROLE("heading")
STAMP_ADD_AT(37.5 36.0 40.0 30.0 "Map" "freehand" "" "" freehand "solid" "#000000" 0.5 "#FEFEFE" 100)
STAMP_ADD_AT(89.5 36.0 26.0 30.0 "Coat of arms" "freehand" "" "" freehand "solid" "#000000" 0.5 "#FEFEFE" 100)
STAMP_ADD_AT(127.5 36.0 45.0 30.0 "Flag" "freehand" "" "" freehand "solid" "#000000" 0.5 "#FEFEFE" 100)
PAGE_TEXT_AT(20.0 79.8 170.0 25.0 "HN" 10 "Two or three sentences on the country, then the postal history: when the first post office opened, what was used before the first stamps, and why this issue came about." "left")
PAGE_TEXT_AT(20.0 112.8 170.0 8.0 "HB" 11 "First issue, year" "center")
PAGE_TEXT_AT(20.0 121.8 170.0 7.0 "HN" 9 "Printer · watermark · perforation · date of issue" "center")
STAMP_ADD_AT(28.6 135.4 20.0 24.0 "Value 1" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(61.8 135.4 20.0 24.0 "Value 2" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(95.0 135.4 20.0 24.0 "Value 3" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(128.2 135.4 20.0 24.0 "Value 4" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(161.4 135.4 20.0 24.0 "Value 5" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(28.6 183.7 20.0 24.0 "Value 6" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(61.8 183.7 20.0 24.0 "Value 7" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(95.0 183.7 20.0 24.0 "Value 8" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(128.2 183.7 20.0 24.0 "Value 9" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(161.4 183.7 20.0 24.0 "Value 10" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(30.3 232.0 41.0 26.0 "Value 11" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(84.5 232.0 41.0 26.0 "Value 12" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(138.7 232.0 41.0 26.0 "Value 13" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
""",
    },
    {
        "id": "long_set",
        "name": "Long set",
        "description": "A long set in rows of five, low values first, then the high values in a larger size, each group with its own heading.",
        "category": "Album",
        "content": r"""ALBUM_PAGES_BORDER(0.5 0 0 1)
ALBUM_PAGES_BORDER_STYLE("solid")
COLOUR_ALBUM_BORDER("#000000")
ALBUM_THEME("exhibition")
ALBUM_TITLE("Long set")
ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)
ALBUM_MOUNT(1.5 1)
PAGE_START
PAGE_TEXT_AT(20.0 18.0 170.0 10.0 "HB" 16 "Set title, year of issue" "center")
PAGE_TEXT_ROLE("heading")
PAGE_TEXT_AT(20.0 34.0 170.0 8.0 "HB" 11 "Low values" "center")
PAGE_TEXT_AT(20.0 43.0 170.0 7.0 "HN" 9 "Printer · watermark · perforation" "center")
STAMP_ADD_AT(28.6 56.6 20.0 24.0 "Value 1" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(61.8 56.6 20.0 24.0 "Value 2" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(95.0 56.6 20.0 24.0 "Value 3" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(128.2 56.6 20.0 24.0 "Value 4" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(161.4 56.6 20.0 24.0 "Value 5" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(28.6 104.9 20.0 24.0 "Value 6" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(61.8 104.9 20.0 24.0 "Value 7" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(95.0 104.9 20.0 24.0 "Value 8" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(128.2 104.9 20.0 24.0 "Value 9" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(161.4 104.9 20.0 24.0 "Value 10" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(28.6 153.2 20.0 24.0 "Value 11" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(61.8 153.2 20.0 24.0 "Value 12" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(95.0 153.2 20.0 24.0 "Value 13" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(128.2 153.2 20.0 24.0 "Value 14" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(161.4 153.2 20.0 24.0 "Value 15" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
PAGE_TEXT_AT(20.0 202.9 170.0 8.0 "HB" 11 "High values" "center")
PAGE_TEXT_AT(20.0 211.9 170.0 7.0 "HN" 9 "Printer · watermark · perforation" "center")
STAMP_ADD_AT(30.3 225.5 41.0 26.0 "Value 16" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(84.5 225.5 41.0 26.0 "Value 17" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(138.7 225.5 41.0 26.0 "Value 18" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
""",
    },
    {
        "id": "stamps_with_illustrations",
        "name": "Stamps with illustrations",
        "description": "Pictures of the overprint types above the stamps they explain, then a second printing with its own picture.",
        "category": "Album",
        "content": r"""ALBUM_PAGES_BORDER(0.5 0 0 1)
ALBUM_PAGES_BORDER_STYLE("solid")
COLOUR_ALBUM_BORDER("#000000")
ALBUM_THEME("exhibition")
ALBUM_TITLE("Stamps with illustrations")
ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)
ALBUM_MOUNT(1.5 1)
PAGE_START
PAGE_TEXT_AT(20.0 18.0 170.0 10.0 "HB" 16 "Issue title, year" "center")
PAGE_TEXT_ROLE("heading")
PAGE_TEXT_AT(20.0 29.0 170.0 7.0 "HN" 9 "Printer · watermark · perforation" "center")
STAMP_ADD_AT(45.0 44.0 50.0 22.0 "Overprint type 1" "freehand" "" "" freehand "solid" "#000000" 0.5 "#FEFEFE" 100)
STAMP_ADD_AT(115.0 44.0 50.0 22.0 "Overprint type 2" "freehand" "" "" freehand "solid" "#000000" 0.5 "#FEFEFE" 100)
STAMP_ADD_AT(40.8 82.4 34.0 28.0 "Value 1" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(88.0 82.4 34.0 28.0 "Value 2" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(135.2 82.4 34.0 28.0 "Value 3" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(40.8 134.7 34.0 28.0 "Value 4" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(88.0 134.7 34.0 28.0 "Value 5" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(135.2 134.7 34.0 28.0 "Value 6" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
PAGE_TEXT_AT(20.0 186.4 170.0 8.0 "HB" 11 "Second printing" "center")
STAMP_ADD_AT(80.0 198.4 50.0 22.0 "Overprint detail" "freehand" "" "" freehand "solid" "#000000" 0.5 "#FEFEFE" 100)
STAMP_ADD_AT(40.8 236.8 34.0 28.0 "Value 7" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(88.0 236.8 34.0 28.0 "Value 8" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(135.2 236.8 34.0 28.0 "Value 9" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_DETAILS("Value" "Used" "")
""",
    },
    {
        "id": "normal_and_varieties",
        "name": "Normal and varieties",
        "description": "Three values, each in a row: the normal stamp, then its shade, paper, watermark and perforation varieties, each named above it.",
        "category": "Album",
        "content": r"""ALBUM_PAGES_BORDER(0.5 0 0 1)
ALBUM_PAGES_BORDER_STYLE("solid")
COLOUR_ALBUM_BORDER("#000000")
ALBUM_THEME("exhibition")
ALBUM_TITLE("Normal and varieties")
ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)
ALBUM_MOUNT(1.5 1)
PAGE_START
PAGE_TEXT_AT(20.0 18.0 170.0 10.0 "HB" 16 "Issue title, year" "center")
PAGE_TEXT_ROLE("heading")
PAGE_TEXT_AT(20.0 29.0 170.0 7.0 "HN" 9 "Printer · watermark · perforation" "center")
PAGE_TEXT_AT(20.0 46.0 170.0 8.0 "HB" 11 "First value" "center")
STAMP_ADD_AT(21.1 64.6 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Normal")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(57.3 64.6 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Shade")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(93.5 64.6 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Paper")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(129.7 64.6 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Watermark")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(165.9 64.6 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Perforation")
STAMP_DETAILS("Value" "Used" "")
PAGE_TEXT_AT(20.0 124.3 170.0 8.0 "HB" 11 "Second value" "center")
STAMP_ADD_AT(21.1 142.9 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Normal")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(57.3 142.9 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Shade")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(93.5 142.9 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Paper")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(129.7 142.9 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Watermark")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(165.9 142.9 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Perforation")
STAMP_DETAILS("Value" "Used" "")
PAGE_TEXT_AT(20.0 202.6 170.0 8.0 "HB" 11 "Third value" "center")
STAMP_ADD_AT(21.1 221.2 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Normal")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(57.3 221.2 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Shade")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(93.5 221.2 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Paper")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(129.7 221.2 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Watermark")
STAMP_DETAILS("Value" "Used" "")
STAMP_ADD_AT(165.9 221.2 23.0 28.0 "Name" "Cat. no." "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)
STAMP_HEADING("HN" 9 "Perforation")
STAMP_DETAILS("Value" "Used" "")
""",
    },
]
