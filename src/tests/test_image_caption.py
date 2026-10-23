# ruff: noqa: F811
"""An image's caption: 8 pt italic, centred 2 mm below the image, wrapped to its width.

The owner's choices (2026-10-15): wrap to the image's width; a 2 mm gap, as stamp captions.
No frame round the caption or the image. The label (the file's name) is never printed.
In the file it is the third quoted field of STAMP_ADD_IMG, empty in every older album.
"""
import io
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401

from stamp_album.api import app
from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.engines import caption_layout as cl

SC = 2.5
X, Y, W, H = 60.0, 80.0, 50.0, 40.0
CAPTION = "Coat of arms, adopted 1932"
LINE = 8 * 1.3 * 25.4 / 72  # an 8 pt line box, mm
BELOW_TOP = Y + H + 2  # no frame: 2 mm below the image's own edge


def _picture(**kw):
    el = {"t": "image", "s": "rectangle", "x": X * SC, "y": Y * SC, "w": W * SC, "h": H * SC,
          "lbl": "arms.png", "img": "/images/arms.png", "cap": CAPTION,
          # as the editor placed images before this change: a thin border in the request
          "bdr": "solid", "bdrC": "#999", "bdrW": 0.5, "fill": "#fff", "fillA": 100}
    el.update(kw)
    return el


def _export(fmt, el):
    state = {"elements": [el], "pages": [], "page_width_px": 210 * SC,
             "page_height_px": 297 * SC, "scale": SC, "format": fmt, "source_path": "t.slbum"}
    url = "/render-from-state" if fmt == "html" else "/export-from-state"
    r = TestClient(app).post(url, json=state)
    assert r.status_code == 200, r.text
    return r.content


def _fake_measure(text, font_id, size):
    return len(text) * size * 0.5 * 25.4 / 72


def _parse(dsl):
    return AlbumParser().parse(dsl)


def _pic_stamp(caption=CAPTION):
    album = _parse('ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n'
                   f'STAMP_ADD_IMG({X} {Y} {W} {H} "/images/arms.png" "arms.png" "{caption}" "")\n')
    (stamp,) = album.pages[0].absolute_stamps
    return stamp


# ── The shared layout ──

def test_layout_is_one_italic_line_2mm_below_the_image():
    lines = cl.layout(_pic_stamp(), X, Y, W, H, _fake_measure)
    assert [(ln.kind, ln.text, ln.font_id, ln.size_pt) for ln in lines] == [
        ("picture", CAPTION, "CapI", 8.0)]
    assert lines[0].top == pytest.approx(BELOW_TOP)
    assert lines[0].x + lines[0].width / 2 == pytest.approx(X + W / 2)  # centred


def test_layout_wraps_to_the_image_width():
    long = "A caption long enough to need three lines under a narrow picture"
    lines = cl.layout(_pic_stamp(long), X, Y, 20, H, _fake_measure)
    assert len(lines) >= 3
    assert all(ln.width <= 20 + 1e-6 for ln in lines)
    assert lines[1].top == pytest.approx(lines[0].bottom)  # it grows downwards


def test_no_caption_no_lines_and_the_label_is_never_printed():
    assert cl.layout(_pic_stamp(""), X, Y, W, H, _fake_measure) == []
    assert all("arms.png" not in ln.text for ln in cl.layout(_pic_stamp(), X, Y, W, H))


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_editor_layout_matches_the_exports():
    el = {"t": "image", "lbl": "arms.png", "img": "/images/arms.png",
          "cap": "A caption long enough to wrap under the picture", "bdr": "solid", "bdrW": 0.5}
    core = Path(__file__).resolve().parents[1] / "stamp_album" / "web" / "dsl_core.js"
    script = (f"const c = require({json.dumps(str(core))});"
              f"const m = (t, f, s) => t.length * s * 0.5 * 25.4 / 72;"
              f"console.log(JSON.stringify("
              f"c.captionLayout({json.dumps(el)}, {X}, {Y}, 30, {H}, m)));")
    js = json.loads(subprocess.run([shutil.which("node"), "-e", script], capture_output=True,
                                   text=True, encoding="utf-8", check=True).stdout)
    py = cl.layout(_pic_stamp(el["cap"]), X, Y, 30, H, _fake_measure)
    assert [(j["kind"], j["text"], j["fontId"]) for j in js] == [
        (p.kind, p.text, p.font_id) for p in py]
    for j, p in zip(js, py):
        assert (j["top"], j["bottom"], j["x"]) == pytest.approx((p.top, p.bottom, p.x))


# ── The file ──

def test_old_albums_open_without_a_caption():
    assert _pic_stamp("").picture_caption == ""
    album = _parse('ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n'
                   'STAMP_ADD_IMG(10 10 40 30 "/images/a.png" "a.png" "" "")\n')
    assert album.pages[0].absolute_stamps[0].picture_caption == ""


