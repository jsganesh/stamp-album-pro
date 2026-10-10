# ruff: noqa: F811
"""Page borders: the same picture in the editor, preview, PDF, PNG and SVG.

The editor's drawing (web/borders.js) is the reference; engines/page_border.py
ports it and every export draws its primitives.
"""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageFilter
from reportlab.pdfgen import canvas as rl_canvas
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

from stamp_album.api import app
from stamp_album.engines import page_border as pb

SC = 2.5
PAGE_W, PAGE_H = 210.0, 297.0
STYLES = list(pb.STYLES)
PNG_PPM = 200 / 25.4  # the PNG export's pixels per mm


def _state(style, fmt, theme="#000000"):
    return {
        "elements": [],
        "pages": [],
        "page_width_px": PAGE_W * SC,
        "page_height_px": PAGE_H * SC,
        "scale": SC,
        "format": fmt,
        "source_path": "t.slbum",
        "border_style": style,
        "border_color": theme,
        "theme_color": theme,
    }


def _export(style, fmt):
    url = "/render-from-state" if fmt == "html" else "/export-from-state"
    r = TestClient(app).post(url, json=_state(style, fmt))
    assert r.status_code == 200, r.text
    return r.content


def _png(style):
    return Image.open(BytesIO(_export(style, "png"))).convert("L")


# ── The shared drawing ──


def test_dashes_are_cut_to_the_pattern():
    stroke = pb.Stroke([(0.0, 0.0), (10.0, 0.0)], 0.4, dash=(2.0, 1.0))
    dashes = pb.strokes_with_dashes([stroke])
    assert [(d.points[0][0], d.points[-1][0]) for d in dashes] == [
        pytest.approx((a, a + 2)) for a in (0, 3, 6)
    ] + [pytest.approx((9, 10))]


def test_every_style_draws_something_inside_the_page():
    for style in STYLES:
        prims = pb.primitives(style, PAGE_W, PAGE_H)
        assert prims, style
        pts = [p for prim in prims for p in prim.points]
        assert (
            min(x for x, _ in pts) >= 4.8 - 1e-6 and max(x for x, _ in pts) <= PAGE_W - 4.8 + 1e-6
        )
        assert (
            min(y for _, y in pts) >= 4.8 - 1e-6 and max(y for _, y in pts) <= PAGE_H - 4.8 + 1e-6
        )


def _editor_markup(page, style, theme="exhibition"):
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    page.evaluate("StampAlbum.newAlbum()")
    page.select_option("#def-theme", theme)
    page.select_option("#def-bdr", style)
    return page.evaluate(
        "(() => { const b = document.getElementById('page-border');"
        " const s = StampAlbum._sc;"
        " return {html: b.innerHTML, w: StampAlbum._pw / s, h: StampAlbum._ph / s}; })()"
    )


@pytest.mark.parametrize("style", STYLES)
def test_exports_draw_the_editors_border(page, style):
    """page_border.py builds the same picture as renderPageBorder in borders.js."""
    got = _editor_markup(page, style)
    editor = pb.markup_primitives(got["html"])
    ours = pb.primitives(style, got["w"], got["h"])
    assert [type(p).__name__ for p in editor] == [type(p).__name__ for p in ours]
    for e, o in zip(editor, ours):
        assert e.points == [pytest.approx(pt, abs=1e-3) for pt in o.points]
        if isinstance(e, pb.Stroke):
            assert (e.width, e.closed, e.dash) == (
                pytest.approx(o.width),
                o.closed,
                pytest.approx(o.dash),
            )


@pytest.mark.parametrize("style", ["greek_key", "rope"])
def test_edge_patterns_take_the_theme_colour_in_the_editor(page, style):
    got = _editor_markup(page, style, theme="green")
    colours = page.evaluate(
        "[...document.querySelectorAll('#page-border [stroke]')]"
        ".map(e => e.getAttribute('stroke').toUpperCase())"
    )
    assert colours and set(colours) == {"#2E5E3A"}, got["html"][:200]


# ── Every view draws the same picture ──


def _ink(img, threshold=160):
    return img.point(lambda v: 255 if v < threshold else 0)


def _preview_img(page, style):
    html = _export(style, "html").decode()
    pg = page.context.browser.new_page(
        viewport={"width": 900, "height": 1200}, device_scale_factor=2
    )
    try:
        pg.set_content(html)
        img = Image.open(BytesIO(pg.locator(".page").first.screenshot())).convert("L")
    finally:
        pg.close()
    return img


def _editor_img(base_url, page, style):
    pg = page.context.browser.new_page(
        viewport={"width": 1500, "height": 950}, device_scale_factor=3
    )
    try:
        pg.goto(base_url + "/")
        pg.wait_for_function("window.StampAlbum && document.getElementById('page')")
        _editor_markup(pg, style)
        pg.evaluate(
            "(() => { const p = document.getElementById('page'); p.style.background = '#fff';"
            " p.style.backgroundImage = 'none';"
            " p.querySelectorAll('.cel, .col-guide').forEach(n => n.remove()); })()"
        )
        return Image.open(BytesIO(pg.locator("#page-border").screenshot())).convert("L")
    finally:
        pg.close()


