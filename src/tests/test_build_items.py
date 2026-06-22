"""
Tests guarding the build-item drag/click → DSL conversion (Phase 2 UX fix).

The web UI's insertStampElement / insertTextElement / insertRowElement produce
DSL strings that MUST parse cleanly. This test pins the exact DSL shapes the
JS emits so a regression (e.g. raw JSON leaking into the editor) is caught.
"""
import pytest
from stamp_album.core.parser import AlbumParser


@pytest.fixture
def parser():
    return AlbumParser()


# These mirror the exact strings produced by app.js insert* functions.
BUILD_ITEM_DSL = {
    "stamp_rectangle": 'STAMP_ADD(40 30 "New Stamp" "" "" "")',
    "stamp_oval": 'STAMP_ADD_OVAL(40 30 "New Stamp" "" "" "")',
    "stamp_diamond": 'STAMP_ADD_DIAMOND(40 30 "New Stamp" "" "" "")',
    "stamp_triangle": 'STAMP_ADD_TRIANGLE(40 30 "New Stamp" "" "" "")',
    "text_left": 'PAGE_TEXT("HN" 12 "New Text")',
    "text_center": 'PAGE_TEXT_CENTRE("HN" 12 "New Text")',
    "text_right": 'PAGE_TEXT_RIGHT("HN" 12 "New Text")',
    "row_fs": 'ROW_START_FS("HN" 10 5 180)',
    "row_es": 'ROW_START_ES("HN" 10 5 180)',
}


class TestBuildItemDSL:
    """Every build-item produces parseable DSL (not raw JSON)."""

    def test_stamp_rectangle_parses(self, parser):
        dsl = f'PAGE_START\nROW_START_FS("HN" 10 5 180)\n{BUILD_ITEM_DSL["stamp_rectangle"]}'
        album = parser.parse(dsl)
        assert len(album.pages[0].rows[0].stamps) == 1
        stamp = album.pages[0].rows[0].stamps[0]
        assert stamp.width == 40 and stamp.height == 30

    @pytest.mark.parametrize("shape_key", [
        "stamp_rectangle", "stamp_oval", "stamp_diamond", "stamp_triangle",
    ])
    def test_all_stamp_shapes_parse(self, parser, shape_key):
        dsl = f'PAGE_START\nROW_START_FS("HN" 10 5 180)\n{BUILD_ITEM_DSL[shape_key]}'
        album = parser.parse(dsl)
        assert len(album.pages[0].rows[0].stamps) == 1

    @pytest.mark.parametrize("text_key", ["text_left", "text_center", "text_right"])
    def test_text_elements_parse(self, parser, text_key):
        dsl = f'PAGE_START\n{BUILD_ITEM_DSL[text_key]}'
        album = parser.parse(dsl)
        assert len(album.pages[0].text_elements) == 1
        assert album.pages[0].text_elements[0].content == "New Text"

    @pytest.mark.parametrize("row_key", ["row_fs", "row_es"])
    def test_row_elements_parse(self, parser, row_key):
        dsl = f'PAGE_START\n{BUILD_ITEM_DSL[row_key]}'
        album = parser.parse(dsl)
        assert len(album.pages[0].rows) == 1

    def test_full_dropped_sequence_renders(self, parser):
        """A realistic click/drag sequence produces a complete, renderable album."""
        from stamp_album.engines.pdf_generator import HTMLRenderer

        dsl = (
            'ALBUM_TITLE("Test")\n'
            'ALBUM_PAGES_SIZE(210 297)\n'
            'PAGE_START\n'
            'ROW_START_FS("HN" 10 5 180)\n'
            f'{BUILD_ITEM_DSL["stamp_rectangle"]}\n'
            f'{BUILD_ITEM_DSL["stamp_oval"]}\n'
            f'{BUILD_ITEM_DSL["text_center"]}'
        )
        album = parser.parse(dsl)
        html = HTMLRenderer(album, None).render()
        assert "stamp" in html.lower()
        assert "New Stamp" in html

    def test_raw_json_is_not_valid_dsl(self, parser):
        """Sanity check: the leaked JSON payload should NOT parse as stamps.

        This documents the bug we fixed — raw '{"type":"stamp"...}' in the
        editor must not silently look like valid content.
        """
        raw_json = 'PAGE_START\n{"type":"stamp","shape":"rectangle","width":40,"height":30}'
        album = parser.parse(raw_json)
        # The JSON line is not a recognized command, so no stamps are created
        total_stamps = sum(len(r.stamps) for p in album.pages for r in p.rows)
        assert total_stamps == 0
