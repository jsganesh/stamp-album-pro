# ruff: noqa: F811
"""Opening an album whose elements sit past the page edge offers to move them inside.

Nothing moves unless the person chooses "Move inside"; the move is one undo step.
Only opening a file asks: templates, the wizard, the tutorial and DSL Apply stay silent.
"""

import re

from axe_playwright_python.sync_playwright import Axe
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)

A4 = "ALBUM_PAGES_SIZE(210 297)\n"
FITS = 'STAMP_ADD_AT(20 20 19 22 "fits" "" "" "")\n'
PAST_RIGHT = 'STAMP_ADD_AT(195 40 40 30 "past right" "" "" "")\n'
PAST_LEFT = 'STAMP_ADD_AT(-5 60 19 22 "past left" "" "" "")\n'
# Every element of the open album, with the current page's live ones.
ALL = "StampAlbum._pages.map((p, i) => i === StampAlbum._currentPage ? StampAlbum.E : p).flat()"


def _album(*pages):
    return A4 + "".join("PAGE_START\n" + "".join(p) for p in pages)


def _open_saved(page, dsl, name="old album.slbum"):
    """Open an album from File › Open recent, served by a fake file store."""
    page.route(re.compile(r".*/files\?.*"), lambda r: r.fulfill(json=[name]))
    page.route(re.compile(r".*/files/[^/?]+$"),
               lambda r: r.fulfill(body=dsl, content_type="text/plain"))
    page.click("#menu-file-btn")
    page.click("#menu-recent")
    page.wait_for_selector("#menu-recent-list .mi[data-file]")
    page.click("#menu-recent-list .mi[data-file]")
    for _ in range(100):
        if page.evaluate(f"StampAlbum._currentFile === {name!r}"):
            break
        page.wait_for_timeout(50)


def _prompt_open(page):
    return page.evaluate("document.getElementById('fit-prompt-overlay').classList.contains('open')")


def _stamp(page, label):
    return page.evaluate(f"""(() => {{
        const e = {ALL}.find(e => e.lbl === {label!r}), sc = StampAlbum._sc;
        return {{x: e.x / sc, y: e.y / sc, w: e.w / sc, h: e.h / sc}};
    }})()""")


def test_opening_an_album_past_the_edge_asks_first(page):
    _open_saved(page, _album([FITS, PAST_RIGHT]))
    assert _prompt_open(page)
    assert page.inner_text("#fp-note").startswith("1 element sits past the page edge.")
    assert page.evaluate("document.activeElement.id") == "fp-leave"
    assert _stamp(page, "past right")["x"] == 195  # nothing has moved yet
    assert page.js_errors == []


def test_leave_keeps_the_album_as_saved(page):
    _open_saved(page, _album([FITS, PAST_RIGHT]))
    page.click("#fp-leave")
    assert not _prompt_open(page)
    assert _stamp(page, "past right") == {"x": 195, "y": 40, "w": 40, "h": 30}
    assert page.evaluate("StampAlbum._dirty") is False


def test_escape_leaves_the_album_as_saved(page):
    _open_saved(page, _album([FITS, PAST_RIGHT]))
    page.keyboard.press("Escape")
    assert not _prompt_open(page)
    assert _stamp(page, "past right")["x"] == 195
    assert page.evaluate("StampAlbum._dirty") is False


def test_move_inside_is_one_undo_step(page):
    _open_saved(page, _album([FITS, PAST_RIGHT]))
    page.click("#fp-move")
    assert not _prompt_open(page)
    s = _stamp(page, "past right")
    assert s["x"] + s["w"] <= 210 and (s["w"], s["h"]) == (40, 30)  # inside, same size
    assert page.evaluate("StampAlbum._dirty") is True
    page.evaluate("StampAlbum.undo()")
    assert _stamp(page, "past right")["x"] == 195  # back to the album as opened
    assert page.evaluate("StampAlbum._undoStack.length") == 1  # and no further back
    assert page.js_errors == []


def test_counts_every_edge_and_every_page(page):
    _open_saved(page, _album([FITS, PAST_RIGHT], [PAST_LEFT]))
    assert page.inner_text("#fp-note").startswith("2 elements on 2 pages sit past the page edge.")
    page.click("#fp-move")
    s = _stamp(page, "past left")
    assert s["x"] >= 0


def test_an_album_that_fits_opens_without_asking(page):
    _open_saved(page, _album([FITS]))
    assert not _prompt_open(page)
    assert page.js_errors == []


def test_file_open_also_asks(page):
    page.set_input_files("#file-inp", files=[{"name": "picked.slbum", "mimeType": "text/plain",
                                               "buffer": _album([PAST_RIGHT]).encode()}])
    for _ in range(100):
        if _prompt_open(page):
            break
        page.wait_for_timeout(50)
    assert _prompt_open(page)
    assert page.evaluate("StampAlbum._currentFile") == "picked.slbum"


def test_loading_dsl_without_a_file_does_not_ask(page):
    # Templates, the wizard, the tutorial sample and DSL Apply load through parseDSL alone.
    page.evaluate(f"StampAlbum.parseDSL({_album([PAST_RIGHT])!r}); StampAlbum.render()")
    assert not _prompt_open(page)


def test_old_oversized_album_offers_the_move(page):
    # v0.2.0 saved A4 as 238 x 336.8 mm; corrected to A4, this stamp now sits past the edge.
    old = 'ALBUM_PAGES_SIZE(238 336.8)\nPAGE_START\nSTAMP_ADD_AT(200 20 30 30 "old" "" "" "")\n'
    page.evaluate(f"StampAlbum.parseDSL({old!r})")
    toast = page.inner_text("#toast-container")
    assert toast.startswith("Page size corrected to 210 x 297 mm")
    assert "past the page edge" not in toast
    _open_saved(page, old)
    assert _prompt_open(page)


def test_keys_stay_in_the_dialog(page):
    _open_saved(page, _album([FITS, PAST_RIGHT]))
    page.keyboard.press("Delete")  # would delete the selection if the page saw it
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "fp-move"
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "fp-leave"
    assert page.evaluate(ALL + ".length") == 2


def test_dialog_passes_axe(page):
    _open_saved(page, _album([FITS, PAST_RIGHT]))
    page.evaluate("Promise.all(document.getAnimations().map(a => a.finished.catch(() => null)))")
    res = Axe().run(page, context="#fit-prompt-overlay", options={"resultTypes": ["violations"]})
    assert [v["id"] for v in res.response["violations"]] == []
