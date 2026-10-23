# ruff: noqa: F811
"""A folder for each album (storage.py).

StampAlbum/<album>/<album>.slbum with its pictures in <album>/images. Albums from before
folders sat loose and shared one images folder: they move into folders of their own when the
app starts, with copies of their pictures, and nothing else is deleted. Pictures are looked for
in the open album's folder first (the editor names it in a cookie), then the old shared folder.
"""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401

from stamp_album import api, storage

ALBUM = 'ALBUM_PAGES_SIZE(210 297)\nPAGE_START\nSTAMP_ADD_AT(40 40 25 30 "x" "" "" "")\n{extra}'


def _png(colour, size=(40, 30)):
    buf = io.BytesIO()
    Image.new("RGB", size, colour).save(buf, "PNG")
    return buf.getvalue()


def _with(*names):
    return ALBUM.format(extra="".join(
        f'STAMP_ADD_IMG(100 100 40 30 "/images/{n}" "" "" "")\n' for n in names))


RED, BLUE, GREEN = _png((200, 0, 0)), _png((0, 0, 200)), _png((0, 200, 0))


@pytest.fixture(autouse=True)
def folders(tmp_path, monkeypatch):
    files = tmp_path / "StampAlbum"
    (files / "images").mkdir(parents=True)
    monkeypatch.setattr(storage, "FILES_DIR", files)
    monkeypatch.setattr(storage, "IMAGES_DIR", files / "images")
    storage.LAST_MOVED.clear()
    return files


# ── Saving ──


def test_saving_makes_the_album_a_folder_with_its_pictures(folders):
    (folders / "images" / "map.png").write_bytes(RED)
    (folders / "images" / "unused.png").write_bytes(BLUE)
    (folders / ".unsaved-images").mkdir()
    (folders / ".unsaved-images" / "flag.png").write_bytes(GREEN)
    path = storage.save_album("Chalons.slbum", _with("map.png", "flag.png"))
    assert path == folders / "Chalons" / "Chalons.slbum"
    assert sorted(p.name for p in (folders / "Chalons" / "images").iterdir()) == [
        "flag.png", "map.png"]
    assert (folders / "images" / "map.png").exists(), "the shared copy stays"


def test_save_as_takes_the_pictures_from_the_open_album(folders):
    storage.save_album("A.slbum", _with())
    (folders / "A" / "images").mkdir()
    (folders / "A" / "images" / "map.png").write_bytes(BLUE)
    (folders / "images" / "map.png").write_bytes(RED)  # a different picture of the same name
    storage.save_album("B.slbum", _with("map.png"), from_album="A.slbum")
    assert (folders / "B" / "images" / "map.png").read_bytes() == BLUE


def test_saving_a_loose_album_moves_it_in(folders):
    (folders / "Old.slbum").write_text("before", encoding="utf-8")
    assert storage.album_path("Old.slbum") == folders / "Old.slbum"
    storage.save_album("Old.slbum", _with())
    assert not (folders / "Old.slbum").exists()
    assert storage.album_path("Old.slbum") == folders / "Old" / "Old.slbum"


def test_the_list_has_folders_and_loose_albums(folders):
    storage.save_album("A.slbum", _with())
    (folders / "B.txt").write_text("x", encoding="utf-8")
    (folders / "notes").mkdir()                      # a folder that isn't an album
    (folders / ".unsaved-images").mkdir()
    assert sorted(p.name for p in storage.list_albums()) == ["A.slbum", "B.txt"]


def test_deleting_removes_the_folder(folders):
    storage.save_album("A.slbum", _with())
    (folders / "A" / "exports").mkdir()
    storage.delete_album("A.slbum")
    assert not (folders / "A").exists()
    (folders / "Loose.slbum").write_text("x", encoding="utf-8")
    storage.delete_album("Loose.slbum")
    assert not (folders / "Loose.slbum").exists()
    assert (folders / "images").is_dir()


# ── Finding pictures ──


