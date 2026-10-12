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
        assert sys.stdout is not None and sys.stdout.isatty() is False
        assert sys.stderr is not None
        print("goes nowhere")
    finally:
        sys.stdout.close()
        sys.stderr.close()
