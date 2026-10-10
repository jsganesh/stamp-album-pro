"""Accessibility tests for the web editor.

Two kinds of check:
- an automated axe-core scan of the editor and its dialogs, so new markup
  without a label or name fails CI;
- keyboard and screen-reader behaviour axe cannot see: every sidebar item,
  page dot and element on the page can be reached and used without a mouse.

Like the smoke tests, these skip without Playwright or Chromium unless
STAMP_ALBUM_REQUIRE_BROWSER=1 (CI) is set, in which case they fail instead.
"""
# The browser fixtures come from test_ui_smoke; pytest passes them in as arguments.
# ruff: noqa: F811
import json
import os
import re

import pytest
from test_ui_smoke import _els, _empty_album, base_url, page  # noqa: F401  (fixtures)

try:
    from axe_playwright_python.sync_playwright import Axe
except ImportError as exc:
    if os.environ.get("STAMP_ALBUM_REQUIRE_BROWSER"):
        raise ImportError(f"STAMP_ALBUM_REQUIRE_BROWSER is set but axe-playwright-python is not installed: {exc}") from exc
    pytest.skip(f"axe-playwright-python not installed: {exc}", allow_module_level=True)

# 1x1 transparent PNG, served for fake library images
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)


# ── Helpers ──

def _stamp_album(page, n=2):
    """A fresh album with n stamps in a row, the first selected, grid 5 mm."""
    pushes = "".join(
        "StampAlbum.E.push({id: 's%d', t: 'stamp', s: 'rectangle', x: %d, y: 100, w: 100, h: 75, lbl: 'stamp %d'});"
        % (i + 1, 100 + i * 150, i + 1) for i in range(n))
    page.evaluate("StampAlbum.newAlbum(); StampAlbum._snapEnabled = false;" + pushes + "StampAlbum.render()")
    page.select_option("#grid", "5")


def _el(page, el_id):
    return page.evaluate(f"(() => {{ const e = StampAlbum.E.find(e => e.id === '{el_id}'); return {{x: e.x, y: e.y}}; }})()")


def _focused(page):
    return page.evaluate("(() => { const a = document.activeElement; return {id: a.id, cel: a.dataset ? a.dataset.id || null : null,"
                         " cls: a.className, name: a.getAttribute('aria-label') || a.textContent.trim()}; })()")


def _fake_library(page, images=("stamp1.png",), files=("my album.slbum",)):
    page.route("**/images", lambda r: r.fulfill(json=list(images)))
    page.route(re.compile(r".*/images/[^/]+$"), lambda r: r.fulfill(body=PNG, content_type="image/png"))
    page.route("**/files", lambda r: r.fulfill(json=list(files)))
    page.evaluate("StampAlbum.loadImageList(); StampAlbum.loadFileList()")
    page.wait_for_selector(".img-item")
    page.wait_for_selector(".file-item")


def _axe(page, context=None):
    # Let fades and transitions finish first: mid-fade text is part-transparent, which axe
    # reports as low contrast (the palette hint fading in failed this on fast CI runners).
    page.evaluate("Promise.all(document.getAnimations().map(a => a.finished.catch(() => null)))")
    res = Axe().run(page, context=context, options={"resultTypes": ["violations"]})
    return ["%s (%s): %s" % (v["id"], v["impact"], [n["target"] for n in v["nodes"]][:6])
            for v in res.response["violations"]]


# ── Automated axe-core scan ──

def test_axe_editor_with_a_selected_stamp(page):
    _stamp_album(page)
    page.evaluate("StampAlbum.select('s1')")
    _fake_library(page)
    assert _axe(page) == []


OPENERS = {
    "wizard": "document.getElementById('btn-wizard').click()",
    "dsl editor": "document.getElementById('btn-dsl').click()",
    "page setup": "document.getElementById('btn-page-setup').click()",
    "keyboard shortcuts": "document.getElementById('help-overlay').classList.add('open')",
    "template gallery": "document.getElementById('btn-wiz-template').click()",
}


@pytest.mark.parametrize("dialog", list(OPENERS))
def test_axe_dialogs(page, dialog):
    page.route("**/api/templates", lambda r: r.fulfill(json=[{"id": "t1", "name": "Plain", "description": "One page", "category": "Basic"}]))
    page.evaluate(OPENERS[dialog])
    page.wait_for_timeout(200)
    assert _axe(page) == []


