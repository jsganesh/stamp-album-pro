# ruff: noqa: F811
"""Exports saved into the album's own folder (StampAlbum/<album>/exports).

On the computer the app runs on, a saved album's PDF, PNG, SVG and HTML go into its exports
folder, replacing the last of each kind, with a button to show the file in Finder (Explorer on
Windows). An album not saved yet is offered a save first. A phone on the Wi-Fi still downloads.
"""

import pytest
from fastapi.testclient import TestClient
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401

from stamp_album import api, storage

ALBUM = 'ALBUM_PAGES_SIZE(210 297)\nPAGE_START\nSTAMP_ADD_AT(40 40 25 30 "x" "" "" "")\n'
STATE = {"elements": [{"id": "a", "t": "stamp", "s": "rectangle", "x": 100, "y": 100,
                       "w": 50, "h": 60, "lbl": "Name", "bdr": "solid", "bdrW": 0.5,
                       "fill": "#fff", "fillA": 100}],
         "pages": [], "page_width_px": 525, "page_height_px": 742.5, "scale": 2.5,
         "source_path": "Chalons.slbum"}
MAGIC = {"pdf": b"%PDF", "png": b"\x89PNG", "svg": b"<svg", "html": b"<"}


@pytest.fixture(autouse=True)
def folders(tmp_path, monkeypatch):
    files = tmp_path / "StampAlbum"
    (files / "images").mkdir(parents=True)
    monkeypatch.setattr(storage, "FILES_DIR", files)
    monkeypatch.setattr(storage, "IMAGES_DIR", files / "images")
    return files


@pytest.mark.parametrize("fmt", ["pdf", "png", "svg", "html"])
def test_an_export_goes_into_the_albums_folder(folders, fmt):
    storage.save_album("Chalons.slbum", ALBUM)
    r = TestClient(api.app).post("/export-from-state", json=dict(STATE, format=fmt, save=True))
    assert r.status_code == 200, r.text
    path = folders / "Chalons" / "exports" / f"Chalons.{fmt}"
    assert r.json() == {"status": "saved", "path": str(path), "name": f"Chalons.{fmt}",
                        "folder": str(path.parent)}
    assert path.read_bytes().lstrip()[:len(MAGIC[fmt])] in (MAGIC[fmt], MAGIC[fmt].lower())


def test_exporting_again_replaces_the_last_one(folders):
    storage.save_album("Chalons.slbum", ALBUM)
    client = TestClient(api.app)
    client.post("/export-from-state", json=dict(STATE, format="png", save=True))
    first = (folders / "Chalons" / "exports" / "Chalons.png").read_bytes()
    moved = dict(STATE, format="png", save=True,
                 elements=[dict(STATE["elements"][0], x=300)])
    client.post("/export-from-state", json=moved)
    assert sorted(p.name for p in (folders / "Chalons" / "exports").iterdir()) == ["Chalons.png"]
    assert (folders / "Chalons" / "exports" / "Chalons.png").read_bytes() != first


def test_the_html_finds_its_pictures_next_door(folders):
    storage.save_album("Chalons.slbum", ALBUM)
    state = dict(STATE, format="html", save=True, elements=[
        {"id": "i", "t": "image", "s": "rectangle", "x": 100, "y": 100, "w": 50, "h": 40,
         "img": "/images/map.png", "bdr": "none", "fill": "transparent", "fillA": 0}])
    TestClient(api.app).post("/export-from-state", json=state)
    html = (folders / "Chalons" / "exports" / "Chalons.html").read_text(encoding="utf-8")
    assert 'src="../images/map.png"' in html and 'src="/images/' not in html


def test_an_album_not_saved_has_no_folder_to_export_to(folders):
    for source in ("Nowhere.slbum", "../evil.slbum", "album.txt"):
        r = TestClient(api.app).post("/export-from-state",
                                     json=dict(STATE, format="pdf", save=True, source_path=source))
        assert r.status_code == 409, source
    assert not any(p.name == "exports" for p in folders.rglob("*"))


