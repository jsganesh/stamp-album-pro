"""Browser smoke test: loads the real web UI and exercises the main buttons.

Skipped when Playwright or a Chromium browser is unavailable (locally);
set STAMP_ALBUM_REQUIRE_BROWSER=1 (CI does) to fail instead of skip, in both cases. It exists
because no other test loads the UI, which let a wizard whose script was
never included in index.html ship.
"""
import os
import socket
import threading
import time

import pytest

try:
    import playwright.sync_api as pw
except ImportError as exc:  # Playwright not installed
    if os.environ.get("STAMP_ALBUM_REQUIRE_BROWSER"):
        # CI (and anyone who sets the flag) must run these tests, never silently skip them
        raise ImportError(f"STAMP_ALBUM_REQUIRE_BROWSER is set but Playwright is not installed: {exc}") from exc
    pytest.skip(f"playwright not installed: {exc}", allow_module_level=True)


@pytest.fixture(scope="module")
def base_url():
    import uvicorn

    from stamp_album.api import app

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    t.join(timeout=5)


@pytest.fixture()
def page(base_url):
    with pw.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:  # no browser installed
            if os.environ.get("STAMP_ALBUM_REQUIRE_BROWSER"):
                raise  # CI must run these tests, never silently skip them
            pytest.skip(f"chromium unavailable: {exc}")
        pg = browser.new_page(viewport={"width": 1500, "height": 950})
        pg.js_errors = []
        pg.on("pageerror", lambda e: pg.js_errors.append(str(e)))
        pg.goto(base_url + "/")
        pg.wait_for_function("window.StampAlbum && document.getElementById('page')")
        pg.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
        yield pg
        browser.close()


def _size(pg):
    return pg.evaluate("(()=>{const e=document.getElementById('page');return [e.offsetWidth,e.offsetHeight]})()")


def test_no_js_errors_on_load(page):
    assert page.js_errors == []


def test_wizard_applies_function_exists(page):
    assert page.evaluate("typeof StampAlbum.applyWizard") == "function"


def _open_wizard(page):
    page.click("#menu-file-btn")
    page.click("#btn-wizard")


def test_wizard_creates_landscape_album(page):
    _open_wizard(page)
    page.select_option("#wiz-orient", "landscape")
    page.fill("#wiz-title", "Landscape test")
    page.click("#btn-wiz-apply")
    w, h = _size(page)
    assert w > h, f"page should be landscape, got {w}x{h}"
    assert abs(w - 742.5) < 1.5 and abs(h - 525) < 1.5
    assert "ALBUM_PAGES_SIZE(297 210)" in page.evaluate("StampAlbum.buildDSL()")
    assert page.js_errors == []


def test_wizard_portrait_a4(page):
    _open_wizard(page)
    page.click("#btn-wiz-apply")
    w, h = _size(page)
    assert h > w


def test_landscape_dsl_sizes_page(page):
    page.evaluate("StampAlbum.parseDSL('ALBUM_PAGES_SIZE(297 210)\\nPAGE_START'); StampAlbum.render()")
    w, h = _size(page)
    assert w > h


def test_page_setup_resets_inline_size(page):
    page.evaluate("StampAlbum.parseDSL('ALBUM_PAGES_SIZE(297 210)\\nPAGE_START'); StampAlbum.render()")
    _page_setup(page, size="a5", orient="portrait")
    w, h = _size(page)
    assert abs(w - 370) < 1.5 and abs(h - 525) < 1.5


# (menu to open first, or None; button id). Grid fill needs a selected stamp.
MAIN_BUTTONS = [("file", "btn-new"), ("file", "btn-wizard"), (None, "btn-page-setup"), (None, "btn-preview"),
                ("view", "btn-dsl"), (None, "btn-grid"), (None, "btn-undo"), (None, "btn-redo")]


