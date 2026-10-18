# ruff: noqa: F811
"""The page strip (UI review item 5, option A; owner's choices 2026-10-16): a column of page
pictures down the canvas's left edge, one row along the bottom on a phone, each with a ⋯ menu
(Move earlier, Move later, Delete page). It replaces the page dots in the bar above the page."""

from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)
from test_zoom_ui import phone  # noqa: F401  (fixture)

# Each drawn shape on page 1's picture: [tag, number of polygon points, dash pattern]
SHAPES = r"""[...document.querySelectorAll('#pg-list .pg-item[data-idx="0"] .pg-shape')]
    .map(n => [n.tagName, (n.getAttribute('points') || '').trim().split(/\s+/)
                              .filter(Boolean).length,
               n.getAttribute('stroke-dasharray')])"""

# The diamond's top point less the top centre of the stamp (mm), and its frame's outset
DIAMOND_TOP = r"""(() => { const S = StampAlbum, el = S.E.find(e => e.id === 'd');
    const pts = document.querySelectorAll('#pg-list .pg-shape')[2].getAttribute('points')
        .trim().split(/\s+/).map(p => p.split(',').map(Number));
    const o = S.CORE.frameOutset(el), top = pts.reduce((a, p) => p[1] < a[1] ? p : a);
    return [top[0] - (el.x + el.w / 2) / S._sc, top[1] - el.y / S._sc, o]; })()"""


def _three_pages(pg):
    """An album of three pages: one stamp on page 1, two on page 2, none on page 3; page 1 open."""
    pg.evaluate("""() => { const S = StampAlbum; S.newAlbum();
        const st = (id, x) => ({id, t: 'stamp', s: 'rectangle', x, y: 100, w: 60, h: 70, lbl: id});
        S._pages = [[st('a', 100)], [st('b', 100), st('c', 250)], []];
        S.E = JSON.parse(JSON.stringify(S._pages[0])); S._currentPage = 0;
        S.renderPageDots(); S.render(); S.resetUndo(); }""")


def _pages(pg):
    """Each page's item ids, the open one taken from S.E."""
    return pg.evaluate("""StampAlbum._pages.map((p, i) => (i === StampAlbum._currentPage
        ? StampAlbum.E : p).map(e => e.id))""")


def _boxes(pg, idx):
    """How many stamps, shapes and pictures a page's picture draws."""
    return pg.evaluate(f"""document.querySelectorAll(
        '#pg-list .pg-item[data-idx="{idx}"] svg .pg-shape').length""")


def _open_menu(pg, idx):
    pg.click(f'#pg-list .pg-item[data-idx="{idx}"] .pg-more')
    assert pg.is_visible("#pg-menu")


# ── The strip ──


def test_one_named_picture_per_page_and_the_open_one_marked(page):
    _three_pages(page)
    thumbs = page.locator("#pg-list .pg-thumb")
    assert thumbs.count() == 3
    for i in range(3):
        b = page.get_by_role("button", name=f"Page {i + 1}", exact=True)
        assert b.inner_text().strip() == str(i + 1)  # the number shows under the picture
        assert (b.get_attribute("aria-current") == "page") == (i == 0)
    assert page.get_by_role("navigation", name="Pages").count() == 1
    assert page.js_errors == []


def test_the_pictures_show_each_pages_items(page):
    _three_pages(page)
    assert [_boxes(page, i) for i in range(3)] == [1, 2, 0]


def test_the_open_pages_picture_follows_changes(page):
    _three_pages(page)
    page.evaluate("""StampAlbum.E.push({id: 'd', t: 'stamp', s: 'rectangle', x: 300, y: 300,
        w: 60, h: 70}); StampAlbum.render()""")
    assert _boxes(page, 0) == 2
    page.evaluate("StampAlbum.E.length = 0; StampAlbum.render()")
    assert _boxes(page, 0) == 0


