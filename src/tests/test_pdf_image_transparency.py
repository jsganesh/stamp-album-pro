"""Transparent PNGs must keep their transparency in PDF export (not turn black)."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from stamp_album.api import app


@pytest.fixture()
def home_with_images(tmp_path, monkeypatch):
    images = tmp_path / "StampAlbum" / "images"
    images.mkdir(parents=True)
    rgba = Image.new("RGBA", (60, 80), (0, 0, 0, 0))
    for x in range(10, 50):
        for y in range(10, 70):
            rgba.putpixel((x, y), (200, 30, 30, 255))
    rgba.save(images / "arms_rgba.png")
    Image.new("RGB", (60, 80), (200, 30, 30)).save(images / "arms_rgb.png")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    return images


def _pdf(name):
    state = {
        "elements": [{"t": "image", "s": "rectangle", "x": 50, "y": 50, "w": 100, "h": 120,
                      "img": name, "bdr": "none", "fill": "transparent"}],
        "pages": [], "page_width_px": 525, "page_height_px": 742.5, "scale": 2.5,
        "format": "pdf", "source_path": "t.slbum",
    }
    r = TestClient(app).post("/export-from-state", json=state)
    assert r.status_code == 200
    return r.content


def test_rgba_image_gets_a_soft_mask(home_with_images):
    assert b"/SMask" in _pdf("arms_rgba.png")


def test_opaque_image_has_no_mask(home_with_images):
    assert b"/SMask" not in _pdf("arms_rgb.png")
