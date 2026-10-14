"""The editor's phrase lists.

web/locales.js is current, and tools/i18n_check.py passes and catches mistakes.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import i18n_check  # noqa: E402
import locales  # noqa: E402


def test_locales_js_is_current():
    """web/locales.js matches locales/*.json: rerun tools/locales.py if this fails."""
    assert locales.OUT.read_text(encoding="utf-8") == locales.source()


def test_phrase_lists_match_the_code():
    problems, _notes = i18n_check.check()
    assert problems == []


def test_english_has_every_kind_of_phrase():
    en = json.loads((locales.LOCALES / "en.json").read_text(encoding="utf-8"))
    assert en["msg.page_added"] == "Page added"
    assert en["msg.count_elements"] == {"one": "{count} element", "other": "{count} elements"}
    assert en["ui.new_album"] == "New album"
    assert "_comment" in en  # a note for translators, not shipped
    assert "_comment" not in locales.load()["en"]


@pytest.fixture()
def editor(tmp_path, monkeypatch):
    """A tiny editor for the checker: a page, a script and phrase lists."""
    web, loc = tmp_path / "web", tmp_path / "locales"
    web.mkdir()
    loc.mkdir()
    (web / "index.html").write_text(
        '<button data-i18n="ui.save">Save</button>'
        '<button data-i18n-attr="title:ui.undo_title;aria-label:ui.undo">x</button>',
        encoding="utf-8")
    monkeypatch.setattr(i18n_check, "WEB", web)
    monkeypatch.setattr(i18n_check, "LOCALES", loc)

    def write(script, en, **others):
        (web / "app.js").write_text(script, encoding="utf-8")
        for lang, phrases in {"en": en, **others}.items():
            (loc / f"{lang}.json").write_text(json.dumps(phrases), encoding="utf-8")
        return i18n_check.check()

    return write


EN = {"ui.save": "Save", "ui.undo": "Undo", "ui.undo_title": "Undo (⌘Z)",
      "msg.opened": "Opened {name}", "msg.aligned_left": "Aligned: left"}
SCRIPT = 'S.t("msg.opened", { name: f }); S.t("msg.aligned_" + d);'


def test_checker_passes_a_clean_editor(editor):
    problems, notes = editor(SCRIPT, EN,
                             de={"ui.save": "Speichern", "msg.opened": "{name} geöffnet"})
    assert problems == []
    assert notes == ["de: 2 of 5 phrases translated"]


def test_checker_finds_a_missing_phrase(editor):
    problems, _ = editor(SCRIPT + ' S.t("msg.new_thing");', EN)
    assert problems == ["en.json has no phrase for msg.new_thing"]


def test_checker_finds_an_unused_phrase(editor):
    problems, _ = editor(SCRIPT, {**EN, "msg.old": "Old"})
    assert problems == ["en.json: msg.old is not used"]


def test_checker_finds_a_missing_prefix(editor):
    en = {k: v for k, v in EN.items() if k != "msg.aligned_left"}
    problems, _ = editor(SCRIPT, en)
    assert problems == ["en.json has no phrases starting msg.aligned_"]


@pytest.mark.parametrize("line", [
    'showToast("Page added", "success");',
    'if (!confirm("Delete this element?")) return;',
    'el.textContent = "No selection";',
    'b.title = "Delete " + f;',
    'b.setAttribute("aria-label", "Open " + f);',
])
def test_checker_finds_english_in_a_script(editor, line):
    problems, _ = editor(SCRIPT + "\n" + line, EN)
    assert len(problems) == 1 and "English in a message" in problems[0], problems


def test_checker_allows_codes_and_comments(editor):
    script = SCRIPT + "\n".join(["", '// showToast("Like this", "info")', 'b.title = "";',
                                    'el.textContent = "✎ " + S.t("msg.opened");'])
    problems, _ = editor(script, EN)
    assert problems == []


def test_checker_finds_translation_mistakes(editor):
    problems, _ = editor(SCRIPT, EN, de={
        "msg.opened": "Geöffnet",             # lost {name}
        "msg.extra": "Nicht im Englischen",   # not an English key
        "ui.save": {"one": "Speichern"},      # plural forms need "other"
        "ui.undo": '<a href="x">Rückgängig</a>',  # only inline markup like <b>
    })
    assert sorted(problems) == sorted([
        "de.json: msg.extra is not an English key",
        "de.json: msg.opened placeholders [] differ from English ['name']",
        'de.json: ui.save has plural forms but no "other"',
        "de.json: ui.undo has markup other than b, br, em, i, kbd, strong: a",
    ])


def _marked(html):
    """(kind, key, English in the page) for every marked element of index.html."""
    import re
    from html.parser import HTMLParser

    void = {"meta", "link", "br", "img", "input", "hr"}
    found = []

    class P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []  # [attrs, own texts, inner start offset]

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            for pair in (a.get("data-i18n-attr") or "").split(";"):
                if pair:
                    name, key = pair.split(":", 1)
                    found.append(("attr " + name.strip(), key.strip(), a.get(name.strip())))
            if tag not in void:
                line, col = self.getpos()
                start = sum(len(x) for x in html.splitlines(True)[:line - 1]) + col
                self.stack.append([a, [], start + len(self.get_starttag_text())])

        def handle_endtag(self, tag):
            if tag in void or not self.stack:
                return
            a, texts, inner = self.stack.pop()
            if a.get("data-i18n"):
                own = [t for t in texts if t.strip()]
                text = re.sub(r"\s+", " ", own[0].strip()) if own else None
                found.append(("text", a["data-i18n"], text))
            if a.get("data-i18n-html"):
                line, col = self.getpos()
                end = sum(len(x) for x in html.splitlines(True)[:line - 1]) + col
                found.append(("html", a["data-i18n-html"], html[inner:end]))

        def handle_data(self, d):
            if self.stack:
                self.stack[-1][1].append(d)

    P().feed(html)
    return found


def test_page_english_matches_the_phrase_list():
    """index.html keeps its English, shown before i18n.js runs; it must be en.json's."""
    html = (i18n_check.WEB / "index.html").read_text(encoding="utf-8")
    en = locales.load()["en"]
    marked = _marked(html)
    assert len(marked) > 300
    wrong = [(kind, key, text, en.get(key)) for kind, key, text in marked if en.get(key) != text]
    assert wrong == []
    kinds = {kind for kind, _, _ in marked}
    assert kinds >= {"text", "html", "attr title", "attr aria-label", "attr placeholder",
                     "attr alt"}
