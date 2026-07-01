# AlbumEasy DSL Command Reference

> Extracted from user's 6 albums (Tristan da Cunha, Bahrain, BAT, Christmas Island, Guernsey, Pakistan)
> These are the commands StampAlbum Pro needs to support for import compatibility.

## Page Setup (Header Section)

| Command | Example | Purpose |
|---------|---------|---------|
| ALBUM_TITLE | `ALBUM_TITLE("Bahrain - First Issues")` | Album name |
| ALBUM_AUTHOR | `ALBUM_AUTHOR("Dr J Saravana Ganesh ...")` | Collector name |
| COLOUR_ALBUM_TITLE | `COLOUR_ALBUM_TITLE(red)` | Title color |
| COLOUR_ALBUM_BORDER | `COLOUR_ALBUM_BORDER(blue)` | Page border color |
| COLOR_ALBUM_FOOTER | `COLOR_ALBUM_FOOTER(Lime)` | Footer color |
| ALBUM_PAGES_SIZE | `ALBUM_PAGES_SIZE(210.0 297.0)` | A4 page dimensions |
| ALBUM_PAGES_MARGINS | `ALBUM_PAGES_MARGINS(15.0 15.0 15.0 15.0)` | L,R,T,B margins |
| ALBUM_PAGES_DECORATIVE_BORDER | `ALBUM_PAGES_DECORATIVE_BORDER("CornerStyleA.txt")` | Corner ornament |
| ALBUM_PAGES_BORDER | `ALBUM_PAGES_BORDER(0.5 0.1 0.0 1.0)` | Border line weights |
| ALBUM_PAGES_SPACING | `ALBUM_PAGES_SPACING(5.0 8.0)` | H,V gap between stamps |
| ALBUM_PAGES_TITLE | `ALBUM_PAGES_TITLE(TN 25 "Bahrain - First Issues")` | Page header text |
| STAMP_BOXES_SIZE_ADJUST | `STAMP_BOXES_SIZE_ADJUST(6.0)` | Mount = stamp + 6mm |
| ALBUM_STAMP_IMG_SETTING | `ALBUM_STAMP_IMG_SETTING(0.4 0.4 True)` | Image scale in mount |

## Row & Page Layout

| Command | Example | Purpose |
|---------|---------|---------|
| PAGE_START_VAR | `PAGE_START_VAR(5.0 10.0)` | New page with margins |
| ROW_ALIGN_BOTTOM | `ROW_ALIGN_BOTTOM` | Align row to bottom |
| ROW_ALIGN_TOP | `ROW_ALIGN_TOP` | Align row to top |
| ROW_START_ES | `ROW_START_ES(TB 6 0.1 5.0)` | Start row: font, gap, spacing |
| PAGE_VSPACE | `PAGE_VSPACE(-3.0)` | Vertical space (negative=tighter) |

## Text Commands

| Command | Example | Purpose |
|---------|---------|---------|
| PAGE_TEXT_CENTRE | `PAGE_TEXT_CENTRE(TB 10 "Title" 1.5)` | Centered text with spacing |
| PAGE_TEXT_PARAGRAPH_START | `PAGE_TEXT_PARAGRAPH_START(TI 10 Justified)` | Begin paragraph block |
| PAGE_TEXT_PARAGRAPH_END | `PAGE_TEXT_PARAGRAPH_END` | End paragraph block |

## Stamp Commands

| Command | Example | Purpose |
|---------|---------|---------|
| STAMP_ADD | `STAMP_ADD(38 28 "" "violet\nSG#1 SC#1" "½p" "A24")` | Empty mount with text |
| STAMP_ADD_IMG | `STAMP_ADD_IMG(30 30 "bahloc.png" "" "" "")` | Mount with image |
| STAMP_HEADING_VA | `STAMP_HEADING_VA(HS 8 "May 1908")` | Heading below mount |
| STAMP_HEADING | `STAMP_HEADING(HS 8 "M.V. Kista Dan")` | Heading (alias) |

## Font Codes

| Code | Meaning |
|------|---------|
| TN | Times New Roman Normal |
| TB | Times New Roman Bold |
| TI | Times New Roman Italic |
| HS | Helvetica Small |

## Text Styles (for paragraphs)

| Style | Meaning |
|-------|---------|
| Justified | Full alignment |
| Centered | Center alignment |
| Left | Left alignment |

## Observations from User's Albums

1. **Every page starts with** country intro: flag + map + coat of arms + location image
2. **Every page has** 150-300 word historical paragraph (TI 10pt Justified)
3. **Every stamp row** has 2-4 stamps with heading below
4. **Catalog numbers** always SG#/SC# format, sometimes Michel
5. **Denomination** format: "½p", "1S", "2Sh6p", "1£"
6. **Perforation codes**: "A1", "A24", "A46", "A83" etc.
7. **Watermark references**: "Wmk. Inv." (inverted), "Wmk 314", "Wmk 251"
8. **Color descriptions**: "dark blue", "carmine rose & black", "prussian blue"
9. **All use A4** (210×297mm) with 15mm margins
10. **Mount oversize**: 6mm (STAMP_BOXES_SIZE_ADJUST(6.0))