@pytest.mark.parametrize("menu,btn", MAIN_BUTTONS)
def test_main_buttons_do_not_throw(page, menu, btn):
    page.on("dialog", lambda d: d.dismiss())  # Grid fill prompts for rows and columns
    if btn == "btn-grid":
        page.evaluate("StampAlbum.select(StampAlbum.E[0].id)")
    if btn in ("btn-undo", "btn-redo"):  # enabled only when there is something to undo or redo
        page.evaluate("StampAlbum.E.push({id: 'u1', t: 'stamp', s: 'rectangle', x: 50, y: 50, w: 100, h: 75}); StampAlbum.pushUndo()")
        if btn == "btn-redo":
            page.evaluate("StampAlbum.undo()")
    if menu:
        page.click(f"#menu-{menu}-btn")
    page.click("#" + btn)
    page.wait_for_timeout(150)
    assert page.js_errors == []


def test_legacy_oversized_a4_is_migrated(page):
    page.evaluate("StampAlbum.parseDSL('ALBUM_PAGES_SIZE(238 336.8)\\nPAGE_START\\nSTAMP_ADD_AT(20 20 40 30 \"x\" \"\" \"\" \"\")'); StampAlbum.render()")
    w, h = _size(page)
    assert abs(w - 525) < 1.5 and abs(h - 742.5) < 1.5
    assert "ALBUM_PAGES_SIZE(210 297)" in page.evaluate("StampAlbum.buildDSL()")
    assert page.inner_text("#btn-page-setup").strip() == "A4 · Portrait"
    assert page.js_errors == []


def test_legacy_oversized_landscape_a4_is_migrated(page):
    page.evaluate("StampAlbum.parseDSL('ALBUM_PAGES_SIZE(336.8 238)\\nPAGE_START'); StampAlbum.render()")
    w, h = _size(page)
    assert abs(w - 742.5) < 1.5 and abs(h - 525) < 1.5


# ── Preview (server-rendered HTML) ──

def _preview_html(base_url, elements):
    import json
    import urllib.request

    state = {"elements": elements, "pages": [], "page_width_px": 525, "page_height_px": 742.5,
             "scale": 2.5, "format": "html", "source_path": "t.slbum"}
    req = urllib.request.Request(base_url + "/render-from-state", data=json.dumps(state).encode(),
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req).read().decode()


def _stamp(shape, x, y, w, h, lbl):
    return {"t": "stamp", "s": shape, "x": x, "y": y, "w": w, "h": h, "lbl": lbl,
            "bdr": "solid", "bdrC": "#000000", "bdrW": 1, "fill": "#ffffff", "fillA": 100}


@pytest.mark.parametrize("shape", ["rectangle", "oval", "octagon", "diamond"])
def test_preview_description_sits_below_the_shape(base_url, page, shape):
    html = _preview_html(base_url, [_stamp(shape, 100, 100, 150, 110, "LABELTEXT")])
    page.set_content(html)
    info = page.evaluate("""() => {
        const lab = document.querySelector('.caption-description');
        const box = document.querySelector('.stamp').getBoundingClientRect();
        const r = lab.getBoundingClientRect();
        const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
        return {visible: !!el && (el === lab || lab.contains(el)), below: r.top - box.bottom};
    }""")
    assert info["visible"], "something paints over the stamp's description"
    assert info["below"] > 0, "the description belongs below the box, not inside it"


def test_preview_oval_fills_non_square_box(base_url, page):
    html = _preview_html(base_url, [_stamp("oval", 100, 100, 200, 100, "x")])
    page.set_content(html)
    w, h = page.evaluate("""() => {
        const e = document.querySelector('.stamp-frame ellipse.stamp-fill').getBoundingClientRect();
        return [e.width, e.height];
    }""")
    assert w > h * 1.5, f"oval rendered {w:.0f}x{h:.0f}, should follow the 2:1 box"


# ── Canvas text matches the printed page ──

def test_canvas_font_size_is_points_at_page_scale(page):
    page.evaluate("StampAlbum.parseDSL('ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\nPAGE_TEXT_AT(10 10 100 30 \"HB\" 40 \"Bahrain\" \"left\")'); StampAlbum.render()")
    px = page.evaluate("parseFloat(getComputedStyle(document.querySelector('#page .cel .elbl')).fontSize)")
    # 40 pt = 14.11 mm; the canvas draws 2.5 px per mm
    assert px == pytest.approx(40 * 25.4 / 72 * 2.5, abs=0.1)


