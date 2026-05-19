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

# Template definitions
TEMPLATES = [
    {
        "id": "blank",
        "name": "Blank Album",
        "description": "Start with a blank album - configure everything yourself.",
        "category": "Basic",
        "content": """# Blank Album
# Configure your album settings below

ALBUM_PAGES_SIZE (210.0 297.0)
ALBUM_PAGES_MARGINS (20.0 15.0 15.0 15.0)
ALBUM_PAGES_SPACING (6.0 6.0)

PAGE_START

""",
    },
    {
        "id": "classic",
        "name": "Classic Album",
        "description": "Traditional layout with triple border, centered titles, and stamp rows.",
        "category": "Basic",
        "content": """# Classic Album Template
ALBUM_TITLE ("My Stamp Collection")
ALBUM_PAGES_SIZE (210.0 297.0)
ALBUM_PAGES_MARGINS (20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER (0.1 0.5 0.1 1.0)
ALBUM_PAGES_SPACING (6.0 6.0)
ALBUM_PAGES_TITLE (TB 16 "My Stamp Collection")

PAGE_START

PAGE_TEXT_CENTRE (HS 14 "Section Title")
PAGE_TEXT_CENTRE (HN 10 "Description text goes here.")

ROW_START_FS (HN 8 0.5 6.0)
STAMP_ADD (32.0 37.0 "Description" "sg 1" "" "sacc 1")
STAMP_ADD (32.0 37.0 "Description" "sg 2" "" "sacc 2")

""",
    },
    {
        "id": "competition",
        "name": "Competition Display",
        "description": "Large format with ornate borders, designed for exhibition frames.",
        "category": "Competition",
        "content": """# Competition Display Template
ALBUM_TITLE ("Exhibition Title")
ALBUM_AUTHOR ("Exhibitor Name")
ALBUM_PAGES_SIZE (210.0 297.0)
ALBUM_PAGES_MARGINS (15.0 15.0 12.0 12.0)
ALBUM_PAGES_BORDER (0.2 0.6 0.2 1.5)
ALBUM_PAGES_SPACING (8.0 8.0)
ALBUM_PAGES_TITLE (TB 18 "Exhibition Title")
ALBUM_PAGES_FOOTER_NUMBER (HN 10 C 1 "Page " " of $PAGES$")

COLOUR_ALBUM_TITLE (darkblue)
COLOUR_ALBUM_BORDER (darkred)

PAGE_START

PAGE_TEXT_CENTRE (HS 16 "Section Heading")
PAGE_TEXT_CENTRE (HN 12 "Brief description of this section.")

PAGE_RULE_H (0.5 4 0)

ROW_START_FS (HN 9 0.5 7.0)
STAMP_ADD (35.0 40.0 "Stamp description" "sg 1" "" "")
STAMP_HEADING (HB 10 "Key Item")

""",
    },
    {
        "id": "modern",
        "name": "Modern Minimal",
        "description": "Clean, minimalist design with subtle styling.",
        "category": "Modern",
        "content": """# Modern Minimal Template
ALBUM_TITLE ("Collection")
ALBUM_PAGES_SIZE (210.0 297.0)
ALBUM_PAGES_MARGINS (25.0 25.0 20.0 20.0)
ALBUM_PAGES_SPACING (10.0 10.0)
ALBUM_PAGES_TITLE (HN 14 "Collection")

COLOUR_ALBUM_TITLE (gray)

PAGE_START

PAGE_TEXT (HN 11 "Section heading - left aligned")

ROW_START_FS (HN 8 1.0 6.0)
STAMP_ADD (30.0 35.0 "Description" "sg 1" "" "")
STAMP_ADD (30.0 35.0 "Description" "sg 2" "" "")

""",
    },
    {
        "id": "two_column",
        "name": "Two Column Layout",
        "description": "Page split into two columns for dense information display.",
        "category": "Layout",
        "content": """# Two Column Layout Template
ALBUM_TITLE ("Two Column Album")
ALBUM_PAGES_SIZE (210.0 297.0)
ALBUM_PAGES_MARGINS (15.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER (0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING (5.0 5.0)
ALBUM_PAGES_TITLE (TB 14 "Two Column Album")

PAGE_START

PAGE_COLUMN_START (10.0)

PAGE_TEXT_CENTRE (HS 12 "Left Column")
ROW_START_FS (HN 7 0.3 5.0)
STAMP_ADD (25.0 28.0 "Stamp" "sg 1" "" "")

PAGE_COLUMN_NEXT

PAGE_TEXT_CENTRE (HS 12 "Right Column")
ROW_START_FS (HN 7 0.3 5.0)
STAMP_ADD (25.0 28.0 "Stamp" "sg 2" "" "")

PAGE_COLUMN_STOP

""",
    },
    {
        "id": "thematic",
        "name": "Thematic Collection",
        "description": "Organized by theme with color-coded sections.",
        "category": "Thematic",
        "content": """# Thematic Collection Template
ALBUM_TITLE ("Thematic Collection")
ALBUM_PAGES_SIZE (210.0 297.0)
ALBUM_PAGES_MARGINS (20.0 15.0 15.0 15.0)
ALBUM_PAGES_SPACING (6.0 6.0)
ALBUM_PAGES_TITLE (TB 16 "Thematic Collection")

PAGE_START

# Theme: Section 1
COLOUR_PAGE_TEXT (darkblue)
PAGE_TEXT_CENTRE (HS 14 "Theme: Birds")
PAGE_TEXT_CENTRE (HN 10 "Description of this thematic section.")

ROW_START_FS (HN 8 0.5 6.0)
STAMP_ADD (32.0 37.0 "Bird stamp" "sg 1" "" "")
STAMP_ADD (32.0 37.0 "Bird stamp" "sg 2" "" "")

# Theme: Section 2
COLOUR_PAGE_TEXT (darkgreen)
PAGE_TEXT_CENTRE (HS 14 "Theme: Flowers")
PAGE_TEXT_CENTRE (HN 10 "Description of this thematic section.")

ROW_START_FS (HN 8 0.5 6.0)
STAMP_ADD (32.0 37.0 "Flower stamp" "sg 3" "" "")
STAMP_ADD (32.0 37.0 "Flower stamp" "sg 4" "" "")

""",
    },
]


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
