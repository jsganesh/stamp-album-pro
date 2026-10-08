"""STAMP_ALBUM_REQUIRE_BROWSER=1 must fail the browser tests when Playwright is
missing, not skip them. Before, the module-level importorskip ran first, so a
machine without Playwright skipped all browser tests even with the flag set."""
import os
import subprocess
import sys
from pathlib import Path

SMOKE = Path(__file__).with_name("test_ui_smoke.py")
# Run pytest on the browser tests with Playwright made unimportable.
RUNNER = (
    "import sys; sys.modules['playwright'] = None; sys.modules['playwright.sync_api'] = None;"
    "import pytest; sys.exit(pytest.main(['-rs', '-p', 'no:cacheprovider', sys.argv[1]]))"
)


def _run(require):
    env = dict(os.environ)
    env.pop("STAMP_ALBUM_REQUIRE_BROWSER", None)
    if require:
        env["STAMP_ALBUM_REQUIRE_BROWSER"] = "1"
    return subprocess.run([sys.executable, "-c", RUNNER, str(SMOKE)], env=env,
                          capture_output=True, text=True, timeout=120)


def test_missing_playwright_fails_when_browser_is_required():
    r = _run(require=True)
    assert r.returncode != 0, r.stdout
    assert "STAMP_ALBUM_REQUIRE_BROWSER" in r.stdout, r.stdout


def test_missing_playwright_skips_when_browser_is_optional():
    r = _run(require=False)
    assert r.returncode in (0, 5), r.stdout  # 5: every test was skipped at collection
    assert "skipped" in r.stdout and "failed" not in r.stdout, r.stdout
