"""
Live preview panel for StampAlbum Pro.

Renders a real-time preview of the album as the user edits,
using WeasyPrint to generate page images for accurate preview.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QScrollArea,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class PreviewPanel(QWidget):
    """
    Live preview panel that displays the album as it's being edited.

    Shows a rendered preview of the current album state, updating
    automatically when the source changes.
    """

    # Signal emitted when user wants to refresh preview
    refresh_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._html_content: str = ""
        self._page_count: int = 0
        self._current_page: int = 0
        self._zoom_level: float = 1.0
        self._page_images: list[QPixmap] = []

        self._setup_ui()

    def _setup_ui(self):
        """Set up the preview panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Preview area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            "background-color: #E0E0E0; border: 1px solid #CCCCCC;"
        )
        self.scroll_area.setWidget(self.preview_label)

        layout.addWidget(self.scroll_area)

        # Status bar
        self.status_label = QLabel("No preview available")
        self.status_label.setStyleSheet(
            "padding: 4px; background-color: #F5F5F5; border-top: 1px solid #CCCCCC;"
        )
        layout.addWidget(self.status_label)

    def _create_toolbar(self) -> QToolBar:
        """Create the preview toolbar."""
        toolbar = QToolBar("Preview Toolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setStyleSheet(
            "QToolBar { background-color: #F5F5F5; border-bottom: 1px solid #CCCCCC; }"
        )

        # Zoom controls
        zoom_label = QLabel("Zoom:")
        toolbar.addWidget(zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self._on_zoom_changed)
        toolbar.addWidget(self.zoom_combo)

        toolbar.addSeparator()

        # Page navigation
        self.prev_page_btn = QPushButton("◀")
        self.prev_page_btn.setEnabled(False)
        self.prev_page_btn.clicked.connect(self._prev_page)
        toolbar.addWidget(self.prev_page_btn)

        self.page_label = QLabel("Page 0 / 0")
        toolbar.addWidget(self.page_label)

        self.next_page_btn = QPushButton("▶")
        self.next_page_btn.setEnabled(False)
        self.next_page_btn.clicked.connect(self._next_page)
        toolbar.addWidget(self.next_page_btn)

        toolbar.addSeparator()

        # Refresh button
        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.clicked.connect(lambda: self.refresh_requested.emit())
        toolbar.addWidget(refresh_btn)

        return toolbar

    def _on_zoom_changed(self, zoom_text: str):
        """Handle zoom level changes."""
        zoom_map = {
            "50%": 0.5,
            "75%": 0.75,
            "100%": 1.0,
            "125%": 1.25,
            "150%": 1.5,
            "200%": 2.0,
        }
        self._zoom_level = zoom_map.get(zoom_text, 1.0)
        self._update_display()

    def _prev_page(self):
        """Navigate to previous page."""
        if self._current_page > 0:
            self._current_page -= 1
            self._update_display()

    def _next_page(self):
        """Navigate to next page."""
        if self._current_page < self._page_count - 1:
            self._current_page += 1
            self._update_display()

    def set_html_content(self, html: str):
        """
        Set the HTML content to display.

        Args:
            html: HTML string to render
        """
        self._html_content = html
        self._render_pages()
        self._current_page = 0
        self._update_display()

    def _render_pages(self):
        """Render HTML pages to QPixmap images using WeasyPrint."""
        from weasyprint import HTML

        self._page_images = []
        self._page_count = 0

        if not self._html_content:
            return

        try:
            # Render HTML to PNG images using WeasyPrint
            html_doc = HTML(string=self._html_content)
            doc = html_doc.render()

            self._page_count = len(doc.pages)

            for page in doc.pages:
                # Render each page to PNG
                png_bytes = page.write_to_image().write_png()
                pixmap = QPixmap()
                pixmap.loadFromData(png_bytes)
                self._page_images.append(pixmap)
        except Exception:
            # If rendering fails, show error
            self._page_count = 0
            self._page_images = []

    def _update_display(self):
        """Update the preview display."""
        if not self._page_images:
            self.preview_label.setText("No preview available")
            self.status_label.setText("No preview available")
            self.page_label.setText("Page 0 / 0")
            self.prev_page_btn.setEnabled(False)
            self.next_page_btn.setEnabled(False)
            return

        # Display current page image with zoom
        if 0 <= self._current_page < len(self._page_images):
            pixmap = self._page_images[self._current_page]
            scaled = pixmap.scaled(
                int(pixmap.width() * self._zoom_level),
                int(pixmap.height() * self._zoom_level),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_label.setPixmap(scaled)

        # Update status
        self.status_label.setText(
            f"Page {self._current_page + 1} of {self._page_count} | "
            f"Zoom: {int(self._zoom_level * 100)}%"
        )

        # Update page navigation
        self.page_label.setText(f"Page {self._current_page + 1} / {self._page_count}")
        self.prev_page_btn.setEnabled(self._current_page > 0)
        self.next_page_btn.setEnabled(self._current_page < self._page_count - 1)

    def clear(self):
        """Clear the preview."""
        self._html_content = ""
        self._page_count = 0
        self._current_page = 0
        self._page_images = []
        self._update_display()

    @property
    def zoom_level(self) -> float:
        """Get the current zoom level."""
        return self._zoom_level

    @zoom_level.setter
    def zoom_level(self, value: float):
        """Set the zoom level."""
        self._zoom_level = max(0.25, min(value, 3.0))
        self._update_display()