@pytest.mark.parametrize("align", ["left", "center", "right"])
def test_canvas_text_alignment_and_top_anchor(page, align):
    page.evaluate("a => { StampAlbum.parseDSL('ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\nPAGE_TEXT_AT(10 10 100 60 \"HN\" 12 \"Hi\" \"' + a + '\")'); StampAlbum.render() }", align)
    info = page.evaluate("""() => {
        const cel = document.querySelector('#page .cel');
        const s = cel.querySelector('.elbl');
        const range = document.createRange(); range.selectNodeContents(s);
        const t = range.getBoundingClientRect(), box = cel.getBoundingClientRect();
        return {top: t.top - box.top, left: t.left - box.left, right: box.right - t.right, w: box.width};
    }""")
    assert info["top"] < 10, "text must sit at the top of its box, not vertically centred"
    if align == "left":
        assert info["left"] < 10
    elif align == "right":
        assert info["right"] < 10
    else:
        assert abs(info["left"] - info["right"]) < 3


# ── Elements loaded from a file must be visible on the canvas ──

LOADED = (
    "ALBUM_PAGES_SIZE(210 297)\n"
    "PAGE_START\n"
    'PAGE_TEXT_AT(10 10 100 30 "HB" 20 "Bahrain" "left")\n'
    'STAMP_ADD_IMG(20 60 40 48 "arms.png" "cap" "" "")'
)


def test_loaded_text_and_image_elements_are_not_transparent(page):
    page.evaluate("d => { StampAlbum.parseDSL(d.replace(/\\\\n/g, '\\n')); StampAlbum.render(); }", LOADED)
    ops = page.evaluate("[...document.querySelectorAll('#page .cel')].map(c => parseFloat(getComputedStyle(c).opacity))")
    assert len(ops) == 2
    assert all(o == 1 for o in ops), f"loaded elements rendered with opacity {ops}"


def test_fill_alpha_does_not_fade_the_whole_element(page):
    page.evaluate("""() => { StampAlbum.parseDSL('ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\nPAGE_TEXT_AT(10 10 100 30 "HN" 12 "Hi" "left")');
        StampAlbum.E[0].fill = '#ff0000'; StampAlbum.E[0].fillA = 50; StampAlbum.render(); }""")
    info = page.evaluate("""() => { const c = document.querySelector('#page .cel');
        return [getComputedStyle(c).opacity, getComputedStyle(c).backgroundColor]; }""")
    assert info[0] == "1"
    assert "rgba(255, 0, 0, 0.5)" in info[1]


def test_preview_shows_no_label_over_an_image(base_url, page):
    el = {"t": "image", "s": "rectangle", "x": 100, "y": 100, "w": 150, "h": 150, "lbl": "SHOULDNOTSHOW",
          "img": "arms.png", "bdr": "none", "fill": "transparent"}
    html = _preview_html(base_url, [el])
    assert "SHOULDNOTSHOW" not in html


# ── Page setup on the open album ──

TWO_STAMPS = ("ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\n"
              "STAMP_ADD_AT(20 20 40 30 \\\"a\\\" \\\"\\\" \\\"\\\" \\\"\\\")\\n"
              "STAMP_ADD_AT(20 250 40 30 \\\"b\\\" \\\"\\\" \\\"\\\" \\\"\\\")")


def _load(page, dsl):
    page.evaluate("StampAlbum.parseDSL(\"" + dsl + "\"); StampAlbum.render()")


def _stamps(page):
    import re

    dsl = page.evaluate("StampAlbum.buildDSL()")
    return [tuple(float(v) for v in m.groups()) for m in re.finditer(r"STAMP_ADD_AT\(([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)", dsl)]


def _page_setup(page, size=None, orient=None, apply=True):
    page.click("#btn-page-setup")
    if size:
        page.select_option("#ps-size", size)
    if orient:
        page.check("#ps-orient-" + orient)
    if apply:
        page.click("#ps-apply")


