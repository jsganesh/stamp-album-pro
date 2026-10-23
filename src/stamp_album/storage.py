"""Where albums, their pictures and their exports are kept.

Each album has a folder of its own in the albums folder (``~/StampAlbum`` unless
``STAMP_ALBUM_FILES`` says otherwise)::

    StampAlbum/
      New Zealand/
        New Zealand.slbum
        images/      the pictures this album uses
        exports/     its PDF, PNG, SVG and HTML (exports.py)

An album is named by its file name, "New Zealand.slbum", as before; its folder is the
name without ".slbum". Albums from before folders sat loose in the albums folder and
shared one ``images`` folder: ``move_loose_albums`` gives each its own folder when the app
starts, copying the pictures it uses (nothing is deleted). A loose album found later is
still listed and opened, and moves into a folder when it is next saved.

Pictures are referred to by name ("/images/map.png" in the file). ``find_image`` looks in
the album's own folder, then the old shared folder, then the holding folder for pictures
attached before an album's first save, then any album's folder.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Optional

FILES_DIR = Path(os.environ.get("STAMP_ALBUM_FILES", Path.home() / "StampAlbum"))
IMAGES_DIR = FILES_DIR / "images"  # the shared folder albums used before they had their own
HOLD_NAME = ".unsaved-images"  # pictures attached to an album not yet saved
MOVED_NOTE = "Albums moved into folders.txt"
LAST_MOVED: list[tuple[str, str]] = []  # what move_loose_albums moved when the app started

ALBUM_SUFFIXES = (".slbum", ".txt")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
# A picture placed in an album: STAMP_ADD_IMG(x y w h "img" ...), "img" a name or "/images/name"
_IMG_RE = re.compile(r'^\s*STAMP_ADD_IMG\(\s*\S+\s+\S+\s+\S+\s+\S+\s+"((?:[^"\\]|\\.)*)"', re.M)


def hold_dir() -> Path:
    return FILES_DIR / HOLD_NAME


def valid_album_name(name: str, saving: bool = False) -> bool:
    """Whether *name* is a plain album file name (no folders), .slbum (or .txt to open)."""
    return bool(
        name
        and not name.startswith(".")
        and not any(c in name for c in "/\\:\0")
        and Path(name).suffix.lower() in ((".slbum",) if saving else ALBUM_SUFFIXES)
    )


class OutsideAlbums(ValueError):
    """A path that would lead outside the albums folder."""


def inside(*parts) -> Path:
    """The albums folder joined with *parts*, or OutsideAlbums if the result would be outside
    it. Every path built from a name the editor sends goes through here, so no name ("..",
    "/etc", "a/../../x") can reach another folder."""
    base = os.path.normpath(os.path.abspath(FILES_DIR))
    path = os.path.normpath(os.path.join(base, *[str(p) for p in parts]))
    if path != base and not path.startswith(base + os.sep):
        raise OutsideAlbums(path)
    return Path(path)


def album_dir(name: str) -> Path:
    """The folder of the album named *name* ("New Zealand.slbum" -> StampAlbum/New Zealand)."""
    return inside(Path(name).stem)


def album_path(name: str) -> Path:
    """Where the album *name* is: in its own folder, or loose (an album not yet moved)."""
    own = inside(Path(name).stem, name)
    loose = inside(name)
    if own.is_file() or not loose.is_file():
        return own
    return loose


def images_dir(name: Optional[str]) -> Path:
    """Where pictures attached to the album *name* go: its folder, or the holding folder."""
    if name and valid_album_name(name) and album_path(name).is_file():
        return inside(Path(name).stem, "images")
    return hold_dir()


def list_albums() -> list[Path]:
    """Every album: one in each folder, and any still loose in the albums folder."""
    if not FILES_DIR.is_dir():
        return []
    out = []
    for p in FILES_DIR.iterdir():
        if p.name.startswith("."):
            continue
        if p.is_file() and p.suffix in ALBUM_SUFFIXES and p.name != MOVED_NOTE:
            out.append(p)
        elif p.is_dir() and p != IMAGES_DIR:
            for suffix in ALBUM_SUFFIXES:
                f = p / (p.name + suffix)
                if f.is_file():
                    out.append(f)
    return out


def image_names(dsl: str) -> list[str]:
    """The picture names an album's text uses, each once, in order."""
    seen: list[str] = []
    for ref in _IMG_RE.findall(dsl):
        name = ref.replace("\\\\", "\\").split("/")[-1].split("\\")[-1]
        if name and Path(name).suffix.lower() in IMAGE_SUFFIXES and name not in seen:
            seen.append(name)
    return seen


