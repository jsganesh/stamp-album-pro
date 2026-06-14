"""
Tests for column layout parsing and rendering fixes.
"""

import pytest
from stamp_album.core.parser import AlbumParser, ParseError
from stamp_album.core.models import ColumnMode


class TestColumnLayoutFixes:
    """Test suite for column layout bug fixes."""

    @pytest.fixture
    def parser(self):
        return AlbumParser()

    def test_page_column_start_two_columns_default_gap(self, parser):
        """PAGE_COLUMN_START with 2 columns should use default 10mm gap."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (2)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        # Note: column_mode is set by PAGE_COLUMN_START for the entire page
        assert album.pages[0].column_mode == ColumnMode.TWO
        assert album.pages[0].column_gap == 10.0, "Should use default 10mm gap"

    def test_page_column_start_two_columns_custom_gap(self, parser):
        """PAGE_COLUMN_START with 2 columns and custom gap."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (2 15.0)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        assert album.pages[0].column_mode == ColumnMode.TWO
        assert album.pages[0].column_gap == 15.0, "Should use custom 15mm gap"

    def test_page_column_start_three_columns_custom_gap(self, parser):
        """PAGE_COLUMN_START with 3 columns and custom gap."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (3 8.5)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        assert album.pages[0].column_mode == ColumnMode.THREE
        assert album.pages[0].column_gap == 8.5, "Should use custom 8.5mm gap"

    def test_page_column_next_no_parse_error(self, parser):
        """PAGE_COLUMN_NEXT should not cause parse error (was unhandled before)."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (2)
        PAGE_TEXT (HN 10 "Col 1")
        PAGE_COLUMN_NEXT
        PAGE_TEXT (HN 10 "Col 2")
        PAGE_END
        """
        # This should not raise ParseError
        album = parser.parse(dsl, "test.slbum")
        assert album.pages[0].column_mode == ColumnMode.TWO
        # Verify both text elements are in content_flow
        text_count = sum(1 for ctype, _ in album.pages[0].content_flow if ctype == "text")
        assert text_count == 2, "Both text elements should be present"

    def test_page_column_stop_resets_mode(self, parser):
        """PAGE_COLUMN_STOP should reset column mode to NONE for subsequent content."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (2)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_COLUMN_STOP
        PAGE_TEXT (HN 10 "After column")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        # After PAGE_COLUMN_STOP, mode is reset to NONE for the page
        # This means rendering won't use columns for the entire page
        assert album.pages[0].column_mode == ColumnMode.NONE

    def test_column_layout_gap_zero_uses_default(self, parser):
        """Column gap of 0 should be stored as-is (rendering will use default 10.0)."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (2 0.0)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        # 0.0 is stored as-is, but rendering will use default
        assert album.pages[0].column_gap == 0.0

    def test_column_layout_one_column(self, parser):
        """PAGE_COLUMN_START with 1 column should set ColumnMode.ONE."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (1)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        assert album.pages[0].column_mode == ColumnMode.ONE

    def test_column_layout_invalid_column_count(self, parser):
        """PAGE_COLUMN_START with invalid count (>3) should set ColumnMode.NONE."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (4)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        assert album.pages[0].column_mode == ColumnMode.NONE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
