#!/bin/bash
# StampAlbum Pro Launcher for macOS
# Double-click this file in Finder to start the app.
# Terminal will open and show the server log.
# Press Ctrl+C to stop the server.

cd "$(dirname "$0")/.."
if [ -f venv/bin/python3 ]; then
    exec venv/bin/python3 -m stamp_album.serve
elif [ -f venv/bin/python ]; then
    exec venv/bin/python -m stamp_album.serve
else
    exec python3 -m stamp_album.serve
fi
