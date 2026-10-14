# ruff: noqa: F811
"""The editor in other languages, in a browser.

- English is the default, and every phrase the editor asks for exists.
- In the pseudo-language (?lang=pseudo: every phrase accented and about a third
  longer) no English is left in the editor's own words, and the layout still fits
  at 1024 px and on a phone.
- The computer's language is followed when there is a phrase list for it; the
  Language menu appears only then, and a choice there is remembered and takes
  effect at once, matching a fresh start in that language.
German isn't shipped yet, so these tests add a small German list of their own.
"""
import json
import os
import re
from pathlib import Path

import pytest
from test_ui_smoke import base_url, pw, wait_for_app  # noqa: F401

IPHONE = {"width": 390, "height": 664}

# A few German phrases, as a translator would write them; the rest fall back to English.
GERMAN = {
    "ui.file": "Datei", "ui.new_album": "Neues Album", "ui.view": "Ansicht",
    "ui.properties": "Eigenschaften",
    "ui.select_an_element_to_edit": "Element zum Bearbeiten auswählen",
    "msg.page_n_of": "Seite {n} von {total}", "msg.no_selection": "Keine Auswahl",
    "msg.count_elements": {"one": "{count} Element", "other": "{count} Elemente"},
    "msg.untitled": "Unbenannt", "msg.paper_orientation": "{paper} · {orientation}",
    "ui.portrait": "Hochformat", "msg.hide_sidebar": "Seitenleiste ausblenden",
}
ADD_GERMAN = "window.StampAlbumLocales = { de: %s };" % json.dumps(GERMAN)
EN = json.loads((Path(__file__).resolve().parents[1] / "stamp_album" / "locales" / "en.json")
                .read_text(encoding="utf-8"))
NO_TUTORIAL = "try { localStorage.setItem('stampalbum-tutorial-done', '1'); } catch (e) {}"


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as exc:
            if os.environ.get("STAMP_ALBUM_REQUIRE_BROWSER"):
                raise
            pytest.skip(f"chromium unavailable: {exc}")
        yield b
        b.close()


def _open(browser, base_url, query="", locale="en-US", german=False, viewport=None, phone=False):
    opts = {"locale": locale, "viewport": viewport or {"width": 1280, "height": 860}}
    if phone:
        opts.update(viewport=IPHONE, device_scale_factor=3, is_mobile=True, has_touch=True)
    ctx = browser.new_context(**opts)
    ctx.add_init_script(NO_TUTORIAL)
    if german:
        ctx.add_init_script(ADD_GERMAN)
    pg = ctx.new_page()
    pg.js_errors = []
    pg.on("pageerror", lambda e: pg.js_errors.append(str(e)))
    pg.goto(base_url + "/" + query)
    wait_for_app(pg)
    pg.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
    pg.wait_for_timeout(300)  # panels finish sliding (phone)
    return pg


def _add_stamp(pg):
    # Clicked by script: on a phone the palette starts hidden.
    pg.evaluate("document.querySelector('.p-item[data-s=rectangle]').click()")
    pg.wait_for_timeout(100)


def _lang(pg):
    return pg.evaluate("[document.documentElement.lang, StampAlbumI18n.language()]")


# ── English ──

def test_english_by_default_with_every_phrase(browser, base_url):
    pg = _open(browser, base_url)
    assert _lang(pg) == ["en", "en"]
    assert pg.inner_text("#btn-new") == "New album"
    assert pg.inner_text("#sb-page") == "Page 1 of 1"
    _add_stamp(pg)
    assert pg.inner_text("#sb-elements") == "1 element"
    for menu in ("file", "edit", "view"):
        pg.click(f"#menu-{menu}-btn")
        pg.keyboard.press("Escape")
    pg.click("#btn-page-setup")
    pg.click("#ps-cancel")
    assert pg.evaluate("StampAlbumI18n.missing()") == []
    # The tutorial's steps keep their bold words and line breaks, built from the phrases.
    rich = pg.evaluate("[...document.querySelectorAll('[data-i18n-html]')]"
                       ".map(e => [e.dataset.i18nHtml, e.innerHTML])")
    assert len(rich) == 4
    assert [html for _, html in rich] == [EN[key] for key, _ in rich]
    assert pg.js_errors == []


def test_phrases_cannot_add_other_markup(browser, base_url):
    key = "ui.add_stamps_at_their_catalogue"
    sneaky = {key: '<b>Marken</b><br><img src=x onerror="window.hacked=1"> <a href="#">Link</a>'}
    ctx = browser.new_context(locale="de-DE")
    ctx.add_init_script(NO_TUTORIAL)
    ctx.add_init_script("window.StampAlbumLocales = { de: %s };" % json.dumps(sneaky))
    pg = ctx.new_page()
    pg.goto(base_url + "/")
    wait_for_app(pg)
    step = pg.locator(f'[data-i18n-html="{key}"]')
    assert step.evaluate("e => [...e.querySelectorAll('*')].map(c => c.localName)") == ["b", "br"]
    assert '<img src=x onerror="window.hacked=1"> <a href="#">Link</a>' in step.text_content()
    assert pg.evaluate("window.hacked") is None
    ctx.close()


