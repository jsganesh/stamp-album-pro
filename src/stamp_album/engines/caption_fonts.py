"""The bundled caption font: Source Serif 4, Caption optical size (SIL OFL).

Every view measures and draws stamp captions with these four files (in
``web/fonts``), so a caption wraps the same way in the editor, the preview and
the PDF, PNG and SVG exports.

Widths are the fonts' own advance widths (``hmtx`` through ``cmap``), with no
kerning and no ligatures. ReportLab draws exactly that; the editor and the
preview switch kerning and ligatures off to match. The editor measures with the
same table, written to ``web/caption_metrics.js`` by ``tools/caption_metrics.py``
(a test checks the two agree).

Caption font ids:

* ``CapR``: Regular (description)
* ``CapI``: Italic (details and catalogue)
* ``CapB``: Bold (heading, the default)
* ``CapSB``: Semibold (heading, when the album chooses it)

Keep in step with ``CAPTION_FONTS`` in ``web/dsl_core.js``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent.parent / "web" / "fonts"
FAMILY = "Source Serif 4 Caption"

# id -> (file, CSS weight, CSS style)
FONTS: dict[str, tuple[str, int, str]] = {
    "CapR": ("SourceSerif4Caption-Regular.ttf", 400, "normal"),
    "CapI": ("SourceSerif4Caption-It.ttf", 400, "italic"),
    "CapB": ("SourceSerif4Caption-Bold.ttf", 700, "normal"),
    "CapSB": ("SourceSerif4Caption-Semibold.ttf", 600, "normal"),
}

# The album's choice of heading weight (CAPTION_HEADING in the DSL).
HEADING_WEIGHTS = {"bold": "CapB", "semibold": "CapSB"}
DEFAULT_HEADING_WEIGHT = "bold"

MM_PER_PT = 25.4 / 72.0


def heading_font(weight: str | None) -> str:
    """The caption font id for an album's heading weight."""
    return HEADING_WEIGHTS.get((weight or "").lower(), HEADING_WEIGHTS[DEFAULT_HEADING_WEIGHT])


# The files the app serves at /fonts/<name>, by name (nothing else under web/ is reachable there).
SERVED: dict[str, Path] = {f: FONT_DIR / f for f, _, _ in FONTS.values()}


def path(font_id: str) -> Path:
    return FONT_DIR / FONTS[font_id][0]


def weight(font_id: str) -> int:
    return FONTS[font_id][1]


def style(font_id: str) -> str:
    return FONTS[font_id][2]


def reportlab_name(font_id: str) -> str:
    """The font's name in ReportLab, registered on first use."""
    _register_reportlab()
    return "SourceSerif4Caption-" + font_id


@lru_cache(maxsize=1)
def _register_reportlab() -> None:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for fid in FONTS:
        pdfmetrics.registerFont(TTFont("SourceSerif4Caption-" + fid, str(path(fid))))


@lru_cache(maxsize=None)
def metrics(font_id: str) -> tuple[int, dict[int, int], int]:
    """(units per em, {code point: advance}, .notdef advance) for one font."""
    from fontTools.ttLib import TTFont

    with TTFont(str(path(font_id)), lazy=True) as tt:
        upm = tt["head"].unitsPerEm
        hmtx = tt["hmtx"].metrics
        cmap = tt.getBestCmap()
        adv = {cp: hmtx[name][0] for cp, name in cmap.items()}
        notdef = hmtx[".notdef"][0]
    return upm, adv, notdef


def measure(text: str, font_id: str, size_pt: float) -> float:
    """Width of *text* in mm: the sum of the glyphs' advance widths.

    A character the font lacks counts as the font's .notdef glyph, in the editor too.
    """
    upm, adv, notdef = metrics(font_id)
    units = sum(adv.get(ord(ch), notdef) for ch in text)
    return units * size_pt / upm * MM_PER_PT


def pillow_font(font_id: str, size_px: float):
    """A Pillow font for drawing (basic layout: no kerning or ligatures, as measured)."""
    return _pillow_font(font_id, round(size_px, 3))


@lru_cache(maxsize=64)
def _pillow_font(font_id: str, size_px: float):
    from PIL import ImageFont

    return ImageFont.truetype(str(path(font_id)), size_px, layout_engine=ImageFont.Layout.BASIC)


def css_font_faces(url_prefix: str = "/fonts/") -> str:
    """@font-face rules for the four files, served by the app at *url_prefix*."""
    return "".join(
        f"@font-face{{font-family:'{FAMILY}';src:url('{url_prefix}{f}') format('truetype');"
        f"font-weight:{w};font-style:{s};font-display:block;}}"
        for f, w, s in FONTS.values()
    )


# Kerning and ligatures off, so drawn text is as wide as measured; geometricPrecision stops
# Chrome on Linux rounding each glyph's advance to whole pixels at small sizes.
CSS_TEXT_RULES = (
    "font-kerning:none;font-variant-ligatures:none;font-feature-settings:'kern' 0,'liga' 0;"
    "text-rendering:geometricPrecision;"
)


def css_family() -> str:
    return f"'{FAMILY}',Georgia,serif"


def subset_font_faces(used: dict[str, set[str]]) -> str:
    """@font-face rules embedding only the glyphs used, one subset per font (SVG, HTML).

    *used* maps caption font ids to the characters set in them. The subsets drop
    kerning and ligatures, so the text draws at the measured width anywhere.
    """
    # A fixed order, so the same album gives the same file
    return "".join(_subset_face(fid, "".join(sorted(used[fid]))) for fid in FONTS if used.get(fid))


@lru_cache(maxsize=32)  # the preview refreshes often with the same captions
def _subset_face(font_id: str, chars: str) -> str:
    import base64
    import io

    from fontTools import subset
    from fontTools.ttLib import TTFont

    opts = subset.Options()
    opts.layout_features = []  # no kerning, no ligatures...
    opts.drop_tables += ["GPOS", "GSUB", "GDEF", "BASE"]  # ...and no layout tables at all
    opts.hinting = False
    opts.notdef_outline = True
    opts.name_IDs = ["*"]  # keep the font's names and its OFL notice
    opts.name_languages = ["*"]
    # recalcTimestamp=False keeps the font's own date, so the same album gives the same file
    with TTFont(str(path(font_id)), recalcTimestamp=False) as tt:
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=[ord(c) for c in chars])
        sub.subset(tt)
        buf = io.BytesIO()
        tt.save(buf)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    _, w, s = FONTS[font_id]
    return (
        f"@font-face{{font-family:'{FAMILY}';"
        f"src:url(data:font/ttf;base64,{data}) format('truetype');"
        f"font-weight:{w};font-style:{s};}}"
    )
