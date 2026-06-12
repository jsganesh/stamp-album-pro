# Cross-Platform Build & Packaging Guide

StampAlbum Pro ships as a **single desktop app** on Windows, macOS, and Linux by
wrapping the FastAPI web application in a native window via
[pywebview](https://pywebview.flowrl.com/). One codebase, three platforms.

## Architecture

```
┌─────────────────────────────────────────┐
│  Native window (pywebview)               │
│  ┌─────────────────────────────────────┐ │
│  │  Web UI (index.html + JS)           │ │  ← all features live here
│  │  drag-drop, collections, accounts,  │ │
│  │  version history, live preview      │ │
│  └─────────────────────────────────────┘ │
│                  ▲ HTTP                    │
│  ┌───────────────┴─────────────────────┐ │
│  │  FastAPI server (localhost, daemon) │ │  ← started by desktop.py
│  │  WeasyPrint → PDF, PyMuPDF → PNG    │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

The PyQt6 desktop UI (`ui/`) is **legacy** and no longer the primary product.
The web app + pywebview wrapper is the cross-platform path.

## Running from source (any OS)

```bash
python -m venv venv
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -e .
python -m stamp_album.desktop      # opens the native desktop window
```

Or just run the web app and use a browser (works everywhere):

```bash
python -m stamp_album.api          # then open http://localhost:8080
```

## Native dependencies (WeasyPrint)

WeasyPrint needs Pango/Cairo/GDK-Pixbuf. **PyMuPDF** (rasterization for
PNG/SVG preview) ships as a self-contained wheel — no system libs needed.

| OS | Install command |
|----|-----------------|
| **macOS (Apple Silicon)** | `brew install pango glib gdk-pixbuf libffi harfbuzz fribidi cairo` |
| **macOS (Intel)** | Same — Homebrew installs to `/usr/local`; the build script detects both prefixes |
| **Windows** | Install [GTK3 runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Installer/releases) **or** use the MSYS2 Pango bundle. WeasyPrint docs: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows |
| **Linux (Debian/Ubuntu)** | `sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev` |
| **Linux (Fedora)** | `sudo dnf install pango gdk-pixbuf2 cairo` |

pywebview's native rendering backend per OS:
- **macOS**: WKWebView (built in, via pyobjc — installed automatically)
- **Windows**: EdgeChromium / WebView2 (ships with Windows 10/11)
- **Linux**: GTK WebKit2 — `sudo apt install libwebkit2gtk-4.1-0 gir1.2-webkit2-4.1` (or `python3-gi`)

## Building distributable bundles

### macOS (.app)

```bash
pyinstaller stamp_album.spec
# Output: dist/StampAlbum Pro.app
```

The spec auto-detects Apple Silicon (`/opt/homebrew`) vs Intel (`/usr/local`)
Homebrew prefixes and bundles the right dylibs.

### Windows (.exe)

```powershell
pyinstaller --name "StampAlbumPro" --windowed --onedir ^
  --add-data "src/stamp_album/web;stamp_album/web" ^
  src/stamp_album/desktop.py
```

Ship the GTK3 runtime DLLs alongside (or document the GTK install step).

### Linux (AppImage / binary)

```bash
pyinstaller --name stamp-album-pro --onedir \
  --add-data "src/stamp_album/web:stamp_album/web" \
  src/stamp_album/desktop.py
# Optionally wrap dist/ into an AppImage with appimagetool.
```

## Docker (web deployment)

For the hosted/SaaS version, run the FastAPI app in a container:

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .
EXPOSE 8080
CMD ["python", "-m", "stamp_album.api"]
```

```bash
docker build -t stampalbum-pro .
docker run -p 8080:8080 stampalbum-pro
```

## Verifying a build

```bash
pytest src/tests/ -q                          # all logic tests
python -m stamp_album.desktop                  # smoke-test the window
curl -X POST localhost:8080/export -d '{"dsl":"PAGE_START","format":"pdf"}' \
     -H 'Content-Type: application/json' -o test.pdf   # export path
```
