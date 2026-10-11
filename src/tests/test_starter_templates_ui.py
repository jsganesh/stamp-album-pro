# ruff: noqa: F811
"""Each starter template, opened from the wizard's Template Gallery, shows no "!" badge:
no caption or frame runs past the page border or into another item."""

import re

import pytest
from test_ui_smoke import base_url, page  # noqa: F401  (fixtures)

from stamp_album.templates import TEMPLATES


def _open_template(pg, name):
    pg.evaluate("document.getElementById('btn-wiz-template').click()")
    card = pg.get_by_role("button", name=re.compile("^" + re.escape(name)))
    card.wait_for()
    card.click()
    for _ in range(100):
        if pg.evaluate("StampAlbum._pages.reduce(function(n, p) { return n + p.length; }, 0)") > 0:
            return
        pg.wait_for_timeout(50)
    raise AssertionError(f"template {name!r} did not load")


@pytest.mark.parametrize("t", TEMPLATES, ids=[t["id"] for t in TEMPLATES])
def test_template_opens_without_warnings(page, t):
    _open_template(page, t["name"])
    assert page.evaluate("StampAlbum._pages.length") == 1  # each template is one page
    warnings = page.evaluate(
        "Array.from(document.querySelectorAll('#page .caption-warn')).map(function(n) {"
        " return n.getAttribute('aria-description'); })"
    )
    assert warnings == []
    assert page.js_errors == []
