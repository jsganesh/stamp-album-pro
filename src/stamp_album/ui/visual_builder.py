"""
Visual drag-and-drop builder for stamp album pages.

Provides a canvas where users can visually place stamps,
text elements, and configure rows/columns.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPen, QWheelEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from stamp_album.core.models import (
    FormattedText,
    Page,
    Row,
    RowStyle,
    Stamp,
    TextAlignment,
)
from stamp_album.engines.layout_engine import LayoutEngine, LayoutStrategy


class StampCanvas(QWidget):
    """Interactive canvas for visual stamp placement."""

    selection_changed = pyqtSignal(object)  # Selected element
    element_moved = pyqtSignal(object, float, float)  # Element, new_x, new_y

    def __init__(self, page: Page, page_setup, parent=None):
        super().__init__(parent)
        self.page = page
        self.page_setup = page_setup
        self.scale = 2.0  # pixels per mm
        self.selected_element = None
        self.dragging = False
        self.drag_offset = (0, 0)
        self.grid_visible = True
        self.grid_size = 5.0  # mm

        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        # Page area
        page_w = int(self.page_setup.width * self.scale)
        page_h = int(self.page_setup.height * self.scale)
        margin_l = int(self.page_setup.margin_left * self.scale)
        margin_t = int(self.page_setup.margin_top * self.scale)

        # Page background
        painter.fillRect(margin_l, margin_t, page_w, page_h, QColor(255, 255, 255))

        # Page border
        pen = QPen(QColor(100, 100, 100), 1)
        painter.setPen(pen)
        painter.drawRect(margin_l, margin_t, page_w, page_h)

        # Grid
        if self.grid_visible:
            grid_pen = QPen(QColor(200, 200, 200), 0.5)
            painter.setPen(grid_pen)
            step = int(self.grid_size * self.scale)
            for x in range(margin_l, margin_l + page_w, step):
                painter.drawLine(x, margin_t, x, margin_t + page_h)
            for y in range(margin_t, margin_t + page_h, step):
                painter.drawLine(margin_l, y, margin_l + page_w, y)

        # Stamp rows
        y_offset = margin_t + 10
        for row in self.page.rows:
            x_offset = margin_l + 5
            row_height = max((s.height for s in row.stamps), default=0) * self.scale

            for stamp in row.stamps:
                w = int(stamp.width * self.scale)
                h = int(stamp.height * self.scale)

                # Stamp box
                is_selected = self.selected_element is stamp
                if is_selected:
                    painter.fillRect(x_offset, y_offset, w, h, QColor(173, 216, 230, 100))
                    pen = QPen(QColor(0, 100, 200), 2)
                else:
                    pen = QPen(QColor(128, 128, 128), 1)

                painter.setPen(pen)
                painter.drawRect(x_offset, y_offset, w, h)

                # Description
                if stamp.description:
                    painter.setPen(QColor(50, 50, 50))
                    font = painter.font()
                    font.setPointSize(6)
                    painter.setFont(font)
                    painter.drawText(
                        x_offset + 2, y_offset + h - 2, stamp.description[:20]
                    )

                x_offset += w + int(row.spacing * self.scale)

            y_offset += row_height + int(self.page_setup.vspace * self.scale)

        # Text elements
        for text_elem in self.page.text_elements:
            painter.setPen(QColor(0, 0, 0))
            font = painter.font()
            font.setPointSize(int(text_elem.size))
            if text_elem.alignment == TextAlignment.CENTER:
                font.setBold(True)
            painter.setFont(font)

            is_selected = self.selected_element is text_elem
            if is_selected:
                painter.setPen(QColor(0, 100, 200))

            # Simple text rendering
            painter.drawText(
                margin_l + 10,
                y_offset,
                int((self.page_setup.width - 30) * self.scale),
                20,
                Qt.AlignmentFlag.AlignLeft,
                text_elem.content[:50],
            )
            y_offset += 25

    def wheelEvent(self, event: QWheelEvent):
        """Zoom in/out with mouse wheel."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale = min(5.0, self.scale * 1.1)
        else:
            self.scale = max(0.5, self.scale / 1.1)
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._handle_click(event.pos())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging and self.selected_element:
            # Could implement drag logic here
            pass

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False

    def _handle_click(self, pos):
        """Handle click on canvas to select elements."""
        # Simple hit testing - could be enhanced
        self.selected_element = None
        self.selection_changed.emit(None)
        self.update()

    def set_grid_visible(self, visible: bool):
        self.grid_visible = visible
        self.update()

    def set_grid_size(self, size: float):
        self.grid_size = size
        self.update()


