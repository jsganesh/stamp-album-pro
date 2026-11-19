"""The "buy me a coffee" link is the same everywhere it appears, and only ever a link.

It is a hosted PayPal payment page: no account details or keys are involved, and the app
itself never mentions it, so nothing in the editor asks for money.
"""

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("release_notes", ROOT / "tools" / "release_notes.py")
release_notes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(release_notes)

URL = release_notes.SUPPORT_URL


def test_it_is_a_paypal_payment_page():
    assert re.fullmatch(r"https://www\.paypal\.com/ncp/payment/[A-Z0-9]+", URL)


def test_readme_and_sponsor_button_use_it():
    assert URL in (ROOT / "README.md").read_text(encoding="utf-8")
    assert URL in (ROOT / ".github" / "FUNDING.yml").read_text(encoding="utf-8")


def test_every_release_note_carries_it():
    changelog = "# Changelog\n\n## [1.0.0] - 2026-01-01\n\n### Added\n- A thing\n"
    assert URL in release_notes.release_notes(changelog, "v1.0.0")


def test_the_editor_does_not_ask_for_money():
    web = ROOT / "src" / "stamp_album" / "web"
    for path in web.glob("*"):
        if path.suffix in {".js", ".html"}:
            assert "paypal" not in path.read_text(encoding="utf-8").lower(), path.name
