# ruff: noqa: F811
"""The editor's page sits on whole device pixels.

#page-wrap centres the page, and pages are a fractional number of pixels wide
(A4 is 525 px, Letter 539.75 px at 2.5 px/mm), so the page's left edge used to
land between pixels (457.5, 450.125 ...) and every line on it looked soft.
"""

import os

import playwright.sync_api as pw
import pytest
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)

SIZES = {"A4": (210, 297), "Letter": (215.9, 279.4), "A4 landscape": (297, 210)}
WIDTHS = [1500, 1501, 1280, 1024, 1023]


def _origin(pg):
    return pg.evaluate(
        "(()=>{const b=document.getElementById('page').getBoundingClientRect();"
        "return [b.left, b.top, b.width, b.height]})()"
    )


def _on_device_pixel(v, dpr):
    return abs(v * dpr - round(v * dpr)) < 1e-3


def _settle(pg):
    # The snap runs from a ResizeObserver, which fires before the next paint.
    pg.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")


@pytest.mark.parametrize("name", list(SIZES))
def test_page_on_whole_pixels(page, name):
    w_mm, h_mm = SIZES[name]
    page.evaluate(f"StampAlbum.applyPageSize({w_mm}, {h_mm})")
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900})
        _settle(page)
        left, top, w, h = _origin(page)
        assert _on_device_pixel(left, 1) and _on_device_pixel(top, 1), (name, width, left, top)
        # The page itself keeps its size: 2.5 px per mm.
        assert abs(w - w_mm * 2.5) < 1e-6 and abs(h - h_mm * 2.5) < 1e-6


def test_page_snaps_when_a_panel_changes_the_space(page):
    page.set_viewport_size({"width": 1500, "height": 900})
    page.evaluate("StampAlbum.applyPageSize(210, 297)")
    _settle(page)
    # Narrow the canvas area without resizing the window, as a side panel would.
    page.evaluate("document.getElementById('page-wrap').style.marginRight = '2px'")
    _settle(page)
    left, top, _, _ = _origin(page)
    assert _on_device_pixel(left, 1), left
    page.evaluate("document.getElementById('page-wrap').style.marginRight = ''")


def test_page_on_whole_device_pixels_on_retina(base_url):
    with pw.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:
            if os.environ.get("STAMP_ALBUM_REQUIRE_BROWSER"):
                raise
            pytest.skip(f"chromium unavailable: {exc}")
        pg = browser.new_page(viewport={"width": 1500, "height": 950}, device_scale_factor=2)
        pg.goto(base_url + "/")
        wait_for_app(pg)
        pg.evaluate("StampAlbum.applyPageSize(215.9, 279.4)")  # Letter: left was x.125
        for width in WIDTHS:
            pg.set_viewport_size({"width": width, "height": 900})
            _settle(pg)
            left, top, _, _ = _origin(pg)
            assert _on_device_pixel(left, 2) and _on_device_pixel(top, 2), (width, left, top)
        browser.close()
