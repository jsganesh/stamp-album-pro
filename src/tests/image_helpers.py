"""Small Pillow helpers shared by the image tests."""


def pixels(im):
    """The image's pixel values, row by row.

    Pillow 12.1 added ``get_flattened_data`` and Pillow 14 removes ``getdata``;
    the project still allows Pillow 10, so fall back on older versions.
    """
    if hasattr(im, "get_flattened_data"):
        return im.get_flattened_data()
    return im.getdata()
