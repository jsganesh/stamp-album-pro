"""The catch-all static route sends each file with its real media type.

It used to send every image as image/png, so an .svg was served as a PNG.
"""

import pytest
from fastapi.testclient import TestClient

import stamp_album.api as api


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "WEB_DIR", tmp_path)
    return TestClient(api.app), tmp_path


@pytest.mark.parametrize(
    "name, media_type",
    [
        ("logo.svg", "image/svg+xml"),
        ("photo.jpg", "image/jpeg"),
        ("photo.jpeg", "image/jpeg"),
        ("anim.gif", "image/gif"),
        ("shot.png", "image/png"),
        ("style.css", "text/css"),
        ("app.js", "application/javascript"),
    ],
)
def test_static_media_type(client, name, media_type):
    tc, web = client
    (web / name).write_bytes(b"x")
    r = tc.get("/" + name)
    assert r.status_code == 200
    assert r.headers["content-type"].split(";")[0] == media_type


def test_static_upper_case_extension(client):
    tc, web = client
    (web / "LOGO.SVG").write_bytes(b"x")
    assert tc.get("/LOGO.SVG").headers["content-type"].split(";")[0] == "image/svg+xml"


def test_real_web_files_keep_their_types():
    tc = TestClient(api.app)
    assert tc.get("/tutorial-1-add.png").headers["content-type"] == "image/png"
    assert tc.get("/style.css").headers["content-type"].startswith("text/css")
