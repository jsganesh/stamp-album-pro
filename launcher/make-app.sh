#!/bin/bash
# Creates a double-clickable StampAlbum.app for macOS.
# No PyInstaller needed — just a thin wrapper that runs the Python server.
#
# Usage:
#   bash launcher/make-app.sh
#
# Result:
#   ./dist/StampAlbum.app   — drag to Applications folder or launch directly

set -e

APP_NAME="StampAlbum"
APP_DIR="dist/${APP_NAME}.app"
MACS_DIR="${APP_DIR}/Contents/MacOS"
RES_DIR="${APP_DIR}/Contents/Resources"

# Clean previous
rm -rf "$APP_DIR"
mkdir -p "$MACS_DIR" "$RES_DIR"

# Create Info.plist
cat > "${APP_DIR}/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>StampAlbum</string>
    <key>CFBundleIdentifier</key>
    <string>com.stampalbum.pro</string>
    <key>CFBundleName</key>
    <string>StampAlbum Pro</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
PLIST

# Create the launcher script (this is the app's executable)
cat > "${MACS_DIR}/${APP_NAME}" <<'SCRIPT'
#!/bin/bash
# StampAlbum Pro launcher
# Finds the project root (parent of the .app bundle), activates venv,
# starts the server, and opens the browser.

# Determine the app bundle's location and navigate to project root.
# Layout: project-root/dist/StampAlbum.app/Contents/MacOS/StampAlbum (this script)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"                          # .../MacOS
APP_BUNDLE="$(cd "$SCRIPT_DIR/../.." && pwd)"                         # .../StampAlbum.app
DIST_DIR="$(dirname "$APP_BUNDLE")"                                   # .../dist
PROJECT="$(dirname "$DIST_DIR")"                                      # project root

cd "$PROJECT"

# Use venv Python if available, otherwise system Python
PYTHON=""
if [ -f "$PROJECT/venv/bin/python3" ]; then
    PYTHON="$PROJECT/venv/bin/python3"
elif [ -f "$PROJECT/venv/bin/python" ]; then
    PYTHON="$PROJECT/venv/bin/python"
else
    PYTHON=$(which python3 2>/dev/null || which python 2>/dev/null)
fi

if [ -z "$PYTHON" ]; then
    osascript -e 'display dialog "Python not found. Please install Python 3." buttons {"OK"} default button 1 with icon stop'
    exit 1
fi

export STAMP_ALBUM_NO_BROWSER=0
exec "$PYTHON" -m stamp_album.serve
SCRIPT

chmod +x "${MACS_DIR}/${APP_NAME}"

# Create a simple SVG icon (stamp icon)
cat > "${RES_DIR}/icon.svg" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="8" y="8" width="84" height="84" rx="10" fill="#e94560"/>
  <rect x="18" y="18" width="64" height="64" rx="6" fill="#fff"/>
  <rect x="28" y="28" width="44" height="44" rx="4" fill="none" stroke="#e94560" stroke-width="3"/>
  <circle cx="50" cy="50" r="10" fill="#e94560"/>
</svg>
SVG

echo ""
echo "  ✓ Created ${APP_DIR}"
echo ""
echo "  To use: open '${APP_DIR}'"
echo "  Or: mv '${APP_DIR}' /Applications/"
echo ""
