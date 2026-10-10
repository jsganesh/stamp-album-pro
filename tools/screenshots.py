"""Regenerate the tutorial pictures and the README screenshots from the running app.

    python tools/screenshots.py        (or: make screenshots)

Starts the app on a free port, loads the tutorial's sample album in Chromium
(Playwright) and writes:

* src/stamp_album/web/tutorial-1-add.png … tutorial-4-export.png (520 x 260 CSS px, at 2x)
* docs/screenshots/01-main-editor.png and 04-dsl-editor.png

Run it after a change to the editor's look, then check the pictures and commit them.
Needs Playwright's Chromium (``playwright install chromium``).
"""

from __future__ import annotations

import socket
import sys
import threading
import time
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import uvicorn  # noqa: E402
from PIL import Image  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from stamp_album.api import app  # noqa: E402

WEB = ROOT / "src" / "stamp_album" / "web"
DOCS = ROOT / "docs" / "screenshots"
DSF = 2  # device pixels per CSS pixel
TUTORIAL_SIZE = (520 * DSF, 260 * DSF)
BACKGROUND = (250, 248, 243)  # --bg1


def _serve() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return port
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("the app did not start")


def _box(page, selector):
    b = page.locator(selector).first.bounding_box()
    return b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"]


def _page_mm(page, x0, y0, x1, y1):
    """A box given in page millimetres, in CSS px of the window."""
    left, top, _, _ = _box(page, "#page")
    sc = page.evaluate("StampAlbum._sc")
    return left + x0 * sc, top + y0 * sc, left + x1 * sc, top + y1 * sc


def _shot(page) -> Image.Image:
    return Image.open(BytesIO(page.screenshot())).convert("RGB")


def _crop(img, box, pad=0):
    x0, y0, x1, y1 = box
    return img.crop(tuple(round(v * DSF) for v in (x0 - pad, y0 - pad, x1 + pad, y1 + pad)))


def _fit(parts, size=TUTORIAL_SIZE, gap=16 * DSF, margin=14 * DSF):
    """Lay crops side by side, scaled to fit *size*, centred on the app's background."""
    w, h = size
    total_w = sum(p.width for p in parts) + gap * (len(parts) - 1)
    tall = max(p.height for p in parts)
    k = min((w - 2 * margin) / total_w, (h - 2 * margin) / tall, 1.0)
    out = Image.new("RGB", size, BACKGROUND)
    x = round((w - total_w * k) / 2)
    for p in parts:
        q = p.resize((max(1, round(p.width * k)), max(1, round(p.height * k))), Image.LANCZOS)
        out.paste(q, (x, round((h - q.height) / 2)))
        x += q.width + round(gap * k)
    return out


def _stack(rows, gap=12 * DSF):
    """Crops (or rows of crops) one above the other, left-aligned, at their own scale."""
    rows = [r if isinstance(r, Image.Image) else _row(r, gap) for r in rows]
    out = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows) + gap * (len(rows) - 1)),
                    BACKGROUND)
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height + gap
    return out


def _row(parts, gap):
    out = Image.new("RGB", (sum(p.width for p in parts) + gap * (len(parts) - 1), max(p.height for p in parts)),
                    BACKGROUND)
    x = 0
    for p in parts:
        out.paste(p, (x, 0))
        x += p.width + gap
    return out


def _save(img: Image.Image, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.quantize(colors=256, method=Image.Quantize.FASTOCTREE).save(path, optimize=True)
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)")


def main():
    port = _serve()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=DSF)
        page.add_init_script("try { localStorage.setItem('stampalbum-tutorial-done', '1'); } catch (e) {}")
        page.goto(f"http://127.0.0.1:{port}/")
        page.wait_for_function("window.StampAlbum && document.getElementById('page')")
        page.evaluate("""() => {
            StampAlbum.newAlbum();
            StampAlbum.loadSampleAlbum();
            StampAlbum.select(StampAlbum.E.find(e => e.lbl === 'Penny Black').id);
            document.activeElement && document.activeElement.blur();
        }""")
        # No hover outlines, size labels or empty-panel hint in the pictures
        page.add_style_tag(content=".cel .dim { display: none !important; } #rp-none { visibility: hidden; }")
        page.mouse.move(5, 890)
        page.wait_for_timeout(400)
        full = _shot(page)

        # 1. A stamp at its catalogue size, and the sizes in Properties
        stamp = _crop(full, _page_mm(page, 40, 40, 82, 104))
        props_top = _box(page, "#rp .rp-sec")[1]
        props = _crop(full, (_box(page, "#rp")[0], props_top, _box(page, "#rp")[2], _box(page, "#pframe-size")[3] + 4))
        _save(_fit([stamp, props]), WEB / "tutorial-1-add.png")

        # 2. Frames and captions on the sample page
        page.evaluate("StampAlbum.select(null)")
        page.wait_for_timeout(200)
        full = _shot(page)
        _save(_fit([_crop(full, _page_mm(page, 38, 38, 172, 102))]), WEB / "tutorial-2-captions.png")

        # 3. The bar above the page (Page, then Page border and Theme) over the top of the page
        bar = _box(page, "#ca-toolbar")
        page_btn = _box(page, "#btn-page-setup")
        border_sel, theme_sel = _box(page, "#def-bdr"), _box(page, "#def-theme")
        left = _crop(full, (bar[0], bar[1], page_btn[2] + 8, bar[3]))
        right = _crop(full, (border_sel[0] - 92, bar[1], theme_sel[2] + 8, bar[3]))
        sheet = _crop(full, _page_mm(page, 0, 0, 210, 44))
        _save(_fit([_stack([[left, right], sheet])]), WEB / "tutorial-3-page.png")

        # 4. Preview and the Export menu
        page.click("#btn-export")
        page.wait_for_timeout(250)
        full = _shot(page)
        menu = page.evaluate("""() => {
            const m = [...document.querySelectorAll('#btn-export-dd [role=menu], #btn-export-dd .export-menu, #btn-export-dd ul, #btn-export-dd div')]
                .filter(n => n.offsetParent && n.getBoundingClientRect().height > 40)[0];
            const b = (m || document.getElementById('btn-export')).getBoundingClientRect();
            return [b.left, b.top, b.right, b.bottom];
        }""")
        prev = _box(page, "#btn-preview")
        right = max(_box(page, "#btn-export-dd")[2], menu[2]) + 24
        region = (min(prev[0], menu[0]) - 24, prev[1] - 10, right, menu[3] + 12)
        _save(_fit([_crop(full, region)]), WEB / "tutorial-4-export.png")
        page.keyboard.press("Escape")
        page.mouse.click(5, 890)

        # README: the editor, and the DSL editor
        page.evaluate("StampAlbum.select(StampAlbum.E.find(e => e.lbl === 'Penny Black').id)")
        page.mouse.move(5, 890)
        page.wait_for_timeout(300)
        _save(_shot(page), DOCS / "01-main-editor.png")
        page.click("#menu-view-btn")
        page.click("#btn-dsl")
        page.wait_for_timeout(400)
        _save(_shot(page), DOCS / "04-dsl-editor.png")
        browser.close()


if __name__ == "__main__":
    main()
