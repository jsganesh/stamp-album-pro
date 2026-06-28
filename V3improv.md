# V3 Philatelic Template & UI Overhaul — Improvement Plan

> **Branch:** `v3-philatelic-templates`
> **Date:** 2026-06-28
> **Author:** Dr J Saravana Ganesh + Holmes (AI)
> **Status:** Planning — ready for phased execution
> **Reference:** User's existing AlbumEasy albums (6 countries, ~80 pages of real philatelic content)

---

## 0. Executive Summary

StampAlbum Pro v2 is a capable drawing tool but it does not look or feel like a *stamp collector's* app.
The canvas is dark, the templates are empty grids, and the DSL parser understands only a subset of the
commands that real philatelic album software (AlbumEasy) generates. This plan defines a **v3 overhaul**
that makes the app:

1. **Authentically philatelic** — templates match FIP exhibition standards and AlbumEasy's DSL vocabulary
2. **Respectful of the audience** — older collectors need larger fonts, high contrast, clear labels, no dark-mode chic
3. **DSL-compatible** — import the user's existing `.txt` AlbumEasy files directly, preserving years of work
4. **Template-rich** — 15+ realistic page layouts with proper stamp mounts, catalog numbers, and narrative text

---

## 1. Reference: User's Existing Albums (Critical Input)

The user has **6 complete country albums** created in AlbumEasy, totaling ~80 pages of real philatelic content:

| Folder | Country | Pages | DSL File | Key Features |
|--------|---------|-------|----------|--------------|
| `Tristan da Cunha` | TDC | 13+ | `tdc.txt` (8.5KB) | Cachet types, volcano eruption issues, watermark pages |
| `Bahrain` | Bahrain | 8+ | `Bahrain.txt` (8.2KB) | Overprint types, Indian postal history, cancellation marks |
| `British Antarctic Territory` | BAT | 6+ | `BritishAntarcticTerritory.txt` (7.5KB) | First issue 15-value set, definitive series |
| `Christmas Island` | CX | ? | `xmasisland.txt` | ? |
| `Guernsey` | GG | 6+ | `guernsey.txt` (6.8KB) | German occupation, bisect issues, regional issues |
| `Pakistan` | PK | 10+ | `Pakistan.txt` (10.4KB) | Overprint types, first permanent definitives |

### What These Albums Teach Us