def _agreement(a, b, within_mm=0.4):
    """Share of a's ink that lies within *within_mm* of b's ink, at the PNG export's resolution."""
    size = (round(PAGE_W * PNG_PPM), round(PAGE_H * PNG_PPM))
    a, b = _ink(a.resize(size)), _ink(b.resize(size))
    reach = round(within_mm * PNG_PPM)
    near_b = b.filter(ImageFilter.MaxFilter(2 * reach + 1))
    a_px = sum(1 for v in a.getdata() if v)
    both = sum(1 for va, vb in zip(a.getdata(), near_b.getdata()) if va and vb)
    return both / max(1, a_px)


@pytest.mark.parametrize(
    "style", ["solid", "double", "dashed", "classic", "artdeco", "greek_key", "rope"]
)
def test_png_preview_and_editor_draw_the_same_border(base_url, page, style):
    png = _png(style)
    views = {"preview": _preview_img(page, style), "editor": _editor_img(base_url, page, style)}
    for name, img in views.items():
        # The editor's page can sit on a half pixel, so its lines may land a screen pixel over
        within = 0.6 if name == "editor" else 0.4
        assert _agreement(png, img, within) > 0.95, f"PNG ink missing from the {name}"
        assert _agreement(img, png, within) > 0.95, f"{name} ink missing from the PNG"


@pytest.mark.parametrize("style", STYLES)
def test_png_border_has_all_four_edges(style):
    img = _ink(_png(style))
    reach = 10.0  # mm from the page edge: the border and any edge pattern lie within it

    def has_ink(box_mm):
        x0, y0, x1, y1 = (round(v * PNG_PPM) for v in box_mm)
        return img.crop((x0, y0, x1, y1)).getbbox() is not None

    mid = (60.0, 150.0)  # well away from corner ornaments
    assert has_ink((mid[0], 4.0, mid[0] + 20, reach)), "top"
    assert has_ink((mid[0], PAGE_H - reach, mid[0] + 20, PAGE_H - 4.0)), "bottom"
    assert has_ink((4.0, mid[1], reach, mid[1] + 20)), "left"
    assert has_ink((PAGE_W - reach, mid[1], PAGE_W - 4.0, mid[1] + 20)), "right"


@pytest.mark.parametrize("style", ["dashed", "dotted"])
def test_png_dashed_borders_have_gaps(style):
    img = _png(style)
    y = round(4.8 * PNG_PPM)
    row = [
        min(img.getpixel((x, yy)) for yy in range(y - 2, y + 3))
        for x in range(round(20 * PNG_PPM), round(60 * PNG_PPM))
    ]
    changes = sum(1 for a, b in zip(row, row[1:]) if (a < 128) != (b < 128))
    assert changes >= 10, "a dashed border was drawn solid"


@pytest.mark.parametrize("style", ["greek_key", "rope"])
def test_png_edge_patterns_are_drawn_at_the_editors_size(style):
    """A Greek key repeats every 4.8 mm and is 1.2 mm deep; rope circles are 1.6 mm across."""
    img = _ink(_png(style))
    x0, x1 = round(20 * PNG_PPM), round(68 * PNG_PPM)  # 48 mm of the top edge
    band = img.crop((x0, round(4.0 * PNG_PPM), x1, round(8.0 * PNG_PPM)))
    left, top, right, bottom = band.getbbox()
    depth = (bottom - top) / PNG_PPM
    want = 1.2 + 0.32 if style == "greek_key" else 1.6 + 0.28  # plus the line's own width
    assert depth == pytest.approx(want, abs=0.25), f"pattern {depth:.2f} mm deep"


# ── PDF and SVG draw the shared primitives ──


@pytest.mark.parametrize("style", STYLES)
def test_pdf_draws_the_shared_border(monkeypatch, style):
    calls = []
    orig = rl_canvas.Canvas.drawPath
    monkeypatch.setattr(
        rl_canvas.Canvas,
        "drawPath",
        lambda self, path, *a, **k: (calls.append(k), orig(self, path, *a, **k))[1],
    )
    _export(style, "pdf")
    want = pb.strokes_with_dashes(pb.primitives(style, PAGE_W, PAGE_H))
    assert len(calls) == len(want)
    assert sum(1 for k in calls if k.get("fill")) == sum(1 for p in want if isinstance(p, pb.Fill))


@pytest.mark.parametrize("style", STYLES)
def test_svg_draws_the_shared_border(style):
    import xml.etree.ElementTree as ET

    root = ET.fromstring(_export(style, "svg"))
    group = next(
        g for g in root.iter("{http://www.w3.org/2000/svg}g") if g.get("class") == "page-border"
    )
    want = pb.strokes_with_dashes(pb.primitives(style, PAGE_W, PAGE_H))
    assert len(list(group)) == len(want)
    widths = sorted(
        {round(float(e.get("stroke-width")), 3) for e in group if e.get("stroke") != "none"}
    )
    assert widths == sorted({round(p.width, 3) for p in want if isinstance(p, pb.Stroke)})
