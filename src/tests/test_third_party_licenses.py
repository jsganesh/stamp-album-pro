"""The built app carries the licence notices its libraries require, and none of them is copyleft.

The generator (tools/third_party_licenses.py) runs inside the PyInstaller spec, so these
tests check it against the packages installed here, whichever platform that is.
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import third_party_licenses as tpl  # noqa: E402

COPYLEFT = re.compile(r"\b(A?GPL)", re.I)  # GPL and AGPL; LGPL's "L" breaks the word boundary


@pytest.fixture(scope="module")
def notices(tmp_path_factory):
    out = tpl.write(tmp_path_factory.mktemp("licences") / "THIRD_PARTY_LICENSES.txt")
    return out.read_text(encoding="utf-8")


def test_every_runtime_package_has_a_section(notices):
    packages = tpl.runtime_packages()
    assert {"pillow", "reportlab", "fastapi", "pywebview"} <= set(packages)
    for name, dist in packages.items():
        assert f"{name} {dist.version}" in notices, name


def test_the_apps_own_licence_comes_first(notices):
    assert "MIT License" in notices.split(tpl.RULE)[0]


def test_dev_tools_are_not_listed(notices):
    for name in ("pytest", "ruff", "pyinstaller", "playwright"):
        assert f"\n{name} " not in notices


def test_no_runtime_package_is_gpl_or_agpl():
    for name, dist in tpl.runtime_packages().items():
        meta = dist.metadata
        declared = " ".join(
            [meta.get("License-Expression") or "", meta.get("License") or ""]
            + (meta.get_all("Classifier") or [])
        )
        assert not COPYLEFT.search(declared), f"{name}: {declared[:80]}"


def test_a_package_without_a_licence_file_still_gets_a_notice(notices):
    section = notices.split("proxy-tools ")[1].split(tpl.RULE)[1]
    assert "Copyright" in section


def test_the_spec_bundles_the_notices():
    spec = (ROOT / "packaging" / "stamp_album.spec").read_text(encoding="utf-8")
    assert "third_party_licenses.write" in spec
    assert '(str(NOTICES), ".")' in spec
