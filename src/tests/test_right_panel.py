# ruff: noqa: F811
"""The right panel (UI review B2 and item 5).

With nothing selected the right panel holds the album and page settings: paper,
page border, theme, headings and snap. The bar above the page keeps the pages and
the selected item's tools, in one row, so selecting never shrinks the page.

A stamp's caption fields are Heading and Name ("Description" is the paragraph text
item); Value, Condition, Perforation and Catalogue no. are under "More details
(optional)", folded unless one is filled in, with no placeholders. The palette's text
items are Heading, Label and Description, each with its size and what it is for, and
no font codes. All renames are on screen only: the file keeps its words.
"""

import re

from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)

SETTINGS = ["#btn-page-setup", "#def-bdr", "#def-theme", "#def-heading", "#grid"]


def _stamp(page, **fields):
    """Select the first stamp, after setting any of its fields (denom, cond, perf, cat)."""
    return page.evaluate(
        """(f) => { const el = StampAlbum.E.find(e => e.t === 'stamp')
                 || (StampAlbum.add({ t: 'stamp', s: 'rectangle', x: 100, y: 100, w: 50, h: 60,
                                      lbl: 'Penny Black' }), StampAlbum.E[StampAlbum.E.length - 1]);
                 ['denom', 'cond', 'perf', 'cat'].forEach(k => { el[k] = f[k] || ''; });
                 StampAlbum.select(null); StampAlbum.select(el.id); return el.id; }""",
        fields,
    )


def _text(page):
    return page.evaluate(
        """() => { StampAlbum.add({ t: 'text', x: 50, y: 50, w: 300, h: 45, lbl: 'Notes',
                                    font: 'HN', fs: 10 });
                   const el = StampAlbum.E[StampAlbum.E.length - 1];
                   StampAlbum.select(el.id); return el.id; }"""
    )


def _visible_labels(page, root):
    return page.evaluate(
        f"""[...document.querySelectorAll('{root} label')]
            .filter(l => l.getClientRects().length).map(l => l.textContent.trim())"""
    )


# ── Nothing selected: the album and page settings ──

def test_nothing_selected_shows_the_album_settings(page):
    page.evaluate("StampAlbum.select(null)")
    assert page.inner_text("#rp-title") == "Album and page"
    for sel in SETTINGS:
        assert page.is_visible(sel), sel
        assert page.evaluate(f"!!document.querySelector('#rp {sel}')"), f"{sel} is in the panel"
    assert "Select an element to edit" not in page.inner_text("#rp")
    assert page.is_hidden("#rp-content")


def test_page_bar_holds_only_pages_and_selection_tools(page):
    for sel in SETTINGS:
        assert not page.evaluate(f"!!document.querySelector('#ca-toolbar {sel}')"), sel
    assert page.locator("#ca-toolbar select, #ca-toolbar label").count() == 0


def test_settings_still_change_the_album(page):
    page.evaluate("StampAlbum.select(null)")
    page.select_option("#def-theme", "green")
    page.select_option("#def-bdr", "double")
    assert page.evaluate("[StampAlbum._theme, StampAlbum._pageBorder]") == ["green", "double"]
    page.click("#btn-page-setup")
    assert page.is_visible("#page-setup-overlay")


def test_panel_goes_back_to_settings_whatever_clears_the_selection(page):
    """Escape, undo and a page switch clear the selection without select(null)."""
    _stamp(page)
    assert page.is_hidden("#rp-none")
    page.focus("#page")
    page.keyboard.press("Escape")
    assert page.is_visible("#def-theme") and page.inner_text("#rp-title") == "Album and page"
    _stamp(page)
    page.evaluate("StampAlbum.switchPage(0, true)")
    assert page.is_visible("#def-theme")


def test_selecting_keeps_the_page_bar_one_row_and_the_page_size(page):
    page.set_viewport_size({"width": 1512, "height": 982})  # a 14-inch MacBook
    page.evaluate("StampAlbum.setZoomMode('fit-page')")
    page.evaluate("StampAlbum.select(null)")
    page.wait_for_timeout(300)
    bar = page.evaluate("document.getElementById('ca-toolbar').getBoundingClientRect().height")
    zoom = page.evaluate("StampAlbum.zoom")
    _stamp(page)
    page.wait_for_timeout(300)
    assert page.is_visible("#sel-tools")
    assert abs(page.evaluate(
        "document.getElementById('ca-toolbar').getBoundingClientRect().height") - bar) <= 2
    assert bar < 64, f"the page bar is {bar} px: more than one row"
    assert abs(page.evaluate("StampAlbum.zoom") - zoom) < 0.005, "selecting shrank the page"


