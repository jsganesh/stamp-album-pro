"""
Round-trip tests: parse DSL -> serialize -> re-parse -> verify.

Catches bugs where the serializer produces invalid DSL or loses data.
"""
import pytest

from stamp_album.core.models import Color
from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer


@pytest.fixture
def parser():
    return AlbumParser()


@pytest.fixture
def serializer():
    return AlbumSerializer()


class TestColorHex:
    """Tests for Color.to_hex() and equality."""

    def test_to_hex_red(self):
        c = Color(r=1.0, g=0.0, b=0.0)
        assert c.to_hex() == "#FF0000"

    def test_to_hex_black(self):
        c = Color()
        assert c.to_hex() == "#000000"

    def test_to_hex_white(self):
        c = Color(r=1.0, g=1.0, b=1.0)
        assert c.to_hex() == "#FFFFFF"

    def test_to_hex_clamps(self):
        c = Color(r=1.5, g=-0.5, b=0.5)
        h = c.to_hex()
        assert h == "#FF007F"

    def test_equality(self):
        c1 = Color(r=1.0, g=0.0, b=0.0)
        c2 = Color(r=1.0, g=0.0, b=0.0)
        assert c1 == c2

    def test_inequality(self):
        c1 = Color(r=1.0, g=0.0, b=0.0)
        c2 = Color(r=0.0, g=1.0, b=0.0)
        assert c1 != c2

    def test_hash(self):
        c1 = Color(r=0.5, g=0.5, b=0.5)
        c2 = Color(r=0.5, g=0.5, b=0.5)
        assert hash(c1) == hash(c2)
        s = {c1, c2}
        assert len(s) == 1


class TestRoundTripMinimal:
    """Round-trip tests for minimal albums."""

    def test_empty_album(self, parser, serializer):
        album = parser.parse("")
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        assert reparsed.title == ""
        assert len(reparsed.pages) == 0

    def test_title_only(self, parser, serializer):
        source = 'ALBUM_TITLE("My Album")\nALBUM_AUTHOR("Ganesh")\n'
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        assert reparsed.title == "My Album"
        assert reparsed.author == "Ganesh"

    def test_page_setup(self, parser, serializer):
        source = """ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.5 0.3 0.5 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
"""
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        assert reparsed.page_setup.width == 210.0
        assert reparsed.page_setup.height == 297.0
        assert reparsed.page_setup.margin_left == 20.0
        assert reparsed.page_setup.has_border is True
        assert reparsed.page_setup.border_outer == 0.5
        assert reparsed.page_setup.hspace == 6.0

    def test_single_page(self, parser, serializer):
        source = """PAGE_START
PAGE_TEXT("HN" 10 "Hello World")
"""
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        assert len(reparsed.pages) == 1
        assert len(reparsed.pages[0].text_elements) == 1
        assert reparsed.pages[0].text_elements[0].content == "Hello World"


class TestRoundTripStamps:
    """Round-trip tests for stamps and rows."""

    def test_single_stamp(self, parser, serializer):
        source = """PAGE_START
ROW_START_FS("HN" 10 5 180)
STAMP_ADD(40 30 "Test Stamp" "sg 1" "" "sacc 1")
"""
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        assert len(reparsed.pages) == 1
        assert len(reparsed.pages[0].rows) == 1
        assert len(reparsed.pages[0].rows[0].stamps) == 1
        stamp = reparsed.pages[0].rows[0].stamps[0]
        assert stamp.width == 40
        assert stamp.height == 30
        assert stamp.description == "Test Stamp"

    def test_multiple_stamps(self, parser, serializer):
        source = """PAGE_START
ROW_START_FS("HN" 10 5 180)
STAMP_ADD(40 30 "First" "" "" "")
STAMP_ADD(40 30 "Second" "" "" "")
"""
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        assert len(reparsed.pages[0].rows[0].stamps) == 2

    def test_blank_stamp(self, parser, serializer):
        source = """PAGE_START
ROW_START_FS("HN" 10 5 180)
STAMP_ADD_BLANK(40 30)
"""
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        stamp = reparsed.pages[0].rows[0].stamps[0]
        assert stamp.width == 40
        assert stamp.height == 30

    def test_stamp_heading(self, parser, serializer):
        source = """PAGE_START
ROW_START_FS("HN" 10 5 180)
STAMP_ADD(40 30 "Test" "" "" "")
STAMP_HEADING("HB" 10 "Scarce")
"""
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        stamp = reparsed.pages[0].rows[0].stamps[0]
        assert stamp.heading is not None
        assert stamp.heading.text == "Scarce"


class TestRoundTripColors:
    """Round-trip tests for color commands."""

    def test_border_color(self, parser, serializer):
        source = "COLOUR_ALBUM_BORDER(red)\n"
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        assert reparsed.color_album_border is not None
        assert reparsed.color_album_border == Color.from_name("red")

    def test_hex_color(self, parser, serializer):
        source = "COLOUR_ALBUM_BORDER(#FF8800)\n"
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        assert reparsed.color_album_border is not None


class TestRoundTripMultiPage:
    """Round-trip tests for multi-page albums."""

    def test_two_pages(self, parser, serializer):
        source = """ALBUM_TITLE("Test")
PAGE_START
PAGE_TEXT("HN" 10 "Page 1")
PAGE_START
PAGE_TEXT("HN" 10 "Page 2")
"""
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        assert len(reparsed.pages) == 2
        assert reparsed.pages[0].text_elements[0].content == "Page 1"
        assert reparsed.pages[1].text_elements[0].content == "Page 2"

    def test_font_definitions(self, parser, serializer):
        source = 'ALBUM_DEFINE_FONT("MY" "DejaVu Serif")\n'
        album = parser.parse(source)
        dsl = serializer.to_dsl(album)
        reparsed = parser.parse(dsl)
        assert len(reparsed.fonts) == 1
        assert reparsed.fonts[0].font_id == "MY"
        assert reparsed.fonts[0].font_name == "DejaVu Serif"
