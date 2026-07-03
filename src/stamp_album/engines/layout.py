"""
Shared row-layout computation for stamp album pages.

Computes (x, y, stamp) positions for row-based stamps so that all
renderers (HTML, PDF, PNG, SVG) produce identical layouts from one
canonical function.
"""

from __future__ import annotations

from stamp_album.core.models import Album


def layout_rows(
    album: Album,
    start_y: float = 20.0,
    row_padding: float = 3.0,
) -> list[list[tuple[float, float, "Stamp"]]]:
    """Compute (x_mm, y_mm, stamp) for every row-based stamp.

    Returns a list aligned with *album.pages*, where each element is a
    list of ``(x_mm, y_mm, stamp)`` tuples for the row stamps on that
    page.

    Layout rules (matches / improves upon HTMLRenderer):
      * The first row begins at *start_y* mm from the top of the page.
      * Within a row stamps flow left-to-right (x = 0, then previous
        width + ``row.spacing``).
      * After each row, y advances by the tallest stamp in that row
        plus *row_padding* mm — this fixes the previous hard-coded
        30 mm increment that caused collisions with tall stamps.
    """
    result: list[list[tuple[float, float, "Stamp"]]] = []
    for page in album.pages:
        items: list[tuple[float, float, "Stamp"]] = []
        y = start_y
        for row in page.rows:
            x = 0.0
            max_h = 0.0
            for stamp in row.stamps:
                items.append((x, y, stamp))
                x += stamp.width + row.spacing
                if stamp.height > max_h:
                    max_h = stamp.height
            y += max_h + row_padding
        result.append(items)
    return result