def test_page_bar_is_one_row_at_1280(page):
    page.set_viewport_size({"width": 1280, "height": 800})
    _stamp(page)
    page.wait_for_timeout(300)
    bar = page.evaluate("document.getElementById('ca-toolbar').getBoundingClientRect().height")
    assert bar < 64, f"the page bar is {bar} px: more than one row"


# ── A stamp: Position and size, Frame, Caption, More details ──

def test_stamp_panel_sections_and_names(page):
    _stamp(page)
    assert page.inner_text("#rp-title") == "Stamp"
    secs = page.evaluate("""[...document.querySelectorAll('#rp-content .rp-sec')]
        .filter(h => h.getClientRects().length).map(h => h.textContent.trim())""")
    assert secs == ["Position and size", "Frame", "Caption"]
    labels = _visible_labels(page, "#rp-content")
    assert labels.index("Heading") < labels.index("Name")
    assert "Description" not in labels and "Label" not in labels
    assert "Philatelic data" not in page.inner_text("#rp")
    assert page.is_visible("#more-toggle")
    assert page.inner_text("#more-toggle").startswith("More details (optional)")


def test_more_details_folded_when_empty(page):
    _stamp(page)
    assert page.get_attribute("#more-toggle", "aria-expanded") == "false"
    assert page.is_hidden("#more-body") and page.is_hidden("#pcat")
    assert "none filled in" in page.inner_text("#more-toggle")
    page.click("#more-toggle")
    assert page.get_attribute("#more-toggle", "aria-expanded") == "true"
    assert _visible_labels(page, "#more-body") == ["Value", "Condition", "Perforation",
                                                   "Catalogue no."]
    assert "imperforate" in page.inner_text("#more-body")


def test_more_details_open_when_one_is_filled(page):
    _stamp(page, cond="Used")
    assert page.get_attribute("#more-toggle", "aria-expanded") == "true"
    assert page.input_value("#pcond") == "Used"
    assert "1 filled in" in page.inner_text("#more-toggle")
    page.fill("#pperf", "14")
    page.press("#pperf", "Tab")
    assert "2 filled in" in page.inner_text("#more-toggle")


def test_folding_by_hand_lasts_while_the_stamp_stays_selected(page):
    eid = _stamp(page, cat="SG 1")
    page.click("#more-toggle")
    assert page.is_hidden("#more-body")
    page.fill("#plbl", "Penny Red")
    page.press("#plbl", "Tab")  # a change redraws the page
    assert page.is_hidden("#more-body")
    page.evaluate(f"StampAlbum.select(null); StampAlbum.select('{eid}')")
    assert page.is_visible("#more-body"), "selecting it again opens it, since one is filled"


def test_caption_fields_have_no_placeholders(page):
    _stamp(page)
    page.click("#more-toggle")
    for sel in ("#phdg", "#plbl", "#pdenom", "#pperf", "#pcat"):
        assert page.get_attribute(sel, "placeholder") is None, sel


def test_renames_are_on_screen_only(page):
    """Name is still the file's label, Value its denomination: the DSL is unchanged."""
    eid = _stamp(page)
    page.fill("#plbl", "Penny Black")
    page.press("#plbl", "Tab")
    page.click("#more-toggle")
    page.fill("#pdenom", "1d")
    page.press("#pdenom", "Tab")
    page.fill("#pcat", "Cat 1")
    page.press("#pcat", "Tab")
    el = page.evaluate(f"StampAlbum.E.find(e => e.id === '{eid}')")
    assert (el["lbl"], el["denom"], el["cat"]) == ("Penny Black", "1d", "Cat 1")
    dsl = page.evaluate("StampAlbum.buildDSL()")
    assert re.search(r'STAMP_ADD_AT\([^)]*"Penny Black" "Cat 1"', dsl), dsl


def test_name_on_the_page_is_called_name(page):
    _stamp(page)
    assert page.evaluate(
        "document.querySelector('.cel .caption-description').getAttribute('aria-label')"
    ) == "Name below the stamp"


# ── A text item ──

def test_text_panel(page):
    _text(page)
    assert page.inner_text("#rp-title") == "Text"
    labels = _visible_labels(page, "#rp-content")
    assert "Text" in labels and "Name" not in labels and "Heading" not in labels
    assert page.is_hidden("#more-toggle")
    assert page.is_visible("#pfnt") and page.is_visible("#phead")


# ── The palette's text items ──

