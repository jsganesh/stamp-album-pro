# ruff: noqa: F811
"""The phone layout (UI review item 7, option A; owner's choices 2026-10-18, mockup approved).

At phone width a bar along the bottom has Add, Undo, Properties and Page. Add, Properties and
Page each open a sheet from the bottom holding the panel they replace (the palette, the
selected item's settings, the pages and the album settings); Undo acts at once. The side
panels, their edge handles, the bar above the page, the page strip and the status bar leave
the screen, so the page has the room. With more than one page a small pager floats over the
page. Properties opens only from its button. The top bar keeps its menus."""

import playwright.sync_api as pw
import pytest
from test_accessibility import _axe
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)
from test_zoom_ui import IPHONE, phone  # noqa: F401  (fixture)

BAR = ["pb-add", "pb-undo", "pb-props", "pb-page"]


def _shown(pg, sel):
    """Whether something is on screen: displayed, visible and with a size."""
    return pg.evaluate(f"""(() => {{ const e = document.querySelector({sel!r});
        if (!e) return false;
        const r = e.getBoundingClientRect();
        return e.checkVisibility({{visibilityProperty: true}}) && r.width > 0 && r.height > 0;
        }})()""")


# Undo and Properties stay tappable when they have nothing to do (aria-disabled), so they can
# say why; Playwright waits for such buttons to be enabled unless forced.

def _fresh(pg):
    """A new album with one stamp ('a') on its one page; nothing selected, nothing to undo."""
    pg.evaluate("""() => { const S = StampAlbum; S.newAlbum();
        S.E.push({id: 'a', t: 'stamp', s: 'rectangle', x: 100, y: 100, w: 60, h: 75, lbl: 'One',
                  font: 'HN', fs: 12, bdr: 'solid', bdrC: '#000', bdrW: 0.5});
        S._pages[0] = S.E; S.sel = null; S.renderPageDots(); S.render(); S.updateProps();
        S.resetUndo(); }""")


def _count(pg):
    return pg.evaluate("StampAlbum.E.length")


def _toast(pg):
    return pg.evaluate("document.getElementById('toast-container').textContent")


def _sheet_open(pg):
    return _shown(pg, "#sheet")


# ── The bar ──


def test_the_bar_has_four_buttons_along_the_bottom(phone):
    assert _shown(phone, "#phone-bar")
    names = phone.evaluate("""[...document.querySelectorAll('#phone-bar button')]
        .map(b => [b.id, b.textContent.trim()])""")
    assert names == [["pb-add", "Add"], ["pb-undo", "Undo"], ["pb-props", "Properties"],
                     ["pb-page", "Page"]]
    bar = phone.locator("#phone-bar").bounding_box()
    assert abs(bar["y"] + bar["height"] - IPHONE["height"]) <= 1
    for b in BAR:
        box = phone.locator("#" + b).bounding_box()
        assert box["height"] >= 44 - 0.5 and box["width"] >= 44 - 0.5, b
        size = phone.evaluate(f"parseFloat(getComputedStyle(document.getElementById('{b}'))"
                              ".fontSize)")
        assert size >= 16, b


def test_the_panels_and_bars_around_the_page_leave_the_phone(phone):
    for sel in ("#sidebar", "#rp", "#sb-handle", "#rp-handle", "#ca-toolbar", "#status-bar",
                "#pg-strip"):
        assert not _shown(phone, sel), sel
    # The page area runs from the top bar to the bottom bar
    tb = phone.locator("#tb").bounding_box()
    wrap = phone.locator("#page-wrap").bounding_box()
    bar = phone.locator("#phone-bar").bounding_box()
    assert abs(wrap["y"] - (tb["y"] + tb["height"])) <= 1
    assert abs(wrap["y"] + wrap["height"] - bar["y"]) <= 3  # the shut wizard and DSL panels' edges
    assert phone.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_the_top_bar_keeps_its_menus(phone):
    for b in ("menu-file-btn", "menu-edit-btn", "menu-view-btn", "menu-help-btn", "btn-export"):
        assert _shown(phone, "#" + b), b


def test_a_computer_shows_no_bar_and_keeps_its_panels(page):
    assert not _shown(page, "#phone-bar")
    assert not _shown(page, "#pg-pager")
    for sel in ("#sidebar", "#rp", "#ca-toolbar", "#status-bar", "#pg-strip"):
        assert _shown(page, sel), sel


# ── Add ──


