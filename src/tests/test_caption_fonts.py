"""Stamp captions are set in the bundled Source Serif 4 Caption, measured the same way everywhere.

The editor (web/dsl_core.js with web/caption_metrics.js) and the exports
(engines/caption_fonts.py) measure with the fonts' own advance widths, so a caption
breaks in the same places in the editor, the preview, and the PDF, PNG and SVG exports.
The album chooses Bold or Semibold headings (CAPTION_HEADING).
"""

import base64
import io
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fontTools.ttLib import TTFont
from PIL import Image

from stamp_album.api import app
from stamp_album.core.models import Stamp, StampHeading
from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.engines import caption_fonts, caption_layout

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "src" / "stamp_album" / "web"
SC = 2.5

# Captions that wrap near the frame's width, odd punctuation, and characters the font lacks.
SAMPLES = [
    "Penny Black on cover",
    "1d · Used · Imperforate",
    "Plate 1a, check letters A–L, lightly cancelled",
    "Cat. no. 2 · Ref. 1 · No. 14a",
    "Office fluff: “quoted” — dashes, ½ and ¾, fi fl ffi",
    "Ελλάς · Россия · Österreich · Ærø",
    "日本 ₹ 🙂",
    "Averyveryverylongwordthatcannotfitonalineatall",
]
WIDTHS = [21.4, 27.4, 42.4]  # frame widths of 19, 25 and 40 mm stamps with a thin frame


def _node():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    return node


