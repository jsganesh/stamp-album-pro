# ruff: noqa: F811
"""The template gallery (UI review item 10, option A; owner's choices 2026-10-17): each card
shows a simple drawing of its page, in the page strip's style, drawn from the template itself.
Picking a template starts a new, unnamed album: it asks first when there is unsaved work, and a
later Save never writes over the album that was open. The wizard starts albums the same way."""

import pytest
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)
from test_zoom_ui import phone  # noqa: F401  (fixture)

from stamp_album import api
from stamp_album.templates import TEMPLATES


@pytest.fixture(autouse=True)
def albums(tmp_path, monkeypatch):
    """Saves go to a folder of their own, never the albums folder on this computer."""
    files = tmp_path / "albums"
    files.mkdir()
    monkeypatch.setattr(api, "FILES_DIR", files)
    return files

OPEN = "document.getElementById('btn-wiz-template').click()"

# Per card: [template id, stamps and pictures drawn, text bars drawn, has a border]
DRAWN = r"""[...document.querySelectorAll('#template-grid .tg-card')].map(c => [c.dataset.id,
    c.querySelectorAll('svg .pg-shape').length, c.querySelectorAll('svg .pg-text').length,
    c.querySelectorAll('svg .pg-border').length])"""

# Per template, as the editor's parser reads it: [stamps and pictures, text items, border?]
PARSED = r"""(dsl) => { const st = StampAlbum.CORE.parseDSL(dsl), items = st.pages[0];
    return [items.filter(e => e.t !== 'text').length, items.filter(e => e.t === 'text').length,
            !!(st.pageBorder && st.pageBorder !== 'none')]; }"""


def _gallery(pg):
    pg.evaluate(OPEN)
    for _ in range(100):
        n = pg.evaluate("document.querySelectorAll('#template-grid .tg-card').length")
        drawn = pg.evaluate("[...document.querySelectorAll('#template-grid .tg-card')]"
                            ".every(c => c.querySelector('svg rect'))")
        if n and drawn:
            return
        pg.wait_for_timeout(50)
    raise AssertionError("the gallery's pictures were not drawn")


def _pick(pg, name):
    pg.get_by_role("button", name=name, exact=True).click()


def _wait(pg, js):
    for _ in range(100):
        if pg.evaluate(js):
            return
        pg.wait_for_timeout(50)
    raise AssertionError(js)


def _a_saved_album(pg):
    """An album opened from the file "mine.slbum", with one stamp and an unsaved change."""
    pg.evaluate("""() => { const S = StampAlbum;
        S.openAlbum('mine.slbum', 'ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\n'
            + 'STAMP_ADD_AT(20 20 40 30 "mine" "" "" "")\\nPAGE_END');
        S.E[0].x += 10; S.pushUndo(); S.render(); }""")
    assert pg.evaluate("StampAlbum._dirty") is True


def test_every_card_draws_its_own_page(page):
    _gallery(page)
    drawn = page.evaluate(DRAWN)
    assert [d[0] for d in drawn] == [t["id"] for t in TEMPLATES]
    for (tid, shapes, texts, border), t in zip(drawn, TEMPLATES):
        want_shapes, want_texts, want_border = page.evaluate(PARSED, t["content"])
        assert shapes == want_shapes, tid
        assert texts >= want_texts > 0, tid  # a text item draws one bar per line
        assert border == int(want_border), tid
    # The pages look different
    assert len({tuple(d[1:]) for d in drawn}) == len(TEMPLATES)
    assert page.js_errors == []


def test_pictures_keep_the_papers_shape(page):
    _gallery(page)
    ratios = page.evaluate("""[...document.querySelectorAll('#template-grid .tg-pic')].map(s => {
        const r = s.getBoundingClientRect(); return [r.width, r.height]; })""")
    assert len(ratios) == len(TEMPLATES)
    for w, h in ratios:
        assert h >= 150  # big enough to tell the pages apart
        assert abs(w / h - 210 / 297) < 0.02


def test_frames_use_the_templates_mounts_not_the_open_albums(page):
    """The open album has mounts 0 + 1 mm; the templates 1.5 + 1. Drawing the gallery
    neither borrows the album's mounts nor changes them."""
    page.evaluate("StampAlbum.CORE.setMount(0, 1)")
    _gallery(page)
    t = TEMPLATES[0]
    got = page.evaluate("""(dsl) => { const S = StampAlbum, st = S.CORE.parseDSL(dsl);
        const el = st.pages[0].find(e => e.t !== 'text');
        const r = document.querySelector('#template-grid .tg-card .pg-shape');
        const w = Number(r.getAttribute('width'));
        return [w - el.w, S.CORE.getMount()]; }""", t["content"])
    outset_twice, mount = got
    assert mount == {"overhang": 0, "gap": 1}
    assert outset_twice > 2 * 2.5  # frame line beyond 1.5 + 1 mm each side