def test_caption_survives_a_save_in_python():
    text = 'He said "1932" \\\\ revised'
    quoted = text.replace('"', '\\"')
    dsl = AlbumSerializer().to_dsl(_parse(
        'ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n'
        f'STAMP_ADD_IMG(10 10 40 30 "/images/a.png" "a.png" "{quoted}" "")\n'))
    assert re.search(r'STAMP_ADD_IMG\([^)]*"a\.png" "He said \\"1932\\" ', dsl), dsl
    again = _parse(dsl).pages[0].absolute_stamps[0]
    assert again.picture_caption == 'He said "1932" \\ revised'


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_caption_survives_a_save_in_the_editor():
    core = Path(__file__).resolve().parents[1] / "stamp_album" / "web" / "dsl_core.js"
    dsl = ('ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n'
           'STAMP_ADD_IMG(10 10 40 30 "/images/a.png" "a.png" "Arms, \\"1932\\"" "")')
    script = (f"const c = require({json.dumps(str(core))});"
              f"const s = c.parseDSL({json.dumps(dsl)});"
              f"const el = s.pages.flat().find(e => e.t === 'image');"
              f"console.log(JSON.stringify([el.cap, el.lbl, c.serializeEl(el)]));")
    out = subprocess.run([shutil.which("node"), "-e", script], capture_output=True, text=True,
                         encoding="utf-8")
    assert out.returncode == 0, out.stderr
    cap, lbl, line = json.loads(out.stdout)
    assert (cap, lbl) == ('Arms, "1932"', "a.png")
    assert line.endswith('"/images/a.png" "a.png" "Arms, \\"1932\\"" "")')


# ── Every export ──

def test_svg_prints_the_caption_in_italics_and_no_frame():
    root = ET.fromstring(_export("svg", _picture()))
    ns = "{http://www.w3.org/2000/svg}"
    texts = [t for t in root.iter(ns + "text") if t.text == CAPTION]
    assert len(texts) == 1
    t = texts[0]
    assert t.get("font-style") == "italic"
    assert float(t.get("font-size")) == pytest.approx(8 * 25.4 / 72, abs=0.01)
    assert float(t.get("y")) == pytest.approx(BELOW_TOP + 8 * 25.4 / 72, abs=0.01)
    assert not [t for t in root.iter(ns + "text") if "arms.png" in (t.text or "")]
    # No frame line round the picture
    rects = [r for r in root.iter(ns + "rect") if r.get("stroke") not in (None, "none")]
    assert not [r for r in rects
                if abs(float(r.get("width", 0)) - W) < 3 and abs(float(r.get("height", 0)) - H) < 3]


def test_preview_prints_the_caption():
    html = _export("html", _picture()).decode()
    m = re.search(r'<div class="caption caption-picture"[^>]*>([^<]*)</div>', html)
    assert m and m.group(1) == CAPTION
    assert "font-style:italic" in m.group(0)
    assert float(re.search(r"top:([\d.]+)mm", m.group(0)).group(1)) == pytest.approx(BELOW_TOP,
                                                                                     abs=0.01)


def test_pdf_prints_the_caption(monkeypatch):
    from reportlab.pdfgen import canvas

    drawn, state = [], {}
    orig_font, orig_draw = canvas.Canvas.setFont, canvas.Canvas.drawString

    def set_font(self, name, size, *a, **k):
        state["font"] = (name, size)
        return orig_font(self, name, size, *a, **k)

    def draw(self, x, y, text, *a, **k):
        drawn.append((text, y, state.get("font")))
        return orig_draw(self, x, y, text, *a, **k)

    monkeypatch.setattr(canvas.Canvas, "setFont", set_font)
    monkeypatch.setattr(canvas.Canvas, "drawString", draw)
    _export("pdf", _picture())
    pt = 72 / 25.4
    (got,) = [(297 * pt - y) / pt for t, y, f in drawn if t == CAPTION]
    assert got == pytest.approx(BELOW_TOP + 8 / pt, abs=0.01)
    assert [f for t, y, f in drawn if t == CAPTION] == [("SourceSerif4Caption-CapI", 8)]


def test_png_prints_the_caption_below_the_gap():
    img = Image.open(io.BytesIO(_export("png", _picture()))).convert("L")
    ppm = img.width / 210

    def darkest(top, bottom):
        box = (int((X + 2) * ppm), int(top * ppm), int((X + W - 2) * ppm), int(bottom * ppm))
        return img.crop(box).getextrema()[0]

    assert darkest(Y + H + 0.3, BELOW_TOP - 0.1) == 255, "the 2 mm gap stays clear"
    assert darkest(BELOW_TOP, BELOW_TOP + LINE) < 60, "the caption is drawn below it"
    assert darkest(Y - 3, Y - 0.3) == 255, "no frame line above the picture"


def test_an_empty_caption_prints_nothing():
    root = ET.fromstring(_export("svg", _picture(cap="")))
    assert not [t for t in root.iter("{http://www.w3.org/2000/svg}text")
                if "caption" in (t.get("class") or "")]


