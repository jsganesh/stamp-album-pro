"""Stamp frames: drawn outside the stamp's own size, the same in every view.

A stamp's width and height are its size from the catalogue. The frame leaves 1 mm clear
all round, then draws its line or lines: thin 0.5 pt, medium 1 pt, double two 0.5 pt lines
1 pt apart. Stamps are framed in black.
"""

import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from reportlab.pdfgen import canvas as rl_canvas

from stamp_album.api import app
from stamp_album.core.models import Stamp, StampShape
from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.engines import frames

PT = 25.4 / 72  # mm per point
SC = 2.5  # canvas px per mm in a request
X, Y, W, H = 40.0, 60.0, 30.0, 40.0  # the stamp's own size, mm
FRAMES = {
    "thin": ("solid", 0.5),
    "medium": ("solid", 1),
    "double": ("double", 1),
    "none": ("none", 0),
}
SHAPES = ["rectangle", "oval", "triangle", "diamond", "hexagon", "octagon", "pentagon"]


def _stamp(frame="thin", shape=StampShape.RECTANGLE, freehand=False):
    s = Stamp(width=W, height=H, abs_x=X, abs_y=Y, shape=shape)
    s.frame = frame
    s.is_freehand = freehand
    return s


def _el(frame="thin", shape="rectangle", **kw):
    bdr, bdr_w = FRAMES[frame]
    el = {
        "t": "stamp",
        "s": shape,
        "x": X * SC,
        "y": Y * SC,
        "w": W * SC,
        "h": H * SC,
        "bdr": bdr,
        "bdrC": "#000000",
        "bdrW": bdr_w,
        "fill": "#ffffff",
        "fillA": 100,
    }
    el.update(kw)
    return el


def _export(fmt, els):
    state = {
        "elements": els,
        "pages": [],
        "page_width_px": 210 * SC,
        "page_height_px": 297 * SC,
        "scale": SC,
        "format": fmt,
        "source_path": "t.slbum",
    }
    r = TestClient(app).post("/export-from-state", json=state)
    assert r.status_code == 200, r.text
    return r.content


# ── The shared geometry ──


def test_thin_medium_and_double_frames_leave_1mm_clear():
    thin, medium, double = (frames.lines(_stamp(f)) for f in ("thin", "medium", "double"))
    assert [(ln.offset - ln.width / 2, ln.width) for ln in thin] == [pytest.approx((1.0, 0.5 * PT))]
    assert [(ln.offset - ln.width / 2, ln.width) for ln in medium] == [
        pytest.approx((1.0, 1.0 * PT))
    ]
    inner, outer = double
    assert inner.offset - inner.width / 2 == pytest.approx(1.0)  # 1 mm clear to the inner line
    assert (outer.offset - outer.width / 2) - (inner.offset + inner.width / 2) == pytest.approx(
        1.0 * PT
    )
    assert frames.outset(_stamp("thin")) == pytest.approx(1 + 0.5 * PT)
    assert frames.outset(_stamp("double")) == pytest.approx(1 + 2 * PT)
    assert frames.lines(_stamp("none")) == [] and frames.outset(_stamp("none")) == 0


def test_a_free_shape_is_its_own_frame():
    (ln,) = frames.lines(_stamp("thin", freehand=True))
    assert ln.offset - ln.width / 2 == pytest.approx(0.0)  # no clearance


