"""Check the editor's phrase lists against its code.

    python3 tools/i18n_check.py

Reports, and exits 1 if there are any:
- keys the page or the scripts use that en.json doesn't have;
- keys in en.json that nothing uses;
- English written straight into a script message (showToast, confirm, prompt,
  textContent, title, aria-label) instead of S.t("…");
- in another language: keys English doesn't have, placeholders that differ from
  English, plural forms without "other".
Phrases another language hasn't translated yet are counted, not errors: they
show in English.

src/tests/test_i18n.py runs this.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "src" / "stamp_album" / "web"
LOCALES = ROOT / "src" / "stamp_album" / "locales"
# Scripts the editor loads; generated and third-party files are left out.
SKIP = {"locales.js", "caption_metrics.js", "codemirror.min.js", "i18n.js"}

KEY = r"(?:ui|msg)\.[A-Za-z0-9_.]+"
HTML_KEYS = re.compile(r'data-i18n(?:-html)?="(' + KEY + ')"')
HTML_ATTR_KEYS = re.compile(r'data-i18n-attr="([^"]+)"')
JS_KEYS = re.compile(r'"(' + KEY + ')"')
# "msg.aligned_" + direction, (open ? "msg.hide_" : "msg.show_") + what: every key
# starting with the prefix counts as used.
JS_PREFIXES = re.compile(r'"((?:ui|msg)\.[A-Za-z0-9_.]*[_.])"')
# English written straight into something the user sees or hears.
UNTRANSLATED = re.compile(
    r"""(?:showToast|confirm|prompt)\(\s*["'][^"']*[A-Za-z]{2}"""
    r"""|\.(?:textContent|title|label)\s*=\s*["'][^"']*[A-Za-z]{2}"""
    r"""|setAttribute\(\s*["'](?:aria-label|title|placeholder|aria-description)["']\s*,\s*["'][^"']*[A-Za-z]{2}"""
)
PLACEHOLDER = re.compile(r"\{(\w+)\}")


def phrase_lists() -> dict[str, dict]:
    out = {}
    for path in sorted(LOCALES.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        out[path.stem] = {k: v for k, v in data.items() if not k.startswith("_")}
    return out


def used_keys() -> tuple[set[str], set[str]]:
    keys, prefixes = set(), set()
    html = (WEB / "index.html").read_text(encoding="utf-8")
    keys.update(HTML_KEYS.findall(html))
    for spec in HTML_ATTR_KEYS.findall(html):
        for pair in spec.split(";"):
            keys.add(pair.split(":", 1)[1].strip())
    for js in scripts():
        src = js.read_text(encoding="utf-8")
        prefixes.update(JS_PREFIXES.findall(src))
        keys.update(k for k in JS_KEYS.findall(src) if not k.endswith(("_", ".")))
    return keys, prefixes


def scripts() -> list[Path]:
    return [p for p in sorted(WEB.glob("*.js")) if p.name not in SKIP]


def placeholders(v) -> set[str]:
    vals = v.values() if isinstance(v, dict) else [v]
    return {name for s in vals for name in PLACEHOLDER.findall(s)} - {"count"}


def check() -> tuple[list[str], list[str]]:
    """(problems, notes)"""
    problems, notes = [], []
    lists = phrase_lists()
    en = lists.get("en", {})
    keys, prefixes = used_keys()

    for k in sorted(keys - set(en)):
        problems.append(f"en.json has no phrase for {k}")
    for k in sorted(set(en) - keys):
        if not any(k.startswith(p) for p in prefixes):
            problems.append(f"en.json: {k} is not used")
    for p in sorted(prefixes):
        if not any(k.startswith(p) for k in en):
            problems.append(f"en.json has no phrases starting {p}")

    for js in scripts():
        for n, line in enumerate(js.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("//"):
                continue
            if UNTRANSLATED.search(line):
                problems.append(f"{js.name}:{n}: English in a message; use S.t(…): "
                                f"{line.strip()[:90]}")

    for lang, phrases in lists.items():
        for k, v in phrases.items():
            if isinstance(v, dict) and "other" not in v:
                problems.append(f"{lang}.json: {k} has plural forms but no \"other\"")
        if lang == "en":
            continue
        for k in sorted(set(phrases) - set(en)):
            problems.append(f"{lang}.json: {k} is not an English key")
        for k in sorted(set(phrases) & set(en)):
            if placeholders(phrases[k]) != placeholders(en[k]):
                problems.append(f"{lang}.json: {k} placeholders {sorted(placeholders(phrases[k]))}"
                                f" differ from English {sorted(placeholders(en[k]))}")
        left = len(set(en) - set(phrases))
        notes.append(f"{lang}: {len(en) - left} of {len(en)} phrases translated")
    return problems, notes


if __name__ == "__main__":
    problems, notes = check()
    for n in notes:
        print(n)
    for p in problems:
        print("ERROR", p)
    if not problems:
        print(f"OK: {len(phrase_lists().get('en', {}))} English phrases, all used, none missing")
    sys.exit(1 if problems else 0)
