"""
Configuration dialog for StampAlbum Pro.

Allows users to customize application settings including:
- Editor preferences (font, size, dark mode)
- PDF generation options
- Default page settings
"""

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class ConfigDialog(QDialog):
    """
    Configuration dialog for StampAlbum Pro settings.
    """

    def __init__(self, parent: QWidget | None = None, config: dict | None = None):
        super().__init__(parent)
        self.config = config or self._default_config()
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        self._load_config()

    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "editor": {
                "font_family": "Menlo",
                "font_size": 12,
                "tab_width": 4,
                "dark_mode": False,
                "show_line_numbers": True,
                "auto_save": True,
            },
            "pdf": {
                "auto_open": True,
                "output_dir": "",
            },
            "defaults": {
                "page_size": "A4",
                "margins": (20.0, 15.0, 15.0, 15.0),
                "spacing": (6.0, 6.0),
            },
        }

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Tab widget
        self.tabs = QTabWidget()

        # Editor tab
        editor_tab = self._create_editor_tab()
        self.tabs.addTab(editor_tab, "Editor")

        # PDF tab
        pdf_tab = self._create_pdf_tab()
        self.tabs.addTab(pdf_tab, "PDF")

        # Defaults tab
        defaults_tab = self._create_defaults_tab()
        self.tabs.addTab(defaults_tab, "Defaults")

        layout.addWidget(self.tabs)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_editor_tab(self) -> QWidget:
        """Create the editor settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Font family
        self.font_combo = QComboBox()
        # Common monospace fonts
        fonts = ["Menlo", "Consolas", "Monaco", "Courier New", "Source Code Pro", "Fira Code"]
        self.font_combo.addItems(fonts)
        layout.addRow("Font:", self.font_combo)

        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        layout.addRow("Font Size:", self.font_size_spin)

        # Tab width
        self.tab_width_spin = QSpinBox()
        self.tab_width_spin.setRange(2, 8)
        self.tab_width_spin.setValue(4)
        layout.addRow("Tab Width:", self.tab_width_spin)

        # Dark mode
        self.dark_mode_check = QCheckBox("Enable dark mode")
        layout.addRow("", self.dark_mode_check)

        # Line numbers
        self.line_numbers_check = QCheckBox("Show line numbers")
        self.line_numbers_check.setChecked(True)
        layout.addRow("", self.line_numbers_check)

        # Auto-save
        self.auto_save_check = QCheckBox("Auto-save on generate")
        self.auto_save_check.setChecked(True)
        layout.addRow("", self.auto_save_check)

        layout.addRow(QWidget())  # Spacer
        return tab

    def _create_pdf_tab(self) -> QWidget:
        """Create the PDF settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Auto-open PDF
        self.auto_open_check = QCheckBox("Automatically open PDF after generation")
        self.auto_open_check.setChecked(True)
        layout.addRow("", self.auto_open_check)

        # Output directory
        self.output_dir_label = QLabel("Same as source file")
        layout.addRow("Output Directory:", self.output_dir_label)

        layout.addRow(QWidget())  # Spacer
        return tab

    def _create_defaults_tab(self) -> QWidget:
        """Create the default settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Page size
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4", "Letter", "A3", "A5", "Legal"])
        layout.addRow("Default Page Size:", self.page_size_combo)

        # Margins
        margin_group = QGroupBox("Default Margins (mm)")
        margin_layout = QFormLayout(margin_group)

        self.margin_left_spin = QDoubleSpinBox()
        self.margin_left_spin.setRange(0, 50)
        self.margin_left_spin.setSingleStep(0.5)
        self.margin_left_spin.setValue(20.0)
        margin_layout.addRow("Left:", self.margin_left_spin)

        self.margin_right_spin = QDoubleSpinBox()
        self.margin_right_spin.setRange(0, 50)
        self.margin_right_spin.setSingleStep(0.5)
        self.margin_right_spin.setValue(15.0)
        margin_layout.addRow("Right:", self.margin_right_spin)

        self.margin_top_spin = QDoubleSpinBox()
        self.margin_top_spin.setRange(0, 50)
        self.margin_top_spin.setSingleStep(0.5)
        self.margin_top_spin.setValue(15.0)
        margin_layout.addRow("Top:", self.margin_top_spin)

        self.margin_bottom_spin = QDoubleSpinBox()
        self.margin_bottom_spin.setRange(0, 50)
        self.margin_bottom_spin.setSingleStep(0.5)
        self.margin_bottom_spin.setValue(15.0)
        margin_layout.addRow("Bottom:", self.margin_bottom_spin)

        layout.addRow(margin_group)

        # Spacing
        spacing_group = QGroupBox("Default Spacing (mm)")
        spacing_layout = QHBoxLayout(spacing_group)

        spacing_layout.addWidget(QLabel("Horizontal:"))
        self.hspace_spin = QDoubleSpinBox()
        self.hspace_spin.setRange(0, 20)
        self.hspace_spin.setSingleStep(0.5)
        self.hspace_spin.setValue(6.0)
        spacing_layout.addWidget(self.hspace_spin)

        spacing_layout.addWidget(QLabel("Vertical:"))
        self.vspace_spin = QDoubleSpinBox()
        self.vspace_spin.setRange(0, 20)
        self.vspace_spin.setSingleStep(0.5)
        self.vspace_spin.setValue(6.0)
        spacing_layout.addWidget(self.vspace_spin)

        layout.addRow(spacing_group)

        layout.addRow(QWidget())  # Spacer
        return tab

    def _load_config(self):
        """Load configuration into UI elements."""
        editor = self.config.get("editor", {})
        self.font_combo.setCurrentText(editor.get("font_family", "Menlo"))
        self.font_size_spin.setValue(editor.get("font_size", 12))
        self.tab_width_spin.setValue(editor.get("tab_width", 4))
        self.dark_mode_check.setChecked(editor.get("dark_mode", False))
        self.line_numbers_check.setChecked(editor.get("show_line_numbers", True))
        self.auto_save_check.setChecked(editor.get("auto_save", True))

        pdf = self.config.get("pdf", {})
        self.auto_open_check.setChecked(pdf.get("auto_open", True))

        defaults = self.config.get("defaults", {})
        self.page_size_combo.setCurrentText(defaults.get("page_size", "A4"))
        margins = defaults.get("margins", (20.0, 15.0, 15.0, 15.0))
        self.margin_left_spin.setValue(margins[0])
        self.margin_right_spin.setValue(margins[1])
        self.margin_top_spin.setValue(margins[2])
        self.margin_bottom_spin.setValue(margins[3])
        spacing = defaults.get("spacing", (6.0, 6.0))
        self.hspace_spin.setValue(spacing[0])
        self.vspace_spin.setValue(spacing[1])

    def _on_accept(self):
        """Save configuration and accept."""
        self._save_config()
        self.accept()

    def _save_config(self):
        """Save UI values to configuration."""
        self.config["editor"] = {
            "font_family": self.font_combo.currentText(),
            "font_size": self.font_size_spin.value(),
            "tab_width": self.tab_width_spin.value(),
            "dark_mode": self.dark_mode_check.isChecked(),
            "show_line_numbers": self.line_numbers_check.isChecked(),
            "auto_save": self.auto_save_check.isChecked(),
        }

        self.config["pdf"] = {
            "auto_open": self.auto_open_check.isChecked(),
        }

        self.config["defaults"] = {
            "page_size": self.page_size_combo.currentText(),
            "margins": (
                self.margin_left_spin.value(),
                self.margin_right_spin.value(),
                self.margin_top_spin.value(),
                self.margin_bottom_spin.value(),
            ),
            "spacing": (
                self.hspace_spin.value(),
                self.vspace_spin.value(),
            ),
        }

    def get_config(self) -> dict:
        """Return the current configuration."""
        return self.config