def test_add_opens_the_palette_in_a_sheet(phone):
    phone.click("#pb-add")
    assert _sheet_open(phone)
    assert phone.get_attribute("#pb-add", "aria-expanded") == "true"
    assert phone.inner_text("#sheet-title") == "Add to the page"
    assert phone.evaluate("document.getElementById('sheet').contains(document.activeElement)")
    for sel in ("#p-stamp", "#shapes-toggle", "#img-upl-btn"):
        assert _shown(phone, sel), sel
        assert phone.evaluate(f"document.getElementById('sheet').contains("
                              f"document.querySelector('{sel}'))"), sel
    # The sheet leaves some of the page in view above it
    sheet = phone.locator("#sheet").bounding_box()
    assert sheet["y"] >= IPHONE["height"] * 0.25


def test_tapping_a_tile_adds_it_and_closes_the_sheet(phone):
    _fresh(phone)
    phone.click("#pb-add")
    phone.click("#p-stamp")
    assert _count(phone) == 2
    assert not _sheet_open(phone)
    assert phone.get_attribute("#pb-add", "aria-expanded") == "false"
    assert "Drag it into place" in _toast(phone)


def test_the_sheet_closes_with_close_escape_or_a_tap_above_it(phone):
    phone.click("#pb-add")
    phone.click("#sheet-close")
    assert not _sheet_open(phone)
    assert phone.evaluate("document.activeElement.id") == "pb-add"
    phone.click("#pb-add")
    phone.keyboard.press("Escape")
    assert not _sheet_open(phone)
    phone.click("#pb-add")
    phone.mouse.click(IPHONE["width"] / 2, 80)  # on the scrim, above the sheet
    assert not _sheet_open(phone)
    phone.click("#pb-add")
    phone.click("#pb-add")  # the same button again
    assert not _sheet_open(phone)


def test_closing_puts_the_panels_back(phone):
    homes = {"#sb-body": "sidebar", "#rp-content": "rp", "#rp-none": "rp", "#pg-strip": "ca-body"}
    _fresh(phone)
    phone.evaluate("StampAlbum.select('a')")
    for b in ("#pb-add", "#pb-props", "#pb-page"):
        phone.click(b)
        phone.click("#sheet-close")
    for sel, home in homes.items():
        assert phone.evaluate(f"document.querySelector('{sel}').parentElement.id") == home, sel


def test_a_wider_window_closes_the_sheet(phone):
    phone.click("#pb-page")
    phone.set_viewport_size({"width": 1024, "height": 768})
    phone.wait_for_timeout(100)
    assert not _sheet_open(phone)
    assert phone.evaluate("document.getElementById('pg-strip').parentElement.id") == "ca-body"
    assert phone.evaluate("document.getElementById('rp-none').parentElement.id") == "rp"
    assert _shown(phone, "#pg-strip")


# ── Undo ──


def test_undo_says_when_there_is_nothing_to_undo(phone):
    _fresh(phone)
    assert phone.get_attribute("#pb-undo", "aria-disabled") == "true"
    phone.click("#pb-undo", force=True)
    assert "Nothing to undo" in _toast(phone)
    assert _count(phone) == 1


def test_undo_takes_back_the_last_change(phone):
    _fresh(phone)
    phone.click("#pb-add")
    phone.click("#p-stamp")
    assert phone.get_attribute("#pb-undo", "aria-disabled") == "false"
    phone.click("#pb-undo", force=True)
    assert _count(phone) == 1
    assert phone.get_attribute("#pb-undo", "aria-disabled") == "true"


# ── Properties ──


def test_properties_asks_for_an_item_first(phone):
    _fresh(phone)
    assert phone.get_attribute("#pb-props", "aria-disabled") == "true"
    phone.click("#pb-props", force=True)
    assert not _sheet_open(phone)
    assert "Tap a stamp or some text on the page first" in _toast(phone)


def test_selecting_does_not_open_properties_by_itself(phone):
    _fresh(phone)
    phone.locator('.cel[data-id="a"]').click()
    assert phone.evaluate("StampAlbum.sel") == "a"
    assert not _sheet_open(phone)
    assert phone.get_attribute("#pb-props", "aria-disabled") == "false"


def test_properties_shows_the_selected_item(phone):
    _fresh(phone)
    phone.evaluate("StampAlbum.select('a')")
    phone.click("#pb-props", force=True)
    assert _sheet_open(phone)
    assert phone.inner_text("#sheet-title") == "Stamp"
    assert _shown(phone, "#plbl") and _shown(phone, "#px")
    assert not _shown(phone, "#rp-none")
    phone.fill("#plbl", "Penny Black")
    phone.dispatch_event("#plbl", "change")
    assert phone.evaluate("StampAlbum.E[0].lbl") == "Penny Black"


