"""Fonts on this computer print as they show (owner's report, 2026-10-24; ADR-001).

A text item set in a font installed on the computer showed in the editor but printed in
Helvetica: the exports looked for a file whose name resembled the font, in the top level
of each font folder only (macOS keeps most fonts in a subfolder), and SVG and HTML never
looked at all. One font finder (engines/system_fonts.py) now reads each font's own name,
searches the folders with their subfolders, and serves the PDF, PNG, SVG and HTML.

The tests "install" the bundled caption font, under a folder two levels down with a file
name unlike its family name, as the only font on the computer.
"""

import io
import re
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fontTools.ttLib import TTCollection, TTFont
from PIL import Image

from stamp_album.api import app
from stamp_album.engines import system_fonts, text_layout

FONTS = Path(__file__).resolve().parents[1] / "stamp_album" / "web" / "fonts"
FAMILY = "Source Serif 4 Caption"
TEXT = "Penny Black"


def _install(tmp_path, monkeypatch, files):
    """Make *files* {relative path: source font} the computer's fonts, offered by FAMILY."""
    for rel, src in files.items():
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(src, TTCollection):
            src.save(str(dst))
        else:
            shutil.copy(src, dst)
    monkeypatch.setattr(system_fonts, "font_dirs", lambda: [tmp_path])
    monkeypatch.setattr(system_fonts, "CANDIDATES", (FAMILY, "Georgia"))
    system_fonts.clear_cache()


@pytest.fixture(autouse=True)
def _fresh():
    system_fonts.clear_cache()
    yield
    system_fonts.clear_cache()


@pytest.fixture()
def installed(tmp_path, monkeypatch):
    _install(tmp_path, monkeypatch, {
        "Supplemental/Serif/body-face.ttf": FONTS / "SourceSerif4Caption-Regular.ttf",
        "Supplemental/Serif/body-face-bold.ttf": FONTS / "SourceSerif4Caption-Bold.ttf",
    })


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _export(client, fmt, font):
    el = dict(t="text", x=25, y=25, w=400, h=60, lbl=TEXT, font=font, fs=18, align="left")
    state = {"elements": [el], "pages": [], "page_width_px": 525, "page_height_px": 742.5,
             "scale": 2.5, "format": fmt, "source_path": "t.slbum"}
    r = client.post("/export-from-state", json=state)
    assert r.status_code == 200, r.text
    return r.content


# ── Finding a font ──

def test_a_font_is_found_by_its_own_name_in_a_subfolder(installed):
    face = system_fonts.find(FAMILY)
    assert face is not None
    assert face.path.name == "body-face.ttf", "the regular face, not the bold"
    assert system_fonts.find(FAMILY.lower()) == face
    assert system_fonts.find("Georgia") is None


def test_the_font_list_is_what_is_installed(installed, client):
    assert system_fonts.available() == [FAMILY]
    assert client.get("/api/fonts").json() == {"fonts": [FAMILY]}


def test_a_font_in_a_collection_is_found_at_its_place(tmp_path, monkeypatch):
    coll = TTCollection()
    coll.fonts = [TTFont(str(FONTS / "SourceSerif4Caption-Bold.ttf")),
                  TTFont(str(FONTS / "SourceSerif4Caption-Regular.ttf"))]
    _install(tmp_path, monkeypatch, {"Collections/serif.ttc": coll})
    face = system_fonts.find(FAMILY)
    assert face is not None and face.path.suffix == ".ttc" and face.index == 1
    assert system_fonts.reportlab_name(FAMILY)
    assert system_fonts.pillow_font(FAMILY, 20) is not None


def test_a_font_that_may_not_be_embedded_is_not_offered(tmp_path, monkeypatch):
    tt = TTFont(str(FONTS / "SourceSerif4Caption-Regular.ttf"))
    tt["OS/2"].fsType = 0x0002  # restricted licence
    restricted = tmp_path / "src.ttf"
    tt.save(str(restricted))
    _install(tmp_path / "fonts", monkeypatch, {"x.ttf": restricted})
    assert system_fonts.find(FAMILY) is None
    assert system_fonts.available() == []


def test_print_preview_names_the_font_or_falls_back(installed):
    assert text_layout.css_font(FAMILY)[0].startswith(f"'{FAMILY}'")
    assert text_layout.css_font("Georgia")[0].startswith("Helvetica")


# ── Every export uses it ──

def test_pdf_embeds_the_font(installed, client):
    pdf = _export(client, "pdf", FAMILY)
    assert b"SourceSerif4Caption" in pdf, "the font is named in the PDF"
    assert b"/FontFile2" in pdf, "and embedded (ReportLab lists Helvetica on every page anyway)"


def test_pdf_falls_back_to_helvetica_for_a_font_not_here(installed, client):
    pdf = _export(client, "pdf", "Georgia")
    assert b"/FontFile2" not in pdf and b"Georgia" not in pdf


def test_png_draws_in_the_font(installed, client):
    a = Image.open(io.BytesIO(_export(client, "png", FAMILY))).convert("L")
    b = Image.open(io.BytesIO(_export(client, "png", "HN"))).convert("L")
    assert a.getbbox() and a.tobytes() != b.tobytes(), "not drawn in Helvetica"


def test_svg_embeds_the_font_for_its_text(installed, client):
    svg = _export(client, "svg", FAMILY).decode("utf-8")
    assert re.search(rf"@font-face\{{font-family:'{FAMILY}';src:url\(data:font/ttf", svg)
    assert re.search(rf"<text[^>]*font-family:'{FAMILY}'[^>]*>{TEXT}<", svg)


def test_html_embeds_the_font_for_its_text(installed, client):
    html = _export(client, "html", FAMILY).decode("utf-8")
    assert "@font-face{font-family:'Source Serif 4 Caption'" in html
    text_div = html.split(TEXT)[0].rsplit("<div", 1)[1]
    assert f"font-family:'{FAMILY}'" in text_div
