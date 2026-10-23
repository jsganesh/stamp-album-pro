# ruff: noqa: F811
"""Page headings linked to the plan, the Philatelic note tile, and Check exhibit.

A page heading can be linked to a chapter of the title and plan page (PAGE_TEXT_CHAPTER): its
words are the plan's and follow the plan when it changes in the form. A Philatelic note is
italic and smaller, set apart from the story as FIP thematic rules ask. View › Check exhibit
lists what FIP judges would mark down, page by page, with a button to go there.
"""

from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401

from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer

LINKED = ('ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n'
          'PAGE_TEXT_AT(20 20 170 10 "HB" 16 "1.1 Blued paper" "left")\n'
          'PAGE_TEXT_ROLE("heading")\nPAGE_TEXT_CHAPTER("1.1")\n')


def test_python_keeps_the_link():
    album = AlbumParser().parse(LINKED, "t.slbum")
    assert album.pages[0].absolute_stamps[0].chapter == "1.1"
    out = AlbumSerializer().to_dsl(album)
    assert 'PAGE_TEXT_ROLE("heading")\nPAGE_TEXT_CHAPTER("1.1")' in out
    bad = AlbumParser().parse(LINKED.replace('"1.1")\n', '"x")\n'), "t.slbum")
    assert bad.pages[0].absolute_stamps[0].chapter == ""


# ── The editor ──


def _plan(page, chapters=(("chapter", "First printing"), ("section", "Blued paper"),
                          ("chapter", "Later printings"))):
    page.evaluate("StampAlbum.select(null); StampAlbum.openExhibitPlan()")
    page.fill("#tp-title", "The First Issues")
    page.evaluate("document.getElementById('tp-plan-list').textContent = ''")
    for kind, text in chapters:
        page.click("#tp-add-" + kind)
        page.keyboard.type(text)
    page.click("#tp-apply")


def _heading_on_page_2(page):
    page.evaluate("StampAlbum.addPage()")
    page.click(".p-item[data-st='heading']")
    return page.evaluate("StampAlbum.sel")


def _el(page, eid):
    return page.evaluate("id => StampAlbum.E.find(e => e.id === id)", eid)


def test_no_chapter_field_without_a_plan(page):
    page.evaluate("StampAlbum.newAlbum()")
    page.click(".p-item[data-st='heading']")
    assert page.is_hidden("#pchap-row")


def test_a_heading_takes_its_chapter_from_the_plan(page):
    page.evaluate("StampAlbum.newAlbum()")
    _plan(page)
    eid = _heading_on_page_2(page)
    assert page.is_visible("#pchap-row") and page.is_visible("#pchap-note")
    options = page.evaluate(
        "[...document.querySelectorAll('#pchap option')].map(o => o.textContent)")
    assert options == ["Not linked", "1. First printing", "1.1 Blued paper", "2. Later printings"]
    page.select_option("#pchap", "1.1")
    el = _el(page, eid)
    assert (el["lbl"], el["chapter"], el["role"]) == ("1.1 Blued paper", "1.1", "heading")
    assert page.input_value("#plbl") == "1.1 Blued paper"
    assert 'PAGE_TEXT_CHAPTER("1.1")' in page.evaluate("StampAlbum.buildDSL()")
    page.evaluate("StampAlbum.undo()")
    assert "chapter" not in _el(page, eid)


def test_the_plan_pages_own_items_have_no_chapter_field(page):
    page.evaluate("StampAlbum.newAlbum()")
    _plan(page)
    page.evaluate("StampAlbum.select(StampAlbum.E.find(e => e.part === 'title').id)")
    assert page.is_hidden("#pchap-row")


