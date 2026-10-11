"""Report test failures as GitHub Actions annotations.

Job logs can't be downloaded from a cloud session, but a check run's
annotations can be read through the API. The runner turns a line printed as
``::error file=…,line=…,title=…::message`` into an annotation, so this plugin
prints one per failed test, error or collection error at the end of the run.

It does nothing unless ``GITHUB_ACTIONS`` is ``true``, so local runs are
unchanged. GitHub shows at most 10 error annotations per step: up to 9 are
written in full and the 10th lists the rest.

Read them back with:
    gh api repos/OWNER/REPO/commits/SHA/check-runs --jq '.check_runs[] | "\\(.id) \\(.name)"'
    gh api repos/OWNER/REPO/check-runs/ID/annotations
"""

import os
from pathlib import Path

MAX_ANNOTATIONS = 10  # GitHub's limit per step
MAX_MESSAGE = 4000

_failures = []


def _escape_data(s):
    return s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(s):
    return _escape_data(s).replace(":", "%3A").replace(",", "%2C")


def _relative(path, root):
    """*path* relative to the repo root with forward slashes, or None if outside it."""
    try:
        p = Path(path)
        if not p.is_absolute():
            p = Path(root) / p
        return p.resolve().relative_to(Path(root).resolve()).as_posix()
    except (ValueError, OSError):
        return None


def _location(report, root):
    """File and line to annotate: where it crashed if that's in the repo, else the test."""
    crash = getattr(getattr(report, "longrepr", None), "reprcrash", None)
    if crash is not None and getattr(crash, "path", None):
        rel = _relative(crash.path, root)
        if rel and "site-packages" not in rel and ".venv" not in rel.split("/"):
            return rel, crash.lineno
    loc = getattr(report, "location", None)
    if loc:
        rel = _relative(loc[0], root) or loc[0].replace("\\", "/")
        return rel, (loc[1] or 0) + 1
    return (_relative(report.fspath, root) or str(report.fspath).replace("\\", "/")), 1


def _message(report):
    """The `E` lines pytest shows, else the end of the traceback."""
    text = str(getattr(report, "longrepr", "") or "")
    lines = text.splitlines()
    e_lines = [ln for ln in lines if ln.startswith("E ")]
    body = "\n".join(e_lines) if e_lines else "\n".join(lines[-30:])
    return body or "(no details)"


def _truncate(s):
    return s if len(s) <= MAX_MESSAGE else s[: MAX_MESSAGE - 20] + "\n… (truncated)"


def _record(report, kind, root):
    path, line = _location(report, root)
    _failures.append(
        {
            "nodeid": report.nodeid or path,
            "kind": kind,
            "file": path,
            "line": line,
            "message": _message(report),
        }
    )


def _command(file, line, title, message):
    props = f"file={_escape_property(file)},line={line},title={_escape_property(title)}"
    return f"::error {props}::{_escape_data(_truncate(message))}"


def build_commands(failures):
    """The ::error lines for *failures*, keeping within GitHub's per-step limit."""
    shown = failures if len(failures) <= MAX_ANNOTATIONS else failures[: MAX_ANNOTATIONS - 1]
    out = [
        _command(f["file"], f["line"], f"pytest: {f['nodeid']} {f['kind']}", f["message"])
        for f in shown
    ]
    rest = failures[len(shown):]
    if rest:
        names = "\n".join(f"{f['nodeid']} ({f['kind']})" for f in rest)
        out.append(
            _command(rest[0]["file"], rest[0]["line"], f"pytest: {len(rest)} more failures", names)
        )
    return out


def _active():
    return os.environ.get("GITHUB_ACTIONS") == "true"


def pytest_runtest_logreport(report):
    if not _active() or not report.failed:
        return
    kind = "failed" if report.when == "call" else f"error in {report.when}"
    _record(report, kind, os.environ.get("GITHUB_WORKSPACE") or os.getcwd())


def pytest_collectreport(report):
    if _active() and report.failed:
        _record(report, "collection error", os.environ.get("GITHUB_WORKSPACE") or os.getcwd())


def pytest_terminal_summary(terminalreporter):
    if not _active() or not _failures:
        return
    terminalreporter.write_line("")
    for cmd in build_commands(_failures):
        terminalreporter.write_line(cmd)
