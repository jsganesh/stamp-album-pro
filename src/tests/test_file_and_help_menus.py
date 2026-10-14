# ruff: noqa: F811
"""File and Help menus, and the left panel holding only things to add (UI review item 6).

- File › Open recent lists the 10 newest saved albums; File › Manage saved albums… opens
  or deletes them. Both ask before replacing unsaved work.
- Help is a menu: Show the tutorial, Keyboard shortcuts (still on ?), Print calibration page.
- The CSV/Excel import is gone: it filled a stamp list nothing ever showed.
- The Images section lists the images the open album uses; a new album says how to add one.
  Attaching an image places it on the page. An image is never deleted from the panel.
"""
import io
import os
import time

import pytest
from fastapi.testclient import TestClient
from test_accessibility import _axe
from test_ui_smoke import base_url, page, wait_for_app  # noqa: F401

from stamp_album import api


def _png(colour, size=(30, 20)):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, colour).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def folders(tmp_path, monkeypatch):
    """Saved albums and images in a folder of the test's own (the server reads these per call)."""
    files = tmp_path / "StampAlbum"
    images = files / "images"
    images.mkdir(parents=True)
    monkeypatch.setattr(api, "FILES_DIR", files)
    monkeypatch.setattr(api, "IMAGES_DIR", images)
    return files


ALBUM = (
    'ALBUM_PAGES_SIZE(210 297)\n'
    'PAGE_START\n'
    'STAMP_ADD_AT(40 40 25 30 "{name}" "" "" "")\n'
    '{extra}'
)


def _save(folder, name, extra="", mtime=None):
    p = folder / name
    p.write_text(ALBUM.format(name=name, extra=extra), encoding="utf-8")
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


def _open_file_menu(pg):
    pg.click("#menu-file-btn")
    assert pg.is_visible("#menu-file")


def _recent_names(pg):
    return pg.evaluate(
        "[...document.querySelectorAll('#menu-recent-list .mi')].map(b => b.textContent)")


def _wait(pg, js, timeout_ms=5000):
    deadline = time.monotonic() + timeout_ms / 1000
    while not pg.evaluate(js):
        if time.monotonic() > deadline:
            raise TimeoutError(js)
        pg.wait_for_timeout(50)


# ── The left panel ──

def test_left_panel_holds_only_things_to_add(page):
    for gone in ("#btn-import-csv", "#btn-import-excel", "#imp-body", "#imp-inp",
                 "#file-list", "#file-body", "#btn-new-file"):
        assert page.locator(gone).count() == 0, gone
    headings = page.evaluate(
        "[...document.querySelectorAll('#sidebar h2')].map(h => h.textContent.trim())")
    assert headings == ["Stamps", "Text", "Images"]
    assert page.get_attribute("#sidebar", "aria-label") == "Add to the page"
    assert page.evaluate("document.getElementById('btn-new').textContent") == "New album"


def test_import_routes_are_gone():
    client = TestClient(api.app)
    files = {"file": ("s.csv", io.BytesIO(b"country,year\nGB,1840\n"), "text/csv")}
    assert client.post("/api/stamps/import", files=files).status_code in (404, 405)
    assert client.post("/api/stamps/import-excel", files=files).status_code in (404, 405)
    assert client.get("/api/stamps").status_code == 404


# ── Help ──

def test_help_is_a_menu_with_three_items(page):
    assert page.locator("#btn-help-tb").count() == 0
    page.click("#menu-help-btn")
    assert page.is_visible("#menu-help")
    items = page.evaluate("[...document.querySelectorAll('#menu-help .mi')].map(b => b.id)")
    assert items == ["menu-tutorial", "btn-help", "menu-calibration"]
    # They left View and File
    assert page.locator("#menu-view #menu-tutorial, #menu-view #btn-help").count() == 0
    assert page.locator("#menu-file #menu-calibration").count() == 0


