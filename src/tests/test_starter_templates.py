"""The starter templates in the Template Gallery (``stamp_album/templates.py``).

Every template must be a page someone could print as it is: placed items only (no
legacy rows), everything inside the page margins, nothing running into anything
else, and clean exports. The geometry is the export engines' own (``frames`` and
``caption_layout`` with the caption font's own widths); the browser test checks
the editor's "!" badges.
"""

import itertools

import pytest
from fastapi.testclient import TestClient

from stamp_album.api import app
from stamp_album.core.parser import AlbumParser
from stamp_album.engines import caption_layout, frames, text_layout
from stamp_album.templates import TEMPLATES

EXPECTED_IDS = ["single_stamp", "set_row", "title_page", "exhibition_page",
                "introduction_page", "long_set", "stamps_with_illustrations",
                "normal_and_varieties"]
# From the owner's AlbumEasy layouts (2026-10-17); their picture spaces are free shapes
ALBUMEASY_IDS = EXPECTED_IDS[4:]
IDS = [t["id"] for t in TEMPLATES]
EPS = 1e-6


def _parse(t):
    return AlbumParser().parse(t["content"], t["id"] + ".slbum")


def _text_fits(s) -> bool:
    """Whether a text item's wrapped lines fit inside its own box."""
    from reportlab.pdfbase import pdfmetrics

    from stamp_album.engines.pdf import _BUILTIN_FONT_MAP

    font = _BUILTIN_FONT_MAP.get(s.font_id or "HN", "Helvetica")
    measure = lambda line: pdfmetrics.stringWidth(line, font, s.font_size) * 25.4 / 72  # noqa: E731
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
            caption = caption_layout.layout(s, x, y, w, h)
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


def test_the_starter_templates():
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
        assert s.description.strip(), "every stamp and picture space is named"
        if s.is_freehand:
            continue  # a picture space: labelled, no frame or catalogue number
        assert s.frame != "none"
        assert s.catalog_refs, "every stamp shows how to caption it"


@pytest.mark.parametrize("tid", IDS)
def test_template_fits_the_page(tid):
    assert layout_problems(next(t for t in TEMPLATES if t["id"] == tid)) == []


def _stamps(t):
    return [s for p in _parse(t).pages for s in p.absolute_stamps if not s.is_text_element]


def _bottom(s) -> float:
    """The lowest edge of an item: its box, or for a stamp its frame and captions."""
    x, y, w, h = s.abs_x, s.abs_y, s.width, s.height
    if s.is_text_element:
        return y + h
    fx, fy, fw, fh = frames.outer_box(s, x, y, w, h)
    cb = caption_layout.bounds(caption_layout.layout(s, x, y, w, h))
    return max(fy + fh, cb[3] if cb else 0)


@pytest.mark.parametrize("tid", IDS)
def test_no_caption_wraps(tid):
    """Placeholder captions are short enough for one line each, even on 19 mm stamps."""
    for s in _stamps(next(t for t in TEMPLATES if t["id"] == tid)):
        lines = caption_layout.layout(s, s.abs_x, s.abs_y, s.width, s.height)
        kinds = [line.kind for line in lines]
        assert len(kinds) == len(set(kinds)), f"'{s.description}' wraps: {kinds}"


@pytest.mark.parametrize("tid", IDS)
def test_text_shares_one_left_edge(tid):
    """Every text item spans the same 20 to 190 mm, so paragraphs line up across templates."""
    album = _parse(next(t for t in TEMPLATES if t["id"] == tid))
    for s in (s for p in album.pages for s in p.absolute_stamps if s.is_text_element):
        assert (s.abs_x, s.abs_x + s.width) == (20.0, 190.0), s.description[:30]


@pytest.mark.parametrize("tid", [i for i in IDS if i != "title_page"])
def test_stamp_pages_fill_the_page(tid):
    """A page of stamps reaches the lower part of the page instead of stopping two-thirds down."""
    t = next(t for t in TEMPLATES if t["id"] == tid)
    album = _parse(t)
    ps = album.page_setup
    lowest = max(_bottom(s) for p in album.pages for s in p.absolute_stamps)
    assert lowest >= ps.height - ps.margin_bottom - 20, f"content ends at {lowest:.1f} mm"


def test_exhibition_page_captions():
    """Every Exhibition page stamp has a heading; descriptions are placeholders, not sizes."""
    import re

    for s in _stamps(next(t for t in TEMPLATES if t["id"] == "exhibition_page")):
        assert s.heading and s.heading.text.strip(), f"'{s.description}' has no heading"
        assert not re.search(r"\d\s*×\s*\d", s.description), s.description


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


def test_stamp_placeholders_never_say_description():
    """A stamp's own name is Name; "Description" is the paragraph text item."""
    for t in TEMPLATES:
        for s in _stamps(t):
            assert s.description != "Description", t["id"]
    names = {s.description for s in _stamps(next(t for t in TEMPLATES
                                                    if t["id"] == "exhibition_page"))}
    assert names == {"Name"}


@pytest.mark.parametrize("tid", ALBUMEASY_IDS)
def test_albumeasy_layouts_carry_nothing_of_the_owners_albums(tid):
    """Layouts only: no country, write-up, colour name or catalogue number from the albums."""
    import re

    content = next(t for t in TEMPLATES if t["id"] == tid)["content"]
    for word in ("Pakistan", "Qatar", "Bahawalpur", "Nigeria", "Bahrain", "Tristan", "India",
                 "SG#", "SC#", "Scott", "Gibbons", "carmine", "Elizabeth", "George"):
        assert word.lower() not in content.lower(), word
    assert not re.search(r"\b(SG|SC|SW)\s*\d", content)


PICTURE_SPACES = {
    "introduction_page": ["Map", "Coat of arms", "Flag"],
    "stamps_with_illustrations": ["Overprint type 1", "Overprint type 2", "Overprint detail"],
}


@pytest.mark.parametrize("tid", list(PICTURE_SPACES))
def test_picture_spaces_are_labelled_free_shapes(tid):
    pics = [s for s in _stamps(next(t for t in TEMPLATES if t["id"] == tid))
            if s.is_freehand]
    assert [s.description for s in pics] == PICTURE_SPACES[tid]


def test_varieties_are_named_above_each_stamp():
    stamps = _stamps(next(t for t in TEMPLATES if t["id"] == "normal_and_varieties"))
    heads = [s.heading.text for s in stamps]
    assert heads == ["Normal", "Shade", "Paper", "Watermark", "Perforation"] * 3
