# QA: system-fonts and caption-typing (2026-10-24)

- New tests: `test_system_fonts.py` (10), `test_font_list_ui.py` (4), `test_caption_typing.py` (10).
  Export and Font-list tests fail on `main`; finder unit tests cover the new module.
- First full run on both branches together: 2 failures, both fixed —
  `test_caption_fonts::test_png_captions_do_not_depend_on_system_fonts` patched the removed
  `raster._get_system_font_dirs` (now patches `system_fonts.font_dirs`);
  `test_themes_ui::test_heading_tick_box_marks_and_unmarks` caught Undo re-sending a focused tick
  box's change (caption-typing now counts only typed boxes; regression test added).
- By hand: PDF with DejaVu Serif and FreeMono embeds both (`pdffonts`), unknown font → Helvetica.
- Not covered by CI: macOS `/System/Library/Fonts/Supplemental` and Windows folders (owner checks
  on the Mac); a real `.otf` (CFF) font being left out (logic: no `glyf` table).
