"""
Tests for the DSL parser.
"""

import pytest

from stamp_album.core.models import (
    RowStyle,
    StampShape,
    TextAlignment,
)
from stamp_album.core.parser import AlbumParser


@pytest.fixture
def parser():
    """Create a fresh parser instance."""
    return AlbumParser()


class TestParserBasics:
    """Basic parser functionality tests."""

    def test_parse_empty(self, parser):
        """Parsing empty input should return an empty album."""
        album = parser.parse("")
        assert album is not None
        assert len(album.pages) == 0

    def test_parse_comments_only(self, parser):
        """Parsing comments-only input should return an empty album."""
        source = "# This is a comment\n# Another comment"
        album = parser.parse(source)
        assert album is not None
        assert len(album.pages) == 0

    def test_parse_document_title(self, parser):
        """Test parsing ALBUM_TITLE command."""
        source = 'ALBUM_TITLE ("My Album")'
        album = parser.parse(source)
        assert album.title == "My Album"

    def test_parse_document_author(self, parser):
        """Test parsing ALBUM_AUTHOR command."""
        source = 'ALBUM_AUTHOR ("John Doe")'
        album = parser.parse(source)
        assert album.author == "John Doe"


class TestPageSetup:
    """Tests for page setup commands."""

    def test_parse_page_size(self, parser):
        """Test parsing ALBUM_PAGES_SIZE command."""
        source = "ALBUM_PAGES_SIZE (215.9 279.4)"
        album = parser.parse(source)
        assert album.page_setup.width == 215.9
        assert album.page_setup.height == 279.4

    def test_parse_margins(self, parser):
        """Test parsing ALBUM_PAGES_MARGINS command."""
        source = "ALBUM_PAGES_MARGINS (25.0 12.0 15.0 15.0)"
        album = parser.parse(source)
        assert album.page_setup.margin_left == 25.0
        assert album.page_setup.margin_right == 12.0
        assert album.page_setup.margin_top == 15.0
        assert album.page_setup.margin_bottom == 15.0

    def test_parse_even_margins(self, parser):
        """Test parsing ALBUM_PAGES_MARGINSE command."""
        source = "ALBUM_PAGES_MARGINSE (12.0 25.0 15.0 15.0)"
        album = parser.parse(source)
        assert album.page_setup.even_margin_left == 12.0
        assert album.page_setup.even_margin_right == 25.0
        assert album.page_setup.mirror_margins is True

    def test_parse_border_four_params(self, parser):
        """Test parsing ALBUM_PAGES_BORDER with 4 parameters."""
        source = "ALBUM_PAGES_BORDER (0.1 0.5 0.1 1.0)"
        album = parser.parse(source)
        assert album.page_setup.has_border is True
        assert album.page_setup.border_outer == 0.1
        assert album.page_setup.border_inner1 == 0.5
        assert album.page_setup.border_inner2 == 0.1
        assert album.page_setup.border_spacing == 1.0

    def test_parse_spacing(self, parser):
        """Test parsing ALBUM_PAGES_SPACING command."""
        source = "ALBUM_PAGES_SPACING (6.0 6.0)"
        album = parser.parse(source)
        assert album.page_setup.hspace == 6.0
        assert album.page_setup.vspace == 6.0

    def test_parse_title(self, parser):
        """Test parsing ALBUM_PAGES_TITLE command."""
        source = 'ALBUM_PAGES_TITLE (TB 16 "My Title")'
        album = parser.parse(source)
        assert album.page_setup.title is not None
        assert album.page_setup.title.font_id == "TB"
        assert album.page_setup.title.size == 16.0
        assert album.page_setup.title.content == "My Title"

    def test_parse_title_with_vspace(self, parser):
        """Test parsing ALBUM_PAGES_TITLE with optional vspace."""
        source = 'ALBUM_PAGES_TITLE (TB 16 "My Title" 5.0)'
        album = parser.parse(source)
        assert album.page_setup.title.vspace == 5.0


