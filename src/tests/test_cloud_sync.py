"""
Tests for multi-user and cloud sync (P2-14 + P2-16).
"""
import pytest
from fastapi.testclient import TestClient

from stamp_album.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestAuth:
    """Tests for user authentication."""

    def test_register_user(self, client):
        response = client.post("/api/auth/register", json={
            "username": "testuser_" + str(__import__("time").time())[:10],
            "password": "password123",
            "display_name": "Test User",
        })
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "testuser_" + str(__import__("time").time())[:10]

    def test_register_duplicate_fails(self, client):
        client.post("/api/auth/register", json={"username": "dup", "password": "pass1234"})
        response = client.post("/api/auth/register", json={"username": "dup", "password": "pass1234"})
        assert response.status_code == 400

    def test_register_short_password_fails(self, client):
        response = client.post("/api/auth/register", json={"username": "short", "password": "123"})
        assert response.status_code == 400

    def test_login(self, client):
        client.post("/api/auth/register", json={"username": "logintest", "password": "password123"})
        response = client.post("/api/auth/login", json={"username": "logintest", "password": "password123"})
        assert response.status_code == 200
        assert "token" in response.json()

    def test_login_invalid_password(self, client):
        client.post("/api/auth/register", json={"username": "invalid", "password": "password123"})
        response = client.post("/api/auth/login", json={"username": "invalid", "password": "wrong"})
        assert response.status_code == 401

    def test_get_current_user(self, client):
        client.post("/api/auth/register", json={"username": "me_test", "password": "password123"})
        login_resp = client.post("/api/auth/login", json={"username": "me_test", "password": "password123"})
        token = login_resp.json()["token"]
        response = client.get("/api/auth/me", cookies={"session_token": token})
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "me_test"

    def test_logout(self, client):
        client.post("/api/auth/register", json={"username": "logout_test", "password": "password123"})
        login_resp = client.post("/api/auth/login", json={"username": "logout_test", "password": "password123"})
        token = login_resp.json()["token"]
        response = client.post("/api/auth/logout", cookies={"session_token": token})
        assert response.status_code == 200
        # Verify session is gone
        me_resp = client.get("/api/auth/me", cookies={"session_token": token})
        assert me_resp.status_code == 401


class TestFileSharing:
    """Tests for file sharing."""

    def _login(self, client, username):
        client.post("/api/auth/register", json={"username": username, "password": "password123"})
        resp = client.post("/api/auth/login", json={"username": username, "password": "password123"})
        return resp.json()["token"]

    def test_share_file(self, client):
        token = self._login(client, "sharer")
        response = client.post("/api/share", json={
            "filename": "test.slbum",
            "shared_with": "other",
            "permission": "write",
        }, cookies={"session_token": token})
        assert response.status_code == 200
        assert response.json()["share"]["permission"] == "write"

    def test_share_requires_auth(self, client):
        response = client.post("/api/share", json={"filename": "test.slbum", "shared_with": "other"})
        assert response.status_code == 401

    def test_list_shared_with_me(self, client):
        # Setup: owner shares with viewer
        owner_token = self._login(client, "owner_share")
        self._login(client, "viewer_share")
        client.post("/api/share", json={
            "filename": "shared.slbum",
            "shared_with": "viewer_share",
        }, cookies={"session_token": owner_token})
        # Viewer checks
        viewer_token = self._login(client, "viewer_share")
        response = client.get("/api/share/received", cookies={"session_token": viewer_token})
        assert response.status_code == 200
        assert response.json()["shares"][0]["filename"] == "shared.slbum"

    def test_revoke_share(self, client):
        token = self._login(client, "revoker")
        self._login(client, "revokee")
        share_resp = client.post("/api/share", json={
            "filename": "to_revoke.slbum",
            "shared_with": "revokee",
        }, cookies={"session_token": token})
        share_id = share_resp.json()["share"]["id"]
        response = client.delete(f"/api/share/{share_id}", cookies={"session_token": token})
        assert response.status_code == 200