def test_language_menu_hidden_with_one_language(browser, base_url):
    pg = _open(browser, base_url, locale="de-DE")  # no German list is shipped yet
    assert _lang(pg) == ["en", "en"]
    assert pg.inner_text("#btn-new") == "New album"
    pg.click("#menu-view-btn")
    assert pg.evaluate("document.getElementById('menu-lang').hidden") is True
    assert pg.evaluate("document.querySelectorAll('#menu-lang .mi').length") == 0


# ── Pseudo-language: nothing left in English ──

# Not words to translate: the name, file formats, units, letters on axes, key names,
# numbers and percentages, font names.
NOT_WORDS = re.compile(
    r"^(StampAlbum( Pro)?|Stam.*|PDF|PNG|SVG|HTML|mm|pt|[XYWHB+−!?]|F5|Del|Esc|Tab|Enter|"
    r"(Ctrl|Shift|⌘|⇧)\S*|[\d\s%.,×:·–-]+|[◀▶▼▲]|"
    r"Helvetica.*|Times New Roman.*|Courier New.*|Arial.*|Georgia|Verdana|Trebuchet MS|Impact|"
    r"Comic Sans MS)$")
PSEUDO_MARK = re.compile(r"[àëïöüÿçñšžÀËÏÖÜŸÇÑŠŽ·\[\]]")

LEFTOVERS = """() => {
  const out = [];
  // The album itself, font names, the DSL, and lists of the user's files and templates.
  const skip = el => el.closest(
    '#page, #pfnt, .CodeMirror, #template-grid, #file-list, #img-list, #file-name');
  const visible = el => {
    const cs = getComputedStyle(el);
    return cs.display !== 'none' && cs.visibility !== 'hidden' && el.getClientRects().length;
  };
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = walk.nextNode());) {
    const el = n.parentElement, s = n.nodeValue.trim();
    if (!s || !/[A-Za-z]{2}/.test(s) || !el || skip(el) || !visible(el)) continue;
    if (el.closest('script,style')) continue;
    out.push(['text', s]);
  }
  for (const el of document.body.querySelectorAll('[title],[aria-label],[placeholder],[alt]')) {
    if (skip(el)) continue;
    for (const a of ['title', 'aria-label', 'placeholder', 'alt']) {
      const s = (el.getAttribute(a) || '').trim();
      if (s && /[A-Za-z]{2}/.test(s)) out.push([a + ' of #' + (el.id || el.className), s]);
    }
  }
  return out;
}"""


def _english_left(pg):
    return sorted({(where, s) for where, s in pg.evaluate(LEFTOVERS)
                   if not NOT_WORDS.match(s) and not PSEUDO_MARK.search(s)})


def _states(pg):
    """The editor's screens, one after another; yields each one's name."""
    yield "start"
    _add_stamp(pg)
    yield "stamp selected"
    for menu in ("file", "edit", "view"):
        pg.click(f"#menu-{menu}-btn")
        yield f"{menu} menu"
        pg.keyboard.press("Escape")
    for opener, closer, name in (("#btn-page-setup", "#ps-cancel", "page setup"),
                                 ("#btn-help-tb", None, "keyboard shortcuts")):
        pg.click(opener)
        yield name
        if closer:
            pg.click(closer)
        else:
            pg.keyboard.press("Escape")
            pg.evaluate("document.getElementById('help-overlay').classList.remove('open')")
    pg.evaluate("StampAlbum.openCalibration()")
    yield "calibration page"
    pg.evaluate("document.getElementById('calibration-overlay').classList.remove('open')")
    pg.evaluate("document.getElementById('wizard-panel').classList.add('open')")
    yield "wizard"
    pg.evaluate("document.getElementById('wizard-panel').classList.remove('open')")
    for step in range(1, 5):
        pg.evaluate("""step => { const o = document.getElementById('tutorial-overlay');
            o.classList.add('open');
            o.querySelectorAll('.tutorial-step').forEach(
                s => s.classList.toggle('active', s.dataset.step === String(step))); }""", step)
        yield f"tutorial step {step}"
    pg.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")


def test_pseudo_leaves_no_english(browser, base_url):
    pg = _open(browser, base_url, "?lang=pseudo")
    assert _lang(pg) == ["en-XA", "pseudo"]
    left = {}
    for state in _states(pg):
        found = _english_left(pg)
        if found:
            left[state] = found
    assert left == {}
    assert pg.evaluate("StampAlbumI18n.missing()") == []
    assert pg.js_errors == []