class TestFontDefinition:
    """Tests for font definition commands."""

    def test_define_font(self, parser):
        """Test parsing ALBUM_DEFINE_FONT command."""
        source = 'ALBUM_DEFINE_FONT (MY "DejaVu Serif")'
        album = parser.parse(source)
        assert len(album.fonts) == 1
        assert album.fonts[0].font_id == "MY"
        assert album.fonts[0].font_name == "DejaVu Serif"


class TestColorCommands:
    """Tests for color commands."""

    def test_color_album_border(self, parser):
        """Test parsing COLOUR_ALBUM_BORDER command."""
        source = "COLOUR_ALBUM_BORDER (red)"
        album = parser.parse(source)
        assert album.color_album_border is not None
        assert album.color_album_border.r == 1.0

    def test_color_album_title(self, parser):
        """Test parsing COLOUR_ALBUM_TITLE command."""
        source = "COLOUR_ALBUM_TITLE (blue)"
        album = parser.parse(source)
        assert album.color_title is not None
        assert album.color_title.b == 1.0

    def test_color_hex(self, parser):
        """Test parsing color with hex value."""
        source = "COLOUR_ALBUM_BORDER (#FF0000)"
        album = parser.parse(source)
        assert album.color_album_border is not None
        assert album.color_album_border.r == 1.0

    def test_color_american_spelling(self, parser):
        """Test parsing COLOR (American spelling) command."""
        source = "COLOR_ALBUM_BORDER (green)"
        album = parser.parse(source)
        assert album.color_album_border is not None
        assert album.color_album_border.g == 0.5


class TestPageCommands:
    """Tests for page-level commands."""

    def test_page_start(self, parser):
        """Test parsing PAGE_START command."""
        source = "PAGE_START"
        album = parser.parse(source)
        assert len(album.pages) == 1

    def test_page_text(self, parser):
        """Test parsing PAGE_TEXT command."""
        source = 'PAGE_START\nPAGE_TEXT (HN 10 "Hello World")'
        album = parser.parse(source)
        assert len(album.pages) == 1
        assert len(album.pages[0].text_elements) == 1
        assert album.pages[0].text_elements[0].content == "Hello World"

    def test_page_text_center(self, parser):
        """Test parsing PAGE_TEXT_CENTRE command."""
        source = 'PAGE_START\nPAGE_TEXT_CENTRE (HS 12 "Centered Text")'
        album = parser.parse(source)
        text = album.pages[0].text_elements[0]
        assert text.alignment == TextAlignment.CENTER

    def test_page_text_right(self, parser):
        """Test parsing PAGE_TEXT_RIGHT command."""
        source = 'PAGE_START\nPAGE_TEXT_RIGHT (HN 10 "Right Text")'
        album = parser.parse(source)
        text = album.pages[0].text_elements[0]
        assert text.alignment == TextAlignment.RIGHT

    def test_page_vspace(self, parser):
        """Test parsing PAGE_VSPACE command."""
        source = "PAGE_START\nPAGE_VSPACE (10.0)"
        album = parser.parse(source)
        assert album.pages[0].vspace == 10.0

    def test_page_rule(self, parser):
        """Test parsing PAGE_RULE_H command."""
        source = "PAGE_START\nPAGE_RULE_H (0.5 3 0)"
        album = parser.parse(source)
        assert len(album.pages[0].h_rules) == 1
        assert album.pages[0].h_rules[0] == (0.5, 3.0, 0.0)

    def test_page_background_img(self, parser):
        """Test parsing PAGE_BACKGROUND_IMG command."""
        source = 'PAGE_START\nPAGE_BACKGROUND_IMG ("background.png")'
        album = parser.parse(source)
        assert album.pages[0].background_image == "background.png"

    def test_page_add_box(self, parser):
        """Test parsing PAGE_ADD_BOX command."""
        source = "PAGE_START\nPAGE_ADD_BOX (10 20 50 30)"
        album = parser.parse(source)
        assert len(album.pages[0].boxes) == 1
        assert album.pages[0].boxes[0] == (10.0, 20.0, 50.0, 30.0)

    def test_multiple_pages(self, parser):
        """Test parsing multiple pages."""
        source = "PAGE_START\nPAGE_START\nPAGE_START"
        album = parser.parse(source)
        assert len(album.pages) == 3