@pytest.mark.parametrize("item, overlay", [
    ("#menu-tutorial", "#tutorial-overlay"),
    ("#btn-help", "#help-overlay"),
    ("#menu-calibration", "#calibration-overlay"),
])
def test_help_items_open_their_screens(page, item, overlay):
    page.click("#menu-help-btn")
    page.click(item)
    assert "open" in page.get_attribute(overlay, "class")
    assert not page.is_visible("#menu-help")


def test_question_mark_still_opens_the_shortcuts(page):
    page.click("#page", position={"x": 5, "y": 5})
    page.keyboard.press("?")
    assert "open" in page.get_attribute("#help-overlay", "class")


def test_arrow_keys_reach_the_help_menu(page):
    page.focus("#menu-view-btn")
    page.keyboard.press("Enter")
    page.keyboard.press("ArrowRight")
    assert page.is_visible("#menu-help")
    assert page.evaluate("document.activeElement.id") == "menu-tutorial"


# ── File › Open recent ──

def test_open_recent_lists_the_ten_newest(page, folders):
    now = time.time()
    for i in range(12):  # album-00 is the oldest
        _save(folders, "album-%02d.slbum" % i, mtime=now - 1000 + i * 10)
    _open_file_menu(page)
    page.hover("#menu-recent")
    _wait(page, "document.querySelectorAll('#menu-recent-list .mi').length === 10")
    assert _recent_names(page) == ["album-%02d" % i for i in range(11, 1, -1)]
    assert page.get_attribute("#menu-recent", "aria-expanded") == "true"


def test_open_recent_opens_the_album(page, folders):
    _save(folders, "Penny Black.slbum")
    _open_file_menu(page)
    page.click("#menu-recent")
    _wait(page, "document.querySelectorAll('#menu-recent-list .mi').length === 1")
    page.click("#menu-recent-list .mi")
    _wait(page, "StampAlbum._currentFile === 'Penny Black.slbum'")
    assert page.evaluate("StampAlbum.E.length") == 1
    assert not page.is_visible("#menu-file")


def test_open_recent_says_when_there_are_none(page):
    _open_file_menu(page)
    page.click("#menu-recent")
    _wait(page, "document.querySelectorAll('#menu-recent-list .mi').length === 1")
    assert _recent_names(page) == ["No saved albums yet"]
    assert page.evaluate("document.querySelector('#menu-recent-list .mi').disabled")


def test_open_recent_by_keyboard(page, folders):
    _save(folders, "a.slbum", mtime=time.time() - 50)
    _save(folders, "b.slbum")
    _open_file_menu(page)
    page.focus("#menu-recent")
    page.keyboard.press("ArrowRight")
    _wait(page, "document.activeElement.dataset.file === 'b.slbum'")
    page.keyboard.press("ArrowDown")
    assert page.evaluate("document.activeElement.dataset.file") == "a.slbum"
    page.keyboard.press("ArrowLeft")
    assert page.evaluate("document.activeElement.id") == "menu-recent"
    assert page.is_hidden("#menu-recent-list")
    # Escape in the submenu closes it only; a second Escape closes File.
    page.keyboard.press("ArrowRight")
    _wait(page, "document.activeElement.dataset.file === 'b.slbum'")
    page.keyboard.press("Escape")
    assert page.is_hidden("#menu-recent-list") and page.is_visible("#menu-file")
    page.keyboard.press("Escape")
    assert page.is_hidden("#menu-file")
    # The File menu's own arrow keys skip the submenu's items.
    page.keyboard.press("Enter")
    page.keyboard.press("ArrowDown")
    ids = []
    for _ in range(4):
        page.keyboard.press("ArrowDown")
        ids.append(page.evaluate("document.activeElement.id"))
    assert "menu-recent" in ids and "menu-manage" in ids