def test_lang_in_address_is_not_remembered(browser, base_url):
    pg = _open(browser, base_url, "?lang=pseudo")
    assert pg.evaluate("localStorage.getItem('stampalbum-lang')") is None


# ── Pseudo-language: longer words still fit ──

OVERFLOW = """() => {
  const vw = document.documentElement.clientWidth, out = [];
  const sw = document.documentElement.scrollWidth;
  if (sw > vw) out.push('page scrolls sideways: ' + sw + ' > ' + vw);
  const parts = '#tb *, #ca-toolbar *, #rp *, #sidebar *, #status-bar *, .tb-menu-list *';
  for (const el of document.querySelectorAll(parts)) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (!el.getClientRects().length || el.closest('#sidebar.collapsed, #rp.collapsed')) continue;
    const r = el.getBoundingClientRect();
    const name = el.id || el.getAttribute('class') || el.tagName;
    if (r.right > vw + 1) out.push('past the window: ' + name);
    // Words cut off by a box that hides its overflow (the selection may shorten with "…")
    if (el.id !== 'sb-selection' && el.children.length === 0 && /\\S/.test(el.textContent) &&
        ['hidden', 'clip'].includes(cs.overflowX) && el.scrollWidth > el.clientWidth + 1)
      out.push('cut off: ' + name);
  }
  return out;
}"""


@pytest.mark.parametrize("where", ["1024", "phone"])
def test_pseudo_fits(browser, base_url, where):
    if where == "phone":
        pg = _open(browser, base_url, "?lang=pseudo", phone=True)
    else:
        pg = _open(browser, base_url, "?lang=pseudo", viewport={"width": 1024, "height": 768})
    problems = {}
    for state in ("start", "stamp selected", "file menu", "view menu"):
        if state == "stamp selected":
            if where == "phone":
                pg.click("#rp-handle")
                pg.wait_for_timeout(300)
            _add_stamp(pg)
        elif state.endswith("menu"):
            pg.keyboard.press("Escape")
            pg.click(f"#menu-{state.split()[0]}-btn")
        found = pg.evaluate(OVERFLOW)
        if found:
            problems[state] = found
    assert problems == {}


# ── The computer's language, and choosing one ──

def test_follows_the_computer_language(browser, base_url):
    pg = _open(browser, base_url, locale="de-AT", german=True)
    assert _lang(pg) == ["de", "de"]
    assert pg.inner_text("#btn-new") == "Neues Album"
    assert pg.inner_text("#sb-page") == "Seite 1 von 1"
    assert pg.inner_text("#btn-page-setup") == "A4 · Hochformat"
    # A phrase the German list doesn't have: English
    assert pg.evaluate("document.getElementById('menu-add-page').textContent") == "Add page"
    _add_stamp(pg)
    assert pg.inner_text("#sb-elements") == "1 Element"
    pg.click("#menu-view-btn")
    assert pg.evaluate("document.getElementById('menu-lang').hidden") is False
    items = pg.evaluate("[...document.querySelectorAll('#menu-lang .mi')]"
                        ".map(b => [b.textContent, b.getAttribute('aria-checked'), b.lang])")
    assert items == [["English", "false", "en"], ["Deutsch", "true", "de"]]
    assert pg.js_errors == []


def _chrome_words(pg):
    return sorted(s for _, s in pg.evaluate(LEFTOVERS))


def test_choosing_a_language_is_remembered_and_complete(browser, base_url):
    pg = _open(browser, base_url, locale="de-DE", german=True)
    _add_stamp(pg)
    pg.click("#menu-view-btn")
    pg.click("#menu-lang-en")
    assert _lang(pg) == ["en", "en"]
    assert pg.inner_text("#btn-new") == "New album"
    assert pg.inner_text("#sb-elements") == "1 element"
    assert pg.evaluate("StampAlbum.E.length") == 1  # the album is untouched
    assert pg.evaluate("localStorage.getItem('stampalbum-lang')") == "en"
    switched = _chrome_words(pg)

    # A fresh start in English with the same album shows exactly the same words.
    fresh = _open(browser, base_url, locale="en-US")
    _add_stamp(fresh)
    assert switched == _chrome_words(fresh)

    # And the choice is kept on this device, over the computer's German.
    pg.reload()
    wait_for_app(pg)
    assert _lang(pg) == ["en", "en"]
    pg.click("#menu-view-btn")
    pg.click("#menu-lang-de")
    assert pg.inner_text("#btn-new") == "Neues Album"
    assert pg.evaluate("localStorage.getItem('stampalbum-lang')") == "de"
    assert pg.js_errors == []
