"""The editor's paper table must match real paper sizes (millimetres x px-per-mm)."""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "stamp_album" / "web"
PAPER_MM = {"a4": (210, 297), "a5": (148, 210), "a3": (297, 420),
            "letter": (215.9, 279.4), "legal": (215.9, 355.6)}
NAMES = "a4|a5|a3|letter|legal"


def _scale():
    m = re.search(r"_sc\s*=\s*([\d.]+)", (WEB / "app.js").read_text(encoding="utf-8"))
    assert m, "px-per-mm scale not found in app.js"
    return float(m.group(1))


def _check(table):
    assert set(table) == set(PAPER_MM), sorted(table)
    for name, (w, h) in table.items():
        ew, eh = PAPER_MM[name]
        assert abs(w / _scale() - ew) < 0.2 and abs(h / _scale() - eh) < 0.2, (name, w, h)


def _js_table(filename):
    text = (WEB / filename).read_text(encoding="utf-8")
    pat = r"\b(%s)\s*:\s*\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]" % NAMES
    return {m.group(1): (float(m.group(2)), float(m.group(3))) for m in re.finditer(pat, text)}




def test_init_js_paper_table():
    _check(_js_table("init.js"))


def test_css_page_sizes():
    text = (WEB / "style.css").read_text(encoding="utf-8")
    pat = r"\.page\.(%s)\s*\{\s*width:\s*([\d.]+)px;\s*height:\s*([\d.]+)px;" % NAMES
    _check({m.group(1): (float(m.group(2)), float(m.group(3))) for m in re.finditer(pat, text)})


def test_default_page_is_a4():
    m = re.search(r"_pw\s*=\s*([\d.]+),\s*_ph\s*=\s*([\d.]+)", (WEB / "app.js").read_text(encoding="utf-8"))
    assert m, "default page size not found in app.js"
    assert abs(float(m.group(1)) / _scale() - 210) < 0.2
    assert abs(float(m.group(2)) / _scale() - 297) < 0.2