def test_without_save_it_downloads_as_before(folders):
    r = TestClient(api.app).post("/export-from-state", json=dict(STATE, format="pdf"))
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    assert not (folders / "Chalons").exists()


# ── Show in Finder ──


def test_show_in_finder_only_on_this_computer(folders, monkeypatch):
    storage.save_album("Chalons.slbum", ALBUM)
    client = TestClient(api.app)
    client.post("/export-from-state", json=dict(STATE, format="pdf", save=True))
    shown = []
    monkeypatch.setattr(api, "_reveal", shown.append)
    ask = {"album": "Chalons.slbum", "format": "pdf"}
    assert client.post("/exports/reveal", json=ask).status_code == 403  # "testclient" isn't local
    monkeypatch.setattr(api, "_is_this_computer", lambda request: True)
    assert client.post("/exports/reveal", json=ask).status_code == 200
    assert shown == [folders / "Chalons" / "exports" / "Chalons.pdf"]
    assert client.post("/exports/reveal", json={"album": "../x.slbum", "format": "pdf"}
                       ).status_code == 400
    assert client.post("/exports/reveal", json=dict(ask, format="exe")).status_code == 400
    assert client.post("/exports/reveal", json=dict(ask, format="png")).status_code == 404


def test_the_reveal_command_names_the_file(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("subprocess.Popen", lambda cmd: calls.append(cmd))
    f = tmp_path / "x.pdf"
    for platform, expected in (("darwin", ["open", "-R", str(f)]),
                               ("win32", ["explorer", "/select,", str(f)]),
                               ("linux", ["xdg-open", str(tmp_path)])):
        monkeypatch.setattr("sys.platform", platform)
        api._reveal(f)
        assert calls[-1] == expected


# ── The editor ──


def _open_saved(page, folders):
    storage.save_album("Chalons.slbum", ALBUM)
    page.evaluate("""() => fetch('/files/Chalons.slbum').then(r => r.text())
        .then(t => StampAlbum.openAlbum('Chalons.slbum', t))""")


def _wait_for(page, js):
    for _ in range(200):
        if page.evaluate(js):
            return
        page.wait_for_timeout(50)
    raise AssertionError(js)


def test_a_saved_album_exports_into_its_folder(page, folders):
    _open_saved(page, folders)
    page.evaluate("StampAlbum.exportFormat('pdf')")
    _wait_for(page, "!!document.querySelector('.toast.has-action')")
    assert (folders / "Chalons" / "exports" / "Chalons.pdf").is_file()
    toast = page.inner_text(".toast.has-action")
    assert "Chalons.pdf" in toast and "StampAlbum/Chalons/exports" in toast
    assert "100%" in toast
    assert page.inner_text(".toast.has-action button").startswith("Show")


def test_an_unsaved_album_is_offered_a_save_first(page, folders):
    page.evaluate("StampAlbum.newAlbum()")
    asked = []

    def answer(d):
        asked.append(d.type)
        d.accept("Chalons" if d.type == "prompt" else None)
    page.on("dialog", answer)
    page.evaluate("StampAlbum.exportFormat('png')")
    _wait_for(page, "!!document.querySelector('.toast.has-action')")
    assert asked[:2] == ["confirm", "prompt"]
    assert (folders / "Chalons" / "Chalons.slbum").is_file()
    assert (folders / "Chalons" / "exports" / "Chalons.png").is_file()


def test_saying_no_downloads_instead(page, folders):
    page.evaluate("StampAlbum.newAlbum()")
    page.on("dialog", lambda d: d.dismiss())
    with page.expect_download() as dl:
        page.evaluate("StampAlbum.exportFormat('png')")
    assert dl.value.suggested_filename == "album.png"
    assert not any(p.name == "exports" for p in folders.rglob("*"))


def test_a_phone_downloads(page, folders):
    _open_saved(page, folders)
    page.evaluate("StampAlbum.exportsToFolder = () => false")
    with page.expect_download() as dl:
        page.evaluate("StampAlbum.exportFormat('png')")
    assert dl.value.suggested_filename == "Chalons.png"
    assert not (folders / "Chalons" / "exports").exists()
