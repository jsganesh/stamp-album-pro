# ruff: noqa: F811
"""Stamp captions on the editor canvas: drawn where they print, with a warning when
they run into another item or past the page border."""

import pytest
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

SC = 2.5  # canvas px per mm
OUT = 1.0 + 0.5 * 25.4 / 72  # a thin frame's outer edge: 1 mm clear, then a 0.5 pt line
FULL = {
    "hdg": "Penny Black",
    "lbl": "Plate 1a",
    "denom": "1d",
    "cond": "Used",
    "perf": "Imperforate",
    "cat": "SG 2",
}


def _stamp(i, x, y, w=40, h=30, shape="rectangle", **kw):
    el = {
        "id": f"s{i}",
        "t": "stamp",
        "s": shape,
        "x": x * SC,
        "y": y * SC,
        "w": w * SC,
        "h": h * SC,
        "bdr": "solid",
        "bdrC": "#000000",
        "bdrW": 0.5,
        "fill": "#ffffff",
        "fillA": 100,
        "font": "HN",
        "fs": 12,
    }
    el.update(kw)
    return el


def _show(page, els, border="none"):
    page.evaluate(
        """([els, border]) => {
        StampAlbum.newAlbum();
        StampAlbum.E.length = 0;
        els.forEach(e => StampAlbum.E.push(e));
        StampAlbum._pageBorder = border;
        StampAlbum.render();
    }""",
        [els, border],
    )


def _captions(page, sid):
    """Each caption's box relative to the stamp box, in canvas px, plus its computed style."""
    return page.evaluate(
        """sid => {
        const cel = document.querySelector('.cel[data-id="' + sid + '"]');
        const b = cel.getBoundingClientRect();
        return [...cel.querySelectorAll('.caption')].map(n => {
            const r = n.getBoundingClientRect(), cs = getComputedStyle(n);
            return {kind: [...n.classList].find(c => c.startsWith('caption-')).slice(8),
                    text: n.textContent, top: r.top - b.top, bottom: r.bottom - b.top,
                    boxH: b.height, weight: cs.fontWeight, style: cs.fontStyle,
                    color: cs.color, size: parseFloat(cs.fontSize)};
        });
    }""",
        sid,
    )


@pytest.mark.parametrize("shape", ["rectangle", "oval"])
def test_captions_are_drawn_where_they_print(page, shape):
    _show(page, [_stamp(1, 40, 60, shape=shape, **FULL)])
    caps = {c["kind"]: c for c in _captions(page, "s1")}
    assert list(caps) == ["heading", "description", "details", "catalogue"]
    gap = (2 + OUT) * SC  # 2 mm from the frame, which is outside the stamp
    assert caps["heading"]["bottom"] == pytest.approx(-gap, abs=1)
    box_h = caps["heading"]["boxH"]
    assert caps["description"]["top"] == pytest.approx(box_h + gap, abs=1)
    assert caps["details"]["top"] == pytest.approx(caps["description"]["bottom"], abs=0.5)
    assert caps["catalogue"]["top"] == pytest.approx(caps["details"]["bottom"], abs=0.5)
    assert caps["details"]["text"] == "1d · Used · Imperforate"
    assert caps["heading"]["weight"] in ("700", "bold")
    assert caps["details"]["style"] == "italic" and caps["catalogue"]["style"] == "italic"
    assert caps["description"]["style"] == "normal" and caps["description"]["weight"] in (
        "400",
        "normal",
    )
    assert {c["color"] for c in caps.values()} == {"rgb(0, 0, 0)"}
    pt = 25.4 / 72 * SC
    assert caps["heading"]["size"] == pytest.approx(9 * pt, abs=0.05)
    assert caps["description"]["size"] == pytest.approx(8 * pt, abs=0.05)
    assert (
        page.locator('.cel[data-id="s1"] .stamp-inner .elbl').count() == 0
    )  # nothing inside the box


def test_description_is_edited_below_the_box(page):
    _show(page, [_stamp(1, 40, 60, lbl="Old")])
    desc = page.locator('.cel[data-id="s1"] .caption-description')
    assert desc.get_attribute("contenteditable") == "true"
    desc.click()
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.type("A new description that wraps over more than one line")
    page.locator("#page").click(position={"x": 5, "y": 5})
    page.wait_for_timeout(50)
    assert (
        page.evaluate("StampAlbum.E[0].lbl")
        == "A new description that wraps over more than one line"
    )
    lines = page.locator('.cel[data-id="s1"] .caption-description').text_content().split("\n")
    assert len(lines) > 1, "the edited description should re-wrap to the box width"


def test_no_warning_for_a_neat_page(page):
    _show(page, [_stamp(1, 30, 40, **FULL), _stamp(2, 100, 40, **FULL)], border="solid")
    assert page.locator(".cel.caption-warn").count() == 0


def test_warns_when_captions_run_past_the_border(page):
    # Inside the page, but the captions cross the border line near the bottom
    _show(page, [_stamp(1, 30, 255, **FULL)], border="solid")
    cel = page.locator('.cel[data-id="s1"]')
    assert "caption-warn" in cel.get_attribute("class")
    assert cel.get_attribute("aria-description") == "Captions run past the page border"
    assert (
        cel.locator(".caption-warn-badge").get_attribute("title")
        == "Captions run past the page border"
    )


def test_warns_when_captions_run_into_the_next_stamp(page):
    _show(page, [_stamp(1, 30, 40, **FULL), _stamp(2, 30, 80)])
    assert (
        page.locator('.cel[data-id="s1"]').get_attribute("aria-description")
        == "Captions run into another item"
    )
    assert page.locator('.cel[data-id="s2"].caption-warn').count() == 0


def test_warning_clears_when_the_stamp_is_moved_away(page):
    _show(page, [_stamp(1, 30, 40, **FULL), _stamp(2, 30, 80)])
    page.evaluate("StampAlbum.E[1].y = 120 * 2.5; StampAlbum.render()")
    assert page.locator(".cel.caption-warn").count() == 0