def test_page_setup_switches_open_album_to_landscape(page):
    _load(page, TWO_STAMPS)
    _page_setup(page, orient="landscape")
    w, h = _size(page)
    assert w > h, f"page should be landscape, got {w}x{h}"
    assert "ALBUM_PAGES_SIZE(297 210)" in page.evaluate("StampAlbum.buildDSL()")
    assert len(_stamps(page)) == 2, "the open album's elements must be kept"
    assert page.inner_text("#btn-page-setup").strip() == "A4 · Landscape"
    assert not page.is_visible("#page-setup-overlay")
    assert page.js_errors == []


def test_page_setup_warns_then_moves_elements_inside(page):
    _load(page, TWO_STAMPS)
    _page_setup(page, orient="landscape", apply=False)
    assert "1 element" in page.inner_text("#ps-note")
    page.click("#ps-apply")
    (ax, ay, _, _), (bx, by, bw, bh) = _stamps(page)
    assert (ax, ay) == (20, 20), "elements that already fit stay put"
    assert bx == 20, "only the overflowing axis changes"
    assert by + bh <= 210 - 15 + 0.1, f"stamp b should be inside the page margin, bottom at {by + bh}"
    assert (bw, bh) == (40, 30), "sizes are never changed"


def test_page_setup_note_is_quiet_when_everything_fits(page):
    _load(page, TWO_STAMPS)
    _page_setup(page, size="a3", apply=False)
    assert "element" not in page.inner_text("#ps-note")


def test_page_setup_cancel_changes_nothing(page):
    _load(page, TWO_STAMPS)
    _page_setup(page, orient="landscape", apply=False)
    page.click("#ps-cancel")
    w, h = _size(page)
    assert h > w
    assert _stamps(page)[1][1] == 250


def test_page_setup_is_one_undo_step(page):
    _load(page, TWO_STAMPS)
    page.evaluate("StampAlbum.resetUndo()")
    _page_setup(page, orient="landscape")
    page.click("#btn-undo")
    w, h = _size(page)
    assert h > w, "undo should restore the portrait page"
    assert _stamps(page)[1][1] == 250, "undo should restore element positions"
    assert page.inner_text("#btn-page-setup").strip() == "A4 · Portrait"
    page.click("#btn-redo")
    w, h = _size(page)
    assert w > h, "redo should re-apply the landscape page"
    assert _stamps(page)[1][1] < 250


def test_undo_steps_back_one_state_at_a_time(page):
    page.evaluate("StampAlbum.newAlbum()")
    for i in range(3):
        page.evaluate(f"StampAlbum.E.push({{id: 'u{i}', t: 'stamp', s: 'rectangle', x: 50, y: {50 + i * 100}, w: 100, h: 75}}); StampAlbum.pushUndo()")
    page.click("#btn-undo")
    page.click("#btn-undo")
    assert page.evaluate("StampAlbum.E.length") == 1
    page.click("#btn-redo")
    assert page.evaluate("StampAlbum.E.length") == 2


def test_first_edit_after_load_can_be_undone(page):
    before = page.evaluate("StampAlbum.E.length")
    page.evaluate("StampAlbum.E.push({id: 'z1', t: 'stamp', s: 'rectangle', x: 50, y: 50, w: 100, h: 75}); StampAlbum.pushUndo()")
    page.click("#btn-undo")
    assert page.evaluate("StampAlbum.E.length") == before


def test_landscape_survives_a_reload_from_draft(page):
    _load(page, TWO_STAMPS)
    _page_setup(page, orient="landscape")
    page.evaluate("StampAlbum.saveDraft()")
    page.reload()
    page.wait_for_function("window.StampAlbum && document.getElementById('page')")
    w, h = _size(page)
    assert w > h, f"draft should restore the landscape page, got {w}x{h}"
    assert page.inner_text("#btn-page-setup").strip() == "A4 · Landscape"


def test_wizard_asks_before_replacing_unsaved_album(page):
    _load(page, TWO_STAMPS)
    page.evaluate("StampAlbum.pushUndo()")  # make the album dirty
    messages = []
    page.once("dialog", lambda d: (messages.append(d.message), d.dismiss()))
    _open_wizard(page)
    page.click("#btn-wiz-apply")
    assert messages and "Discard" in messages[0]
    assert len(_stamps(page)) == 2, "declining must keep the open album"
    page.once("dialog", lambda d: d.accept())
    page.click("#btn-wiz-apply")
    assert len(_stamps(page)) == 0, "accepting creates the new album"