def test_each_shape_is_drawn_as_its_own_outline(page):
    """A diamond is not a box: the picture uses the outline the page and the exports draw."""
    page.evaluate("""() => { const S = StampAlbum; S.newAlbum();
        const st = (id, s, x) => ({id, t: 'stamp', s, x, y: 100, w: 100, h: 70,
                                   bdr: 'solid', bdrW: 0.5});
        S.E.push(st('r', 'rectangle', 40), st('o', 'oval', 160), st('d', 'diamond', 280),
                 st('h', 'hexagon', 400), {id: 'f', t: 'freehand', x: 40, y: 300, w: 100, h: 70});
        S.render(); }""")
    shapes = page.evaluate(SHAPES)
    assert shapes == [["rect", 0, None], ["ellipse", 0, None], ["polygon", 4, None],
                      ["polygon", 6, None], ["rect", 0, "2 1.5"]], shapes
    # The diamond's top point sits at the frame's outer edge, centred over the stamp
    top = page.evaluate(DIAMOND_TOP)
    assert abs(top[0]) < 1e-6 and top[1] < 0 and top[1] >= -top[2] * 1.5, top


def test_clicking_a_picture_opens_that_page(page):
    _three_pages(page)
    page.click('#pg-list .pg-item[data-idx="1"] .pg-thumb')
    assert page.evaluate("StampAlbum._currentPage") == 1
    assert page.get_by_role("button", name="Page 2", exact=True).get_attribute(
        "aria-current") == "page"
    assert sorted(page.evaluate("StampAlbum.E.map(e => e.id)")) == ["b", "c"]


def test_arrow_keys_move_between_pages(page):
    _three_pages(page)
    page.focus('#pg-list .pg-item[data-idx="0"] .pg-thumb')
    page.keyboard.press("ArrowDown")
    assert page.evaluate("StampAlbum._currentPage") == 1
    page.keyboard.press("End")
    assert page.evaluate("StampAlbum._currentPage") == 2
    page.keyboard.press("ArrowUp")
    assert page.evaluate("StampAlbum._currentPage") == 1
    assert page.evaluate("document.activeElement.getAttribute('aria-label')") == "Page 2"


def test_add_page_adds_one_at_the_end_and_opens_it(page):
    _three_pages(page)
    add = page.get_by_role("button", name="Add page", exact=True)
    assert add.inner_text().strip() == "Add page"
    add.click()
    assert page.evaluate("[StampAlbum._pages.length, StampAlbum._currentPage]") == [4, 3]
    assert page.evaluate("document.activeElement.getAttribute('aria-label')") == "Page 4"


def test_the_bar_above_the_page_has_no_page_buttons(page):
    _three_pages(page)
    assert page.evaluate("!!document.getElementById('pg-dots')") is False
    assert page.locator("#ca-toolbar button:not(#sel-tools button)").count() == 0


def test_the_strip_stands_beside_the_page_and_bar(page):
    _three_pages(page)
    strip = page.locator("#pg-strip").bounding_box()
    bar = page.locator("#ca-toolbar").bounding_box()
    wrap = page.locator("#page-wrap").bounding_box()
    assert strip["x"] + strip["width"] <= bar["x"] + 0.5
    assert strip["x"] + strip["width"] <= wrap["x"] + 0.5
    assert strip["y"] <= bar["y"] + 0.5  # it runs the full height, beside the bar too


# ── The ⋯ menu ──


def test_move_later_and_earlier_keep_the_open_page_open(page):
    _three_pages(page)
    _open_menu(page, 0)
    assert page.is_disabled("#pg-menu-earlier") and page.is_enabled("#pg-menu-later")
    page.click("#pg-menu-later")
    assert _pages(page) == [["b", "c"], ["a"], []]
    assert page.evaluate("StampAlbum._currentPage") == 1  # still the page with "a"
    _open_menu(page, 1)
    page.click("#pg-menu-earlier")
    assert _pages(page) == [["a"], ["b", "c"], []]
    assert page.evaluate("StampAlbum._currentPage") == 0
    _open_menu(page, 2)
    assert page.is_disabled("#pg-menu-later")
    page.keyboard.press("Escape")


