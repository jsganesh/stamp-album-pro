"""Caption headings in a row: stamps whose frame bottoms are level put their headings on
one line, above the row's highest frame, in every view (``caption_layout.heading_rows``,
``captionRows`` in ``web/dsl_core.js``).

The Exhibition page template's second row (36 x 25 mm beside 19 x 22 mm) is the case that
showed it: the small stamps' headings sat 3 mm lower than their neighbours'.
"""

import json
import random
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from stamp_album.core.parser import AlbumParser
from stamp_album.engines import caption_layout as cl
from stamp_album.engines import frames
from stamp_album.templates import TEMPLATES

CORE = Path(__file__).resolve().parents[1] / "stamp_album" / "web" / "dsl_core.js"
EXHIBITION = next(t for t in TEMPLATES if t["id"] == "exhibition_page")


def _node(script: str):
    out = subprocess.run(
        [shutil.which("node"), "-e", f"const c = require({json.dumps(str(CORE))});" + script],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    return json.loads(out)


def _second_row():
    """The Exhibition page's second row: stamps whose top is between 140 and 150 mm."""
    album = AlbumParser().parse(EXHIBITION["content"], "exhibition_page.slbum")
    page = album.pages[0]
    row = [s for s in page.absolute_stamps if not s.is_text_element and 140 < s.abs_y < 150]
    assert len(row) == 4 and len({s.abs_y for s in row}) == 2  # mixed heights
    return album, page, row


# ── The rule ──


def test_rows_match_the_editor():
    """heading_rows and captionRows agree on pages of random boxes."""
    rng = random.Random(7)
    pages = []
    for _ in range(200):
        items = []
        for _ in range(rng.randint(1, 8)):
            w, h = rng.choice([19, 22, 25, 36]), rng.choice([10, 22, 25, 30])
            bottom = rng.choice([60, 60.5, 61.2, 90, 120])
            items.append((rng.uniform(10, 180), bottom - h, w, h, rng.random() < 0.75))
        pages.append(items)
    js = _node(
        f"const pages = {json.dumps(pages)};"
        "console.log(JSON.stringify(pages.map(p => c.captionRows("
        "p.map(([x, y, w, h, heading]) => ({x, y, w, h, heading}))))));"
    )
    for items, got in zip(pages, js):
        py = cl.heading_rows(items)
        assert [None if v is None else round(v, 6) for v in py] == [
            None if v is None else round(v, 6) for v in got
        ], items
    assert cl.ROW_TOLERANCE_MM == _node("console.log(c.CAPTION.ROW_TOLERANCE_MM)")


def test_layout_with_a_row_top_matches_the_editor():
    el = {"t": "stamp", "bdr": "solid", "bdrW": 0.5, "hdg": "Heading", "lbl": "Name"}
    js = _node(
        "const m = (t, f, s) => t.length * s * 0.5 * 25.4 / 72;"
        f"console.log(JSON.stringify(c.captionLayout({json.dumps(el)}, 80, 146, 19, 22, m,"
        " { rowTop: 141.8 })));"
    )
    from stamp_album.core.models import Stamp, StampHeading

    s = Stamp(description="Name")
    s.heading = StampHeading(text="Heading", font_id="HN", size=9.0)
    py = cl.layout(s, 80, 146, 19, 22, lambda t, f, z: len(t) * z * 0.5 * 25.4 / 72, row_top=141.8)
    assert [(j["kind"], j["top"]) for j in js] == [(p.kind, pytest.approx(p.top)) for p in py]
    assert py[0].bottom == pytest.approx(141.8 - cl.GAP_MM)


def test_the_exhibition_page_row_shares_one_heading_line():
    _album, page, row = _second_row()
    tops = cl.page_row_tops(page.absolute_stamps)
    highest = min(frames.outer_box(s, s.abs_x, s.abs_y, s.width, s.height)[1] for s in row)
    assert [tops[id(s)] for s in row] == pytest.approx([highest] * 4)
    bottoms = {
        round(cl.layout(s, s.abs_x, s.abs_y, s.width, s.height, row_top=tops[id(s)])[0].bottom, 6)
        for s in row
    }
    assert len(bottoms) == 1


# ── Every export ──


def _export(gen_cls, method="generate_to_bytes", **kw):
    album, _page, row = _second_row()
    return getattr(gen_cls(), method)(album, **kw), row


def test_pdf_headings_on_one_line(monkeypatch):
    from reportlab.pdfgen import canvas

    from stamp_album.engines.pdf import PDFGenerator

    baselines, orig = [], canvas.Canvas.drawString

    def draw(self, x, y, text, *a, **k):
        if text == "Heading":
            baselines.append(round(y, 3))
        return orig(self, x, y, text, *a, **k)

    monkeypatch.setattr(canvas.Canvas, "drawString", draw)
    _export(PDFGenerator)
    # The page has three rows of headed stamps; the second row's four share one baseline.
    assert len(baselines) == 8 and len(set(baselines[3:7])) == 1, baselines


def test_svg_headings_on_one_line():
    from stamp_album.engines.svg_export import SVGExporter

    svg, _row = _export(SVGExporter, "generate_to_string")
    root = ET.fromstring(svg)
    ys = [float(t.get("y")) for t in root.iter("{http://www.w3.org/2000/svg}text")
          if t.text == "Heading"]
    assert len(ys) == 8 and len({round(y, 3) for y in ys[3:7]}) == 1, ys


def test_preview_headings_on_one_line():
    from stamp_album.engines.html_renderer import HTMLRenderer

    album, _page, _row = _second_row()
    html = HTMLRenderer(album).render()
    tops = [float(m.group(1)) for m in re.finditer(
        r'class="caption caption-heading"[^>]*top:([\d.]+)mm[^>]*>Heading<', html)]
    assert len(tops) == 8 and len(set(tops[3:7])) == 1, tops


def test_png_headings_on_one_line():
    from stamp_album.engines.raster import PNGGenerator

    png, row = _export(PNGGenerator)
    img = Image.open(BytesIO(png)).convert("L")
    ppm = img.width / 210

    def ink_bottom(s):  # lowest dark pixel in the band above the stamp's frame
        fx, fy, fw, _ = frames.outer_box(s, s.abs_x, s.abs_y, s.width, s.height)
        band = img.crop((int(fx * ppm), int((fy - 8) * ppm), int((fx + fw) * ppm), int(fy * ppm)))
        rows = [y for y in range(band.height)
                if min(band.crop((0, y, band.width, y + 1)).getextrema()) < 128]
        return (fy - 8) + (max(rows) + 1) / ppm

    bottoms = [ink_bottom(s) for s in row]
    assert max(bottoms) - min(bottoms) < 2 / ppm, bottoms
