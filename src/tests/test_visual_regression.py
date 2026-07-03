"""
Visual regression test: render a fixed album through all output paths and
snapshot-diff the text-based results (HTML, SVG).

Run with  SNAPSHOT_UPDATE=1  to regenerate snapshots when output changes are
intentional.
"""

import os
import pathlib

import pytest

from stamp_album.core.parser import AlbumParser, ParseError
from stamp_album.engines.pdf_generator import HTMLRenderer
from stamp_album.engines.pdf import PDFGenerator
from stamp_album.engines.raster import PNGGenerator
from stamp_album.engines.svg_export import SVGExporter

SNAPSHOT_DIR = pathlib.Path(__file__).resolve().parent / "snapshots"
UPDATE = bool(os.environ.get("SNAPSHOT_UPDATE"))


# ---------------------------------------------------------------------------
# Fixed test album with comprehensive features
# ---------------------------------------------------------------------------

# NOTE: SVGExporter, PDFGenerator, and PNGGenerator currently render only
# absolute stamps (STAMP_ADD_AT), not row-based stamps.  The HTMLRenderer
# renders both.  This test uses absolute stamps to exercise all engines.

ALBUM_DSL = r"""
ALBUM_TITLE("Regression Test Album")
ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)
ALBUM_HAS_BORDER(1)
ALBUM_BORDER_OUTER(0.8)
ALBUM_BORDER_INNER1(0.4)
ALBUM_BORDER_SPACING(2)
ALBUM_BORDER_STYLE(classic)
ALBUM_ALBUM_BORDER(#8B0000)
COLOR_STAMP_BORDER(#000000)
COLOR_STAMP_BACKGROUND(#F5F5F0)

PAGE_START

STAMP_ADD_AT(15 30 40 30 "1d Red" "sg 1" "" "sacc 1")
STAMP_ADD_AT(65 30 40 30 "2d Blue" "sg 2" "scott 3" "sacc 2")
STAMP_ADD_AT(115 30 40 30 "3d Green" "sg 3" "" "sacc 3")

PAGE_START

STAMP_ADD_AT(20 40 45 35 "4d Violet" "sg 4" "" "sacc 4")
STAMP_ADD_AT(80 40 45 35 "5d Orange" "sg 5" "" "sacc 5")
STAMP_ADD_AT(140 40 45 35 "6d Purple" "sg 6" "" "sacc 6")
"""

DSL_STRIP = ALBUM_DSL.strip()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def album():
    parser = AlbumParser()
    return parser.parse(DSL_STRIP)


# ---------------------------------------------------------------------------
# Rendering tests
# ---------------------------------------------------------------------------

class TestVisualRegression:

    def test_html_renderer_output(self, album):
        html = HTMLRenderer(album, None).render()
        assert isinstance(html, str) and len(html) > 500
        assert "1d Red" in html
        assert "2d Blue" in html
        assert "3d Green" in html
        assert "4d Violet" in html
        _check_snapshot("html_renderer.html", html)

    def test_svg_exporter_output(self, album):
        svg = SVGExporter().generate_to_string(album)
        assert isinstance(svg, str) and len(svg) > 500
        assert svg.strip().startswith("<svg")
        assert "1d Red" in svg
        assert "2d Blue" in svg
        assert "4d Violet" in svg
        _check_snapshot("svg_exporter.svg", svg)

    def test_pdf_generator_output(self, album):
        pdf_bytes = PDFGenerator().generate_to_bytes(album)
        assert isinstance(pdf_bytes, bytes) and len(pdf_bytes) > 500
        assert pdf_bytes[:5] == b"%PDF-"

    def test_png_generator_output(self, album):
        png_bytes = PNGGenerator().generate_to_bytes(album, dpi=150)
        assert isinstance(png_bytes, bytes) and len(png_bytes) > 500
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_two_pages_present(self, album):
        assert len(album.pages) >= 2

    def test_catalog_refs_present(self, album):
        refs = set()
        for page in album.pages:
            for stamp in page.absolute_stamps:
                refs.update(stamp.catalog_refs or [])
        assert "sg 1" in refs
        assert "sg 2" in refs
        assert "sacc 4" in refs

    def test_absolute_stamps(self, album):
        abs_stamps = [s for p in album.pages for s in p.absolute_stamps]
        assert len(abs_stamps) == 6
        descs = {s.description for s in abs_stamps}
        assert "1d Red" in descs
        assert "4d Violet" in descs


# ---------------------------------------------------------------------------
# Snapshot helpers
# ---------------------------------------------------------------------------

def _check_snapshot(name: str, content: str):
    path = SNAPSHOT_DIR / name
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    if UPDATE or not path.exists():
        path.write_text(content, encoding="utf-8")
        return

    expected = path.read_text(encoding="utf-8")
    assert content == expected, (
        f"Snapshot mismatch: {name}\n"
        f"  Expected  {path}\n"
        f"  Generated content differs.\n"
        f"  Run with SNAPSHOT_UPDATE=1 to update snapshots if changes are intentional."
    )