def test_moving_a_page_can_be_undone(page):
    _three_pages(page)
    _open_menu(page, 1)
    page.click("#pg-menu-later")
    assert _pages(page) == [["a"], [], ["b", "c"]]
    page.evaluate("StampAlbum.undo()")
    assert _pages(page) == [["a"], ["b", "c"], []]


def test_deleting_a_page_with_items_asks_first(page):
    _three_pages(page)
    asked = []
    page.once("dialog", lambda d: (asked.append(d.message), d.dismiss()))
    _open_menu(page, 1)
    page.click("#pg-menu-delete")
    assert asked == ["Delete page 2 and everything on it? You can undo this with Edit › Undo."]
    assert len(_pages(page)) == 3
    page.once("dialog", lambda d: d.accept())
    _open_menu(page, 1)
    page.click("#pg-menu-delete")
    assert _pages(page) == [["a"], []]
    assert page.evaluate("StampAlbum._currentPage") == 0  # page 1 stays open
    page.evaluate("StampAlbum.undo()")
    assert _pages(page) == [["a"], ["b", "c"], []]


def test_deleting_an_empty_page_does_not_ask(page):
    _three_pages(page)
    asked = []
    page.on("dialog", lambda d: (asked.append(d.message), d.dismiss()))
    page.click('#pg-list .pg-item[data-idx="2"] .pg-thumb')
    _open_menu(page, 2)
    page.click("#pg-menu-delete")
    assert asked == [] and _pages(page) == [["a"], ["b", "c"]]
    assert page.evaluate("StampAlbum._currentPage") == 1


def test_the_last_page_cannot_be_deleted(page):
    page.evaluate("StampAlbum.newAlbum()")
    _open_menu(page, 0)
    assert page.is_disabled("#pg-menu-delete")
    assert page.is_disabled("#pg-menu-earlier") and page.is_disabled("#pg-menu-later")


def test_the_menu_works_by_keyboard(page):
    _three_pages(page)
    more = page.get_by_role("button", name="Page 2: move or delete", exact=True)
    assert more.get_attribute("aria-haspopup") == "menu"
    more.focus()
    page.keyboard.press("Enter")
    assert more.get_attribute("aria-expanded") == "true"
    assert page.evaluate("document.activeElement.id") == "pg-menu-earlier"
    page.keyboard.press("ArrowDown")
    assert page.evaluate("document.activeElement.id") == "pg-menu-later"
    page.keyboard.press("Escape")
    assert page.is_hidden("#pg-menu")
    assert page.evaluate("document.activeElement.getAttribute('aria-label')") == (
        "Page 2: move or delete")
    page.keyboard.press("Enter")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")  # Move later
    assert _pages(page) == [["a"], [], ["b", "c"]]
    assert page.evaluate("document.activeElement.getAttribute('aria-label')") == "Page 3"


def test_edit_menu_delete_page_asks_too(page):
    _three_pages(page)
    asked = []
    page.once("dialog", lambda d: (asked.append(d.message), d.dismiss()))
    page.click("#menu-edit-btn")
    page.click("#menu-del-page")
    assert asked and len(_pages(page)) == 3


# ── Phone ──


def test_on_a_phone_the_strip_is_one_row_in_the_page_sheet(phone):
    # UI review item 7: on a phone the pages are in the Page sheet (test_phone_bar.py)
    _three_pages(phone)
    assert not phone.locator("#pg-strip").is_visible()
    phone.click("#pb-page")
    assert phone.evaluate("document.getElementById('sheet').contains("
                          "document.getElementById('pg-strip'))")
    tops = phone.evaluate("""[...document.querySelectorAll('#pg-list .pg-thumb')]
        .map(b => Math.round(b.getBoundingClientRect().top))""")
    assert len(tops) == 3 and len(set(tops)) == 1
    sizes = phone.evaluate("""[...document.querySelectorAll('#pg-strip button')]
        .map(b => { const r = b.getBoundingClientRect(); return [r.width, r.height]; })""")
    assert all(w >= 40 - 0.5 and h >= 40 - 0.5 for w, h in sizes), sizes
    phone.click('#pg-list .pg-item[data-idx="1"] .pg-thumb')
    assert phone.evaluate("StampAlbum._currentPage") == 1
