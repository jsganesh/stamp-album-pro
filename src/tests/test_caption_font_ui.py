# ruff: noqa: F811
"""The editor draws stamp captions in the bundled Source Serif 4 Caption, as wide as measured,
and the Headings control chooses Bold or Semibold for the whole album (one undo step)."""

import json

import pytest
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

SC = 2.5  # canvas px per mm
FAMILY = "Source Serif 4 Caption"
TEXTS = {
    "hdg": "Penny Black",
    "lbl": "Office fluff, check letters A–L",
    "denom": "1d",
    "cond": "Used",
    "perf": "Imperforate",
    "cat": "Cat. no. 1",
}


def _show(page, **kw):
    el = {"id": "s1", "t": "stamp", "s": "rectangle", "x": 40 * SC, "y": 60 * SC,
          "w": 40 * SC, "h": 30 * SC, "bdr": "solid", "bdrC": "#000000", "bdrW": 0.5,
          "fill": "#ffffff", "fillA": 100, "font": "CN", "fs": 12, **TEXTS, **kw}
    page.evaluate(
        """el => {
        StampAlbum.newAlbum();
        StampAlbum.E.length = 0;
        StampAlbum.E.push(el);
        StampAlbum.render();
        StampAlbum.resetUndo();
    }""",
        el,
    )
    _fonts_ready(page)


def _fonts_ready(page):
    for _ in range(200):
        if page.evaluate("document.fonts.status === 'loaded'"):
            return
        page.wait_for_timeout(25)
    raise TimeoutError("fonts did not load")


def _drawn(page):
    """Each drawn caption line: its kind, text, ink width (px), and computed font."""
    return page.evaluate(
        """() => [...document.querySelectorAll('.cel[data-id="s1"] .caption')].flatMap(n => {
            const cs = getComputedStyle(n);
            const kind = [...n.classList].find(c => c.startsWith('caption-')).slice(8);
            const node = n.firstChild, text = node.textContent, out = [];
            let start = 0;
            text.split('\\n').forEach(line => {
                const r = document.createRange();
                r.setStart(node, start); r.setEnd(node, start + line.length);
                out.push({kind, text: line, width: r.getBoundingClientRect().width,
                          family: cs.fontFamily, weight: cs.fontWeight, style: cs.fontStyle,
                          kerning: cs.fontKerning, ligatures: cs.fontVariantLigatures,
                          rendering: cs.textRendering});
                start += line.length + 1;
            });
            return out;
        })"""
    )


def _layout(page):
    return page.evaluate(
        """() => { const el = StampAlbum.E[0], sc = StampAlbum._sc;
            return StampAlbum.CORE.captionLayout(el, el.x / sc, el.y / sc, el.w / sc, el.h / sc,
                                                 null,
                                                 {headingWeight: StampAlbum._captionHeading}); }"""
    )


def test_the_caption_font_loads(page):
    _show(page)
    assert page.evaluate(f"document.fonts.check('8pt \"{FAMILY}\"')")
    assert page.evaluate(f"document.fonts.check('italic 8pt \"{FAMILY}\"')")
    assert page.evaluate(f"document.fonts.check('bold 9pt \"{FAMILY}\"')")
    loaded = page.evaluate(
        "[...document.fonts].filter(f => f.family.replace(/\"/g, '') === "
        + json.dumps(FAMILY) + " && f.status === 'loaded').map(f => f.weight + ' ' + f.style)"
    )
    assert {"400 normal", "400 italic", "700 normal"} <= set(loaded)
    assert page.js_errors == []


def test_captions_are_drawn_as_wide_as_measured(page):
    """The ink matches the advance widths the layout (and the exports) measured: right font,
    no kerning, no ligatures, whatever the stamp's own font (Courier here)."""
    _show(page)
    drawn, laid = _drawn(page), _layout(page)
    assert [(d["kind"], d["text"]) for d in drawn] == [(ln["kind"], ln["text"]) for ln in laid]
    for d, ln in zip(drawn, laid):
        assert FAMILY in d["family"]
        assert d["kerning"] == "none" and d["ligatures"] == "none"
        assert d["rendering"] == "geometricprecision"
        assert d["width"] == pytest.approx(ln["width"] * SC, abs=0.15), d["text"]
    weights = {d["kind"]: (d["weight"], d["style"]) for d in drawn}
    assert weights == {"heading": ("700", "normal"), "description": ("400", "normal"),
                       "details": ("400", "italic"), "catalogue": ("400", "italic")}


def test_headings_semibold_is_one_undo_step(page):
    _show(page)
    assert page.input_value("#def-heading") == "bold"
    page.select_option("#def-heading", "semibold")
    _fonts_ready(page)
    # The Semibold file loaded
    assert page.evaluate(f"document.fonts.check('600 9pt \"{FAMILY}\"')")
    heading = [d for d in _drawn(page) if d["kind"] == "heading"]
    laid = [ln for ln in _layout(page) if ln["kind"] == "heading"]
    assert heading and all(d["weight"] == "600" for d in heading)
    for d, ln in zip(heading, laid):
        assert d["width"] == pytest.approx(ln["width"] * SC, abs=0.15)
    assert page.evaluate("StampAlbum._dirty") is True
    assert 'CAPTION_HEADING("semibold")' in page.evaluate("StampAlbum.buildDSL()")
    page.evaluate("StampAlbum.undo()")
    assert page.input_value("#def-heading") == "bold"
    assert page.evaluate("StampAlbum._captionHeading") == "bold"
    assert all(d["weight"] == "700" for d in _drawn(page) if d["kind"] == "heading")
    page.evaluate("StampAlbum.redo()")
    assert page.input_value("#def-heading") == "semibold"
    assert page.js_errors == []


def test_opening_a_semibold_album_shows_semibold(page):
    page.evaluate(
        """dsl => { StampAlbum.parseDSL(dsl); }""",
        'ALBUM_PAGES_SIZE(210 297)\nCAPTION_HEADING("semibold")\nPAGE_START\n'
        'STAMP_ADD_AT(40 60 19 22 "Plate 1a" "" "" "")\n',
    )
    for _ in range(100):
        if page.evaluate("StampAlbum._captionHeading") == "semibold":
            break
        page.wait_for_timeout(25)
    assert page.input_value("#def-heading") == "semibold"


@pytest.mark.parametrize("route, call", [
    ("**/render-from-state", "StampAlbum.openPreview()"),
    ("**/export-from-state", "StampAlbum.exportPDF()"),
])
def test_preview_and_exports_get_the_heading_weight(page, route, call):
    _show(page)
    page.select_option("#def-heading", "semibold")
    sent = []

    def handle(r):
        sent.append(json.loads(r.request.post_data))
        r.fulfill(status=500, body="stop here")

    page.route(route, handle)
    page.evaluate(call)
    for _ in range(100):
        if sent:
            break
        page.wait_for_timeout(25)
    assert sent and sent[0]["caption_heading"] == "semibold"