# ── The editor ──

def _png_bytes(size=(300, 200)):
    buf = io.BytesIO()
    Image.new("RGB", size, (180, 40, 40)).save(buf, "PNG")
    return buf.getvalue()


def _new_with_image(page, cap=""):
    page.route(re.compile(r".*/images/[^/]+$"),
               lambda r: r.fulfill(body=_png_bytes(), content_type="image/png"))
    page.evaluate("""cap => { StampAlbum._dirty = false; StampAlbum.newAlbum();
        StampAlbum.add({t: 'image', s: 'rectangle', x: 150, y: 200, w: 125, h: 100,
                        lbl: 'arms.png', img: '/images/arms.png', cap: cap,
                        bdr: 'none', bdrW: 0, fill: 'transparent', fillA: 0}); }""", cap)
    return page.evaluate("StampAlbum.E[0].id")


def test_panel_caption_field_prints_below_the_image(page):
    _new_with_image(page)
    assert page.is_visible("#pcap") and page.is_visible("#pcap-note")
    assert page.text_content("#cap-sec") == "Caption"
    assert not page.is_visible("#plbl")
    assert page.locator(".cel .caption-picture").count() == 0  # empty: nothing on the page
    page.fill("#pcap", "Coat of arms")
    page.press("#pcap", "Tab")
    cap = page.locator(".cel .caption-picture")
    assert cap.text_content() == "Coat of arms"
    # Read in one step: typing redraws the page on the next frame, which replaces the line a
    # locator found a moment earlier (its style then reads as empty on slower machines).
    style = page.evaluate("""(() => { const n = document.querySelector('.cel .caption-picture');
        return [getComputedStyle(n).fontStyle, getComputedStyle(n).borderStyle]; })()""")
    assert style == ["italic", "none"]
    img, c = page.evaluate("""[document.querySelector('.cel').getBoundingClientRect().bottom,
        document.querySelector('.cel .caption-picture').getBoundingClientRect().top]""")
    zoom = page.evaluate("StampAlbum.zoom || 1")
    assert (c - img) / zoom == pytest.approx(2 * SC, abs=1.5)  # 2 mm at 2.5 px/mm
    assert page.evaluate("StampAlbum.buildDSL()").count('"arms.png" "Coat of arms" ""') == 1


def test_caption_is_typed_on_the_page_and_undone(page):
    _new_with_image(page, "Arms")
    page.click(".cel .caption-picture")
    page.keyboard.press("End")
    page.keyboard.type(" of Bahrain")
    page.click("#page", position={"x": 5, "y": 5})
    page.wait_for_timeout(100)
    assert page.evaluate("StampAlbum.E[0].cap") == "Arms of Bahrain"
    page.keyboard.press("Control+z")
    assert page.evaluate("StampAlbum.E[0].cap") == "Arms"


def test_long_caption_grows_and_wraps_to_the_image(page):
    _new_with_image(page, "A long caption under a picture that wraps over several lines here")
    w, lines = page.evaluate("""[document.querySelector('.cel').getBoundingClientRect().width,
        document.querySelector('.cel .caption-picture').textContent.split('\\n').length]""")
    assert lines >= 2
    cw = page.evaluate(
        "document.querySelector('.cel .caption-picture').getBoundingClientRect().width")
    assert cw <= w + 1


def test_duplicate_keeps_the_caption(page):
    _new_with_image(page, "Arms")
    page.keyboard.press("Control+d")
    assert page.evaluate("StampAlbum.E.map(e => e.cap)") == ["Arms", "Arms"]


def test_caption_past_the_border_is_flagged(page):
    page.route(re.compile(r".*/images/[^/]+$"),
               lambda r: r.fulfill(body=_png_bytes(), content_type="image/png"))
    page.evaluate("""() => { StampAlbum._dirty = false; StampAlbum.newAlbum();
        StampAlbum.add({t: 'image', s: 'rectangle', x: 150, y: StampAlbum._ph - 105, w: 125, h: 100,
                        lbl: 'a.png', img: '/images/a.png', cap: 'Too low to fit',
                        bdr: 'none', bdrW: 0, fill: 'transparent', fillA: 0}); }""")
    assert page.locator(".cel.caption-warn").count() == 1


def test_attached_images_have_no_frame(page):
    page.route(re.compile(r".*/images/[^/]+$"),
               lambda r: r.fulfill(body=_png_bytes(), content_type="image/png"))
    page.evaluate("StampAlbum._dirty = false; StampAlbum.newAlbum();"
                  " StampAlbum.placeImage('x.png')")
    for _ in range(100):
        if page.evaluate("StampAlbum.E.length"):
            break
        page.wait_for_timeout(50)
    el = page.evaluate("StampAlbum.E[0]")
    assert el["bdr"] == "none" and el["cap"] == ""
    assert page.evaluate("getComputedStyle(document.querySelector('.cel')).borderStyle") == "none"