class TestRowCommands:
    """Tests for row commands."""

    def test_row_start_fs(self, parser):
        """Test parsing ROW_START_FS command."""
        source = "PAGE_START\nROW_START_FS (HN 6 0.1 6.0)"
        album = parser.parse(source)
        assert len(album.pages[0].rows) == 1
        row = album.pages[0].rows[0]
        assert row.style == RowStyle.FIXED_SPACE
        assert row.font_id == "HN"
        assert row.size == 6.0
        assert row.spacing == 0.1
        assert row.width == 6.0

    def test_row_start_es(self, parser):
        """Test parsing ROW_START_ES command."""
        source = "PAGE_START\nROW_START_ES (HN 8 0.5 5.0)"
        album = parser.parse(source)
        row = album.pages[0].rows[0]
        assert row.style == RowStyle.EQUAL_SPACE

    def test_row_start_js(self, parser):
        """Test parsing ROW_START_JS command."""
        source = "PAGE_START\nROW_START_JS (HN 8 0.5 5.0)"
        album = parser.parse(source)
        row = album.pages[0].rows[0]
        assert row.style == RowStyle.JUSTIFIED_SPACE

    def test_row_align_middle(self, parser):
        """Test parsing ROW_ALIGN_MIDDLE command."""
        source = "PAGE_START\nROW_START_FS (HN 6 0.1 6.0)\nROW_ALIGN_MIDDLE"
        album = parser.parse(source)
        from stamp_album.core.models import RowAlignment

        assert album.pages[0].rows[0].alignment == RowAlignment.MIDDLE


class TestStampCommands:
    """Tests for stamp commands."""

    def test_stamp_add(self, parser):
        """Test parsing STAMP_ADD command."""
        source = (
            "PAGE_START\n"
            "ROW_START_FS (HN 6 0.1 6.0)\n"
            'STAMP_ADD (32.0 37.0 "2 1/2d deep blue" "sg 1" "" "sacc 1")'
        )
        album = parser.parse(source)
        row = album.pages[0].rows[0]
        assert len(row.stamps) == 1
        stamp = row.stamps[0]
        assert stamp.width == 32.0
        assert stamp.height == 37.0
        assert stamp.description == "2 1/2d deep blue"
        assert stamp.shape == StampShape.RECTANGLE

    def test_stamp_add_blank(self, parser):
        """Test parsing STAMP_ADD_BLANK command."""
        source = "PAGE_START\nROW_START_FS (HN 6 0.1 6.0)\nSTAMP_ADD_BLANK (25.0 28.0)"
        album = parser.parse(source)
        stamp = album.pages[0].rows[0].stamps[0]
        assert stamp.width == 25.0
        assert stamp.height == 28.0
        assert stamp.description == ""

    def test_stamp_add_triangle(self, parser):
        """Test parsing STAMP_ADD_TRIANGLE command."""
        source = (
            "PAGE_START\n"
            "ROW_START_FS (HN 6 0.1 6.0)\n"
            'STAMP_ADD_TRIANGLE (25.0 28.0 "Triangle stamp" "sg 1" "" "")'
        )
        album = parser.parse(source)
        stamp = album.pages[0].rows[0].stamps[0]
        assert stamp.shape == StampShape.TRIANGLE

    def test_stamp_add_diamond(self, parser):
        """Test parsing STAMP_ADD_DIAMOND command."""
        source = (
            "PAGE_START\n"
            "ROW_START_FS (HN 6 0.1 6.0)\n"
            'STAMP_ADD_DIAMOND (25.0 28.0 "Diamond stamp" "sg 1" "" "")'
        )
        album = parser.parse(source)
        stamp = album.pages[0].rows[0].stamps[0]
        assert stamp.shape == StampShape.DIAMOND

    def test_stamp_add_oval(self, parser):
        """Test parsing STAMP_ADD_OVAL command."""
        source = (
            "PAGE_START\n"
            "ROW_START_FS (HN 6 0.1 6.0)\n"
            'STAMP_ADD_OVAL (25.0 28.0 "Oval stamp" "sg 1" "" "")'
        )
        album = parser.parse(source)
        stamp = album.pages[0].rows[0].stamps[0]
        assert stamp.shape == StampShape.OVAL

    def test_stamp_heading(self, parser):
        """Test parsing STAMP_HEADING command."""
        source = (
            "PAGE_START\n"
            "ROW_START_FS (HN 6 0.1 6.0)\n"
            'STAMP_ADD (32.0 37.0 "Test" "sg 1" "" "")\n'
            'STAMP_HEADING (HB 10 "Scarce")'
        )
        album = parser.parse(source)
        stamp = album.pages[0].rows[0].stamps[0]
        assert stamp.heading is not None
        assert stamp.heading.font_id == "HB"
        assert stamp.heading.size == 10.0
        assert stamp.heading.text == "Scarce"

    def test_multiple_stamps_in_row(self, parser):
        """Test parsing multiple stamps in a row."""
        source = (
            "PAGE_START\n"
            "ROW_START_FS (HN 6 0.1 6.0)\n"
            'STAMP_ADD (25.0 28.0 "Stamp 1" "sg 1" "" "")\n'
            'STAMP_ADD (25.0 28.0 "Stamp 2" "sg 2" "" "")\n'
            'STAMP_ADD (25.0 28.0 "Stamp 3" "sg 3" "" "")'
        )
        album = parser.parse(source)
        row = album.pages[0].rows[0]
        assert len(row.stamps) == 3


