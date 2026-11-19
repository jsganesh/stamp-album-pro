"""open_page retries only the transient Windows socket error, and only a few times."""

import pytest
from browser_helpers import open_page


class FakePage:
    def __init__(self, *failures):
        self.failures = list(failures)
        self.calls = 0

    def goto(self, url):
        self.calls += 1
        if self.failures:
            raise RuntimeError(self.failures.pop(0))
        return f"loaded {url}"


BUSY = "Page.goto: net::ERR_NO_BUFFER_SPACE at http://127.0.0.1:50115/"


def test_a_page_that_loads_is_loaded_once():
    page = FakePage()
    assert open_page(page, "http://x/", pause=0) == "loaded http://x/"
    assert page.calls == 1


def test_the_transient_error_is_tried_again():
    page = FakePage(BUSY, BUSY)
    assert open_page(page, "http://x/", pause=0) == "loaded http://x/"
    assert page.calls == 3


def test_it_gives_up_after_the_attempts_and_says_why():
    page = FakePage(BUSY, BUSY, BUSY)
    with pytest.raises(RuntimeError, match="ERR_NO_BUFFER_SPACE"):
        open_page(page, "http://x/", attempts=3, pause=0)
    assert page.calls == 3


def test_any_other_error_is_raised_at_once():
    page = FakePage("Page.goto: net::ERR_CONNECTION_REFUSED", BUSY)
    with pytest.raises(RuntimeError, match="CONNECTION_REFUSED"):
        open_page(page, "http://x/", pause=0)
    assert page.calls == 1
