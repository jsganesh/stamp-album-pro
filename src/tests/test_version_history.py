"""
Tests for version history (P2-15).
"""
import pytest
from fastapi.testclient import TestClient

from stamp_album.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestVersionHistory:
    """Tests for version history API."""

    def test_save_version(self, client):
        response = client.post("/api/version/save", json={
            "filename": "test.slbum",
            "dsl": 'ALBUM_TITLE("Test")\nPAGE_START',
            "comment": "First version",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.slbum"
        assert data["comment"] == "First version"
        assert "id" in data

    def test_get_versions(self, client):
        client.post("/api/version/save", json={"filename": "test2.slbum", "dsl": "content"})
        response = client.get("/api/version/list/test2.slbum")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_get_specific_version(self, client):
        save_resp = client.post("/api/version/save", json={
            "filename": "test3.slbum",
            "dsl": "specific content here",
        })
        version_id = save_resp.json()["id"]
        response = client.get(f"/api/version/get/test3.slbum/{version_id}")
        assert response.status_code == 200
        assert response.json()["dsl"] == "specific content here"

    def test_get_nonexistent_version(self, client):
        response = client.get("/api/version/get/test.slbum/nonexistent")
        assert response.status_code == 404

    def test_delete_version(self, client):
        save_resp = client.post("/api/version/save", json={
            "filename": "test4.slbum",
            "dsl": "to delete",
        })
        version_id = save_resp.json()["id"]
        response = client.delete(f"/api/version/delete/test4.slbum/{version_id}")
        assert response.status_code == 200
        get_resp = client.get(f"/api/version/get/test4.slbum/{version_id}")
        assert get_resp.status_code == 404

    def test_save_empty_dsl_fails(self, client):
        response = client.post("/api/version/save", json={
            "filename": "test.slbum",
            "dsl": "",
        })
        assert response.status_code == 400

    def test_save_no_filename_fails(self, client):
        response = client.post("/api/version/save", json={
            "filename": "",
            "dsl": "content",
        })
        assert response.status_code == 400
