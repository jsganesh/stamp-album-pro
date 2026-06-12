"""
Cross-platform desktop wrapper for StampAlbum Pro (Windows / macOS / Linux).

Launches the FastAPI web app on a background thread bound to localhost on a
free port, waits until it is serving, then opens a native desktop window
(via pywebview) pointing at it. This gives a single codebase that ships as a
native-feeling desktop app on all three operating systems while reusing the
full-featured web UI (drag-and-drop, collections, accounts, version history).

Usage:
    python -m stamp_album.desktop
    # or after install:
    stamp-album-desktop
"""

from __future__ import annotations

import socket
import sys
import threading
import time
from urllib.request import urlopen

import uvicorn


def _find_free_port() -> int:
    """Ask the OS for an available TCP port on the loopback interface."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _ServerThread(threading.Thread):
    """Runs uvicorn in a daemon thread so it dies with the GUI."""

    def __init__(self, host: str, port: int):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self._server: uvicorn.Server | None = None

    def run(self) -> None:
        from stamp_album.api import app

        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="warning",
            # Single worker — desktop app is single-user locally
            workers=1,
        )
        self._server = uvicorn.Server(config)
        self._server.run()

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True


def _wait_for_server(url: str, timeout: float = 15.0) -> bool:
    """Poll the server until it responds or the timeout elapses."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.15)
    return False


def main() -> int:
    """Launch the server and open the desktop window."""
    host = "127.0.0.1"
    port = _find_free_port()
    base_url = f"http://{host}:{port}"

    # Start the FastAPI server in the background
    server = _ServerThread(host, port)
    server.start()

    if not _wait_for_server(base_url + "/", timeout=20.0):
        print(
            "ERROR: StampAlbum Pro server did not start in time.\n"
            "This usually means a native dependency (WeasyPrint / Pango / Cairo) "
            "is missing. See the README for per-OS install instructions.",
            file=sys.stderr,
        )
        return 1

    # Open the native desktop window pointing at the local server
    try:
        import webview
    except ImportError:
        print(
            "ERROR: pywebview is not installed. Install it with:\n"
            "    pip install pywebview\n"
            f"Meanwhile, the app is running at {base_url} — open it in a browser.",
            file=sys.stderr,
        )
        # Keep the server alive so the user can still use the browser
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return 0

    window = webview.create_window(
        "StampAlbum Pro",
        base_url,
        width=1400,
        height=900,
        min_size=(900, 600),
        text_select=True,
    )

    def _on_closed() -> None:
        server.stop()

    window.events.closed += _on_closed

    # webview.start() blocks until the window is closed.
    # gui=None lets pywebview auto-pick the best native backend per OS
    # (Cocoa/WebKit on macOS, EdgeChromium on Windows, GTK/QT on Linux).
    webview.start()
    server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
