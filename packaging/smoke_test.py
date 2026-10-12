"""Check a built StampAlbum Pro app (PyInstaller output) actually works.

    python packaging/smoke_test.py "dist/StampAlbum Pro.app/Contents/MacOS/StampAlbumPro"
    python packaging/smoke_test.py dist/StampAlbumPro/StampAlbumPro.exe

Runs the frozen binary, not the source:
1. ``--cli``: a small album to PDF.
2. ``--web``: starts the server without a browser, then fetches the editor page,
   its scripts and styles, a tutorial picture and each caption font, and exports
   a PDF and a PNG.

The app is windowed (no console), so nothing is read from its output; every
check looks at files and HTTP responses. Exit code 0 means every check passed.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

DSL = (
    'ALBUM_TITLE("Smoke test")\n'
    "ALBUM_PAGES_SIZE(210 297)\n"
    "PAGE_START\n"
    'PAGE_TEXT_CENTER("HB" 14 "StampAlbum Pro")\n'
)

STATIC = {
    "/": "text/html",
    "/app.js": "javascript",
    "/dsl_core.js": "javascript",
    "/caption_metrics.js": "javascript",
    "/codemirror.min.js": "javascript",
    "/style.css": "text/css",
    "/tutorial-1-add.png": "image/png",
}
FONTS = [
    "SourceSerif4Caption-Regular.ttf",
    "SourceSerif4Caption-It.ttf",
    "SourceSerif4Caption-Bold.ttf",
    "SourceSerif4Caption-Semibold.ttf",
]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get(url: str, data: bytes | None = None) -> tuple[int, str, bytes]:
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()


def check_cli(app: Path, work: Path) -> None:
    src = work / "smoke.slbum"
    out = work / "smoke.pdf"
    src.write_text(DSL, encoding="utf-8")
    subprocess.run([str(app), "--cli", str(src), "-o", str(out)], timeout=180, check=True)
    assert out.read_bytes().startswith(b"%PDF"), "CLI did not write a PDF"
    print("ok  --cli wrote a PDF")


def check_server(app: Path, work: Path) -> None:
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ, STAMP_ALBUM_NO_BROWSER="1", STAMP_ALBUM_PORT=str(port),
               STAMP_ALBUM_FILES=str(work / "files"))
    proc = subprocess.Popen([str(app), "--web"], env=env)
    try:
        deadline = time.time() + 120
        while True:
            try:
                _get(base + "/")
                break
            except OSError:
                if proc.poll() is not None:
                    raise AssertionError(f"server exited with {proc.returncode}") from None
                if time.time() > deadline:
                    raise AssertionError("server did not start in 120 s") from None
                time.sleep(0.5)
        print(f"ok  --web serving at {base}")

        for path, kind in STATIC.items():
            status, ctype, body = _get(base + path)
            assert status == 200 and kind in ctype and body, (path, status, ctype)
        print(f"ok  {len(STATIC)} editor files")

        for name in FONTS:
            status, ctype, body = _get(f"{base}/fonts/{name}")
            assert status == 200 and len(body) > 10_000, (name, status, len(body))
        print(f"ok  {len(FONTS)} caption fonts")

        for fmt, magic in (("pdf", b"%PDF"), ("png", b"\x89PNG")):
            payload = json.dumps({"dsl": DSL, "format": fmt}).encode()
            status, _, body = _get(base + "/export", payload)
            assert status == 200 and body.startswith(magic), (fmt, status, body[:20])
            print(f"ok  /export {fmt}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    app = Path(argv[1]).resolve()
    if not app.is_file():
        print(f"not a file: {app}")
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        check_cli(app, work)
        check_server(app, work)
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
