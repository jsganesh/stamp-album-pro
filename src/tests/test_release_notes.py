"""tools/release_notes.py: the notes the App build workflow publishes for a v* tag."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("release_notes", ROOT / "tools" / "release_notes.py")
release_notes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(release_notes)

CHANGELOG = """# Changelog

## [Unreleased]

### Added
- Something new

## [1.2.0] - 2026-11-01

Summary line.

### Fixed
- A fix

## [1.1.0] - 2026-10-01

### Added
- Older
"""


def test_notes_hold_only_that_versions_section():
    notes = release_notes.release_notes(CHANGELOG, "v1.2.0")
    assert notes.startswith("### Downloads\n")
    assert "Summary line." in notes and "- A fix" in notes
    assert "Something new" not in notes and "Older" not in notes


def test_notes_link_to_the_changelog_heading():
    notes = release_notes.release_notes(CHANGELOG, "1.2.0")
    assert "/blob/v1.2.0/CHANGELOG.md#120---2026-11-01)" in notes


def test_the_last_section_runs_to_the_end():
    assert "- Older" in release_notes.release_notes(CHANGELOG, "1.1.0")


@pytest.mark.parametrize("version", ["9.9.9", "1.2"])
def test_a_version_without_a_section_is_an_error(version):
    with pytest.raises(LookupError):
        release_notes.release_notes(CHANGELOG, version)


def test_an_empty_section_is_an_error():
    with pytest.raises(LookupError):
        release_notes.release_notes("## [2.0.0] - 2026-12-01\n\n## [1.0.0]\n- x\n", "2.0.0")


def test_every_released_version_has_notes():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for version in ("0.2.0", "0.2.1", "0.3.0"):
        assert release_notes.release_notes(changelog, version)
