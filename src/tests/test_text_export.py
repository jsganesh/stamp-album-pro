"""Free-form text elements must wrap, align and size the same in every export."""
import io
import re

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from reportlab.pdfgen import canvas as rl_canvas

from stamp_album.api import app
from stamp_album.engines import text_layout

PAGE_W_MM, PAGE_H_MM = 210.0, 297.0
PT = 72.0 / 25.4
LONG = "This is a long descriptive paragraph that must wrap inside its box and not run off the page edge at all."


def _el(**kw):
    base = dict(t="text", x=0, y=0, w=100, h=50, lbl="", font="HN", fs=12, align="left")
    base.update(kw)
    return base


def _state(elements, fmt):
    return {"elements": elements, "pages": [], "page_width_px": PAGE_W_MM * 2.5,
            "page_height_px": PAGE_H_MM * 2.5, "scale": 2.5, "format": fmt,
            "source_path": "t.slbum"}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _px(mm):
    return mm * 2.5


# ── shared layout ──

def test_wrap_lines_breaks_at_width():
    lines = text_layout.wrap_lines("aaa bbb ccc", 7, lambda s: len(s))
    assert lines == ["aaa bbb", "ccc"]


def test_wrap_lines_splits_overlong_word():
    lines = text_layout.wrap_lines("abcdefghij", 4, lambda s: len(s))
    assert all(len(line) <= 4 for line in lines) and "".join(lines) == "abcdefghij"


def test_wrap_lines_keeps_newlines():
    assert text_layout.wrap_lines("a\n\nb", 10, lambda s: len(s)) == ["a", "", "b"]


@pytest.mark.parametrize("align,expected", [("left", 11.0), ("center", 30.0), ("right", 49.0)])
def test_line_x(align, expected):
    assert text_layout.line_x(10, 60, 20, align, 1) == pytest.approx(expected)


# ── PDF: record what is drawn ──

@pytest.fixture()
def drawn(monkeypatch):
    calls = []
    orig = rl_canvas.Canvas.drawString

    def spy(self, x, y, text, *a, **k):
        calls.append((x, y, text, self._fontsize))
        return orig(self, x, y, text, *a, **k)

    monkeypatch.setattr(rl_canvas.Canvas, "drawString", spy)
    return calls


def _pdf(client, elements):
    r = client.post("/export-from-state", json=_state(elements, "pdf"))
    assert r.status_code == 200
    return r.content


def test_pdf_heading_is_centered_and_inside_page(client, drawn):
    _pdf(client, [_el(x=_px(10), y=_px(8), w=_px(190), h=_px(18), fs=40, align="center", lbl="Bahrain")])
    x, y, text, size = next(c for c in drawn if c[2] == "Bahrain")
    from reportlab.pdfbase.pdfmetrics import stringWidth
    tw = stringWidth("Bahrain", "Helvetica", size)
    page_h = PAGE_H_MM * PT
    box_center = (10 + 95) * PT
    assert abs((x + tw / 2) - box_center) < 25
    # the baseline is below the top of the page: text must not be clipped
    assert page_h - y > size * 0.7


def test_pdf_paragraph_wraps_inside_box(client, drawn):
    _pdf(client, [_el(x=_px(10), y=_px(30), w=_px(80), h=_px(22), fs=11, lbl=LONG)])
    lines = [c for c in drawn if c[2] in LONG]
    assert len(lines) >= 3, "paragraph should wrap into several lines"
    from reportlab.pdfbase.pdfmetrics import stringWidth
    for x, y, text, size in lines:
        assert x + stringWidth(text, "Helvetica", size) <= (10 + 80) * PT + 1
    ys = [c[1] for c in lines]
    assert ys == sorted(ys, reverse=True), "lines go downwards"


def test_pdf_right_align(client, drawn):
    _pdf(client, [_el(x=_px(100), y=_px(30), w=_px(100), h=_px(10), fs=14, align="right", lbl="Right")])
    x, y, text, size = next(c for c in drawn if c[2] == "Right")
    from reportlab.pdfbase.pdfmetrics import stringWidth
    right_edge = x + stringWidth("Right", "Helvetica", size)
    assert abs(right_edge - (200 - text_layout.PAD_MM) * PT) < 6


# ── SVG ──

def test_svg_text_wraps_aligns_and_uses_mm_font_size(client):
    r = client.post("/export-from-state", json=_state(
        [_el(x=_px(100), y=_px(30), w=_px(100), h=_px(10), fs=14, align="right", lbl="Right"),
         _el(x=_px(10), y=_px(60), w=_px(80), h=_px(22), fs=11, lbl=LONG)], "svg"))
    svg = r.text
    assert 'text-anchor="end"' in svg
    sizes = {float(m) for m in re.findall(r'font-size="([\d.]+)"', svg)}
    assert all(s < 10 for s in sizes), f"font sizes should be mm-scale, got {sizes}"
    assert svg.count("<text") >= 4


# ── PNG ──

def _ink_bbox(png_bytes):
    im = Image.open(io.BytesIO(png_bytes)).convert("L")
    return im.point(lambda v: 255 if v < 160 else 0).getbbox(), im.size


def test_png_text_scales_with_resolution(client):
    r = client.post("/export-from-state", json=_state(
        [_el(x=_px(10), y=_px(10), w=_px(190), h=_px(30), fs=40, align="left", lbl="Bahrain")], "png"))
    bbox, (w, h) = _ink_bbox(r.content)
    assert bbox is not None
    ink_h_mm = (bbox[3] - bbox[1]) / (w / PAGE_W_MM)
    # 40 pt capitals + descenders ~ 10-14 mm tall; the old bug drew ~1.5 mm
    assert ink_h_mm > 7, f"text far too small ({ink_h_mm:.1f} mm)"


def test_png_text_centered(client):
    r = client.post("/export-from-state", json=_state(
        [_el(x=_px(10), y=_px(10), w=_px(190), h=_px(30), fs=40, align="center", lbl="Bahrain")], "png"))
    bbox, (w, h) = _ink_bbox(r.content)
    center_mm = ((bbox[0] + bbox[2]) / 2) / (w / PAGE_W_MM)
    assert abs(center_mm - 105) < 6


# ── HTML preview ──

def test_preview_honours_alignment(client):
    r = client.post("/render-from-state", json=_state(
        [_el(x=_px(10), y=_px(10), w=_px(190), h=_px(20), fs=20, align="center", lbl="Bahrain")], "html"))
    assert "text-align:center" in r.text.replace(" ", "")