class TestConditionalCommands:
    """Tests for conditional compilation commands."""

    def test_define(self, parser):
        """Test parsing $DEFINE command."""
        source = "$DEFINE (MYFLAG)"
        album = parser.parse(source)
        assert "MYFLAG" in album.defines

    def test_undefine(self, parser):
        """Test parsing $UNDEFINE command."""
        source = "$DEFINE (MYFLAG)\n$UNDEFINE (MYFLAG)"
        album = parser.parse(source)
        assert "MYFLAG" not in album.defines


class TestTextSettings:
    """Tests for text setting commands."""

    def test_char_spacing(self, parser):
        """Test parsing TEXT_CHAR_SPACING command."""
        source = "TEXT_CHAR_SPACING (0.5)"
        album = parser.parse(source)
        assert album.page_setup.text_char_spacing == 0.5

    def test_line_leading(self, parser):
        """Test parsing TEXT_LINE_LEADING command."""
        source = "TEXT_LINE_LEADING (1.5)"
        album = parser.parse(source)
        assert album.page_setup.text_line_leading == 1.5


class TestFullAlbum:
    """Integration tests parsing complete album files."""

    def test_parse_sample_album(self, parser):
        """Test parsing a complete sample album."""
        source = """
ALBUM_TITLE ("Test Album")
ALBUM_PAGES_SIZE (210.0 297.0)
ALBUM_PAGES_MARGINS (20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER (0.1 0.5 0.1 1.0)
ALBUM_PAGES_SPACING (6.0 6.0)
ALBUM_PAGES_TITLE (TB 16 "Test Title")

PAGE_START

PAGE_TEXT (HN 10 "Introduction text goes here.")
PAGE_TEXT_CENTRE (HS 12 "Section Heading")

ROW_START_FS (HN 8 0.5 6.0)
STAMP_ADD (32.0 37.0 "2 1/2d deep blue" "sg 1" "" "sacc 1")
STAMP_ADD (32.0 37.0 "2 1/2d blue" "sg 2" "" "sacc 1a")

PAGE_START

PAGE_TEXT_CENTRE (HN 12 "Second Page")

ROW_START_FS (HN 8 0.5 6.0)
STAMP_ADD (25.0 28.0 "1d green" "sg 3" "" "sacc 2")
"""
        album = parser.parse(source)

        assert album.title == "Test Album"
        assert album.page_setup.width == 210.0
        assert len(album.pages) == 2
        assert len(album.pages[0].rows) == 1
        assert len(album.pages[0].rows[0].stamps) == 2
        assert len(album.pages[1].rows) == 1
