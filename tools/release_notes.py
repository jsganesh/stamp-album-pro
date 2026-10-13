"""Print the GitHub release notes for one version, taken from CHANGELOG.md.

    python3 tools/release_notes.py 0.3.0      (or v0.3.0)

Used by the App build workflow when a v* tag is pushed. The notes are a short
Downloads section followed by that version's section of the changelog. Exits
with an error if the changelog has no section for the version, so a release
can't go out with empty notes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/jsganesh/stamp-album-pro"

DOWNLOADS = """### Downloads
- `StampAlbumPro-macos.zip`: the macOS app (Apple silicon). Unzip and open; the first time, \
right-click › Open, as the app is not signed yet.
- `StampAlbumPro-windows.zip`: the Windows folder. Unzip and run `StampAlbumPro.exe`; the \
first time, More info › Run anyway, as the app is not signed yet.
"""


def github_anchor(heading: str) -> str:
    """GitHub's link anchor for a Markdown heading ("[0.3.0] - 2026-10-14" → "030---2026-10-14")."""
    text = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return text.replace(" ", "-")


def changelog_section(changelog: str, version: str) -> tuple[str, str]:
    """The `## [version]` section's heading text and body."""
    heading = re.compile(rf"^## \[{re.escape(version)}\][^\n]*\n", re.MULTILINE)
    m = heading.search(changelog)
    if not m:
        raise LookupError(f"CHANGELOG.md has no section for {version}")
    nxt = re.compile(r"^## \[", re.MULTILINE).search(changelog, m.end())
    body = changelog[m.end(): nxt.start() if nxt else len(changelog)].strip()
    if not body:
        raise LookupError(f"CHANGELOG.md's section for {version} is empty")
    return m.group(0)[3:], body


def release_notes(changelog: str, version: str) -> str:
    version = version.removeprefix("v")
    heading, body = changelog_section(changelog, version)
    anchor = github_anchor(heading)
    link = f"{REPO_URL}/blob/v{version}/CHANGELOG.md#{anchor}"
    return f"{DOWNLOADS}\n{body}\n\n[Changelog for {version}]({link})\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    try:
        print(release_notes(changelog, argv[1]), end="")
    except LookupError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
