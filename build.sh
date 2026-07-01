#!/bin/bash
set -e

echo "========================================="
echo "  StampAlbum Pro - macOS Build Script"
echo "========================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

# No native library dependencies needed (pure Python PDF via PyMuPDF)

# Install dev dependencies
echo ""
echo "Installing dependencies..."
pip install -e ".[dev]" -q

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf build/ dist/ __pycache__/ src/stamp_album/__pycache__/ src/stamp_album/*/__pycache__/

# Run PyInstaller
echo ""
echo "Building macOS app bundle..."
pyinstaller stamp_album.spec --clean

# Verify the build
if [ -d "dist/StampAlbum Pro.app" ]; then
    echo ""
    echo "========================================="
    echo "  Build successful!"
    echo "========================================="
    echo ""
    echo "App bundle: dist/StampAlbum Pro.app"
    echo ""
    echo "To run: open \"dist/StampAlbum Pro.app\""
    echo ""
    
    # Show app size
    APP_SIZE=$(du -sh "dist/StampAlbum Pro.app" | cut -f1)
    echo "App size: $APP_SIZE"
else
    echo ""
    echo "ERROR: Build failed. Check the output above for details."
    exit 1
fi
