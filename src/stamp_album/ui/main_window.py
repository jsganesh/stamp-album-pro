"""
Main window for StampAlbum Pro.

The central application window containing:
- Toolbar with actions
- Splitter view (editor + preview)
- Status bar
- Menu system
"""

import os
import tempfile
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QFont, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
)

from stamp_album.core.parser import AlbumParser
from stamp_album.engines.pdf_generator import PDFGenerator
from stamp_album.ui.config_dialog import ConfigDialog
from stamp_album.ui.editor import AlbumEditor
from stamp_album.ui.preview_panel import PreviewPanel
from stamp_album.ui.template_gallery import TemplateGallery

# Application styling
APP_STYLESHEET = """
QMainWindow {
    background-color: #1E1E1E;
}

QToolBar {
    background-color: #2D2D2D;
    border: none;
    border-bottom: 1px solid #3E3E3E;
    padding: 4px;
    spacing: 4px;
}

QToolBar QToolButton {
    background-color: #3C3C3C;
    color: #CCCCCC;
    border: 1px solid #4A4A4A;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
}

QToolBar QToolButton:hover {
    background-color: #4A4A4A;
    border-color: #5A5A5A;
}

QToolBar QToolButton:pressed {
    background-color: #2A2A2A;
}

QToolBar QToolButton:disabled {
    background-color: #2D2D2D;
    color: #666666;
    border-color: #3A3A3A;
}

QMenuBar {
    background-color: #2D2D2D;
    color: #CCCCCC;
    border: none;
    padding: 2px;
}

QMenuBar::item {
    padding: 6px 12px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #3C3C3C;
}

QMenu {
    background-color: #2D2D2D;
    color: #CCCCCC;
    border: 1px solid #3E3E3E;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
}

QMenu::item:selected {
    background-color: #3C3C3C;
}

QMenu::separator {
    height: 1px;
    background-color: #3E3E3E;
    margin: 4px 8px;
}

QStatusBar {
    background-color: #007ACC;
    color: white;
    border: none;
}

QStatusBar QLabel {
    color: white;
    padding: 2px 8px;
}

QSplitter::handle {
    background-color: #3E3E3E;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #007ACC;
}

QLabel {
    color: #CCCCCC;
}

QComboBox {
    background-color: #3C3C3C;
    color: #CCCCCC;
    border: 1px solid #4A4A4A;
    border-radius: 4px;
    padding: 4px 8px;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #2D2D2D;
    color: #CCCCCC;
    selection-background-color: #007ACC;
}

QPushButton {
    background-color: #3C3C3C;
    color: #CCCCCC;
    border: 1px solid #4A4A4A;
    border-radius: 4px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #4A4A4A;
}

QPushButton:pressed {
    background-color: #2A2A2A;
}

QDialog {
    background-color: #1E1E1E;
}

QTabWidget::pane {
    border: 1px solid #3E3E3E;
    background-color: #1E1E1E;
}

QTabBar::tab {
    background-color: #2D2D2D;
    color: #CCCCCC;
    padding: 8px 16px;
    border: 1px solid #3E3E3E;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #1E1E1E;
    border-bottom: 1px solid #1E1E1E;
}

QScrollArea {
    border: none;
    background-color: #1E1E1E;
}

QGroupBox {
    color: #CCCCCC;
    border: 1px solid #3E3E3E;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}

QLineEdit {
    background-color: #3C3C3C;
    color: #CCCCCC;
    border: 1px solid #4A4A4A;
    border-radius: 4px;
    padding: 4px 8px;
}

QSpinBox, QDoubleSpinBox {
    background-color: #3C3C3C;
    color: #CCCCCC;
    border: 1px solid #4A4A4A;
    border-radius: 4px;
    padding: 4px 8px;
}

QCheckBox {
    color: #CCCCCC;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #4A4A4A;
    border-radius: 3px;
    background-color: #3C3C3C;
}

QCheckBox::indicator:checked {
    background-color: #007ACC;
    border-color: #007ACC;
}

QMessageBox {
    background-color: #1E1E1E;
}

QMessageBox QLabel {
    color: #CCCCCC;
}
"""


