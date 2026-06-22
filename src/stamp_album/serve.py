"""
Browser launcher for StampAlbum Pro (Windows / macOS / Linux).

Starts the FastAPI web app on localhost and opens it in the user's default
web browser. This is the simplest cross-platform way to run the app — no
native GUI toolkit, no WebKit/pywebview dependency, just the browser everyone
already has.

Usage:
    python -m stamp_album.serve
    # or after install:
    stamp-album              (defaults here)
    stamp-album-web

Options (env vars):
    STAMP_ALBUM_PORT   preferred port (default: 8080, falls back to a free one)
    STAMP_ALBUM_HOST   bind host (default: 127.0.0.1)
    STAMP_ALBUM_NO_BROWSER=1   start the server but don't open a browser
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from urllib.request import urlopen

import uvicorn


def _port_is_free(host: str, port: int) -> bool:
    """Return True if the port can be bound on the host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _pick_port(host: str, preferred: int) -> int:
    """Use the preferred port if free, otherwise ask the OS for any free port."""
    if _port_is_free(host, preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def _wait_and_open(url: str, timeout: float = 20.0) -> None:
    """Wait for the server to respond, then open it in the default browser."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.15)

    if os.environ.get("STAMP_ALBUM_NO_BROWSER") == "1":
        return
    try:
        webbrowser.open(url)
    except Exception:
        # Headless / no browser available — the URL is printed by main() anyway
        pass


def main() -> int:
    """Start the server and open the app in the default browser."""
    # macOS: ensure WeasyPrint can find Homebrew native libraries
    if sys.platform == "darwin":
        for brew_prefix in ("/opt/homebrew", "/usr/local"):
            lib_dir = os.path.join(brew_prefix, "lib")
            if os.path.isdir(lib_dir):
                os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", lib_dir)

    host = os.environ.get("STAMP_ALBUM_HOST", "127.0.0.1")
    preferred = int(os.environ.get("STAMP_ALBUM_PORT", "8080"))

    # Kill any existing server on the preferred port first
    if not _port_is_free(host, preferred):
        import subprocess
        try:
            subprocess.run(["lsof", "-ti", f":{preferred}"], capture_output=True, text=True)
            result = subprocess.run(
                ["lsof", "-ti", f":{preferred}"], capture_output=True, text=True
            )
            if result.stdout.strip():
                pid = result.stdout.strip().split("\n")[0]
                os.kill(int(pid), 9)
                time.sleep(0.3)
        except Exception:
            pass

    port = _pick_port(host, preferred)
    url = f"http://{host}:{port}"

    print(f"")
    print(f"  ╔══════════════════════════════════╗")
    print(f"  ║  StampAlbum Pro                  ║")
    print(f"  ║  {url}  ║")
    print(f"  ╚══════════════════════════════════╝")
    print(f"")

    # Open the browser once the server is ready (background thread)
    opener = threading.Thread(target=_wait_and_open, args=(url + "/",), daemon=True)
    opener.start()

    # Run uvicorn in the foreground (blocks until Ctrl+C)
    from stamp_album.api import app

    reload = os.environ.get("STAMP_ALBUM_RELOAD", "") == "1"

    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="warning",
            reload=reload,
        )
    except KeyboardInterrupt:
        pass
    print("\nStampAlbum Pro stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
