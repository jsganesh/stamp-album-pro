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


def test_wizard_creates_landscape_album(page):
    page.click("#btn-wizard")
    page.select_option("#wiz-orient", "landscape")
    page.fill("#wiz-title", "Landscape test")
    page.click("#btn-wiz-apply")
    w, h = _size(page)
    assert w > h, f"page should be landscape, got {w}x{h}"
    assert abs(w - 742.5) < 1.5 and abs(h - 525) < 1.5
    assert "ALBUM_PAGES_SIZE(297 210)" in page.evaluate("StampAlbum.buildDSL()")
    assert page.js_errors == []


def test_wizard_portrait_a4(page):
    page.click("#btn-wizard")
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


@pytest.mark.parametrize("btn", ["btn-new", "btn-wizard", "btn-page-setup", "btn-preview", "btn-dsl", "btn-grid", "btn-undo", "btn-redo"])
def test_main_buttons_do_not_throw(page, btn):
    page.click("#" + btn, force=True)
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
def test_preview_label_is_not_hidden_by_shape(base_url, page, shape):
    html = _preview_html(base_url, [_stamp(shape, 100, 100, 150, 110, "LABELTEXT")])
    page.set_content(html)
    hit = page.evaluate("""() => {
        const lab = [...document.querySelectorAll('.stamp div')].find(d => d.textContent.includes('LABELTEXT'));
        const r = lab.getBoundingClientRect();
        const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
        return !!el && (el === lab || lab.contains(el));
    }""")
    assert hit, "the stamp shape paints over its label"


def test_preview_oval_fills_non_square_box(base_url, page):
    html = _preview_html(base_url, [_stamp("oval", 100, 100, 200, 100, "x")])
    page.set_content(html)
    w, h = page.evaluate("""() => {
        const e = document.querySelector('.stamp svg ellipse').getBoundingClientRect();
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
    page.click("#btn-wizard")
    page.click("#btn-wiz-apply")
    assert messages and "Discard" in messages[0]
    assert len(_stamps(page)) == 2, "declining must keep the open album"
    page.once("dialog", lambda d: d.accept())
    page.click("#btn-wiz-apply")
    assert len(_stamps(page)) == 0, "accepting creates the new album"
