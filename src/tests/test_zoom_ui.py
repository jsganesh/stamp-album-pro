# ruff: noqa: F811
"""Zoom to fit on phones and narrow windows.

The A4 page (525 px at 2.5 px/mm) used to be wider than an iPhone's screen, and
its left side could not be scrolled to. Zoom now scales the page on screen only:
element positions stay in canvas px, so a drag of N screen px moves an item by
N / zoom canvas px.
"""

import os

import playwright.sync_api as pw
import pytest
from test_ui_smoke import base_url, wait_for_app  # noqa: F401  (fixtures)

IPHONE = {"width": 390, "height": 664}
IPHONE_LANDSCAPE = {"width": 750, "height": 342}


@pytest.fixture
def phone(base_url):
    with pw.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:
            if os.environ.get("STAMP_ALBUM_REQUIRE_BROWSER"):
                raise
            pytest.skip(f"chromium unavailable: {exc}")
        ctx = browser.new_context(viewport=IPHONE, device_scale_factor=3,
                                  is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        pg.js_errors = []
        pg.on("pageerror", lambda e: pg.js_errors.append(str(e)))
        pg.goto(base_url + "/")
        wait_for_app(pg)
        pg.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
        _settle(pg)  # a phone starts with the side panels sliding shut
        yield pg
        assert pg.js_errors == []
        browser.close()


def _settle(pg):
    """Wait until the zoom stops changing: panels slide open or shut over 0.2 s."""
    pg.evaluate(
        """new Promise(done => { let last = -1, same = 0;
        (function tick() { const z = StampAlbum.zoom;
          same = z === last ? same + 1 : 0; last = z;
          if (same >= 15) done(); else requestAnimationFrame(tick); })(); })"""
    )


def _geometry(pg):
    return pg.evaluate(
        """(()=>{const w=document.getElementById('page-wrap'), p=document.getElementById('page');
        const cs=getComputedStyle(w), wr=w.getBoundingClientRect(), pr=p.getBoundingClientRect();
        return {zoom: StampAlbum.zoom, mode: StampAlbum.zoomMode,
          wrapLeft: wr.left + w.clientLeft + parseFloat(cs.paddingLeft),
          visibleRight: wr.left + w.clientLeft + w.clientWidth,
          avail: w.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight),
          scrollW: w.scrollWidth, clientW: w.clientWidth,
          left: pr.left, top: pr.top, width: pr.width, height: pr.height}})()"""
    )


def _add_item(pg):
    """Add a palette item at the page centre and return its id (selected)."""
    eid = pg.evaluate(
        """(()=>{const before=new Set(StampAlbum.E.map(e=>e.id));
        const it=document.querySelector('.p-item[draggable]');
        StampAlbum.addAtCentre(StampAlbum.paletteElement(StampAlbum.paletteItemSpec(it),0,0));
        const el=StampAlbum.E.find(e=>!before.has(e.id));
        StampAlbum.select(el.id); return el.id})()"""
    )
    _settle(pg)
    return eid


def _item(pg, eid):
    return pg.evaluate(
        "id => { const e = StampAlbum.E.find(x => x.id === id);"
        " return {x: e.x, y: e.y, w: e.w, h: e.h}; }",
        eid,
    )


def _centre_on_screen(pg, eid):
    return pg.evaluate(
        f"""(()=>{{const r=document.querySelector('.cel[data-id="{eid}"]').getBoundingClientRect();
        return [r.left + r.width/2, r.top + r.height/2]}})()"""
    )


def _touch_drag(pg, x0, y0, dx, dy, steps=5):
    """A one-finger drag, as the TouchEvents iOS Safari sends.

    Synthetic events: headless Chromium's emulated touch hands the gesture to
    scrolling and sends no touchmove, so CDP touch input can't drive this.
    """
    pg.evaluate(
        f"""(()=>{{const t=document.elementFromPoint({x0},{y0});
        const pt=(x,y)=>new Touch({{identifier:1,target:t,clientX:x,clientY:y}});
        const fire=(tgt,type,x,y,end)=>{{const p=pt(x,y);
          tgt.dispatchEvent(new TouchEvent(type,{{bubbles:true,cancelable:true,
            touches:end?[]:[p],targetTouches:end?[]:[p],changedTouches:[p]}}));}};
        fire(t,'touchstart',{x0},{y0});
        for(let i=1;i<={steps};i++) fire(t,'touchmove',{x0}+{dx}*i/{steps},{y0}+{dy}*i/{steps});
        fire(t,'touchend',{x0}+{dx},{y0}+{dy},true);}})()"""
    )


def test_phone_fits_the_page_width(phone):
    g = _geometry(phone)
    assert g["mode"] == "fit-width"
    assert 0.5 < g["zoom"] < 1, g
    # The whole width of the page is on screen, inside the canvas area: no sideways scroll.
    assert g["width"] <= g["avail"] + 0.5, g
    assert g["left"] >= g["wrapLeft"] - 0.5, g
    assert g["scrollW"] <= g["clientW"], g
    # Still A4 in the editor's units; only the drawing is scaled.
    assert phone.evaluate("StampAlbum._pw") == 525
    assert abs(g["width"] - 525 * g["zoom"]) < 0.01 and abs(g["height"] - 742.5 * g["zoom"]) < 0.01
    assert phone.locator("#sb-zoom").inner_text() == f"{round(g['zoom'] * 100)}%"


def test_actual_size_keeps_the_left_edge_reachable(phone):
    phone.locator("#sb-zoom").click()  # Fit width -> Actual size
    _settle(phone)
    g = _geometry(phone)
    assert g["mode"] == "actual" and g["zoom"] == 1
    assert g["scrollW"] > g["clientW"]  # wider than the screen: it scrolls
    phone.evaluate("document.getElementById('page-wrap').scrollLeft = 0")
    g = _geometry(phone)
    # The left edge used to be 74 px off screen with no way to scroll to it.
    assert g["left"] >= g["wrapLeft"] - 0.5, g
    phone.evaluate("document.getElementById('page-wrap').scrollLeft = 1e6")
    g = _geometry(phone)
    assert g["left"] + g["width"] <= g["visibleRight"] + 0.5, g  # and the right edge
    phone.locator("#sb-zoom").click()  # back to Fit width
    _settle(phone)
    assert _geometry(phone)["mode"] == "fit-width"


def test_zoom_is_remembered_on_reload(phone):
    phone.evaluate("StampAlbum.setZoomMode('fit-page')")
    g = _geometry(phone)
    assert g["mode"] == "fit-page"
    # Fit whole page: the full height is visible too.
    # The canvas area's height, less its padding
    vis_h = phone.evaluate("document.getElementById('page-wrap').clientHeight - 40")
    assert g["height"] <= vis_h + 0.5, (g, vis_h)
    phone.reload()
    wait_for_app(phone)
    _settle(phone)
    assert phone.evaluate("StampAlbum.zoomMode") == "fit-page"
    assert phone.evaluate("localStorage.getItem('stampalbum-zoom')") == "fit-page"
    phone.evaluate("StampAlbum.setZoomMode('fit-width')")


def test_view_menu_sets_and_shows_the_zoom(phone):
    phone.locator("#menu-view-btn").click()
    phone.locator("#menu-zoom-actual").click()
    assert phone.evaluate("StampAlbum.zoomMode") == "actual"
    assert phone.locator("#menu-view").is_hidden()  # the menu closes
    phone.locator("#menu-view-btn").click()
    assert phone.locator("#menu-zoom-actual").get_attribute("aria-checked") == "true"
    assert phone.locator("#menu-zoom-fit-width").get_attribute("aria-checked") == "false"
    phone.locator("#menu-zoom-fit-width").click()
    assert phone.evaluate("StampAlbum.zoomMode") == "fit-width"


def test_touch_drag_moves_by_screen_distance_over_zoom(phone):
    phone.select_option("#grid", "0")  # Snap Off and no snapping to guides: the move is exact
    phone.evaluate("StampAlbum._snapEnabled = false")
    eid = _add_item(phone)
    before = _item(phone, eid)
    z = phone.evaluate("StampAlbum.zoom")
    x0, y0 = _centre_on_screen(phone, eid)
    _touch_drag(phone, x0, y0, 50, 40)
    after = _item(phone, eid)
    assert abs((after["x"] - before["x"]) - 50 / z) < 0.6, (before, after, z)
    assert abs((after["y"] - before["y"]) - 40 / z) < 0.6, (before, after, z)


def test_touch_drag_snaps_to_the_grid_in_mm(phone):
    phone.select_option("#grid", "5")  # 5 mm = 12.5 canvas px
    phone.evaluate("StampAlbum._snapEnabled = false")
    eid = _add_item(phone)
    before = _item(phone, eid)
    x0, y0 = _centre_on_screen(phone, eid)
    _touch_drag(phone, x0, y0, 33, 0)
    after = _item(phone, eid)
    moved = after["x"] - before["x"]
    # It used to snap to 5 px steps; a 5 mm grid moves in 12.5 px steps.
    assert moved != 0 and abs(moved / 12.5 - round(moved / 12.5)) < 1e-6, moved


def test_mouse_drag_moves_by_screen_distance_over_zoom(phone):
    phone.select_option("#grid", "0")
    phone.evaluate("StampAlbum._snapEnabled = false")
    eid = _add_item(phone)
    before = _item(phone, eid)
    z = phone.evaluate("StampAlbum.zoom")
    x0, y0 = _centre_on_screen(phone, eid)
    # Mouse events, as an iPad with a trackpad or a narrow desktop window sends.
    phone.evaluate(f"""(()=>{{const t=document.elementFromPoint({x0},{y0});
        const o={{bubbles:true,cancelable:true,clientX:{x0},clientY:{y0},button:0}};
        t.dispatchEvent(new MouseEvent('mousedown',o));
        const to={{...o,clientX:{x0}+30,clientY:{y0}+20}};
        document.dispatchEvent(new MouseEvent('mousemove',to));
        document.dispatchEvent(new MouseEvent('mouseup',o))}})()""")
    after = _item(phone, eid)
    assert abs((after["x"] - before["x"]) - 30 / z) < 0.6, (before, after, z)
    assert abs((after["y"] - before["y"]) - 20 / z) < 0.6, (before, after, z)


def test_screen_points_map_to_page_positions(phone):
    g = _geometry(phone)
    p = phone.evaluate(f"StampAlbum.toPagePx({g['left']} + 100, {g['top']} + 50)")
    assert abs(p["x"] - 100 / g["zoom"]) < 1e-6 and abs(p["y"] - 50 / g["zoom"]) < 1e-6


def test_handles_keep_their_size_on_screen(phone):
    _add_item(phone)
    _settle(phone)
    se = ".cel.selected .rh.se"
    w = phone.evaluate("s => document.querySelector(s).getBoundingClientRect().width", se)
    assert abs(w - 10) < 0.2, w
    # A finger gets a 24 px target.
    hit = phone.evaluate(
        "(()=>{const s=getComputedStyle(document.querySelector('.cel.selected .rh.se'),'::after');"
        "return [s.content, s.inset || s.top]})()"
    )
    assert hit[0] == '""', hit


def test_a_finger_on_an_item_drags_instead_of_scrolling(phone):
    eid = _add_item(phone)
    sel = f'.cel[data-id="{eid}"]'
    ta = phone.evaluate("s => getComputedStyle(document.querySelector(s)).touchAction", sel)
    assert ta == "none", ta
    assert phone.evaluate("getComputedStyle(document.getElementById('page')).touchAction") == "auto"


def test_new_paper_size_refits(phone):
    z_portrait = phone.evaluate("StampAlbum.zoom")
    phone.evaluate("StampAlbum.applyPageSize(297, 210)")
    g = _geometry(phone)
    assert g["zoom"] < z_portrait and g["width"] <= g["avail"] + 0.5, (z_portrait, g)
    phone.evaluate("StampAlbum.applyPageSize(210, 297)")


def test_rotating_the_phone_refits(phone):
    phone.set_viewport_size(IPHONE_LANDSCAPE)
    _settle(phone)
    g = _geometry(phone)
    assert g["width"] <= g["avail"] + 0.5 and g["left"] >= g["wrapLeft"] - 0.5, g
    phone.set_viewport_size(IPHONE)
    _settle(phone)
    g = _geometry(phone)
    assert g["width"] <= g["avail"] + 0.5, g


def _desktop(p, size):
    """A fresh computer window (mouse, no touch)."""
    try:
        browser = p.chromium.launch()
    except Exception as exc:
        if os.environ.get("STAMP_ALBUM_REQUIRE_BROWSER"):
            raise
        pytest.skip(f"chromium unavailable: {exc}")
    return browser, browser.new_page(viewport=size)


def _open(pg, base_url, stored=None):
    pg.goto(base_url + "/")
    if stored:
        pg.evaluate(f"localStorage.setItem('stampalbum-zoom', {stored!r})")
        pg.reload()
    wait_for_app(pg)
    pg.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    _settle(pg)


@pytest.mark.parametrize("size", [{"width": 1440, "height": 900}, {"width": 1512, "height": 982},
                                  {"width": 2560, "height": 1440}])
def test_desktop_opens_with_the_whole_page_in_view(base_url, size):
    with pw.sync_playwright() as p:
        browser, pg = _desktop(p, size)
        _open(pg, base_url)
        g = _geometry(pg)
        assert g["mode"] == "fit-page", g
        # All of the page is on screen, inside the canvas area: no scrolling either way.
        assert g["width"] <= g["avail"] + 0.5 and g["left"] >= g["wrapLeft"] - 0.5, g
        assert g["scrollW"] <= g["clientW"], g
        assert pg.evaluate("document.getElementById('page-wrap').scrollHeight"
                           " <= document.getElementById('page-wrap').clientHeight"), g
        # A 14-inch MacBook and larger show it above 100%, never above 200%.
        if size["height"] >= 982:
            assert 1 < g["zoom"] <= 2, g
        assert pg.locator("#sb-zoom").inner_text() == f"{round(g['zoom'] * 100)}%"
        browser.close()


def test_status_bar_switches_a_desktop_between_whole_page_and_actual_size(base_url):
    with pw.sync_playwright() as p:
        browser, pg = _desktop(p, {"width": 1512, "height": 982})
        _open(pg, base_url)
        pg.locator("#sb-zoom").click()
        _settle(pg)
        assert _geometry(pg)["mode"] == "actual" and pg.evaluate("StampAlbum.zoom") == 1
        assert pg.evaluate("document.getElementById('page').style.transform") == ""
        pg.locator("#sb-zoom").click()
        _settle(pg)
        assert _geometry(pg)["mode"] == "fit-page"
        browser.close()


def test_a_stored_choice_beats_the_desktop_default(base_url):
    with pw.sync_playwright() as p:
        browser, pg = _desktop(p, {"width": 1512, "height": 982})
        _open(pg, base_url, stored="fit-width")
        g = _geometry(pg)
        assert g["mode"] == "fit-width" and g["zoom"] > 1.5, g  # the width, enlarged
        browser.close()


def test_a_narrow_computer_window_fits_the_width(base_url):
    with pw.sync_playwright() as p:
        browser, pg = _desktop(p, {"width": 650, "height": 900})
        _open(pg, base_url)
        assert _geometry(pg)["mode"] == "fit-width"
        browser.close()
