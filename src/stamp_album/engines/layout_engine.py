"""
Layout engine for intelligent stamp arrangement.

Provides algorithms for auto-arranging stamps on pages,
calculating optimal spacing, and suggesting layouts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from stamp_album.core.models import (
    PageSetup,
    Row,
    RowStyle,
    Stamp,
)


@dataclass
class LayoutSuggestion:
    """A suggested layout configuration."""

    rows: list[Row]
    total_height: float
    fits_on_page: bool
    wasted_space: float


class LayoutEngine:
    """
    Calculates optimal stamp layouts for album pages.

    Provides methods for auto-arranging stamps, calculating
    row configurations, and suggesting optimal layouts.
    """

    def __init__(self, page_setup: PageSetup):
        self.page_setup = page_setup

    def calculate_content_width(self) -> float:
        """Calculate the usable width within page margins."""
        return self.page_setup.width - self.page_setup.margin_left - self.page_setup.margin_right

    def calculate_content_height(self) -> float:
        """Calculate the usable height within page margins."""
        return self.page_setup.height - self.page_setup.margin_top - self.page_setup.margin_bottom

    def auto_arrange_stamps(
        self,
        stamps: list[Stamp],
        max_width: Optional[float] = None,
        spacing: Optional[float] = None,
    ) -> LayoutSuggestion:
        """
        Automatically arrange stamps into rows.

        Args:
            stamps: List of stamps to arrange
            max_width: Maximum row width (defaults to content width)
            spacing: Horizontal spacing between stamps

        Returns:
            LayoutSuggestion with arranged rows
        """
        if max_width is None:
            max_width = self.calculate_content_width()

        if spacing is None:
            spacing = self.page_setup.hspace

        rows = []
        current_row = Row(
            style=RowStyle.FIXED_SPACE,
            spacing=spacing,
        )
        current_width = 0.0

        for stamp in stamps:
            stamp_width = stamp.width + spacing

            if current_width + stamp_width > max_width and current_row.stamps:
                # Start new row
                rows.append(current_row)
                current_row = Row(
                    style=RowStyle.FIXED_SPACE,
                    spacing=spacing,
                )
                current_width = 0.0

            current_row.stamps.append(stamp)
            current_width += stamp_width

        # Add last row if not empty
        if current_row.stamps:
            rows.append(current_row)

        # Calculate total height
        total_height = self._calculate_layout_height(rows)

        return LayoutSuggestion(
            rows=rows,
            total_height=total_height,
            fits_on_page=total_height <= self.calculate_content_height(),
            wasted_space=self.calculate_content_height() - total_height,
        )

    def optimize_spacing(
        self,
        row: Row,
        available_width: float,
    ) -> float:
        """
        Calculate optimal spacing for stamps in a row.

        Args:
            row: Row containing stamps
            available_width: Width available for the row

        Returns:
            Optimal spacing value
        """
        if not row.stamps:
            return self.page_setup.hspace

        total_stamp_width = sum(s.width for s in row.stamps)
        num_gaps = len(row.stamps) - 1

        if num_gaps <= 0:
            return self.page_setup.hspace

        optimal_spacing = (available_width - total_stamp_width) / num_gaps

        # Clamp to reasonable range
        return max(1.0, min(optimal_spacing, self.page_setup.hspace * 2))

    def calculate_row_height(self, row: Row) -> float:
        """Calculate the height needed for a row."""
        if not row.stamps:
            return 0.0

        # Row height is determined by tallest stamp
        max_height = max(s.height for s in row.stamps)

        # Add heading/footer space if present
        for stamp in row.stamps:
            if stamp.heading:
                max_height += stamp.heading.size * 0.5  # Approximate heading height

        return max_height

    def suggest_layout(
        self,
        stamps: list[Stamp],
        max_pages: int = 1,
    ) -> list[LayoutSuggestion]:
        """
        Suggest optimal layout across multiple pages.

        Args:
            stamps: List of stamps to layout
            max_pages: Maximum number of pages to use

        Returns:
            List of LayoutSuggestions, one per page
        """
        suggestions = []
        remaining_stamps = list(stamps)

        for _ in range(max_pages):
            if not remaining_stamps:
                break

            suggestion = self.auto_arrange_stamps(remaining_stamps)
            suggestions.append(suggestion)

            # Remove stamps that fit on this page
            stamps_on_page = sum(len(r.stamps) for r in suggestion.rows)
            remaining_stamps = remaining_stamps[stamps_on_page:]

        return suggestions

    def balance_rows(
        self,
        stamps: list[Stamp],
        target_rows: int,
    ) -> list[Row]:
        """
        Distribute stamps evenly across a target number of rows.

        Args:
            stamps: List of stamps
            target_rows: Desired number of rows

        Returns:
            List of balanced rows
        """
        if not stamps or target_rows <= 0:
            return []

        stamps_per_row = len(stamps) // target_rows
        remainder = len(stamps) % target_rows

        rows = []
        idx = 0

        for i in range(target_rows):
            count = stamps_per_row + (1 if i < remainder else 0)
            row = Row(
                style=RowStyle.JUSTIFIED_SPACE,
                spacing=self.page_setup.hspace,
            )
            row.stamps = stamps[idx : idx + count]
            rows.append(row)
            idx += count

        return rows

    def fit_stamps_in_grid(
        self,
        stamps: list[Stamp],
        cols: int,
    ) -> list[Row]:
        """
        Arrange stamps in a fixed-column grid.

        Args:
            stamps: List of stamps
            cols: Number of columns

        Returns:
            List of rows with stamps arranged in grid
        """
        if not stamps or cols <= 0:
            return []

        rows = []
        for i in range(0, len(stamps), cols):
            row = Row(
                style=RowStyle.FIXED_SPACE,
                spacing=self.page_setup.hspace,
            )
            row.stamps = stamps[i : i + cols]
            rows.append(row)

        return rows

    def _calculate_layout_height(self, rows: list[Row]) -> float:
        """Calculate total height of a layout."""
        height = 0.0

        for row in rows:
            height += self.calculate_row_height(row)
            height += self.page_setup.vspace  # Space between rows

        return height
