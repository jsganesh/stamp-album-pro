# ruff: noqa: F811
"""The Title and plan page form (web/exhibit_plan.js).

The form makes an exhibit's first page as FIP guidelines ask (title, purpose, scope, a plan in
numbered chapters, important items, research, references) out of ordinary text items, each
marked with its part (PAGE_TEXT_PART in the file). It reads its answers back from those items,
replaces only them when applied again, and is one undo step. The Python side keeps the parts.
"""

from test_starter_templates import _text_fits
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401

from stamp_album.core.models import PLAN_PARTS
from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer

PLAN_DSL = (
    'ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n'
    'PAGE_TEXT_AT(20 40 170 13 "HB" 22 "My exhibit" "center")\nPAGE_TEXT_ROLE("heading")\n'
    'PAGE_TEXT_PART("title")\n'
    'PAGE_TEXT_AT(20 74 170 8 "HB" 11 "Plan of the exhibit" "left")\nPAGE_TEXT_PART("plan_label")\n'
    'PAGE_TEXT_AT(20 83 170 20 "HN" 10 "1. A\\n1.1 B\\n2. C" "left")\nPAGE_TEXT_PART("plan")\n'
    'PAGE_TEXT_AT(20 120 170 10 "HN" 10 "Not from the form" "left")\nPAGE_TEXT_PART("bogus")\n'
)


# ── The file, in Python ──


def test_python_reads_and_writes_the_parts():
    album = AlbumParser().parse(PLAN_DSL, "plan.slbum")
    items = album.pages[0].absolute_stamps
    assert [s.part for s in items] == ["title", "plan_label", "plan", ""]
    assert items[0].role == "heading"
    out = AlbumSerializer().to_dsl(album)
    assert 'PAGE_TEXT_ROLE("heading")\nPAGE_TEXT_PART("title")' in out
    assert 'PAGE_TEXT_PART("plan")' in out
    assert "bogus" not in out
    again = AlbumParser().parse(out, "plan.slbum")
    assert [s.part for s in again.pages[0].absolute_stamps] == ["title", "plan_label", "plan", ""]


def test_python_and_the_editor_know_the_same_parts(page):
    assert set(page.evaluate("StampAlbum.CORE.PLAN_PART_NAMES")) == PLAN_PARTS


# ── The form ──


def _open(page):
    page.evaluate("StampAlbum.select(null)")
    page.click("#menu-file-btn")
    page.click("#menu-exhibit-plan")
    assert page.is_visible("#plan-overlay")


def _fill(page, title="Exhibit Title", chapters=(("chapter", "First"), ("section", "A"),
                                                  ("chapter", "Second"))):
    page.fill("#tp-title", title)
    page.fill("#tp-by", "A traditional exhibit by Your Name")
    page.fill("#tp-purpose", "What the exhibit shows and why, in a sentence or two of plain words.")
    page.fill("#tp-scope", "Where it begins and ends.")
    page.fill("#tp-important", "Important and rare items have a double frame.")
    page.fill("#tp-research", "Plating of the lowest value.")
    page.fill("#tp-references", "The handbook.")
    page.evaluate("document.getElementById('tp-plan-list').textContent = ''")
    for kind, text in chapters:
        page.click("#tp-add-" + kind)
        page.keyboard.type(text)


def _items(page, idx=None):
    """The items of a page (the current one by default), in mm."""
    return page.evaluate("""idx => {
        const S = StampAlbum, pages = S._pages.slice(); pages[S._currentPage] = S.E;
        return pages[idx === null ? S._currentPage : idx].map(e => Object.assign({}, e,
            { x: e.x / S._sc, y: e.y / S._sc, w: e.w / S._sc, h: e.h / S._sc }));
    }""", idx)


def _parts(items):
    return [e.get("part") for e in items if e.get("part")]


