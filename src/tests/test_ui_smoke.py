"""Browser smoke test: loads the real web UI and exercises the main buttons.

Skipped when Playwright or a Chromium browser is unavailable. It exists
because no other test loads the UI, which let a wizard whose script was
never included in index.html ship.
"""
import socket
import threading
import time

import pytest

pw = pytest.importorskip("playwright.sync_api")


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


def test_page_size_dropdown_resets_inline_size(page):
    page.evaluate("StampAlbum.parseDSL('ALBUM_PAGES_SIZE(297 210)\\nPAGE_START'); StampAlbum.render()")
    page.select_option("#pg-size", "a5")
    w, h = _size(page)
    assert abs(w - 370) < 1.5 and abs(h - 525) < 1.5


@pytest.mark.parametrize("btn", ["btn-new", "btn-wizard", "btn-preview", "btn-dsl", "btn-grid", "btn-undo", "btn-redo"])
def test_main_buttons_do_not_throw(page, btn):
    page.click("#" + btn, force=True)
    page.wait_for_timeout(150)
    assert page.js_errors == []