def test_open_recent_asks_before_replacing_unsaved_work(page, folders):
    _save(folders, "other.slbum")
    page.evaluate("StampAlbum._dirty = false; StampAlbum.newAlbum();"
                  " StampAlbum.add({t: 'stamp', x: 10, y: 10, w: 50, h: 60})")
    assert page.evaluate("StampAlbum._dirty")
    asked = []
    page.on("dialog", lambda d: (asked.append(d.message), d.dismiss()))
    _open_file_menu(page)
    page.click("#menu-recent")
    _wait(page, "document.querySelectorAll('#menu-recent-list .mi').length === 1")
    page.click("#menu-recent-list .mi")
    page.wait_for_timeout(300)
    assert asked == ["Discard unsaved changes?"]
    assert page.evaluate("StampAlbum._currentFile") is None
    assert page.evaluate("StampAlbum.E.length") == 1


def test_file_open_asks_before_replacing_unsaved_work(page):
    page.evaluate("StampAlbum._dirty = false; StampAlbum.newAlbum()")
    page.evaluate("StampAlbum.add({t: 'stamp', x: 10, y: 10, w: 50, h: 60})")
    asked = []
    page.on("dialog", lambda d: (asked.append(d.message), d.dismiss()))
    page.evaluate("document.getElementById('file-inp').addEventListener('click',"
                  " e => { window._picked = true; e.preventDefault(); })")
    _open_file_menu(page)
    page.click("#btn-open")
    assert asked == ["Discard unsaved changes?"]
    assert not page.evaluate("!!window._picked")


# ── File › Manage saved albums… ──

def test_manage_saved_albums_lists_newest_first(page, folders):
    _save(folders, "old.slbum", mtime=time.time() - 100)
    _save(folders, "new.slbum")
    _open_file_menu(page)
    page.click("#menu-manage")
    _wait(page, "document.querySelectorAll('#alb-list .alb-row').length === 2")
    names = page.evaluate("[...document.querySelectorAll('.alb-name')].map(n => n.textContent)")
    assert names == ["new", "old"]
    assert page.get_attribute("#albums-overlay", "aria-modal") == "true"
    assert page.evaluate("document.activeElement.className") == "alb-open"
    assert _axe(page, "#albums-overlay") == []


def test_manage_saved_albums_opens_one(page, folders):
    _save(folders, "Set row.slbum")
    page.evaluate("StampAlbum.openManageAlbums()")
    _wait(page, "document.querySelectorAll('#alb-list .alb-open').length === 1")
    page.click(".alb-open")
    _wait(page, "StampAlbum._currentFile === 'Set row.slbum'")
    assert "open" not in (page.get_attribute("#albums-overlay", "class") or "")


def test_manage_saved_albums_deletes_after_asking(page, folders):
    _save(folders, "keep.slbum", mtime=time.time() - 100)
    gone = _save(folders, "gone.slbum")
    page.evaluate("StampAlbum.openManageAlbums()")
    _wait(page, "document.querySelectorAll('#alb-list .alb-del').length === 2")
    page.once("dialog", lambda d: d.dismiss())
    page.click(".alb-del >> nth=0")
    page.wait_for_timeout(200)
    assert gone.exists()
    page.once("dialog", lambda d: d.accept())
    page.click(".alb-del >> nth=0")
    _wait(page, "document.querySelectorAll('#alb-list .alb-row').length === 1")
    assert not gone.exists() and (folders / "keep.slbum").exists()


def test_deleting_the_open_album_leaves_it_on_screen_not_saved(page, folders):
    _save(folders, "mine.slbum")
    page.evaluate("StampAlbum.openSaved('mine.slbum')")
    _wait(page, "StampAlbum._currentFile === 'mine.slbum'")
    page.evaluate("StampAlbum.openManageAlbums()")
    _wait(page, "document.querySelectorAll('#alb-list .alb-del').length === 1")
    page.once("dialog", lambda d: d.accept())
    page.click(".alb-del")
    _wait(page, "StampAlbum._currentFile === null")
    assert page.evaluate("StampAlbum._dirty") and page.is_visible("#tb-dirty")
    assert page.evaluate("StampAlbum.E.length") == 1