def _plain_image_name(name: str) -> str:
    return str(name or "").split("/")[-1].split("\\")[-1]


def find_image(name: str, album: Optional[str] = None) -> Optional[Path]:
    """The file for the picture *name* of the album *album*, wherever it is kept, or None."""
    fname = _plain_image_name(name)
    if not fname or fname.startswith("."):
        return None
    places = []
    if album and valid_album_name(album):
        places.append(inside(Path(album).stem, "images", fname))
    places += [inside(IMAGES_DIR, fname), inside(HOLD_NAME, fname)]
    for f in list_albums():  # any album's folder: the picture may have come from another
        if f.parent != FILES_DIR:
            places.append(inside(f.parent, "images", fname))
    for p in places:
        if p.is_file():
            return p
    return None


def copy_images(dsl: str, to_album: str, from_album: Optional[str] = None) -> list[str]:
    """Copy the pictures *dsl* uses into *to_album*'s images folder, from wherever they are
    (*from_album* is looked in first). Pictures already there are left. Returns the names copied."""
    dest = inside(Path(to_album).stem, "images")
    copied = []
    for name in image_names(dsl):
        target = inside(dest, name)
        if target.exists():
            continue
        src = find_image(name, from_album)
        if src is None or src.parent == dest:
            continue
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        copied.append(name)
    return copied


def save_album(name: str, content: str, from_album: Optional[str] = None) -> Path:
    """Write the album into its own folder, with the pictures it uses. A loose file of the
    same name (an album from before folders) moves in: it is replaced by this save."""
    folder = album_dir(name)
    folder.mkdir(parents=True, exist_ok=True)
    path = inside(folder, name)
    path.write_text(content, encoding="utf-8")
    copy_images(content, name, from_album)
    loose = inside(name)
    if loose.is_file() and loose != path:
        loose.unlink()
    return path


def delete_album(name: str) -> None:
    """Delete the album: its whole folder (pictures and exports too), or a loose file."""
    base, path = inside(), album_path(name)
    folder = inside(path.parent)
    if folder != base and folder.parent == base:  # its own folder, never the albums folder
        shutil.rmtree(folder)
    else:
        inside(path).unlink()


def _free_name(stem: str) -> str:
    """*stem*, or "stem (2)", "stem (3)"... whichever has no folder yet."""
    n = 1
    while True:
        candidate = stem if n == 1 else f"{stem} ({n})"
        if not (FILES_DIR / candidate).exists():
            return candidate
        n += 1


def move_loose_albums() -> list[tuple[str, str]]:
    """Give every album still loose in the albums folder a folder of its own, with copies of
    the pictures it uses from the shared images folder. Nothing is deleted except the loose
    album file once its copy is in place. Returns [(old file name, new file name)] and adds
    them to a note in the albums folder."""
    if not FILES_DIR.is_dir():
        return []
    moved = []
    for p in sorted(FILES_DIR.iterdir()):
        if not (p.is_file() and p.suffix in ALBUM_SUFFIXES) or p.name.startswith("."):
            continue
        if p.name == MOVED_NOTE:  # this function's own note, not an album
            continue
        stem = _free_name(p.stem)
        folder = FILES_DIR / stem
        new_name = stem + p.suffix
        content = p.read_text(encoding="utf-8", errors="replace")
        folder.mkdir()
        target = folder / new_name
        shutil.copy2(p, target)
        dest = folder / "images"
        for img in image_names(content):
            src = IMAGES_DIR / img
            if src.is_file():
                dest.mkdir(exist_ok=True)
                shutil.copy2(src, dest / img)
        p.unlink()
        moved.append((p.name, new_name))
    LAST_MOVED[:] = moved
    if moved:
        note = FILES_DIR / MOVED_NOTE
        lines = [f"{old} -> {Path(new).stem}/{new}" for old, new in moved]
        with note.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    return moved
