# ruff: noqa: F811
"""Saving never writes over a .txt album (an AlbumEasy file opens blank today, so saving it
would replace it with an empty album) and never replaces another saved album without asking.
The server saves only plain .slbum names inside the albums folder (owner's choices 2026-10-17)."""

import pytest
from fastapi.testclient import TestClient
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

from stamp_album import api, storage

ALBUM = 'ALBUM_PAGES_SIZE(210 297)\nPAGE_START\nSTAMP_ADD_AT(20 20 40 30 "x" "" "" "")\nPAGE_END\n'
ALBUMEASY = "ALBUM_PAGES_SIZE (210 297)\nPAGE_START\nROW_START_FS (2)\nSTAMP_ADD (24 28 \"\")\n"


@pytest.fixture()
def albums(tmp_path, monkeypatch):
    """The albums folder, emptied for each test (also used by the in-process server)."""
    files = tmp_path / "albums"
    files.mkdir()
    monkeypatch.setattr(storage, "FILES_DIR", files)
    return files


@pytest.fixture()
def client():
    return TestClient(api.app)


def _answer(pg, *answers):
    """Answer the next dialogs in turn: True/False for a question, a string (or None to
    cancel) for a name box. Returns the dialogs seen as [type, message, default]."""
    seen, queue = [], list(answers)

    def handle(d):
        seen.append([d.type, d.message, d.default_value])
        a = queue.pop(0) if queue else None
        if d.type == "prompt":
            d.accept(a) if a is not None else d.dismiss()
        else:
            d.accept() if a else d.dismiss()

    pg.on("dialog", handle)
    return seen


def _save(pg):
    return pg.evaluate("StampAlbum.saveFile()")


def _open(pg, name, content=ALBUM, change=True):
    pg.evaluate("([n, c]) => StampAlbum.openAlbum(n, c)", [name, content])
    if change:
        pg.evaluate("() => { const S = StampAlbum; S.E.push({id: 'y', t: 'stamp', s: 'rectangle',"
                    " x: 300, y: 300, w: 60, h: 70, lbl: 'new'}); S.pushUndo(); S.render(); }")


# ── The server ──

def test_server_never_saves_a_txt(albums, client):
    (albums / "tdc.txt").write_text("AlbumEasy", encoding="utf-8")
    r = client.post("/files/tdc.txt", json={"content": ""})
    assert r.status_code == 400
    assert storage.album_path("tdc.txt").read_text(encoding="utf-8") == "AlbumEasy"
    assert client.get("/files/tdc.txt").text == "AlbumEasy"  # still opens


@pytest.mark.parametrize("name", ["..\\up.slbum", "C:up.slbum", ".hidden.slbum", "up.slbum\\x",
                                  "album", "album.pdf"])
def test_server_saves_only_plain_slbum_names(albums, client, name):
    from urllib.parse import quote

    r = client.post("/files/" + quote(name, safe=""), json={"content": "x"})
    assert r.status_code in (400, 404)
    assert list(albums.parent.rglob("*up.slbum")) == []
    assert list(albums.iterdir()) == []


@pytest.mark.parametrize("method", ["get", "delete"])
def test_server_reads_and_deletes_only_album_names(albums, client, method):
    (albums.parent / "secret.slbum").write_text("outside", encoding="utf-8")
    r = getattr(client, method)("/files/..%5Csecret.slbum")
    assert r.status_code == 400
    assert (albums.parent / "secret.slbum").exists()


def test_server_still_saves_an_album(albums, client):
    assert client.post("/files/My album.slbum", json={"content": ALBUM}).status_code == 200
    assert storage.album_path("My album.slbum").read_text(encoding="utf-8") == ALBUM


# ── The editor ──

def test_a_txt_album_is_saved_as_a_new_slbum(albums, page):
    (albums / "tdc.txt").write_text(ALBUMEASY, encoding="utf-8")
    _open(page, "tdc.txt")
    seen = _answer(page, "tdc.slbum")
    assert _save(page) is True
    assert [s[0] for s in seen] == ["prompt"]
    assert seen[0][2] == "tdc.slbum"  # suggested
    assert storage.album_path("tdc.txt").read_text(encoding="utf-8") == ALBUMEASY  # untouched
    assert "STAMP_ADD_AT" in storage.album_path("tdc.slbum").read_text(encoding="utf-8")
    assert page.evaluate("StampAlbum._currentFile") == "tdc.slbum"
    assert page.evaluate("StampAlbum._dirty") is False
    # The next Save goes to tdc.slbum without asking
    assert _save(page) is True
    assert len(seen) == 1


def test_a_typed_txt_name_becomes_slbum(albums, page):
    _open(page, "old.txt")
    _answer(page, "notes.txt")
    assert _save(page) is True
    assert sorted(p.name for p in storage.list_albums()) == ["notes.slbum"]
    assert (albums / "notes" / "notes.slbum").is_file()  # in a folder of its own


def test_cancel_saves_nothing(albums, page):
    _open(page, "tdc.txt")
    _answer(page, None)
    assert _save(page) is False
    assert list(albums.iterdir()) == []
    assert page.evaluate("StampAlbum._currentFile") == "tdc.txt"
    assert page.evaluate("StampAlbum._dirty") is True


def test_replacing_a_saved_album_asks_first(albums, page):
    (albums / "album.slbum").write_text("first", encoding="utf-8")
    page.evaluate("StampAlbum.newAlbum()")
    # "album" is taken: say No, then cancel the name box: nothing is written
    seen = _answer(page, "album", False, None)
    assert _save(page) is False
    assert [s[0] for s in seen] == ["prompt", "confirm", "prompt"]
    assert "album" in seen[1][1] and "Replace" in seen[1][1]
    assert seen[2][2] == "album.slbum"  # asked again with the same name
    assert storage.album_path("album.slbum").read_text(encoding="utf-8") == "first"


def test_replacing_when_confirmed(albums, page):
    (albums / "album.slbum").write_text("first", encoding="utf-8")
    page.evaluate("StampAlbum.newAlbum()")
    _answer(page, "album.slbum", True)
    assert _save(page) is True
    assert storage.album_path("album.slbum").read_text(encoding="utf-8") != "first"


def test_another_name_after_saying_no(albums, page):
    (albums / "album.slbum").write_text("first", encoding="utf-8")
    page.evaluate("StampAlbum.newAlbum()")
    _answer(page, "album", False, "album 2")
    assert _save(page) is True
    assert sorted(p.name for p in storage.list_albums()) == ["album 2.slbum", "album.slbum"]
    assert storage.album_path("album.slbum").read_text(encoding="utf-8") == "first"


def test_saving_the_open_slbum_does_not_ask(albums, page):
    (albums / "mine.slbum").write_text(ALBUM, encoding="utf-8")
    _open(page, "mine.slbum")
    seen = _answer(page)
    assert _save(page) is True
    assert seen == []
    assert "new" in storage.album_path("mine.slbum").read_text(encoding="utf-8")


def test_file_names_are_made_plain(page):
    names = page.evaluate("""['tdc.txt', 'a/b', 'a\\\\b', 'C:x', '..hidden', ' x ', '', '.txt',
        'Album.SLBUM'].map(StampAlbum.albumFileName)""")
    assert names == ["tdc.slbum", "a-b.slbum", "a-b.slbum", "C-x.slbum", "hidden.slbum",
                     "x.slbum", "", "", "Album.SLBUM"]
