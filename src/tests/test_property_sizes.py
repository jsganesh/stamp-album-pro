# ruff: noqa: F811
"""Sizes and positions typed in Properties, or read from an album file, are kept as given:
a stamp's catalogue size (19 x 22 mm, say) must not change on the way in."""

import pytest
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)


def _ready(page):
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    page.evaluate("""StampAlbum.newAlbum();
        StampAlbum.E.push({id: 'a', t: 'stamp', s: 'rectangle', x: 100, y: 100, w: 75, h: 75,
                           bdr: 'solid', bdrW: 0.5, bdrC: '#000000', fill: '#ffffff', fillA: 100});
        StampAlbum.select('a');""")


def _mm(page):
    return page.evaluate("(() => { const e = StampAlbum.E[0], s = StampAlbum._sc;"
                         " return [e.x / s, e.y / s, e.w / s, e.h / s]; })()")


def _type(page, field, value):
    page.fill(field, value)
    page.press(field, "Tab")


def test_typed_size_and_position_are_kept_in_millimetres(page):
    _ready(page)
    for field, value in (("#pw", "19"), ("#ph", "22"), ("#px", "51.5"), ("#py", "55")):
        _type(page, field, value)
    assert _mm(page) == [pytest.approx(v) for v in (51.5, 55, 19, 22)]
    assert [page.input_value(f) for f in ("#px", "#py", "#pw", "#ph")] == ["51.5", "55", "19", "22"]


def test_sizes_read_from_a_file_are_not_rounded(page):
    _ready(page)
    page.evaluate("""StampAlbum.parseDSL('ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\n' +
        'STAMP_ADD_AT(51.5 55.0 19.0 22.0 "Penny Black" "" "" "" rectangle ' +
        '"solid" "#000000" 0.5 "#ffffff" 100)');
        StampAlbum.render();""")
    assert _mm(page) == [pytest.approx(v) for v in (51.5, 55, 19, 22)]
    dsl = page.evaluate("StampAlbum.buildDSL()")
    assert "STAMP_ADD_AT(51.5 55.0 19.0 22.0 " in dsl, "saved as read"