class MainWindow(QMainWindow):
    """
    Main application window for StampAlbum Pro.
    """

    def __init__(self):
        super().__init__()
        self._file_path: str | None = None
        self._config: dict = {}
        self._recent_files: list[str] = []
        self._pdf_path: str | None = None

        self._setup_window()
        self._setup_actions()
        self._setup_toolbar()
        self._setup_menu()
        self._setup_central_widget()
        self._setup_status_bar()
        self._apply_stylesheet()

    def _setup_window(self):
        """Configure the main window."""
        self.setWindowTitle("StampAlbum Pro")
        self.resize(1400, 900)
        self.setMinimumSize(900, 600)

        # Set application font
        font = QFont("SF Pro Text", 13)
        self.setFont(font)

    def _apply_stylesheet(self):
        """Apply the application stylesheet."""
        self.setStyleSheet(APP_STYLESHEET)

    def _setup_actions(self):
        """Create all application actions."""
        # File actions
        self.act_new = QAction("📄 New", self)
        self.act_new.setShortcut(QKeySequence.StandardKey.New)
        self.act_new.setStatusTip("Create a new album")
        self.act_new.triggered.connect(self._new_album)

        self.act_open = QAction("📂 Open", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.setStatusTip("Open an album file")
        self.act_open.triggered.connect(self._open_file)

        self.act_save = QAction("💾 Save", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.setStatusTip("Save the current album")
        self.act_save.triggered.connect(self._save_file)
        self.act_save.setEnabled(False)

        self.act_save_as = QAction("Save As...", self)
        self.act_save_as.setShortcut(QKeySequence("Shift+Ctrl+S"))
        self.act_save_as.setStatusTip("Save the album with a new name")
        self.act_save_as.triggered.connect(self._save_file_as)
        self.act_save_as.setEnabled(False)

        self.act_generate = QAction("⚡ Generate PDF", self)
        self.act_generate.setShortcut(QKeySequence("Ctrl+G"))
        self.act_generate.setStatusTip("Generate the PDF album")
        self.act_generate.triggered.connect(self._generate_pdf)
        self.act_generate.setEnabled(False)

        self.act_view_pdf = QAction("👁 View PDF", self)
        self.act_view_pdf.setShortcut(QKeySequence("Ctrl+V"))
        self.act_view_pdf.setStatusTip("View the generated PDF")
        self.act_view_pdf.triggered.connect(self._view_pdf)
        self.act_view_pdf.setEnabled(False)

        # Edit actions
        self.act_undo = QAction("↩ Undo", self)
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.act_undo.triggered.connect(lambda: self.editor.undo())

        self.act_redo = QAction("↪ Redo", self)
        self.act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.act_redo.triggered.connect(lambda: self.editor.redo())

        self.act_cut = QAction("✂ Cut", self)
        self.act_cut.setShortcut(QKeySequence.StandardKey.Cut)
        self.act_cut.triggered.connect(lambda: self.editor.cut())

        self.act_copy = QAction("📋 Copy", self)
        self.act_copy.setShortcut(QKeySequence.StandardKey.Copy)
        self.act_copy.triggered.connect(lambda: self.editor.copy())

        self.act_paste = QAction("📌 Paste", self)
        self.act_paste.setShortcut(QKeySequence.StandardKey.Paste)
        self.act_paste.triggered.connect(lambda: self.editor.paste())

        self.act_find = QAction("🔍 Find...", self)
        self.act_find.setShortcut(QKeySequence.StandardKey.Find)
        self.act_find.triggered.connect(self._show_find_dialog)

        # View actions
        self.act_toggle_preview = QAction("👁 Toggle Preview", self)
        self.act_toggle_preview.setShortcut(QKeySequence("Ctrl+P"))
        self.act_toggle_preview.setStatusTip("Show/hide the preview panel")
        self.act_toggle_preview.triggered.connect(self._toggle_preview)
        self.act_toggle_preview.setCheckable(True)
        self.act_toggle_preview.setChecked(True)

        # Tools actions
        self.act_templates = QAction("🎨 Template Gallery", self)
        self.act_templates.setShortcut(QKeySequence("Ctrl+T"))
        self.act_templates.setStatusTip("Browse album templates")
        self.act_templates.triggered.connect(self._show_templates)

        self.act_settings = QAction("⚙ Settings...", self)
        self.act_settings.setShortcut(QKeySequence("Ctrl+,"))
        self.act_settings.setStatusTip("Open settings dialog")
        self.act_settings.triggered.connect(self._show_settings)

        # Help actions
        self.act_help = QAction("❓ Help", self)
        self.act_help.setShortcut(QKeySequence.StandardKey.HelpContents)
        self.act_help.triggered.connect(self._show_help)

        self.act_about = QAction("ℹ About", self)
        self.act_about.triggered.connect(self._show_about)

    def _setup_toolbar(self):
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addAction(self.act_new)
        toolbar.addAction(self.act_open)
        toolbar.addAction(self.act_save)
        toolbar.addSeparator()
        toolbar.addAction(self.act_generate)
        toolbar.addAction(self.act_view_pdf)
        toolbar.addSeparator()
        toolbar.addAction(self.act_templates)
        toolbar.addSeparator()
        toolbar.addAction(self.act_toggle_preview)
        toolbar.addAction(self.act_settings)

        self.addToolBar(toolbar)

    def _setup_menu(self):
        """Create the menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.act_new)
        file_menu.addAction(self.act_open)
        file_menu.addAction(self.act_save)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.act_generate)
        file_menu.addAction(self.act_view_pdf)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)

        # Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.act_undo)
        edit_menu.addAction(self.act_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_cut)
        edit_menu.addAction(self.act_copy)
        edit_menu.addAction(self.act_paste)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_find)

        # View menu
        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.act_toggle_preview)

        # Tools menu
        tools_menu = self.menuBar().addMenu("&Tools")
        tools_menu.addAction(self.act_templates)
        tools_menu.addSeparator()
        tools_menu.addAction(self.act_settings)

        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.act_help)
        help_menu.addAction(self.act_about)

    def _setup_central_widget(self):
        """Set up the central widget with splitter."""
        # Create splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Editor
        self.editor = AlbumEditor()
        self.editor.modification_changed.connect(self._on_modified_changed)
        self.editor.cursor_position_changed.connect(self._on_cursor_position_changed)
        self.editor.textChanged.connect(self._on_text_changed)
        self.splitter.addWidget(self.editor)

        # Preview panel
        self.preview = PreviewPanel()
        self.preview.refresh_requested.connect(self._refresh_preview)
        self.splitter.addWidget(self.preview)

        # Set splitter sizes (65% editor, 35% preview)
        self.splitter.setSizes([910, 490])

        self.setCentralWidget(self.splitter)

    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()

        # File path label
        self.file_label = QLabel("No file open")
        self.file_label.setStyleSheet("padding: 2px 8px;")
        self.status_bar.addPermanentWidget(self.file_label, stretch=1)

        # Cursor position label
        self.cursor_label = QLabel("Line: 1, Col: 1")
        self.cursor_label.setStyleSheet("padding: 2px 8px;")
        self.status_bar.addPermanentWidget(self.cursor_label)

        self.setStatusBar(self.status_bar)

    # -- Event handlers --

    def _new_album(self):
        """Create a new album."""
        if self.editor.is_modified:
            if not self._prompt_save():
                return

        self._file_path = None
        self.editor.clear()
        self.editor.file_path = None
        self._update_title()
        self._update_actions()
        self.file_label.setText("New album")
        self.preview.clear()

    def _open_file(self):
        """Open an album file."""
        if self.editor.is_modified:
            if not self._prompt_save():
                return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Album File",
            "",
            "Album Files (*.txt);;All Files (*)",
        )

        if file_path:
            self._load_file(file_path)

    def _load_file(self, file_path: str):
        """Load a file into the editor."""
        if self.editor.load_file(file_path):
            self._file_path = file_path
            self._update_title()
            self._update_actions()
            self.file_label.setText(file_path)
            self._add_recent_file(file_path)
            self._refresh_preview()

    def _save_file(self) -> bool:
        """Save the current file."""
        if not self._file_path:
            return self._save_file_as()

        if self.editor.save_file(self._file_path):
            self._update_title()
            return True
        return False

    def _save_file_as(self) -> bool:
        """Save the file with a new name."""
        file_path = self.editor.save_file_as()
        if file_path:
            self._file_path = file_path
            self._update_title()
            self._update_actions()
            self.file_label.setText(file_path)
            return True
        return False

    def _generate_pdf(self):
        """Generate PDF from the current album."""
        # Auto-save if configured
        if self.config.get("editor", {}).get("auto_save", True) and self._file_path:
            self._save_file()

        # Parse the album
        source_text = self.editor.toPlainText()
        try:
            parser = AlbumParser()
            album = parser.parse(source_text, self._file_path)
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to parse album:\n\n{str(e)}")
            return

        if not album.pages:
            QMessageBox.warning(
                self,
                "No Pages",
                "The album has no pages. Add PAGE_START commands to create pages.",
            )
            return

        # Determine output path
        if self._file_path:
            output_path = str(Path(self._file_path).with_suffix(".pdf"))
        else:
            # Save to temp file
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, "stamp_album_preview.pdf")

        # Generate PDF
        try:
            generator = PDFGenerator()
            generator.generate(album, output_path)
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Failed to generate PDF:\n\n{str(e)}")
            return

        self.status_bar.showMessage(f"PDF generated: {output_path}", 5000)

        # Enable view action
        self.act_view_pdf.setEnabled(True)
        self._pdf_path = output_path

        # Auto-open if configured
        if self.config.get("pdf", {}).get("auto_open", True):
            self._view_pdf()

        # Update preview
        self._refresh_preview()

    def _view_pdf(self):
        """Open the generated PDF in the system viewer."""
        if self._pdf_path and Path(self._pdf_path).exists():
            import platform
            import subprocess

            if platform.system() == "Darwin":
                subprocess.run(["open", self._pdf_path])
            elif platform.system() == "Windows":
                os.startfile(self._pdf_path)
            else:
                subprocess.run(["xdg-open", self._pdf_path])
        else:
            QMessageBox.warning(self, "No PDF", "Generate a PDF first.")

    def _toggle_preview(self):
        """Show or hide the preview panel."""
        if self.preview.isVisible():
            self.preview.hide()
            self.act_toggle_preview.setChecked(False)
        else:
            self.preview.show()
            self.act_toggle_preview.setChecked(True)

    def _refresh_preview(self):
        """Refresh the preview panel."""
        try:
            parser = AlbumParser()
            album = parser.parse(self.editor.toPlainText(), self._file_path)
            generator = PDFGenerator()
            html = generator.get_html_preview(album)
            self.preview.set_html_content(html)
        except Exception:
            # Silently ignore preview errors (user is still typing)
            pass

    def _show_templates(self):
        """Show the template gallery."""
        dialog = TemplateGallery(self)
        if dialog.exec():
            if dialog.selected_content:
                self._new_album()
                self.editor.setPlainText(dialog.selected_content)
                self._refresh_preview()

    def _show_settings(self):
        """Show the settings dialog."""
        dialog = ConfigDialog(self, self.config)
        if dialog.exec():
            self.config = dialog.get_config()
            self._apply_config()

    def _show_find_dialog(self):
        """Show a simple find dialog."""
        from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Find")
        dialog.setModal(True)
        dialog.setStyleSheet(APP_STYLESHEET)

        layout = QVBoxLayout(dialog)

        find_edit = QLineEdit()
        find_edit.setPlaceholderText("Search text...")
        layout.addWidget(find_edit)

        button_layout = QHBoxLayout()
        find_btn = QPushButton("Find")
        find_btn.clicked.connect(lambda: self._find_text(find_edit.text()))
        button_layout.addWidget(find_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.show()

    def _find_text(self, text: str):
        """Find text in the editor."""
        if text:
            self.editor.find_text(text)

    def _show_help(self):
        """Show help."""
        QMessageBox.information(
            self,
            "Help",
            "StampAlbum Pro Help\n\n"
            "1. Create a new album or open an existing one\n"
            "2. Edit the album source in the editor\n"
            "3. Click 'Generate PDF' to create the album\n"
            "4. Use 'View PDF' to open the generated file\n\n"
            "Press Ctrl+T to browse templates.",
        )

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About StampAlbum Pro",
            "StampAlbum Pro v0.1.0\n\n"
            "Modern stamp album typesetter with live preview\n"
            "and advanced typography.\n\n"
            "© 2026 Stamp Album Pro Contributors\n"
            "MIT License",
        )

    def _on_modified_changed(self, modified: bool):
        """Handle document modification changes."""
        self._update_title()

    def _on_cursor_position_changed(self, line: int, col: int):
        """Handle cursor position changes."""
        self.cursor_label.setText(f"Line: {line}, Col: {col}")

    def _on_text_changed(self):
        """Handle text changes (for auto-preview)."""
        # Debounced preview update could go here
        pass

    def _update_title(self):
        """Update the window title."""
        if self._file_path:
            name = Path(self._file_path).name
            modified = " * " if self.editor.is_modified else " - "
            self.setWindowTitle(f"{name}{modified}StampAlbum Pro")
        else:
            modified = " *" if self.editor.is_modified else ""
            self.setWindowTitle(f"Untitled{modified} - StampAlbum Pro")

    def _update_actions(self):
        """Update action enabled states."""
        has_file = self._file_path is not None
        self.act_save.setEnabled(has_file)
        self.act_save_as.setEnabled(True)
        self.act_generate.setEnabled(True)

    def _add_recent_file(self, file_path: str):
        """Add a file to the recent files list."""
        if file_path in self._recent_files:
            self._recent_files.remove(file_path)
        self._recent_files.insert(0, file_path)
        self._recent_files = self._recent_files[:10]  # Keep last 10

    def _prompt_save(self) -> bool:
        """Prompt to save if modified."""
        if not self.editor.is_modified:
            return True

        reply = QMessageBox.question(
            self,
            "Save Changes",
            "The current file has unsaved changes. Save?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Save:
            return self._save_file()
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _apply_config(self):
        """Apply configuration changes."""
        editor_config = self.config.get("editor", {})
        self.editor.set_dark_mode(editor_config.get("dark_mode", False))
        self.editor.update_highlighting()

    @property
    def config(self) -> dict:
        """Get the application configuration."""
        return self._config

    @config.setter
    def config(self, value: dict):
        """Set the application configuration."""
        self._config = value
