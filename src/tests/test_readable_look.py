# ruff: noqa: F811
"""The editor is easy to read and to operate for collectors who may not see small text well.

UI review items 4 and 9 (B1): text at least 14 px, buttons and fields at least 40 px tall,
line icons instead of emoji, and View › Text size (Standard, Large, Extra large) remembered
on the device. The album page, its captions and the exports keep their sizes at any text size.
"""

import re

import pytest
from test_accessibility import _axe, _fake_library, _stamp_album
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401  (fixtures)

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿■-◿\U0001F000-\U0001F2FF]")

# Visible text outside the album page: element, its size in px and its text.
TEXTS = """() => [...document.querySelectorAll('body *')].filter(e => {
    if (e.closest('#page-wrap, .icon-sprite, svg, script, style')) return false;
    if (!e.getClientRects().length || getComputedStyle(e).visibility === 'hidden') return false;
    return [...e.childNodes].some(n => n.nodeType === 3 && n.nodeValue.trim());
  }).map(e => [e.id || e.tagName + '.' + e.className, parseFloat(getComputedStyle(e).fontSize),
               [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.nodeValue)
                 .join('').trim()])"""

# Things you click or type in, outside the album page, and their height on screen.
CONTROLS = """() => [...document.querySelectorAll(
    'button, select, input:not([type=checkbox]):not([type=radio]):not([type=color])'
    + ':not([type=range]):not([type=file]), [role=button], [role=menuitem], [role=menuitemradio]')]
  .filter(e => !e.closest('#page-wrap') && e.getClientRects().length
               && getComputedStyle(e).visibility !== 'hidden')
  .map(e => [e.id || e.tagName + '.' + e.className, e.getBoundingClientRect().height])"""

# Small by design: the panel edge handles, the status bar's zoom percentage, and the
# delete cross that sits on an image thumbnail (the thumbnail itself is the 40 px button).
SMALL_OK = re.compile(r"^(sb-handle|rp-handle|sb-zoom|BUTTON\.img-del)$")


def _open_everything(page):
    _stamp_album(page)
    page.evaluate("StampAlbum.select('s1')")
    _fake_library(page)


def test_no_text_under_14px_outside_the_page(page):
    page.set_viewport_size({"width": 1440, "height": 900})
    _open_everything(page)
    small = [t for t in page.evaluate(TEXTS) if t[1] < 14 - 0.01]
    assert small == [], small


def test_buttons_and_fields_are_at_least_40px_tall(page):
    page.set_viewport_size({"width": 1440, "height": 900})
    _open_everything(page)
    for menu in ("file", "view"):
        page.click(f"#menu-{menu}-btn")
        short = [c for c in page.evaluate(CONTROLS) if c[1] < 40 - 0.5 and not SMALL_OK.match(c[0])]
        assert short == [], (menu, short)
        page.keyboard.press("Escape")


def test_no_emoji_anywhere_in_the_editor(page):
    _open_everything(page)
    html = page.evaluate("document.body.innerHTML")
    for opener in ("btn-wizard", "menu-template", "btn-help"):
        page.evaluate(f"document.getElementById('{opener}').click()")
    found = sorted(set(EMOJI.findall(html + page.evaluate("document.body.innerText"))))
    assert found == [], found


def test_icons_come_from_the_one_line_icon_set(page):
    missing = page.evaluate(
        """[...document.querySelectorAll('svg.ic use')].map(u => u.getAttribute('href'))
        .filter(h => !document.querySelector(h))"""
    )
    assert missing == []
    assert page.locator("#sidebar .p-item .icon svg.ic").count() == 11


def test_every_toolbar_button_has_a_word_at_1440(page):
    page.set_viewport_size({"width": 1440, "height": 900})
    words = page.evaluate(
        """['btn-undo', 'btn-redo', 'btn-preview', 'btn-export', 'btn-help-tb'].map(id =>
           document.getElementById(id).innerText.trim())"""
    )
    assert words == ["Undo", "Redo", "Preview", "Export", "Help"]


@pytest.mark.parametrize(("item", "scale", "root_px"), [
    ("standard", 1, 16), ("large", 1.25, 20), ("xlarge", 1.5, 24),
])
def test_text_size_scales_the_editor_but_not_the_page(page, item, scale, root_px):
    _stamp_album(page)
    page.evaluate("StampAlbum.setZoomMode('actual')")
    before = page.evaluate(
        "[document.getElementById('page').offsetWidth,"
        " getComputedStyle(document.querySelector('#page .cel .elbl')).fontSize]"
    )
    page.click("#menu-view-btn")
    page.click(f"#menu-text-{item}")
    assert page.evaluate("StampAlbum.textSize") == scale
    root = "parseFloat(getComputedStyle(document.documentElement).fontSize)"
    assert page.evaluate(root) == root_px
    tile = "parseFloat(getComputedStyle(document.querySelector('.p-item .lbl')).fontSize)"
    assert page.evaluate(tile) == pytest.approx(15 * scale)
    after = page.evaluate(
        "[document.getElementById('page').offsetWidth,"
        " getComputedStyle(document.querySelector('#page .cel .elbl')).fontSize]"
    )
    assert after == before, "the album page and its text keep their size"
    page.click("#menu-view-btn")
    checked = page.evaluate(
        "[...document.querySelectorAll('[id^=menu-text-]')]"
        ".filter(e => e.getAttribute('aria-checked') === 'true').map(e => e.id)"
    )
    assert checked == [f"menu-text-{item}"]


def test_text_size_is_remembered_after_a_restart(page):
    page.click("#menu-view-btn")
    page.click("#menu-text-large")
    page.reload()
    wait_for_app(page)
    assert page.evaluate("StampAlbum.textSize") == 1.25
    assert page.evaluate("parseFloat(getComputedStyle(document.documentElement).fontSize)") == 20


@pytest.mark.parametrize("item", ["large", "xlarge"])
def test_axe_at_larger_text_sizes(page, item):
    _open_everything(page)
    page.click("#menu-view-btn")
    page.click(f"#menu-text-{item}")
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)  # panel width transition
    assert _axe(page) == []


def test_not_saved_is_shown_in_words(page):
    _stamp_album(page)
    page.evaluate("StampAlbum._dirty = true; StampAlbum.updateTitle()")
    assert page.locator("#tb-dirty").is_visible()
    assert page.inner_text("#tb-dirty") == "Not saved"
    assert not page.inner_text("#file-name").startswith("●")


def test_add_page_says_so_in_words(page):
    add = page.get_by_role("button", name="Add page", exact=True)
    assert add.inner_text().strip() == "Add page"