def _run_node(script: str):
    out = subprocess.run(
        [_node(), "-e", script], capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout
    return json.loads(out)


def _stamp(**kw):
    s = Stamp(width=kw.get("w", 19.0), height=22.0)
    s.description = kw.get("description", "")
    s.footer_text = kw.get("details", "")
    s.catalog_refs = kw.get("catalog_refs", [])
    s.font_id = kw.get("font_id", "HN")
    if kw.get("heading"):
        s.heading = StampHeading(text=kw["heading"], font_id="HN", size=9.0)
    return s


def _export(fmt, caption_heading=None, el=None):
    el = el or {
        "t": "stamp", "s": "rectangle", "x": 40 * SC, "y": 60 * SC, "w": 19 * SC, "h": 22 * SC,
        "bdr": "solid", "bdrC": "#000000", "bdrW": 0.5, "fill": "#ffffff", "fillA": 100,
        "font": "HN", "fs": 12, "hdg": "Penny Black", "lbl": "Plate 1a", "denom": "1d",
        "cond": "Used", "perf": "Imperforate", "cat": "SG 2",
    }
    state = {"elements": [el], "pages": [], "page_width_px": 210 * SC, "page_height_px": 297 * SC,
             "scale": SC, "format": fmt, "source_path": "t.slbum"}
    if caption_heading:
        state["caption_heading"] = caption_heading
    url = "/render-from-state" if fmt == "html" else "/export-from-state"
    r = TestClient(app).post(url, json=state)
    assert r.status_code == 200, r.text
    return r.content


# ── The bundled files ──


def test_the_four_fonts_and_their_licence_are_bundled():
    names = sorted(p.name for p in (WEB / "fonts").iterdir())
    assert names == [
        "OFL.txt",
        "SourceSerif4Caption-Bold.ttf",
        "SourceSerif4Caption-It.ttf",
        "SourceSerif4Caption-Regular.ttf",
        "SourceSerif4Caption-Semibold.ttf",
    ]
    assert "SIL Open Font License" in (WEB / "fonts" / "OFL.txt").read_text(encoding="utf-8")
    for fid, (_, weight, style) in caption_fonts.FONTS.items():
        with TTFont(str(caption_fonts.path(fid))) as tt:
            assert tt["name"].getDebugName(1).startswith("Source Serif 4 Caption")
            assert tt["OS/2"].usWeightClass == weight
            assert bool(tt["head"].macStyle & 2) == (style == "italic")
            assert tt["OS/2"].fsType == 0  # embedding allowed (PDF, SVG and HTML embed it)
    assert "*.ttf" in (ROOT / "MANIFEST.in").read_text(encoding="utf-8")


def test_the_editor_metrics_are_up_to_date():
    """web/caption_metrics.js matches the TTFs: rerun tools/caption_metrics.py if this fails."""
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import caption_metrics
    finally:
        sys.path.pop(0)
    assert (WEB / "caption_metrics.js").read_text(encoding="utf-8") == caption_metrics.source()


def test_font_route_serves_only_the_fonts():
    client = TestClient(app)
    r = client.get("/fonts/SourceSerif4Caption-Regular.ttf")
    assert r.status_code == 200 and r.headers["content-type"] == "font/ttf"
    assert r.content == caption_fonts.path("CapR").read_bytes()
    for bad in ("/fonts/OFL.txt", "/fonts/missing.ttf", "/fonts/..%2Fapp.js", "/fonts/..%5Capi.py"):
        assert client.get(bad).status_code == 404, bad


# ── One measure everywhere ──


def test_measure_is_reportlabs_width():
    """The PDF draws the advance widths the layout measured."""
    from reportlab.pdfbase import pdfmetrics

    for fid in caption_fonts.FONTS:
        for text in SAMPLES:
            want = pdfmetrics.stringWidth(text, caption_fonts.reportlab_name(fid), 8) * 25.4 / 72
            got = caption_fonts.measure(text, fid, 8)
            assert got == pytest.approx(want, rel=1e-12), (fid, text)


def test_editor_measures_like_the_exports():
    core = WEB / "dsl_core.js"
    script = (
        f"const c = require({json.dumps(str(core))});"
        f"const ids = {json.dumps(list(caption_fonts.FONTS))}, texts = {json.dumps(SAMPLES)};"
        "console.log(JSON.stringify(ids.map(f => texts.map(t => c.captionMeasure(t, f, 8)))));"
    )
    js = _run_node(script)
    for fi, fid in enumerate(caption_fonts.FONTS):
        for ti, text in enumerate(SAMPLES):
            want = caption_fonts.measure(text, fid, 8)
            assert js[fi][ti] == pytest.approx(want, rel=1e-12), (fid, text)


@pytest.mark.parametrize("weight", ["bold", "semibold"])
def test_editor_breaks_lines_like_the_exports(weight):
    """captionLayout (dsl_core.js) and caption_layout.layout break every sample alike."""
    core = WEB / "dsl_core.js"
    cases = []
    for w in WIDTHS:
        stamp_w = w - 2 * (1.0 + 0.5 * 25.4 / 72)  # the stamp inside a thin frame
        for text in SAMPLES:
            cases.append({"w": stamp_w, "text": text})
    script = (
        f"const c = require({json.dumps(str(core))});"
        f"const cases = {json.dumps(cases)};"
        "console.log(JSON.stringify(cases.map(k => c.captionLayout("
        "{t: 'stamp', bdr: 'solid', bdrW: 0.5,"
        " hdg: k.text, lbl: k.text, denom: k.text, cat: k.text},"
        f" 20, 60, k.w, 22, null, {{headingWeight: {json.dumps(weight)}}})"
        ".map(l => [l.kind, l.text, l.fontId, l.x]))));"
    )
    js = _run_node(script)
    for case, got in zip(cases, js):
        s = _stamp(w=case["w"], heading=case["text"], description=case["text"],
                   details=case["text"], catalog_refs=[case["text"]])
        py = caption_layout.layout(s, 20, 60, case["w"], 22, heading_weight=weight)
        assert [(k, t, f) for k, t, f, _ in got] == [(p.kind, p.text, p.font_id) for p in py], case
        assert [x for *_, x in got] == pytest.approx([p.x for p in py])


def test_the_caption_cut_wraps_where_helvetica_did_not():
    """Item 6: the exports measured Helvetica; a line that fitted there wraps now, everywhere."""
    s = _stamp(w=19.0, description="Plate 1a check letters")
    lines = [ln.text for ln in caption_layout.layout(s, 20, 60, 19.0, 22.0)]
    assert lines == ["Plate 1a check", "letters"]


# ── The exports ──


def test_pdf_embeds_the_caption_font():
    pdf = _export("pdf")
    fonts = set(re.findall(rb"/BaseFont\s*/[A-Z]{6}\+([\w-]+)", pdf))
    want = {b"SourceSerif4Caption-Bold", b"SourceSerif4Caption-Regular", b"SourceSerif4Caption-It"}
    assert want <= fonts


def test_pdf_semibold_headings():
    pdf = _export("pdf", caption_heading="semibold")
    fonts = set(re.findall(rb"/BaseFont\s*/[A-Z]{6}\+([\w-]+)", pdf))
    assert b"SourceSerif4Caption-Semibold" in fonts and b"SourceSerif4Caption-Bold" not in fonts


def test_png_captions_do_not_depend_on_system_fonts(monkeypatch):
    """The PNG draws captions from the bundled files, so a machine's fonts make no difference."""
    from PIL import ImageFont

    from stamp_album.engines import system_fonts

    caption_fonts._pillow_font.cache_clear()
    normal = Image.open(io.BytesIO(_export("png"))).convert("L")

    real = ImageFont.truetype

    def only_bundled(font, *a, **k):
        if not str(font).startswith(str(caption_fonts.FONT_DIR)):
            raise OSError("no system fonts here")
        return real(font, *a, **k)

    monkeypatch.setattr(ImageFont, "truetype", only_bundled)
    monkeypatch.setattr(system_fonts, "font_dirs", lambda: [])
    system_fonts.clear_cache()
    caption_fonts._pillow_font.cache_clear()
    try:
        bare = Image.open(io.BytesIO(_export("png"))).convert("L")
    finally:
        caption_fonts._pillow_font.cache_clear()
        system_fonts.clear_cache()
    ppm = normal.width / 210
    # The stamp and its captions
    band = (int(15 * ppm), int(45 * ppm), int(85 * ppm), int(105 * ppm))
    assert normal.crop(band).tobytes() == bare.crop(band).tobytes()
    assert normal.crop(band).getextrema()[0] < 40  # and the captions are there


def _embedded_faces(css: str) -> dict:
    """{(weight, style): set of characters} from @font-face rules with data: URLs."""
    out = {}
    for m in re.finditer(
        r"@font-face\{font-family:'Source Serif 4 Caption';src:url\(data:font/ttf;base64,([^)]+)\) "
        r"format\('truetype'\);font-weight:(\d+);font-style:(\w+);\}", css
    ):
        with TTFont(io.BytesIO(base64.b64decode(m.group(1)))) as tt:
            assert "GPOS" not in tt and "GSUB" not in tt  # no kerning or ligatures to change widths
            out[(int(m.group(2)), m.group(3))] = {chr(c) for c in tt.getBestCmap()}
    return out


def test_svg_embeds_only_the_glyphs_it_uses():
    svg = _export("svg").decode("utf-8")
    faces = _embedded_faces(svg)
    assert faces == {
        (700, "normal"): set("Penny Black"),
        (400, "normal"): set("Plate 1a"),
        (400, "italic"): set("1d · Used · Imperforate") | set("SG 2"),
    }
    root = ET.fromstring(svg)
    for t in root.iter("{http://www.w3.org/2000/svg}text"):
        if "caption" in (t.get("class") or ""):
            assert t.get("font-family") is None  # the style rule sets the caption font
    rule = "text.caption{font-family:'Source Serif 4 Caption',Georgia,serif;font-kerning:none"
    assert rule in svg
    assert "text-rendering:geometricPrecision" in svg
    assert len(svg) < 60_000  # subsets, not the whole fonts


def test_svg_semibold_headings():
    svg = _export("svg", caption_heading="semibold").decode("utf-8")
    assert (600, "normal") in _embedded_faces(svg) and (700, "normal") not in _embedded_faces(svg)
    assert re.search(r'<text class="caption caption-heading"[^>]*font-weight="600"', svg)


def test_preview_and_html_export_embed_the_caption_font():
    html = _export("html").decode("utf-8")
    assert set(_embedded_faces(html)) == {(700, "normal"), (400, "normal"), (400, "italic")}
    assert ".caption{font-family:'Source Serif 4 Caption',Georgia,serif;font-kerning:none" in html
    assert "text-rendering:geometricPrecision" in html
    assert re.search(r'class="caption caption-heading"[^>]*font-weight:700', html)
    html = _export("html", caption_heading="semibold").decode("utf-8")
    assert re.search(r'class="caption caption-heading"[^>]*font-weight:600', html)


# ── CAPTION_HEADING in the file ──


def test_python_reads_and_writes_the_heading_weight():
    base = "ALBUM_PAGES_SIZE(210 297)\n"
    assert AlbumParser().parse(base).caption_heading == "bold"
    album = AlbumParser().parse(base + 'CAPTION_HEADING("semibold")\n')
    assert album.caption_heading == "semibold"
    assert AlbumParser().parse(base + 'CAPTION_HEADING("heavy")\n').caption_heading == "bold"
    out = AlbumSerializer().to_dsl(album)
    assert 'CAPTION_HEADING("semibold")' in out
    assert AlbumParser().parse(out).caption_heading == "semibold"
    album.caption_heading = "bold"
    assert "CAPTION_HEADING" not in AlbumSerializer().to_dsl(album)  # bold is the default


def test_editor_reads_and_writes_the_heading_weight():
    core = WEB / "dsl_core.js"
    script = (
        f"const c = require({json.dumps(str(core))});"
        "const base = 'ALBUM_PAGES_SIZE(210 297)\\nPAGE_START\\n';"
        "const withHeading = w => c.parseDSL(base.replace("
        "'PAGE_START', 'CAPTION_HEADING(\"' + w + '\")\\nPAGE_START'));"
        "const semi = withHeading('semibold'), odd = withHeading('heavy');"
        "console.log(JSON.stringify({plain: c.parseDSL(base).captionHeading,"
        " semi: semi.captionHeading, odd: odd.captionHeading, written: c.buildDSL(semi),"
        " plainWritten: c.buildDSL(c.parseDSL(base))}));"
    )
    r = _run_node(script)
    assert (r["plain"], r["semi"], r["odd"]) == ("bold", "semibold", "bold")
    assert 'CAPTION_HEADING("semibold")' in r["written"]
    assert "CAPTION_HEADING" not in r["plainWritten"]
    # And the Python reader understands what the editor wrote
    assert AlbumParser().parse(r["written"]).caption_heading == "semibold"


def test_the_same_album_gives_the_same_svg(monkeypatch):
    """The subsets keep the font's own date, so exports don't change from one run to the next."""
    from fontTools.ttLib.tables import _h_e_a_d

    caption_fonts._subset_face.cache_clear()
    first = _export("svg")
    monkeypatch.setattr(_h_e_a_d, "timestampNow", lambda: 12345)  # "now" is another time
    caption_fonts._subset_face.cache_clear()
    try:
        assert _export("svg") == first
    finally:
        caption_fonts._subset_face.cache_clear()
