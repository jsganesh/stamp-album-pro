"""
Code editor widget for StampAlbum Pro DSL source files.

Features:
- Line numbers
- Syntax highlighting
- Current line highlighting
- Find/replace
- Auto-indent
"""

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QTextCharFormat,
    QTextDocument,
)
from PyQt6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)

from stamp_album.ui.syntax_highlighter import DSLHighlighter


class LineNumberArea(QWidget):
    """Widget that displays line numbers alongside the editor."""

    def __init__(self, editor: "AlbumEditor"):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor._line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor._line_number_area_paint_event(event)


class AlbumEditor(QPlainTextEdit):
    """
    Code editor for StampAlbum Pro DSL source files.

    Provides line numbers, syntax highlighting, and other editor features.
    """

    # Signals
    modification_changed = pyqtSignal(bool)
    cursor_position_changed = pyqtSignal(int, int)

    def __init__(self, parent: QWidget | None = None, dark_mode: bool = False):
        super().__init__(parent)
        self._dark_mode = dark_mode
        self._file_path: str | None = None
        self._highlighter: DSLHighlighter | None = None

        self._setup_editor()
        self._setup_line_numbers()
        self._setup_highlighter()
        self._setup_connections()

    def _setup_editor(self):
        """Configure the editor appearance and behavior."""
        # Use monospace font
        font = QFont("Menlo" if self._is_macos() else "Consolas", 12)
        font.setFixedPitch(True)
        self.setFont(font)

        # Tab settings
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
        self.setTabChangesFocus(False)

        # Line wrap
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Margins
        self._setup_margins()

        # Apply dark mode styling
        self._apply_editor_style()

    def _is_macos(self) -> bool:
        """Check if running on macOS."""
        import platform

        return platform.system() == "Darwin"

    def _setup_margins(self):
        """Set up editor margins."""
        margin = 4
        self.setViewportMargins(self._line_number_area_width(), 0, margin, 0)

    def _apply_editor_style(self):
        """Apply dark or light mode styling to the editor."""
        if self._dark_mode:
            self.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #1E1E1E;
                    color: #D4D4D4;
                    border: none;
                    selection-background-color: #264F78;
                }
                """)
            palette = self.palette()
            palette.setColor(palette.ColorRole.Base, QColor("#1E1E1E"))
            palette.setColor(palette.ColorRole.Text, QColor("#D4D4D4"))
            self.setPalette(palette)
        else:
            self.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #FFFFFF;
                    color: #000000;
                    border: none;
                    selection-background-color: #ADD6FF;
                }
                """)
            palette = self.palette()
            palette.setColor(palette.ColorRole.Base, QColor("#FFFFFF"))
            palette.setColor(palette.ColorRole.Text, QColor("#000000"))
            self.setPalette(palette)

    def _setup_line_numbers(self):
        """Set up the line number area."""
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)

    def _setup_highlighter(self):
        """Set up syntax highlighting."""
        self._highlighter = DSLHighlighter(self.document(), self._dark_mode)

    def _setup_connections(self):
        """Connect editor signals."""
        self.cursorPositionChanged.connect(self._on_cursor_position_changed)
        self.modificationChanged.connect(self.modification_changed.emit)

    def _line_number_area_width(self) -> int:
        """Calculate the width needed for the line number area."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1

        space = 3 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def _update_line_number_area_width(self):
        """Update the line number area width when block count changes."""
        self.setViewportMargins(self._line_number_area_width(), 0, 4, 0)

    def _update_line_number_area(self, rect, dy):
        """Update the line number area when text changes."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def _line_number_area_paint_event(self, event):
        """Paint the line number area."""
        painter = QPainter(self.line_number_area)

        if self._dark_mode:
            painter.fillRect(event.rect(), QColor("#1E1E1E"))
            painter.setPen(QColor("#858585"))
        else:
            painter.fillRect(event.rect(), QColor("#F0F0F0"))
            painter.setPen(QColor("#808080"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0,
                    int(top),
                    self.line_number_area.width() - 2,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            cr.left(), cr.top(), self._line_number_area_width(), cr.height()
        )

    def _on_cursor_position_changed(self):
        """Handle cursor position changes."""
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber()
        self.cursor_position_changed.emit(line, col)

    def _highlight_current_line(self):
        """Highlight the current line."""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            if self._dark_mode:
                line_color = QColor("#2A2A2A")
            else:
                line_color = QColor("#E8E8E8")

            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def load_file(self, file_path: str) -> bool:
        """Load a file into the editor."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.setPlainText(content)
            self._file_path = file_path
            self.document().setModified(False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{file_path}\n\n{str(e)}")
            return False

    def save_file(self, file_path: str | None = None) -> bool:
        """Save the current content to a file."""
        path = file_path or self._file_path
        if not path:
            return False

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())
            self.document().setModified(False)
            self._file_path = path
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{path}\n\n{str(e)}")
            return False

    def save_file_as(self) -> str | None:
        """Show save dialog and save file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Album File",
            self._file_path or "",
            "Album Files (*.txt);;All Files (*)",
        )

        if file_path:
            if self.save_file(file_path):
                return file_path
        return None

    @property
    def file_path(self) -> str | None:
        """Get the current file path."""
        return self._file_path

    @file_path.setter
    def file_path(self, path: str | None):
        """Set the current file path."""
        self._file_path = path

    @property
    def is_modified(self) -> bool:
        """Check if the document has been modified."""
        return self.document().isModified()

    def update_highlighting(self):
        """Re-apply syntax highlighting."""
        if self._highlighter:
            self._highlighter.update_formatting()

    def set_dark_mode(self, enabled: bool):
        """Enable or disable dark mode."""
        self._dark_mode = enabled
        self._apply_editor_style()
        if self._highlighter:
            self._highlighter = DSLHighlighter(self.document(), self._dark_mode)

    def find_text(self, text: str, case_sensitive: bool = False) -> bool:
        """Find text in the document."""
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        found = self.find(text, flags)
        return found

    def replace_text(self, find_text: str, replace_text: str, case_sensitive: bool = False) -> int:
        """Replace all occurrences of text."""
        content = self.toPlainText()
        if not case_sensitive:
            count = content.lower().count(find_text.lower())
            content = content.replace(find_text, replace_text)
        else:
            count = content.count(find_text)
            content = content.replace(find_text, replace_text)

        self.setPlainText(content)
        return count