class VisualBuilder(QWidget):
    """Main visual builder widget with canvas and property panel."""

    def __init__(self, page: Page, page_setup, parent=None):
        super().__init__(parent)
        self.page = page
        self.page_setup = page_setup
        self.layout_engine = LayoutEngine(page_setup)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Canvas
        canvas_scroll = QScrollArea()
        self.canvas = StampCanvas(self.page, self.page_setup)
        canvas_scroll.setWidget(self.canvas)
        canvas_scroll.setWidgetResizable(True)
        splitter.addWidget(canvas_scroll)

        # Right: Property panel
        panel = self._create_property_panel()
        splitter.addWidget(panel)

        splitter.setSizes([600, 300])
        layout.addWidget(splitter)

    def _create_property_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMaximumWidth(320)
        layout = QVBoxLayout(panel)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize((16, 16))

        grid_btn = QPushButton("Grid")
        grid_btn.setCheckable(True)
        grid_btn.setChecked(True)
        grid_btn.clicked.connect(lambda: self.canvas.set_grid_visible(grid_btn.isChecked()))
        toolbar.addWidget(grid_btn)

        layout.addWidget(toolbar)

        # Add stamp section
        stamp_group = QGroupBox("Add Stamp")
        stamp_layout = QFormLayout(stamp_group)

        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(5, 200)
        self.width_spin.setValue(30)
        self.width_spin.setSuffix(" mm")
        stamp_layout.addRow("Width:", self.width_spin)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(5, 200)
        self.height_spin.setValue(35)
        self.height_spin.setSuffix(" mm")
        stamp_layout.addRow("Height:", self.height_spin)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Stamp description")
        stamp_layout.addRow("Description:", self.desc_edit)

        add_stamp_btn = QPushButton("Add Stamp")
        add_stamp_btn.clicked.connect(self._add_stamp)
        stamp_layout.addRow(add_stamp_btn)

        layout.addWidget(stamp_group)

        # Add text section
        text_group = QGroupBox("Add Text")
        text_layout = QFormLayout(text_group)

        self.text_content = QLineEdit()
        self.text_content.setPlaceholderText("Text content")
        text_layout.addRow("Content:", self.text_content)

        self.font_size_spin = QDoubleSpinBox()
        self.font_size_spin.setRange(6, 48)
        self.font_size_spin.setValue(10)
        text_layout.addRow("Font Size:", self.font_size_spin)

        self.align_combo = QComboBox()
        self.align_combo.addItems(["Left", "Center", "Right", "Justify"])
        text_layout.addRow("Alignment:", self.align_combo)

        add_text_btn = QPushButton("Add Text")
        add_text_btn.clicked.connect(self._add_text)
        text_layout.addRow(add_text_btn)

        layout.addWidget(text_group)

        # Auto-layout section
        auto_group = QGroupBox("Auto Layout")
        auto_layout = QFormLayout(auto_group)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([s.value for s in LayoutStrategy])
        auto_layout.addRow("Strategy:", self.strategy_combo)

        auto_btn = QPushButton("Auto Arrange")
        auto_btn.clicked.connect(self._auto_arrange)
        auto_layout.addRow(auto_btn)

        layout.addWidget(auto_group)

        layout.addStretch()

        return panel

    def _add_stamp(self):
        """Add a stamp to the current page."""
        stamp = Stamp(
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            description=self.desc_edit.text(),
        )

        # Add to last row or create new row
        if self.page.rows:
            self.page.rows[-1].stamps.append(stamp)
        else:
            row = Row(style=RowStyle.FIXED_SPACE, spacing=self.page_setup.hspace)
            row.stamps.append(stamp)
            self.page.rows.append(row)

        self.desc_edit.clear()
        self.canvas.update()

    def _add_text(self):
        """Add a text element to the current page."""
        align_map = {
            "Left": TextAlignment.LEFT,
            "Center": TextAlignment.CENTER,
            "Right": TextAlignment.RIGHT,
            "Justify": TextAlignment.JUSTIFY,
        }

        text = FormattedText(
            content=self.text_content.text(),
            size=self.font_size_spin.value(),
            alignment=align_map[self.align_combo.currentText()],
        )

        self.page.text_elements.append(text)
        self.text_content.clear()
        self.canvas.update()

    def _auto_arrange(self):
        """Auto-arrange stamps using selected strategy."""
        strategy_map = {s.value: s for s in LayoutStrategy}
        strategy = strategy_map[self.strategy_combo.currentText()]

        # Collect all stamps
        all_stamps = []
        for row in self.page.rows:
            all_stamps.extend(row.stamps)

        if not all_stamps:
            return

        # Clear existing rows
        self.page.rows.clear()

        # Apply new layout
        result = self.layout_engine.auto_arrange_stamps(all_stamps, strategy=strategy)
        self.page.rows = result.rows

        self.canvas.update()

    def get_page(self) -> Page:
        """Return the modified page."""
        return self.page


class VisualBuilderDialog(QDialog):
    """Dialog for visual page editing."""

    def __init__(self, page: Page, page_setup, parent=None):
        super().__init__(parent)
        self.page = page
        self.page_setup = page_setup
        self.builder = VisualBuilder(page, page_setup)

        self.setWindowTitle("Visual Page Builder")
        self.resize(1000, 700)

        layout = QVBoxLayout(self)
        layout.addWidget(self.builder)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_page(self) -> Page:
        return self.builder.get_page()
