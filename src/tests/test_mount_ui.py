# ruff: noqa: F811
"""Stamp mounts and FIP sheets in the editor (owner's decisions 2026-10-16): Mount overhang and
Gap to frame under Album and page, the frame drawn their sum out from the stamp, the mount's
edge as a faint dotted line never printed; FIP exhibit sheets in Page setup."""

import pytest
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

PT = 25.4 / 72


def _stamp(pg):
    pg.evaluate("""() => { const S = StampAlbum, sc = S._sc;
        S.E.push({id: 's1', t: 'stamp', s: 'rectangle', x: 60 * sc, y: 60 * sc, w: 25 * sc,
                  h: 30 * sc, bdr: 'solid', bdrC: '#000000', bdrW: 0.5, lbl: 'Penny Black'});
        S.render(); }""")


def _frame_mm(pg):
    """How far out the stamp's frame line sits (its centre, mm from the stamp's edge)."""
    return pg.evaluate("""-Number(document.querySelector('.cel[data-id="s1"] .frame-line')
        .getAttribute('x')) / StampAlbum._sc""")


def _mount_edge_mm(pg):
    return pg.evaluate("""(() => {
        const n = document.querySelector('.cel[data-id="s1"] .mount-edge');
        return n ? -Number(n.getAttribute('x')) / StampAlbum._sc : null; })()""")


def _fields(pg):
    return pg.evaluate("[document.getElementById('def-mount-over').value,"
                       " document.getElementById('def-mount-gap').value]")


def test_a_new_album_starts_at_1_5_plus_1(page):
    page.evaluate("StampAlbum.newAlbum()")
    _stamp(page)
    page.evaluate("StampAlbum.select(null)")
    assert _fields(page) == ["1.5", "1"]
    assert page.get_by_label("Mount overhang", exact=True).is_visible()
    assert page.get_by_label("Gap to frame", exact=True).is_visible()
    assert "Frames are drawn 2.5 mm out from the stamp" in page.inner_text("#mount-note")
    assert _frame_mm(page) == pytest.approx(2.5 + 0.25 * PT, abs=1e-3)
    assert _mount_edge_mm(page) == pytest.approx(1.5, abs=1e-3)
    options = page.evaluate("[...document.querySelectorAll('#def-mount-over option')]"
                            ".map(o => o.textContent)")
    assert options == ["None", "1 mm", "1.5 mm", "2 mm", "2.5 mm", "3 mm"]
    assert page.js_errors == []


def test_changing_the_mount_moves_every_frame_and_can_be_undone(page):
    page.evaluate("StampAlbum.newAlbum()")
    _stamp(page)
    page.evaluate("StampAlbum.select(null); StampAlbum.pushUndo()")
    page.select_option("#def-mount-gap", "2")
    assert _frame_mm(page) == pytest.approx(3.5 + 0.25 * PT, abs=1e-3)
    page.select_option("#def-mount-over", "0")
    assert _frame_mm(page) == pytest.approx(2 + 0.25 * PT, abs=1e-3)
    assert _mount_edge_mm(page) is None  # no mount shows, so no edge line
    assert "No mount shows beyond the stamps" in page.inner_text("#mount-note")
    page.evaluate("StampAlbum.undo()")
    assert _fields(page) == ["1.5", "2"]
    assert _frame_mm(page) == pytest.approx(3.5 + 0.25 * PT, abs=1e-3)


def test_the_mount_edge_is_never_printed(page):
    page.evaluate("StampAlbum.newAlbum()")
    _stamp(page)
    state = page.evaluate("StampAlbum.buildCanvasState('svg')")
    assert (state["mount_overhang"], state["mount_gap"]) == (1.5, 1)
    svg = page.request.post(page.url.rstrip("/") + "/export-from-state", data=state).text()
    assert "mount-edge" not in svg and "frame-line" in svg


def test_an_old_album_opens_at_1mm_and_saves_it(page):
    page.evaluate("""StampAlbum.openAlbum('old.slbum', 'ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\n' +
        'STAMP_ADD_AT(24 24 25 30 "x" "" "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)'
        + '\\n')""")
    page.evaluate("StampAlbum.select(null)")
    assert _fields(page) == ["0", "1"]
    assert page.evaluate("StampAlbum.CORE.frameClearance(StampAlbum.E[0])") == 1
    assert "ALBUM_MOUNT(0 1)" in page.evaluate("StampAlbum.buildDSL()")


def test_the_stamp_panel_says_where_the_frame_is(page):
    page.evaluate("StampAlbum.newAlbum()")
    _stamp(page)
    page.evaluate("StampAlbum.select('s1')")
    note = page.inner_text("#pframe-size")
    assert note.startswith("Frame 30.4 × 35.4 mm: mount 1.5 mm, then 1 mm to the frame line"), note
    page.evaluate("StampAlbum.CORE.setMount(0, 1); StampAlbum.render(); StampAlbum.select('s1')")
    assert "1 mm clear all round" in page.inner_text("#pframe-size")


def test_a_draft_keeps_the_mount(page):
    page.evaluate("StampAlbum.newAlbum()")
    _stamp(page)
    page.evaluate("StampAlbum.CORE.setMount(2, 1.5); StampAlbum.saveDraft();"
                  " StampAlbum.CORE.setMount(0, 1); StampAlbum.loadDraft()")
    assert page.evaluate("StampAlbum.CORE.getMount()") == {"overhang": 2, "gap": 1.5}


# ── FIP sheets ──


def test_page_setup_offers_fip_sheets_used_as_listed(page):
    page.evaluate("StampAlbum.newAlbum(); StampAlbum.select(null)")
    page.click("#btn-page-setup")
    labels = page.evaluate("[...document.querySelectorAll('#ps-size option')]"
                           ".map(o => o.textContent)")
    assert labels[-3:] == ["FIP sheet 23 × 29.7 cm", "FIP sheet 31 × 29.7 cm",
                           "FIP sheet 46 × 29.7 cm"]
    assert page.is_visible("#ps-orient")
    page.select_option("#ps-size", "fip31")
    assert page.is_hidden("#ps-orient")  # no portrait or landscape for an FIP sheet
    page.click("#ps-apply")
    assert page.evaluate("[StampAlbum._pw / StampAlbum._sc, StampAlbum._ph / StampAlbum._sc]") == [
        310, 297]
    assert page.inner_text("#btn-page-setup").strip().startswith("FIP sheet 31 × 29.7 cm")
    assert "ALBUM_PAGES_SIZE(310 297)" in page.evaluate("StampAlbum.buildDSL()")
    page.click("#btn-page-setup")
    assert page.evaluate("document.getElementById('ps-size').value") == "fip31"
    assert page.is_hidden("#ps-orient")


def test_the_wizard_offers_fip_sheets(page):
    values = page.evaluate(
        "[...document.querySelectorAll('#wiz-pg-size option')].map(o => o.value)")
    assert values[-3:] == ["fip23", "fip31", "fip46"]
