"""
Tests for drag-and-drop stamp placement (P2-12).
"""
import pytest
from stamp_album.core.parser import AlbumParser, ParseError
from stamp_album.core.models import StampShape


@pytest.fixture
def parser():
    return AlbumParser()


class TestStampAddAt:
    """Tests for STAMP_ADD_AT command."""

    def test_basic_absolute_position(self, parser):
        source = """PAGE_START
STAMP_ADD_AT(10.0 20.0 40 30 "Test Stamp" "" "" "")
"""
        album = parser.parse(source)
        assert len(album.pages) == 1
        assert len(album.pages[0].absolute_stamps) == 1
        stamp = album.pages[0].absolute_stamps[0]
        assert stamp.abs_x == 10.0
        assert stamp.abs_y == 20.0
        assert stamp.width == 40
        assert stamp.height == 30
        assert stamp.description == "Test Stamp"

    def test_multiple_absolute_stamps(self, parser):
        source = """PAGE_START
STAMP_ADD_AT(10 20 40 30 "First" "" "" "")
STAMP_ADD_AT(60 20 40 30 "Second" "" "" "")
"""
        album = parser.parse(source)
        assert len(album.pages[0].absolute_stamps) == 2
        assert album.pages[0].absolute_stamps[0].abs_x == 10
        assert album.pages[0].absolute_stamps[1].abs_x == 60

    def test_absolute_stamp_outside_page_raises(self, parser):
        with pytest.raises(ParseError, match="outside of PAGE_START"):
            parser.parse('STAMP_ADD_AT(10 20 40 30 "Test" "" "" "")')

    def test_absolute_stamp_with_catalog_refs(self, parser):
        source = """PAGE_START
STAMP_ADD_AT(10 20 40 30 "Stamp" "SG 1" "" "sacc 1")
"""
        album = parser.parse(source)
        stamp = album.pages[0].absolute_stamps[0]
        assert stamp.description == "Stamp"
        assert stamp.catalog_refs == ["SG 1", "", "sacc 1"]

    def test_mixed_row_and_absolute_stamps(self, parser):
        source = """PAGE_START
ROW_START_FS("HN" 8 5 180)
STAMP_ADD(40 30 "Row Stamp" "" "" "")
STAMP_ADD_AT(10 60 40 30 "Absolute Stamp" "" "" "")
"""
        album = parser.parse(source)
        assert len(album.pages[0].rows) == 1
        assert len(album.pages[0].rows[0].stamps) == 1
        assert len(album.pages[0].absolute_stamps) == 1
