"""
Layout engine for intelligent stamp arrangement.

Provides algorithms for auto-arranging stamps on pages,
calculating optimal spacing, suggesting layouts, and
constraint-based layout solving.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from stamp_album.core.models import (
    PageSetup,
    Row,
    RowStyle,
    Stamp,
)


class LayoutStrategy(Enum):
    """Layout strategy for auto-arrangement."""

    ROW_FIRST = "row_first"  # Fill rows left-to-right
    COLUMN_FIRST = "column_first"  # Fill columns top-to-bottom
    GRID = "grid"  # Fixed grid layout
    PACKING = "packing"  # Bin-packing for mixed sizes
    BALANCED = "balanced"  # Balance rows by width


@dataclass
class LayoutConstraint:
    """A constraint for layout solving."""

    max_width: Optional[float] = None
    max_height: Optional[float] = None
    min_stamps_per_row: int = 1
    max_stamps_per_row: int = 10
    fixed_rows: Optional[int] = None
    fixed_cols: Optional[int] = None
    uniform_spacing: bool = True
    align_to_grid: bool = False
    grid_size: float = 1.0  # mm


@dataclass
class LayoutSuggestion:
    """A suggested layout configuration."""

    rows: list[Row]
    total_height: float
    fits_on_page: bool
    wasted_space: float
    strategy: LayoutStrategy = LayoutStrategy.ROW_FIRST
    score: float = 0.0  # Higher is better


@dataclass
class PlacementRect:
    """A rectangular placement on the page."""

    x: float
    y: float
    width: float
    height: float


class LayoutEngine:
    """
    Calculates optimal stamp layouts for album pages.

    Provides methods for auto-arranging stamps, calculating
    row configurations, constraint-based layout solving,
    and collision detection.
    """

    def __init__(self, page_setup: PageSetup):
        self.page_setup = page_setup
        self._placed_rects: list[PlacementRect] = []

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
        strategy: LayoutStrategy = LayoutStrategy.ROW_FIRST,
    ) -> LayoutSuggestion:
        """
        Automatically arrange stamps into rows using specified strategy.

        Args:
            stamps: List of stamps to arrange
            max_width: Maximum row width (defaults to content width)
            spacing: Horizontal spacing between stamps
            strategy: Layout strategy to use

        Returns:
            LayoutSuggestion with arranged rows
        """
        if max_width is None:
            max_width = self.calculate_content_width()
        if spacing is None:
            spacing = self.page_setup.hspace

        strategy_map = {
            LayoutStrategy.ROW_FIRST: self._arrange_row_first,
            LayoutStrategy.COLUMN_FIRST: self._arrange_column_first,
            LayoutStrategy.GRID: self._arrange_grid,
            LayoutStrategy.PACKING: self._arrange_packing,
            LayoutStrategy.BALANCED: self._arrange_balanced,
        }

        arrange_fn = strategy_map.get(strategy, self._arrange_row_first)
        rows = arrange_fn(stamps, max_width, spacing)

        total_height = self._calculate_layout_height(rows)
        content_height = self.calculate_content_height()

        # Score: higher is better (less wasted space, fits on page)
        score = self._score_layout(rows, total_height, content_height)

        return LayoutSuggestion(
            rows=rows,
            total_height=total_height,
            fits_on_page=total_height <= content_height,
            wasted_space=max(0, content_height - total_height),
            strategy=strategy,
            score=score,
        )

    def solve_with_constraints(
        self,
        stamps: list[Stamp],
        constraints: LayoutConstraint,
    ) -> LayoutSuggestion:
        """
        Solve layout with explicit constraints.

        Args:
            stamps: List of stamps to arrange
            constraints: Layout constraints to satisfy

        Returns:
            Best LayoutSuggestion that satisfies constraints
        """
        max_width = constraints.max_width or self.calculate_content_width()
        max_height = constraints.max_height or self.calculate_content_height()
        spacing = self.page_setup.hspace if constraints.uniform_spacing else 0

        best_suggestion = None
        best_score = -1

        # Try different strategies
        for strategy in LayoutStrategy:
            suggestion = self.auto_arrange_stamps(stamps, max_width, spacing, strategy)

            # Check constraints
            if constraints.fixed_rows and len(suggestion.rows) != constraints.fixed_rows:
                continue
            if constraints.fixed_cols:
                if any(len(r.stamps) > constraints.fixed_cols for r in suggestion.rows):
                    continue
            if suggestion.total_height > max_height:
                continue

            if suggestion.score > best_score:
                best_score = suggestion.score
                best_suggestion = suggestion

        # Fallback to row-first if no strategy satisfies constraints
        if best_suggestion is None:
            best_suggestion = self.auto_arrange_stamps(stamps, max_width, spacing)

        return best_suggestion

    def detect_collisions(self, placements: list[PlacementRect]) -> list[tuple[int, int]]:
        """
        Detect overlapping placements.

        Args:
            placements: List of placement rectangles

        Returns:
            List of (index1, index2) pairs that collide
        """
        collisions = []
        for i in range(len(placements)):
            for j in range(i + 1, len(placements)):
                if self._rects_overlap(placements[i], placements[j]):
                    collisions.append((i, j))
        return collisions

    def check_placement_valid(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        margin: float = 0.0,
    ) -> bool:
        """
        Check if a placement at (x, y) is valid (no collisions).

        Args:
            x, y: Position
            width, height: Size
            margin: Additional margin around placement

        Returns:
            True if placement is valid
        """
        new_rect = PlacementRect(x - margin, y - margin, width + 2 * margin, height + 2 * margin)
        for rect in self._placed_rects:
            if self._rects_overlap(new_rect, rect):
                return False
        return True

    def place_element(self, x: float, y: float, width: float, height: float) -> None:
        """Record a placement on the page."""
        self._placed_rects.append(PlacementRect(x, y, width, height))

    def clear_placements(self) -> None:
        """Clear all recorded placements."""
        self._placed_rects.clear()

    def find_next_position(
        self,
        width: float,
        height: float,
        start_y: float = 0.0,
        margin: float = 0.0,
    ) -> Optional[tuple[float, float]]:
        """
        Find the next valid position for an element.

        Scans from top-left, finding first position that doesn't collide.

        Args:
            width, height: Element size
            start_y: Starting Y position to scan from
            margin: Required margin around element

        Returns:
            (x, y) tuple or None if no valid position found
        """
        content_width = self.calculate_content_width()
        content_height = self.calculate_content_height()

        # Try positions in a grid pattern
        step = max(1.0, margin)
        x = 0.0
        y = start_y

        while y + height <= content_height:
            while x + width <= content_width:
                if self.check_placement_valid(x, y, width, height, margin):
                    return (x, y)
                x += step
            x = 0.0
            y += step

        return None

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
        strategy: LayoutStrategy = LayoutStrategy.ROW_FIRST,
    ) -> list[LayoutSuggestion]:
        """
        Suggest optimal layout across multiple pages.

        Args:
            stamps: List of stamps to layout
            max_pages: Maximum number of pages to use
            strategy: Layout strategy

        Returns:
            List of LayoutSuggestions, one per page
        """
        suggestions = []
        remaining_stamps = list(stamps)

        for _ in range(max_pages):
            if not remaining_stamps:
                break

            suggestion = self.auto_arrange_stamps(remaining_stamps, strategy=strategy)
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

    # ------------------------------------------------------------------
    # Private: Strategy implementations
    # ------------------------------------------------------------------

    def _arrange_row_first(
        self, stamps: list[Stamp], max_width: float, spacing: float
    ) -> list[Row]:
        """Fill rows left-to-right, wrapping when width exceeded."""
        rows = []
        current_row = Row(style=RowStyle.FIXED_SPACE, spacing=spacing)
        current_width = 0.0

        for stamp in stamps:
            stamp_width = stamp.width + spacing
            if current_width + stamp_width > max_width and current_row.stamps:
                rows.append(current_row)
                current_row = Row(style=RowStyle.FIXED_SPACE, spacing=spacing)
                current_width = 0.0
            current_row.stamps.append(stamp)
            current_width += stamp_width

        if current_row.stamps:
            rows.append(current_row)

        return rows

    def _arrange_column_first(
        self, stamps: list[Stamp], max_width: float, spacing: float
    ) -> list[Row]:
        """Fill columns top-to-bottom, then wrap to next column."""
        content_height = self.calculate_content_height()
        columns: list[list[Stamp]] = [[]]
        col_heights = [0.0]

        for stamp in stamps:
            stamp_height = stamp.height + self.page_setup.vspace
            if col_heights[-1] + stamp_height > content_height and columns[-1]:
                columns.append([])
                col_heights.append(0.0)
            columns[-1].append(stamp)
            col_heights[-1] += stamp_height

        # Convert columns to rows (each column becomes a row)
        rows = []
        for col_stamps in columns:
            row = Row(style=RowStyle.FIXED_SPACE, spacing=spacing)
            row.stamps = col_stamps
            rows.append(row)

        return rows

    def _arrange_grid(self, stamps: list[Stamp], max_width: float, spacing: float) -> list[Row]:
        """Arrange in a uniform grid based on average stamp size."""
        if not stamps:
            return []

        avg_width = sum(s.width for s in stamps) / len(stamps)
        cols = max(1, int(max_width / (avg_width + spacing)))
        return self.fit_stamps_in_grid(stamps, cols)

    def _arrange_packing(self, stamps: list[Stamp], max_width: float, spacing: float) -> list[Row]:
        """Bin-packing approach: sort by height, pack tallest first."""
        sorted_stamps = sorted(stamps, key=lambda s: s.height, reverse=True)
        return self._arrange_row_first(sorted_stamps, max_width, spacing)

    def _arrange_balanced(self, stamps: list[Stamp], max_width: float, spacing: float) -> list[Row]:
        """Balance rows by total width rather than stamp count."""
        if not stamps:
            return []

        # Estimate number of rows
        total_width = sum(s.width + spacing for s in stamps)
        estimated_rows = max(1, int(total_width / max_width) + 1)

        rows = []
        current_row = Row(style=RowStyle.JUSTIFIED_SPACE, spacing=spacing)
        current_width = 0.0
        target_width = total_width / estimated_rows

        for stamp in stamps:
            if current_width + stamp.width > target_width and current_row.stamps:
                rows.append(current_row)
                current_row = Row(style=RowStyle.JUSTIFIED_SPACE, spacing=spacing)
                current_width = 0.0
            current_row.stamps.append(stamp)
            current_width += stamp.width + spacing

        if current_row.stamps:
            rows.append(current_row)

        return rows

    # ------------------------------------------------------------------
    # Private: Helpers
    # ------------------------------------------------------------------

    def _calculate_layout_height(self, rows: list[Row]) -> float:
        """Calculate total height of a layout."""
        height = 0.0
        for row in rows:
            height += self.calculate_row_height(row)
            height += self.page_setup.vspace
        return height

    def _score_layout(self, rows: list[Row], total_height: float, content_height: float) -> float:
        """
        Score a layout (higher is better).

        Considers:
        - Fits on page (big factor)
        - Less wasted space
        - More uniform row widths
        """
        if total_height > content_height:
            return 0.0  # Doesn't fit

        space_utilization = 1.0 - (total_height / content_height)
        uniformity = self._row_uniformity(rows)

        return space_utilization * 0.4 + uniformity * 0.6

    def _row_uniformity(self, rows: list[Row]) -> float:
        """Calculate how uniform the row widths are (0-1)."""
        if not rows:
            return 1.0

        widths = [sum(s.width for s in r.stamps) for r in rows if r.stamps]
        if not widths:
            return 1.0

        avg = sum(widths) / len(widths)
        if avg == 0:
            return 1.0

        variance = sum((w - avg) ** 2 for w in widths) / len(widths)
        cv = (variance**0.5) / avg  # Coefficient of variation

        return max(0.0, 1.0 - cv)

    @staticmethod
    def _rects_overlap(a: PlacementRect, b: PlacementRect) -> bool:
        """Check if two rectangles overlap."""
        return not (
            a.x + a.width <= b.x
            or b.x + b.width <= a.x
            or a.y + a.height <= b.y
            or b.y + b.height <= a.y
        )
