"""Stamp shapes and stamp labels must be drawn the same in every export."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas as rl_canvas

from stamp_album.api import app
from stamp_album.engines.borders import SHAPE_POLYGON_VIEWBOX, polygon_points

PT = 72.0 / 25.4
PAGE_W, PAGE_H = 210.0, 297.0
POLY_SHAPES = {"triangle": "TRIANGLE", "diamond": "DIAMOND", "hexagon": "HEXAGON",
               "octagon": "OCTAGON", "pentagon": "PENTAGON"}


def _state(shape, fmt, lbl="L"):
    el = {"t": "stamp", "s": shape, "x": 25, "y": 50, "w": 150, "h": 100, "lbl": lbl,
          "bdr": "solid", "bdrC": "#000000", "fill": "#ffffff"}
    return {"elements": [el], "pages": [], "page_width_px": PAGE_W * 2.5,
            "page_height_px": PAGE_H * 2.5, "scale": 2.5, "format": fmt, "source_path": "t"}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _box_mm():
    return 10.0, 20.0, 60.0, 40.0  # x, y, w, h in mm (canvas px / 2.5)


def test_polygon_points_parses_canonical_outline():
    pts = polygon_points("OCTAGON", 0, 0, 100, 100)
    assert pts[0] == (30.0, 0.0) and len(pts) == 8
    assert polygon_points("OVAL", 0, 0, 10, 10) == []
    assert set(POLY_SHAPES.values()) <= set(SHAPE_POLYGON_VIEWBOX)


@pytest.mark.parametrize("shape,name", POLY_SHAPES.items())
def test_pdf_polygon_matches_canonical(client, monkeypatch, shape, name):
    paths = []
    orig = rl_canvas.Canvas.drawPath

    def spy(self, path, *a, **k):
        paths.append(list(path._code))
        return orig(self, path, *a, **k)

    monkeypatch.setattr(rl_canvas.Canvas, "drawPath", spy)
    assert client.post("/export-from-state", json=_state(shape, "pdf")).status_code == 200
    code = next(p for p in paths if p)
    nums = [tuple(float(v) for v in line.split()[:2]) for line in code if line.split()[-1] in ("m", "l")]
    x, y, w, h = _box_mm()
    expected = [(px * PT, (PAGE_H - py) * PT) for px, py in polygon_points(name, x, y, w, h)]
    assert len(nums) == len(expected)
    for got, want in zip(nums, expected):
        assert got == pytest.approx(want, abs=0.05)


def test_pdf_triangle_apex_points_up(client, monkeypatch):
    paths = []
    orig = rl_canvas.Canvas.drawPath
    monkeypatch.setattr(rl_canvas.Canvas, "drawPath",
                        lambda self, path, *a, **k: (paths.append(list(path._code)), orig(self, path, *a, **k))[1])
    client.post("/export-from-state", json=_state("triangle", "pdf"))
    pts = [tuple(float(v) for v in line.split()[:2]) for line in paths[0] if line.split()[-1] in ("m", "l")]
    apex = pts[0]
    assert apex[1] > max(p[1] for p in pts[1:]), "apex must be the highest point on the page (PDF is y-up)"


@pytest.mark.parametrize("shape,name", POLY_SHAPES.items())
def test_png_polygon_matches_canonical(client, monkeypatch, shape, name):
    polys = []
    orig = ImageDraw.ImageDraw.polygon
    monkeypatch.setattr(ImageDraw.ImageDraw, "polygon",
                        lambda self, xy, *a, **k: (polys.append(list(xy)), orig(self, xy, *a, **k))[1])
    r = client.post("/export-from-state", json=_state(shape, "png"))
    assert r.status_code == 200
    px_per_mm = 200 / 25.4
    x, y, w, h = _box_mm()
    expected = [(px * px_per_mm, py * px_per_mm) for px, py in polygon_points(name, x, y, w, h)]
    got = polys[0]
    assert len(got) == len(expected)
    for g, e in zip(got, expected):
        assert g == pytest.approx(e, abs=1.0)


def test_svg_polygon_uses_canonical_points(client):
    svg = client.post("/export-from-state", json=_state("octagon", "svg")).text
    assert SHAPE_POLYGON_VIEWBOX["OCTAGON"] in svg


def test_png_stamp_label_has_readable_size(client):
    r = client.post("/export-from-state", json=_state("rectangle", "png", lbl="HHHH"))
    im = Image.open(io.BytesIO(r.content)).convert("L")
    bbox = im.crop((int(30 / 25.4 * 200), int(55 / 25.4 * 200), int(170 / 25.4 * 200),
                    int(145 / 25.4 * 200))).point(lambda v: 255 if v < 128 else 0).getbbox()
    assert bbox is not None
    cap_h_mm = (bbox[3] - bbox[1]) / (200 / 25.4)
    # default 12 pt * 0.9 capitals are ~2.7 mm; the old bug drew them ~0.6 mm
    assert cap_h_mm > 2.0, f"label capitals only {cap_h_mm:.2f} mm tall"


# ── PNG images keep their aspect ratio ──

def test_png_image_keeps_aspect_ratio(client, tmp_path, monkeypatch):
    from pathlib import Path
    images = tmp_path / "StampAlbum" / "images"
    images.mkdir(parents=True)
    Image.new("RGB", (60, 80), (200, 30, 30)).save(images / "tall.png")  # 3:4
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    state = _state("rectangle", "png", lbl="")
    state["elements"][0].update({"t": "image", "img": "tall.png", "bdr": "none", "fill": "transparent",
                                 "x": 50, "y": 50, "w": 200, "h": 200})  # square box
    r = client.post("/export-from-state", json=state)
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    r_, g_, b_ = im.split()
    # the image is (200, 30, 30); the stamp outline is black, so match on a strong red channel
    mask = Image.merge("L", [r_]).point(lambda v: 255 if v > 150 else 0)
    mask = Image.composite(mask, Image.new("L", im.size, 0), g_.point(lambda v: 255 if v < 100 else 0))
    bbox = mask.getbbox()
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    assert w / h == pytest.approx(0.75, abs=0.03), f"image drawn {w}x{h}, should keep 3:4"
