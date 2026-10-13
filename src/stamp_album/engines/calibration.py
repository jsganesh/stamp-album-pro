"""Print calibration page: a PDF to check that the printer prints 1 mm as 1 mm.

Printed at 100% ("Actual size") and measured with a ruler, it shows:

* rulers across and down the page, with 1 mm ticks: a printer that scales one
  direction more than the other shows up as two rulers that measure differently;
* a square of known size (100 mm, or 50 mm on paper too small for 100 mm);
* corner marks 5 mm and 10 mm in from each paper edge: a missing mark lies in the
  printer's unprintable margin;
* Penny Black-size stamps (19 x 22 mm) with the Thin, Medium and Double frames and
  captions, drawn by the same code as the PDF export (frames.py, caption_layout.py).

The page is always portrait. There is deliberately no correction factor: a page that
measures wrong means a scaling setting in the print dialog, and the fix belongs there.

``layout()`` works out where everything goes (mm, top-left origin, y down) so it can be
tested without reading a PDF; ``generate_pdf()`` draws it with ReportLab.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from stamp_album.core.models import PageSize, Stamp, StampHeading

# Paper sizes offered, as in the editor's Page setup (key -> label, width, height in mm).
PAPERS: dict[str, tuple[str, float, float]] = {
    "a4": ("A4", *PageSize.A4.value),
    "a5": ("A5", *PageSize.A5.value),
    "a3": ("A3", *PageSize.A3.value),
    "letter": ("Letter", *PageSize.LETTER.value),
    "legal": ("Legal", *PageSize.LEGAL.value),
}

MARGIN_MM = 15.0
CORNER_INSETS_MM = (5.0, 10.0)
CORNER_ARM_MM = 6.0
SAMPLE_W_MM, SAMPLE_H_MM = 19.0, 22.0  # the Penny Black, as in the first-run sample
SAMPLE_FRAMES = (("thin", "Thin 0.5 pt"), ("medium", "Medium 1 pt"), ("double", "Double"))
TICK_MM = {"minor": 2.0, "half": 3.5, "major": 5.0}  # tick lengths: 1 mm, 5 mm, 10 mm marks
LABEL_GAP_MM = 1.2  # between a 10 mm tick and its number
RULER_LABEL_ROOM_MM = 12.0  # left of the down ruler, for its numbers

BODY_FONT, BODY_PT = "Helvetica", 9.0
SMALL_PT = 7.0
TITLE_FONT, TITLE_PT = "Helvetica-Bold", 14.0
LINE_MM = BODY_PT * 1.35 * 25.4 / 72  # body line spacing

INSTRUCTIONS = (
    "Print this page at 100% scale (“Actual size”), not “Fit to page” or "
    "“Shrink to fit”, then measure it with a good ruler. If a ruler or the square "
    "measures wrong, change the scaling in the print dialog: StampAlbum Pro does not rescale "
    "pages. Corner marks are 5\u00a0mm and 10\u00a0mm from the paper's edges; "
    "a missing mark lies in your printer's unprintable margin."
)


@dataclass(frozen=True)
class Ruler:
    x: float  # start of the ruler line
    y: float
    length: float  # mm, a whole number of centimetres
    vertical: bool


@dataclass(frozen=True)
class Sample:
    frame: str  # "thin", "medium" or "double"
    label: str
    x: float  # the stamp's own box; its frame is drawn outside it
    y: float
    w: float = SAMPLE_W_MM
    h: float = SAMPLE_H_MM


@dataclass
class Layout:
    paper: str
    label: str
    width: float
    height: float
    title_y: float  # baselines, mm from the top
    instruction_lines: list[str]
    instructions_y: float  # baseline of the first instruction line
    across: Ruler
    down: Ruler
    square_x: float
    square_y: float
    square_size: float
    samples: list[Sample] = field(default_factory=list)
    footer_y: float = 0.0

    @property
    def paper_label(self) -> str:
        return f"{self.label} ({_mm(self.width)} × {_mm(self.height)} mm)"


def _mm(v: float) -> str:
    return f"{v:g}"


def _whole_cm(v: float) -> float:
    return float(int(v // 10) * 10)


def ticks(length: float) -> list[tuple[float, str]]:
    """Tick positions along a ruler (mm from its start) and their kind: minor, half, major."""
    out = []
    for i in range(int(round(length)) + 1):
        out.append((float(i), "major" if i % 10 == 0 else "half" if i % 5 == 0 else "minor"))
    return out


def corner_marks(width: float, height: float) -> list[tuple[tuple[float, float], tuple, tuple]]:
    """Each corner mark as (vertex, end of one arm, end of the other), mm."""
    out = []
    for d in CORNER_INSETS_MM:
        for cx, sx in ((d, 1), (width - d, -1)):
            for cy, sy in ((d, 1), (height - d, -1)):
                out.append(((cx, cy), (cx + sx * CORNER_ARM_MM, cy), (cx, cy + sy * CORNER_ARM_MM)))
    return out


def layout(paper: str) -> Layout:
    """Where everything goes on the calibration page for *paper* (a key of PAPERS)."""
    if paper not in PAPERS:
        raise ValueError(f"Unknown paper size: {paper!r}")
    label, width, height = PAPERS[paper]
    m = MARGIN_MM
    to_mm = 72 / 25.4

    title_y = 21.0
    lines = simpleSplit(INSTRUCTIONS, BODY_FONT, BODY_PT, (width - 2 * m) * to_mm)
    instructions_y = title_y + 7.0
    instructions_end = instructions_y + (len(lines) - 1) * LINE_MM

    # Ruler across: ticks rise from the line, numbers above them.
    across_y = instructions_end + 14.0
    across = Ruler(m, across_y, _whole_cm(width - 2 * m), vertical=False)

    # Ruler down, at the right margin: ticks point left, numbers left of them.
    down_y = across_y + 10.0
    footer_y = height - 13.0
    down = Ruler(width - m, down_y, _whole_cm(footer_y - 8.0 - down_y), vertical=True)

    # The square, then the frame samples below it; 100 mm if it all fits, else 50 mm.
    square_y = down_y + 4.0
    samples_room = 14.0 + SAMPLE_H_MM + 16.0  # heading above, box, captions below
    square = 100.0 if square_y + 100.0 + samples_room <= footer_y - 6.0 else 50.0

    sample_y = square_y + square + 14.0
    usable = (down.x - RULER_LABEL_ROOM_MM) - m
    step = min(40.0, usable / len(SAMPLE_FRAMES))
    samples = [
        Sample(frame, text, m + 2.0 + i * step, sample_y)
        for i, (frame, text) in enumerate(SAMPLE_FRAMES)
    ]

    return Layout(
        paper=paper, label=label, width=width, height=height,
        title_y=title_y, instruction_lines=lines, instructions_y=instructions_y,
        across=across, down=down,
        square_x=m, square_y=square_y, square_size=square,
        samples=samples, footer_y=footer_y,
    )


def sample_stamp(sample: Sample) -> Stamp:
    """The frame sample as a stamp, so it is drawn exactly as an exported stamp is."""
    return Stamp(
        width=sample.w,
        height=sample.h,
        description="1d black",
        footer_text=f"{_mm(sample.w)} × {_mm(sample.h)} mm",
        heading=StampHeading(text=sample.label),
        frame=sample.frame,
        abs_x=sample.x,
        abs_y=sample.y,
    )


# ── Drawing ──

def _pt(v: float) -> float:
    return v * 72 / 25.4


def _draw_ruler(c: canvas.Canvas, r: Ruler, page_h: float) -> None:
    y = lambda v: page_h - _pt(v)  # noqa: E731  (mm from the top -> PDF points)
    c.setLineWidth(_pt(0.15))
    if r.vertical:
        c.line(_pt(r.x), y(r.y), _pt(r.x), y(r.y + r.length))
    else:
        c.line(_pt(r.x), y(r.y), _pt(r.x + r.length), y(r.y))
    c.setFont(BODY_FONT, SMALL_PT)
    for pos, kind in ticks(r.length):
        t = TICK_MM[kind]
        if r.vertical:
            c.line(_pt(r.x), y(r.y + pos), _pt(r.x - t), y(r.y + pos))
            if kind == "major":
                c.drawRightString(_pt(r.x - t - LABEL_GAP_MM), y(r.y + pos) - SMALL_PT * 0.35,
                                  _mm(pos))
        else:
            c.line(_pt(r.x + pos), y(r.y), _pt(r.x + pos), y(r.y - t))
            if kind == "major":
                c.drawCentredString(_pt(r.x + pos), y(r.y - t - LABEL_GAP_MM), _mm(pos))


def generate_pdf(paper: str, version: str = "", today: Optional[date] = None) -> bytes:
    """The calibration page for *paper* as PDF bytes."""
    from stamp_album.engines.pdf import _draw_captions, _draw_stamp_shape

    lay = layout(paper)
    today = today or date.today()
    page_w, page_h = _pt(lay.width), _pt(lay.height)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))
    c.setTitle(f"StampAlbum Pro calibration page, {lay.label}")
    c.setAuthor("StampAlbum Pro")
    y = lambda v: page_h - _pt(v)  # noqa: E731
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)

    c.setFont(TITLE_FONT, TITLE_PT)
    c.drawCentredString(page_w / 2, y(lay.title_y), f"Print calibration page · {lay.paper_label}")
    c.setFont(BODY_FONT, BODY_PT)
    for i, line in enumerate(lay.instruction_lines):
        c.drawString(_pt(MARGIN_MM), y(lay.instructions_y + i * LINE_MM), line)

    _draw_ruler(c, lay.across, page_h)
    _draw_ruler(c, lay.down, page_h)
    c.setFont(BODY_FONT, SMALL_PT)
    c.drawString(_pt(lay.across.x), y(lay.across.y + 4.0),
                 f"Across: {_mm(lay.across.length)} mm from 0 to {_mm(lay.across.length)}.  "
                 f"Down (right): {_mm(lay.down.length)} mm.")

    # The square, with its size inside it.
    s = lay.square_size
    c.setLineWidth(_pt(0.2))
    c.rect(_pt(lay.square_x), y(lay.square_y + s), _pt(s), _pt(s), fill=0, stroke=1)
    c.setFont(TITLE_FONT, 12)
    cx = _pt(lay.square_x + s / 2)
    c.drawCentredString(cx, y(lay.square_y + s / 2 - 1.0), f"{_mm(s)} mm square")
    c.setFont(BODY_FONT, BODY_PT if s >= 100 else SMALL_PT)
    c.drawCentredString(cx, y(lay.square_y + s / 2 + 4.0),
                        f"Each side should measure {_mm(s)} mm")

    # Corner marks, 5 mm and 10 mm in from each edge.
    c.setLineWidth(_pt(0.2))
    for (vx, vy), (ax, ay), (bx, by) in corner_marks(lay.width, lay.height):
        c.line(_pt(vx), y(vy), _pt(ax), y(ay))
        c.line(_pt(vx), y(vy), _pt(bx), y(by))
    c.setFont(BODY_FONT, 5.5)
    for d in CORNER_INSETS_MM:
        c.drawString(_pt(d + 1.0), y(d + 3.0), _mm(d))

    # Frame samples, drawn and captioned by the export code.
    for sample in lay.samples:
        st = sample_stamp(sample)
        _draw_stamp_shape(c, st, sample.x, sample.y, sample.w, sample.h, page_h,
                          (0, 0, 0), (1, 1, 1))
        _draw_captions(c, st, sample.x, sample.y, page_h)
    c.setFillColorRGB(0, 0, 0)

    c.setFont(BODY_FONT, SMALL_PT)
    footer = " · ".join(
        p for p in (
            f"StampAlbum Pro {version}".strip(), "Calibration page", lay.paper_label,
            f"{today.day} {today:%B %Y}",
        ) if p
    )
    c.drawCentredString(page_w / 2, y(lay.footer_y), footer)

    c.showPage()
    c.save()
    return buf.getvalue()
