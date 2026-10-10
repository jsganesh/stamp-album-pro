"""Stamp captions: one layout in every export (PDF, PNG, SVG, HTML preview).

Heading above the box (bold 9 pt); below it the description (8 pt), the details line
and the catalogue number (8 pt italic). The frame is drawn outside the stamp (1 mm clear,
then the line); the nearest line box is 2 mm from the frame's outer edge, lines are centred
and wrapped to the frame's width, and captions are black.
"""

import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from stamp_album.api import app
from stamp_album.core.models import Stamp, StampHeading
from stamp_album.engines import caption_layout as cl

SC = 2.5  # canvas px per mm in the request
X, Y, W, H = 40.0, 60.0, 40.0, 30.0
LINE = 8 * 1.3 * 25.4 / 72  # 8 pt line box in mm
OUT = 1.0 + 0.5 * 25.4 / 72  # a thin frame's outer edge: 1 mm clear, then a 0.5 pt line
HEADING_BOTTOM = Y - OUT - 2  # bottom of the heading's line box
BELOW_TOP = Y + H + OUT + 2  # top of the first line box below the stamp


def _el(**kw):
    el = {
        "t": "stamp",
        "s": "rectangle",
        "x": X * SC,
        "y": Y * SC,
        "w": W * SC,
        "h": H * SC,
        "bdr": "solid",
        "bdrC": "#000000",
        "bdrW": 0.5,
        "fill": "#ffffff",
        "fillA": 100,
        "font": "HN",
        "fs": 12,
        "hdg": "Penny Black",
        "lbl": "Plate 1a",
        "denom": "1d",
        "cond": "Used",
        "perf": "Imperforate",
        "cat": "SG 2",
    }
    el.update(kw)
    return el


def _export(fmt, el=None):
    state = {
        "elements": [el or _el()],
        "pages": [],
        "page_width_px": 210 * SC,
        "page_height_px": 297 * SC,
        "scale": SC,
        "format": fmt,
        "source_path": "t.slbum",
    }
    url = "/render-from-state" if fmt == "html" else "/export-from-state"
    r = TestClient(app).post(url, json=state)
    assert r.status_code == 200, r.text
    return r.content


def _fake_measure(text, font_id, size):  # deterministic widths for layout tests
    return len(text) * size * 0.5 * 25.4 / 72


def _stamp(**kw):
    s = Stamp(
        description=kw.get("description", "Plate 1a"),
        catalog_refs=kw.get("catalog_refs", ["SG 2", "", ""]),
    )
    s.font_id = kw.get("font_id", "HN")
    if kw.get("heading", "Penny Black"):
        s.heading = StampHeading(text=kw.get("heading", "Penny Black"), font_id="HN", size=9.0)
    s.footer_text = kw.get("footer_text", "1d · Used · Imperforate")
    return s


# ── The shared layout ──


def test_layout_order_gaps_and_styles():
    lines = cl.layout(_stamp(), X, Y, W, H, _fake_measure)
    assert [ln.kind for ln in lines] == ["heading", "description", "details", "catalogue"]
    head, desc, det, cat = lines
    assert head.bottom == pytest.approx(HEADING_BOTTOM)
    assert desc.top == pytest.approx(BELOW_TOP)
    assert det.top == pytest.approx(desc.bottom) and cat.top == pytest.approx(det.bottom)
    assert (head.font_id, head.size_pt) == ("HB", 9)
    assert (desc.font_id, desc.size_pt) == ("HN", 8)
    assert (det.font_id, det.size_pt) == ("HI", 8) and (cat.font_id, cat.size_pt) == ("HI", 8)
    assert cat.text == "SG 2"  # empty catalogue fields are dropped
    for ln in lines:
        assert ln.x + ln.width / 2 == pytest.approx(X + W / 2)  # centred


def test_layout_wraps_to_the_box_and_stacks_headings_upwards():
    s = _stamp(
        heading="A heading long enough to wrap over two lines",
        description="A description that is far too long for one line of a forty millimetre box",
    )
    lines = cl.layout(s, X, Y, W, H, _fake_measure)
    heads = [ln for ln in lines if ln.kind == "heading"]
    descs = [ln for ln in lines if ln.kind == "description"]
    assert len(heads) >= 2 and len(descs) >= 2
    assert heads[-1].bottom == pytest.approx(HEADING_BOTTOM)
    assert heads[0].bottom == pytest.approx(heads[1].top)
    assert all(ln.width <= W + 2 * OUT + 1e-6 for ln in lines)  # wrapped to the frame


