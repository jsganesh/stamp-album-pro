# ruff: noqa: F811
"""Print preview (UI review item 8, option A; owner's choices 2026-10-16: "Print preview" on the
toolbar button, fit only, no Actual size). One page at a time, fitted to the window, opening on
the page being edited, with page arrows; no Refresh; Export is the one main button."""

import playwright.sync_api as pw
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)
from test_zoom_ui import _desktop, _open, phone  # noqa: F401  (fixture)

# The drawn page's box on screen and the space it sits in
GEOMETRY = r"""(() => { const b = document.getElementById('pv-box').getBoundingClientRect();
    const body = document.getElementById('preview-body'), cs = getComputedStyle(body);
    return { w: b.width, h: b.height,
             aw: body.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight),
             ah: body.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom),
             scale: Number(document.getElementById('pv-box').dataset.scale) }; })()"""

# The labels of the stamps on the printed page that shows
SHOWN = r"""(() => { const d = document.getElementById('preview-frame').contentDocument;
    return [...d.querySelectorAll('.page')].filter(p => p.style.display !== 'none')
        .map(p => p.textContent.replace(/\s+/g, ' ').trim()); })()"""


def _three_pages(pg, current=0, last_empty=False):
    """Pages with stamps "Alpha", "Bravo", "Charlie" (or an empty third page)."""
    pg.evaluate("""([cur, lastEmpty]) => { const S = StampAlbum; S.newAlbum();
        const st = (id) => ({id, t: 'stamp', s: 'rectangle', x: 100, y: 100, w: 60, h: 70,
                             lbl: id});
        S._pages = [[st('Alpha')], [st('Bravo')], lastEmpty ? [] : [st('Charlie')]];
        S.E = JSON.parse(JSON.stringify(S._pages[cur])); S._currentPage = cur;
        S.renderPageDots(); S.render(); }""", [current, last_empty])


def _open_preview(pg):
    pg.evaluate("StampAlbum.openPreview()")  # resolves once the page is drawn
    assert pg.is_visible("#preview-overlay")


def _close(pg):
    pg.evaluate("StampAlbum.closePreview()")


# ── Names ──


def test_called_print_preview_everywhere(page):
    assert page.inner_text("#preview-title") == "Print preview"
    assert page.inner_text("#btn-preview .lbl") == "Print preview"
    assert page.get_attribute("#btn-preview", "title") == "Print preview (F5)"
    assert page.evaluate("document.getElementById('menu-preview').firstChild.textContent") \
        == "Print preview"
    assert page.get_attribute("#preview-overlay", "aria-labelledby") == "preview-title"
    assert page.get_attribute("#preview-overlay", "aria-modal") == "true"


def test_no_refresh_button_and_export_is_the_main_button(page):
    assert page.locator("#btn-preview-refresh").count() == 0
    assert page.locator("#preview-overlay button", has_text="Refresh").count() == 0
    assert "primary" in (page.get_attribute("#btn-preview-export", "class") or "")
    assert page.locator("#preview-overlay button.primary").count() == 1
    close_bg = page.evaluate(
        "getComputedStyle(document.getElementById('btn-preview-close')).backgroundColor")
    export_bg = page.evaluate(
        "getComputedStyle(document.getElementById('btn-preview-export')).backgroundColor")
    assert export_bg == "rgb(139, 26, 26)" and close_bg == "rgb(255, 255, 255)"


def test_no_pop_up_messages_while_drawing(page):
    _three_pages(page)
    page.evaluate("document.querySelectorAll('.toast').forEach(t => t.remove())")
    _open_preview(page)
    texts = page.evaluate("[...document.querySelectorAll('.toast')].map(t => t.textContent)")
    assert not any("review" in t for t in texts), texts
    assert page.is_hidden("#pv-loading")  # the quiet note is gone once the page is drawn
    _close(page)


# ── Pages ──


def test_opens_on_the_page_being_edited(page):
    for cur, label in [(0, "Alpha"), (1, "Bravo"), (2, "Charlie")]:
        _three_pages(page, cur)
        _open_preview(page)
        assert page.evaluate(SHOWN) == [label]
        assert page.inner_text("#pv-count") == f"Page {cur + 1} of 3"
        _close(page)


def test_an_empty_last_page_shows_the_last_printed_page(page):
    """The export leaves out empty pages at the end, so the preview shows what will print."""
    _three_pages(page, 2, last_empty=True)
    _open_preview(page)
    assert page.evaluate(SHOWN) == ["Bravo"]
    assert page.inner_text("#pv-count") == "Page 2 of 2"
    _close(page)


def test_arrows_step_through_the_pages(page):
    _three_pages(page, 0)
    _open_preview(page)
    assert page.is_disabled("#pv-prev") and page.is_enabled("#pv-next")
    page.get_by_role("button", name="Next page").click()
    assert page.evaluate(SHOWN) == ["Bravo"]
    page.get_by_role("button", name="Next page").click()
    assert page.evaluate(SHOWN) == ["Charlie"]
    assert page.inner_text("#pv-count") == "Page 3 of 3"
    assert page.is_disabled("#pv-next") and page.is_enabled("#pv-prev")
    page.get_by_role("button", name="Previous page").click()
    assert page.evaluate(SHOWN) == ["Bravo"]
    assert page.evaluate("StampAlbum._currentPage") == 0  # the editor's page is unchanged
    _close(page)


