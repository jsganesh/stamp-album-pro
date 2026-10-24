# ruff: noqa: F811
"""Expertised stamps, reproductions, and the Frames view.

FIP asks for a bold "(e)" after an item with a certificate (STAMP_EXPERTISED), and that a copy
or scan of a real item differ in size from it by at least 25% and say it is one
(STAMP_IMG_REPRO: the original's size and the word printed under it). View › Frames shows the
pages as they hang: 4, 3 or 2 to a row by sheet size, 4 rows to a frame.
"""

import io

from fastapi.testclient import TestClient
from PIL import Image
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401

from stamp_album import api
from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.engines import caption_layout

DSL = ('ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n'
       'STAMP_ADD_IMG(10 10 30 20 "/images/a.png" "a.png" "Map" "")\n'
       'STAMP_IMG_REPRO(40 26.7 "Reproduction")\n'
       'STAMP_ADD_AT(60 60 20 24 "Penny" "" "" "" rectangle "solid" "#000" 0.5 "#fff" 100)\n'
       'STAMP_EXPERTISED()\n')


def test_python_reads_writes_and_captions_them():
    album = AlbumParser().parse(DSL, "t.slbum")
    pic, stamp = album.pages[0].absolute_stamps
    assert pic.repro_size == (40, 26.7) and pic.repro_label == "Reproduction"
    assert stamp.expertised
    assert [p[:3] for p in caption_layout.caption_parts(pic)[1]] == [
        ("picture", "Map", "CapI"), ("reproduction", "Reproduction", "CapI")]
    assert caption_layout.caption_parts(stamp)[1][-1][:3] == ("expertised", "(e)", "CapB")
    out = AlbumSerializer().to_dsl(album)
    assert 'STAMP_IMG_REPRO(40 26.7 "Reproduction")' in out and "STAMP_EXPERTISED()" in out


def test_the_lines_belong_to_the_right_items():
    odd = DSL.replace('STAMP_EXPERTISED()\n', '').replace(
        'STAMP_IMG_REPRO(40 26.7 "Reproduction")\n', 'STAMP_EXPERTISED()\n')
    odd += 'STAMP_IMG_REPRO(40 26.7 "Reproduction")\n'
    pic, stamp = AlbumParser().parse(odd, "t.slbum").pages[0].absolute_stamps
    assert not pic.expertised and stamp.repro_size is None  # each only after its own kind


def test_python_and_the_editor_caption_alike(page):
    page.evaluate("StampAlbum.CORE.setMount(0, 1)")  # as the file says (no ALBUM_MOUNT line)
    lines = page.evaluate("""d => StampAlbum.CORE.parseDSL(d).pages[0].map(el =>
        StampAlbum.CORE.captionLayout(el, el.x, el.y, el.w, el.h).map(l =>
            [l.kind, l.text, l.fontId, Math.round(l.top * 100) / 100]))""", DSL)
    album = AlbumParser().parse(DSL, "t.slbum")
    ours = [[[ln.kind, ln.text, ln.font_id, round(ln.top, 2)]
             for ln in caption_layout.layout(s, s.abs_x, s.abs_y, s.width, s.height)]
            for s in album.pages[0].absolute_stamps]
    assert lines == ours


def _png_ink_below(state, y0_mm, y1_mm, x0_mm, x1_mm):
    r = TestClient(api.app).post("/export-from-state", json=state)
    assert r.status_code == 200
    img = Image.open(io.BytesIO(r.content)).convert("L")
    w, h = img.size
    box = tuple(round(v) for v in (x0_mm * w / 210, y0_mm * h / 297,
                                   x1_mm * w / 210, y1_mm * h / 297))
    return img.crop(box).point(lambda v: 255 if v < 128 else 0).getbbox() is not None


def test_the_export_prints_the_e_mark():
    stamp = {"id": "s", "t": "stamp", "s": "rectangle", "x": 150, "y": 150, "w": 50, "h": 60,
             "lbl": "Penny", "bdr": "solid", "bdrW": 0.5, "fill": "#fff", "fillA": 100}
    state = {"elements": [stamp], "pages": [], "page_width_px": 525, "page_height_px": 742.5,
             "scale": 2.5, "format": "png", "mount_overhang": 0, "mount_gap": 1}
    # Below the name's line (frame bottom 85 + 1 mm, name about 86 to 91 mm): the (e) line
    assert not _png_ink_below(state, 91.5, 96, 60, 80)
    stamp["exp"] = True
    assert _png_ink_below(state, 91.5, 96, 60, 80)


# ── The editor ──


def _picture(page, w=60, h=40):
    page.evaluate("StampAlbum.newAlbum()")
    page.evaluate(f"""StampAlbum.add({{ t: 'image', s: 'rectangle', x: StampAlbum.px(40),
        y: StampAlbum.px(60), w: StampAlbum.px({w}), h: StampAlbum.px({h}), lbl: 'map.png',
        img: '/images/map.png', cap: 'Route map', bdr: 'none', bdrW: 0, fill: 'transparent',
        fillA: 0 }})""")


