"""
Tests for drop caps (P2-2), text shadows/outlines (P2-3), and gradient fills (P2-4).
"""
import pytest
from stamp_album.engines.pdf_generator import HTMLRenderer
from stamp_album.core.models import (
    Album, FormattedText, TextAlignment, Color, TextShadow, TextOutline,
    GradientFill, GradientStop,
)


@pytest.fixture
def renderer():
    album = Album()
    return HTMLRenderer(album, None)


class TestDropCaps:
    """Tests for drop cap rendering."""

    def test_no_drop_cap(self, renderer):
        ft = FormattedText(content="Hello world", size=12)
        html = renderer._render_text_element(ft)
        assert "float: left" not in html

    def test_drop_cap_rendered(self, renderer):
        ft = FormattedText(content="Hello world", size=12, drop_cap_lines=2)
        html = renderer._render_text_element(ft)
        assert "float: left" in html
        assert "font-size: 24pt" in html  # 12 * 2

    def test_drop_cap_3_lines(self, renderer):
        ft = FormattedText(content="Once upon a time", size=10, drop_cap_lines=3)
        html = renderer._render_text_element(ft)
        assert "font-size: 30pt" in html  # 10 * 3


class TestTextShadow:
    """Tests for text shadow rendering."""

    def test_no_shadow(self, renderer):
        ft = FormattedText(content="Hello")
        html = renderer._render_text_element(ft)
        assert "text-shadow" not in html

    def test_shadow_rendered(self, renderer):
        ft = FormattedText(
            content="Shadow text",
            shadow=TextShadow(offset_x=1, offset_y=-1, blur=0.5, color=Color(r=0, g=0, b=0), opacity=0.5),
        )
        html = renderer._render_text_element(ft)
        assert "text-shadow" in html
        assert "rgba(0, 0, 0, 0.5)" in html


class TestTextOutline:
    """Tests for text outline rendering."""

    def test_no_outline(self, renderer):
        ft = FormattedText(content="Hello")
        html = renderer._render_text_element(ft)
        assert "text-stroke" not in html

    def test_outline_rendered(self, renderer):
        ft = FormattedText(
            content="Outlined",
            outline=TextOutline(width=0.3, color=Color(r=0, g=0, b=0)),
        )
        html = renderer._render_text_element(ft)
        assert "-webkit-text-stroke" in html


class TestGradientFill:
    """Tests for gradient text fill rendering."""

    def test_no_gradient(self, renderer):
        ft = FormattedText(content="Hello")
        html = renderer._render_text_element(ft)
        assert "background-clip: text" not in html

    def test_gradient_rendered(self, renderer):
        ft = FormattedText(
            content="Gradient",
            gradient=GradientFill(
                direction="horizontal",
                stops=[
                    GradientStop(offset=0, color=Color(r=1, g=0, b=0)),
                    GradientStop(offset=1, color=Color(r=0, g=0, b=1)),
                ],
            ),
        )
        html = renderer._render_text_element(ft)
        assert "background-clip: text" in html
        assert "linear-gradient" in html
        assert "-webkit-text-fill-color: transparent" in html

    def test_gradient_vertical(self, renderer):
        ft = FormattedText(
            content="Vertical",
            gradient=GradientFill(
                direction="vertical",
                stops=[
                    GradientStop(offset=0, color=Color(r=1, g=0, b=0)),
                    GradientStop(offset=1, color=Color(r=0, g=0, b=1)),
                ],
            ),
        )
        html = renderer._render_text_element(ft)
        assert "180deg" in html
