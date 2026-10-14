# ruff: noqa: F811
"""Pinch to zoom the page (pending item 15), and the same free zoom on a desktop.

Two fingers on the canvas zoom the page, keeping the page point between them under
them; a second finger during a stamp drag puts the stamp back. On a desktop, Ctrl/Cmd +
wheel (and a trackpad pinch), Safari's gesture events and Ctrl/Cmd + = / - / 0 do the
same. A free zoom is 25% to 400% and lasts for the session only. Only the canvas area
stops the browser's own pinch zoom.

Touches are synthetic TouchEvents: headless Chromium's emulated touch hands gestures to
scrolling. Each finger's events go to the element it started on, as on iOS, even after a
redraw has removed that element.
"""

from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)
from test_zoom_ui import (  # noqa: F401
    _add_item,
    _centre_on_screen,
    _item,
    _settle,
    _touch_drag,
    phone,
)


def _pinch(pg, a0, b0, a1, b1, steps=6, a_moves=None):
    """Two fingers from a0/b0 to a1/b1 (screen points). Finger A goes down first.

    a_moves: points finger A drags through alone before finger B comes down.
    """
    pg.evaluate(
        """([a0, b0, a1, b1, steps, aMoves]) => {
        const at = p => document.elementFromPoint(...p)
            || document.getElementById('page-wrap');
        const ta = at(a0);
        const pt = (id, tgt, [x, y]) =>
            new Touch({identifier: id, target: tgt, clientX: x, clientY: y});
        const fire = (tgt, type, touches, changed) => tgt.dispatchEvent(new TouchEvent(type, {
            bubbles: true, cancelable: true,
            touches, targetTouches: touches, changedTouches: changed}));
        let a = pt(1, ta, a0);
        fire(ta, 'touchstart', [a], [a]);
        let last = a0;
        for (const m of (aMoves || [])) {
            a = pt(1, ta, m); fire(ta, 'touchmove', [a], [a]); last = m;
        }
        const tb = at(b0);
        let b = pt(2, tb, b0);
        fire(tb, 'touchstart', [a, b], [b]);
        for (let i = 1; i <= steps; i++) {
            const f = i / steps;
            const lerp = (p, q) => [p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f];
            a = pt(1, ta, lerp(last, a1)); b = pt(2, tb, lerp(b0, b1));
            fire(ta, 'touchmove', [a, b], [a]);
            fire(tb, 'touchmove', [a, b], [b]);
        }
        fire(tb, 'touchend', [a], [b]);
        fire(ta, 'touchend', [], [a]);
    }""",
        [a0, b0, a1, b1, steps, a_moves],
    )


EMPTY_A4 = "ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n"


def _empty(pg):
    """Start from an empty A4 page, so fingers land on paper, not on the sample's stamps.

    (Touching a stamp selects it, and the contextual toolbar that appears moves the canvas.)
    """
    pg.evaluate(f"StampAlbum.parseDSL({EMPTY_A4!r})")
    _settle(pg)


def _page_point(pg, x, y):
    return pg.evaluate(f"StampAlbum.toPagePx({x}, {y})")


def _paper_point(pg):
    """A screen point on empty paper near the middle of the visible page."""
    return pg.evaluate(
        """(()=>{const r=document.getElementById('page').getBoundingClientRect(),
        w=document.getElementById('page-wrap').getBoundingClientRect();
        const x=Math.max(r.left,w.left)+40, y=Math.max(r.top,w.top)+60; return [x, y]})()"""
    )


# ── Phone ──

def test_pinch_out_zooms_in_around_the_fingers(phone):
    _empty(phone)
    z0 = phone.evaluate("StampAlbum.zoom")
    x, y = _paper_point(phone)
    mx, my = x + 60, y + 60
    before = _page_point(phone, mx, my)
    # Fingers 40 px apart move to 120 px apart: three times the zoom.
    _pinch(phone, [mx - 20, my], [mx + 20, my], [mx - 60, my], [mx + 60, my])
    z = phone.evaluate("StampAlbum.zoom")
    assert abs(z - min(4, z0 * 3)) < 0.01, (z0, z)
    assert phone.evaluate("StampAlbum.zoomMode") == "custom"
    after = _page_point(phone, mx, my)
    assert abs(after["x"] - before["x"]) < 1 and abs(after["y"] - before["y"]) < 1, (before, after)
    assert phone.inner_text("#sb-zoom") == f"{round(z * 100)}%"


def test_pinch_stops_at_the_limits(phone):
    _empty(phone)
    x, y = _paper_point(phone)
    # 10 px apart to 300 px apart is 30 times: stops at 400%.
    _pinch(phone, [x, y], [x + 10, y], [x, y], [x + 300, y])
    assert phone.evaluate("StampAlbum.zoom") == 4
    # And back from 300 px to 10 px: stops at 25%.
    _pinch(phone, [x, y], [x + 300, y], [x, y], [x + 10, y])
    assert phone.evaluate("StampAlbum.zoom") == 0.25