@pytest.mark.parametrize("shape", ["TRIANGLE", "DIAMOND", "HEXAGON", "PENTAGON"])
def test_polygon_frames_keep_the_clearance_on_every_side(shape):
    import math

    pts = frames.outline(shape, X, Y, W, H)[1]
    out = frames.outline(shape, X, Y, W, H, 1.0)[1]
    n = len(pts)
    for i in range(n):  # each side of the frame is 1 mm out from the same side of the stamp
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        for px, py in (out[i], out[(i + 1) % n]):
            dist = abs((by - ay) * px - (bx - ax) * py + bx * ay - by * ax) / math.hypot(
                bx - ax, by - ay
            )
            assert dist == pytest.approx(1.0), (shape, i)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_editor_frame_geometry_matches_the_exports():
    """web/dsl_core.js frameLines / shapeOutline give the same geometry as frames.py."""
    core = Path(__file__).resolve().parents[1] / "stamp_album" / "web" / "dsl_core.js"
    cases = [(f, s) for f in FRAMES for s in SHAPES]
    script = (
        f"const c = require({json.dumps(str(core))});"
        f"const cases = {json.dumps(cases)};"
        "console.log(JSON.stringify(cases.map(([f, s]) => {"
        f"  const bdr = {json.dumps({k: v[0] for k, v in FRAMES.items()})}[f];"
        f"  const bdrW = {json.dumps({k: v[1] for k, v in FRAMES.items()})}[f];"
        "  const el = {t: 'stamp', s: s, bdr: bdr, bdrW: bdrW};"
        "  const ls = c.frameLines(el);"
        f"  const o = c.shapeOutline(s, {X}, {Y}, {W}, {H}, 1.3);"
        "  return {lines: ls, outset: c.frameOutset(el), outline: o};"
        "})));"
    )
    out = subprocess.run(
        [shutil.which("node"), "-e", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    for (frame, shape), js in zip(cases, json.loads(out)):
        st = _stamp(frame, StampShape(shape) if shape != "rectangle" else StampShape.RECTANGLE)
        assert [(j["offset"], j["width"]) for j in js["lines"]] == [
            pytest.approx((ln.offset, ln.width)) for ln in frames.lines(st)
        ], (frame, shape)
        assert js["outset"] == pytest.approx(frames.outset(st))
        kind, geom = frames.outline(st.shape.name, X, Y, W, H, 1.3)
        assert js["outline"]["kind"] == kind
        if kind == "polygon":
            assert [tuple(p) for p in js["outline"]["points"]] == [pytest.approx(p) for p in geom]
        elif kind == "ellipse":
            o = js["outline"]
            assert (o["cx"], o["cy"], o["rx"], o["ry"]) == pytest.approx(geom)
        else:
            o = js["outline"]
            assert (o["x"], o["y"], o["w"], o["h"]) == pytest.approx(geom)


# ── The album file keeps the frame ──


@pytest.mark.parametrize("frame", list(FRAMES))
def test_parser_and_serializer_keep_the_frame(frame):
    bdr, bdr_w = FRAMES[frame]
    dsl = (
        "ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n"
        f'STAMP_ADD_AT(40 60 30 40 "Plate 1a" "SG 2" "" "" rectangle '
        f'"{bdr}" "#000000" {bdr_w} "#ffffff" 100)\n'
    )
    album = AlbumParser().parse(dsl)
    assert album.pages[0].absolute_stamps[0].frame == frame
    again = AlbumParser().parse(AlbumSerializer().to_dsl(album))
    assert again.pages[0].absolute_stamps[0].frame == frame


def test_older_files_without_frame_fields_get_a_thin_frame():
    album = AlbumParser().parse(
        'ALBUM_PAGES_SIZE(210 297)\nPAGE_START\nSTAMP_ADD_AT(40 60 30 40 "x" "" "" "")\n'
    )
    stamp = album.pages[0].absolute_stamps[0]
    assert (stamp.frame, stamp.width, stamp.height) == (
        "thin",
        30,
        40,
    )  # stored size is the stamp's


# ── PNG: sampled pixels ──


def _dark_runs(values, threshold=128):
    """[(start, end)] index ranges of dark pixels."""
    runs, start = [], None
    for i, v in enumerate(values + [255]):
        if v < threshold and start is None:
            start = i
        elif v >= threshold and start is not None:
            runs.append((start, i))
            start = None
    return runs


@pytest.mark.parametrize("frame", ["thin", "medium", "double", "none"])
def test_png_frame_is_outside_the_stamp_on_all_four_sides(frame):
    img = Image.open(BytesIO(_export("png", [_el(frame)]))).convert("L")
    ppm = img.width / 210
    mid_y, mid_x = int((Y + H / 2) * ppm), int((X + W / 2) * ppm)
    row = [img.getpixel((i, mid_y)) for i in range(img.width)]
    col = [img.getpixel((mid_x, j)) for j in range(img.height)]
    sides = {
        "left": [(row, X - 3, X)],
        "right": [(row, X + W, X + W + 3)],
        "top": [(col, Y - 3, Y)],
        "bottom": [(col, Y + H, Y + H + 3)],
    }
    widths = {}
    for side, [(line, a, b)] in sides.items():
        lo, hi = int(a * ppm), int(b * ppm)
        runs = [(s + lo, e + lo) for s, e in _dark_runs(line[lo:hi])]
        if frame == "none":
            assert runs == [], side
            continue
        assert len(runs) == (2 if frame == "double" else 1), (side, runs)
        edge = X if side == "left" else X + W if side == "right" else Y if side == "top" else Y + H
        for s, e in runs:  # each line lies between 1 mm and 1 mm + 2 pt from the stamp edge
            near = min(abs(s / ppm - edge), abs(e / ppm - edge))
            far = max(abs(s / ppm - edge), abs(e / ppm - edge))
            assert near >= 1.0 - 1.5 / ppm and far <= 1.0 + 2 * PT + 1.5 / ppm, (
                side,
                s / ppm,
                e / ppm,
            )
        widths[side] = max(e - s for s, e in runs)
    if frame != "none":
        assert len(set(widths.values())) == 1, f"all four sides drawn alike: {widths}"


def test_png_medium_frame_is_heavier_than_thin():
    def width(frame):
        img = Image.open(BytesIO(_export("png", [_el(frame)]))).convert("L")
        ppm = img.width / 210
        mid_y = int((Y + H / 2) * ppm)
        row = [img.getpixel((i, mid_y)) for i in range(int((X - 3) * ppm), int(X * ppm))]
        return sum(1 for v in row if v < 128)

    assert width("medium") > width("thin") > 0


# ── PDF: drawing calls ──


def _pdf_frame_strokes(monkeypatch, el):
    strokes, width = [], [None]
    orig_w, orig_rect = rl_canvas.Canvas.setLineWidth, rl_canvas.Canvas.rect

    def set_w(self, w):
        width[0] = w
        return orig_w(self, w)

    def rect(self, x, y, w, h, stroke=1, fill=0):
        if stroke:
            strokes.append((width[0], x / 72 * 25.4, y / 72 * 25.4, w / 72 * 25.4, h / 72 * 25.4))
        return orig_rect(self, x, y, w, h, stroke=stroke, fill=fill)

    monkeypatch.setattr(rl_canvas.Canvas, "setLineWidth", set_w)
    monkeypatch.setattr(rl_canvas.Canvas, "rect", rect)
    _export("pdf", [el])
    return strokes


@pytest.mark.parametrize("frame", ["thin", "medium", "double"])
def test_pdf_frame_widths_and_position(monkeypatch, frame):
    strokes = _pdf_frame_strokes(monkeypatch, _el(frame))
    want = frames.lines(_stamp(frame))
    assert len(strokes) == len(want)
    for (lw, x, y_up, w, h), ln in zip(strokes, want):
        assert lw == pytest.approx(ln.width / PT)  # points
        assert x == pytest.approx(X - ln.offset, abs=1e-3)
        assert w == pytest.approx(W + 2 * ln.offset, abs=1e-3)
        assert y_up == pytest.approx(297 - (Y + H + ln.offset), abs=1e-3)  # PDF is y-up
        assert h == pytest.approx(H + 2 * ln.offset, abs=1e-3)


def test_pdf_no_frame_draws_no_line(monkeypatch):
    assert _pdf_frame_strokes(monkeypatch, _el("none")) == []


# ── SVG: elements ──


@pytest.mark.parametrize("frame", ["thin", "medium", "double", "none"])
def test_svg_frame_lines(frame):
    root = ET.fromstring(_export("svg", [_el(frame)]))
    ns = "{http://www.w3.org/2000/svg}"
    lines = [e for e in root.iter() if e.get("class") == "frame-line"]
    fill = next(e for e in root.iter(ns + "rect") if e.get("class") == "stamp-fill")
    assert (float(fill.get("x")), float(fill.get("width"))) == pytest.approx(
        (X, W)
    )  # the stamp's own size
    want = frames.lines(_stamp(frame))
    assert len(lines) == len(want)
    for e, ln in zip(lines, want):
        assert e.get("stroke") == "#000000"
        assert float(e.get("stroke-width")) == pytest.approx(ln.width, abs=1e-3)  # mm, not 0.3
        assert float(e.get("x")) == pytest.approx(X - ln.offset, abs=1e-3)
        assert float(e.get("height")) == pytest.approx(H + 2 * ln.offset, abs=1e-3)
