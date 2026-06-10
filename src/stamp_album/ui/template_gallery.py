"""
Template gallery widget for StampAlbum Pro.

Displays a visual gallery of album templates that users can browse
and select to start a new album.
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from stamp_album.templates import TEMPLATES


class TemplateCard(QWidget):
    """A card widget representing a single template."""

    selected = pyqtSignal(str)  # Emits template content

    def __init__(self, template: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.template = template
        self._selected = False
        self._setup_ui()

    def _setup_ui(self):
        """Set up the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Card frame
        self.frame = QFrame()
        self.frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.frame.setStyleSheet(
            "QFrame { background-color: white; border: 2px solid #CCCCCC; border-radius: 4px; }"
        )

        card_layout = QVBoxLayout(self.frame)
        card_layout.setContentsMargins(12, 12, 12, 12)

        # Template name
        name_label = QLabel(self.template["name"])
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(12)
        name_label.setFont(name_font)
        card_layout.addWidget(name_label)

        # Category badge
        category_label = QLabel(self.template["category"])
        category_label.setStyleSheet(
            "background-color: #E3F2FD; color: #1976D2; "
            "padding: 2px 8px; border-radius: 10px; font-size: 10px;"
        )
        category_label.setFixedWidth(
            category_label.fontMetrics().horizontalAdvance(self.template["category"]) + 16
        )
        card_layout.addWidget(category_label)

        # Description
        desc_label = QLabel(self.template["description"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666; font-size: 11px;")
        card_layout.addWidget(desc_label)

        layout.addWidget(self.frame)

    def mousePressEvent(self, event):
        """Handle click to select template."""
        self._selected = True
        self.frame.setStyleSheet(
            "QFrame { background-color: #E3F2FD; border: 2px solid #1976D2; border-radius: 4px; }"
        )
        self.selected.emit(self.template["content"])

    @property
    def is_selected(self) -> bool:
        return self._selected

    def deselect(self):
        """Deselect this card."""
        self._selected = False
        self.frame.setStyleSheet(
            "QFrame { background-color: white; border: 2px solid #CCCCCC; border-radius: 4px; }"
        )


class TemplateGallery(QDialog):
    """
    Dialog that displays a gallery of album templates.

    Users can browse templates by category and select one to
    create a new album.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.selected_content: str = ""
        self.setWindowTitle("Template Gallery")
        self.setMinimumSize(800, 600)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the gallery UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Choose a Template")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(16)
        header.setFont(header_font)
        layout.addWidget(header)

        subtitle = QLabel("Select a template to start your album, or import your own file.")
        subtitle.setStyleSheet("color: #666666;")
        layout.addWidget(subtitle)

        # Category filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Category:")
        filter_layout.addWidget(filter_label)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All")
        categories = sorted(set(t["category"] for t in TEMPLATES))
        for cat in categories:
            self.category_combo.addItem(cat)
        self.category_combo.currentTextChanged.connect(self._filter_templates)
        filter_layout.addWidget(self.category_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Template grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)

        self.cards: list[TemplateCard] = []
        self._populate_grid()

        self.scroll.setWidget(self.grid_widget)
        layout.addWidget(self.scroll)

        # Import button
        import_layout = QHBoxLayout()
        self.import_btn = QPushButton("Import Custom Template...")
        self.import_btn.clicked.connect(self._import_template)
        import_layout.addWidget(self.import_btn)
        import_layout.addStretch()
        layout.addLayout(import_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_grid(self, filter_category: str = "All"):
        """Populate the template grid."""
        # Clear existing cards
        for card in self.cards:
            card.deleteLater()
        self.cards.clear()

        # Filter templates
        filtered = [
            t for t in TEMPLATES if filter_category == "All" or t["category"] == filter_category
        ]

        # Add cards to grid (3 per row)
        row = 0
        col = 0
        for template in filtered:
            card = TemplateCard(template)
            card.selected.connect(self._on_template_selected)
            self.cards.append(card)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        # Add stretch to fill remaining space
        self.grid_layout.setRowStretch(row + 1, 1)

    def _filter_templates(self, category: str):
        """Filter templates by category."""
        self._populate_grid(category)

    def _on_template_selected(self, content: str):
        """Handle template selection."""
        self.selected_content = content
        # Deselect all other cards
        for card in self.cards:
            if card.template["content"] != content:
                card.deselect()

    def _import_template(self):
        """Import a custom template file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Template",
            "",
            "Album Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.selected_content = f.read()
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import file:\n{str(e)}")

    def _on_accept(self):
        """Handle OK button click."""
        if not self.selected_content:
            QMessageBox.warning(
                self,
                "No Template Selected",
                "Please select a template or import a custom file.",
            )
            return
        self.accept()
