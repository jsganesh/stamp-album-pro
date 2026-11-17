"""A picture whose bytes are not one of the accepted formats is refused, whatever its name.

Pillow picks the decoder from the contents, so a shared album could carry a ".png"
that is really another format and reach that decoder. PCX stands in for the risky
ones (FlashPix, PSD, ...): Pillow can write it and would happily read it back.
"""
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image, UnidentifiedImageError

from stamp_album.api import app
from stamp_album.engines import user_images

RED = (200, 30, 30)


@pytest.fixture()
def images(tmp_path, monkeypatch):
    folder = tmp_path / "StampAlbum" / "images"
    folder.mkdir(parents=True)
    Image.new("RGB", (60, 80), RED).save(folder / "real.png")
    Image.new("RGB", (60, 80), RED).save(folder / "disguised.png", format="PCX")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    from stamp_album import storage
    monkeypatch.setattr(storage, "FILES_DIR", tmp_path / "StampAlbum")
    monkeypatch.setattr(storage, "IMAGES_DIR", folder)
    return folder


def _export(name, fmt):
    state = {
        "elements": [{"t": "image", "s": "rectangle", "x": 50, "y": 50, "w": 100, "h": 120,
                      "img": name, "bdr": "none", "fill": "transparent"}],
        "pages": [], "page_width_px": 525, "page_height_px": 742.5, "scale": 2.5,
        "format": fmt, "source_path": "t.slbum",
    }
    r = TestClient(app).post("/export-from-state", json=state)
    assert r.status_code == 200
    return r.content


def test_open_image_refuses_a_png_name_holding_another_format(images):
    Image.open(images / "disguised.png").close()  # unrestricted Pillow would decode it
    with pytest.raises(UnidentifiedImageError):
        user_images.open_image(images / "disguised.png")
    with user_images.open_image(images / "real.png") as im:
        assert im.format == "PNG"


def test_pdf_export_leaves_the_disguised_picture_out(images):
    assert b"/Subtype /Image" in _export("real.png", "pdf")
    assert b"/Subtype /Image" not in _export("disguised.png", "pdf")


def _red_pixels(png_bytes):
    with Image.open(io.BytesIO(png_bytes)) as im:
        return sum(1 for p in im.convert("RGB").get_flattened_data() if p == RED)


def test_png_export_leaves_the_disguised_picture_out(images):
    assert _red_pixels(_export("real.png", "png")) > 1000
    assert _red_pixels(_export("disguised.png", "png")) == 0
