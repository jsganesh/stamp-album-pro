# ruff: noqa: F811
"""Stamp frames in the editor and the preview: drawn outside the stamp's own size,
with the size marked by a dashed line and given in Properties, and never clipped."""

import json
import urllib.request
from io import BytesIO

import pytest
from PIL import Image
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

SC = 2.5  # canvas px per mm
PT = 25.4 / 72
X, Y, W, H = 40.0, 60.0, 30.0, 40.0
FRAMES = {
    "thin": ("solid", 0.5),
    "medium": ("solid", 1),
    "double": ("double", 1),
    "none": ("none", 0),
}


def _stamp(i, x=X, y=Y, w=W, h=H, frame="thin", shape="rectangle", **kw):
    bdr, bdr_w = FRAMES[frame]
    el = {
        "id": f"s{i}",
        "t": "stamp",
        "s": shape,
        "x": x * SC,
        "y": y * SC,
        "w": w * SC,
        "h": h * SC,
        "bdr": bdr,
        "bdrC": "#000000",
        "bdrW": bdr_w,
        "fill": "#ffffff",
        "fillA": 100,
        "font": "HN",
        "fs": 12,
    }
    el.update(kw)
    return el


def _show(page, els, border="none", select=None):
    page.evaluate(
        """([els, border, sel]) => {
        StampAlbum.newAlbum();
        StampAlbum.E.length = 0;
        els.forEach(e => StampAlbum.E.push(e));
        StampAlbum._pageBorder = border;
        if (sel) StampAlbum.select(sel); else StampAlbum.render();
    }""",
        [els, border, select],
    )


def _boxes(page, sid):
    """Bounding boxes relative to the stamp's own box (canvas px)."""
    return page.evaluate(
        """sid => {
        const cel = document.querySelector('.cel[data-id="' + sid + '"]');
        const b = cel.getBoundingClientRect();
        const rel = n => {
            const r = n.getBoundingClientRect();
            return {l: r.left - b.left, t: r.top - b.top,
                    r: r.right - b.right, b: r.bottom - b.bottom};
        };
        return {lines: [...cel.querySelectorAll('.stamp-frame .frame-line')].map(rel),
                guide: [...cel.querySelectorAll('.stamp-frame .stamp-size-guide')].map(rel)};
    }""",
        sid,
    )


@pytest.mark.parametrize("frame", ["thin", "medium", "double"])
def test_editor_frame_is_drawn_outside_the_stamp(page, frame):
    _show(page, [_stamp(1, frame=frame)])
    boxes = _boxes(page, "s1")
    assert len(boxes["guide"]) == 1, "the stamp's own size is marked by a dashed line"
    g = boxes["guide"][0]
    assert max(abs(v) for v in g.values()) < 0.6  # ...at exactly the stored size
    assert len(boxes["lines"]) == (2 if frame == "double" else 1)
    for ln in boxes["lines"]:
        for side in ("l", "t"):
            assert ln[side] <= -0.5 * SC, (
                f"{frame}: frame line {side} not outside the 1 mm clearance"
            )
        for side in ("r", "b"):
            assert ln[side] >= 0.5 * SC
        assert ln["l"] >= -(1 + 2 * PT) * SC - 2  # and no further out than a double frame reaches


@pytest.mark.parametrize("shape", ["oval", "hexagon"])
def test_editor_shaped_stamps_have_the_frame_outside_too(page, shape):
    _show(page, [_stamp(1, shape=shape)])
    (ln,) = _boxes(page, "s1")["lines"]
    assert ln["l"] < -SC * 0.9 and ln["r"] > SC * 0.9


def test_properties_give_the_stamp_and_frame_sizes(page):
    _show(page, [_stamp(1)], select="s1")
    note = page.inner_text("#pframe-size")
    assert "Frame 32.4 × 42.4 mm" in note
    assert "1 mm clear all round" in note and "30 × 40 mm" in note
    assert (
        page.input_value("#pw") == "30" or float(page.input_value("#pw")) == 30
    )  # W is the stamp's own width
    page.select_option("#pbs", "double")
    assert "Frame 33.4 × 43.4 mm" in page.inner_text("#pframe-size")
    page.select_option("#pbs", "none")
    assert page.inner_text("#pframe-size").startswith("No frame")