def test_a_picture_is_found_in_the_album_first(folders):
    storage.save_album("A.slbum", _with())
    (folders / "A" / "images").mkdir()
    (folders / "A" / "images" / "map.png").write_bytes(BLUE)
    (folders / "images" / "map.png").write_bytes(RED)
    assert storage.find_image("/images/map.png", "A.slbum").read_bytes() == BLUE
    assert storage.find_image("map.png", None).read_bytes() == RED  # no album: the shared one
    assert storage.find_image("../A/images/map.png", None).read_bytes() == RED  # names only
    assert storage.find_image("none.png", "A.slbum") is None
    (folders / "images" / "map.png").unlink()
    assert storage.find_image("map.png", "B.slbum") == folders / "A" / "images" / "map.png"


# ── Moving the old albums ──


def test_loose_albums_move_into_folders(folders):
    (folders / "images" / "map.png").write_bytes(RED)
    (folders / "images" / "other.png").write_bytes(BLUE)
    (folders / "NZ.slbum").write_text(_with("map.png"), encoding="utf-8")
    (folders / "tdc.txt").write_text("AlbumEasy", encoding="utf-8")
    (folders / "Taken").mkdir()  # a folder already has this name
    (folders / "Taken.slbum").write_text(_with(), encoding="utf-8")
    moved = storage.move_loose_albums()
    assert moved == [("NZ.slbum", "NZ.slbum"), ("Taken.slbum", "Taken (2).slbum"),
                     ("tdc.txt", "tdc.txt")]
    assert (folders / "NZ" / "NZ.slbum").read_text(encoding="utf-8") == _with("map.png")
    assert (folders / "NZ" / "images" / "map.png").read_bytes() == RED
    assert not (folders / "NZ" / "images" / "other.png").exists()
    assert (folders / "tdc" / "tdc.txt").read_text(encoding="utf-8") == "AlbumEasy"
    assert (folders / "Taken (2)" / "Taken (2).slbum").is_file()
    assert sorted(p.name for p in (folders / "images").iterdir()) == ["map.png", "other.png"]
    assert [p.name for p in folders.iterdir() if p.is_file()] == [storage.MOVED_NOTE]
    assert storage.MOVED_NOTE not in [p.name for p in storage.list_albums()]
    assert "NZ.slbum -> NZ/NZ.slbum" in (folders / storage.MOVED_NOTE).read_text(encoding="utf-8")
    assert storage.move_loose_albums() == [], "a second start moves nothing"


def test_the_editor_is_told_once(folders):
    (folders / "NZ.slbum").write_text(_with(), encoding="utf-8")
    storage.move_loose_albums()
    client = TestClient(api.app)
    assert client.get("/albums/moved").json() == [{"from": "NZ.slbum", "to": "NZ.slbum"}]
    assert client.get("/albums/moved").json() == []


# ── The server ──


def _client(album=None):
    client = TestClient(api.app)
    if album:
        client.cookies.set(api.ALBUM_COOKIE, album)
    return client


def test_the_server_saves_into_the_folder(folders):
    (folders / ".unsaved-images").mkdir()
    (folders / ".unsaved-images" / "scan.png").write_bytes(RED)
    r = _client().post("/files/Mine.slbum", json={"content": _with("scan.png")})
    assert r.status_code == 200
    assert r.json()["folder"] == str(folders / "Mine")
    assert (folders / "Mine" / "images" / "scan.png").read_bytes() == RED
    assert _client().get("/files").json() == ["Mine.slbum"]
    assert _client().get("/files/Mine.slbum").text == _with("scan.png")


def test_pictures_come_from_the_open_album(folders):
    storage.save_album("A.slbum", _with())
    (folders / "A" / "images").mkdir()
    (folders / "A" / "images" / "map.png").write_bytes(BLUE)
    (folders / "images" / "map.png").write_bytes(RED)
    assert _client("A.slbum").get("/images/map.png").content == BLUE
    assert _client().get("/images/map.png").content == RED
    assert _client("../x.slbum").get("/images/map.png").content == RED  # not an album name


