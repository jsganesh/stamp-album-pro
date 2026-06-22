"""
Font management system.

Handles scanning, validation, and mapping of system and bundled fonts.
Uses fonttools for TTF/TTC parsing and validation.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fontTools.ttLib import TTFont


@dataclass
class FontInfo:
    """Information about a discovered font."""

    name: str
    file_path: Path
    file_name: str
    font_index: int = -1  # -1 for TTF, >= 0 for TTC
    is_valid: bool = True
    error_message: str = ""
    is_variable: bool = False
    variable_axes: list = field(default_factory=list)


class FontManager:
    """
    Manages font discovery, validation, and lookup.

    Scans system font directories and bundled fonts, validates
    TrueType/OpenType files, and provides lookup by name.
    """

    # Required tables for a valid TTF file
    REQUIRED_TABLES = {
        "OS/2",
        "cmap",
        "glyf",
        "head",
        "hhea",
        "hmtx",
        "loca",
        "maxp",
        "name",
        "post",
    }

    def __init__(self):
        self._fonts: list[FontInfo] = []
        self._bad_fonts: list[str] = []
        self._font_map: dict[str, FontInfo] = {}
        self._bundled_font_dir: Optional[Path] = None
        self._include_system_fonts = True

    @property
    def fonts(self) -> list[FontInfo]:
        """Return list of discovered fonts."""
        return self._fonts

    @property
    def font_map(self) -> dict[str, FontInfo]:
        """Return font name → FontInfo lookup map."""
        return self._font_map

    def set_bundled_font_dir(self, path: Path) -> None:
        """Set the directory containing bundled fonts."""
        self._bundled_font_dir = path

    def set_include_system_fonts(self, include: bool) -> None:
        """Enable or disable system font scanning."""
        self._include_system_fonts = include

    def scan_fonts(self) -> None:
        """Scan for available fonts."""
        self._fonts.clear()
        self._bad_fonts.clear()
        self._font_map.clear()

        paths = self._get_font_paths()

        for path in paths:
            self._scan_font_file(path)

        # Build lookup map
        for font in self._fonts:
            if font.name not in self._font_map:
                self._font_map[font.name] = font

    def _get_font_paths(self) -> list[Path]:
        """Get list of directories to scan for fonts."""
        paths = []

        # Bundled fonts
        if self._bundled_font_dir and self._bundled_font_dir.exists():
            paths.append(self._bundled_font_dir)

        # System fonts
        if self._include_system_fonts:
            paths.extend(self._get_system_font_dirs())

        return paths

    def _get_system_font_dirs(self) -> list[Path]:
        """Get system-specific font directories."""
        system = platform.system()
        dirs = []

        if system == "Darwin":  # macOS
            dirs.extend(
                [
                    Path("/Library/Fonts"),
                    Path.home() / "Library/Fonts",
                    Path("/System/Library/Fonts"),
                ]
            )
        elif system == "Linux":
            dirs.extend(
                [
                    Path("/usr/share/fonts"),
                    Path("/usr/local/share/fonts"),
                    Path.home() / ".fonts",
                    Path.home() / ".local/share/fonts",
                ]
            )
        elif system == "Windows":
            dirs.extend(
                [
                    Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts",
                    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
                ]
            )

        return [d for d in dirs if d.exists()]

    def _scan_font_file(self, directory: Path) -> None:
        """Scan a directory for font files."""
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith((".ttf", ".ttc", ".otf")):
                    file_path = Path(root) / filename
                    self._parse_font_file(file_path)

    def _parse_font_file(self, file_path: Path) -> None:
        """Parse a single font file and extract font info."""
        try:
            if file_path.suffix.lower() == ".ttc":
                self._parse_ttc(file_path)
            else:
                self._parse_ttf(file_path)
        except Exception:
            self._bad_fonts.append(str(file_path))

    def _parse_ttf(self, file_path: Path) -> None:
        """Parse a TrueType font file."""
        try:
            font = TTFont(str(file_path))

            # Check required tables
            tables = set(font.keys())
            missing = self.REQUIRED_TABLES - tables
            if missing:
                self._bad_fonts.append(str(file_path))
                return

            # Get font name from name table
            name = self._get_font_name(font)
            if not name:
                self._bad_fonts.append(str(file_path))
                return

            # Clean up name
            name = name.strip()
            if name.endswith("Regular"):
                name = name[:-7].rstrip(" -")

            font_info = FontInfo(
                name=name,
                file_path=file_path,
                file_name=file_path.name,
                font_index=-1,
            )
            self._fonts.append(font_info)

            # Check for variable font (fvar table)
            if 'fvar' in font:
                font_info.is_variable = True
                try:
                    fvar = font['fvar']
                    for axis in fvar.axes:
                        font_info.variable_axes.append({
                            'name': axis.axisNameID,
                            'tag': axis.axisTag,
                            'min': axis.minValue,
                            'max': axis.maxValue,
                            'default': axis.defaultValue,
                        })
                except Exception:
                    pass
            font.close()
        except Exception:
            self._bad_fonts.append(str(file_path))

    def _parse_ttc(self, file_path: Path) -> None:
        """Parse a TrueType Collection file."""
        try:
            font = TTFont(str(file_path))

            # TTC files contain multiple fonts
            for i, font_name in enumerate(font.getGlyphOrder()):
                # Get name from name table for this font
                name = self._get_font_name(font)
                if name:
                    name = name.strip()
                    if name.endswith("Regular"):
                        name = name[:-7].rstrip(" -")

                    font_info = FontInfo(
                        name=name,
                        file_path=file_path,
                        file_name=file_path.name,
                        font_index=i,
                    )
                    self._fonts.append(font_info)

            # Check for variable font (fvar table)
            if 'fvar' in font:
                font_info.is_variable = True
                try:
                    fvar = font['fvar']
                    for axis in fvar.axes:
                        font_info.variable_axes.append({
                            'name': axis.axisNameID,
                            'tag': axis.axisTag,
                            'min': axis.minValue,
                            'max': axis.maxValue,
                            'default': axis.defaultValue,
                        })
                except Exception:
                    pass
            font.close()
        except Exception:
            self._bad_fonts.append(str(file_path))

    def _get_font_name(self, font: TTFont) -> Optional[str]:
        """Extract the font name from the name table."""
        if "name" not in font:
            return None

        name_table = font["name"]

        # Try to get the font name (nameID 4)
        for record in name_table.names:
            if record.nameID == 4:
                try:
                    return record.toUnicode()
                except Exception:
                    continue

        return None

    def find_font(self, name: str) -> Optional[FontInfo]:
        """Find a font by name (case-insensitive)."""
        for font in self._fonts:
            if font.name.lower() == name.lower():
                return font
        return None

    def get_font(self, name: str) -> Optional[FontInfo]:
        """Get font info by exact or case-insensitive name."""
        if name in self._font_map:
            return self._font_map[name]

        # Case-insensitive fallback
        for font_name, font_info in self._font_map.items():
            if font_name.lower() == name.lower():
                return font_info

        return None

    @property
    def fonts(self) -> list[FontInfo]:
        """Get list of all valid fonts."""
        return self._fonts

    @property
    def bad_fonts(self) -> list[str]:
        """Get list of invalid font file paths."""
        return self._bad_fonts

    @property
    def font_names(self) -> list[str]:
        """Get list of all font names."""
        return [f.name for f in self._fonts]

    def validate_font(self, file_path: str) -> tuple[bool, str]:
        """
        Validate a font file.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            font = TTFont(file_path)
            tables = set(font.keys())
            missing = self.REQUIRED_TABLES - tables

            if missing:
                return False, f"Missing tables: {', '.join(missing)}"

            name = self._get_font_name(font)
            if not name:
                return False, "No font name found in name table"

            font.close()
            return True, ""
        except Exception as e:
            return False, str(e)