def test_marking_a_copy_and_making_it_75_percent(page):
    _picture(page)
    assert page.is_visible("#prepro-row") and page.is_hidden("#porig-row")
    page.check("#prepro")
    el = page.evaluate("StampAlbum.E[0]")
    assert (el["origW"], el["origH"], el["reproLbl"]) == (60, 40, "Reproduction")
    assert "100% of the original: too close" in page.inner_text("#prepro-note")
    assert page.is_visible("#prepro-fit")
    page.click("#prepro-fit")
    size = page.evaluate("[StampAlbum.mm(StampAlbum.E[0].w), StampAlbum.mm(StampAlbum.E[0].h)]")
    assert size == [45, 30]
    assert page.inner_text("#prepro-note") == "Shown at 75% of the original."
    assert page.is_hidden("#prepro-fit")
    assert page.locator(".caption-reproduction").count() == 1
    assert 'STAMP_IMG_REPRO(60 40 "Reproduction")' in page.evaluate("StampAlbum.buildDSL()")
    page.evaluate("StampAlbum.undo()")
    assert page.evaluate("StampAlbum.mm(StampAlbum.E[0].w)") == 60


def test_the_original_size_can_be_corrected(page):
    _picture(page, 30, 20)
    page.check("#prepro")
    page.fill("#porig-w", "40")
    page.press("#porig-w", "Tab")
    assert page.evaluate("StampAlbum.E[0].origW") == 40
    assert page.inner_text("#prepro-note") == "Shown at 75% of the original."
    page.uncheck("#prepro")
    assert "origW" not in page.evaluate("StampAlbum.E[0]")
    assert page.locator(".caption-reproduction").count() == 0


def test_check_exhibit_flags_a_copy_too_close_in_size(page):
    _picture(page)
    page.check("#prepro")
    page.evaluate("StampAlbum.select(null); StampAlbum.openCheck()")
    assert "1 copy is too close in size" in page.inner_text("#chk-fix")


def test_an_expertised_stamp(page):
    page.evaluate("StampAlbum.newAlbum()")
    page.evaluate("""StampAlbum.add({ t: 'stamp', s: 'rectangle', x: StampAlbum.px(60),
        y: StampAlbum.px(60), w: StampAlbum.px(20), h: StampAlbum.px(24), lbl: 'Penny' })""")
    page.click("#more-toggle")
    page.check("#pexp")
    assert page.evaluate("StampAlbum.E[0].exp") is True
    assert page.locator(".caption-expertised").inner_text() == "(e)"
    assert "1 filled in" in page.inner_text("#more-count")
    assert "STAMP_EXPERTISED()" in page.evaluate("StampAlbum.buildDSL()")
    page.uncheck("#pexp")
    assert page.locator(".caption-expertised").count() == 0


# ── Frames ──


def _frames(page, pages, size=None):
    page.evaluate("StampAlbum.newAlbum()")
    if size:
        page.evaluate("StampAlbum.select(null)")
        page.click("#btn-page-setup")
        page.select_option("#ps-size", size)
        page.click("#ps-apply")
    for _ in range(pages - 1):
        page.evaluate("StampAlbum.addPage()")
    page.click("#menu-view-btn")
    page.click("#menu-frames")
    assert page.is_visible("#frames-overlay")
    return page.evaluate("""[...document.querySelectorAll('.fv-frame')].map(f =>
        [f.querySelector('h3').textContent, f.querySelectorAll('.fv-page').length,
         getComputedStyle(f.querySelector('.fv-grid')).gridTemplateColumns.split(' ').length])""")


def test_a4_pages_hang_16_to_a_frame(page):
    assert _frames(page, 20) == [["Frame 1", 16, 4], ["Frame 2", 4, 4]]
    assert page.inner_text("#fv-note").endswith("4 sheets to a row, 16 to a frame. 2 frames.")


def test_31_cm_sheets_hang_3_to_a_row(page):
    assert _frames(page, 12, "fip31") == [["Frame 1", 12, 3]]


def test_a_page_in_a_frame_goes_to_it(page):
    _frames(page, 5)
    assert page.get_attribute(".fv-page:nth-child(3)", "aria-label") == "Page 3: go to it"
    page.click(".fv-page:nth-child(3)")
    assert page.is_hidden("#frames-overlay")
    assert page.evaluate("StampAlbum._currentPage") == 2
    page.keyboard.press("Escape")
    assert page.js_errors == []


def test_page_pictures_draw_the_border_where_the_album_has_it(page):
    page.evaluate("StampAlbum.newAlbum(); StampAlbum._pageBorder = 'solid'")
    page.evaluate("StampAlbum.syncPageBar()")
    page.evaluate("StampAlbum.render()")
    x = page.evaluate("Number(document.querySelector('#pg-list .pg-border').getAttribute('x'))")
    assert x == 13
