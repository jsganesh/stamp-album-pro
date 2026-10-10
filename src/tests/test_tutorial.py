# ruff: noqa: F811
"""The first-run tutorial: four steps, each with a picture of the current editor,
and a sample album laid out as an exhibition page."""

import pytest
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

SC = 2.5


def _open(page):
    page.evaluate("StampAlbum.showTutorial()")
    return page.locator("#tutorial-overlay .tutorial-step")


def test_every_step_has_a_picture_that_loads(page):
    steps = _open(page)
    assert steps.count() == 4
    for i in range(4):
        img = steps.nth(i).locator("img.tutorial-img")
        assert img.count() == 1, f"step {i + 1} has no picture"
        assert len(img.get_attribute("alt") or "") > 20, f"step {i + 1} picture needs a description"
        page.evaluate("i => { const s = [...document.querySelectorAll('#tutorial-overlay .tutorial-step')];"
                      " s.forEach((n, k) => n.classList.toggle('active', k === i)); }", i)
        img.evaluate("im => im.complete || new Promise(r => { im.onload = im.onerror = r; })")
        size = img.evaluate("im => [im.naturalWidth, im.naturalHeight]")
        assert size[0] > 0, f"step {i + 1} picture did not load"
        assert size[0] == 2 * size[1], "pictures are 2:1, as the tutorial box shows them"


def test_next_walks_through_the_steps_and_finishes(page):
    _open(page)
    for step in range(1, 5):
        active = page.evaluate("document.querySelector('#tutorial-overlay .tutorial-step.active').dataset.step")
        assert active == str(step)
        label = page.inner_text("#btn-tutorial-next")
        assert label == ("Get Started" if step == 4 else "Next")
        page.click("#btn-tutorial-next")
    assert "open" not in (page.get_attribute("#tutorial-overlay", "class") or "")


@pytest.mark.parametrize("selector", ["#pbs", "#phil-sec", "#def-theme", "#def-bdr", "#btn-page-setup",
                                      "#btn-preview", "#btn-export", "#btn-save", "#pw", "#ph"])
def test_the_controls_the_tutorial_names_exist(page, selector):
    assert page.locator(selector).count() == 1


def test_sample_album_shows_stamps_at_catalogue_size(page):
    page.evaluate("StampAlbum.newAlbum(); StampAlbum.loadSampleAlbum()")
    stamps = page.evaluate("StampAlbum.E.filter(e => e.t === 'stamp').map(e => "
                           "({lbl: e.lbl, w: e.w / StampAlbum._sc, h: e.h / StampAlbum._sc, x: e.x / StampAlbum._sc,"
                           " cat: e.cat, frame: StampAlbum.frameOf(e)}))")
    assert [s["lbl"] for s in stamps] == ["Penny Black", "Twopence Blue", "Penny Red"]
    for s in stamps:
        assert (s["w"], s["h"]) == (pytest.approx(19), pytest.approx(23)), "kept at the catalogue size"
        assert s["frame"] == "thin" and s["cat"]
    assert stamps[0]["x"] == pytest.approx(51.5)
    assert page.locator("#page .caption-warn").count() == 0, "the sample page has no warnings"
    assert page.evaluate("StampAlbum._pageBorder") == "solid"
