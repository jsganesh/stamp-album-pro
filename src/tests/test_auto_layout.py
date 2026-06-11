"""
Tests for auto-layout API endpoint (P2-6).
"""
import io
import pytest
from fastapi.testclient import TestClient

from stamp_album.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestAutoLayout:
    """Tests for the auto-layout API endpoint."""

    def test_auto_layout_row_first(self, client):
        dsl = """ALBUM_TITLE("Test")
PAGE_START
ROW_START_FS("HN" 8 5 180)
STAMP_ADD(40 30 "Stamp 1" "" "" "")
STAMP_ADD(40 30 "Stamp 2" "" "" "")
STAMP_ADD(40 30 "Stamp 3" "" "" "")
"""
        response = client.post("/api/auto-layout", json={
            "dsl": dsl,
            "strategy": "row_first",
            "page_idx": 0,
        })
        assert response.status_code == 200
        result = response.json()
        assert result["stamps_arranged"] == 3
        assert result["rows_created"] >= 1
        assert "dsl" in result

    def test_auto_layout_balanced(self, client):
        dsl = """ALBUM_TITLE("Test")
PAGE_START
ROW_START_FS("HN" 8 5 180)
STAMP_ADD(30 25 "A" "" "" "")
STAMP_ADD(30 25 "B" "" "" "")
STAMP_ADD(30 25 "C" "" "" "")
STAMP_ADD(30 25 "D" "" "" "")
"""
        response = client.post("/api/auto-layout", json={
            "dsl": dsl,
            "strategy": "balanced",
            "page_idx": 0,
        })
        assert response.status_code == 200
        result = response.json()
        assert result["stamps_arranged"] == 4

    def test_auto_layout_empty_page(self, client):
        dsl = """ALBUM_TITLE("Test")
PAGE_START
"""
        response = client.post("/api/auto-layout", json={
            "dsl": dsl,
            "strategy": "row_first",
            "page_idx": 0,
        })
        assert response.status_code == 400

    def test_auto_layout_invalid_page(self, client):
        dsl = """ALBUM_TITLE("Test")
PAGE_START
ROW_START_FS("HN" 8 5 180)
STAMP_ADD(40 30 "Stamp" "" "" "")
"""
        response = client.post("/api/auto-layout", json={
            "dsl": dsl,
            "strategy": "row_first",
            "page_idx": 99,
        })
        assert response.status_code == 400

    def test_auto_layout_invalid_dsl(self, client):
        response = client.post("/api/auto-layout", json={
            "dsl": "INVALID DSL SYNTAX !!!",
            "strategy": "row_first",
            "page_idx": 0,
        })
        assert response.status_code == 400

    def test_auto_layout_grid_strategy(self, client):
        dsl = """ALBUM_TITLE("Test")
PAGE_START
ROW_START_FS("HN" 8 5 180)
STAMP_ADD(25 20 "S1" "" "" "")
STAMP_ADD(25 20 "S2" "" "" "")
STAMP_ADD(25 20 "S3" "" "" "")
STAMP_ADD(25 20 "S4" "" "" "")
"""
        response = client.post("/api/auto-layout", json={
            "dsl": dsl,
            "strategy": "grid",
            "page_idx": 0,
        })
        assert response.status_code == 200
        result = response.json()
        assert result["stamps_arranged"] == 4

    def test_auto_layout_preserves_content(self, client):
        dsl = """ALBUM_TITLE("My Album")
PAGE_START
PAGE_TEXT_CENTER("HN" 14 "Introduction")
ROW_START_FS("HN" 8 5 180)
STAMP_ADD(40 30 "Penny Black" "SG 1" "" "")
"""
        response = client.post("/api/auto-layout", json={
            "dsl": dsl,
            "strategy": "row_first",
            "page_idx": 0,
        })
        assert response.status_code == 200
        result = response.json()
        # The title text should still be in the output
        assert "My Album" in result["dsl"] or "PAGE_TEXT" in result["dsl"]
