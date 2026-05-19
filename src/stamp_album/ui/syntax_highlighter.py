"""
Syntax highlighter for the StampAlbum Pro DSL.

Provides color-coded highlighting for commands, strings, comments,
and parameters in the album source editor.
"""

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor, QTextDocument


class DSLHighlighter:
    """Syntax highlighter for StampAlbum Pro DSL source files."""

    def __init__(self, document: QTextDocument, dark_mode: bool = False):
        self.document = document
        self.dark_mode = dark_mode
        self._setup_formats()
        self._setup_rules()
        self.highlight()

    def _setup_formats(self):
        """Set up text formats for different token types."""
        if self.dark_mode:
            self._keyword_format = self._make_format(foreground=QColor("#569CD6"), bold=True)
            self._string_format = self._make_format(foreground=QColor("#CE9178"))
            self._comment_format = self._make_format(foreground=QColor("#6A9955"), italic=True)
            self._number_format = self._make_format(foreground=QColor("#B5CEA8"))
            self._paren_format = self._make_format(foreground=QColor("#FFD700"), bold=True)
            self._error_format = self._make_format(foreground=QColor("#F44747"), underline=True)
        else:
            self._keyword_format = self._make_format(foreground=QColor("#0000FF"), bold=True)
            self._string_format = self._make_format(foreground=QColor("#A31515"))
            self._comment_format = self._make_format(foreground=QColor("#008000"), italic=True)
            self._number_format = self._make_format(foreground=QColor("#098658"))
            self._paren_format = self._make_format(foreground=QColor("#FF0000"), bold=True)
            self._error_format = self._make_format(foreground=QColor("#FF0000"), underline=True)

    def _make_format(
        self,
        foreground: QColor | None = None,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
    ) -> QTextCharFormat:
        """Create a QTextCharFormat with the specified properties."""
        fmt = QTextCharFormat()
        if foreground:
            fmt.setForeground(foreground)
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        if underline:
            fmt.setFontUnderline(True)
        return fmt

    def _setup_rules(self):
        """Set up highlighting rules."""
        # DSL commands (start with uppercase or $)
        self._keyword_patterns = [
            r"\b(ALBUM_[A-Z_]+)\b",
            r"\b(PAGE_[A-Z_]+)\b",
            r"\b(ROW_[A-Z_]+)\b",
            r"\b(STAMP_[A-Z_]+)\b",
            r"\b(COLOUR_[A-Z_]+)\b",
            r"\b(COLOR_[A-Z_]+)\b",
            r"\b(TEXT_[A-Z_]+)\b",
            r"\b(STAMP_ADD[A-Z_]*)\b",
            r"(\$[A-Z]+)\b",
        ]

        # Strings in quotes
        self._string_pattern = r'"[^"\\]*(?:\\.[^"\\]*)*"'

        # Comments
        self._comment_pattern = r"#[^\n]*"

        # Numbers
        self._number_pattern = r"\b\d+\.?\d*\b"

        # Parentheses
        self._paren_pattern = r"[()]"

    def highlight(self):
        """Apply syntax highlighting to the document."""
        # Clear all formatting
        cursor = self.document.find("")
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(QTextCharFormat())
        cursor.clearSelection()

        # Apply comment highlighting first (to avoid highlighting inside comments)
        self._highlight_pattern(self._comment_pattern, self._comment_format)

        # Apply string highlighting
        self._highlight_pattern(self._string_pattern, self._string_format)

        # Apply keyword highlighting
        for pattern in self._keyword_patterns:
            self._highlight_pattern(pattern, self._keyword_format)

        # Apply number highlighting
        self._highlight_pattern(self._number_pattern, self._number_format)

        # Apply parenthesis highlighting
        self._highlight_pattern(self._paren_pattern, self._paren_format)

    def _highlight_pattern(self, pattern: str, fmt: QTextCharFormat):
        """Highlight all occurrences of a regex pattern."""
        regex = QRegularExpression(pattern)
        text = self.document.toPlainText()
        match = regex.match(text)

        while match.hasMatch():
            start = match.capturedStart()
            length = match.capturedLength()

            # Check if this position is already inside a comment or string
            if not self._is_inside_format(start, length):
                cursor = self.document.find("")
                cursor.setPosition(start)
                cursor.setPosition(start + length, QTextDocument.MoveMode.KeepAnchor)
                cursor.mergeCharFormat(fmt)

            match = regex.match(text, match.capturedStart() + 1)

    def _is_inside_format(self, start: int, length: int) -> bool:
        """Check if a position is already formatted (to avoid overwriting)."""
        cursor = self.document.find("")
        cursor.setPosition(start)
        fmt = cursor.charFormat()
        return (
            fmt.fontItalic()
            or fmt.fontUnderline()
            or fmt.foreground().color().name()
            in [
                QColor("#008000").name(),  # comment green
                QColor("#6A9955").name(),  # dark comment green
                QColor("#A31515").name(),  # string red
                QColor("#CE9178").name(),  # dark string orange
            ]
        )

    def update_formatting(self):
        """Re-apply all highlighting."""
        self.highlight()
