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

    print("StampAlbum Pro v0.1.0")
    print("=" * 40)
    print()
    print("Usage:")
    print("  stamp-album [options] <source_file>")
    print()
    print("Options:")
    print("  -o, --output <file>   Output PDF file path")
    print("  -p, --preview         Show HTML preview")
    print("  -h, --help            Show this help message")
    print()

    if len(sys.argv) < 2:
        print("No source file specified.")
        sys.exit(1)

    source_file = sys.argv[-1]

    if not Path(source_file).exists():
        print(f"Error: File not found: {source_file}")
        sys.exit(1)

    # Parse the album
    from stamp_album.core.parser import AlbumParser

    parser = AlbumParser()
    album = parser.parse_file(source_file)

    print(f"Parsed album: {album.title or 'Untitled'}")
    print(f"Pages: {len(album.pages)}")
    print(f"Fonts: {len(album.fonts)}")
    print()

    # Determine output path
    output_path = None
    for i, arg in enumerate(sys.argv):
        if arg in ("-o", "--output") and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
            break

    if output_path is None:
        output_path = str(Path(source_file).with_suffix(".pdf"))

    # Generate PDF
    from stamp_album.engines.pdf_generator import PDFGenerator

    generator = PDFGenerator()
    generator.generate(album, output_path)

    print(f"PDF generated: {output_path}")

    # Show preview if requested
    if "-p" in sys.argv or "--preview" in sys.argv:
        html = generator.get_html_preview(album)
        preview_path = str(Path(output_path).with_suffix(".html"))
        Path(preview_path).write_text(html, encoding="utf-8")
        print(f"HTML preview: {preview_path}")


if __name__ == "__main__":
    main()
