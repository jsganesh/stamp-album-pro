# Building the app

StampAlbum Pro is a web app (FastAPI server + browser UI in `src/stamp_album/web`). The installed app is the same code, frozen with [PyInstaller](https://pyinstaller.org/), and opens the editor in its own window through [pywebview](https://pywebview.flowrl.com/):

```
StampAlbum Pro.app / StampAlbumPro.exe
  └── __main__.py  (no arguments, frozen → desktop.py)
        ├── uvicorn + FastAPI on 127.0.0.1, a free port, in a background thread
        └── pywebview window → that address
              macOS: WKWebView (built in)   Windows: WebView2 (built into Windows 10 and 11)
```

Exports in the window use a native Save As dialog (`desktop.py`'s `save_export`). If pywebview cannot load, the app opens in the default browser instead.

The built app also accepts the usual flags: `--cli` (headless PDF from a DSL file), `--web` (browser mode). The checks below use them.

## Run from source

See the README: `uv sync --extra dev`, then `uv run stamp-album` (browser) or `uv run stamp-album --desktop` (own window).

## macOS

On a Mac, from the project root:

```bash
make app        # or ./build.sh
```

This builds with `packaging/stamp_album.spec`, runs the built app's checks (`packaging/smoke_test.py`), and zips it:

- `dist/StampAlbum Pro.app`
- `dist/StampAlbumPro-macos.zip` (made with `ditto`, which keeps the app's internal links; Finder's Compress does too)

The app is built for the Mac's own processor: Apple silicon on an Apple silicon Mac, Intel on an Intel Mac.

The app is not signed. The first time, right-click it and choose **Open**, then **Open** again (on macOS 15 and later: open it once, then System Settings › Privacy & Security › **Open Anyway**).

## Windows

Windows builds come from CI, since there's no Windows machine in the workflow. The **App build** workflow (`.github/workflows/app.yml`) builds on `macos-latest` and `windows-latest`, runs the built app's checks on each, and keeps both zips as workflow artifacts for 30 days:

- `StampAlbumPro-windows.zip`: the `StampAlbumPro` folder. Unzip it anywhere and run `StampAlbumPro.exe`. Keep the `_internal` folder next to it.
- `StampAlbumPro-macos.zip`: as above (Apple silicon, since `macos-latest` is).

The workflow runs when `packaging/`, `pyproject.toml`, `uv.lock`, the app's start-up code (`__main__.py`, `desktop.py`, `serve.py`) or the workflow itself changes, and on demand: Actions › App build › **Run workflow**. Download the zips from the run's **Artifacts** section. GitHub wraps each in a zip of its own, so unzip twice.

The exe is not signed. Windows SmartScreen shows "Windows protected your PC" the first time: **More info › Run anyway**.

On a Windows machine the same build works by hand:

```powershell
uv sync --extra dev
uv run pyinstaller packaging/stamp_album.spec --clean --noconfirm
uv run python packaging/smoke_test.py dist/StampAlbumPro/StampAlbumPro.exe
```

## What the spec bundles

- All of `src/stamp_album/web`: the editor page, scripts, styles, tutorial pictures, CodeMirror, and the Source Serif 4 Caption fonts with `OFL.txt`.
- Every `stamp_album` module, uvicorn's run-time modules (it picks them by name), websockets and python-multipart.
- The version comes from `stamp_album/__init__.py`.
- Qt and Tk are excluded on macOS and Windows.

Files the app writes (saved albums, images, version history) go to `~/StampAlbum`, as when run from source.

## Checking a build

`packaging/smoke_test.py <built binary>` runs the frozen app, not the source:

1. `--cli`: a small album to PDF.
2. `--web` on a free port with no browser: fetches the editor page, its scripts and styles, a tutorial picture and all four caption fonts, and exports a PDF and a PNG.

`src/tests/test_packaging.py` keeps the spec, `build.sh`, the workflow and this checker in step with the code, and checks how a frozen app starts (own window by default, browser without pywebview).

## Not done yet

- **Signing and notarisation.** These need an Apple Developer ID (for `codesign_identity` and notarisation) and a Windows code-signing certificate.
- **An installer** for Windows (the zip is the stopgap), and a `.dmg` for macOS.
- **An app icon.**
- **Intel Macs** need a build on an Intel Mac (or a `macos-13` runner), or a universal2 Python for a universal app.
