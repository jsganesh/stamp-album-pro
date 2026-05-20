from future import annotations
from typing import Optional, Dict, Any
import dataclasses

from stamp_album.core.models import Album, Page, Row, Stamp
from stamp_album.core.parser import AlbumParser

class AlbumSerializer:
	"""
	Handles the conversion between Album models and DSL text.
	This allows the Visual Builder to modify the model and 'save' it back to DSL.
	"""

	def init(self):
		self.parser = AlbumParser()

	def to_dsl(self, album: Album) -> str:
		lines = []

		if album.title:
			lines.append(f'ALBUM_TITLE("{album.title}")')
		if album.author:
			lines.append(f'ALBUM_AUTHOR("{album.author}")')

        ps = album.page_setup
		lines.append(f'ALBUM_PAGES_SIZE({ps.width}, {ps.height})')
		lines.append(f'ALBUM_PAGES_MARGINS({ps.margin_left}, {ps.margin_right}, {ps.margin_top}, {ps.margin_bottom})')

		if ps.has_border:
			lines.append(f'ALBUM_PAGES_BORDER({ps.border_outer}, {ps.border_inner1}, {ps.border_inner2}, {ps.border_spacing})')

        for font in album.fonts:
			lines.append(f'ALBUM_DEFINE_FONT("{font.font_id}", "{font.font_name}")')

        for page in album.pages:
			lines.append('PAGE_START')
            for text in page.text_elements:
				align = text.alignment.value.upper()
				lines.append(f'PAGE_TEXT_{align}("{text.font_id}", {text.size}, "{text.content}", {text.vspace})')

			for row in page.rows:
				lines.append(f'STAMP_ROW({row.style.value}, {row.spacing})')
				for stamp in row.stamps:
					lines.append(f'  STAMP({stamp.width}, {stamp.height}, "{stamp.description}")')
			lines.append('PAGE_END')

		return "\n".join(lines)

	def update_stamp_position(self, dsl: str, page_idx: int, row_idx: int, stamp_idx: int, new_width: float, new_height: float) -> str:
		album = self.parser.parse(dsl)
		if page_idx < len(album.pages):
			page = album.pages[page_idx]
			if row_idx < len(page.rows):
				row = page.rows[row_idx]
				if stamp_idx < len(row.stamps):
					stamp = row.stamps[stamp_idx]
					stamp.width = new_width
					stamp.height = new_height
		return self.to_dsl(album)