def test_pinch_moving_both_fingers_pans(phone):
    _empty(phone)
    x, y = _paper_point(phone)
    _pinch(phone, [x, y], [x + 40, y], [x, y], [x + 100, y])  # zoom in, so there is room to pan
    a, b = [x + 60, y + 40], [x + 140, y + 40]
    target = _page_point(phone, x + 100, y + 40)
    # Same spread, both fingers 30 px left and 20 px up: the page point follows the fingers.
    _pinch(phone, a, b, [a[0] - 30, a[1] - 20], [b[0] - 30, b[1] - 20])
    now = _page_point(phone, x + 70, y + 20)
    assert abs(now["x"] - target["x"]) < 1.5 and abs(now["y"] - target["y"]) < 1.5, (target, now)


def test_pinch_starting_on_a_stamp_does_not_move_it(phone):
    _empty(phone)
    eid = _add_item(phone)
    before = _item(phone, eid)
    undo_len = phone.evaluate("StampAlbum._undoStack.length")
    cx, cy = _centre_on_screen(phone, eid)
    z0 = phone.evaluate("StampAlbum.zoom")
    _pinch(phone, [cx, cy], [cx + 30, cy + 30], [cx - 30, cy - 30], [cx + 70, cy + 70])
    assert phone.evaluate("StampAlbum.zoom") > z0 * 1.5
    assert _item(phone, eid) == before
    assert phone.evaluate("StampAlbum._undoStack.length") == undo_len


def test_second_finger_mid_drag_puts_the_stamp_back(phone):
    _empty(phone)
    eid = _add_item(phone)
    before = _item(phone, eid)
    undo_len = phone.evaluate("StampAlbum._undoStack.length")
    cx, cy = _centre_on_screen(phone, eid)
    # Finger A drags the stamp 40 px, then finger B comes down and they pinch.
    _pinch(phone, [cx, cy], [cx + 60, cy + 60], [cx - 20, cy], [cx + 100, cy + 80],
           a_moves=[[cx + 20, cy], [cx + 40, cy]])
    assert _item(phone, eid) == before
    assert phone.evaluate("StampAlbum._undoStack.length") == undo_len
    assert phone.evaluate("StampAlbum.zoomMode") == "custom"


def test_one_finger_drag_after_a_pinch_moves_by_screen_distance(phone):
    _empty(phone)
    x, y = _paper_point(phone)
    _pinch(phone, [x, y], [x + 40, y], [x - 20, y], [x + 60, y])  # about twice the zoom
    eid = _add_item(phone)
    z = phone.evaluate("StampAlbum.zoom")
    before = _item(phone, eid)
    cx, cy = _centre_on_screen(phone, eid)
    _touch_drag(phone, cx, cy, 50 * z, 0)  # 50 canvas px = 20 mm
    after = _item(phone, eid)
    assert abs(after["x"] - before["x"] - 50) <= 12.5, (z, before, after)  # within the grid step
    assert after["y"] == before["y"]


def test_free_zoom_lasts_for_the_session_only(phone):
    phone.evaluate("StampAlbum.setZoomMode('actual')")
    x, y = _paper_point(phone)
    _pinch(phone, [x, y], [x + 60, y], [x + 20, y], [x + 40, y])
    assert phone.evaluate("StampAlbum.zoomMode") == "custom"
    phone.reload()
    wait_for_app(phone)
    assert phone.evaluate("StampAlbum.zoomMode") == "actual"


def test_status_bar_returns_from_a_free_zoom_to_fit_width(phone):
    _empty(phone)
    x, y = _paper_point(phone)
    _pinch(phone, [x, y], [x + 40, y], [x - 20, y], [x + 60, y])
    assert "fit the page to the window" in phone.get_attribute("#sb-zoom", "aria-label")
    phone.evaluate("document.getElementById('sb-zoom').click()")
    _settle(phone)
    assert phone.evaluate("StampAlbum.zoomMode") == "fit-width"


def test_only_the_canvas_blocks_the_browser_pinch(phone):
    styles = phone.evaluate(
        """['page-wrap', 'toolbar', 'statusbar'].map(id => {
            const e = document.getElementById(id) || document.querySelector('.' + id);
            return e ? getComputedStyle(e).touchAction : null; })"""
    )
    assert styles[0] == "pan-x pan-y"
    assert all(s in (None, "auto") for s in styles[1:]), styles
    # A pinch outside the canvas is left to the browser.
    z0 = phone.evaluate("StampAlbum.zoom")
    r = phone.evaluate("(()=>{const r=document.querySelector('#sb-zoom').getBoundingClientRect();"
                       " return [r.left + 2, r.top + 2]})()")
    _pinch(phone, r, [r[0] + 10, r[1]], [r[0] - 30, r[1]], [r[0] + 40, r[1]])
    assert phone.evaluate("StampAlbum.zoom") == z0


