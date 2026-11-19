"""PyInstaller packaging (pending item 11): one spec that builds the current
web app, and an installed app that opens its own window.

Building the app is too slow for the test suite; CI's "App build" workflow
builds it on macOS and Windows and runs packaging/smoke_test.py against it.
These tests keep the spec, the build script and the checker in step with the
code, and check how a frozen app starts.
"""

import re
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "src" / "stamp_album"
SPEC = ROOT / "packaging" / "stamp_album.spec"


def _spec() -> str:
    return SPEC.read_text(encoding="utf-8")


def test_one_spec():
    assert sorted(p.name for p in (ROOT / "packaging").glob("*.spec")) == ["stamp_album.spec"]


def test_build_script_and_workflow_use_the_spec():
    for path in (ROOT / "build.sh", ROOT / ".github" / "workflows" / "app.yml"):
        assert "packaging/stamp_album.spec" in path.read_text(encoding="utf-8"), path


def test_spec_bundles_the_whole_web_folder():
    # index.html, scripts, styles, tutorial pictures, caption fonts and OFL.txt
    assert '(str(PKG / "web"), "stamp_album/web")' in _spec()
    assert (PKG / "web" / "fonts" / "OFL.txt").is_file()


def test_spec_takes_the_version_from_the_package():
    spec = _spec()
    assert 'PKG / "__init__.py"' in spec
    assert not re.search(r'["\']\d+\.\d+\.\d+["\']', spec), "hard-coded version"


def test_spec_names_no_removed_modules():
    spec = _spec()
    for gone in ("stamp_album.ui", "layout_engine", "assets/templates", "weasyprint"):
        assert gone not in spec, gone


# --- App icon --------------------------------------------------------------

ICON = ROOT / "packaging" / "icon"


def test_spec_uses_the_rendered_icons():
    spec = _spec()
    assert 'ICON / "StampAlbum.icns"' in spec
    assert 'ICON / "StampAlbum.ico"' in spec


def test_icns_holds_every_mac_size_with_the_grid_margin():
    from PIL import Image

    with Image.open(ICON / "StampAlbum.icns") as icns:
        assert (512, 512, 2) in icns.info["sizes"]
        icns.size = (512, 512)
        icns.load(scale=2)
        big = icns.convert("RGBA")
    # Apple's grid leaves 100 of 1024 px clear all round; the corner is see-through.
    assert big.size == (1024, 1024)
    assert big.getpixel((50, 50))[3] == 0
    assert big.getpixel((512, 512))[3] == 255


def test_ico_holds_the_windows_sizes():
    from PIL import Image

    with Image.open(ICON / "StampAlbum.ico") as ico:
        assert {(16, 16), (32, 32), (48, 48), (256, 256)} <= ico.info["sizes"]


def test_workflow_releases_as_a_draft_until_the_notarised_zip_is_in():
    workflow = (ROOT / ".github" / "workflows" / "app.yml").read_text(encoding="utf-8")
    create = workflow.split("gh release create")[1].split("dist/StampAlbumPro-macos.zip")[0]
    assert "--draft" in create


# --- Signing and notarisation (macOS) -------------------------------------

# Each one switches off a hardened-runtime protection Apple's notary checks for.
WEAKENING = {
    "com.apple.security.cs.disable-library-validation",
    "com.apple.security.cs.allow-jit",
    "com.apple.security.cs.allow-dyld-environment-variables",
    "com.apple.security.get-task-allow",
}


def test_entitlements_keep_the_hardened_runtime_whole():
    import plistlib

    path = ROOT / "packaging" / "entitlements.plist"
    entitlements = plistlib.loads(path.read_bytes())
    assert not WEAKENING & set(entitlements)


def test_spec_signs_only_with_an_identity_from_the_environment():
    spec = _spec()
    assert 'os.environ.get("CODESIGN_IDENTITY")' in spec
    assert "Developer ID Application:" not in spec.split("CODESIGN_IDENTITY =")[1]


# Windows' `bash` is the WSL launcher, and build.sh is never run there (CI builds Windows).
@pytest.mark.skipif(sys.platform == "win32", reason="build.sh runs on macOS and Linux only")
def test_build_refuses_to_notarise_an_unsigned_app():
    import os
    import subprocess

    env = {k: v for k, v in os.environ.items() if k != "CODESIGN_IDENTITY"}
    env["NOTARY_PROFILE"] = "any"
    run = subprocess.run(
        ["bash", str(ROOT / "build.sh")], env=env, capture_output=True, text=True, timeout=30
    )
    assert run.returncode == 1
    assert "needs CODESIGN_IDENTITY" in run.stderr


def test_build_staples_before_the_shipped_zip():
    body = (ROOT / "build.sh").read_text(encoding="utf-8").split("notarise() {")[1]
    body = body.split("}")[0]
    assert body.index("notarytool submit") < body.index("stapler staple") < body.rindex("zip_app")


def test_smoke_test_checks_every_caption_font():
    sys.path.insert(0, str(ROOT / "packaging"))
    try:
        import smoke_test
    finally:
        sys.path.pop(0)
    from stamp_album.engines.caption_fonts import SERVED

    assert sorted(smoke_test.FONTS) == sorted(SERVED)
    for path in smoke_test.STATIC:
        if path != "/":
            assert (PKG / "web" / path.lstrip("/")).is_file(), path


# --- How a frozen (PyInstaller) app starts --------------------------------


@pytest.fixture
def launch(monkeypatch):
    """Run __main__.main() with argv and frozen-ness; report what it started."""
    import stamp_album.__main__ as entry
    import stamp_album.desktop as desktop
    import stamp_album.serve as serve

    started = []
    monkeypatch.setattr(desktop, "main", lambda: started.append("window") or 0)
    monkeypatch.setattr(serve, "main", lambda: started.append("browser") or 0)

    def run(argv, frozen, webview=True):
        monkeypatch.setattr(sys, "argv", argv)
        if frozen:
            monkeypatch.setattr(sys, "frozen", True, raising=False)
        else:
            monkeypatch.delattr(sys, "frozen", raising=False)
        # None in sys.modules makes `import webview` raise ImportError.
        fake = types.ModuleType("webview") if webview else None
        monkeypatch.setitem(sys.modules, "webview", fake)
        started.clear()
        with pytest.raises(SystemExit) as exc:
            entry.main()
        assert exc.value.code == 0
        return started[:]

    return run


def test_frozen_app_opens_its_own_window(launch):
    assert launch(["StampAlbumPro"], frozen=True) == ["window"]


def test_frozen_app_ignores_finder_process_number(launch):
    assert launch(["StampAlbumPro", "-psn_0_12345"], frozen=True) == ["window"]


def test_frozen_app_without_pywebview_uses_the_browser(launch):
    assert launch(["StampAlbumPro"], frozen=True, webview=False) == ["browser"]


def test_frozen_app_web_flag_uses_the_browser(launch):
    assert launch(["StampAlbumPro", "--web"], frozen=True) == ["browser"]


def test_from_source_still_opens_the_browser(launch):
    assert launch(["stamp-album"], frozen=False) == ["browser"]


def test_windowed_app_gets_stdout_and_stderr(monkeypatch):
    import stamp_album.__main__ as entry

    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(sys, "argv", ["StampAlbumPro"])
    entry._frozen_setup()
    try:
        assert sys.stdout is not None
        sys.stdout.isatty()  # uvicorn's formatter calls this (True for Windows' nul)
        assert sys.stderr is not None
        print("goes nowhere")
    finally:
        sys.stdout.close()
        sys.stderr.close()
