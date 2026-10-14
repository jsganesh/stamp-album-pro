# ruff: noqa: F811
"""Unsaved work from last time is drawn when the editor opens, and said so.

It used to be loaded but not drawn: the page looked blank, the status bar counted the
old items, and adding a stamp brought them all back; undo then went back to the old
work, not to a blank page.
"""

from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)


def _drawn(pg):
    return pg.evaluate("document.querySelectorAll('#page .cel').length")


def _reopen_with_draft(pg):
    """Make some unsaved work, wait for its draft to be kept, then open the editor again."""
    pg.evaluate("StampAlbum.newAlbum(); StampAlbum.loadSampleAlbum(); StampAlbum.pushUndo()")
    pg.evaluate("StampAlbum.saveDraft && StampAlbum.saveDraft()")
    for _ in range(50):
        if pg.evaluate("!!localStorage.getItem('stampalbum.draft')"):
            break
        pg.wait_for_timeout(100)
    n = pg.evaluate("StampAlbum.E.length")
    pg.evaluate("localStorage.setItem('stampalbum-tutorial-done', '1')")  # no tutorial on top
    pg.reload()
    wait_for_app(pg)
    return n


def test_restored_work_is_drawn_and_marked_unsaved(page):
    n = _reopen_with_draft(page)
    assert n > 0
    assert page.evaluate("StampAlbum.E.length") == n
    assert _drawn(page) == n, "the restored items are on the page"
    assert page.is_visible("#restore-note")
    assert "last time" in page.inner_text("#restore-note")
    assert page.is_visible("#tb-dirty"), "it shows Not saved"


def test_undo_after_an_add_goes_back_to_the_restored_work(page):
    n = _reopen_with_draft(page)
    page.click("#sidebar .p-item[data-s=rectangle]")
    assert _drawn(page) == n + 1
    page.evaluate("StampAlbum.undo()")
    assert _drawn(page) == n
    page.evaluate("StampAlbum.undo()")  # nothing further back: it stops at the restored work
    assert _drawn(page) == n


def test_keep_working_hides_the_note(page):
    _reopen_with_draft(page)
    page.click("#restore-keep")
    assert page.is_hidden("#restore-note")


def test_start_a_new_album_asks_then_clears(page):
    _reopen_with_draft(page)
    page.once("dialog", lambda d: d.accept())
    page.click("#restore-new")
    assert page.evaluate("StampAlbum.E.length") == 0 and _drawn(page) == 0
    assert page.is_hidden("#restore-note")


def test_start_a_new_album_can_be_cancelled(page):
    n = _reopen_with_draft(page)
    page.once("dialog", lambda d: d.dismiss())
    page.click("#restore-new")
    assert _drawn(page) == n
    assert page.is_visible("#restore-note")


def test_no_note_without_unsaved_work(page):
    page.evaluate("localStorage.removeItem('stampalbum.draft')")
    page.reload()
    wait_for_app(page)
    assert page.is_hidden("#restore-note")
