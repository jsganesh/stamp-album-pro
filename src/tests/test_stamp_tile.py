# ruff: noqa: F811
"""The Stamp tile and "Other shapes" (UI review item 3, as revised 2026-10-14).

The left panel starts with one "Stamp" tile that adds a rectangle at the stamp size
used last: 25 × 30 mm to begin with, then whatever the user last typed into W or H,
or dragged a stamp to. The size shows on the tile and is remembered on this computer.
Opening a file or a template doesn't change it. The other shapes (oval, diamond,
triangle, hexagon, octagon, pentagon) take the same size; Free shape keeps its own.
They fold under "Other shapes", shut at first and then as the user left them.
"""

import pytest
from test_accessibility import _axe
from test_starter_templates_ui import _open_template
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)
from test_zoom_ui import phone  # noqa: F401  (fixture)

MM = 2.5  # canvas px per mm
SHAPES = ["oval", "diamond", "triangle", "hexagon", "octagon", "pentagon"]


def _empty(page):
    page.evaluate("StampAlbum.select(null); StampAlbum.newAlbum();"
                  " StampAlbum._snapEnabled = false; StampAlbum.render()")
    page.select_option("#grid", "0")


def _last(page):
    """The newest item: its type, shape and size in mm."""
    return page.evaluate("""(() => { const e = StampAlbum.E[StampAlbum.E.length - 1];
        return { t: e.t, s: e.s, w: e.w / 2.5, h: e.h / 2.5 }; })()""")


def _type_size(page, w, h):
    for sel, v in (("#pw", w), ("#ph", h)):
        page.fill(sel, str(v))
        page.press(sel, "Tab")


def _reload(page):
    page.reload()
    wait_for_app(page)
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    page.evaluate("StampAlbum.setZoomMode('actual')")


def _shapes_open(page):
    return page.get_attribute("#shapes-toggle", "aria-expanded") == "true"


# ── The Stamp tile ──

def test_stamp_tile_comes_first_and_shows_its_size(page):
    first = page.evaluate("document.querySelector('#sidebar .p-item').id")
    assert first == "p-stamp"
    assert page.inner_text("#p-stamp .lbl") == "Stamp"
    assert page.inner_text("#stamp-size") == "25 × 30 mm"
    assert "last stamp size" in page.inner_text("#hint-stamp")
    assert page.get_attribute("#p-stamp", "aria-label") == "Add Stamp"
    assert page.get_attribute("#p-stamp", "aria-describedby") == "stamp-size hint-stamp"


def test_stamp_tile_adds_a_25_by_30_mm_rectangle(page):
    _empty(page)
    page.click("#p-stamp")
    assert _last(page) == {"t": "stamp", "s": "rectangle", "w": 25, "h": 30}


def test_typed_size_is_used_for_the_next_stamp(page):
    _empty(page)
    page.click("#p-stamp")
    _type_size(page, 19, 22)
    assert page.inner_text("#stamp-size") == "19 × 22 mm"
    page.click("#p-stamp")
    assert _last(page) == {"t": "stamp", "s": "rectangle", "w": 19, "h": 22}


def test_a_typed_fraction_is_kept(page):
    _empty(page)
    page.click("#p-stamp")
    _type_size(page, 21.25, 24.5)
    assert page.inner_text("#stamp-size") == "21.25 × 24.5 mm"
    page.click("#p-stamp")
    assert _last(page)["w"] == pytest.approx(21.25, abs=0.01)  # kept to 1/100 px


def test_dragging_a_handle_sets_the_size(page):
    _empty(page)
    page.select_option("#grid", "5")  # the drag snaps to whole 5 mm steps
    page.click("#p-stamp")
    handle = page.locator("#page .cel.selected .rh[data-h='se']")
    box = handle.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 10 * MM + 1, y + 5 * MM + 1, steps=4)  # the page is at Actual size
    page.mouse.up()
    assert page.inner_text("#stamp-size") == "35 × 35 mm"
    page.click("#p-stamp")
    assert (_last(page)["w"], _last(page)["h"]) == (35, 35)


def test_a_click_on_a_handle_without_moving_changes_nothing(page):
    _empty(page)
    page.evaluate("""StampAlbum.add({ t: 'stamp', s: 'rectangle', x: 100, y: 100,
                                     w: 40 * 2.5, h: 20 * 2.5 })""")
    page.locator("#page .cel.selected .rh[data-h='se']").click()
    assert page.inner_text("#stamp-size") == "25 × 30 mm"


def test_the_size_is_remembered_after_closing(page):
    _empty(page)
    page.click("#p-stamp")
    _type_size(page, 19, 22)
    _reload(page)
    assert page.inner_text("#stamp-size") == "19 × 22 mm"
    _empty(page)
    page.click("#p-stamp")
    assert (_last(page)["w"], _last(page)["h"]) == (19, 22)