def test_pictures_attached_to_a_saved_album_go_in_its_folder(folders):
    storage.save_album("A.slbum", _with())
    upload = {"file": ("scan.png", io.BytesIO(RED), "image/png")}
    r = _client("A.slbum").post("/images", files=upload)
    assert r.status_code == 200
    assert (folders / "A" / "images" / "scan.png").read_bytes() == RED
    assert _client("A.slbum").get("/images").json() == ["scan.png"]


def test_the_exports_find_the_albums_own_pictures(folders):
    storage.save_album("A.slbum", _with())
    (folders / "A" / "images").mkdir()
    (folders / "A" / "images" / "map.png").write_bytes(_png((0, 0, 200), (80, 60)))
    state = {"elements": [{"id": "i", "t": "image", "s": "rectangle", "x": 250, "y": 250,
                           "w": 100, "h": 75, "img": "/images/map.png", "bdr": "none",
                           "fill": "transparent", "fillA": 0}],
             "pages": [], "page_width_px": 525, "page_height_px": 742.5, "scale": 2.5,
             "format": "png", "source_path": "A.slbum"}
    r = _client("A.slbum").post("/export-from-state", json=state)
    assert r.status_code == 200
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    w, h = img.size
    r_, g, b = img.getpixel((int(w * 120 / 210), int(h * 115 / 297)))  # inside the picture
    assert b > 150 and r_ < 80, (r_, g, b)


# ── The editor ──


def test_the_editor_names_the_open_album(page):
    cookie = "() => document.cookie.split('; ').find(c => c.startsWith('stampalbum_album=')) || ''"
    page.evaluate("StampAlbum._currentFile = 'My album.slbum'")
    assert page.evaluate(cookie) == "stampalbum_album=My%20album.slbum"
    page.evaluate("StampAlbum.newAlbum()")
    assert page.evaluate(cookie) == ""


def test_saving_a_new_album_keeps_its_pictures(page, folders, tmp_path):
    page.evaluate("StampAlbum.newAlbum()")
    f = tmp_path / "scan.png"
    f.write_bytes(_png((200, 0, 0), (300, 200)))
    page.set_input_files("#upl-inp", str(f))
    for _ in range(100):
        if page.evaluate("StampAlbum.E.length") == 1:
            break
        page.wait_for_timeout(50)
    page.on("dialog", lambda d: d.accept("Chalons"))
    assert page.evaluate("StampAlbum.saveFile()") is True
    assert (folders / "Chalons" / "Chalons.slbum").is_file()
    assert (folders / "Chalons" / "images" / "scan.png").is_file()
    # Reopened, the picture is drawn from the album's folder
    (folders / ".unsaved-images" / "scan.png").unlink()
    page.evaluate("""() => fetch('/files/Chalons.slbum').then(r => r.text())
        .then(t => StampAlbum.openAlbum('Chalons.slbum', t))""")
    loaded = page.evaluate("""() => new Promise(done => { const i = new Image();
        i.onload = () => done(i.naturalWidth); i.onerror = () => done(0);
        i.src = '/images/scan.png?' + Date.now(); })""")
    assert loaded == 300


def test_starting_the_app_moves_loose_albums(tmp_path):
    """serve.py and desktop.py set STAMP_ALBUM_APP_START; importing the server then moves them.
    Test servers don't set it, so they never touch an albums folder."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    files = tmp_path / "Albums"
    files.mkdir()
    (files / "NZ.slbum").write_text(_with(), encoding="utf-8")
    src = str(Path(storage.__file__).resolve().parents[1])
    env = dict(os.environ, STAMP_ALBUM_FILES=str(files), PYTHONPATH=src)
    code = "import stamp_album.api"
    subprocess.run([sys.executable, "-c", code], env=env, check=True, timeout=120)
    assert (files / "NZ.slbum").exists(), "without the flag nothing moves"
    env["STAMP_ALBUM_APP_START"] = "1"
    subprocess.run([sys.executable, "-c", code], env=env, check=True, timeout=120)
    assert (files / "NZ" / "NZ.slbum").is_file() and not (files / "NZ.slbum").exists()