# ── Names and labels ──

PROPERTY_LABELS = {
    "px": "X position", "py": "Y position", "pw": "Width", "ph": "Height",
    "pbs": "Frame", "phead": "Mark as heading", "plbl": "Label", "pfnt": "Font", "pfs": "Font size",
    "phdg": "Heading", "pcat": "Catalogue number", "pdenom": "Denomination",
    "pcond": "Condition", "pperf": "Perforation",
}


@pytest.mark.parametrize("field,label", PROPERTY_LABELS.items())
def test_properties_inputs_are_found_by_their_label(page, field, label):
    _stamp_album(page)
    page.evaluate("StampAlbum.select('s1')")
    found = page.get_by_label(label, exact=True)
    assert found.count() == 1, label
    assert found.get_attribute("id") == field


def test_wizard_fields_are_found_by_their_label(page):
    for label, field in [("Album title", "wiz-title"), ("Author", "wiz-author"), ("Page size", "wiz-pg-size"),
                         ("Orientation", "wiz-orient"), ("Template", "wiz-template")]:
        assert page.get_by_label(label, exact=True).get_attribute("id") == field, label


def test_every_button_has_a_spoken_name_with_words(page):
    """No button may be named only by a symbol such as ✕, ↻ or an emoji."""
    _stamp_album(page)
    page.evaluate("StampAlbum.select('s1')")
    _fake_library(page)
    bad = page.evaluate("""() => [...document.querySelectorAll('button, [role=button]')].map(b => {
        let name = b.getAttribute('aria-label');
        if (!name) {
            const c = b.cloneNode(true);
            c.querySelectorAll('[aria-hidden=true]').forEach(n => n.remove());
            name = c.textContent.trim();
        }
        return [b.id || b.className, name];
    }).filter(([_, n]) => !/^[A-Za-z0-9]/.test(n) || /[^\\x00-\\x7F·×…—–’]/.test(n))""")
    assert bad == []


# ── Keyboard access: sidebar ──

def test_images_panel_items_are_named_buttons_that_add_at_the_centre(page):
    _empty_album(page)
    _fake_library(page)
    add = page.get_by_role("button", name="Add image stamp1.png", exact=True)
    assert add.count() == 1
    add.focus()
    page.keyboard.press("Enter")
    els = _els(page)
    assert [e["t"] for e in els] == ["image"], els
    pw_, ph_ = page.evaluate("[StampAlbum._pw, StampAlbum._ph]")
    cx, cy = els[0]["x"] + els[0]["w"] / 2, els[0]["y"] + els[0]["h"] / 2
    assert abs(cx - pw_ / 2) < 15 and abs(cy - ph_ / 2) < 15, els


def test_image_delete_button_is_named_and_shown_on_keyboard_focus(page):
    _fake_library(page)
    dele = page.get_by_role("button", name="Delete image stamp1.png", exact=True)
    assert dele.count() == 1
    dele.focus()
    assert dele.is_visible()


def test_file_list_items_open_and_delete_by_keyboard(page):
    _fake_library(page)
    assert page.get_by_role("button", name="Open my album.slbum", exact=True).count() == 1
    dele = page.get_by_role("button", name="Delete my album.slbum", exact=True)
    assert dele.count() == 1
    dele.focus()
    assert dele.is_visible()


def test_upload_image_is_a_button(page):
    assert page.locator("#img-upl-btn").evaluate("e => e.tagName") == "BUTTON"


@pytest.mark.parametrize("toggle,body", [("img-toggle", "img-body"), ("file-toggle", "file-body"), ("imp-toggle", "imp-body")])
def test_section_toggles_are_buttons_that_report_their_state(page, toggle, body):
    t = page.locator("#" + toggle)
    assert t.evaluate("e => e.tagName") == "BUTTON"
    assert t.get_attribute("aria-expanded") == "true"
    assert t.get_attribute("aria-controls") == body
    t.focus()
    page.keyboard.press("Enter")
    assert t.get_attribute("aria-expanded") == "false"
    assert not page.locator("#" + body).is_visible()
    page.keyboard.press("Space")
    assert t.get_attribute("aria-expanded") == "true"


