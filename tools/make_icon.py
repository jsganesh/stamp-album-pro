"""Render the app icon from packaging/icon/StampAlbum.svg.

    python tools/make_icon.py

Writes packaging/icon/StampAlbum.icns (macOS, through `iconutil`, so run it on a
Mac) and StampAlbum.ico (Windows). Run it after changing the SVG, then look at
the icon at 16 px in Finder's list view and commit all three files.
Needs Playwright's Chromium (``playwright install chromium``).
"""

from __future__ import annotations

import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ICON = Path(__file__).resolve().parents[1] / "packaging" / "icon"
SVG = ICON / "StampAlbum.svg"
MASTER = 1024
# iconutil wants these names; each size also has an @2x twin at double the pixels.
ICONSET_SIZES = (16, 32, 128, 256, 512)
ICO_SIZES = [(s, s) for s in (16, 24, 32, 48, 64, 128, 256)]


def render_master() -> Image.Image:
    """The SVG at 1024 px on a transparent background, as Chromium draws it."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": MASTER, "height": MASTER})
        page.set_content(
            f"<style>html,body{{margin:0;background:transparent}}</style>{SVG.read_text()}"
            f"<style>svg{{display:block;width:{MASTER}px;height:{MASTER}px}}</style>"
        )
        png = page.screenshot(omit_background=True)
        browser.close()
    return Image.open(BytesIO(png)).convert("RGBA")


def write_icns(master: Image.Image) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "StampAlbum.iconset"
        iconset.mkdir()
        for size in ICONSET_SIZES:
            for scale, suffix in ((1, ""), (2, "@2x")):
                px = size * scale
                img = master.resize((px, px), Image.LANCZOS)
                img.save(iconset / f"icon_{size}x{size}{suffix}.png")
        out = ICON / "StampAlbum.icns"
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(out)], check=True)


def main() -> None:
    master = render_master()
    write_icns(master)
    master.save(ICON / "StampAlbum.ico", sizes=ICO_SIZES)
    print(f"Wrote {ICON / 'StampAlbum.icns'} and {ICON / 'StampAlbum.ico'}")


if __name__ == "__main__":
    main()