def test_linked_headings_follow_the_plan(page):
    page.evaluate("StampAlbum.newAlbum()")
    _plan(page)
    eid = _heading_on_page_2(page)
    page.select_option("#pchap", "1.1")
    # A chapter put in front: the heading keeps its section, now 2.1
    _plan(page, (("chapter", "Introduction"), ("chapter", "First printing"),
                 ("section", "Blued paper"), ("chapter", "Later printings")))
    page.evaluate("StampAlbum.switchPage(1)")
    el = _el(page, eid)
    assert (el["lbl"], el["chapter"]) == ("2.1 Blued paper", "2.1")
    # The section renamed in place: it keeps its number and takes the new name
    _plan(page, (("chapter", "Introduction"), ("chapter", "First printing"),
                 ("section", "Bluish paper"), ("chapter", "Later printings")))
    page.evaluate("StampAlbum.switchPage(1)")
    assert _el(page, eid)["lbl"] == "2.1 Bluish paper"


def test_a_philatelic_note_is_small_italic_text(page):
    page.evaluate("StampAlbum.newAlbum()")
    page.click(".p-item[data-st='note']")
    el = page.evaluate("StampAlbum.E[0]")
    assert (el["t"], el["font"], el["fs"], el["lbl"]) == ("text", "HI", 9, "Philatelic note")
    assert "role" not in el


# ── Check exhibit ──


def _check(page):
    page.evaluate("StampAlbum.select(null)")
    page.click("#menu-view-btn")
    page.click("#menu-check")
    assert page.is_visible("#check-overlay")
    return page.evaluate("""() => ({
        summary: document.getElementById('chk-summary').textContent,
        fix: [...document.querySelectorAll('#chk-fix .chk-item')].map(li => li.innerText),
        advice: [...document.querySelectorAll('#chk-advice .chk-item')]
            .map(li => li.innerText)})""")


def test_an_album_without_a_plan_is_told_to_make_one(page):
    page.evaluate("StampAlbum.newAlbum()")
    page.click(".p-item[data-st='heading']")
    got = _check(page)
    assert got["summary"] == "1 thing to fix before exhibiting."
    assert "no title and plan page" in got["fix"][0]
    page.click("#chk-fix .chk-item button")  # "Title and plan page…"
    assert page.is_hidden("#check-overlay") and page.is_visible("#plan-overlay")


def test_findings_name_their_page_and_go_there(page):
    page.evaluate("StampAlbum.newAlbum()")
    _plan(page)
    page.evaluate("StampAlbum.addPage()")
    page.evaluate("""StampAlbum.add({ t: 'stamp', s: 'rectangle', x: StampAlbum.px(100),
        y: StampAlbum.px(150), w: StampAlbum.px(19), h: StampAlbum.px(22), lbl: '' })""")
    page.evaluate("StampAlbum.switchPage(0)")
    got = _check(page)
    assert got["summary"] == "Nothing to fix. The advice below may still help."
    assert page.is_hidden("#chk-fix")
    texts = "\n".join(got["advice"])
    assert "Page 2" in texts and "no heading" in texts and "1 stamp has no name" in texts
    assert "1 frame of 16 sheets, with 2 in it" in texts
    page.click("#chk-advice .chk-item button")  # Go to page 2
    assert page.is_hidden("#check-overlay")
    assert page.evaluate("StampAlbum._currentPage") == 1


def test_a_caption_past_the_border_is_counted(page):
    page.evaluate("StampAlbum.newAlbum()")
    _plan(page)
    page.evaluate("StampAlbum._pageBorder = 'solid'; StampAlbum.syncPageBar()")
    page.evaluate("StampAlbum.addPage()")
    page.click(".p-item[data-st='heading']")
    page.evaluate("""StampAlbum.add({ t: 'stamp', s: 'rectangle', x: StampAlbum.px(100),
        y: StampAlbum.px(266), w: StampAlbum.px(19), h: StampAlbum.px(15), lbl: 'Name' })""")
    page.evaluate("StampAlbum.switchPage(0)")  # counted on pages not on screen too
    got = _check(page)
    assert any("1 caption or frame runs past the border" in f for f in got["fix"]), got


def test_escape_and_close_shut_it(page):
    page.evaluate("StampAlbum.newAlbum()")
    _check(page)
    page.keyboard.press("Escape")
    assert page.is_hidden("#check-overlay")
    _check(page)
    page.click("#chk-done")
    assert page.is_hidden("#check-overlay")
    assert page.js_errors == []