def test_arrow_keys_home_and_end(page):
    _three_pages(page, 1)
    _open_preview(page)
    page.keyboard.press("ArrowRight")
    assert page.evaluate(SHOWN) == ["Charlie"]
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowLeft")
    assert page.evaluate(SHOWN) == ["Alpha"]
    page.keyboard.press("End")
    assert page.evaluate(SHOWN) == ["Charlie"]
    page.keyboard.press("Home")
    assert page.evaluate(SHOWN) == ["Alpha"]
    _close(page)


def test_one_page_has_no_arrows(page):
    page.evaluate("""() => { const S = StampAlbum; S.newAlbum();
        S.E.push({id: 'x', t: 'stamp', s: 'rectangle', x: 100, y: 100, w: 60, h: 70});
        S.render(); }""")
    _open_preview(page)
    assert page.is_hidden("#pv-pager")
    _close(page)


# ── Keys and closing ──


def test_escape_closes_and_does_not_reach_the_editor(page):
    _three_pages(page, 0)
    page.evaluate("StampAlbum.select(StampAlbum.E[0].id)")
    _open_preview(page)
    page.keyboard.press("Escape")
    assert page.is_hidden("#preview-overlay")
    assert page.evaluate("StampAlbum.sel") == "Alpha"  # Escape did not also deselect


def test_editor_shortcuts_do_nothing_while_open(page):
    _three_pages(page, 0)
    page.evaluate("StampAlbum.select(StampAlbum.E[0].id)")
    _open_preview(page)
    page.evaluate("document.activeElement.blur()")  # even with the focus outside the window
    page.keyboard.press("Delete")
    page.keyboard.press("Control+d")
    assert page.evaluate("StampAlbum.E.map(e => e.id)") == ["Alpha"]
    page.keyboard.press("ArrowRight")
    assert page.evaluate(SHOWN) == ["Bravo"]
    page.keyboard.press("Escape")
    assert page.is_hidden("#preview-overlay")


def test_f5_opens_it_and_close_returns_the_focus(page):
    _three_pages(page, 0)
    page.focus("#btn-preview")
    page.keyboard.press("F5")
    page.wait_for_selector("#pv-box[data-scale]", state="attached")
    assert page.is_visible("#preview-overlay")
    assert page.evaluate("document.activeElement.id") == "btn-preview-close"
    page.click("#btn-preview-close")
    assert page.is_hidden("#preview-overlay")
    assert page.evaluate("document.activeElement.id") == "btn-preview"


def test_a_paper_change_while_open_redraws_it_on_the_same_page(page):
    """Page setup's change (and the fit prompt's) asks for a redraw, as before."""
    _three_pages(page, 1)
    _open_preview(page)
    w0 = page.evaluate(GEOMETRY)
    page.evaluate("StampAlbum.applyPageSize(297, 210); StampAlbum.schedulePreviewRefresh()")
    for _ in range(100):
        g = page.evaluate(GEOMETRY)
        if g["w"] > g["h"]:
            break
        page.wait_for_timeout(50)
    assert g["w"] > g["h"] and w0["h"] > w0["w"]
    assert page.evaluate(SHOWN) == ["Bravo"]  # stays on the page shown
    _close(page)
    page.evaluate("StampAlbum.applyPageSize(210, 297)")


# ── Size on screen ──


def _check_fit(g):
    assert g["w"] <= g["aw"] + 0.5 and g["h"] <= g["ah"] + 0.5
    # one side touches the space (to the rounding), unless it stopped at 200%
    assert g["scale"] == 2 or g["aw"] - g["w"] < 2 or g["ah"] - g["h"] < 2, g


def test_whole_page_fits_on_a_laptop_and_grows_on_a_big_screen(base_url):
    with pw.sync_playwright() as p:
        for size, larger_than_100 in [({"width": 1512, "height": 982}, False),
                                      ({"width": 2560, "height": 1600}, True)]:
            browser, pg = _desktop(p, size)
            _open(pg, base_url)
            _three_pages(pg, 0)
            _open_preview(pg)
            g = pg.evaluate(GEOMETRY)
            _check_fit(g)
            assert (g["scale"] > 1) == larger_than_100, g
            browser.close()


def test_whole_page_fits_on_a_phone(phone):
    _three_pages(phone, 1)
    _open_preview(phone)
    g = phone.evaluate(GEOMETRY)
    _check_fit(g)
    assert phone.evaluate(SHOWN) == ["Bravo"]
    # Export and Close stay on one row, and the page arrows are on screen
    e = phone.locator("#btn-preview-export").bounding_box()
    c = phone.locator("#btn-preview-close").bounding_box()
    assert abs(e["y"] - c["y"]) < 1
    n = phone.locator("#pv-next").bounding_box()
    assert n["y"] + n["height"] <= phone.viewport_size["height"]
    phone.locator("#pv-next").tap()
    assert phone.evaluate(SHOWN) == ["Charlie"]
    _close(phone)


def test_the_window_resizing_refits_the_page(base_url):
    with pw.sync_playwright() as p:
        browser, pg = _desktop(p, {"width": 1400, "height": 900})
        _open(pg, base_url)
        _three_pages(pg, 0)
        _open_preview(pg)
        s0 = pg.evaluate(GEOMETRY)["scale"]
        pg.set_viewport_size({"width": 1400, "height": 600})
        for _ in range(40):
            g = pg.evaluate(GEOMETRY)
            if g["scale"] < s0:
                break
            pg.wait_for_timeout(50)
        assert g["scale"] < s0
        _check_fit(g)
        browser.close()
