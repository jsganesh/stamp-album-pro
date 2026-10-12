"""Bold and italic page text must look the same in every export.

The editor draws a "HB" (Helvetica Bold) heading bold, and so do the PDF and the PNG.
The SVG and the HTML (export and preview) used to draw every page text in regular
weight, and the SVG wrapped every line with regular Helvetica's widths.
"""

import re

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfbase import pdfmetrics

from stamp_album.api import app
from stamp_album.core.parser import AlbumParser
from stamp_album.engines import text_layout
from stamp_album.engines.html_renderer import HTMLRenderer
from stamp_album.engines.svg_export import SVGExporter
from stamp_album.templates import TEMPLATES

# font id -> (weight, style), as the editor's fontCSS() in app.js draws it
EXPECTED = {
    "HN": ("normal", "normal"), "HB": ("bold", "normal"),
    "HI": ("normal", "italic"), "HS": ("bold", "italic"),
    "TN": ("normal", "normal"), "TB": ("bold", "normal"),
    "TI": ("normal", "italic"), "TS": ("bold", "italic"),
    "CN": ("normal", "normal"), "CB": ("bold", "normal"),
    "CI": ("normal", "italic"), "CS": ("bold", "italic"),
}
FAMILY = {"H": "Helvetica", "T": "Times", "C": "Courier"}


def _album(font_id: str, text: str = "Low values", w: float = 170.0):
    dsl = (
        "ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n"
        f'PAGE_TEXT_AT(20.0 40.0 {w} 30.0 "{font_id}" 11 "{text}" "left")\n'
    )
    return AlbumParser().parse(dsl, "t.slbum")


def _svg_texts(svg: str) -> list[str]:
    return [t for t in re.findall(r"<text\b[^>]*>", svg) if 'class="caption' not in t]


def _attr(tag: str, name: str, default: str) -> str:
    m = re.search(rf'\b{name}="([^"]*)"', tag)
    return m.group(1) if m else default


@pytest.mark.parametrize("font_id", sorted(EXPECTED))
def test_svg_keeps_weight_style_and_family(font_id):
    weight, style = EXPECTED[font_id]
    tags = _svg_texts(SVGExporter().generate_to_string(_album(font_id)))
    assert tags, "no page text drawn"
    for tag in tags:
        assert _attr(tag, "font-weight", "normal") == weight, tag
        assert _attr(tag, "font-style", "normal") == style, tag
        assert FAMILY[font_id[0]] in tag, tag


@pytest.mark.parametrize("font_id", sorted(EXPECTED))
def test_html_keeps_weight_style_and_family(font_id):
    weight, style = EXPECTED[font_id]
    html = HTMLRenderer(_album(font_id), None).render()
    divs = re.findall(r'<div class="text-el" style="([^"]*)"', html)
    assert divs, "no page text drawn"
    for css in divs:
        assert f"font-weight:{weight};" in css, css
        assert f"font-style:{style};" in css, css
        assert FAMILY[font_id[0]] in css, css


def test_svg_wraps_bold_text_with_bold_widths():
    """A line that fits in regular Helvetica but not in bold must wrap, as in the PDF."""
    text = "Shades and varieties of the second printing"
    size_mm = 11 / text_layout.PT_PER_MM
    regular = pdfmetrics.stringWidth(text, "Helvetica", size_mm)
    bold = pdfmetrics.stringWidth(text, "Helvetica-Bold", size_mm)
    assert bold > regular
    box_w = (regular + bold) / 2 + 2 * text_layout.PAD_MM  # fits regular, not bold
    svg = SVGExporter().generate_to_string(_album("HB", text, round(box_w, 2)))
    assert len(_svg_texts(svg)) == 2


def test_unknown_font_id_falls_back_to_regular_helvetica():
    tags = _svg_texts(SVGExporter().generate_to_string(_album("XX")))
    assert tags and all("font-weight" not in t and "font-style" not in t for t in tags)
    html = HTMLRenderer(_album("XX"), None).render()
    assert "font-weight:normal;font-style:normal;" in html


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.mark.parametrize("tid", [t["id"] for t in TEMPLATES])
def test_export_html_gallery(client, tid):
    """``/export`` with format "html" used to fail with a 500 every time."""
    t = next(t for t in TEMPLATES if t["id"] == tid)
    r = client.post("/export", json={"dsl": t["content"], "format": "html",
                                     "source_path": tid + ".slbum"})
    assert r.status_code == 200, r.text[:300]
    assert r.headers["content-type"].startswith("text/html")
    assert r.text.lstrip().startswith("<!DOCTYPE html>")
    assert 'class="text-el"' in r.text
