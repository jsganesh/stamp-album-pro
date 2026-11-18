"""Small Pillow helpers shared by the image tests."""


def pixels(im):
    """The image's pixel values, row by row (Pillow 14 removes ``getdata``)."""
    return im.get_flattened_data()