def test_properties_has_duplicate_and_delete(phone):
    _fresh(phone)
    phone.evaluate("StampAlbum.select('a')")
    phone.click("#pb-props", force=True)
    assert phone.inner_text("#sheet-dup") == "Duplicate"
    assert phone.inner_text("#sheet-del") == "Delete"
    phone.click("#sheet-dup")
    assert _count(phone) == 2 and _sheet_open(phone)
    phone.once("dialog", lambda d: d.accept())  # Delete asks first, as on a computer
    phone.click("#sheet-del")
    assert _count(phone) == 1
    assert not _sheet_open(phone)  # nothing is selected now


def test_undo_with_properties_open_closes_it_when_the_item_goes(phone):
    _fresh(phone)
    phone.click("#pb-add")
    phone.click("#p-stamp")
    new = phone.evaluate("StampAlbum.sel")
    assert new and new != "a"
    phone.click("#pb-props", force=True)
    assert _sheet_open(phone)
    phone.evaluate("StampAlbum.undo()")
    assert not _sheet_open(phone)
    assert phone.get_attribute("#pb-props", "aria-disabled") == "true"


# ── Page ──


def test_page_shows_the_pages_and_the_album_settings(phone):
    _fresh(phone)
    phone.evaluate("StampAlbum.select('a')")  # still the album settings, not the stamp
    phone.click("#pb-page")
    assert _sheet_open(phone)
    assert phone.inner_text("#sheet-title") == "Pages and album"
    for sel in ("#pg-strip", "#pg-add", "#btn-page-setup", "#def-bdr", "#def-theme", "#grid"):
        assert _shown(phone, sel), sel
    assert not _shown(phone, "#rp-content")
    assert phone.evaluate("StampAlbum.sel") == "a"
    # The pages come first, in one row
    strip = phone.locator("#pg-strip").bounding_box()
    paper = phone.locator("#btn-page-setup").bounding_box()
    assert strip["y"] < paper["y"]


def test_adding_a_page_from_the_sheet(phone):
    _fresh(phone)
    assert not _shown(phone, "#pg-pager")
    phone.click("#pb-page")
    phone.click("#pg-add")
    assert not _sheet_open(phone)
    assert phone.evaluate("[StampAlbum._pages.length, StampAlbum._currentPage]") == [2, 1]
    assert phone.inner_text("#pb-page") == "Page 2"
    assert _shown(phone, "#pg-pager")
    assert phone.inner_text("#pg-pager-label") == "Page 2 of 2"


def test_the_pager_changes_page(phone):
    _fresh(phone)
    phone.click("#pb-page")
    phone.click("#pg-add")
    assert phone.is_disabled("#pg-pager-next")
    phone.click("#pg-pager-prev")
    assert phone.evaluate("StampAlbum._currentPage") == 0
    assert phone.inner_text("#pg-pager-label") == "Page 1 of 2"
    assert phone.inner_text("#pb-page") == "Page 1"
    assert phone.is_disabled("#pg-pager-prev")
    for b in ("#pg-pager-prev", "#pg-pager-next"):
        box = phone.locator(b).bounding_box()
        assert box["width"] >= 44 - 0.5 and box["height"] >= 44 - 0.5, b


def test_tapping_a_page_picture_goes_there_and_closes_the_sheet(phone):
    _fresh(phone)
    phone.evaluate("StampAlbum.addPage()")
    phone.click("#pb-page")
    phone.click('#pg-list .pg-item[data-idx="0"] .pg-thumb')
    assert phone.evaluate("StampAlbum._currentPage") == 0
    assert not _sheet_open(phone)


# ── Not saved, and looks ──


def test_not_saved_shows_in_the_top_bar(phone):
    _fresh(phone)
    assert not _shown(phone, "#tb-dirty")
    phone.click("#pb-add")
    phone.click("#p-stamp")
    assert _shown(phone, "#tb-dirty")
    tb = phone.locator("#tb").bounding_box()
    dirty = phone.locator("#tb-dirty").bounding_box()
    assert dirty["x"] >= 0 and dirty["x"] + dirty["width"] <= tb["width"]
    assert phone.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("which", ["none", "pb-add", "pb-props", "pb-page"])
def test_accessibility_with_each_sheet(phone, which):
    _fresh(phone)
    phone.evaluate("StampAlbum.select('a')")
    if which != "none":
        phone.click("#" + which)
    assert _axe(phone) == []


def test_longer_words_still_fit_the_bar(base_url):
    with pw.sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport=IPHONE, is_mobile=True, has_touch=True)
        pg.goto(base_url + "/?lang=pseudo")
        wait_for_app(pg)
        cut = pg.evaluate("""[...document.querySelectorAll('#phone-bar button, #pg-pager *')]
            .filter(b => b.scrollWidth > b.clientWidth + 1).map(b => b.id)""")
        browser.close()
    assert cut == []
