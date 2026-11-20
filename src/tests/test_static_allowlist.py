"""The catch-all route serves only files found in a list of the web folder, never a path built
from the URL.

Its old guard, `"/" in name`, stopped "../x" but not what Windows also reads as a path:
"..\\x", "D:x" and "\\\\host\\share\\x". Looking the name up in a dict leaves nothing to inject.
"""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from stamp_album import api

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(api.app)

ESCAPES = [
    "..%2F__init__.py",            # ../ (POSIX); the package's own file, one level up
    "..%5C__init__.py",            # ..\ (Windows): the old guard let this one read it
    "..%2Fpyproject.toml",
    "..%5Cpyproject.toml",
    "..%5C..%5Csecret.txt",
    "D%3Aevil.js",                 # a drive: Windows would leave the web folder
    "%5C%5Chost%5Cshare%5Cx.js",   # a network path: Windows would contact the host
    "%2e%2e%2fpyproject.toml",
    "fonts",                       # a folder
    ".DS_Store",
    "app.js%00.png",
    "APP.JS",                      # names are exact
]


@pytest.mark.parametrize("name", ESCAPES)
def test_nothing_outside_the_list_is_served(name):
    assert client.get("/" + name).status_code == 404


def test_every_file_the_page_asks_for_is_served_with_its_type():
    html = (api.WEB_DIR / "index.html").read_text(encoding="utf-8")
    refs = re.findall(r'(?:src|href)="([^"]+)"', html)
    names = {re.split(r"[?#]", r)[0] for r in refs if "://" not in r and r[0] not in "/#"}
    assert len(names) > 30
    for name in names:
        r = client.get("/" + name)
        assert r.status_code == 200, name
        assert r.headers["content-type"].split(";")[0] == api.STATIC_MEDIA_TYPES[Path(name).suffix]


def test_the_list_is_plain_files_of_known_types_in_the_web_folder(tmp_path, monkeypatch):
    for name in ("ok.js", "Style.CSS", ".hidden.js", "data.json", "noext"):
        (tmp_path / name).write_text("x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "inner.js").write_text("x")
    monkeypatch.setattr(api, "WEB_DIR", tmp_path)
    assert set(api._static_files()) == {"ok.js", "Style.CSS"}


def test_no_name_in_the_real_list_can_read_as_a_path():
    names = api._static_files()
    assert names
    for name in names:
        assert not set(name) & set('/\\:*?"<>|'), name
        assert not name.startswith(".")


def test_the_server_file_binds_loopback_only():
    for path in (ROOT / "src" / "stamp_album").glob("*.py"):
        assert 'host="0.0.0.0"' not in path.read_text(encoding="utf-8"), path.name
