# ruff: noqa: F811
"""The editor's grid: faint dots at rest, lines while an item moves.

The dots sit on the snap points (multiples of the snap step from the page's top left)
and keep their size on screen at any zoom. The grid is never part of an export.
"""

from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)

SHOWN = """(cls => { const r = document.querySelector('#grid-overlay .' + cls);
    return getComputedStyle(r).display !== 'none'; })"""


def _shown(pg, cls):
    return pg.evaluate(f"{SHOWN}({cls!r})")


def _stamp_box(pg):
    return pg.locator("#page .cel").nth(2).bounding_box()


def _sample(pg):
    pg.evaluate("StampAlbum.loadSampleAlbum && StampAlbum.loadSampleAlbum()")
    pg.wait_for_timeout(100)
    assert pg.locator("#page .cel").count() >= 3


def test_dots_at_rest_lines_while_dragging(page):
    _sample(page)
    assert _shown(page, "grid-dots") and not _shown(page, "grid-lines")
    b = _stamp_box(page)
    page.mouse.move(b["x"] + 15, b["y"] + 15)
    page.mouse.down()
    # A click that selects without moving keeps the dots.
    assert _shown(page, "grid-dots") and not _shown(page, "grid-lines")
    page.mouse.move(b["x"] + 45, b["y"] + 60, steps=4)
    assert _shown(page, "grid-lines") and not _shown(page, "grid-dots")
    page.mouse.up()
    assert _shown(page, "grid-dots") and not _shown(page, "grid-lines")


def test_lines_while_a_palette_item_is_dragged_over_the_page(page):
    page.evaluate("document.getElementById('page').classList.add('drag-over')")
    assert _shown(page, "grid-lines") and not _shown(page, "grid-dots")
    page.evaluate("document.getElementById('page').classList.remove('drag-over')")
    assert _shown(page, "grid-dots")


def test_dots_sit_on_the_snap_points(page):
    for step in ("5", "10"):
        page.select_option("#grid", step)
        g = page.evaluate(
            """(()=>{const p=document.getElementById('grid-dots'), c=p.querySelector('circle');
            return {w:+p.getAttribute('width'), x:+p.getAttribute('x'), y:+p.getAttribute('y'),
                    cx:+c.getAttribute('cx'), cy:+c.getAttribute('cy')}})()"""
        )
        gs = int(step) * 2.5
        assert g["w"] == gs, g
        # The dot is drawn in the cell's middle and the cell is shifted back by half,
        # so the dots land on 0, gs, 2·gs … from the page's top left.
        assert g["x"] + g["cx"] == 0 and g["y"] + g["cy"] == 0, g


def test_dots_keep_their_size_on_screen(page):
    sizes = []
    for z in (1, 2):
        page.evaluate(f"StampAlbum.zoomAt({z})")
        r, sw, zoom = page.evaluate(
            """[+document.querySelector('#grid-dots circle').getAttribute('r'),
            +document.querySelector('#grid-pattern path').getAttribute('stroke-width'),
            StampAlbum.zoom]"""
        )
        sizes.append((r * zoom, sw * zoom))
    assert abs(sizes[0][0] - sizes[1][0]) < 1e-6 and abs(sizes[0][1] - sizes[1][1]) < 1e-6, sizes


def _overlay_display(pg):
    return pg.evaluate("getComputedStyle(document.getElementById('grid-overlay')).display")


def test_snap_off_hides_the_grid(page):
    page.select_option("#grid", "0")
    assert _overlay_display(page) == "none"
    page.select_option("#grid", "5")
    assert _overlay_display(page) != "none"
    assert not page.js_errors
