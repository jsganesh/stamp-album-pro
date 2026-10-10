"""Exhibition frames, album themes and heading marks in the editor (browser tests)."""

# ruff: noqa: F811  (pytest fixtures are imported, then named as test arguments)
import pytest
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)

GREEN = "rgb(46, 94, 58)"  # THEMES.green, #2E5E3A


def _ready(page):
    page.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")


def _select_kind(page, kind):
    page.evaluate(f"StampAlbum.select(StampAlbum.E.find(e => e.t === '{kind}').id)")


def _visible(page, sel):
    return page.evaluate(
        f"(() => {{ const e = document.querySelector('{sel}'); return !!e && e.getClientRects().length > 0; }})()"
    )


def _options(page, sel):
    return page.evaluate(
        f"[...document.querySelectorAll('{sel} option')].map(o => [o.value, o.textContent.trim()])"
    )


# ── Properties: one Frame choice for stamps, no colours or fills ──


def test_stamp_properties_offer_only_the_four_frames(page):
    _ready(page)
    _select_kind(page, "stamp")
    assert _options(page, "#pbs") == [
        ["none", "None"],
        ["thin", "Thin"],
        ["medium", "Medium"],
        ["double", "Double"],
    ]
    for gone in ("#pbc", "#pbw", "#pfc", "#pfa"):
        assert page.locator(gone).count() == 0, f"{gone} should be removed"


def test_text_properties_show_heading_mark_not_frame(page):
    _ready(page)
    _select_kind(page, "text")
    assert _visible(page, "#phead")
    assert not _visible(page, "#pbs")
    _select_kind(page, "stamp")
    assert not _visible(page, "#phead")
    assert _visible(page, "#pbs")


def _frame_lines(page):
    """The selected stamp's frame lines: stroke widths (canvas px) and colours."""
    return page.evaluate("""(() => {
        const ls = [...document.querySelectorAll('.cel.selected .stamp-frame .frame-line')];
        return {w: ls.map(l => parseFloat(l.getAttribute('stroke-width'))),
                colours: ls.map(l => l.getAttribute('stroke'))};
    })()""")


def test_frame_choice_is_drawn_on_the_page(page):
    _ready(page)
    _select_kind(page, "stamp")
    seen = {}
    for frame in ("none", "thin", "medium", "double"):
        page.select_option("#pbs", frame)
        seen[frame] = _frame_lines(page)
    assert seen["none"]["w"] == []
    assert len(seen["thin"]["w"]) == 1 and len(seen["medium"]["w"]) == 1
    assert seen["thin"]["w"][0] < seen["medium"]["w"][0]
    assert len(seen["double"]["w"]) == 2
    assert all(c == "#000000" for f, s in seen.items() for c in s["colours"])


def test_frame_change_is_one_undo_step(page):
    _ready(page)
    _select_kind(page, "stamp")
    sid = page.evaluate("StampAlbum.sel")
    page.select_option("#pbs", "double")
    page.evaluate("StampAlbum.undo()")
    assert page.evaluate(f"StampAlbum.frameOf(StampAlbum.E.find(e => e.id === '{sid}'))") == "thin"


# ── Page bar: Theme replaces the colour pickers; page borders in two groups ──


def test_page_bar_has_theme_and_no_colour_pickers(page):
    assert page.locator("#def-bdr-c").count() == 0
    assert page.locator("#def-fill-c").count() == 0
    assert _options(page, "#def-theme") == [
        ["exhibition", "Exhibition"],
        ["green", "Green"],
        ["maroon", "Maroon"],
        ["navy", "Navy"],
        ["brown", "Brown"],
    ]
    assert page.input_value("#def-theme") == "exhibition"


def test_page_borders_are_grouped_and_decorative_ones_carry_a_note(page):
    groups = page.evaluate("[...document.querySelectorAll('#def-bdr optgroup')].map(g => g.label)")
    assert groups == ["Plain", "Decorative (not for competition)"]
    plain = page.evaluate(
        "[...document.querySelectorAll('#def-bdr optgroup')[0].querySelectorAll('option')].map(o => o.value)"
    )
    assert plain == ["none", "solid", "double"]
    page.select_option("#def-bdr", "classic")
    assert _visible(page, "#bdr-note")
    assert "not for competition" in page.inner_text("#bdr-note").lower()
    page.select_option("#def-bdr", "double")
    assert not _visible(page, "#bdr-note")


