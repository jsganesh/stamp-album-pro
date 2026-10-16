# ruff: noqa: F811
"""Caption headings in a row, in the editor: the Exhibition page template's second row
shows its headings on one line, where the exports print them; a stamp moved out of the
row takes its heading back above its own frame."""

import pytest
from test_starter_templates_ui import _open_template
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

from stamp_album.core.parser import AlbumParser
from stamp_album.engines import caption_layout
from stamp_album.templates import TEMPLATES

EXHIBITION = next(t for t in TEMPLATES if t["id"] == "exhibition_page")

# Each stamp's heading node: (top of the stamp in mm, top and bottom of the heading in mm),
# measured on screen, so zoom and the page's position don't matter.
HEADINGS = """() => {
  const S = StampAlbum, pr = document.getElementById('page').getBoundingClientRect();
  const k = pr.width / (S._pw / S._sc);  // screen px per mm
  return S.E.filter(e => e.t === 'stamp').map(e => {
    const n = document.querySelector('.cel[data-id="' + e.id + '"] .caption-heading');
    const r = n.getBoundingClientRect();
    return { id: e.id, y: e.y / S._sc, top: (r.top - pr.top) / k, bottom: (r.bottom - pr.top) / k };
  });
}"""


def _second_row(heads):
    return [h for h in heads if 140 < h["y"] < 150]


def test_editor_row_headings_on_one_line(page):
    _open_template(page, EXHIBITION["name"])
    row = _second_row(page.evaluate(HEADINGS))
    assert len(row) == 4
    assert max(h["bottom"] for h in row) - min(h["bottom"] for h in row) < 0.05, row

    # Where the exports put them
    album = AlbumParser().parse(EXHIBITION["content"], "e.slbum")
    stamps = album.pages[0].absolute_stamps
    tops = caption_layout.page_row_tops(stamps)
    want = {}
    for s in stamps:
        if 140 < s.abs_y < 150:
            line = caption_layout.layout(s, s.abs_x, s.abs_y, s.width, s.height,
                                         row_top=tops[id(s)])[0]
            want[round(s.abs_y, 3)] = line.top
    for h in row:
        assert h["top"] == pytest.approx(want[round(h["y"], 3)], abs=0.1), (h, want)
    assert page.js_errors == []


def test_a_stamp_moved_out_of_the_row_takes_its_heading_back(page):
    _open_template(page, EXHIBITION["name"])
    small = min(_second_row(page.evaluate(HEADINGS)), key=lambda h: -h["y"])  # a 19 x 22 stamp
    before = small["bottom"]
    page.evaluate(
        "id => { const S = StampAlbum, e = S.E.find(x => x.id === id);"
        " e.y += 5 * S._sc; S.render(); }", small["id"])
    moved = next(h for h in page.evaluate(HEADINGS) if h["id"] == small["id"])
    # 5 mm lower and out of the row: its heading drops 5 mm plus the 3 mm it had been raised.
    assert moved["bottom"] - before == pytest.approx(8, abs=0.1), (before, moved)
    assert page.js_errors == []
