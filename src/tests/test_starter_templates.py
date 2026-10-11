"""The starter templates in the Template Gallery (``stamp_album/templates.py``).

Every template must be a page someone could print as it is: placed items only (no
legacy rows), everything inside the page margins, nothing running into anything
else, and clean exports. The geometry is the export engines' own (``frames`` and
``caption_layout`` with PDF metrics); the browser test checks the editor's "!" badges.
"""

import itertools

import pytest
from fastapi.testclient import TestClient

from stamp_album.api import app
from stamp_album.core.parser import AlbumParser
from stamp_album.engines import caption_layout, frames, text_layout
from stamp_album.templates import TEMPLATES

EXPECTED_IDS = ["single_stamp", "set_row", "title_page", "exhibition_page"]
IDS = [t["id"] for t in TEMPLATES]
EPS = 1e-6


def _parse(t):
    return AlbumParser().parse(t["content"], t["id"] + ".slbum")


def _text_fits(s) -> bool:
    """Whether a text item's wrapped lines fit inside its own box."""
    measure = lambda line: caption_layout.metrics_measure(line, s.font_id, s.font_size)  # noqa: E731
    width = s.width - 2 * text_layout.PAD_MM
    lines = []
    for para in (s.description or "").split("\n"):
        lines += text_layout.wrap_lines(para, width, measure) or [""]
    line_h = s.font_size * text_layout.LINE_HEIGHT / text_layout.PT_PER_MM
    return len(lines) * line_h + 2 * text_layout.PAD_MM <= s.height + EPS


def layout_problems(t) -> list[str]:
    """Everything wrong with a template's layout, as readable messages (empty when it is fine)."""
    album = _parse(t)
    ps = album.page_setup
    area = (ps.margin_left, ps.margin_top, ps.width - ps.margin_right, ps.height - ps.margin_bottom)
    problems = []
    for pi, page in enumerate(album.pages, 1):
        if page.rows:
            problems.append(f"page {pi}: uses the old row layout")
        boxes = []  # (name, (l, t, r, b))
        for s in page.absolute_stamps:
            x, y, w, h = s.abs_x, s.abs_y, s.width, s.height
            name = (s.description or "item").split("\n")[0][:30]
            if s.is_text_element:
                boxes.append((f"text '{name}'", (x, y, x + w, y + h)))
                if not _text_fits(s):
                    problems.append(f"page {pi}: text '{name}' doesn't fit its box")
                continue
            fx, fy, fw, fh = frames.outer_box(s, x, y, w, h)
            boxes.append((f"frame of '{name}'", (fx, fy, fx + fw, fy + fh)))
            caption = caption_layout.layout(s, x, y, w, h, caption_layout.metrics_measure)
            cb = caption_layout.bounds(caption)
            if cb:
                boxes.append((f"captions of '{name}'", cb))
        for name, (left, top, right, bottom) in boxes:
            if (left < area[0] - EPS or top < area[1] - EPS
                    or right > area[2] + EPS or bottom > area[3] + EPS):
                problems.append(f"page {pi}: {name} is outside the margins")
        for (n1, a), (n2, b) in itertools.combinations(boxes, 2):
            if n1.split("'")[1:] == n2.split("'")[1:]:
                continue  # a stamp's own frame and captions never overlap (layout keeps a gap)
            if a[0] < b[2] - EPS and b[0] < a[2] - EPS and a[1] < b[3] - EPS and b[1] < a[3] - EPS:
                problems.append(f"page {pi}: {n1} runs into {n2}")
    return problems


def test_the_four_starter_templates():
    assert IDS == EXPECTED_IDS
    for t in TEMPLATES:
        assert t["name"] and t["description"] and t["category"] and t["content"]


@pytest.mark.parametrize("tid", IDS)
def test_template_is_exhibition_style(tid):
    t = next(t for t in TEMPLATES if t["id"] == tid)
    album = _parse(t)
    assert "ALBUM_THEME(\"exhibition\")" in t["content"]
    assert album.page_setup.border_style in ("none", "solid", "double")  # a plain border
    stamps = [s for p in album.pages for s in p.absolute_stamps if not s.is_text_element]
    texts = [s for p in album.pages for s in p.absolute_stamps if s.is_text_element]
    assert any(s.role == "heading" for s in texts), "every template has a marked heading"
    if tid != "title_page":
        assert stamps
    for s in stamps:
        assert s.frame != "none"
        assert s.description.strip() and s.catalog_refs, "every stamp shows how to caption it"


@pytest.mark.parametrize("tid", IDS)
def test_template_fits_the_page(tid):
    assert layout_problems(next(t for t in TEMPLATES if t["id"] == tid)) == []


def test_layout_check_catches_problems():
    """The check itself: a stamp past the margin and two stamps on top of each other."""
    bad = {
        "id": "bad",
        "content": "\n".join([
            "ALBUM_PAGES_SIZE(210 297)",
            "ALBUM_PAGES_MARGINS(15 15 15 15)",
            "PAGE_START",
            'STAMP_ADD_AT(185.0 50.0 19.0 22.0 "Past the margin" "SW 1" "" "")',
            'STAMP_ADD_AT(50.0 50.0 19.0 22.0 "One" "SW 2" "" "")',
            'STAMP_ADD_AT(60.0 55.0 19.0 22.0 "Two" "SW 3" "" "")',
        ]),
    }
    problems = layout_problems(bad)
    assert any("outside the margins" in p for p in problems)
    assert any("runs into" in p for p in problems)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.mark.parametrize("fmt, magic", [("pdf", b"%PDF"), ("png", b"\x89PNG"), ("svg", b"<")])
@pytest.mark.parametrize("tid", IDS)
def test_template_exports(client, tid, fmt, magic):
    t = next(t for t in TEMPLATES if t["id"] == tid)
    body = {"dsl": t["content"], "format": fmt, "source_path": tid + ".slbum"}
    r = client.post("/export", json=body)
    assert r.status_code == 200, r.text[:300]
    assert r.content.lstrip()[: len(magic)] == magic


def test_gallery_api_lists_the_templates(client):
    listed = client.get("/api/templates").json()
    assert [t["id"] for t in listed] == EXPECTED_IDS
    for tid in EXPECTED_IDS:
        r = client.get(f"/api/templates/{tid}")
        assert r.status_code == 200 and "PAGE_START" in r.json()["dsl"]