# ── Toolbar: File, Edit and View menus; selection tools; fits narrow windows ──

@pytest.mark.parametrize("width", [1440, 1024, 768, 390])
def test_toolbar_fits_without_sideways_scroll(page, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.wait_for_timeout(100)
    r = page.evaluate("""(() => {
        const out = (el) => [...el.querySelectorAll('button, select, input, span, label')]
            .filter(e => { const b = e.getBoundingClientRect(); return b.width > 0 && b.right > innerWidth + 1; })
            .map(e => e.id || e.className || e.tagName);
        const logo = document.querySelector('#tb .logo').getBoundingClientRect();
        return { doc: document.documentElement.scrollWidth - innerWidth,
                 tb: out(document.getElementById('tb')), ca: out(document.getElementById('ca-toolbar')),
                 logoLines: Math.round(logo.height / 20) };
    })()""")
    assert r["doc"] <= 0, f"page scrolls sideways by {r['doc']} px"
    assert r["tb"] == [] and r["ca"] == [], r
    assert r["logoLines"] <= 1, "the logo must not wrap"


def test_every_toolbar_button_has_a_name(page):
    for width in (1440, 1024, 390):
        page.set_viewport_size({"width": width, "height": 900})
        unnamed = page.evaluate("""[...document.querySelectorAll('#tb button')]
            .filter(b => b.offsetParent && !(b.innerText.trim() || b.getAttribute('aria-label')))
            .map(b => b.id)""")
        assert unnamed == [], f"at {width} px"


def test_menus_open_close_and_only_one_at_a_time(page):
    assert not page.is_visible("#menu-file")
    page.click("#menu-file-btn")
    assert page.is_visible("#menu-file")
    assert page.get_attribute("#menu-file-btn", "aria-expanded") == "true"
    page.keyboard.press("Escape")
    assert not page.is_visible("#menu-file")
    assert page.get_attribute("#menu-file-btn", "aria-expanded") == "false"
    page.click("#menu-file-btn")
    page.click("#menu-edit-btn")
    assert page.is_visible("#menu-edit") and not page.is_visible("#menu-file")
    page.mouse.click(700, 600)
    assert not page.is_visible("#menu-edit")


def test_menu_items_reach_their_actions(page):
    _open_wizard(page)
    assert "open" in page.get_attribute("#wizard-panel", "class")
    assert not page.is_visible("#menu-file"), "choosing an item closes the menu"
    page.click("#menu-file-btn")
    page.click("#menu-page-setup")
    assert page.is_visible("#page-setup-overlay")
    page.click("#ps-cancel")
    assert page.locator("#menu-file [data-fmt]").count() == 4, "File menu lists PDF, PNG, SVG and HTML export"
    page.click("#menu-view-btn")
    page.click("#btn-help")
    assert "open" in page.get_attribute("#help-overlay", "class")
    assert page.js_errors == []


def test_edit_menu_disables_selection_items_without_a_selection(page):
    page.evaluate("StampAlbum.select(null)")
    page.click("#menu-edit-btn")
    assert page.is_disabled("#menu-dup") and page.is_disabled("#menu-del")
    page.keyboard.press("Escape")
    page.evaluate("StampAlbum.select(StampAlbum.E[0].id)")
    page.click("#menu-edit-btn")
    assert not page.is_disabled("#menu-dup") and not page.is_disabled("#menu-del")


def test_selection_tools_show_only_with_a_selection(page):
    page.evaluate("StampAlbum.select(null)")
    assert not page.is_visible("#sel-tools")
    assert page.is_visible("#def-bdr"), "page defaults show when nothing is selected"
    page.evaluate("StampAlbum.select(StampAlbum.E[0].id)")
    assert page.is_visible("#sel-tools") and page.is_visible("#btn-align-l") and page.is_visible("#btn-del")
    assert not page.is_visible("#def-bdr")
    page.evaluate("StampAlbum.select(null)")
    assert not page.is_visible("#sel-tools")


def test_columns_distribute_and_match_controls_are_gone(page):
    for gone in ("col-mode", "col-gap", "btn-dist-h", "btn-dist-v", "btn-match-w", "btn-match-h", "align-group"):
        assert page.locator("#" + gone).count() == 0, gone


def test_album_with_columns_still_saves_its_columns(page):
    _load(page, "ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\nPAGE_COLUMN_START(2 10.0)\\n"
                "STAMP_ADD_AT(20 20 40 30 \\\"a\\\" \\\"\\\" \\\"\\\" \\\"\\\")\\nPAGE_COLUMN_STOP")
    assert "PAGE_COLUMN_START(2 10.0)" in page.evaluate("StampAlbum.buildDSL()")
    assert page.js_errors == []


def test_border_control_sets_the_page_border_only(page):
    before = page.evaluate("StampAlbum._defBdr")
    page.evaluate("StampAlbum.select(null)")
    page.select_option("#def-bdr", "double")
    assert page.evaluate("StampAlbum._pageBorder") == "double"
    assert page.evaluate("StampAlbum._defBdr") == before, "new stamps keep their own default border"


def test_snap_to_guides_state_matches_the_view_menu(page):
    page.click("#menu-view-btn")
    shown = page.get_attribute("#btn-snap", "aria-checked") == "true"
    assert page.evaluate("!!StampAlbum._snapEnabled") == shown
    page.click("#btn-snap")
    page.click("#menu-view-btn")
    assert (page.get_attribute("#btn-snap", "aria-checked") == "true") == page.evaluate("!!StampAlbum._snapEnabled") != shown


def _one_stamp(page, x=100, y=100, extra=""):
    page.evaluate("StampAlbum.newAlbum(); StampAlbum.E.push({id: 'd1', t: 'stamp', s: 'rectangle', x: %s, y: %s, w: 100, h: 75, lbl: 'd'});"
                  "%s StampAlbum.render()" % (x, y, extra))


def _drag(page, el_id, dx, dy):
    box = page.locator(f".cel[data-id='{el_id}']").bounding_box()
    sx, sy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(sx, sy)
    page.mouse.down()
    page.mouse.move(sx + dx / 2, sy + dy / 2, steps=3)
    page.mouse.move(sx + dx, sy + dy, steps=3)
    page.mouse.up()
    return page.evaluate(f"(() => {{ const e = StampAlbum.E.find(e => e.id === '{el_id}'); return [e.x, e.y]; }})()")


def test_drag_with_snap_off_keeps_a_real_position(page):
    _one_stamp(page)
    page.evaluate("StampAlbum._snapEnabled = false")
    page.select_option("#grid", "0")
    x, y = _drag(page, "d1", 37, 23)
    assert x is not None and y is not None, "dragging with Snap Off lost the stamp's position"
    assert abs(x - 137) < 1.5 and abs(y - 123) < 1.5, (x, y)


def test_grid_snap_steps_are_millimetres(page):
    _one_stamp(page)
    page.evaluate("StampAlbum._snapEnabled = false")
    page.select_option("#grid", "5")
    x, y = _drag(page, "d1", 37, 23)
    step = 5 * 2.5  # 5 mm at 2.5 px per mm
    assert abs((x - 100) / step - round((x - 100) / step)) < 1e-6, f"x moved {x - 100} px, not whole 5 mm steps"
    assert abs(x - 137.5) < 0.01 and abs(y - 125) < 0.01, (x, y)


def test_snap_to_guides_pulls_a_stamp_onto_a_guide(page):
    _one_stamp(page, 300, 400, "StampAlbum.E.push({id: 'd2', t: 'stamp', s: 'rectangle', x: 100, y: 100, w: 100, h: 75, lbl: 'e'});")
    page.evaluate("StampAlbum._snapEnabled = true")
    page.select_option("#grid", "0")
    x, _ = _drag(page, "d1", -197, 0)  # left edge lands 3 px from d2's left edge
    assert x == 100, f"stamp should snap onto the guide at 100, got {x}"


def test_view_menu_can_show_the_tutorial_again(page):
    before = page.evaluate("StampAlbum.E.length")
    page.click("#menu-view-btn")
    page.click("#menu-tutorial")
    assert "open" in page.get_attribute("#tutorial-overlay", "class")
    assert page.evaluate("StampAlbum.E.length") == before, "showing the tutorial must not load the sample album"


# ── Palette: click, keyboard and tap add the item at the page centre ──

MM = 2.5  # px per mm on the canvas
OFFSET = 10 * MM  # each repeated add moves 10 mm right and down


def _empty_album(page, grid="0"):
    page.evaluate("StampAlbum.newAlbum(); StampAlbum._snapEnabled = false; StampAlbum.render()")
    page.select_option("#grid", grid)


def _els(page):
    return page.evaluate("StampAlbum.E.map(e => ({id: e.id, t: e.t, s: e.s,"
                         " x: e.x, y: e.y, w: e.w, h: e.h}))")


def _centre(e):
    return e["x"] + e["w"] / 2, e["y"] + e["h"] / 2


def _page_px(page):
    return page.evaluate("[StampAlbum._pw, StampAlbum._ph]")


def test_clicking_a_palette_item_adds_it_at_the_page_centre(page):
    _empty_album(page)
    page.click(".p-item[data-s='oval']")
    els = _els(page)
    assert len(els) == 1 and els[0]["s"] == "oval", els
    pw_, ph_ = _page_px(page)
    cx, cy = _centre(els[0])
    assert abs(cx - pw_ / 2) < 1 and abs(cy - ph_ / 2) < 1, (cx, cy, pw_, ph_)
    assert page.evaluate("StampAlbum.sel") == els[0]["id"], "the new item should be selected"


def test_repeated_palette_clicks_step_10mm_right_and_down(page):
    _empty_album(page)
    for _ in range(3):
        page.click(".p-item[data-s='rectangle']")
    els = _els(page)
    assert len(els) == 3
    for a, b in zip(els, els[1:]):
        assert abs(b["x"] - a["x"] - OFFSET) < 0.01 and abs(b["y"] - a["y"] - OFFSET) < 0.01, els


def test_a_different_item_is_also_offset_from_one_already_at_the_centre(page):
    _empty_album(page)
    page.click(".p-item[data-st='label']")
    page.click(".p-item[data-st='heading']")
    a, b = _els(page)
    (ax, ay), (bx, by) = _centre(a), _centre(b)
    assert abs(bx - ax - OFFSET) < 0.01 and abs(by - ay - OFFSET) < 0.01, (a, b)


def test_palette_add_follows_the_grid(page):
    _empty_album(page, grid="5")
    page.click(".p-item[data-s='hexagon']")
    page.click(".p-item[data-s='hexagon']")
    els = _els(page)
    assert len(els) == 2, els
    for e in els:
        for v in (e["x"], e["y"]):
            assert abs(v / (5 * MM) - round(v / (5 * MM))) < 1e-6, f"{v} px is not on the 5 mm grid"


def test_clicked_items_stay_inside_a_small_landscape_page(page):
    _empty_album(page)
    _page_setup(page, size="a5", orient="landscape")
    assert _page_px(page)[0] > _page_px(page)[1], "page setup should have made the page landscape"
    for _ in range(25):
        page.click(".p-item[data-s='rectangle']")
    pw_, ph_ = _page_px(page)
    els = _els(page)
    assert len(els) == 25
    for e in els:
        assert e["x"] >= 0 and e["y"] >= 0, e
        assert e["x"] + e["w"] <= pw_ + 0.01 and e["y"] + e["h"] <= ph_ + 0.01, (e, pw_, ph_)


def test_palette_add_is_one_undo_step(page):
    _empty_album(page)
    page.click(".p-item[data-s='diamond']")
    page.click(".p-item[data-s='diamond']")
    page.evaluate("StampAlbum.undo()")
    assert len(_els(page)) == 1
    page.evaluate("StampAlbum.undo()")
    assert len(_els(page)) == 0


def test_palette_items_are_named_buttons_reachable_by_keyboard(page):
    items = page.locator(".p-item")
    for i in range(items.count()):
        it = items.nth(i)
        assert it.get_attribute("role") == "button"
        assert it.get_attribute("tabindex") == "0"
        assert (it.get_attribute("aria-label") or "").startswith("Add "), it.inner_html()


def test_enter_and_space_on_a_palette_item_add_it(page):
    _empty_album(page)
    page.focus(".p-item[data-s='triangle']")
    page.keyboard.press("Enter")
    page.keyboard.press("Space")
    els = _els(page)
    assert [e["s"] for e in els] == ["triangle", "triangle"], els


def _touch(page, selector, end_x=None, end_y=None):
    """Touch an element, then lift at (end_x, end_y), or where it started."""
    page.evaluate("""([sel, ex, ey]) => {
        const it = document.querySelector(sel), r = it.getBoundingClientRect();
        const sx = r.left + r.width / 2, sy = r.top + r.height / 2;
        const t0 = new Touch({identifier: 1, target: it, clientX: sx, clientY: sy});
        const opts = (t, now) => ({touches: now, changedTouches: [t],
                                   bubbles: true, cancelable: true});
        it.dispatchEvent(new TouchEvent('touchstart', opts(t0, [t0])));
        const t1 = new Touch({identifier: 1, target: it, clientX: ex ?? sx, clientY: ey ?? sy});
        it.dispatchEvent(new TouchEvent('touchend', opts(t1, [])));
    }""", [selector, end_x, end_y])


def test_tapping_a_palette_item_adds_it_at_the_centre(page):
    _empty_album(page)
    _touch(page, ".p-item[data-s='pentagon']")
    els = _els(page)
    assert len(els) == 1 and els[0]["s"] == "pentagon", els
    pw_, ph_ = _page_px(page)
    cx, cy = _centre(els[0])
    assert abs(cx - pw_ / 2) < 1 and abs(cy - ph_ / 2) < 1


def test_touch_drop_with_grid_off_keeps_a_real_position(page):
    _empty_album(page, grid="0")
    box = page.locator("#page").bounding_box()
    _touch(page, ".p-item[data-s='rectangle']", box["x"] + 100, box["y"] + 120)
    els = _els(page)
    assert len(els) == 1 and els[0]["x"] == 100 and els[0]["y"] == 120, els


# ── Palette hint ──

def _hint_visible(page):
    return page.locator("#palette-hint").is_visible()


def test_palette_hint_shows_until_the_first_item_is_added(page):
    assert _hint_visible(page)
    text = page.inner_text("#palette-hint").lower()
    assert "click" in text and "drag" in text, text
    page.click(".p-item[data-s='rectangle']")
    assert not _hint_visible(page)


def test_palette_hint_returns_after_idling_on_an_empty_page(page):
    page.evaluate("StampAlbum.paletteHintIdleMs = 300")
    page.click(".p-item[data-s='rectangle']")
    page.evaluate("StampAlbum.E.splice(0); StampAlbum.render()")
    page.wait_for_selector("#palette-hint", state="visible", timeout=3000)


def test_palette_hint_stays_hidden_while_idle_with_items_on_the_page(page):
    page.evaluate("StampAlbum.paletteHintIdleMs = 200")
    page.click(".p-item[data-s='rectangle']")
    page.wait_for_timeout(800)
    assert page.locator("#palette-hint").count() == 1
    assert not _hint_visible(page)


def test_palette_hint_returns_after_a_drag_that_misses_the_page(page):
    page.click(".p-item[data-s='rectangle']")
    page.evaluate("""() => {
        const it = document.querySelector(".p-item[data-s='oval']");
        const dt = new DataTransfer();
        it.dispatchEvent(new DragEvent('dragstart', {dataTransfer: dt, bubbles: true}));
        it.dispatchEvent(new DragEvent('dragend', {dataTransfer: dt, bubbles: true}));
    }""")
    assert _hint_visible(page)


def test_palette_hint_returns_after_repeated_clicks_on_a_blank_page(page):
    _empty_album(page)
    page.click(".p-item[data-s='rectangle']")
    page.evaluate("StampAlbum.E.splice(0); StampAlbum.render()")
    page.evaluate("StampAlbum.paletteHintIdleMs = 600000")
    box = page.locator("#page").bounding_box()
    for i in range(3):
        page.mouse.click(box["x"] + 40 + i * 5, box["y"] + 40)
    assert _hint_visible(page)
