"""Album themes: the theme colours the page border and marked headings in every export."""

import io
import re
import zlib

import pytest
from PIL import Image

from stamp_album.api import CanvasElementState, CanvasStateRequest, _canvas_state_to_album
from stamp_album.core.models import Color
from stamp_album.core.parser import AlbumParser
from stamp_album.core.themes import THEMES
from stamp_album.engines.html_renderer import HTMLRenderer
from stamp_album.engines.pdf import PDFGenerator
from stamp_album.engines.raster import PNGGenerator
from stamp_album.engines.svg_export import SVGExporter

GREEN = THEMES["green"]


def _hex(c: Color) -> str:
    return "#%02X%02X%02X" % (round(c.r * 255), round(c.g * 255), round(c.b * 255))


DSL = "\n".join(
    [
        'ALBUM_THEME("green")',
        "ALBUM_PAGES_SIZE(210 297)",
        "ALBUM_PAGES_BORDER(0.5 0 0 1)",
        "PAGE_START",
        'PAGE_TEXT_AT(20.0 15.0 170.0 14.0 "HB" 20 "Great Britain" "left")',
        'PAGE_TEXT_ROLE("heading")',
        'PAGE_TEXT_AT(20.0 40.0 170.0 10.0 "HN" 10 "Plain text" "left")',
    ]
)


def _texts(album):
    return [s for s in album.pages[0].absolute_stamps if s.is_text_element]


# ── Theme list matches the editor's ──


def test_theme_list():
    assert list(THEMES) == ["exhibition", "green", "maroon", "navy", "brown"]
    assert THEMES["exhibition"] == "#000000"


# ── Python parser (exports made from a file) ──


def test_parser_applies_the_theme_to_border_and_marked_headings():
    album = AlbumParser().parse(DSL)
    heading, plain = _texts(album)
    assert _hex(album.color_album_border) == GREEN
    assert heading.text_color is not None and _hex(heading.text_color) == GREEN
    assert plain.text_color is None


def test_parser_custom_border_colour_without_a_theme_is_kept():
    album = AlbumParser().parse(
        'ALBUM_PAGES_BORDER(0.5 0 0 1)\nCOLOUR_ALBUM_BORDER("#FF0000")\nPAGE_START'
    )
    assert _hex(album.color_album_border) == "#FF0000"


# ── Canvas state (exports made from the editor) ──


def _state(**kw):
    els = [
        CanvasElementState(
            t="text",
            s="text",
            x=50,
            y=37.5,
            w=425,
            h=35,
            lbl="Great Britain",
            font="HB",
            fs=20,
            role="heading",
        ),
        CanvasElementState(
            t="text", s="text", x=50, y=100, w=425, h=25, lbl="Plain text", font="HN", fs=10
        ),
        CanvasElementState(t="stamp", s="rectangle", x=50, y=150, w=100, h=75, lbl="Stamp"),
    ]
    return CanvasStateRequest(
        elements=els, border_style="solid", border_color=GREEN, theme_color=GREEN, **kw
    )


def test_canvas_state_colours_marked_headings_only():
    album = _canvas_state_to_album(_state())
    heading, plain = _texts(album)
    assert _hex(heading.text_color) == GREEN
    assert plain.text_color is None
    assert _hex(album.color_album_border) == GREEN


# ── Each export draws the heading in the theme colour ──


def test_svg_heading_in_theme_colour():
    svg = SVGExporter().generate_to_string(_canvas_state_to_album(_state()))
    heading = re.search(r'<text[^>]*fill="([^"]+)"[^>]*>Great Britain<', svg)
    plain = re.search(r'<text[^>]*fill="([^"]+)"[^>]*>Plain text<', svg)
    assert heading and heading.group(1).upper() == GREEN
    assert plain and plain.group(1).upper() != GREEN


def test_html_heading_in_theme_colour():
    html = HTMLRenderer(_canvas_state_to_album(_state()), None).render()
    heading = re.search(r'<div class="text-el" style="([^"]*)">Great Britain<', html)
    plain = re.search(r'<div class="text-el" style="([^"]*)">Plain text<', html)
    assert heading and ("color:" + GREEN.lower()) in heading.group(1).lower()
    assert plain and GREEN.lower() not in plain.group(1).lower()


def _near(rgb, hex_colour, tol=40):
    want = tuple(int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))
    return all(abs(a - b) <= tol for a, b in zip(rgb, want))


def test_png_heading_in_theme_colour():
    png = PNGGenerator().generate_to_bytes(_canvas_state_to_album(_state()), dpi=100)
    im = Image.open(io.BytesIO(png)).convert("RGB")
    px_mm = im.width / 210

    def colours(x0, y0, x1, y1):
        box = im.crop((int(x0 * px_mm), int(y0 * px_mm), int(x1 * px_mm), int(y1 * px_mm)))
        return (
            [p for p in box.get_flattened_data() if sum(p) < 600]
            if hasattr(box, "get_flattened_data")
            else [p for p in box.getdata() if sum(p) < 600]
        )  # ink, not paper

    heading_ink = colours(20, 15, 120, 29)
    plain_ink = colours(20, 40, 80, 50)
    assert heading_ink and sum(_near(p, GREEN) for p in heading_ink) > len(heading_ink) // 2
    assert plain_ink and not any(_near(p, GREEN, tol=20) for p in plain_ink)


def test_pdf_heading_in_theme_colour(tmp_path, monkeypatch):
    from reportlab import rl_config

    monkeypatch.setattr(rl_config, "pageCompression", 0)
    out = tmp_path / "t.pdf"
    PDFGenerator().generate(_canvas_state_to_album(_state()), str(out))
    data = out.read_bytes()
    streams = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        raw = m.group(1)
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            pass
        streams.append(raw.decode("latin-1"))
    page = "\n".join(streams)
    # The fill colour set just before the heading's text is shown
    idx = page.find("(Great Britain)")
    assert idx != -1, "heading text not found in the PDF"
    fills = re.findall(r"([\d.]+) ([\d.]+) ([\d.]+) rg", page[:idx])
    assert fills, "no fill colour before the heading"
    r, g, b = (float(v) * 255 for v in fills[-1])
    assert _near((r, g, b), GREEN, tol=3), (r, g, b)


@pytest.mark.parametrize("theme", ["maroon", "navy", "brown"])
def test_other_themes_reach_the_parser(theme):
    album = AlbumParser().parse(DSL.replace('"green"', f'"{theme}"'))
    assert _hex(_texts(album)[0].text_color) == THEMES[theme]
