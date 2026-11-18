"""Opening pictures that users attach or that arrive inside shared albums.

Pillow chooses a decoder from the file's bytes, not its name, so a ".png" that is
really FlashPix or PSD would reach that decoder. Both engines open user pictures
here, restricted to the formats storage accepts by suffix.
"""
from __future__ import annotations

from PIL import Image
from reportlab.lib.utils import ImageReader

from stamp_album import storage

ALLOWED_FORMATS = tuple(sorted({Image.registered_extensions()[s] for s in storage.IMAGE_SUFFIXES}))


def open_image(fp) -> Image.Image:
    """Image.open limited to ALLOWED_FORMATS; anything else raises UnidentifiedImageError."""
    return Image.open(fp, formats=ALLOWED_FORMATS)


class UserImageReader(ImageReader):
    """ReportLab's reader with the same restriction. Subclassing its _read_image hook
    keeps ReportLab's JPEG pass-through, which re-encoding a decoded image would lose."""

    def _read_image(self, fp):
        return open_image(fp)