# ── Desktop ──

def _wheel(pg, x, y, dy, ctrl=True, meta=False):
    return pg.evaluate(
        f"""(()=>{{const t=document.elementFromPoint({x},{y});
        const e=new WheelEvent('wheel',{{bubbles:true,cancelable:true,clientX:{x},clientY:{y},
          deltaY:{dy},ctrlKey:{str(ctrl).lower()},metaKey:{str(meta).lower()}}});
        t.dispatchEvent(e); return e.defaultPrevented}})()"""
    )


def test_ctrl_wheel_zooms_at_the_pointer(page):
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    page.evaluate(f"StampAlbum.parseDSL({EMPTY_A4!r})")
    assert page.evaluate("StampAlbum.zoom") == 1
    # The page's horizontal middle: while the page is narrower than the canvas it stays
    # centred, so only that point can stay put sideways.
    x, y = page.evaluate("(()=>{const r=document.getElementById('page').getBoundingClientRect();"
                         " return [r.left + r.width / 2, r.top + 200]})()")
    before = _page_point(page, x, y)
    for _ in range(3):
        assert _wheel(page, x, y, -100)  # the browser doesn't zoom the whole app
    z = page.evaluate("StampAlbum.zoom")
    assert z > 1.5, z
    after = _page_point(page, x, y)
    assert abs(after["x"] - before["x"]) < 1 and abs(after["y"] - before["y"]) < 1, (before, after)
    # Cmd + wheel (Mac) does the same; a plain wheel only scrolls.
    assert _wheel(page, x, y, 100, ctrl=False, meta=True)
    assert page.evaluate("StampAlbum.zoom") < z
    z = page.evaluate("StampAlbum.zoom")
    assert not _wheel(page, x, y, 100, ctrl=False)
    assert page.evaluate("StampAlbum.zoom") == z


def test_zoom_keys_and_menu(page):
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    page.evaluate("document.activeElement && document.activeElement.blur()")
    page.keyboard.press("Control+=")
    assert page.evaluate("StampAlbum.zoom") == 1.1
    page.keyboard.press("Control+=")
    assert page.evaluate("StampAlbum.zoom") == 1.25
    page.keyboard.press("Control+-")
    assert page.evaluate("StampAlbum.zoom") == 1.1
    # In the View menu no fit is ticked; Zoom in and Zoom out step too.
    checked = page.evaluate(
        "[...document.querySelectorAll('[id^=menu-zoom-][role=menuitemradio]')]"
        ".filter(e => e.getAttribute('aria-checked') === 'true').length"
    )
    assert checked == 0
    page.evaluate("document.getElementById('menu-zoom-in').click()")
    assert page.evaluate("StampAlbum.zoom") == 1.25
    page.evaluate("document.getElementById('menu-zoom-out').click()")
    assert page.evaluate("StampAlbum.zoom") == 1.1
    page.keyboard.press("Control+0")  # the default fit: the whole page on a computer
    assert page.evaluate("StampAlbum.zoomMode") == "fit-page"
    assert page.evaluate("StampAlbum.zoom") > 1
    # Typing in a field is left alone.
    eid = _add_item(page)
    page.evaluate(f"StampAlbum.select({eid!r})")
    page.focus("#plbl")
    page.keyboard.press("Control+=")
    assert page.evaluate("StampAlbum.zoomMode") == "fit-page"


def test_safari_gesture_events_zoom_the_page(page):
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    x, y = _paper_point(page)
    prevented = page.evaluate(
        f"""(()=>{{const t=document.elementFromPoint({x},{y}); let p=true;
        const g=(type,scale)=>{{const e=new Event(type,{{bubbles:true,cancelable:true}});
          Object.assign(e,{{scale:scale,clientX:{x},clientY:{y}}}); t.dispatchEvent(e);
          p = p && e.defaultPrevented;}};
        g('gesturestart',1); g('gesturechange',1.5); g('gesturechange',2); g('gestureend',2);
        return p}})()"""
    )
    assert prevented
    assert page.evaluate("StampAlbum.zoom") == 2
    # Outside the canvas, Safari keeps its own gesture.
    outside = page.evaluate(
        """(()=>{const e=new Event('gesturestart',{bubbles:true,cancelable:true});
        document.getElementById('sb-zoom').dispatchEvent(e); return e.defaultPrevented})()"""
    )
    assert not outside
