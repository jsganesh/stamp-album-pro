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

A plain `make app` gives the app an ad-hoc signature only. On another Mac, the first time, right-click it and choose **Open**, then **Open** again (on macOS 15 and later: open it once, then System Settings › Privacy & Security › **Open Anyway**).

### Signed and notarised release

A release for other Macs is signed with a Developer ID and notarised by Apple, so it opens with no warning.

One-time setup:

1. **Developer ID Application certificate.** In Xcode › Settings › Accounts, choose the team, **Manage Certificates…**, **+**, **Developer ID Application**. Only the team's Account Holder can create one. `security find-identity -v -p codesigning` then lists it.
2. **Notary credentials in the keychain.** Make an app-specific password at account.apple.com (Sign-In and Security › App-Specific Passwords), then run this and answer its prompts:

   ```bash
   xcrun notarytool store-credentials stampalbum-notary --team-id ZV97P254RG
   ```

Each release:

```bash
CODESIGN_IDENTITY="Developer ID Application: <name> (ZV97P254RG)" NOTARY_PROFILE=stampalbum-notary ./build.sh
```

`CODESIGN_IDENTITY` also takes the certificate's SHA-1 hash from `security find-identity`. With it set, PyInstaller signs every library and the app with the hardened runtime and `packaging/entitlements.plist` (empty: no protection is switched off). `build.sh` then checks the signature, sends the zip to Apple (`notarytool submit --wait`, usually a few minutes), staples the ticket to the app, zips it again and asks Gatekeeper (`spctl`) to accept it. If Apple refuses it, `xcrun notarytool log <submission id> --keychain-profile stampalbum-notary` says why.

`CODESIGN_IDENTITY` without `NOTARY_PROFILE` signs but doesn't notarise, which is how to check a change to the entitlements. `NOTARY_PROFILE` alone is refused, since Apple notarises only Developer ID builds.

CI builds stay unsigned: the certificate and the notary password are on this Mac only.

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
- The app icon: `packaging/icon/StampAlbum.icns` on macOS, `StampAlbum.ico` on Windows. Both are rendered from `packaging/icon/StampAlbum.svg` by `python tools/make_icon.py` (on a Mac, with Playwright's Chromium); edit the SVG, run it, check the icon at 16 px in Finder's list view, and commit all three. The drawing keeps to Apple's grid (an 824 px body with 100 px clear all round), so macOS shows it as it is rather than on a grey tile.
- Qt and Tk are excluded on macOS and Windows, and mypy (pulled in by pydantic's mypy plugin, which the app never loads) everywhere.

Files the app writes go to `~/StampAlbum`, as when run from source: a folder for each album, with its pictures, and version history.

## Checking a build

`packaging/smoke_test.py <built binary>` runs the frozen app, not the source:

1. `--cli`: a small album to PDF.
2. `--web` on a free port with no browser: fetches the editor page, its scripts and styles, a tutorial picture and all four caption fonts, and exports a PDF and a PNG.

`src/tests/test_packaging.py` keeps the spec, `build.sh`, the workflow and this checker in step with the code, and checks how a frozen app starts (own window by default, browser without pywebview).

## Not done yet

- **Windows signing.** It needs a Windows code-signing certificate.
- **Signed builds from CI.** The Developer ID certificate and notary credentials would have to be repository secrets.
- **An installer** for Windows (the zip is the stopgap), and a `.dmg` for macOS.
- **Intel Macs** need a build on an Intel Mac (or a `macos-13` runner), or a universal2 Python for a universal app.
