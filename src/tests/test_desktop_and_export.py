"""
Tests for the desktop wrapper and cross-platform export fixes (Phase 1/2).

These guard against the WeasyPrint 68 API-removal regressions:
- PNG/SVG export must work (write_png/write_svg/write_to_image were removed)
- The desktop wrapper must be able to find a free port and boot the server
"""
import socket

import pytest
from fastapi.testclient import TestClient

from stamp_album.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestCrossPlatformExport:
    """PNG and SVG export now go through PyMuPDF, not the removed WeasyPrint API."""

    DSL = 'ALBUM_TITLE("Test")\nALBUM_PAGES_SIZE(210 297)\nPAGE_START\nPAGE_TEXT_CENTER("HN" 14 "Hi")'

    def test_png_export_works(self, client):
        r = client.post("/export", json={"dsl": self.DSL, "format": "png"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/png"
        # PNG magic number
        assert r.content[:8] == b"\x89PNG\r\n\x1a\n"

    def test_png_export_respects_dpi(self, client):
        low = client.post("/export", json={"dsl": self.DSL, "format": "png", "dpi": 72})
        high = client.post("/export", json={"dsl": self.DSL, "format": "png", "dpi": 200})
        assert low.status_code == 200 and high.status_code == 200
        # Higher DPI should produce a larger image
        assert len(high.content) > len(low.content)

    def test_svg_export_works(self, client):
        r = client.post("/export", json={"dsl": self.DSL, "format": "svg"})
        assert r.status_code == 200
        assert "svg" in r.headers["content-type"]
        assert b"<svg" in r.content

    def test_pdf_export_works(self, client):
        r = client.post("/export", json={"dsl": self.DSL, "format": "pdf"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:5] == b"%PDF-"


class TestDesktopWrapper:
    """The desktop wrapper boots the FastAPI app on a free local port."""

    def test_find_free_port(self):
        from stamp_album.desktop import _find_free_port
        port = _find_free_port()
        assert 1024 < port < 65536
        # Port should actually be bindable
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))

    def test_server_thread_importable(self):
        from stamp_album.desktop import _ServerThread, _wait_for_server, main
        assert callable(main)
        assert _ServerThread is not None
        assert callable(_wait_for_server)
