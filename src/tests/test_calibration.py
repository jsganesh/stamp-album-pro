"""Print calibration page (engines/calibration.py and /calibration.pdf)."""

import re
from datetime import date

import pytest
from fastapi.testclient import TestClient

from stamp_album.api import app
from stamp_album.engines import calibration, frames

PT_PER_MM = 72 / 25.4
PAPERS = list(calibration.PAPERS)


def _inside(lay, x, y, inset=calibration.MARGIN_MM - 1e-6):
    return inset <= x <= lay.width - inset and inset <= y <= lay.height - inset


def test_ticks_every_millimetre_with_5_and_10_mm_marks():
    t = calibration.ticks(30)
    assert [p for p, _ in t] == [float(i) for i in range(31)]
    assert [p for p, k in t if k == "major"] == [0, 10, 20, 30]
    assert [p for p, k in t if k == "half"] == [5, 15, 25]


@pytest.mark.parametrize("paper", PAPERS)
def test_rulers_are_whole_centimetres_inside_the_margins(paper):
    lay = calibration.layout(paper)
    for r in (lay.across, lay.down):
        assert r.length > 0 and r.length % 10 == 0
    a, d = lay.across, lay.down
    assert _inside(lay, a.x, a.y) and _inside(lay, a.x + a.length, a.y)
    assert _inside(lay, d.x, d.y) and _inside(lay, d.x, d.y + d.length)
    assert d.y > a.y, "the ruler down starts below the ruler across"
    assert d.y + d.length < lay.footer_y


def test_a4_has_the_long_rulers_and_a_100_mm_square():
    lay = calibration.layout("a4")
    assert (lay.width, lay.height) == (210.0, 297.0)
    assert lay.across.length == 180 and lay.down.length >= 200
    assert lay.square_size == 100


def test_a5_is_too_small_for_100_mm_and_gets_50():
    assert calibration.layout("a5").square_size == 50


@pytest.mark.parametrize("paper", PAPERS)
def test_square_and_samples_sit_clear_of_the_ruler_down_and_the_footer(paper):
    lay = calibration.layout(paper)
    labels_left = lay.down.x - calibration.RULER_LABEL_ROOM_MM
    assert lay.square_x + lay.square_size < labels_left
    assert lay.square_y + lay.square_size < lay.samples[0].y - 8
    for s in lay.samples:
        st = calibration.sample_stamp(s)
        x, y, w, h = frames.outer_box(st, s.x, s.y, s.w, s.h)
        assert x >= calibration.MARGIN_MM and x + w < labels_left
        assert y + h + 12 < lay.footer_y, "room for the captions above the footer"


def test_samples_are_penny_black_size_with_each_frame():
    lay = calibration.layout("a4")
    assert [s.frame for s in lay.samples] == ["thin", "medium", "double"]
    for s in lay.samples:
        st = calibration.sample_stamp(s)
        assert (st.width, st.height) == (19.0, 22.0) and st.frame == s.frame
        assert st.heading.text == s.label


def test_corner_marks_at_5_and_10_mm_from_every_edge():
    marks = calibration.corner_marks(210, 297)
    vertices = sorted(v for v, _, _ in marks)
    assert vertices == sorted(
        (x, y) for d in (5, 10) for x in (d, 210 - d) for y in (d, 297 - d)
    )
    for (vx, vy), (ax, ay), (bx, by) in marks:
        assert ay == vy and bx == vx, "one arm along each edge"
        assert 0 < ax < 210 and 0 < by < 297, "arms point into the page"


def test_unknown_paper_is_an_error():
    with pytest.raises(ValueError):
        calibration.layout("b5")


def _media_box(pdf: bytes):
    m = re.search(rb"/MediaBox \[\s*0 0 ([\d.]+) ([\d.]+)\s*\]", pdf)
    return float(m.group(1)), float(m.group(2))


@pytest.mark.parametrize("paper", PAPERS)
def test_pdf_page_is_exactly_the_paper_size(paper):
    _, w, h = calibration.PAPERS[paper]
    pdf = calibration.generate_pdf(paper, "v9.9.9", date(2026, 10, 14))
    assert pdf.startswith(b"%PDF")
    assert pdf.count(b"/Type /Page\n") + pdf.count(b"/Type /Page ") == 1, "one page"
    pw, ph = _media_box(pdf)
    assert pw == pytest.approx(w * PT_PER_MM, abs=0.01)
    assert ph == pytest.approx(h * PT_PER_MM, abs=0.01)


def test_pdf_embeds_the_caption_font():
    pdf = calibration.generate_pdf("a4")
    assert b"SourceSerif4Caption" in pdf


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_endpoint_returns_a_pdf_download(client):
    r = client.get("/calibration.pdf", params={"paper": "letter"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert 'filename="calibration-letter.pdf"' in r.headers["content-disposition"]
    pw, _ = _media_box(r.content)
    assert pw == pytest.approx(215.9 * PT_PER_MM, abs=0.01)


def test_endpoint_defaults_to_a4_and_rejects_unknown_paper(client):
    assert _media_box(client.get("/calibration.pdf").content)[0] == pytest.approx(
        210 * PT_PER_MM, abs=0.01
    )
    assert client.get("/calibration.pdf", params={"paper": "b5"}).status_code == 400