def test_theme_colours_the_page_border_and_marked_headings_only(page):
    _ready(page)
    page.evaluate("""StampAlbum.E.push({id: 'h1', t: 'text', s: 'text', x: 50, y: 40, w: 300, h: 40, lbl: 'Heading', font: 'HB', fs: 18, role: 'heading'},
                                       {id: 'p1', t: 'text', s: 'text', x: 50, y: 90, w: 300, h: 30, lbl: 'Plain', font: 'HN', fs: 10}); StampAlbum.render()""")
    page.select_option("#def-bdr", "solid")
    page.select_option("#def-theme", "green")
    colour = lambda el_id: page.evaluate(  # noqa: E731
        f"getComputedStyle(document.querySelector('.cel[data-id=\"{el_id}\"] .elbl')).color"
    )  # noqa: E731
    assert colour("h1") == GREEN
    assert colour("p1") != GREEN
    stroke = page.evaluate("document.querySelector('#page-border rect').getAttribute('stroke')")
    assert stroke.upper() == "#2E5E3A"
    stamp_border = page.evaluate(
        "document.querySelector('.cel.stamp-el .stamp-frame .frame-line').getAttribute('stroke')"
    )
    assert stamp_border == "#000000", "stamp frames stay black"


def test_theme_change_is_saved_undoable_and_survives_a_reload(page):
    _ready(page)
    page.select_option("#def-theme", "navy")
    assert 'ALBUM_THEME("navy")' in page.evaluate("StampAlbum.buildDSL()")
    page.evaluate("StampAlbum.undo()")
    assert page.input_value("#def-theme") == "exhibition"
    page.evaluate("StampAlbum.redo()")
    assert page.input_value("#def-theme") == "navy"
    page.wait_for_timeout(800)
    page.reload()
    wait_for_app(page)
    assert page.input_value("#def-theme") == "navy"


def test_older_album_with_its_own_colour_shows_custom(page):
    page.evaluate(
        """StampAlbum.parseDSL('ALBUM_PAGES_BORDER(0.5 0 0 1)\\nCOLOUR_ALBUM_BORDER("#ff0000")\\nPAGE_START')"""
    )
    assert page.input_value("#def-theme") == "custom"
    assert ["custom", "Custom"] in _options(page, "#def-theme")
    page.select_option("#def-theme", "green")
    assert ["custom", "Custom"] not in _options(page, "#def-theme")


# ── Heading marks ──


@pytest.mark.parametrize("item,role", [("heading", "heading"), ("label", None)])
def test_palette_heading_item_is_marked(page, item, role):
    _ready(page)
    n = page.evaluate("StampAlbum.E.length")
    page.click(f".p-item[aria-label^='Add {item.capitalize()}']")
    assert page.evaluate("StampAlbum.E.length") == n + 1
    assert page.evaluate("StampAlbum.E[StampAlbum.E.length - 1].role || null") == role


def test_heading_tick_box_marks_and_unmarks(page):
    _ready(page)
    _select_kind(page, "text")
    tid = page.evaluate("StampAlbum.sel")
    page.check("#phead")
    assert page.evaluate(f"StampAlbum.E.find(e => e.id === '{tid}').role") == "heading"
    page.uncheck("#phead")
    assert not page.evaluate(f"StampAlbum.E.find(e => e.id === '{tid}').role")
    page.evaluate("StampAlbum.undo()")
    assert page.evaluate(f"StampAlbum.E.find(e => e.id === '{tid}').role") == "heading"


def test_exports_receive_the_theme_and_heading_marks(page):
    _ready(page)
    page.select_option("#def-bdr", "solid")
    page.select_option("#def-theme", "maroon")
    _select_kind(page, "text")
    page.check("#phead")
    state = page.evaluate("StampAlbum.buildCanvasState('pdf')")
    assert state["theme_color"].upper() == "#7A1F2B"
    assert state["border_color"].upper() == "#7A1F2B"
    assert any(e.get("role") == "heading" for e in state["elements"])