def test_collapsed_sidebar_can_be_reopened_by_keyboard(page):
    page.locator("#sb-toggle").focus()
    page.keyboard.press("Enter")
    assert page.evaluate("StampAlbum._collapsed.sb") is True
    handle = page.get_by_role("button", name="Show the sidebar", exact=True)
    handle.focus()
    page.keyboard.press("Enter")
    assert page.evaluate("StampAlbum._collapsed.sb") is False
    assert page.get_by_role("button", name="Hide the sidebar", exact=True).count() >= 1


def test_page_dots_are_named_buttons(page):
    _stamp_album(page)
    dots = page.locator("#pg-dots button")
    assert dots.count() == 2
    p1 = page.get_by_role("button", name="Page 1", exact=True)
    assert p1.get_attribute("aria-current") == "page"
    page.get_by_role("button", name="Add page", exact=True).focus()
    page.keyboard.press("Enter")
    assert page.evaluate("StampAlbum._pages.length") == 2
    assert page.get_by_role("button", name="Page 2", exact=True).get_attribute("aria-current") == "page"
    page.get_by_role("button", name="Page 1", exact=True).focus()
    page.keyboard.press("Enter")
    assert page.evaluate("StampAlbum._currentPage") == 0
    assert page.get_by_role("button", name="Delete current page", exact=True).count() == 1


def test_template_cards_open_by_keyboard(page):
    page.route("**/api/templates", lambda r: r.fulfill(json=[{"id": "t1", "name": "Plain", "description": "One page", "category": "Basic"}]))
    page.route("**/api/templates/t1", lambda r: r.fulfill(json={"name": "Plain", "dsl": 'PAGE_SIZE(210 297)\nSTAMP_ADD_AT(20 20 40 30 "x" "" "" "")'}))
    page.evaluate("document.getElementById('btn-wiz-template').click()")
    card = page.get_by_role("button", name=re.compile("^Plain"))
    card.wait_for()
    card.focus()
    page.keyboard.press("Enter")
    for _ in range(50):
        if len(_els(page)) == 1:
            break
        page.wait_for_timeout(100)
    assert len(_els(page)) == 1


def test_preview_export_items_are_reachable_by_keyboard(page):
    items = page.locator("#btn-preview-export-dd .export-dd-item")
    assert items.count() == 4
    for i in range(4):
        assert items.nth(i).get_attribute("role") == "menuitem"
        assert items.nth(i).get_attribute("tabindex") == "0"


# ── Keyboard access: elements on the page ──

def test_elements_on_the_page_are_named_tab_stops(page):
    _stamp_album(page)
    cel = page.locator(".cel[data-id='s1']")
    assert cel.get_attribute("tabindex") == "0"
    name = cel.get_attribute("aria-label") or ""
    assert "Rectangle stamp" in name and "stamp 1" in name and "40 × 30 mm" in name and "40, 40 mm" in name, name


def test_focusing_an_element_selects_it(page):
    _stamp_album(page)
    page.focus(".cel[data-id='s2']")
    assert page.evaluate("StampAlbum.sel") == "s2"
    assert page.locator("#rp-content").is_visible()
    assert page.locator(".cel[data-id='s2']").get_attribute("aria-current") == "true"
    assert _focused(page)["cel"] == "s2"


def test_tab_moves_between_elements_and_selects_each(page):
    _stamp_album(page, n=3)
    page.focus(".cel[data-id='s1']")
    page.keyboard.press("Tab")
    f = _focused(page)
    if f["cel"] != "s2":  # the stamp label is an editable text stop inside the element
        page.keyboard.press("Tab")
        f = _focused(page)
    assert f["cel"] == "s2", f
    assert page.evaluate("StampAlbum.sel") == "s2"


def test_arrow_keys_nudge_by_the_grid_and_keep_focus(page):
    _stamp_album(page)
    page.focus(".cel[data-id='s1']")
    x0, y0 = _el(page, "s1")["x"], _el(page, "s1")["y"]
    sc = page.evaluate("StampAlbum._sc")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowDown")
    e = _el(page, "s1")
    assert (e["x"] - x0, e["y"] - y0) == (pytest.approx(5 * sc), pytest.approx(5 * sc))
    assert _focused(page)["cel"] == "s1"
    page.keyboard.press("ArrowLeft")
    assert _el(page, "s1")["x"] == pytest.approx(x0)


