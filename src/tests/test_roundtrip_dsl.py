"""
Round-trip test: parse(DSL) → serialize → parse(result) → field-by-field comparison.

Guards against silent data loss when saving canvas-placed content.
"""

import pytest

from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.core.models import StampShape


# A fixture album exercising all content types
FIXTURE_DSL = r"""
ALBUM_TITLE("Round-Trip Test")
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

# Row-based stamps with catalog refs
ROW_START_FS(HN 8 0.5 180)
STAMP_ADD(32 37 "2 1/2d deep blue" "sg 1" "" "sacc 1")
STAMP_ADD_OVAL(28 33 "1d rose red" "sg 2" "" "sacc 2a")
STAMP_ADD_DIAMOND(28 33 "4d sage green" "sg 3" "" "sacc 3")
STAMP_ADD(32 37 "without catalog" "" "" "")

# Absolute stamps
STAMP_ADD_AT(15 140 40 30 "6d violet" "sg 4" "scott 5" "sacc 4")
STAMP_ADD_AT(70 80 50 40 "oval issue" "" "" "" OVAL)
STAMP_ADD_AT(125 30 40 40 "diamond" "sg 25" "" "" DIAMOND)

# Text element at absolute position
PAGE_TEXT_AT(15 200 180 12 HN 10 "A free-form note." LEFT)

PAGE_START

ROW_START_FS(HN 8 0.5 180)
STAMP_ADD(32 37 "1/2d yellow green" "sg 7" "" "sacc 6")
STAMP_ADD_HEXAGON(30 35 "hexagonal" "sg 10" "" "sacc 9")

STAMP_ADD_AT(20 40 45 35 "page two stamp" "" "" "")
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _catalog_set(stamp):
    """Return set of non-empty catalog refs for easy comparison."""
    return {r for r in (stamp.catalog_refs or []) if r}


def _fields(stamp):
    return (
        stamp.abs_x, stamp.abs_y, stamp.width, stamp.height,
        stamp.description,
        stamp.shape,
        stamp.is_text_element,
        stamp.font_id, stamp.font_size,
        frozenset(_catalog_set(stamp)),
        stamp.heading,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRoundTrip:
    """parse → serialize → parse → compare."""

    @pytest.fixture
    def parser(self):
        return AlbumParser()

    @pytest.fixture
    def serializer(self):
        return AlbumSerializer()

    def _roundtrip(self, parser, serializer, dsl, source_path="test.slbum"):
        album1 = parser.parse(dsl, source_path)
        dsl2 = serializer.to_dsl(album1)
        album2 = parser.parse(dsl2, source_path)
        return album1, album2, dsl2

    def test_page_count_preserved(self, parser, serializer):
        a1, a2, dsl2 = self._roundtrip(parser, serializer, FIXTURE_DSL)
        assert len(a1.pages) == len(a2.pages), f"Page count mismatch\n{dsl2}"

    def test_page_setup_preserved(self, parser, serializer):
        a1, a2, _ = self._roundtrip(parser, serializer, FIXTURE_DSL)
        ps1 = a1.page_setup
        ps2 = a2.page_setup
        assert ps1.width == ps2.width
        assert ps1.height == ps2.height
        assert ps1.margin_left == ps2.margin_left
        assert ps1.has_border == ps2.has_border
        assert ps1.border_style == ps2.border_style

    def test_row_stamps_preserved(self, parser, serializer):
        a1, a2, dsl2 = self._roundtrip(parser, serializer, FIXTURE_DSL)
        for pi in range(len(a1.pages)):
            for ri in range(len(a1.pages[pi].rows)):
                s1 = a1.pages[pi].rows[ri].stamps
                s2 = a2.pages[pi].rows[ri].stamps
                assert len(s1) == len(s2), (
                    f"Row {pi}.{ri} stamp count mismatch\n{dsl2}"
                )
                for si in range(len(s1)):
                    assert _fields(s1[si]) == _fields(s2[si]), (
                        f"Row {pi}.{ri}.{si} field mismatch\n"
                        f"  Original: {s1[si]}\n"
                        f"  Round-trip: {s2[si]}"
                    )

    def test_absolute_stamps_preserved(self, parser, serializer):
        a1, a2, dsl2 = self._roundtrip(parser, serializer, FIXTURE_DSL)
        for pi in range(len(a1.pages)):
            s1 = a1.pages[pi].absolute_stamps
            s2 = a2.pages[pi].absolute_stamps
            assert len(s1) == len(s2), (
                f"Page {pi} absolute stamp count mismatch\n{dsl2}"
            )
            for si in range(len(s1)):
                assert _fields(s1[si]) == _fields(s2[si]), (
                    f"Page {pi} absolute stamp {si} field mismatch\n"
                    f"  Original: {s1[si]}\n"
                    f"  Round-trip: {s2[si]}"
                )

    def test_text_elements_preserved(self, parser, serializer):
        a1, a2, dsl2 = self._roundtrip(parser, serializer, FIXTURE_DSL)
        for pi in range(len(a1.pages)):
            abs1 = [s for s in a1.pages[pi].absolute_stamps if s.is_text_element]
            abs2 = [s for s in a2.pages[pi].absolute_stamps if s.is_text_element]
            assert len(abs1) == len(abs2), (
                f"Page {pi} text element count mismatch\n{dsl2}"
            )
            for si in range(len(abs1)):
                assert _fields(abs1[si]) == _fields(abs2[si])

    def test_shapes_preserved(self, parser, serializer):
        a1, a2, dsl2 = self._roundtrip(parser, serializer, FIXTURE_DSL)
        # Check absolute stamps shapes
        shapes1 = set()
        shapes2 = set()
        for pi in range(len(a1.pages)):
            for s in a1.pages[pi].absolute_stamps:
                if not s.is_text_element:
                    shapes1.add(s.shape)
            for s in a2.pages[pi].absolute_stamps:
                if not s.is_text_element:
                    shapes2.add(s.shape)
        assert shapes1 == shapes2, (
            f"Absolute stamp shapes differ: {shapes1} vs {shapes2}\n{dsl2}"
        )

    def test_catalog_refs_preserved_in_row_stamps(self, parser, serializer):
        """Row-based stamps with catalog refs keep them through round-trip."""
        a1, a2, dsl2 = self._roundtrip(parser, serializer, FIXTURE_DSL)
        for pi in range(len(a1.pages)):
            for ri in range(len(a1.pages[pi].rows)):
                for si in range(len(a1.pages[pi].rows[ri].stamps)):
                    s1 = a1.pages[pi].rows[ri].stamps[si]
                    s2 = a2.pages[pi].rows[ri].stamps[si]
                    assert _catalog_set(s1) == _catalog_set(s2), (
                        f"Page {pi} row {ri} stamp {si} catalog refs: "
                        f"{s1.catalog_refs} vs {s2.catalog_refs}\n{dsl2}"
                    )

    def test_catalog_refs_preserved_in_absolute_stamps(self, parser, serializer):
        a1, a2, dsl2 = self._roundtrip(parser, serializer, FIXTURE_DSL)
        for pi in range(len(a1.pages)):
            for si in range(len(a1.pages[pi].absolute_stamps)):
                s1 = a1.pages[pi].absolute_stamps[si]
                s2 = a2.pages[pi].absolute_stamps[si]
                if not s1.is_text_element:
                    assert _catalog_set(s1) == _catalog_set(s2), (
                        f"Page {pi} absolute stamp {si} catalog refs: "
                        f"{s1.catalog_refs} vs {s2.catalog_refs}\n{dsl2}"
                    )