def test_palette_text_items_have_hints_and_no_font_codes(page):
    items = page.evaluate("""[...document.querySelectorAll('#sidebar .p-item[data-t=text]')]
        .map(i => [i.querySelector('.lbl').textContent, i.querySelector('.sz').textContent,
                   i.querySelector('.hint').textContent, i.getAttribute('aria-label'),
                   document.getElementById(i.getAttribute('aria-describedby')).textContent])""")
    assert [i[:3] for i in items] == [
        ["Heading", "16 pt", "A page or section heading"],
        ["Label", "12 pt", "A title above a paragraph"],
        ["Description", "10 pt", "A paragraph on what the page shows"],
    ]
    for name, _, hint, aria, described in items:
        assert aria == f"Add {name}" and described == hint
    text = page.inner_text("#sidebar")
    assert not re.search(r"\b(HN|HB)\b", text), "no font codes"


def test_palette_sizes_match_what_is_added(page):
    for st, fs in (("heading", 16), ("label", 12), ("desc", 10)):
        page.click(f"#sidebar .p-item[data-st={st}]")
        assert page.evaluate("StampAlbum.E[StampAlbum.E.length - 1].fs") == fs, st


# ── Words the tutorial uses ──

def test_tutorial_uses_the_new_names(page):
    text = page.evaluate("document.querySelector('.tutorial-body').textContent")
    assert "Philatelic data" not in text and "Above the page" not in text
    assert "More details" in text and "Name" in text


def test_palette_text_items_hold_their_words(page):
    """Every part of a text item stays inside its box at every text size (a two-line hint
    ran out of the bottom of the Description box)."""
    for size in (1, 1.25, 1.5):
        page.evaluate(f"StampAlbum.setTextSize({size})")
        out = page.evaluate("""[...document.querySelectorAll('#sidebar .p-item.tx')].flatMap(i => {
            const b = i.getBoundingClientRect();
            return [...i.children].filter(c => { const r = c.getBoundingClientRect();
                return r.bottom > b.bottom + 0.5 || r.right > b.right + 0.5; })
              .map(c => i.dataset.st + ' ' + c.className); })""")
        assert out == [], (size, out)
    page.evaluate("StampAlbum.setTextSize(1)")


# ── Only the fields that change the page (owner, 2026-10-14) ──

def _select_new(page, props):
    page.evaluate(
        "p => { StampAlbum._dirty = false; StampAlbum.newAlbum(); StampAlbum.add(p); }", props)


def _shown(page, ids):
    return {i: page.is_visible("#" + i) for i in ids}


def test_mark_as_heading_explains_itself_on_its_own_line(page):
    _select_new(page, {"t": "text", "x": 20, "y": 20, "w": 200, "h": 30, "lbl": "Title"})
    assert page.is_visible("#phead-hint")
    assert page.text_content("#phead-hint") == "A heading is drawn in the album's theme colour."
    row = page.evaluate("document.getElementById('phead-row').getBoundingClientRect().bottom")
    note = page.evaluate("document.getElementById('phead-hint').getBoundingClientRect().top")
    assert note >= row - 0.5, "the note sits below the checkbox, not squeezed beside it"
    assert page.get_attribute("#phead", "aria-describedby") == "phead-hint"


def test_an_image_has_no_label_font_or_size(page):
    _select_new(page, {"t": "image", "x": 20, "y": 20, "w": 100, "h": 75,
                       "lbl": "bahcoa.png", "img": "/images/bahcoa.png"})
    shown = _shown(page, ["cap-sec", "lbl-row", "font-row", "fsize-row", "phead-row",
                          "img-sec", "img-row", "img-file"])
    assert shown == {"cap-sec": False, "lbl-row": False, "font-row": False, "fsize-row": False,
                     "phead-row": False, "img-sec": True, "img-row": True, "img-file": True}
    assert page.text_content("#img-file") == "File: bahcoa.png"


def test_a_free_shape_has_a_label_but_no_font_or_size(page):
    # Its label is a caption, drawn in the caption font at a fixed size.
    _select_new(page, {"t": "freehand", "s": "freehand", "x": 20, "y": 20, "w": 100, "h": 80})
    shown = _shown(page, ["cap-sec", "lbl-row", "font-row", "fsize-row", "img-sec"])
    assert shown == {"cap-sec": True, "lbl-row": True, "font-row": False, "fsize-row": False,
                     "img-sec": False}


def test_a_text_item_keeps_font_and_size(page):
    _select_new(page, {"t": "text", "x": 20, "y": 20, "w": 200, "h": 30, "lbl": "Title"})
    shown = _shown(page, ["lbl-row", "font-row", "fsize-row", "phead-row", "img-sec", "img-file"])
    assert shown == {"lbl-row": True, "font-row": True, "fsize-row": True, "phead-row": True,
                     "img-sec": False, "img-file": False}