def test_manage_dialog_keeps_focus_and_closes_on_escape(page, folders):
    _save(folders, "one.slbum")
    page.focus("#menu-file-btn")
    page.evaluate("StampAlbum.openManageAlbums()")
    _wait(page, "document.activeElement.className === 'alb-open'")
    for _ in range(6):
        page.keyboard.press("Tab")
        assert page.evaluate("!!document.activeElement.closest('#albums-overlay')")
    page.keyboard.press("Delete")  # the editor's shortcuts wait while the dialog is open
    page.keyboard.press("Escape")
    assert "open" not in (page.get_attribute("#albums-overlay", "class") or "")


# ── Images ──

def test_a_new_album_says_how_to_add_an_image(page):
    page.evaluate("StampAlbum.newAlbum()")
    assert page.is_visible("#img-empty")
    assert page.text_content("#img-empty") == "Attach an image to place it on the page."
    assert page.is_hidden("#img-grid")
    assert page.text_content("#img-upl-btn").strip() == "Attach image…"


def test_attaching_places_the_image_on_the_page(page, folders, tmp_path):
    page.evaluate("StampAlbum.newAlbum()")
    f = tmp_path / "scan.png"
    f.write_bytes(_png((200, 0, 0), (300, 200)))
    page.set_input_files("#upl-inp", str(f))
    _wait(page, "StampAlbum.E.length === 1")
    el = page.evaluate("StampAlbum.E[0]")
    assert el["t"] == "image" and el["img"] == "/images/scan.png"
    assert page.evaluate("StampAlbum.sel") == el["id"]
    assert abs(el["w"] / el["h"] - 1.5) < 0.05  # the picture's own shape
    _wait(page, "document.querySelectorAll('#img-grid .img-item').length === 1")
    assert page.is_hidden("#img-empty")
    assert (folders / "images" / "scan.png").exists()
    # A thumbnail adds another copy
    page.click("#img-grid .img-add")
    _wait(page, "StampAlbum.E.length === 2")
    assert page.locator("#img-grid .img-item").count() == 1


def test_thumbnails_have_no_delete_cross(page, folders):
    (folders / "images" / "a.png").write_bytes(_png((0, 0, 200)))
    page.evaluate("StampAlbum.newAlbum(); StampAlbum.placeImage('a.png')")
    _wait(page, "document.querySelectorAll('#img-grid .img-item').length === 1")
    assert page.locator(".img-del").count() == 0
    # Deleting the image on the page takes it off the list; the file stays.
    page.once("dialog", lambda d: d.accept())
    page.keyboard.press("Delete")
    _wait(page, "document.querySelectorAll('#img-grid .img-item').length === 0")
    assert page.is_visible("#img-empty")
    assert (folders / "images" / "a.png").exists()
    page.keyboard.press("Control+z")
    _wait(page, "document.querySelectorAll('#img-grid .img-item').length === 1")


def test_images_follow_the_open_album(page, folders):
    images = folders / "images"
    for n, c in (("one.png", (200, 0, 0)), ("two.png", (0, 200, 0)), ("other.png", (0, 0, 200))):
        (images / n).write_bytes(_png(c))
    _save(folders, "two-pages.slbum",
          'STAMP_ADD_IMG(100 100 40 30 "/images/one.png" "" "" "")\n'
          'PAGE_START\n'
          'STAMP_ADD_IMG(100 100 40 30 "/images/two.png" "" "" "")\n'
          'STAMP_ADD_IMG(10 10 40 30 "/images/one.png" "" "" "")\n')
    _save(folders, "plain.slbum")
    page.evaluate("StampAlbum.openSaved('two-pages.slbum')")
    _wait(page, "StampAlbum._currentFile === 'two-pages.slbum'")
    _wait(page, "document.querySelectorAll('#img-grid .img-item').length === 2")
    labels = page.evaluate("[...document.querySelectorAll('#img-grid .img-add')]"
                           ".map(b => b.getAttribute('aria-label'))")
    assert labels == ["Add image one.png", "Add image two.png"]  # every page, each once
    page.evaluate("StampAlbum.openSaved('plain.slbum')")
    _wait(page, "StampAlbum._currentFile === 'plain.slbum'")
    _wait(page, "document.querySelectorAll('#img-grid .img-item').length === 0")
    assert page.is_visible("#img-empty")


