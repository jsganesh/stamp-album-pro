# ruff: noqa: F811
"""Album files keep what was typed, the Python reader and writer agree with the editor,
and the editor needs nothing from outside the app."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

from stamp_album.api import app
from stamp_album.core.parser import AlbumParser, unquote
from stamp_album.core.serializer import AlbumSerializer

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "src" / "stamp_album" / "web"
CORE = WEB / "dsl_core.js"
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")

TRICKY = 'The "Penny" Black \\ plate 1a\nsecond line'
ELEMENTS = [
    {
        "id": "a",
        "t": "stamp",
        "s": "oval",
        "x": 10,
        "y": 20,
        "w": 19,
        "h": 22,
        "lbl": TRICKY,
        "cat": 'SG "1"',
        "hdg": '1840 "May"',
        "denom": "1d",
        "cond": "Used",
        "perf": 'Imperf "a"',
        "bdr": "double",
        "bdrC": "#000000",
        "bdrW": 1,
        "fill": "#ffffff",
        "fillA": 100,
    },
    {
        "id": "b",
        "t": "text",
        "s": "text",
        "x": 5,
        "y": 5,
        "w": 50,
        "h": 10,
        "lbl": 'Great "Britain"',
        "font": "HB",
        "fs": 16,
        "align": "center",
        "role": "heading",
    },
    {
        "id": "c",
        "t": "image",
        "s": "rectangle",
        "x": 60,
        "y": 20,
        "w": 30,
        "h": 30,
        "lbl": "Arms",
        "img": "arms.png",
        "bdr": "none",
        "bdrC": "transparent",
        "bdrW": 0,
        "fill": "transparent",
        "fillA": 0,
    },
    {
        "id": "d",
        "t": "freehand",
        "s": "freehand",
        "x": 100,
        "y": 20,
        "w": 40,
        "h": 30,
        "lbl": "Note",
        "bdr": "solid",
        "bdrC": "#000000",
        "bdrW": 0.5,
        "fill": "#ffffff",
        "fillA": 100,
    },
]
KEYS = [
    "t",
    "s",
    "x",
    "y",
    "w",
    "h",
    "lbl",
    "cat",
    "hdg",
    "denom",
    "cond",
    "perf",
    "bdr",
    "bdrW",
    "img",
    "font",
    "fs",
    "align",
    "role",
]


def _node(script: str):
    out = subprocess.run(
        [shutil.which("node"), "-e", f"const c = require({json.dumps(str(CORE))});" + script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    return json.loads(out)


def _editor_album() -> str:
    state = {
        "pages": [ELEMENTS],
        "pw": 210,
        "ph": 297,
        "pageBorder": "greek_key",
        "theme": "green",
        "currentFile": 'My "best".slbum',
    }
    return _node(f"console.log(JSON.stringify(c.buildDSL({json.dumps(state)})));")


def _editor_read(dsl: str):
    keys = json.dumps(KEYS)
    return _node(
        f"const s = c.parseDSL({json.dumps(dsl)});"
        f"console.log(JSON.stringify({{theme: s.theme, border: s.pageBorder,"
        f" items: s.pages[0].map(e => Object.fromEntries({keys}.map(k => [k, e[k] ?? null])))}}));"
    )


# ── Quotes, backslashes and new lines survive a save ──


@needs_node
def test_editor_keeps_quotes_backslashes_and_new_lines():
    got = _editor_read(_editor_album())
    stamp, text = got["items"][0], got["items"][1]
    assert stamp["lbl"] == TRICKY
    assert (stamp["cat"], stamp["hdg"], stamp["perf"]) == ('SG "1"', '1840 "May"', 'Imperf "a"')
    assert text["lbl"] == 'Great "Britain"'
    assert len(got["items"]) == 4, "no item is lost"


def test_python_reader_decodes_what_the_writer_escapes():
    s = AlbumSerializer()
    for text in (TRICKY, "a\\nb", "\\", '""', "plain"):
        assert unquote('"' + s._escape_string(text) + '"') == text


# ── The Python reader and writer agree with the editor ──


@needs_node
def test_editor_album_survives_the_python_reader_and_writer():
    original = _editor_album()
    album = AlbumParser().parse(original)
    again = AlbumSerializer().to_dsl(album)
    assert _editor_read(again) == _editor_read(original)


def test_python_writer_uses_the_editors_names():
    album = AlbumParser().parse(
        'ALBUM_PAGES_BORDER(0.5 0 0 1)\nALBUM_PAGES_BORDER_STYLE("rope")\nALBUM_THEME("navy")\n'
        "ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n"
        'STAMP_ADD_AT(1 2 3 4 "x" "" "" "" triangle_inverted "solid" "#000000" 0.5 "#ffffff" 100)\n'
        'STAMP_DETAILS("1d" "" "Imperforate")\n'
    )
    dsl = AlbumSerializer().to_dsl(album)
    assert ' triangle_inverted "solid"' in dsl, "shape names as the editor writes them"
    assert 'ALBUM_PAGES_BORDER_STYLE("rope")' in dsl and 'ALBUM_THEME("navy")' in dsl
    assert 'STAMP_DETAILS("1d" "" "Imperforate")' in dsl, (
        "the three fields, empty ones kept in place"
    )


def test_python_reads_the_editors_placed_pictures():
    album = AlbumParser().parse(
        "ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n"
        'STAMP_ADD_IMG(60.0 20.0 30.0 30.0 "arms.png" "Arms" "" "")\n'
    )
    (pic,) = album.pages[0].absolute_stamps
    assert (pic.abs_x, pic.abs_y, pic.width, pic.height) == (60, 20, 30, 30)
    assert pic.image_path == "arms.png" and pic.is_picture and pic.frame == "none"


# ── Nothing loads from outside the app ──


def test_editor_page_loads_nothing_from_outside():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert not re.findall(r'(?:src|href)="https?://', html), "scripts and styles are bundled"
    for name in ("codemirror.min.js", "codemirror.min.css", "codemirror-LICENSE.txt"):
        assert (WEB / name).is_file(), name
    csp = TestClient(app).get("/").headers["content-security-policy"]
    assert "cdnjs" not in csp and "https:" not in csp


def test_bundled_codemirror_is_served():
    client = TestClient(app)
    js = client.get("/codemirror.min.js")
    assert js.status_code == 200 and "CodeMirror" in js.text[:2000]
    assert client.get("/codemirror.min.css").status_code == 200


def test_dsl_editor_uses_codemirror(page):
    page.evaluate("document.getElementById('btn-dsl').click()")
    assert page.evaluate("typeof CodeMirror") == "function"
    assert page.locator("#dsl-panel .CodeMirror").count() == 1


def test_no_test_waits_with_a_string_function():
    """wait_for_function("...") is run through eval, which the app's CSP blocks (flaky on CI)."""
    offenders = [
        str(p.relative_to(ROOT))
        for p in [*ROOT.joinpath("src", "tests").glob("*.py"), *ROOT.joinpath("tools").glob("*.py")]
        if 'wait_for_function("' in p.read_text(encoding="utf-8") and p.name != Path(__file__).name
    ]
    assert offenders == [], "poll with evaluate() instead (test_ui_smoke.wait_for_app)"
