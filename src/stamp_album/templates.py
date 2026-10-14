# ruff: noqa: E501  (each DSL command is one line, as the editor writes it)
"""Starter templates for the Template Gallery.

Four exhibition-style pages, written in the editor's own format (placed items with
``STAMP_ADD_AT`` and ``PAGE_TEXT_AT``, mm from the page's top-left corner), so they
open in the editor and export exactly as shown.

* Stamps are at their own size; the frame adds 1 mm clearance round them.
* Rows are centred across the page and aligned on the frames' bottoms, so captions line up.
* Everything stays inside the 15 mm margins and nothing runs into anything else:
  ``src/tests/test_starter_templates.py`` checks this with the export engines' geometry.

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
]
