"""
Tests for the core data models.
"""


from stamp_album.core.models import (
    Album,
    Color,
    FontDefinition,
    FormattedText,
    Page,
    PageSetup,
    Row,
    RowAlignment,
    RowStyle,
    Stamp,
    StampShape,
    TextAlignment,
)


class TestColor:
    """Tests for the Color data class."""

    def test_default_color(self):
        c = Color()
        assert c.r == 0.0
        assert c.g == 0.0
        assert c.b == 0.0

    def test_from_name(self):
        c = Color.from_name("red")
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.0

    def test_from_name_blue(self):
        c = Color.from_name("blue")
        assert c.r == 0.0
        assert c.g == 0.0
        assert c.b == 1.0

    def test_from_rgb(self):
        c = Color.from_rgb(255, 128, 64)
        assert c.r == 1.0
        assert abs(c.g - 0.502) < 0.01
        assert abs(c.b - 0.251) < 0.01

    def test_from_hex(self):
        c = Color.from_hex("#FF0000")
        assert c.r == 1.0
        assert c.g == 0.0
        assert c.b == 0.0

    def test_from_hex_gray(self):
        c = Color.from_hex("#808080")
        assert abs(c.r - 0.502) < 0.01
        assert abs(c.g - 0.502) < 0.01
        assert abs(c.b - 0.502) < 0.01

    def test_invalid_color_name(self):
        # Unknown colors now return black instead of raising ValueError
        c = Color.from_name("notacolor")
        assert c.r == 0.0
        assert c.g == 0.0
        assert c.b == 0.0

    def test_to_tuple(self):
        c = Color(r=0.5, g=0.5, b=0.5)
        assert c.to_tuple() == (0.5, 0.5, 0.5)


class TestFormattedText:
    """Tests for the FormattedText data class."""

    def test_defaults(self):
        ft = FormattedText()
        assert ft.font_id == "HN"
        assert ft.size == 10.0
        assert ft.content == ""
        assert ft.alignment == TextAlignment.LEFT

    def test_custom_values(self):
        ft = FormattedText(
            font_id="TB",
            size=16.0,
            content="Hello World",
            alignment=TextAlignment.CENTER,
        )
        assert ft.font_id == "TB"
        assert ft.size == 16.0
        assert ft.content == "Hello World"
        assert ft.alignment == TextAlignment.CENTER


class TestStamp:
    """Tests for the Stamp data class."""

    def test_defaults(self):
        stamp = Stamp()
        assert stamp.width == 0.0
        assert stamp.height == 0.0
        assert stamp.shape == StampShape.RECTANGLE
        assert stamp.catalog_refs == []

    def test_with_values(self):
        stamp = Stamp(
            width=32.0,
            height=37.0,
            description="2 1/2d deep blue",
            catalog_refs=["sg 1", "", "sacc 1"],
        )
        assert stamp.width == 32.0
        assert stamp.height == 37.0
        assert stamp.description == "2 1/2d deep blue"
        assert len(stamp.catalog_refs) == 3


class TestRow:
    """Tests for the Row data class."""

    def test_defaults(self):
        row = Row()
        assert row.style == RowStyle.FIXED_SPACE
        assert row.alignment == RowAlignment.TOP
        assert row.stamps == []

    def test_add_stamps(self):
        row = Row()
        row.stamps.append(Stamp(width=25.0, height=28.0))
        row.stamps.append(Stamp(width=25.0, height=28.0))
        assert len(row.stamps) == 2


class TestPage:
    """Tests for the Page data class."""

    def test_defaults(self):
        page = Page()
        assert page.title is None
        assert page.text_elements == []
        assert page.rows == []

    def test_add_text(self):
        page = Page()
        page.text_elements.append(
            FormattedText(content="Test text", alignment=TextAlignment.CENTER)
        )
        assert len(page.text_elements) == 1


class TestAlbum:
    """Tests for the Album data class."""

    def test_defaults(self):
        album = Album()
        assert album.title == ""
        assert album.author == ""
        assert album.pages == []
        assert album.fonts == []

    def test_add_page(self):
        album = Album()
        album.pages.append(Page())
        album.pages.append(Page())
        assert len(album.pages) == 2

    def test_add_font(self):
        album = Album()
        album.fonts.append(FontDefinition(font_id="MY", font_name="My Font"))
        assert len(album.fonts) == 1
        assert album.fonts[0].font_id == "MY"


class TestPageSetup:
    """Tests for the PageSetup data class."""

    def test_default_a4(self):
        ps = PageSetup()
        assert ps.width == 210.0
        assert ps.height == 297.0

    def test_custom_size(self):
        ps = PageSetup(width=215.9, height=279.4)
        assert ps.width == 215.9
        assert ps.height == 279.4

    def test_margins(self):
        ps = PageSetup(
            margin_left=25.0,
            margin_right=12.0,
            margin_top=15.0,
            margin_bottom=15.0,
        )
        assert ps.margin_left == 25.0
        assert ps.margin_right == 12.0
