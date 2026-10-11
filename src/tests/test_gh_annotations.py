"""The GitHub annotation plugin (gh_annotations.py).

Each test runs pytest in a subprocess on a small throwaway test folder, with
the plugin loaded, and reads the ::error lines it prints.
"""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import gh_annotations as gha

TESTS_DIR = Path(__file__).resolve().parent


def _run(tmp_path, files, github=True):
    for name, body in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(body), encoding="utf-8")
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GITHUB_")}
    env["PYTHONPATH"] = str(TESTS_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    if github:
        env["GITHUB_ACTIONS"] = "true"
        env["GITHUB_WORKSPACE"] = str(tmp_path)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "gh_annotations", "-p", "no:cacheprovider",
         "--tb=short", "-q", str(tmp_path)],
        cwd=tmp_path, env=env, capture_output=True, encoding="utf-8",
    )
    return [ln for ln in r.stdout.splitlines() if ln.startswith("::error ")], r


def _parse(cmd):
    """{'file', 'line', 'title', 'message'} from one ::error line, unescaped."""
    head, message = cmd[len("::error "):].split("::", 1)
    props = dict(p.split("=", 1) for p in head.split(","))

    def un(s):
        return (s.replace("%0A", "\n").replace("%0D", "\r").replace("%3A", ":")
                .replace("%2C", ",").replace("%25", "%"))

    return {"file": un(props["file"]), "line": int(props["line"]),
            "title": un(props["title"]), "message": un(message)}


def test_failed_test_is_annotated_where_it_failed(tmp_path):
    cmds, _ = _run(tmp_path, {"tests/test_a.py": """
        def test_sizes():
            w = 19
            assert w == 21, "frame too narrow"
    """})
    assert len(cmds) == 1
    a = _parse(cmds[0])
    assert a["file"] == "tests/test_a.py" and a["line"] == 4
    assert a["title"] == "pytest: tests/test_a.py::test_sizes failed"
    assert "frame too narrow" in a["message"] and "assert 19 == 21" in a["message"]


def test_error_in_setup(tmp_path):
    cmds, _ = _run(tmp_path, {"test_fixture.py": """
        import pytest

        @pytest.fixture
        def album():
            raise RuntimeError("no album")

        def test_uses_album(album):
            pass
    """})
    assert len(cmds) == 1
    a = _parse(cmds[0])
    assert a["title"] == "pytest: test_fixture.py::test_uses_album error in setup"
    assert "no album" in a["message"]


def test_collection_error(tmp_path):
    # pytest stops the run after a collection error, so this is the only annotation.
    cmds, _ = _run(tmp_path, {
        "test_broken.py": "import not_a_module_anywhere\n",
        "test_fine.py": "def test_ok():\n    assert False\n",
    })
    assert len(cmds) == 1
    a = _parse(cmds[0])
    assert a["title"] == "pytest: test_broken.py collection error"
    assert a["file"] == "test_broken.py" and "not_a_module_anywhere" in a["message"]


def test_special_characters_are_escaped(tmp_path):
    cmds, _ = _run(tmp_path, {"test_esc.py": """
        import pytest

        @pytest.mark.parametrize("v", ["a,b:c"])
        def test_x(v):
            assert False, "100% wrong\\nsecond line"
    """})
    assert len(cmds) == 1
    raw = cmds[0]
    assert "\n" not in raw and "%0A" in raw and "%25" in raw
    head = raw[len("::error "):].split("::", 1)[0]
    assert head.count(",") == 2  # file, line, title: the parameter's comma is escaped
    a = _parse(raw)
    assert a["title"] == "pytest: test_esc.py::test_x[a,b:c] failed"
    assert "100% wrong" in a["message"] and "second line" in a["message"]


def test_at_most_ten_annotations(tmp_path):
    cmds, _ = _run(tmp_path, {"test_many.py": """
        import pytest

        @pytest.mark.parametrize("i", range(12))
        def test_n(i):
            assert i < 0
    """})
    assert len(cmds) == 10
    parsed = [_parse(c) for c in cmds]
    assert all(p["title"].endswith("failed") for p in parsed[:9])
    assert parsed[9]["title"] == "pytest: 3 more failures"
    assert parsed[9]["message"].splitlines() == [
        f"test_many.py::test_n[{i}] (failed)" for i in (9, 10, 11)
    ]


def test_exactly_ten_failures_all_in_full(tmp_path):
    cmds, _ = _run(tmp_path, {"test_ten.py": """
        import pytest

        @pytest.mark.parametrize("i", range(10))
        def test_n(i):
            assert i < 0
    """})
    assert len(cmds) == 10 and all(_parse(c)["title"].endswith("failed") for c in cmds)


def test_crash_outside_the_repo_points_at_the_test(tmp_path):
    cmds, _ = _run(tmp_path, {"test_lib.py": """
        import json

        def test_bad_json():
            json.loads("{")
    """})
    a = _parse(cmds[0])
    assert a["file"] == "test_lib.py" and a["line"] == 4  # the def line, not json/decoder.py


def test_silent_off_github_and_when_all_pass(tmp_path):
    failing = {"test_f.py": "def test_f():\n    assert False\n"}
    cmds, r = _run(tmp_path, failing, github=False)
    assert cmds == [] and "::error" not in r.stdout
    cmds, r = _run(tmp_path, {"test_f.py": "def test_f():\n    assert True\n"})
    assert cmds == [] and r.returncode == 0


def test_long_message_is_truncated():
    cmd = gha.build_commands(
        [{"nodeid": "t", "kind": "failed", "file": "f.py", "line": 1, "message": "x" * 10000}]
    )[0]
    assert len(cmd) < gha.MAX_MESSAGE + 200