def test_shift_arrow_nudges_10mm_and_1mm_without_a_grid(page):
    _stamp_album(page)
    page.select_option("#grid", "0")
    page.focus(".cel[data-id='s1']")
    x0 = _el(page, "s1")["x"]
    sc = page.evaluate("StampAlbum._sc")
    page.keyboard.press("ArrowRight")
    assert _el(page, "s1")["x"] - x0 == pytest.approx(1 * sc)
    page.keyboard.press("Shift+ArrowRight")
    assert _el(page, "s1")["x"] - x0 == pytest.approx(11 * sc)


def test_nudge_stays_inside_the_page(page):
    _stamp_album(page, n=1)
    page.focus(".cel[data-id='s1']")
    for _ in range(80):
        page.keyboard.press("Shift+ArrowLeft")
    assert _el(page, "s1")["x"] == 0
    assert _focused(page)["cel"] == "s1"


def test_each_nudge_is_one_undo_step(page):
    _stamp_album(page)
    page.focus(".cel[data-id='s1']")
    x0 = _el(page, "s1")["x"]
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    page.evaluate("StampAlbum.undo()")
    assert _el(page, "s1")["x"] == pytest.approx(x0 + 5 * page.evaluate("StampAlbum._sc"))


def test_arrows_nudge_the_selection_after_a_mouse_click(page):
    _stamp_album(page)
    box = page.locator(".cel[data-id='s1']").bounding_box()
    page.mouse.click(box["x"] + 10, box["y"] + box["height"] - 8)
    x0 = _el(page, "s1")["x"]
    page.keyboard.press("ArrowRight")
    assert _el(page, "s1")["x"] > x0


def test_arrows_in_a_form_field_do_not_move_the_element(page):
    _stamp_album(page)
    page.evaluate("StampAlbum.select('s1')")
    x0 = _el(page, "s1")["x"]
    page.focus("#plbl")
    page.keyboard.press("ArrowLeft")
    page.focus("#grid")
    page.keyboard.press("ArrowDown")
    assert _el(page, "s1")["x"] == x0


def test_enter_on_an_element_moves_to_its_properties(page):
    _stamp_album(page)
    page.focus(".cel[data-id='s1']")
    page.keyboard.press("Enter")
    assert _focused(page)["id"] == "px"


def test_escape_deselects_but_keeps_focus_on_the_page(page):
    _stamp_album(page)
    page.focus(".cel[data-id='s1']")
    page.keyboard.press("Escape")
    assert page.evaluate("StampAlbum.sel") is None
    assert _focused(page)["cel"] == "s1"


def test_backspace_while_editing_a_label_does_not_delete_the_element(page):
    _stamp_album(page, n=1)
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))
    page.evaluate("StampAlbum.select('s1')")
    lbl = page.locator(".cel[data-id='s1'] .elbl")
    lbl.focus()
    assert page.evaluate("StampAlbum.sel") == "s1"
    page.keyboard.press("End")
    page.keyboard.press("Backspace")
    assert dialogs == [] and len(_els(page)) == 1


def test_delete_key_removes_the_focused_element_and_focus_moves_on(page):
    _stamp_album(page)
    page.on("dialog", lambda d: d.accept())
    page.focus(".cel[data-id='s1']")
    page.keyboard.press("Delete")
    assert [e["id"] for e in _els(page)] == ["s2"]
    assert _focused(page)["cel"] == "s2"


def test_focus_is_visible_on_keyboard_targets(page):
    _stamp_album(page)
    _fake_library(page)
    for sel in [".p-item", ".cel[data-id='s1']", ".img-add", "#pg-dots button", "#img-toggle", "#img-upl-btn"]:
        page.keyboard.press("Tab")  # keyboard in use (modifier keys alone do not count), as when tabbing
        page.focus(sel)
        page.wait_for_timeout(250)  # palette items animate their outline in (transition: all 0.15s)
        style = page.evaluate("(() => { const s = getComputedStyle(document.activeElement); return [s.outlineStyle, s.outlineWidth]; })()")
        assert style[0] != "none" and style[1] != "0px", (sel, style)


def test_page_has_a_name(page):
    assert page.locator("#page").get_attribute("aria-label") == "Album page"


def test_no_js_errors_during_keyboard_use(page):
    _stamp_album(page)
    page.focus(".cel[data-id='s1']")
    for k in ["ArrowRight", "Shift+ArrowDown", "Tab", "Escape", "Enter"]:
        page.keyboard.press(k)
    assert page.js_errors == []
    json.dumps(_els(page))
