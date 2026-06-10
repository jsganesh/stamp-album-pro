"""
StampAlbum Pro - Modern stamp album typesetter.

Entry point for the application.
"""

import sys
from pathlib import Path


def main():
    """Main entry point for the application."""
    # Add src to path for development
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Check for CLI mode
    if len(sys.argv) > 1 and sys.argv[1] in ("-c", "--cli"):
        _run_cli(sys.argv[2:])
        return

    # Run GUI mode
    _run_gui()


def _run_gui():
    """Run the graphical user interface."""
    from PyQt6.QtWidgets import QApplication

    from stamp_album.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("StampAlbum Pro")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("StampAlbum")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def _run_cli(args: list[str]):
    """Run in command-line mode."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="stamp-album",
        description="StampAlbum Pro — Modern stamp album typesetter",
        epilog="Examples:\n  stamp-album -c album.txt -o output.pdf\n  stamp-album -c album.txt -p\n  stamp-album --cli --help\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-c", "--cli",
        action="store_true",
        help="Run in CLI mode (auto-detected when other flags are present)",
    )
    parser.add_argument(
        "source_file",
        nargs="?",
        help="Source DSL file (.slbum or .txt)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Output PDF file path (default: same name as source with .pdf)",
    )
    parser.add_argument(
        "-p", "--preview",
        action="store_true",
        help="Also generate an HTML preview file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="StampAlbum Pro v0.1.0",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed parsing information and validation warnings",
    )

    parsed = parser.parse_args(args)

    if not parsed.source_file:
        parser.print_help()
        sys.exit(1)

    if not Path(parsed.source_file).exists():
        print(f"Error: File not found: {parsed.source_file}")
        sys.exit(1)

    # Parse the album
    from stamp_album.core.parser import AlbumParser

    parser_obj = AlbumParser()
    album = parser_obj.parse_file(parsed.source_file)

    print(f"Parsed album: {album.title or 'Untitled'}")
    print(f"Pages: {len(album.pages)}")
    print(f"Fonts: {len(album.fonts)}")

    if parsed.verbose:
        total_stamps = sum(len(row.stamps) for page in album.pages for row in page.rows)
        print(f"Stamps: {total_stamps}")
        print(f"Source: {parsed.source_file}")
        warnings = parser_obj.validate(album)
        if warnings:
            print(f"\nWarnings ({len(warnings)}):")
            for w in warnings:
                print(f"  ⚠ {w}")
        else:
            print("\nNo validation warnings.")
    print()

    # Determine output path
    output_path = parsed.output or str(Path(parsed.source_file).with_suffix(".pdf"))

    # Generate PDF
    from stamp_album.engines.pdf_generator import PDFGenerator

    generator = PDFGenerator()
    generator.generate(album, output_path)

    print(f"PDF generated: {output_path}")

    # Show preview if requested
    if parsed.preview:
        html = generator.get_html_preview(album)
        preview_path = str(Path(output_path).with_suffix(".html"))
        Path(preview_path).write_text(html, encoding="utf-8")
        print(f"HTML preview: {preview_path}")


if __name__ == "__main__":
    main()
