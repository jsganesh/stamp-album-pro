"""
Tests for inline text formatting (P2-1).
"""
import pytest
from stamp_album.engines.pdf_generator import HTMLRenderer
from stamp_album.core.models import Album, FormattedText, TextAlignment


@pytest.fixture
def renderer():
    album = Album()
    return HTMLRenderer(album, None)


class TestInlineFormatting:
    """Tests for _parse_inline_formatting."""

    def test_bold_doublestar(self, renderer):
        result = renderer._parse_inline_formatting("This is **bold** text")
        assert "<strong>bold</strong>" in result

    def test_bold_double_underscore(self, renderer):
        result = renderer._parse_inline_formatting("This is __bold__ text")
        assert "<strong>bold</strong>" in result

    def test_italic_star(self, renderer):
        result = renderer._parse_inline_formatting("This is *italic* text")
        assert "<em>italic</em>" in result

    def test_italic_underscore(self, renderer):
        result = renderer._parse_inline_formatting("This is _italic_ text")
        assert "<em>italic</em>" in result

    def test_bold_italic(self, renderer):
        result = renderer._parse_inline_formatting("***bold+italic***")
        assert "<strong><em>bold+italic</em></strong>" in result

    def test_strikethrough(self, renderer):
        result = renderer._parse_inline_formatting("~~deleted~~")
        assert "<s>deleted</s>" in result

    def test_code(self, renderer):
        result = renderer._parse_inline_formatting("Use `code` here")
        assert "<code" in result
        assert "code" in result

    def test_superscript(self, renderer):
        result = renderer._parse_inline_formatting("E=mc^2^")
        assert "<sup>2</sup>" in result

    def test_subscript(self, renderer):
        result = renderer._parse_inline_formatting("H~2~O")
        assert "<sub>2</sub>" in result

    def test_escaped_markers(self, renderer):
        result = renderer._parse_inline_formatting(r"Use \* for multiplication")
        assert "* for multiplication" in result
        assert "<em>" not in result

    def test_multiple_formats(self, renderer):
        result = renderer._parse_inline_formatting("**Bold** and *italic* and ~~strike~~")
        assert "<strong>Bold</strong>" in result
        assert "<em>italic</em>" in result
        assert "<s>strike</s>" in result

    def test_html_escaping(self, renderer):
        result = renderer._format_text("Use <b> & **bold**")
        assert "&lt;b&gt;" in result
        assert "&amp;" in result
        assert "<strong>bold</strong>" in result

    def test_newlines_preserved(self, renderer):
        result = renderer._format_text("Line 1\nLine 2")
        assert "<br>" in result

    def test_empty_string(self, renderer):
        result = renderer._format_text("")
        assert result == ""

    def test_no_formatting(self, renderer):
        result = renderer._format_text("Plain text without markers")
        assert result == "Plain text without markers"
