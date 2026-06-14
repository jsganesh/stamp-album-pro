"""
Test column layout HTML rendering with correct gap styling.
"""

import pytest
from stamp_album.core.parser import AlbumParser
from stamp_album.engines.pdf_generator import HTMLRenderer


class TestColumnLayoutRendering:
    """Test suite for column layout HTML rendering."""

    @pytest.fixture
    def parser(self):
        return AlbumParser()

    def test_column_container_renders_with_custom_gap(self, parser):
        """HTML should render column-container div with correct gap style."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (2 15.0)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        renderer = HTMLRenderer(album, None)
        html = renderer.render()

        # Check that column-container is rendered with custom gap
        assert 'class="column-container cols-2"' in html, "Should have column-container with cols-2"
        assert 'gap: 15.0mm' in html, "Should have custom gap of 15.0mm in inline style"

    def test_column_container_renders_with_default_gap(self, parser):
        """HTML should render column-container div with default 10mm gap."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (2)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        renderer = HTMLRenderer(album, None)
        html = renderer.render()

        # Check that column-container is rendered with default gap
        assert 'class="column-container cols-2"' in html, "Should have column-container with cols-2"
        assert 'gap: 10.0mm' in html, "Should have default gap of 10.0mm in inline style"

    def test_three_column_layout_rendering(self, parser):
        """HTML should render three-column layout with correct gap."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (3 12.5)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        renderer = HTMLRenderer(album, None)
        html = renderer.render()

        # Check that three-column container is rendered
        assert 'class="column-container cols-3"' in html, "Should have column-container with cols-3"
        assert 'gap: 12.5mm' in html, "Should have custom gap of 12.5mm in inline style"

    def test_zero_gap_renders_with_default(self, parser):
        """HTML should use default 10mm gap when column_gap is 0."""
        dsl = """
        ALBUM_TITLE ("Test")
        PAGE_START
        PAGE_COLUMN_START (2 0.0)
        STAMP_ADD (32.0 37.0 "test" "" "" "")
        PAGE_END
        """
        album = parser.parse(dsl, "test.slbum")
        renderer = HTMLRenderer(album, None)
        html = renderer.render()

        # When gap is 0, rendering should use default 10.0mm
        assert 'gap: 10.0mm' in html, "Should use default 10.0mm gap when column_gap is 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
