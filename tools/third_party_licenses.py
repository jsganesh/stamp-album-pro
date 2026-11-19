"""Write THIRD_PARTY_LICENSES.txt: the licence notices of everything the built app carries.

    python tools/third_party_licenses.py [output file]

packaging/stamp_album.spec runs this on every build and bundles the result, so the Mac
and Windows apps each list the libraries installed for them (Windows has no PyObjC).
Walks the runtime dependencies of stamp-album-pro, never the dev extra, and takes each
package's own licence files from its installed metadata. Pillow's file already holds the
notices for the C libraries its wheel bundles (libtiff, libjpeg, freetype and the rest).
"""

from __future__ import annotations

import re
import sys
from importlib import metadata as md
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "stamp_album" / "web"
LICENCE_FILE = re.compile(r"(^|/)(licen[cs]e|copying|notice)[^/]*$", re.I)
RULE = "=" * 78

HEADER = """StampAlbum Pro is MIT licensed (see LICENSE). It includes the software below,
each under its own licence. The notices are reproduced as its authors require.
"""


def runtime_packages(root: str = "stamp-album-pro") -> dict[str, md.Distribution]:
    """The installed distributions the app needs at run time, found through Requires-Dist."""
    found: dict[str, md.Distribution] = {}
    todo = [root]
    while todo:
        name = canonicalize_name(todo.pop())
        if name in found:
            continue
        found[name] = md.distribution(name)
        for line in found[name].requires or []:
            req = Requirement(line)
            if not req.marker or req.marker.evaluate({"extra": ""}):
                todo.append(req.name)
    del found[canonicalize_name(root)]
    return found


def licence_texts(dist: md.Distribution) -> list[str]:
    files = [f for f in dist.files or [] if LICENCE_FILE.search(str(f).replace("\\", "/"))]
    paths = [Path(dist.locate_file(f)) for f in files]
    return [p.read_text(encoding="utf-8", errors="replace").strip() for p in paths]


def describe(name: str, dist: md.Distribution) -> str:
    meta = dist.metadata
    licence = meta.get("License-Expression") or "see below"
    lines = [RULE, f"{name} {dist.version}  ({licence})", RULE]
    texts = licence_texts(dist)
    if not texts:  # a few packages ship no licence file: name the author and where it lives
        author = meta.get("Author") or meta.get("Author-email") or "its authors"
        url = meta.get("Home-page") or "its project page"
        texts = [f"Copyright {author}. Licence: {meta.get('License') or licence}. See {url}."]
    return "\n".join(lines + ["\n\n".join(texts), ""])


def extra_notices() -> list[str]:
    """Licences of what is not a pip package: Python itself, CodeMirror and the caption font."""
    python = Path(sys.base_prefix) / "lib" / f"python{sys.version_info[0]}.{sys.version_info[1]}"
    sources = [
        ("Python " + sys.version.split()[0], python / "LICENSE.txt"),
        ("CodeMirror", WEB / "codemirror-LICENSE.txt"),
        ("Source Serif 4 Caption (Adobe)", WEB / "fonts" / "OFL.txt"),
    ]
    out = []
    for title, path in sources:
        if path.is_file():  # the Windows layout of Python has no lib/python3.x folder
            out.append("\n".join([RULE, title, RULE, path.read_text(encoding="utf-8").strip(), ""]))
    return out


def write(target: Path) -> Path:
    parts = [HEADER, (ROOT / "LICENSE").read_text(encoding="utf-8").strip() + "\n"]
    parts += [describe(n, d) for n, d in sorted(runtime_packages().items())]
    parts += extra_notices()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(parts), encoding="utf-8")
    return target


if __name__ == "__main__":
    out = write(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "THIRD_PARTY_LICENSES.txt"))
    print(f"Wrote {out}")
