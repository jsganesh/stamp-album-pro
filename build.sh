#!/bin/bash
# Build the StampAlbum Pro app with PyInstaller, check it, and zip it.
#
#   ./build.sh            (or: make app)
#
# macOS:  dist/StampAlbum Pro.app   and  dist/StampAlbumPro-macos.zip
# Linux:  dist/StampAlbumPro/       (for checking only; not shipped)
# Windows builds come from CI (.github/workflows/app.yml).
#
# Signed release on macOS (docs/BUILD.md has the one-time setup):
#   CODESIGN_IDENTITY="Developer ID Application: Name (TEAMID)"  signs with the hardened runtime
#   NOTARY_PROFILE=stampalbum-notary   also notarises and staples (a notarytool keychain profile)
#
# Uses uv when it is installed (the locked versions), otherwise the current
# Python with the dev extra installed (`pip install -e ".[dev]"`).
set -euo pipefail
cd "$(dirname "$0")"

APP="dist/StampAlbum Pro.app"
ZIP="dist/StampAlbumPro-macos.zip"

if [ -n "${NOTARY_PROFILE:-}" ] && [ -z "${CODESIGN_IDENTITY:-}" ]; then
    echo "NOTARY_PROFILE needs CODESIGN_IDENTITY: Apple notarises only Developer ID builds." >&2
    exit 1
fi

if command -v uv >/dev/null 2>&1; then
    uv sync --extra dev --frozen
    PY=(uv run --no-sync python)
else
    PY=(python3)
fi

zip_app() {
    rm -f "$ZIP"
    ditto -c -k --keepParent "$APP" "$ZIP"
}

# Apple checks the zip, but the ticket is stapled to the app, so the app is
# zipped again afterwards: that second zip opens without a network check.
notarise() {
    echo ""
    echo "Notarising (usually a few minutes)..."
    zip_app
    xcrun notarytool submit "$ZIP" --keychain-profile "$NOTARY_PROFILE" --wait
    xcrun stapler staple "$APP"
    zip_app
    spctl --assess --type execute --verbose=2 "$APP"
}

echo "Building with PyInstaller..."
"${PY[@]}" -m PyInstaller packaging/stamp_album.spec --clean --noconfirm --log-level WARN

if [ "$(uname)" = "Darwin" ]; then
    BIN="$APP/Contents/MacOS/StampAlbumPro"
else
    BIN="dist/StampAlbumPro/StampAlbumPro"
fi

echo ""
echo "Checking the built app..."
"${PY[@]}" packaging/smoke_test.py "$BIN"

if [ "$(uname)" != "Darwin" ]; then
    echo ""
    echo "App:  dist/StampAlbumPro/ ($(du -sh dist/StampAlbumPro | cut -f1))"
    exit 0
fi

codesign --verify --deep --strict "$APP"
if [ -n "${NOTARY_PROFILE:-}" ]; then
    notarise
else
    zip_app
fi
echo ""
echo "App:  $APP ($(du -sh "$APP" | cut -f1))"
echo "Zip:  $ZIP"
echo "Run:  open \"$APP\""
if [ -z "${NOTARY_PROFILE:-}" ]; then
    echo "Not notarised: on another Mac, right-click it and choose Open the first time."
fi
