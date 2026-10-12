# ruff: noqa: F811
"""Every element in the album keeps its own id after an album is loaded.

The editor numbers new items from a counter (`S.nid`). Loading an album, a template, the
sample or a saved draft used to leave that counter where it was, so the next item added
could take an id already in use (on first run, `el1`: the sample's title). Selecting or
dragging the new item then acted on the other one.
"""

import json

from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)

# Every element of the open album, with the current page's live ones.
ALL = "StampAlbum._pages.map((p, i) => i === StampAlbum._currentPage ? StampAlbum.E : p).flat()"

TWO_PAGES = (
    "ALBUM_PAGES_SIZE(210 297)\n"
    "PAGE_START\n"
    'STAMP_ADD_AT(20 20 19 22 "one" "" "" "")\n'
    'STAMP_ADD_AT(60 20 19 22 "two" "" "" "")\n'
    "PAGE_START\n"
    'STAMP_ADD_AT(20 20 19 22 "three" "" "" "")\n'
    'STAMP_ADD_AT(60 20 19 22 "four" "" "" "")\n'
    'STAMP_ADD_AT(100 20 19 22 "five" "" "" "")\n'
)


def _ids(pg):
    return pg.evaluate(f"({ALL}).map(e => e.id)")


def _add_stamp(pg):
    """Add a stamp the way the palette does and return its id (new items go last)."""
    return pg.evaluate(
        """(()=>{StampAlbum.add({t:'stamp', x:300, y:300, w:50, h:55, lbl:'new'});
        return StampAlbum.E[StampAlbum.E.length - 1].id})()"""
    )


def _assert_unique(pg):
    ids = _ids(pg)
    assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"


def test_first_run_sample_then_add(page):
    # The fresh page opens the sample album (the first-run tutorial).
    assert page.evaluate(f"({ALL}).length") > 0
    new_id = _add_stamp(page)
    _assert_unique(page)
    # Selecting the new item selects it, not an item of the sample.
    page.evaluate(f"StampAlbum.select({new_id!r})")
    assert page.evaluate("StampAlbum.E.find(e => e.id === StampAlbum.sel).lbl") == "new"


def test_opened_album_ids_past_every_page(page):
    page.evaluate(f"StampAlbum.parseDSL({TWO_PAGES!r})")
    page.evaluate("StampAlbum.switchPage(0)")
    for _ in range(4):  # page 2's ids are higher than page 1's: none may be reused
        _add_stamp(page)
    _assert_unique(page)
    page.evaluate("StampAlbum.switchPage(1)")
    _add_stamp(page)
    _assert_unique(page)


def test_template_then_add(page):
    page.evaluate(f"StampAlbum.parseDSL({TWO_PAGES!r})")
    for _ in range(3):
        _add_stamp(page)
    _assert_unique(page)


def test_duplicate_after_open(page):
    page.evaluate(f"StampAlbum.parseDSL({TWO_PAGES!r})")
    page.evaluate("StampAlbum.select(StampAlbum.E[0].id)")
    page.keyboard.press("Control+d")
    page.keyboard.press("Control+d")
    _assert_unique(page)


def test_restored_draft_then_add(page):
    # A draft whose ids are past where a fresh counter starts, on more than one page.
    stamp = {"t": "stamp", "s": "rectangle", "w": 47.5, "h": 55, "lbl": "", "bdr": "solid",
             "bdrC": "#000", "bdrW": 1, "fill": "transparent", "fillA": 0, "img": "",
             "font": "HN", "fs": 12}
    pages = [[dict(stamp, id="el3", x=50, y=50), dict(stamp, id="el7", x=150, y=50)],
             [dict(stamp, id="el42", x=50, y=50)]]
    draft = {"v": 1, "pages": pages, "currentPage": 0, "elements": pages[0], "pw": 210, "ph": 297}
    page.evaluate(f"localStorage.setItem('stampalbum.draft', {json.dumps(json.dumps(draft))})")
    page.reload()
    wait_for_app(page)
    assert sorted(_ids(page)) == ["el3", "el42", "el7"]
    for _ in range(45):  # far enough to reach el42 from a counter at el1
        _add_stamp(page)
    _assert_unique(page)
    assert not page.js_errors
