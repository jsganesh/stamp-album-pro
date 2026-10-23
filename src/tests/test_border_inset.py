# ruff: noqa: F811
"""The page border's distance from the paper's edge (ALBUM_BORDER_INSET).

Printers can't print right to the edge (often 10 to 13 mm at the top and bottom), so a border
4.8 mm in was cut off, or the page was printed at "Fit to page", shrinking every stamp box. New
albums put it 13 mm in; an album that doesn't say keeps 4.8 mm; the right panel changes it.
"""

from io import BytesIO

from fastapi.testclient import TestClient
from image_helpers import pixels
from PIL import Image
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401

from stamp_album.api import app
from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.engines import page_border
from stamp_album.templates import TEMPLATES

BORDERED = ('ALBUM_PAGES_BORDER(0.5 0 0 1)\nALBUM_PAGES_BORDER_STYLE("solid")\n'
            'ALBUM_PAGES_SIZE(210 297)\n{inset}PAGE_START\n'
            'PAGE_TEXT_AT(20 20 100 10 "HN" 10 "x" "left")\n')


def _album(inset_line=""):
    return AlbumParser().parse(BORDERED.format(inset=inset_line), "t.slbum")


# ── The file ──


def test_an_album_that_does_not_say_keeps_4_8_mm():
    album = _album()
    assert album.border_inset == 4.8
    assert page_border.page_primitives(album)[0].points[0][0] == __import__("pytest").approx(4.8)


def test_the_file_sets_it_and_keeps_it():
    album = _album("ALBUM_BORDER_INSET(13)\n")
    assert album.border_inset == 13
    assert page_border.page_primitives(album)[0].points[0] == (13, 13)
    assert "ALBUM_BORDER_INSET(13)" in AlbumSerializer().to_dsl(album)
    assert _album("ALBUM_BORDER_INSET(99)\n").border_inset == 4.8  # out of range: ignored


def test_every_template_puts_the_border_13_mm_in():
    for t in TEMPLATES:
        assert AlbumParser().parse(t["content"], "t.slbum").border_inset == 13, t["id"]


def _png_dark_edges(inset):
    state = {"elements": [], "pages": [], "page_width_px": 525, "page_height_px": 742.5,
             "scale": 2.5, "format": "png", "border_style": "solid", "border_color": "#000000",
             "theme_color": "#000000"}
    if inset is not None:
        state["border_inset"] = inset
    r = TestClient(app).post("/export-from-state", json=state)
    assert r.status_code == 200
    img = Image.open(BytesIO(r.content)).convert("L")
    w, h = img.size
    px = pixels(img)
    col = [px[y * w + w // 2] for y in range(h)]
    dark = [y for y, v in enumerate(col) if v < 128]
    mm = 297 / h
    return dark[0] * mm, (h - 1 - dark[-1]) * mm


def test_the_export_draws_the_border_where_the_album_says():
    top, bottom = _png_dark_edges(13)
    assert 12.5 < top < 13.5 and 12.5 < bottom < 13.5, (top, bottom)
    top, bottom = _png_dark_edges(None)  # an export request from before: 4.8 mm
    assert 4.3 < top < 5.3 and 4.3 < bottom < 5.3, (top, bottom)


# ── The editor ──


def _rect_x_mm(page):
    return page.evaluate("""(() => { const r = document.querySelector('#page-border rect');
        return r ? Number(r.getAttribute('x')) / StampAlbum._sc : null; })()""")


def test_a_new_album_puts_the_border_13_mm_in(page):
    page.evaluate("StampAlbum.newAlbum(); StampAlbum.select(null)")
    page.select_option("#def-bdr", "solid")
    assert page.is_visible("#def-bdr-inset")
    assert page.input_value("#def-bdr-inset") == "13"
    assert abs(_rect_x_mm(page) - 13) < 1e-6
    assert "ALBUM_BORDER_INSET(13)" in page.evaluate("StampAlbum.buildDSL()")
    assert page.evaluate("StampAlbum.buildCanvasState('pdf').border_inset") == 13


def test_the_panel_moves_the_border_in_one_undo_step(page):
    page.evaluate("StampAlbum.newAlbum(); StampAlbum.select(null)")
    page.select_option("#def-bdr", "solid")
    page.select_option("#def-bdr-inset", "10")
    assert abs(_rect_x_mm(page) - 10) < 1e-6
    page.evaluate("StampAlbum.undo()")
    assert page.input_value("#def-bdr-inset") == "13"
    assert abs(_rect_x_mm(page) - 13) < 1e-6
    assert page.js_errors == []


def test_an_older_album_keeps_4_8_mm(page):
    page.evaluate("StampAlbum.newAlbum()")
    page.evaluate("d => StampAlbum.parseDSL(d)", BORDERED.format(inset=""))
    page.evaluate("StampAlbum.select(null)")
    assert page.input_value("#def-bdr-inset") == "4.8"
    assert abs(_rect_x_mm(page) - 4.8) < 1e-6


def test_the_setting_shows_only_with_a_border(page):
    page.evaluate("StampAlbum.newAlbum(); StampAlbum.select(null)")
    page.select_option("#def-bdr", "none")
    assert page.is_hidden("#def-bdr-inset") and page.is_hidden("#bdr-inset-note")
    page.select_option("#def-bdr", "double")
    assert page.is_visible("#def-bdr-inset") and page.is_visible("#bdr-inset-note")


def test_a_draft_keeps_it(page):
    page.evaluate("StampAlbum.newAlbum()")
    page.evaluate("StampAlbum.CORE.setBorderInset(10); StampAlbum.saveDraft();"
                  " StampAlbum.CORE.setBorderInset(4.8); StampAlbum.loadDraft()")
    assert page.evaluate("StampAlbum.CORE.getBorderInset()") == 10


def test_captions_are_warned_inside_the_border(page):
    """A caption that would cross the moved-in border gets its "!" badge."""
    page.evaluate("StampAlbum.newAlbum()")
    page.evaluate("StampAlbum._pageBorder = 'solid'; StampAlbum.syncPageBar()")
    page.evaluate("""StampAlbum.add({ t: 'stamp', s: 'rectangle', x: StampAlbum.px(100),
        y: StampAlbum.px(266), w: StampAlbum.px(19), h: StampAlbum.px(15), lbl: 'Name' })""")
    page.evaluate("StampAlbum.CORE.setBorderInset(4.8); StampAlbum.render()")
    assert page.locator(".caption-warn").count() == 0
    page.evaluate("StampAlbum.CORE.setBorderInset(13); StampAlbum.render()")
    assert page.locator(".caption-warn").count() == 1
