"""The Python parser reads the stamp details the editor saves (heading, catalogue, details line)."""

from stamp_album.core.parser import AlbumParser

DSL = "\n".join(
    [
        "ALBUM_PAGES_SIZE(210 297)",
        "PAGE_START",
        'STAMP_ADD_AT(20.0 30.0 40.0 30.0 "Penny Black — 1840" "SG#1" "" "" rectangle "double" "#000" 1 "#ffffff" 100)',
        'STAMP_HEADING("HN" 9 "Penny Black")',
        'STAMP_DETAILS("1/2D" "Used" "Imperforate")',
        'STAMP_ADD_AT(80.0 30.0 40.0 30.0 "Bare" "" "" "" rectangle "solid" "#000" 0.5 "#ffffff" 100)',
        'STAMP_ADD_AT(20.0 90.0 40.0 30.0 "Only condition" "" "" "" oval "solid" "#000" 0.5 "#ffffff" 100)',
        'STAMP_DETAILS("" "Mint NH" "")',
    ]
)


def _stamps():
    return AlbumParser().parse(DSL).pages[0].absolute_stamps


def test_heading_catalogue_and_details_are_read():
    s = _stamps()[0]
    assert s.description == "Penny Black — 1840"
    assert s.heading is not None and s.heading.text == "Penny Black"
    assert s.catalog_refs == ["SG#1"]
    assert s.footer_text == "1/2D · Used · Imperforate"


def test_a_stamp_without_details_gets_none():
    s = _stamps()[1]
    assert s.heading is None
    assert s.catalog_refs == []
    assert s.footer_text == ""


def test_partial_details_skip_the_empty_parts():
    assert _stamps()[2].footer_text == "Mint NH"


def test_empty_catalogue_fields_are_not_printed():
    # Before, ["", "", ""] made the exports print " ·  · " under every stamp.
    album = AlbumParser().parse('PAGE_START\nSTAMP_ADD_AT(20 20 40 30 "x" "" "" "")')
    assert album.pages[0].absolute_stamps[0].catalog_refs == []
