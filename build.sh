#!/bin/bash
# Build the StampAlbum Pro app with PyInstaller, check it, and zip it.
#
#   ./build.sh            (or: make app)
#
# macOS:  dist/StampAlbum Pro.app   and  dist/StampAlbumPro-macos.zip
# Linux:  dist/StampAlbumPro/       (for checking only; not shipped)
# Windows builds come from CI (.github/workflows/app.yml).
#
# Uses uv when it is installed (the locked versions), otherwise the current
# Python with the dev extra installed (`pip install -e ".[dev]"`).
set -euo pipefail
cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
    uv sync --extra dev --frozen
    PY=(uv run --no-sync python)
else
    PY=(python3)
fi

echo "Building with PyInstaller..."
"${PY[@]}" -m PyInstaller packaging/stamp_album.spec --clean --noconfirm --log-level WARN

if [ "$(uname)" = "Darwin" ]; then
    BIN="dist/StampAlbum Pro.app/Contents/MacOS/StampAlbumPro"
else
    BIN="dist/StampAlbumPro/StampAlbumPro"
fi

echo ""
echo "Checking the built app..."
"${PY[@]}" packaging/smoke_test.py "$BIN"

if [ "$(uname)" = "Darwin" ]; then
    rm -f dist/StampAlbumPro-macos.zip
    ditto -c -k --keepParent "dist/StampAlbum Pro.app" dist/StampAlbumPro-macos.zip
    echo ""
    echo "App:  dist/StampAlbum Pro.app ($(du -sh "dist/StampAlbum Pro.app" | cut -f1))"
    echo "Zip:  dist/StampAlbumPro-macos.zip"
    echo "Run:  open \"dist/StampAlbum Pro.app\""
    echo "The app is not signed: the first time, right-click it and choose Open."
else
    echo ""
    echo "App:  dist/StampAlbumPro/ ($(du -sh dist/StampAlbumPro | cut -f1))"
fi