def test_layout_drops_empty_parts():
    s = _stamp(heading="", description="", footer_text="", catalog_refs=["", "", ""])
    assert cl.layout(s, X, Y, W, H, _fake_measure) == []
    s = _stamp(heading="", description="", catalog_refs=[])
    lines = cl.layout(s, X, Y, W, H, _fake_measure)
    assert [ln.kind for ln in lines] == ["details"] and lines[0].top == pytest.approx(BELOW_TOP)


def test_description_follows_the_stamp_font_family():
    kinds = {
        ln.kind: ln.font_id for ln in cl.layout(_stamp(font_id="TN"), X, Y, W, H, _fake_measure)
    }
    assert kinds == {"heading": "HB", "description": "TN", "details": "TI", "catalogue": "TI"}


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_editor_layout_matches_the_exports():
    """web/dsl_core.js captionLayout gives the same lines as caption_layout.py."""
    el = {
        "t": "stamp",
        "bdr": "solid",
        "bdrW": 0.5,  # a thin frame, the Python default
        "hdg": "A heading long enough to wrap over two lines",
        "lbl": "The first adhesive postage stamp",
        "denom": "1d",
        "cond": "Used",
        "perf": "Imperforate",
        "cat": "SG 2",
        "font": "TN",
    }
    core = Path(__file__).resolve().parents[1] / "stamp_album" / "web" / "dsl_core.js"
    script = (
        f"const c = require({json.dumps(str(core))});"
        f"const m = (t, f, s) => t.length * s * 0.5 * 25.4 / 72;"
        f"console.log(JSON.stringify(c.captionLayout({json.dumps(el)}, {X}, {Y}, {W}, {H}, m)));"
    )
    js = json.loads(
        subprocess.run(
            [shutil.which("node"), "-e", script],
            capture_output=True,
            text=True,
            encoding="utf-8",  # the details line has "·"; Windows would decode as cp1252
            check=True,
        ).stdout
    )
    s = _stamp(heading=el["hdg"], description=el["lbl"], catalog_refs=[el["cat"]], font_id="TN")
    py = cl.layout(s, X, Y, W, H, _fake_measure)
    assert [(j["kind"], j["text"], j["fontId"]) for j in js] == [
        (p.kind, p.text, p.font_id) for p in py
    ]
    for j, p in zip(js, py):
        assert (j["top"], j["bottom"], j["x"]) == pytest.approx((p.top, p.bottom, p.x))


# ── PDF ──


def test_pdf_captions(monkeypatch):
    from reportlab.pdfgen import canvas

    calls, state = [], {}
    orig_font, orig_fill, orig_draw = (
        canvas.Canvas.setFont,
        canvas.Canvas.setFillColorRGB,
        canvas.Canvas.drawString,
    )

    def set_font(self, name, size, *a, **k):
        state["font"] = (name, size)
        return orig_font(self, name, size, *a, **k)

    def set_fill(self, r, g, b, *a, **k):
        state["fill"] = (r, g, b)
        return orig_fill(self, r, g, b, *a, **k)

    def draw(self, x, y, text, *a, **k):
        calls.append((text, x, y, state.get("font"), state.get("fill")))
        return orig_draw(self, x, y, text, *a, **k)

    monkeypatch.setattr(canvas.Canvas, "setFont", set_font)
    monkeypatch.setattr(canvas.Canvas, "setFillColorRGB", set_fill)
    monkeypatch.setattr(canvas.Canvas, "drawString", draw)
    _export("pdf")

    pt = 72 / 25.4
    got = {
        t: ((297 * pt - y) / pt, font, fill) for t, x, y, font, fill in calls
    }  # baseline mm from the top
    head, desc = got["Penny Black"], got["Plate 1a"]
    det, cat = got["1d · Used · Imperforate"], got["SG 2"]
    assert head[0] < HEADING_BOTTOM and head[1] == ("Helvetica-Bold", 9)
    assert desc[0] == pytest.approx(BELOW_TOP + 8 / pt, abs=0.01)  # below the box, not inside it
    assert desc[1] == ("Helvetica", 8)
    assert det[0] - desc[0] == pytest.approx(LINE, abs=0.01)  # no overlap
    assert cat[0] - det[0] == pytest.approx(LINE, abs=0.01)
    assert det[1] == ("Helvetica-Oblique", 8) and cat[1] == ("Helvetica-Oblique", 8)
    assert {v[2] for v in (head, desc, det, cat)} == {(0.0, 0.0, 0.0)}


