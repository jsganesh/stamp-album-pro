"""
StampAlbum Pro - Modern stamp album typesetter.

Entry point for the application.
"""

import os
import sys
from pathlib import Path

QT_REMOVED = "The PyQt6 editor was removed. Run `stamp-album` to open the editor."


def _frozen_setup() -> None:
    """Prepare a PyInstaller build before anything else runs.

    A windowed build (no console) starts with sys.stdout and sys.stderr set to
    None, and uvicorn's log formatter calls sys.stdout.isatty(). Older macOS
    versions pass a ``-psn_...`` process serial number when Finder opens an app.
    """
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))
    sys.argv = [sys.argv[0]] + [a for a in sys.argv[1:] if not a.startswith("-psn_")]


def main():
    """Main entry point for the application."""
    frozen = getattr(sys, "frozen", False)
    if frozen:
        _frozen_setup()
    else:
        # Add src to path for development
        src_path = Path(__file__).parent.parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

    # CLI mode (headless PDF generation)
    if len(sys.argv) > 1 and sys.argv[1] in ("-c", "--cli"):
        _run_cli(sys.argv[2:])
        return

    # The PyQt6 editor was removed; say so instead of starting something else.
    if len(sys.argv) > 1 and sys.argv[1] in ("--legacy-qt", "--qt"):
        print(QT_REMOVED, file=sys.stderr)
        sys.exit(1)

    # Browser mode (explicit)
    if len(sys.argv) > 1 and sys.argv[1] in ("--web", "-w"):
        from stamp_album.serve import main as serve_main
        sys.exit(serve_main())

    # Dev mode: enable auto-reload on file changes for rapid iteration
    if len(sys.argv) > 1 and sys.argv[1] in ("--dev", "-d"):
        os.environ["STAMP_ALBUM_RELOAD"] = "1"
        from stamp_album.serve import main as serve_main
        sys.exit(serve_main())

    # Default: serve the web app and open it in the user's browser.
    # Browser mode gives the simplest UX — exports download to the user's
    # Downloads folder, no window trapping, no extra dependencies.
    if len(sys.argv) > 1 and sys.argv[1] in ("--desktop", "--window"):
        try:
            from stamp_album.desktop import main as desktop_main
            sys.exit(desktop_main())
        except ImportError:
            print("ERROR: pywebview is required for desktop mode.", file=sys.stderr)
            sys.exit(1)

    # The installed app (a PyInstaller build) opens its own window by default.
    if frozen and len(sys.argv) == 1:
        # Without pywebview there would be no window, so use the browser.
        try:
            import webview  # noqa: F401

            from stamp_album.desktop import main as desktop_main
        except ImportError:
            pass
        else:
            sys.exit(desktop_main())

    from stamp_album.serve import main as serve_main
    sys.exit(serve_main())


def _run_cli(args: list[str]):
    """Run in command-line mode."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="stamp-album",
        description="StampAlbum Pro — Modern stamp album typesetter",
        epilog=(
            "Examples:\n"
            "  stamp-album -c album.txt -o output.pdf\n"
            "  stamp-album -c album.txt -p\n"
            "  stamp-album --cli --help\n"
        ),
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
        version="StampAlbum Pro v0.3.1",
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
    from stamp_album.engines.pdf import PDFGenerator

    PDFGenerator().generate(album, output_path)

    print(f"PDF generated: {output_path}")

    if parsed.preview:
        from stamp_album.engines.html_renderer import HTMLRenderer
        html = HTMLRenderer(album, None).render()
        preview_path = str(Path(output_path).with_suffix(".html"))
        Path(preview_path).write_text(html, encoding="utf-8")
        print(f"HTML preview: {preview_path}")


if __name__ == "__main__":
    main()
