# ruff: noqa: F811
"""The Font list offers only fonts that print (ADR-001).

The list of fonts on this computer comes from the app (GET /api/fonts), not from the
browser guessing which names it can draw, so every font offered is one every export can
use. A font an album uses that this computer doesn't have is shown as such, and Export
says which fonts printed in Helvetica instead.
"""

import json

from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

FONTS = ["Georgia", "Palatino"]


def _serve_fonts(pg, fonts):
    pg.route("**/api/fonts", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"fonts": fonts})))
    pg.evaluate("StampAlbum.loadSystemFonts()")


def _text_item(pg, font):
    return pg.evaluate(
        """(f) => { StampAlbum.add({ t: 'text', x: 50, y: 50, w: 300, h: 45, lbl: 'Notes',
                                     font: f, fs: 10 });
                    const el = StampAlbum.E[StampAlbum.E.length - 1];
                    StampAlbum.select(el.id); return el.id; }""",
        font,
    )


def _groups(pg):
    return pg.evaluate(
        """() => [...document.querySelectorAll('#pfnt optgroup')].map(g => ({
                 label: g.label, fonts: [...g.querySelectorAll('option')].map(o => o.value) }))"""
    )


def test_the_font_list_is_the_apps(page):
    _serve_fonts(page, FONTS)
    groups = _groups(page)
    assert [g["label"] for g in groups] == ["Standard Fonts", "Fonts on this computer"]
    assert groups[1]["fonts"] == FONTS
    assert "Web Safe" not in page.inner_html("#pfnt"), "no guessed fonts"


def test_a_font_not_on_this_computer_is_shown_as_such(page):
    _serve_fonts(page, FONTS)
    _text_item(page, "Zapfino")
    assert page.input_value("#pfnt") == "Zapfino"
    shown = page.evaluate("document.querySelector('#pfnt').selectedOptions[0].textContent")
    assert shown == "Zapfino (not on this computer)"
    _text_item(page, "Georgia")
    assert page.input_value("#pfnt") == "Georgia"
    assert page.locator("#pfnt option[data-missing]").count() == 0


def test_the_font_list_arriving_late_keeps_the_items_font(page):
    _text_item(page, "Georgia")  # chosen before the app's list has arrived
    _serve_fonts(page, FONTS)
    page.wait_for_timeout(200)
    assert page.input_value("#pfnt") == "Georgia"


def test_export_says_which_fonts_print_in_helvetica(page):
    _serve_fonts(page, FONTS)
    page.wait_for_timeout(200)
    _text_item(page, "Georgia")
    assert page.evaluate("StampAlbum.missingFontsNote()") == ""
    _text_item(page, "Zapfino")
    note = page.evaluate("StampAlbum.missingFontsNote()")
    assert note == " Not on this computer, so printed in Helvetica: Zapfino."
