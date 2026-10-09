"""Run the Node-based tests for the JS DSL core (skipped when node is not installed)."""
import shutil
import subprocess
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
NODE = shutil.which("node")


@pytest.mark.skipif(NODE is None, reason="node is not installed")
@pytest.mark.parametrize("name", ["test_page_size_migration.mjs", "test_dsl_roundtrip.mjs", "test_page_setup.mjs",
                                  "test_page_parsing.mjs", "test_save_details.mjs",
                                  "test_themes.mjs"])
def test_node_suite(name):
    r = subprocess.run([NODE, str(TESTS / name)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
