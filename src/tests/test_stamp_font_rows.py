# ruff: noqa: F811
"""Stamp captions always use the bundled caption font at fixed sizes, so Properties
hides Font and Size for stamps. Other items still use them for their own text."""

from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)


def _ready(page):
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    page.evaluate("""StampAlbum.newAlbum();
        StampAlbum.E.push({id: 's', t: 'stamp', s: 'rectangle', x: 100, y: 100, w: 47.5, h: 55,
                           bdr: 'solid', bdrW: 0.5, bdrC: '#000000', fill: '#ffffff', fillA: 100,
                           lbl: 'Penny Black', font: 'TR', fs: 14});
        StampAlbum.E.push({id: 't', t: 'text', s: 'rectangle', x: 100, y: 300, w: 200, h: 40,
                           bdr: 'none', bdrW: 0, bdrC: '#000000', fill: 'transparent', fillA: 0,
                           lbl: 'Some text', font: 'TR', fs: 14});
        StampAlbum.E.push({id: 'f', t: 'freehand', s: 'oval', x: 300, y: 100, w: 60, h: 60,
                           bdr: 'solid', bdrW: 0.5, bdrC: '#000000', fill: '#ffffff', fillA: 100,
                           lbl: 'Shape', font: 'TR', fs: 14});
        StampAlbum.render();""")


def _shown(page, sel):
    return page.is_visible(sel)


def test_font_and_size_are_hidden_for_stamps(page):
    _ready(page)
    page.evaluate("StampAlbum.select('s')")
    assert not _shown(page, "#pfnt")
    assert not _shown(page, "#pfs")
    assert _shown(page, "#plbl"), "the label is still the stamp's description"
    assert _shown(page, "#pcapfont-note")
    assert "caption font" in page.inner_text("#pcapfont-note")


def test_font_and_size_are_for_text_items_only(page):
    # A free shape's label is a caption, drawn in the caption font at a fixed size,
    # and the file stores no font for it, so Font and Size would do nothing there.
    _ready(page)
    for item in ("s", "t", "s", "f", "t"):
        page.evaluate(f"StampAlbum.select('{item}')")
        text = item == "t"
        assert _shown(page, "#pfnt") is text, item
        assert _shown(page, "#pfs") is text, item
        assert _shown(page, "#pcapfont-note") is (item == "s"), item


def test_stored_stamp_font_is_kept_in_the_file(page):
    _ready(page)
    page.evaluate("StampAlbum.select('s')")
    stamp = page.evaluate("StampAlbum.E.find(e => e.id === 's')")
    assert (stamp["font"], stamp["fs"]) == ("TR", 14), "hiding the rows changes nothing stored"
