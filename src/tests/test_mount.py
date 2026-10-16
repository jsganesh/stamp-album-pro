"""Stamp mounts (owner's decisions 2026-10-16): the album's mount overhang plus its gap to the
frame sets how far out every stamp's frame is drawn, the same in every view. New albums start
at 1.5 + 1 mm; an album that doesn't say (every album before this) is 0 + 1 mm, as before.
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
from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.engines import frames
from stamp_album.templates import TEMPLATES

CORE = Path(__file__).resolve().parents[1] / "stamp_album" / "web" / "dsl_core.js"
SC = 2.5
X, Y, W, H = 40.0, 60.0, 25.0, 30.0
STAMP = ('STAMP_ADD_AT({x} {y} {w} {h} "Penny Black" "" "" "" rectangle "solid" "#000000" 0.5 '
         '"#ffffff" 100)').format(x=X, y=Y, w=W, h=H)


def _album(head=""):
    return AlbumParser().parse(f"{head}ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n{STAMP}\n", "t.slbum")


def _stamp(album):
    return album.pages[0].absolute_stamps[0]


# ── The file ──


def test_an_album_that_does_not_say_keeps_1mm():
    a = _album()
    assert (a.mount_overhang, a.mount_gap) == (0.0, 1.0)
    assert frames.clearance(_stamp(a)) == pytest.approx(1.0)


def test_album_mount_sets_every_frame():
    a = _album("ALBUM_MOUNT(1.5 1)\n")
    assert (a.mount_overhang, a.mount_gap) == (1.5, 1.0)
    assert frames.clearance(_stamp(a)) == pytest.approx(2.5)
    x, y, w, h = frames.outer_box(_stamp(a), X, Y, W, H)
    o = 2.5 + 0.5 * 25.4 / 72  # the clearance, then a thin line
    assert (x, y, w, h) == pytest.approx((X - o, Y - o, W + 2 * o, H + 2 * o))


@pytest.mark.parametrize("line", ["ALBUM_MOUNT(-1 1)", "ALBUM_MOUNT(1 0)", "ALBUM_MOUNT(1)",
                                  "ALBUM_MOUNT(2 50)"])
def test_an_impossible_mount_is_ignored(line):
    a = _album(line + "\n")
    assert (a.mount_overhang, a.mount_gap) == (0.0, 1.0)


@pytest.mark.parametrize("mount", [(0.0, 1.0), (1.5, 1.0), (3.0, 2.5)])
def test_the_mount_is_saved_and_read_back(mount):
    a = _album("ALBUM_MOUNT({} {})\n".format(*mount))
    text = AlbumSerializer().to_dsl(a)
    assert re.search(r"^ALBUM_MOUNT\(([\d.]+) ([\d.]+)\)$", text, re.M).groups() == tuple(
        f"{v:g}" for v in mount)
    b = AlbumParser().parse(text, "t.slbum")
    assert (b.mount_overhang, b.mount_gap) == mount


def test_new_albums_from_templates_start_at_1_5_plus_1():
    for t in TEMPLATES:
        a = AlbumParser().parse(t["content"], t["id"] + ".slbum")
        assert (a.mount_overhang, a.mount_gap) == frames.NEW_ALBUM_MOUNT, t["id"]


def test_choices_match_the_editor():
    js = json.loads(subprocess.run(
        [shutil.which("node"), "-e",
         f"const c = require({json.dumps(str(CORE))}); console.log(JSON.stringify(["
         "c.MOUNT_OVERHANG_CHOICES, c.MOUNT_GAP_CHOICES, c.NEW_ALBUM_MOUNT, c.OLD_ALBUM_MOUNT]))"],
        capture_output=True, text=True, encoding="utf-8", check=True).stdout)
    assert js[0] == list(frames.MOUNT_OVERHANG_CHOICES)
    assert js[1] == list(frames.MOUNT_GAP_CHOICES)
    assert (js[2]["overhang"], js[2]["gap"]) == frames.NEW_ALBUM_MOUNT
    assert (js[3]["overhang"], js[3]["gap"]) == frames.OLD_ALBUM_MOUNT


@pytest.mark.parametrize("mount", [(0, 1), (1.5, 1), (3, 3)])
@pytest.mark.parametrize("frame,bdr,bdr_w", [("thin", "solid", 0.5), ("medium", "solid", 1.0),
                                             ("double", "double", 0.5)])
def test_frame_lines_match_the_editor(mount, frame, bdr, bdr_w):
    el = {"t": "stamp", "bdr": bdr, "bdrW": bdr_w}
    js = json.loads(subprocess.run(
        [shutil.which("node"), "-e",
         f"const c = require({json.dumps(str(CORE))}); c.setMount({mount[0]}, {mount[1]});"
         f"console.log(JSON.stringify(c.frameLines({json.dumps(el)})))"],
        capture_output=True, text=True, encoding="utf-8", check=True).stdout)
    a = _album("ALBUM_MOUNT({} {})\n".format(*mount))
    s = _stamp(a)
    s.frame = frame
    py = frames.lines(s)
    assert [(j["offset"], j["width"]) for j in js] == [
        pytest.approx((p.offset, p.width)) for p in py]


# ── Every export ──


def _state(fmt, **mount):
    el = {"t": "stamp", "s": "rectangle", "x": X * SC, "y": Y * SC, "w": W * SC, "h": H * SC,
          "bdr": "solid", "bdrC": "#000000", "bdrW": 0.5, "fill": "#ffffff", "fillA": 100}
    state = {"elements": [el], "pages": [], "page_width_px": 210 * SC,
             "page_height_px": 297 * SC, "scale": SC, "format": fmt, "source_path": "t.slbum"}
    state.update(mount)
    return state


def _export(fmt, **mount):
    url = "/render-from-state" if fmt == "html" else "/export-from-state"
    r = TestClient(app).post(url, json=_state(fmt, **mount))
    assert r.status_code == 200, r.text
    return r.content


def _svg_frame_x(**mount):
    root = ET.fromstring(_export("svg", **mount))
    line = next(e for e in root.iter() if e.get("class") == "frame-line")
    return X - float(line.get("x"))  # the line's centre, out from the stamp's left edge


def test_svg_frames_follow_the_mount():
    half = 0.25 * 25.4 / 72
    assert _svg_frame_x() == pytest.approx(1 + half, abs=1e-3)  # a request without one: as before
    assert _svg_frame_x(mount_overhang=1.5, mount_gap=1) == pytest.approx(2.5 + half, abs=1e-3)
    assert _svg_frame_x(mount_overhang=3, mount_gap=2) == pytest.approx(5 + half, abs=1e-3)


def test_an_impossible_mount_in_a_request_is_drawn_as_before():
    half = 0.25 * 25.4 / 72
    assert _svg_frame_x(mount_overhang=-2, mount_gap=1) == pytest.approx(1 + half, abs=1e-3)


def test_pdf_frames_follow_the_mount(monkeypatch):
    from reportlab.pdfgen import canvas

    rects, orig = [], canvas.Canvas.rect

    def rect(self, x, y, w, h, *a, **k):
        rects.append((x, w))
        return orig(self, x, y, w, h, *a, **k)

    monkeypatch.setattr(canvas.Canvas, "rect", rect)
    _export("pdf", mount_overhang=1.5, mount_gap=1)
    pt = 72 / 25.4
    want = (W + 2 * (2.5 + 0.25 * 25.4 / 72)) * pt
    assert any(abs(w - want) < 0.05 for _x, w in rects), (want, rects)


def test_png_frames_follow_the_mount():
    def first_dark_column(**mount):
        img = Image.open(BytesIO(_export("png", **mount))).convert("L")
        ppm = img.width / 210
        row = int((Y + H / 2) * ppm)
        for x in range(int((X - 8) * ppm), int(X * ppm)):
            if img.getpixel((x, row)) < 128:
                return X - x / ppm  # mm out from the stamp's left edge
        return None

    old, new = first_dark_column(), first_dark_column(mount_overhang=1.5, mount_gap=1)
    assert old == pytest.approx(1.2, abs=0.35)
    assert new - old == pytest.approx(1.5, abs=0.35)


def test_preview_frames_follow_the_mount():
    def frame_left(**mount):
        html = _export("html", **mount).decode()
        tag = re.search(r'<rect[^>]*class="frame-line"[^>]*>', html)
        assert tag, "no frame line in the preview"
        return float(re.search(r'\bx="([-\d.]+)"', tag.group(0)).group(1))

    assert frame_left() - frame_left(mount_overhang=1.5, mount_gap=1) == pytest.approx(1.5,
                                                                                         abs=1e-3)
