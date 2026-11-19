"""The app has no accounts, sign-in or sharing between users.

The server has no sign-in and can be opened to other devices on a trusted network
(STAMP_ALBUM_HOST), so an account or sharing API would only be a larger surface to
attack. These routes were removed in 0.7.0; this keeps them from coming back unnoticed.
"""
import pytest
from fastapi.testclient import TestClient

from stamp_album.api import app

REMOVED = [
    ("post", "/api/auth/register"),
    ("post", "/api/auth/login"),
    ("post", "/api/auth/logout"),
    ("get", "/api/auth/me"),
    ("get", "/api/users"),
    ("post", "/api/share"),
    ("get", "/api/share/received"),
    ("get", "/api/share/sent"),
    ("delete", "/api/share/some-id"),
]


@pytest.mark.parametrize("method,path", REMOVED)
def test_account_and_sharing_routes_are_gone(method, path):
    response = getattr(TestClient(app), method)(path)
    assert response.status_code in (404, 405)


def test_the_editor_does_not_call_them():
    from pathlib import Path

    web = Path(__file__).resolve().parents[1] / "stamp_album" / "web"
    for js in web.glob("*.js"):
        text = js.read_text(encoding="utf-8")
        assert "/api/auth" not in text and "/api/share" not in text, js.name
