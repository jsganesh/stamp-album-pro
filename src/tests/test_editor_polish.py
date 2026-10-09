"""Small editor fixes from the UI audit: fresh start, toasts, Properties panel width, shortcuts dialog.

Browser tests; they skip like the other browser tests when Playwright is missing locally.
"""

# ruff: noqa: F811  (pytest fixtures are imported, then named as test arguments)
import pytest
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)


def _status(page):
    return page.evaluate("""(() => ({
        page: document.getElementById('sb-page').textContent,
        unsaved: !document.getElementById('sb-dirty').classList.contains('sb-dirty-hidden'),
        title: document.getElementById('file-name').textContent,
        pages: StampAlbum._pages.length, current: StampAlbum._currentPage}))()""")


# ── Fresh start ──


def test_fresh_start_shows_one_page_and_no_unsaved_flag(page):
    # The page fixture is a fresh browser, so the first-run sample album has loaded.
    st = _status(page)
    assert st["page"] == "Page 1 of 1", st
    assert st["pages"] == 1 and st["current"] == 0, st
    assert not st["unsaved"], st
    assert not st["title"].startswith("●"), st


def test_no_unsaved_flag_after_skipping_the_tutorial_or_new_album(page):
    page.evaluate("document.getElementById('tutorial-overlay').classList.add('open')")
    page.click("#btn-tutorial-skip")
    assert not _status(page)["unsaved"]
    page.on("dialog", lambda d: d.accept())
    page.click("#menu-file-btn")
    page.click("#btn-new")
    st = _status(page)
    assert not st["unsaved"] and st["page"] == "Page 1 of 1", st


def test_opened_album_starts_on_its_first_page(page):
    dsl = (
        "ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\n"
        'STAMP_ADD_AT(20 20 40 30 "first" "rectangle" "solid" "#fff")\\nPAGE_START\\n'
        'STAMP_ADD_AT(20 20 40 30 "second" "rectangle" "solid" "#fff")'
    )
    page.evaluate(f"StampAlbum.parseDSL('{dsl}')")
    st = _status(page)
    assert st["page"] == "Page 1 of 2", st
    assert page.evaluate("StampAlbum.E.map(e => e.lbl)") == ["first"]


# ── Toasts ──


def test_a_new_toast_replaces_the_one_showing(page):
    page.evaluate(
        "StampAlbum.showToast('first', 'info'); StampAlbum.showToast('second', 'success')"
    )
    toasts = page.evaluate(
        "[...document.querySelectorAll('#toast-container .toast')].map(t => t.textContent)"
    )
    assert toasts == ["second"]


def test_wizard_shows_one_toast(page):
    page.click("#menu-file-btn")
    page.click("#btn-wizard")
    page.click("#btn-wiz-apply")
    toasts = page.evaluate(
        "[...document.querySelectorAll('#toast-container .toast')].map(t => t.textContent)"
    )
    assert toasts == ["Album created from wizard"]


# ── Properties panel ──


@pytest.mark.parametrize("large_text", [False, True])
@pytest.mark.parametrize("kind", ["stamp", "text"])
def test_properties_panel_fits_at_1440(page, kind, large_text):
    page.set_viewport_size({"width": 1440, "height": 900})
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    if large_text:
        page.click("#menu-view-btn")
        page.click("#btn-large-text")
    page.evaluate(f"StampAlbum.select(StampAlbum.E.find(e => e.t === '{kind}').id)")
    page.wait_for_timeout(250)  # panel width transition
    over = page.evaluate("""(() => {
        const rp = document.getElementById('rp'), edge = rp.getBoundingClientRect().right + 0.5;
        return [...rp.querySelectorAll('*')].filter(k => k.getClientRects().length && k.getBoundingClientRect().right > edge)
            .map(k => k.id || k.tagName + '.' + k.className);
    })()""")
    assert over == [], f"past the Properties panel's right edge: {over}"
    assert page.evaluate(
        "document.getElementById('rp').scrollWidth <= document.getElementById('rp').clientWidth"
    )


# ── Keyboard shortcuts dialog ──


def _listed(page):
    return page.evaluate(
        "[...document.querySelectorAll('#help-overlay .help-row')]"
        ".map(r => [r.querySelector('kbd').textContent.trim(), r.querySelector('span').textContent.trim()])"
    )


def test_shortcuts_dialog_lists_only_keys_that_work(page):
    keys = [k for k, _ in _listed(page)]
    for dead in ("Ctrl+P", "Ctrl+N", "Ctrl+L", "Ctrl+E", "Ctrl+R"):
        assert dead not in keys, f"{dead} is listed but nothing handles it"
    assert keys.count("F5") == 1
    assert ["F5", "Preview"] in _listed(page)
    assert ["Ctrl+D", "Duplicate"] in _listed(page)


def test_listed_shortcuts_do_what_the_dialog_says(page):
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    n = page.evaluate("StampAlbum.E.length")
    page.evaluate(
        "StampAlbum.select(StampAlbum.E[StampAlbum.E.length - 1].id); document.activeElement.blur()"
    )
    page.keyboard.press("Control+d")
    assert page.evaluate("StampAlbum.E.length") == n + 1, "Ctrl+D should duplicate the selection"
    page.keyboard.press("Control+z")
    assert page.evaluate("StampAlbum.E.length") == n, "Ctrl+Z should undo"
    page.keyboard.press("?")
    assert page.evaluate("document.getElementById('help-overlay').classList.contains('open')")


def test_sample_album_fits_inside_the_page_border(page):
    # The first-run sample's third stamp used to run past the page edge.
    inside = page.evaluate("""(() => { const m = 12;  // page border inset, canvas px
        return StampAlbum.E.every(e => e.x >= m && e.y >= m && e.x + e.w <= StampAlbum._pw - m && e.y + e.h <= StampAlbum._ph - m); })()""")
    assert inside