**Every single page follows this structure:**
1. **Header row** — country name, map, coat of arms, flag (4 images across top)
2. **Narrative paragraph(s)** — 150-300 words of historical/philatelic context (TI 10pt Justified)
3. **Centered page title** — series name, date, watermark, perforation info (TB 10pt)
4. **Stamp rows** — 2-4 stamps per row, each with:
   - Stamp image OR empty mount box (with `\n`-separated text lines)
   - **Heading** below/above: issue date, subject, vessel name (HS 8pt)
   - **Text inside mount**: color, catalog numbers (SG#/SC#), denomination, perforation code
5. **Watermark illustration** — small image showing watermark pattern

**Key DSL commands used (NOT currently supported by StampAlbum Pro):**

```
ALBUM_PAGES_SIZE(210.0 297.0)          # A4 page
ALBUM_PAGES_MARGINS(15.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.5 0.1 0.0 1.0)   # double-line rule
ALBUM_PAGES_SPACING(5.0 8.0)           # horizontal, vertical gap
ALBUM_PAGES_TITLE(TN 25 "...")         # page header text
STAMP_BOXES_SIZE_ADJUST(6.0)           # mount = stamp + 6mm border
ALBUM_STAMP_IMG_SETTING(0.4 0.4 True)  # image scaling within mount
ROW_ALIGN_BOTTOM / ROW_ALIGN_TOP
ROW_START_ES(TB 6 0.1 5.0)             # row: font, gap, spacing
PAGE_START_VAR(5.0 10.0)               # page margins
PAGE_TEXT_PARAGRAPH_START(TI 10 Justified) ... PAGE_TEXT_PARAGRAPH_END
PAGE_TEXT_CENTRE(TB 10 "..." 1.5)      # centered text with line spacing
PAGE_VSPACE(-3.0)                      # vertical adjustment (negative = tighter)
STAMP_ADD(w h "img" "label" "denom" "perf")     # empty mount with text
STAMP_ADD_IMG(w h "img" "label" "heading" "extra") # mount with image
STAMP_HEADING_VA(HS 8 "text")          # vertical-align heading below stamp
STAMP_HEADING(HS 8 "text")             # heading below stamp (alias)
```

---

## 2. DSL Compatibility Layer (Priority: CRITICAL)

### Problem
StampAlbum Pro's DSL parser (`dsl.js`) understands only ~15 commands. AlbumEasy uses 40+.
The user's existing albums **cannot be imported** without data loss.

### Solution: Full AlbumEasy DSL Subset Parser

**Phase 2A — Page Setup Commands:**
```
ALBUM_PAGES_SIZE(w h)           → set page dimensions (already supported)
ALBUM_PAGES_MARGINS(l r t b)    → set margins (NEW)
ALBUM_PAGES_BORDER(w1 w2 g1 g2) → decorative border rules (NEW)
ALBUM_PAGES_SPACING(h v)        → default stamp spacing (NEW)
ALBUM_PAGES_TITLE(font size "text") → page header (NEW)
STAMP_BOXES_SIZE_ADJUST(mm)     → mount oversize amount (NEW)
ALBUM_STAMP_IMG_SETTING(x y b)  → image scaling within mount (NEW)
```

**Phase 2B — Row & Layout Commands:**
```
ROW_ALIGN_BOTTOM / ROW_ALIGN_TOP          → vertical alignment (NEW)
ROW_START_ES(font size gap spacing)       → begin a row of stamps (NEW)
PAGE_START_VAR(left top)                  → page with custom margins (NEW)
PAGE_VSPACE(mm)                           → vertical space adjustment (NEW)
PAGE_TEXT_CENTRE(font "text" spacing)     → centered text block (NEW)
PAGE_TEXT_PARAGRAPH_START(font style)     → begin paragraph (NEW)
PAGE_TEXT_PARAGRAPH_END                   → end paragraph (NEW)
```

**Phase 2C — Stamp Commands:**
```
STAMP_ADD(w h "img" "label" "denom" "perf")          → mount with text (ENHANCE)
STAMP_ADD_IMG(w h "img" "label" "heading" "extra")   → mount with image (ENHANCE)
STAMP_HEADING_VA(font "text")                         → heading below mount (NEW)
```

**Phase 2D — Import Workflow:**
1. User clicks "Import AlbumEasy File"
2. Parser reads `.txt`, extracts all commands
3. Renders preview in canvas
4. User can edit visually or re-export
5. Save as native `.slbum` format

---

## 3. Philatelic Template System (Priority: HIGH)

### Problem
Current 27 templates are blank grids with labels — no resemblance to real album pages.

### Solution: 15+ FIP-Standard Templates

**Template Category A — Traditional Philately (most popular):**

| # | Template | Layout | Use Case |
|---|----------|--------|----------|
| A1 | **Definitive Series Page** | Header + 4 rows × 3-4 stamps | Portrait definitives, same-design series |
| A2 | **Commemorative Set Page** | Header + centered set + description | Single issue, 4-8 stamps |
| A3 | **First Day Cover Page** | Large FDC image + cachet detail + stamp | FDC collections |
| A4 | **Postal History Page** | Cover scan left + stamps right + postmark | Covers with stamps used on |
| A5 | **Watermark Display Page** | Watermark image + stamps showing it | Watermark study |
| A6 | **Perforation Study** | Perf gauge + stamps showing variations | Perf variety collection |

**Template Category B — Thematic Philately:**

| # | Template | Layout | Use Case |
|---|----------|--------|----------|
| B1 | **Title/Plan Page** | Title + collector name + plan text + frame # | FIP exhibit opening |
| B2 | **Thematic Story Page** | Stamp top + narrative paragraph (150 words) | Thematic development |
| B3 | **Map + Stamps Page** | Small map + 3-5 stamps illustrating theme | Geographic thematic |
| B4 | **Large Format Display** | 1-2 stamps + extensive annotation | Rare/important items |

**Template Category C — Competitive Exhibition:**

| # | Template | Layout | Use Case |
|---|----------|--------|----------|
| C1 | **APS 5-page Traditional** | Horizontal rows, Scott # below | US competition standard |
| C2 | **FIP 8-frame A4** | One frame per page, detailed text | International exhibition |
| C3 | **A3 Double Frame** | Larger format, 6-8 stamps | Multi-frame traditional |
| C4 | **Square Frame (310×290)** | Modern thematic format | FEPA/FIP thematic |

**Template Category D — Reference/Album Pages:**

| # | Template | Layout | Use Case |
|---|----------|--------|----------|
| D1 | **Country Introduction** | Flag + map + arms + history paragraph | Album opening page |
| D2 | **Catalog Page** | Table layout: SG#/SC#/Michel#/description | Reference listing |
| D3 | **Blank Mount Page** | Grid of empty mounts, various sizes | Custom arrangement |

---

## 4. UI/UX Overhaul for Older Collectors (Priority: HIGH)

### Design Principles
- **Light, paper-like background** — collectors view real albums on white/ivory paper
- **Large, readable text** — minimum 14px, base 16px, high contrast
- **Clear labels everywhere** — no icons without text
- **Generous spacing** — nothing cramped or tiny
- **Familiar patterns** — menus, toolbars, dialogs (not hidden gestures)

### 4.1 Theme: "Album Paper"

```css
/* Light philatelic theme */
--bg-primary: #FAF8F3;        /* Ivory/paper white */
--bg-secondary: #F0EDE6;      /* Slightly darker for panels */
--bg-canvas: #FFFFFF;         /* Pure white for the page */
--text-primary: #1A1A1A;      /* Near-black for readability */
--text-secondary: #4A4A4A;    /* Dark gray for labels */
--border-color: #D4CFC2;      /* Warm gray borders */
--accent: #8B0000;            /* Deep red (philatelic tradition) */
--accent-secondary: #1A3A6B;  /* Navy blue */
--mount-border: #2C2C2C;      /* Near-black for stamp mounts */
--mount-bg: #FEFEFE;          /* White mount interior */
--grid-line: #E8E4D8;         /* Very subtle grid */
```

### 4.2 Typography Scale

| Element | Current | Target | Reason |
|---------|---------|--------|--------|
| Base font | 12px | 16px | Readable without zoom |
| Stamp labels | 10px | 14pt | Catalog numbers must be legible |
| Page titles | 14px | 20-25pt | Clear hierarchy |
| Headings | 12px | 18pt | Section separation |
| UI buttons | 11px | 14-16px | Tappable, readable |
| Properties panel | 12px | 14px | Form labels |

### 4.3 Layout Changes

**Current:** Dark sidebar + dark toolbar + dark canvas → looks like code editor
**Target:** Light toolbar + ivory sidebar + white canvas → looks like album page

```
┌─────────────────────────────────────────────────────────┐
│  File  Edit  View  Insert  Export          [Large icons + text] │  ← Light toolbar
├────────┬──────────────────────────────────┬─────────────┤
│        │                                  │             │
│ Stamps │     WHITE CANVAS                 │ Properties  │
│        │     with subtle grid             │             │
│ Palette│     A4 page outline              │ [Large      │
│        │     Ivory margins                │  labels]    │
│ [Big   │                                  │             │
│  icons]│     Stamp mounts with            │ X: [    ]   │
│        │     catalog numbers              │ Y: [    ]   │
│        │                                  │ W: [    ]   │
│        │                                  │ H: [    ]   │
│        │                                  │             │
├────────┴──────────────────────────────────┴─────────────┤
│  Status: Page 1 of 6 — Bahrain — First Issues          │  ← Light footer
└─────────────────────────────────────────────────────────┘
```

### 4.4 Accessibility Features

- **WCAG AA compliance** minimum (4.5:1 contrast ratio)
- **Keyboard shortcuts** shown in tooltips (not just hidden)
- **"Large Text Mode"** toggle in View menu (scales everything 1.25×)
- **Focus indicators** — visible outlines on focused elements
- **No hover-only interactions** — everything works on click
- **Confirm dialogs** for destructive actions (delete, clear)
- **Undo/redo** prominently visible (not just keyboard)

### 4.5 Stamp Mount Rendering

Real stamp mounts should look like **physical album mounts**:

```
┌─────────────────────────┐  ← Thin black border (0.5pt)
│  ┌───────────────────┐  │  ← Inner border (double-line option)
│  │                   │  │
│  │   [Stamp Image]   │  │  ← Image centered, slightly inset
│  │                   │  │
│  └───────────────────┘  │
│                         │
│  dark blue              │  ← Color description (10pt)
│  SG#1 SC#1              │  ← Catalog numbers (10pt)
│  ½p                     │  ← Denomination (10pt)
│  A1                     │  ← Perforation/print code (9pt)
└─────────────────────────┘
        │
        ▼
   M.V. Kista Dan          ← Heading below mount (8pt, centered)
```

---

## 5. Stamp Data Model Enhancement

### Current Model (too simple)
```json
{"id": "el1", "t": "stamp", "s": "rectangle", "x": 50, "y": 50, "w": 40, "h": 30, "lbl": "", "font": "HN", "fs": 12}
```

### Enhanced Model (philatelic)
```json
{
  "id": "el1",
  "t": "stamp",
  "s": "rectangle",
  "x": 50, "y": 50, "w": 40, "h": 30,
  
  /* Display */
  "img": "bahflag.png",
  "lbl": "dark blue\nSG#1 SC#1",
  
  /* Philatelic metadata */
  "catalog": {
    "sg": "1",
    "sc": "1",
    "michel": "",
    "gibbons": "",
    "other": ""
  },
  "denomination": "½p",
  "color": "dark blue",
  "heading": "M.V. Kista Dan",
  "heading_position": "below",
  "perforation": "A1",
  "watermark": "Wmk 314",
  "condition": "Mint NH",
  "year": "1963",
  "notes": "Engraved. Recess B.W."
}
```

---

## 6. Implementation Phases

### Phase 1: Foundation (2-3 days)
- [ ] Create light theme CSS (`style.css` overhaul)
- [ ] Increase base font sizes (12px → 16px)
- [ ] Add "Large Text Mode" toggle
- [ ] Render stamp mounts with proper borders + inner frame
- [ ] Add catalog number fields to properties panel

### Phase 2: DSL Compatibility (3-4 days)
- [ ] Implement `PAGE_TEXT_PARAGRAPH_START/END` parser
- [ ] Implement `ROW_START_ES`, `ROW_ALIGN_BOTTOM/TOP`
- [ ] Implement `PAGE_VSPACE`, `PAGE_START_VAR`
- [ ] Implement `STAMP_HEADING`, `STAMP_HEADING_VA`
- [ ] Implement `PAGE_TEXT_CENTRE` with spacing parameter
- [ ] Implement `ALBUM_PAGES_MARGINS`, `ALBUM_PAGES_BORDER`
- [ ] Implement `STAMP_BOXES_SIZE_ADJUST`
- [ ] Import workflow: File → Import AlbumEasy `.txt`
- [ ] Test import with all 6 user albums

### Phase 3: Templates (2-3 days)
- [ ] Create 15+ template definitions in `templates.py`
- [ ] Each template generates realistic DSL output
- [ ] Template gallery shows visual previews (not just names)
- [ ] "Country Introduction" template (flag + map + arms + text)
- [ ] "Definitive Series" template (rows of stamps)
- [ ] "Thematic Story" template (stamp + paragraph)
- [ ] "Watermark Display" template
- [ ] "Title/Plan Page" template for FIP exhibits

### Phase 4: UI Polish (1-2 days)
- [ ] Toolbar with text labels under icons
- [ ] Properties panel with logical grouping
- [ ] Status bar with page info
- [ ] "Preview Frame" button (shows page as it would appear in exhibition)
- [ ] Print-ready PDF export with proper margins
- [ ] Onboarding wizard for new users

### Phase 5: Testing & Refinement (1 day)
- [ ] Import all 6 user albums, verify rendering
- [ ] Test with users aged 50+ (if possible)
- [ ] Verify WCAG AA contrast ratios
- [ ] Performance test with 100+ stamp pages

---

## 7. Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| DSL commands supported | ~15 | 40+ (full AlbumEasy subset) |
| User's albums importable | 0/6 | 6/6 |
| Templates | 27 (blank grids) | 15+ (realistic philatelic) |
| Base font size | 12px | 16px |
| Contrast ratio | ~3:1 (grey on grey) | ≥4.5:1 (WCAG AA) |
| Theme | Dark mode | Light/paper |
| Stamp mount rendering | Plain rectangle | Bordered mount + catalog # |
| Catalog number fields | None | SG/SC/Michel/Gibbons |
| Accessibility | None | Large text mode, keyboard nav |

---

## 8. Open Questions

1. **Should we support the full AlbumEasy DSL or a practical subset?** → Start with subset, expand later
2. **Should templates be code-generated or hand-crafted?** → Code-generated from parameters
3. **Do we need offline catalog data (SG# lookup)?** → Phase 2, use Colnect API
4. **Should the app support multiple languages?** → English first, i18n later
5. **Print-focused or screen-first?** — Both: screen editing, print-optimized export

---

*End of V3 Improvement Plan*