def test_a_missing_image_says_so(page, folders):
    page.evaluate("StampAlbum.newAlbum();"
                  " StampAlbum.add({t: 'image', x: 10, y: 10, w: 80, h: 60,"
                  " img: '/images/lost.png'})")
    _wait(page, "document.querySelectorAll('#img-grid .img-item.missing').length === 1")
    assert page.text_content(".img-item.missing").strip() == "Image not found"
    assert page.evaluate("document.querySelector('.img-item.missing .img-add').disabled")


def test_images_panel_passes_axe(page, folders):
    (folders / "images" / "a.png").write_bytes(_png((0, 0, 200)))
    page.evaluate("StampAlbum.newAlbum()")
    assert _axe(page, "#sidebar") == []
    page.evaluate("StampAlbum.placeImage('a.png')")
    _wait(page, "document.querySelectorAll('#img-grid .img-item').length === 1")
    assert _axe(page, "#sidebar") == []


def test_menus_pass_axe(page, folders):
    _save(folders, "x.slbum")
    _open_file_menu(page)
    page.click("#menu-recent")
    _wait(page, "document.querySelectorAll('#menu-recent-list .mi').length === 1")
    assert _axe(page, "#tb") == []
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    page.click("#menu-help-btn")
    assert _axe(page, "#tb") == []


def test_phone_shows_open_recent_below_its_item(base_url, folders):
    import playwright.sync_api as pw

    _save(folders, "x.slbum")
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
        pg.goto(base_url + "/")
        wait_for_app(pg)
        pg.evaluate("document.getElementById('tutorial-overlay').classList.remove('open')")
        assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
        pg.click("#menu-help-btn")
        assert pg.is_visible("#menu-help")
        pg.click("#menu-help-btn")
        pg.click("#menu-file-btn")
        pg.click("#menu-recent")
        _wait(pg, "document.querySelectorAll('#menu-recent-list .mi').length === 1")
        r, item = pg.evaluate("""[
            document.querySelector('#menu-recent-list .mi').getBoundingClientRect().toJSON(),
            document.getElementById('menu-recent').getBoundingClientRect().toJSON()]""")
        assert r["top"] >= item["bottom"] - 1 and r["right"] <= 390
        b.close()


# ── The server ──

def test_recent_route_sorts_newest_first(folders):
    now = time.time()
    _save(folders, "c.slbum", mtime=now - 20)
    _save(folders, "a.txt", mtime=now)
    _save(folders, "b.slbum", mtime=now - 10)
    (folders / "notes.md").write_text("x")
    client = TestClient(api.app)
    assert client.get("/files").json() == ["a.txt", "b.slbum", "c.slbum"]
    assert client.get("/files", params={"sort": "recent"}).json() == ["a.txt", "b.slbum", "c.slbum"]
    _save(folders, "c.slbum")  # saved again: now the newest
    recent = client.get("/files", params={"sort": "recent", "limit": 2}).json()
    assert recent == ["c.slbum", "a.txt"]


def test_attaching_never_replaces_a_different_image(folders):
    client = TestClient(api.app)
    images = folders / "images"

    def up(name, data):
        r = client.post("/images", files={"file": (name, io.BytesIO(data), "image/png")})
        assert r.status_code == 200
        return r.json()["filename"]

    red, blue = _png((200, 0, 0)), _png((0, 0, 200))
    assert up("scan.png", red) == "scan.png"
    assert up("scan.png", blue) == "scan-2.png"  # another album's scan stays as it was
    assert (images / "scan.png").read_bytes() == red
    assert up("scan.png", red) == "scan.png"     # the same picture again reuses its file
    assert up("scan.png", blue) == "scan-2.png"
    assert up("../../evil.png", red) == "evil.png"
    assert not (folders.parent / "evil.png").exists()
    assert sorted(p.name for p in images.iterdir()) == ["evil.png", "scan-2.png", "scan.png"]
