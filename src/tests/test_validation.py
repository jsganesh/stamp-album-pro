"""
Tests for parser validation and error reporting.
"""
import pytest

from stamp_album.core.models import Album, Color, Page, Row, Stamp
from stamp_album.core.parser import AlbumParser, ParseError


class TestParseError:
    """Tests for the ParseError exception."""

    def test_basic_message(self):
        e = ParseError("Something went wrong")
        assert str(e) == "Something went wrong"

    def test_with_line_number(self):
        e = ParseError("Bad syntax", line_number=42)
        assert "line 42" in str(e)

    def test_with_line_text(self):
        e = ParseError("Bad syntax", line_text='PAGE_TEXT("HN" 10 "test")')
        assert 'PAGE_TEXT' in str(e)

    def test_with_all_info(self):
        e = ParseError("Bad syntax", line_number=5, line_text="FOO")
        msg = str(e)
        assert "Bad syntax" in msg
        assert "line 5" in msg
        assert "FOO" in msg

    def test_attributes(self):
        e = ParseError("test", line_number=10, line_text="bar")
        assert e.line_number == 10
        assert e.line_text == "bar"


class TestParserValidation:
    """Tests for the validate() method."""

    @pytest.fixture
    def parser(self):
        return AlbumParser()

    def test_no_pages_warning(self, parser):
        album = Album()
        warnings = parser.validate(album)
        assert any("no pages" in w.lower() for w in warnings)

    def test_empty_page_warning(self, parser):
        album = Album()
        album.pages.append(Page())
        warnings = parser.validate(album)
        assert any("empty page" in w.lower() for w in warnings)

    def test_zero_size_stamp_warning(self, parser):
        album = Album()
        page = Page()
        row = Row()
        row.stamps.append(Stamp(width=0, height=0, description="invisible"))
        page.rows.append(row)
        album.pages.append(page)
        warnings = parser.validate(album)
        assert any("zero-size" in w.lower() for w in warnings)

    def test_zero_width_stamp_warning(self, parser):
        album = Album()
        page = Page()
        row = Row()
        row.stamps.append(Stamp(width=0, height=30))
        page.rows.append(row)
        album.pages.append(page)
        warnings = parser.validate(album)
        assert any("zero width" in w.lower() for w in warnings)

    def test_zero_height_stamp_warning(self, parser):
        album = Album()
        page = Page()
        row = Row()
        row.stamps.append(Stamp(width=40, height=0))
        page.rows.append(row)
        album.pages.append(page)
        warnings = parser.validate(album)
        assert any("zero height" in w.lower() for w in warnings)

    def test_valid_album_no_warnings(self, parser):
        album = Album()
        page = Page()
        row = Row()
        row.stamps.append(Stamp(width=40, height=30, description="Normal stamp"))
        page.rows.append(row)
        album.pages.append(page)
        warnings = parser.validate(album)
        assert len(warnings) == 0

    def test_empty_row_warning(self, parser):
        album = Album()
        page = Page()
        page.rows.append(Row())
        album.pages.append(page)
        warnings = parser.validate(album)
        assert any("no stamps" in w.lower() for w in warnings)


class TestParserErrors:
    """Tests that parser raises ParseError for structural issues."""

    @pytest.fixture
    def parser(self):
        return AlbumParser()

    def test_text_outside_page_raises(self, parser):
        with pytest.raises(ParseError, match="outside of PAGE_START"):
            parser.parse('PAGE_TEXT("HN" 10 "test")')

    def test_row_outside_page_raises(self, parser):
        with pytest.raises(ParseError, match="outside of PAGE_START"):
            parser.parse('ROW_START_FS("HN" 10 5 180)')

    def test_stamp_outside_row_raises(self, parser):
        with pytest.raises(ParseError, match="outside of ROW_START"):
            parser.parse('PAGE_START\nSTAMP_ADD(40 30 "test" "" "" "")')

    def test_blank_stamp_outside_row_raises(self, parser):
        with pytest.raises(ParseError, match="outside of ROW_START"):
            parser.parse('PAGE_START\nSTAMP_ADD_BLANK(40 30)')

    def test_stamp_img_outside_row_raises(self, parser):
        with pytest.raises(ParseError, match="outside of ROW_START"):
            parser.parse('PAGE_START\nSTAMP_ADD_IMG(40 30 "img.png" "test" "" "")')

    def test_triangle_stamp_outside_row_raises(self, parser):
        with pytest.raises(ParseError, match="outside of ROW_START"):
            parser.parse('PAGE_START\nSTAMP_ADD_TRIANGLE(40 30 "test" "" "" "")')

    def test_error_includes_line_number(self, parser):
        with pytest.raises(ParseError) as exc_info:
            parser.parse('PAGE_TEXT("HN" 10 "test")')
        assert exc_info.value.line_number == 1

    def test_error_line_number_multiline(self, parser):
        # STAMP_ADD outside ROW_START on line 3
        with pytest.raises(ParseError) as exc_info:
            parser.parse('PAGE_START\nPAGE_TEXT("HN" 10 "ok")\nSTAMP_ADD(40 30 "test" "" "" "")')
        assert exc_info.value.line_number == 3