def _warning(page, sid):
    return page.evaluate(
        f"""(() => {{ const n = document.querySelector('.cel[data-id="{sid}"]');
        return n.classList.contains('caption-warn')
            ? n.getAttribute('aria-description') : null; }})()"""
    )


def test_frame_past_the_page_edge_is_flagged(page):
    _show(page, [_stamp(1, x=0.5, y=100)])  # stamp inside the page, its frame 0.7 mm past the edge
    assert _warning(page, "s1") == "The frame runs past the page edge"
    _show(page, [_stamp(1, x=1.5, y=100)])
    assert _warning(page, "s1") is None


def test_frames_running_into_each_other_are_flagged(page):
    # 1.5 mm apart: the stamps are clear, their frames (1.18 mm each) overlap
    _show(page, [_stamp(1, x=40), _stamp(2, x=40 + W + 1.5)])
    assert _warning(page, "s1") == "The frame runs into another item"
    _show(page, [_stamp(1, x=40), _stamp(2, x=40 + W + 3)])
    assert _warning(page, "s1") is None and _warning(page, "s2") is None


# ── The preview: sampled pixels ──


def _preview_png(base_url, page, els):
    state = {
        "elements": els,
        "pages": [],
        "page_width_px": 210 * SC,
        "page_height_px": 297 * SC,
        "scale": SC,
        "format": "html",
        "source_path": "t.slbum",
    }
    req = urllib.request.Request(
        base_url + "/render-from-state",
        data=json.dumps(state).encode(),
        headers={"Content-Type": "application/json"},
    )
    html = urllib.request.urlopen(req).read().decode()
    pg = page.context.browser.new_page(
        viewport={"width": 900, "height": 1200}, device_scale_factor=3
    )
    try:
        pg.set_content(html)
        r = pg.evaluate(
            "(() => { const b = document.querySelector('.page').getBoundingClientRect();"
            " return [b.left, b.top, b.width]; })()"
        )
        img = Image.open(BytesIO(pg.screenshot(full_page=True))).convert("L")
    finally:
        pg.close()
    ppm = r[2] / 210 * 3  # device px per mm
    return img, (r[0] * 3, r[1] * 3), ppm


@pytest.mark.parametrize("frame", ["thin", "double"])
def test_preview_frame_is_outside_the_stamp_and_not_clipped(base_url, page, frame):
    img, (ox, oy), ppm = _preview_png(base_url, page, [_stamp(1, frame=frame)])
    mid_x, mid_y = int(ox + (X + W / 2) * ppm), int(oy + (Y + H / 2) * ppm)

    def ink(a_mm, b_mm, horizontal):
        if horizontal:
            vals = [
                img.getpixel((int(ox + v / 10 * ppm), mid_y))
                for v in range(int(a_mm * 10), int(b_mm * 10))
            ]
        else:
            vals = [
                img.getpixel((mid_x, int(oy + v / 10 * ppm)))
                for v in range(int(a_mm * 10), int(b_mm * 10))
            ]
        return min(vals)

    reach = 1 + 2 * PT + 0.3
    for side, (a, b, horiz) in {
        "left": (X - reach, X - 0.9, True),
        "right": (X + W + 0.9, X + W + reach, True),
        "top": (Y - reach, Y - 0.9, False),
        "bottom": (Y + H + 0.9, Y + H + reach, False),
    }.items():
        assert ink(a, b, horiz) < 160, f"{side} frame line missing (clipped?)"
    # the 1 mm between the stamp and its frame stays clear
    for a, b, horiz in (
        (X - 0.8, X - 0.1, True),
        (X + W + 0.1, X + W + 0.8, True),
        (Y + H + 0.1, Y + H + 0.8, False),
    ):
        assert ink(a, b, horiz) > 230
