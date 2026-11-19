"""Helpers for the browser tests."""

import time

# Windows now and then runs out of socket buffers when hundreds of short-lived browsers have
# each opened connections to the test server; the buffers come back within seconds.
TRANSIENT = "ERR_NO_BUFFER_SPACE"


def open_page(pg, url, attempts=4, pause=1.0):
    """pg.goto(url), tried again when the machine is briefly out of socket buffers.

    Any other error, and the last failure, is raised as it is.
    """
    for attempt in range(attempts):
        try:
            return pg.goto(url)
        except Exception as exc:  # playwright's Error, matched by message to keep it optional
            if TRANSIENT not in str(exc) or attempt == attempts - 1:
                raise
            time.sleep(pause * (attempt + 1))
