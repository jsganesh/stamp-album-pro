# ruff: noqa: F811
"""Words typed in the right panel are kept when you move on (owner's report, 2026-10-24).

A stamp's Name, Heading and the optional details used to be saved only when the field
was left with Tab or Enter. Clicking the next stamp swapped the panel over first, so what
had been typed was dropped. Now the words are saved into the item as they are typed and
drawn on the page straight away; leaving the field, choosing another item, clicking the
empty page or closing the phone's Properties sheet records them as one step to undo.
"""

from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)
from test_zoom_ui import phone  # noqa: F401  (fixture)


def _two_stamps(pg):
    """Two stamps side by side, the first selected; returns their ids."""
    return pg.evaluate(
        """() => { StampAlbum.E.length = 0;
                   const s = { t: 'stamp', s: 'rectangle', y: 80, w: 60, h: 70 };
                   StampAlbum.add(Object.assign({ x: 60, lbl: 'First' }, s));
                   StampAlbum.add(Object.assign({ x: 260, lbl: 'Second' }, s));
                   const ids = StampAlbum.E.map(e => e.id);
                   StampAlbum.select(ids[0]); return ids; }"""
    )


def _el(pg, el_id):
    return pg.evaluate("(id) => Object.assign({}, StampAlbum.E.find(e => e.id === id))", el_id)


def _click_stamp(pg, el_id):
    # Near its top-left corner: the middle of a small stamp can be its name on the page.
    pg.click(f'.cel[data-id="{el_id}"]', position={"x": 6, "y": 6})


def _type_into(pg, sel, text):
    pg.click(sel, click_count=3)  # select what is there, as a person would
    pg.keyboard.type(text)


def test_name_typed_is_kept_when_the_next_stamp_is_clicked(page):
    a, b = _two_stamps(page)
    _type_into(page, "#plbl", "Penny Black")
    _click_stamp(page, b)
    assert _el(page, a)["lbl"] == "Penny Black"
    assert _el(page, b)["lbl"] == "Second", "the edit went to the stamp it was typed for"
    assert page.input_value("#plbl") == "Second", "the panel now shows the second stamp"


def test_heading_and_details_typed_are_kept_when_the_next_stamp_is_clicked(page):
    a, b = _two_stamps(page)
    _type_into(page, "#phdg", "Queen Victoria")
    _click_stamp(page, b)
    _click_stamp(page, a)
    page.evaluate("StampAlbum.setMoreOpen(true)")
    _type_into(page, "#pdenom", "1d")
    _click_stamp(page, b)
    el = _el(page, a)
    assert el["hdg"] == "Queen Victoria"
    assert el["denom"] == "1d"
    assert not _el(page, b).get("hdg") and not _el(page, b).get("denom")


def test_name_typed_is_kept_when_the_empty_page_is_clicked(page):
    a, _ = _two_stamps(page)
    _type_into(page, "#plbl", "Two Penny Blue")
    page.click("#page", position={"x": 5, "y": 5})
    assert _el(page, a)["lbl"] == "Two Penny Blue"
    assert page.inner_text("#rp-title") == "Album and page"


def test_name_is_drawn_on_the_page_as_it_is_typed(page):
    a, _ = _two_stamps(page)
    _type_into(page, "#plbl", "Mulready")
    page.wait_for_timeout(100)  # one frame for the redraw
    assert "Mulready" in page.inner_text(f'.cel[data-id="{a}"]')
    assert page.evaluate("StampAlbum._dirty"), "typing counts as an unsaved change"


def test_a_typed_name_is_one_step_to_undo(page):
    a, b = _two_stamps(page)
    before = page.evaluate("StampAlbum._undoStack.length")
    _type_into(page, "#plbl", "Penny Red")
    _click_stamp(page, b)
    assert page.evaluate("StampAlbum._undoStack.length") == before + 1
    page.evaluate("StampAlbum.undo()")
    assert _el(page, a)["lbl"] == "First"


def test_a_size_typed_is_kept_when_the_next_stamp_is_clicked(page):
    a, b = _two_stamps(page)
    _type_into(page, "#pw", "30")
    _click_stamp(page, b)
    assert page.evaluate("(id) => StampAlbum.mm(StampAlbum.E.find(e => e.id === id).w)", a) == 30
    assert _el(page, b)["w"] == 60, "the size went to the stamp it was typed for"


def test_moving_on_from_an_untouched_size_changes_nothing(page):
    a, b = _two_stamps(page)
    before = page.evaluate("StampAlbum._undoStack.length")
    page.click("#pw")
    _click_stamp(page, b)
    assert _el(page, a)["w"] == 60
    assert page.evaluate("StampAlbum._undoStack.length") == before


def test_save_counts_a_name_still_being_typed(page):
    _two_stamps(page)
    _type_into(page, "#plbl", "Black")
    before = page.evaluate("StampAlbum._undoStack.length")
    page.evaluate("StampAlbum.commitPanelEdit()")  # what Save and Export do first
    assert page.evaluate("StampAlbum._undoStack.length") == before + 1


def test_phone_name_typed_is_kept_when_the_sheet_is_closed(phone):
    a, _ = _two_stamps(phone)
    phone.click("#pb-props")
    _type_into(phone, "#plbl", "Penny Lilac")
    before = phone.evaluate("StampAlbum._undoStack.length")
    phone.click("#sheet-close")
    assert _el(phone, a)["lbl"] == "Penny Lilac"
    assert phone.evaluate("StampAlbum._undoStack.length") == before + 1
    assert not phone.js_errors


def test_undo_after_a_tick_box_undoes_it_once(page):
    a, _ = _two_stamps(page)
    page.evaluate("StampAlbum.add({ t: 'text', x: 60, y: 300, w: 200, h: 40, lbl: 'Notes' })")
    tid = page.evaluate("StampAlbum.E[StampAlbum.E.length - 1].id")
    page.evaluate("(id) => StampAlbum.select(id)", tid)
    page.check("#phead")
    page.uncheck("#phead")  # the tick box keeps focus
    page.evaluate("StampAlbum.undo()")
    assert page.evaluate("(id) => StampAlbum.E.find(e => e.id === id).role", tid) == "heading"