def test_cards_are_named_by_title_and_described(page):
    _gallery(page)
    for t in TEMPLATES:
        card = page.get_by_role("button", name=t["name"], exact=True)
        assert card.count() == 1
        desc_id = card.get_attribute("aria-describedby")
        desc = page.evaluate(f"document.getElementById('{desc_id}').textContent")
        assert desc == t["description"]
    # No category line: every card said "Exhibition"
    assert page.locator("#template-grid .tg-card-cat").count() == 0
    assert "Exhibition" not in page.evaluate(
        "[...document.querySelectorAll('#template-grid .tg-card')]"
        ".map(c => c.textContent).join(' ').replace(/Exhibition page/g, '')")


def test_picking_a_template_asks_before_replacing_unsaved_work(page):
    _a_saved_album(page)
    _gallery(page)
    asked = []
    page.once("dialog", lambda d: (asked.append(d.message), d.dismiss()))
    _pick(page, "Set row")
    page.wait_for_timeout(300)
    assert len(asked) == 1
    assert page.evaluate("StampAlbum.E.map(e => e.lbl)") == ["mine"]  # kept
    assert page.evaluate("StampAlbum._currentFile") == "mine.slbum"

    page.once("dialog", lambda d: d.accept())
    _pick(page, "Set row")
    _wait(page, "StampAlbum.E.length > 1")
    assert page.locator("#template-gallery-panel.open").count() == 0


def test_a_template_never_saves_over_the_open_album(page):
    _a_saved_album(page)
    page.evaluate("StampAlbum.saveFile()")
    _wait(page, "!StampAlbum._dirty")
    _gallery(page)
    _pick(page, "Single stamp")  # nothing unsaved: no question
    _wait(page, "StampAlbum.E.length > 1")
    assert page.evaluate("StampAlbum._currentFile") is None
    assert page.evaluate("StampAlbum._dirty") is True  # Not saved
    assert page.locator("#tb-dirty").is_visible()
    # Undo can't bring back the other album's page
    assert page.evaluate("StampAlbum._undoStack.length") == 1
    # Save asks for a name rather than writing to mine.slbum
    asked = []
    page.once("dialog", lambda d: (asked.append(d.type), d.dismiss()))
    page.evaluate("StampAlbum.saveFile()")
    page.wait_for_timeout(200)
    assert asked == ["prompt"]


def test_the_wizard_starts_a_new_unnamed_album(page):
    _a_saved_album(page)
    page.evaluate("StampAlbum.saveFile()")
    _wait(page, "!StampAlbum._dirty")
    page.evaluate("document.getElementById('btn-wizard').click()")
    page.fill("#wiz-title", "My exhibit")
    page.evaluate("StampAlbum.applyWizard()")
    assert page.evaluate("StampAlbum._currentFile") is None
    assert page.evaluate("StampAlbum.E.map(e => e.t)") == ["text"]
    assert page.evaluate("StampAlbum._undoStack.length") == 1


def test_the_wizard_asks_once_before_replacing_unsaved_work(page):
    _a_saved_album(page)
    page.evaluate("document.getElementById('btn-wizard').click()")
    asked = []
    page.on("dialog", lambda d: (asked.append(d.type), d.dismiss()))
    page.evaluate("StampAlbum.applyWizard()")
    assert asked == ["confirm"]
    assert page.evaluate("StampAlbum._currentFile") == "mine.slbum"


def test_an_older_list_without_contents_still_draws(page):
    """A template list without "dsl" (as before this change): each card fetches its page."""
    t = TEMPLATES[1]
    page.route("**/api/templates", lambda r: r.fulfill(json=[
        {"id": t["id"], "name": t["name"], "description": t["description"]}]))
    _gallery(page)
    assert page.evaluate(DRAWN)[0][1] == page.evaluate(PARSED, t["content"])[0]


def test_template_list_carries_each_page(base_url):
    import json
    import urllib.request

    with urllib.request.urlopen(base_url + "/api/templates") as r:
        listed = json.load(r)
    assert [t["dsl"] for t in listed] == [t["content"] for t in TEMPLATES]


def test_phone_shows_one_card_across(phone):
    _gallery(phone)
    boxes = phone.evaluate("""[...document.querySelectorAll('#template-grid .tg-card')].map(c => {
        const r = c.getBoundingClientRect(); return [r.left, r.right]; })""")
    width = phone.evaluate("innerWidth")
    assert len({round(b[0]) for b in boxes}) == 1  # one column
    for left, right in boxes:
        assert left >= 0 and right <= width
    assert phone.js_errors == []


def test_extra_large_text_keeps_cards_inside_the_gallery(page):
    page.evaluate("StampAlbum.setTextSize('xlarge')")
    _gallery(page)
    panel = page.locator("#template-gallery-panel").bounding_box()
    for i in range(len(TEMPLATES)):
        box = page.locator("#template-grid .tg-card").nth(i).bounding_box()
        assert box["x"] >= panel["x"] and box["x"] + box["width"] <= panel["x"] + panel["width"]