def test_a_broken_stored_size_falls_back_to_25_by_30(page):
    page.evaluate("localStorage.setItem('stampalbum-stamp-size', '{\"w\": 0, \"h\": \"x\"}')")
    _reload(page)
    assert page.inner_text("#stamp-size") == "25 × 30 mm"
    page.evaluate("localStorage.setItem('stampalbum-stamp-size', 'not json')")
    _reload(page)
    assert page.inner_text("#stamp-size") == "25 × 30 mm"


def test_opening_a_template_keeps_the_size(page):
    _open_template(page, "Exhibition page")
    assert page.inner_text("#stamp-size") == "25 × 30 mm"


def test_opening_a_file_keeps_the_size(page):
    page.evaluate("""StampAlbum.openAlbum('mine.slbum', 'ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\n'
        + 'STAMP_ADD_AT(24 24 40 50 "x" "" "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)'
        + '\\n')""")
    assert page.evaluate("StampAlbum.E.filter(e => e.t === 'stamp').length") == 1
    assert page.inner_text("#stamp-size") == "25 × 30 mm"


def test_text_free_shapes_and_pictures_dont_set_the_size(page):
    _empty(page)
    page.click(".p-item[data-st='label']")
    _type_size(page, 60, 10)
    page.evaluate("document.getElementById('shapes-toggle').click()")
    page.click(".p-item[data-t='freehand']")
    _type_size(page, 70, 50)
    assert page.inner_text("#stamp-size") == "25 × 30 mm"


# ── Other shapes ──

def test_other_shapes_start_folded(page):
    assert not _shapes_open(page)
    assert page.is_hidden("#shapes-body")
    for s in SHAPES:
        assert page.is_hidden(f".p-item[data-s='{s}']"), s
    assert page.is_hidden(".p-item[data-t='freehand']")
    assert page.inner_text("#shapes-toggle") == "Other shapes"


def test_other_shapes_open_and_shut(page):
    page.click("#shapes-toggle")
    assert _shapes_open(page)
    names = page.evaluate("""[...document.querySelectorAll('#shapes-body .p-item')]
        .map(i => i.dataset.s && i.dataset.t === 'stamp' ? i.dataset.s : i.dataset.t)""")
    assert names == SHAPES + ["freehand"]
    assert page.inner_text("#hint-free") == "For die-cut or irregular stamps"
    page.click("#shapes-toggle")
    assert not _shapes_open(page)
    assert page.is_hidden("#shapes-body")


def test_rectangle_is_only_the_stamp_tile(page):
    assert page.locator("#sidebar .p-item[data-s='rectangle']").count() == 1


@pytest.mark.parametrize("opened", [True, False])
def test_other_shapes_stay_as_left(page, opened):
    page.click("#shapes-toggle")
    if not opened:
        page.click("#shapes-toggle")
    _reload(page)
    assert _shapes_open(page) is opened
    assert page.is_hidden("#shapes-body") is not opened


def test_other_shapes_use_the_last_size(page):
    _empty(page)
    page.click("#p-stamp")
    _type_size(page, 30, 40)
    page.click("#shapes-toggle")
    for s in SHAPES:
        page.click(f".p-item[data-s='{s}']")
        assert _last(page) == {"t": "stamp", "s": s, "w": 30, "h": 40}, s


def test_free_shape_keeps_its_own_size(page):
    _empty(page)
    page.click("#p-stamp")
    _type_size(page, 30, 40)
    page.click("#shapes-toggle")
    page.click(".p-item[data-t='freehand']")
    assert _last(page) == {"t": "freehand", "s": "rectangle", "w": 40, "h": 32}


def test_a_dragged_stamp_carries_the_last_size(page):
    _empty(page)
    page.click("#p-stamp")
    _type_size(page, 19, 22)
    _empty(page)
    page.drag_and_drop("#p-stamp", "#page", target_position={"x": 200, "y": 200})
    assert (_last(page)["w"], _last(page)["h"]) == (19, 22)


# ── Readable, accessible, and on a phone ──

def test_sidebar_passes_axe_with_shapes_open(page):
    page.click("#shapes-toggle")
    assert _axe(page, "#sidebar") == []


def test_fold_button_is_big_enough(page):
    box = page.locator("#shapes-toggle").bounding_box()
    assert box["height"] >= 40
    size = "parseFloat(getComputedStyle(document.querySelector('#shapes-toggle')).fontSize)"
    assert page.evaluate(size) >= 14


def test_phone_tap_on_the_stamp_tile_adds_the_last_size(phone):
    phone.evaluate("StampAlbum.newAlbum(); StampAlbum.render()")
    phone.evaluate("""() => {
        const it = document.getElementById('p-stamp'), r = it.getBoundingClientRect();
        const t = new Touch({ identifier: 1, target: it,
                              clientX: r.left + r.width / 2, clientY: r.top + r.height / 2 });
        const o = (now) => ({ touches: now, changedTouches: [t], bubbles: true, cancelable: true });
        it.dispatchEvent(new TouchEvent('touchstart', o([t])));
        it.dispatchEvent(new TouchEvent('touchend', o([])));
    }""")
    assert _last(phone) == {"t": "stamp", "s": "rectangle", "w": 25, "h": 30}
    assert phone.js_errors == []