# ── PNG ──


def test_png_captions_keep_the_gap_and_are_black():
    img = Image.open(BytesIO(_export("png"))).convert("L")
    ppm = img.width / 210

    def band(top_mm, bottom_mm):
        box = (int((X + 1) * ppm), int(top_mm * ppm), int((X + W - 1) * ppm), int(bottom_mm * ppm))
        return img.crop(box).getextrema()[0]  # darkest pixel

    assert band(Y + H + OUT + 0.3, BELOW_TOP - 0.1) == 255, (
        "caption text runs into the 2 mm gap below the frame"
    )
    assert band(HEADING_BOTTOM + 0.3, Y - OUT - 0.3) == 255, (
        "the heading runs into the 2 mm gap above the frame"
    )
    assert band(BELOW_TOP, BELOW_TOP + 4 * LINE) < 40, (
        "captions should be drawn in black below the box"
    )
    assert band(Y + 1, Y + H - 1) == 255, "nothing is drawn inside the box"


# ── SVG ──


def test_svg_captions():
    root = ET.fromstring(_export("svg"))
    texts = {t.text: t for t in root.iter("{http://www.w3.org/2000/svg}text")}
    head, desc = texts["Penny Black"], texts["Plate 1a"]
    det, cat = texts["1d · Used · Imperforate"], texts["SG 2"]
    for t in (head, desc, det, cat):
        assert t.get("fill") == "#000000"
        assert "pt" not in t.get("font-size")  # user units are mm
    assert float(head.get("font-size")) == pytest.approx(9 * 25.4 / 72, abs=0.01)
    assert float(desc.get("font-size")) == pytest.approx(8 * 25.4 / 72, abs=0.01)
    assert head.get("font-weight") == "bold"
    assert det.get("font-style") == "italic" and cat.get("font-style") == "italic"
    assert desc.get("font-style") is None
    assert float(head.get("y")) < HEADING_BOTTOM
    base = float(desc.get("y"))
    assert base == pytest.approx(BELOW_TOP + 8 * 25.4 / 72, abs=0.01)
    assert float(det.get("y")) - base == pytest.approx(LINE, abs=0.01)
    assert float(cat.get("y")) - base == pytest.approx(2 * LINE, abs=0.01)


# ── HTML preview ──


def test_preview_captions():
    html = _export("html").decode()
    caps = {
        m.group(1): m.group(0)
        for m in re.finditer(r'<div class="caption caption-(\w+)"[^>]*>', html)
    }
    assert set(caps) == {"heading", "description", "details", "catalogue"}

    def top(kind):
        return float(re.search(r"top:([\d.]+)mm", caps[kind]).group(1))

    def height(kind):
        return float(re.search(r"height:([\d.]+)mm", caps[kind]).group(1))

    assert top("heading") + height("heading") == pytest.approx(HEADING_BOTTOM, abs=0.01)
    assert top("description") == pytest.approx(BELOW_TOP, abs=0.01)
    assert top("details") == pytest.approx(BELOW_TOP + LINE, abs=0.01)
    assert top("catalogue") == pytest.approx(BELOW_TOP + 2 * LINE, abs=0.01)
    assert "font-weight:bold" in caps["heading"]
    assert "font-style:italic" in caps["details"] and "font-style:italic" in caps["catalogue"]
    assert all("color:#000000" in c for c in caps.values())


def test_a_picture_has_no_captions():
    el = {
        "t": "image",
        "s": "rectangle",
        "x": 100,
        "y": 100,
        "w": 150,
        "h": 150,
        "lbl": "ARMS",
        "img": "arms.png",
        "bdr": "none",
        "fill": "transparent",
    }
    assert b"ARMS" not in _export("svg", el)
    assert b"ARMS" not in _export("html", el)