def test_the_file_menu_and_the_panel_open_it(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    assert page.inner_text("#tp-apply") == "Make the page"
    assert page.inner_text("#tp-plan-list .tp-num") == "1"  # one empty chapter to start with
    page.click("#tp-cancel")
    assert page.is_hidden("#plan-overlay")
    page.evaluate("StampAlbum.select(null)")
    page.click("#btn-exhibit-plan")
    assert page.is_visible("#plan-overlay")
    page.keyboard.press("Escape")
    assert page.is_hidden("#plan-overlay")


def test_it_makes_the_page_on_an_empty_album(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    _fill(page)
    assert "page 1, which is empty" in page.inner_text("#tp-note")
    page.click("#tp-apply")
    assert page.is_hidden("#plan-overlay")
    items = _items(page)
    assert _parts(items) == ["title", "by", "purpose_label", "purpose", "scope_label", "scope",
                             "plan_label", "plan", "important_label", "important",
                             "research_label", "research", "references_label", "references"]
    by_part = {e["part"]: e for e in items}
    assert by_part["title"]["role"] == "heading" and by_part["title"]["lbl"] == "Exhibit Title"
    assert by_part["plan"]["lbl"] == "1. First\n1.1 A\n2. Second"
    assert by_part["plan_label"]["lbl"] == "Plan of the exhibit"
    assert page.evaluate("StampAlbum._pages.length") == 1
    assert page.js_errors == []


def test_the_text_fits_its_boxes_and_the_page(page):
    """Checked with the PDF's own font widths, as the starter templates are."""
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    _fill(page, chapters=[("chapter", "A longer chapter name to wrap the plan " * 4)]
          + [("section", f"Section {i}") for i in range(6)])
    page.fill("#tp-purpose", "A purpose that runs over several lines of the page. " * 6)
    page.click("#tp-apply")
    album = AlbumParser().parse(page.evaluate("StampAlbum.buildDSL()"), "t.slbum")
    texts = album.pages[0].absolute_stamps
    assert len(texts) == 14
    for s in texts:
        assert _text_fits(s), f"'{s.description[:30]}' doesn't fit its box"
        assert 15 <= s.abs_x and s.abs_x + s.width <= 195 and s.abs_y + s.height <= 282
    for a, b in zip(texts, texts[1:]):
        assert b.abs_y >= a.abs_y + a.height - 1e-6, "items run into each other"


def test_it_reads_its_answers_back(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    _fill(page)
    page.click("#tp-apply")
    _open(page)
    assert page.input_value("#tp-title") == "Exhibit Title"
    assert page.input_value("#tp-scope") == "Where it begins and ends."
    rows = page.evaluate("""[...document.querySelectorAll('#tp-plan-list li')].map(li =>
        [li.querySelector('.tp-num').textContent, li.querySelector('input').value,
         li.querySelector('input').getAttribute('aria-label')])""")
    assert rows == [["1", "First", "Chapter 1"], ["1.1", "A", "Section 1.1"],
                    ["2", "Second", "Chapter 2"]]
    assert page.inner_text("#tp-apply") == "Update the page"
    assert "Updates the title and plan on page 1" in page.inner_text("#tp-note")


def test_an_edit_on_the_page_shows_in_the_form(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    _fill(page)
    page.click("#tp-apply")
    page.evaluate("""() => { const el = StampAlbum.E.find(e => e.part === 'plan');
                             el.lbl = '1. Changed on the page\\n2. Second'; }""")
    _open(page)
    values = page.evaluate(
        "[...document.querySelectorAll('#tp-plan-list input')].map(i => i.value)")
    assert values == ["Changed on the page", "Second"]


def test_updating_keeps_everything_else_on_the_page(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    _fill(page)
    page.click("#tp-apply")
    page.evaluate("""StampAlbum.add({ t: 'stamp', s: 'rectangle', x: StampAlbum.px(30),
        y: StampAlbum.px(255), w: StampAlbum.px(19), h: StampAlbum.px(22), lbl: 'Mine' })""")
    _open(page)
    page.click("#tp-add-chapter")
    page.keyboard.type("Third")
    page.click("#tp-apply")
    items = _items(page)
    assert [e["lbl"] for e in items if e["t"] == "stamp"] == ["Mine"]
    assert len(_parts(items)) == 14, "the form's items are replaced, not added to"
    assert next(e for e in items if e.get("part") == "plan")["lbl"].endswith("3. Third")


def test_it_adds_a_first_page_when_page_1_is_in_use(page):
    page.evaluate("StampAlbum.newAlbum()")
    page.evaluate("""StampAlbum.add({ t: 'stamp', s: 'rectangle', x: StampAlbum.px(30),
        y: StampAlbum.px(40), w: StampAlbum.px(19), h: StampAlbum.px(22), lbl: 'Mine' })""")
    _open(page)
    _fill(page)
    assert "new first page" in page.inner_text("#tp-note")
    page.click("#tp-apply")
    assert page.evaluate("StampAlbum._pages.length") == 2
    assert page.evaluate("StampAlbum._currentPage") == 0
    assert _parts(_items(page, 0))[0] == "title"
    assert [e["lbl"] for e in _items(page, 1)] == ["Mine"], "the old first page is now page 2"


def test_it_is_one_undo_step(page):
    page.evaluate("StampAlbum.newAlbum()")
    page.evaluate("""StampAlbum.add({ t: 'stamp', s: 'rectangle', x: StampAlbum.px(30),
        y: StampAlbum.px(40), w: StampAlbum.px(19), h: StampAlbum.px(22), lbl: 'Mine' })""")
    _open(page)
    _fill(page)
    page.click("#tp-apply")
    assert page.evaluate("StampAlbum._pages.length") == 2
    page.evaluate("StampAlbum.undo()")
    assert page.evaluate("StampAlbum._pages.length") == 1
    assert [e["lbl"] for e in _items(page)] == ["Mine"]
    page.evaluate("StampAlbum.redo()")
    assert page.evaluate("StampAlbum._pages.length") == 2


def test_it_needs_a_title_and_must_fit(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    assert page.is_disabled("#tp-apply")
    assert page.inner_text("#tp-note") == "Fill in at least the title."
    _fill(page)
    assert page.is_enabled("#tp-apply")
    page.fill("#tp-references", "A very long list of references, one after another. " * 120)
    assert page.is_disabled("#tp-apply")
    assert "Too long for one page by" in page.inner_text("#tp-note")
    assert "warn" in page.get_attribute("#tp-note", "class")


def test_it_survives_saving_and_opening(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    _fill(page)
    page.click("#tp-apply")
    dsl = page.evaluate("StampAlbum.buildDSL()")
    assert 'PAGE_TEXT_PART("plan")' in dsl
    page.evaluate("StampAlbum.newAlbum()")
    page.evaluate("d => StampAlbum.parseDSL(d)", dsl)
    _open(page)
    assert page.input_value("#tp-title") == "Exhibit Title"
    assert page.evaluate("document.querySelectorAll('#tp-plan-list li').length") == 3


def test_a_copy_of_a_plan_item_is_ordinary_text(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    _fill(page)
    page.click("#tp-apply")
    page.evaluate("StampAlbum.select(StampAlbum.E.find(e => e.part === 'purpose').id)")
    page.click("#btn-dup-el")
    copies = [e for e in _items(page) if e["lbl"].startswith("What the exhibit")]
    assert len(copies) == 2 and sorted(e.get("part", "") for e in copies) == ["", "purpose"]


def test_enter_adds_a_row_below_at_the_same_level(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    _fill(page)
    page.click("#tp-plan-list li:nth-child(2) input")  # section 1.1
    page.keyboard.press("Enter")
    page.keyboard.type("New")
    assert page.evaluate("""[...document.querySelectorAll('#tp-plan-list li')].map(li =>
        li.querySelector('.tp-num').textContent + ' ' + li.querySelector('input').value)""") == [
        "1 First", "1.1 A", "1.2 New", "2 Second"]
    assert page.is_visible("#plan-overlay"), "Enter in the plan doesn't apply the form"


def test_remove_renumbers(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open(page)
    _fill(page)
    page.click("#tp-plan-list li:first-child button")  # "Remove 1"
    assert page.evaluate("""[...document.querySelectorAll('#tp-plan-list li')].map(li =>
        li.querySelector('.tp-num').textContent + ' ' + li.querySelector('input').value)""") == [
        "1 A", "2 Second"], "a section left without a chapter becomes one"
    assert page.get_attribute("#tp-plan-list li:first-child button", "aria-label") == "Remove 1"
