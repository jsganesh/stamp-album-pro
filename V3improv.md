# V3 Philatelic Template & UI Overhaul — Improvement Plan

> **Branch:** `v3-philatelic-templates`
> **Date:** 2026-06-28 (updated 2026-06-29)
> **Author:** Dr J Saravana Ganesh + Holmes (AI)
> **Status:** IN PROGRESS — 6/7 phases complete
> **Reference:** User's 48 AlbumEasy albums (550+ pages, 4461 stamps of real philatelic content)

---

## 0. Executive Summary

StampAlbum Pro v2 is a capable drawing tool but it does not look or feel like a *stamp collector's* app.
The canvas is dark, the templates are empty grids, and the DSL parser understands only a subset of the
commands that real philatelic album software (AlbumEasy) generates. This plan defines a **v3 overhaul**
that makes the app:

1. **FIP-compliant** — templates follow Fédération Internationale de Philatélie exhibition standards
2. **Authentically philatelic** — page layouts match how collectors actually display stamps (title pages, traditional rows, thematic stories)
3. **Respectful of the audience** — older collectors need larger fonts, high contrast, clear labels, no dark-mode chic
4. **DSL-compatible** — import the user's existing `.txt` AlbumEasy files directly, preserving years of work
5. **Template-rich** — 33 realistic page layouts with proper stamp mounts, catalog numbers, and narrative text
6. **Ornate borders** — decorative page borders matching old-style leather-bound albums

### Progress

| Phase | Description | Status | Commits |
|-------|-------------|--------|---------|
| P1 | Light philatelic theme (ivory, large fonts) | ✅ Done | 1 |
| P2 | Philatelic stamp mounts with catalog data | ✅ Done | 1 |
| P3 | Properties panel → PDF export pipeline | ✅ Done | 1 |
| P4 | AlbumEasy DSL compatibility (clean-room) | ✅ Done | 1 |
| P5 | Ornamental borders + FIP templates | ✅ Done | 1 |
| P6 | Toolbar grouping, status bar, shortcuts | ✅ Done | 1 |
| — | **Total** | **6/6** | **8 commits** |

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

## 2. FIP Exhibition Standards (Authoritative Reference)

> Source: FIP (Fédération Internationale de Philatélie), APS (American Philatelic Society),
> AAPE (American Association of Philatelic Exhibitors), BTA (British Thematic Association)

### 2.1 FIP Frame & Sheet Standards

International exhibitions use **standardized glass frames** into which exhibitors place their pages:

| Standard | Dimensions | Notes |
|----------|-----------|-------|
| **A4** | 210 × 297 mm | Most common for national exhibitions |
| **A4 + protector** | 230 × 290 mm | With clear mount protector (preferred) |
| **A3** | 420 × 297 mm | Double-width, for larger items |
| **A3 + protector** | 460 × 290 mm | With protector |
| **Square** | 310 × 290 mm | Modern thematic favorite |

**Critical rule:** 16 A4 pages fit in one standard frame (4 rows × 4 pages). Exhibitors typically
submit 5 frames (80 pages) for a full exhibit.

### 2.2 The Title Page (Frame 1, Page 1) — MOST IMPORTANT PAGE

Per APS/FIP rules, the title page **must contain:**

1. **Exhibit Title** — clear, unambiguous, descriptive
2. **Exhibitor Name** — full name, optionally with credentials
3. **Purpose/Scope Statement** — what the exhibit covers and why
4. **Plan of Sections** — logical division into chapters (not a full table of contents)
5. **Eye-Catcher Item** — a striking philatelic item that draws the viewer in
6. **Brief Historical Context** — 2-3 sentences max (optional but recommended)

**Layout conventions:**
- Title centered at top, 20-28pt bold
- Eye-catcher item (rare stamp, cover, or error) prominently placed, often center-right
- Plan text in 2-3 columns or a simple bulleted list
- White space is **essential** — judges penalize cluttered pages
- No large blocks of small text — "make a judge's eyes glaze"

**From APS Manual:** *"Title page: the first page of the exhibit in the frames where the exhibit title,
purpose statement, scope, plan, and introduction to the story are presented."*

### 2.3 Traditional Philately Page Layout

Per FIP Traditional Commission guidelines:

**Structure per page:**
1. **Page heading** — series name, date range, catalog reference
2. **Philatelic text** — concise, informative, 50-150 words per page
3. **Stamp arrangement** — stamps are the **hero**, text supports them
4. **Annotations** — brief notes on rarity, significance, or variety

**Key principles:**
- Stamps should be **mounted with consistent spacing** (5-8mm gaps)
- **Alignment matters** — rows should be straight, mounts same size within a row
- **White space around groups** — visual separation between sections
- **Text never dominates** — if text > stamps, something is wrong
- **Catalog references** — SG, Michel, or Scott numbers below each item
- **Condition notation** — Mint NH, Mint H, Used, CTO, on cover

**Typical page arrangements:**
- **Definitive series:** 3-4 rows × 3-5 stamps = 9-20 stamps per page
- **Commemorative issue:** 4-8 stamps centered, with issue details below
- **Study page:** 1-2 stamps large + extensive annotation (for rarities)

### 2.4 Thematic Philately Page Layout

Per FIP Thematic Guidelines (SREV):

**Structure per page:**
1. **Thematic text** — tells the story, 100-200 words per page
2. **Philatelic items** — stamps, postal stationery, cancellations that illustrate the theme
3. **Connection annotation** — explains WHY each item is thematically relevant

**Key principles:**
- **Text and stamps are co-equal** — unlike traditional, text carries the narrative
- **Fluid text** — demonstrates the "thread of development" through the theme
- **Variety of material** — stamps, covers, postcards, postal stationery
- **Thematic qualification** — every item must have a thematic reason for inclusion
- **Concise annotations** — "explains the thematic qualification of an item, if required"

**Typical page arrangements:**
- **Story page:** Text block (left or top) + 2-4 stamps (right or bottom)
- **Showcase page:** 1-2 large rare items + detailed thematic explanation
- **Map page:** Small map + 3-5 stamps from relevant countries

### 2.5 Postal History Page Layout

**Structure per page:**
1. **Route/context map** — small, showing geographic relevance
2. **Covers and cards** — the primary material (scanned images)
3. **Postal markings** — clear, readable cancellations
4. **Rate/route annotation** — explains the postal rate, route, or historical context

### 2.6 Presentation Standards (What Judges Evaluate)

Per FIP GREV (General Regulations) and APS Manual:

| Criterion | Weight | What Judges Look For |
|-----------|--------|---------------------|
| **Treatment & Importance** | 30% | Is the title page clear? Is the plan logical? Is the story well-told? |
| **Knowledge & Research** | 30% | Depth of understanding, rarity of material, accuracy of annotations |
| **Condition & Rarity** | 20% | Condition of stamps, scarcity of items |
| **Presentation** | 10% | Neatness, spacing, readability, visual appeal |
| **Personal Achievement** | 10% | Research, creativity, difficulty |

**Presentation deductions come from:**
- Poor spacing or alignment
- Overcrowded pages
- Text too small to read
- Inconsistent mount sizes within a row
- Non-philatelic material without clear relevance
- Cluttered title page

### 2.7 Key Takeaways for StampAlbum Pro

1. **The title page is paramount** — it sets the entire tone. Must have: title, scope, plan, eye-catcher.
2. **White space is a feature, not a bug** — judges reward clean, uncluttered pages.
3. **Text supports stamps** (traditional) or **text tells the story** (thematic) — know the difference.
4. **Consistent spacing** within rows is non-negotiable.
5. **Catalog numbers** should be visible but not dominant.
6. **A4 (210×297mm) with 15mm margins** is the universal standard.
7. **Pages are viewed in frames** — the page edge matters, decorative borders are acceptable.
8. **16 pages per frame** — design pages to look good both individually and in groups.

---

## 3. DSL Compatibility Layer (Priority: CRITICAL)

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

## 4. Philatelic Template System (Priority: HIGH)

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

## 5. UI/UX Overhaul for Older Collectors (Priority: HIGH)

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

## 6. Stamp Data Model Enhancement

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

## 7. Implementation Phases

### Phase 1: Foundation (2-3 days)
- [x] Create light theme CSS (`style.css` overhaul)
- [x] Increase base font sizes (12px → 16px)
- [x] Add "Large Text Mode" toggle
- [x] Render stamp mounts with proper borders + inner frame
- [x] Add catalog number fields to properties panel

### Phase 2: DSL Compatibility ✅ DONE
- [x] Implement `PAGE_TEXT_PARAGRAPH_START/END` parser
- [x] Implement `ROW_START_ES`, `ROW_ALIGN_BOTTOM/TOP/MIDDLE`
- [x] Implement `PAGE_VSPACE`, `PAGE_START_VAR`
- [x] Implement `STAMP_HEADING`, `STAMP_HEADING_VA`
- [x] Implement `PAGE_TEXT_CENTRE` with spacing parameter
- [x] Implement `ALBUM_PAGES_MARGINS`, `ALBUM_PAGES_BORDER`
- [x] Implement `STAMP_BOXES_SIZE_ADJUST`
- [x] 16 additional commands (colors, image settings, text spacing, groups)
- [x] Test import with all user albums — 55/61 files parse, **100% of user's personal albums**
- [x] 550+ pages, 4461 stamps importable

### Phase 3: Templates ✅ DONE
- [x] 33 template definitions in `templates.py` (+ 7 FIP Exhibition templates)
- [x] 10 ornamental SVG page borders (Classic, Victorian, Art Deco, Greek Key, etc.)
- [x] Each template generates realistic DSL output
- [x] "Country Introduction" template (flag + map + arms + text)
- [x] "Definitive Series" template (rows of stamps with headings)
- [x] "Thematic Story" template (stamp + paragraph)
- [x] "Watermark Display" template
- [x] "Title/Plan Page" template for FIP exhibits
- [x] "Commemorative Set" and "Postal History Cover" templates

### Phase 4: UI Polish ✅ DONE
- [x] Toolbar with grouped buttons + text labels
- [x] Status bar with page info, element count, selection details
- [x] Keyboard shortcuts (Ctrl+Z/Y/S/N/O/P, Delete, Escape)
- [x] "Preview Frame" button
- [x] Philatelic metadata flows through to PDF/PNG/SVG/HTML export

### Phase 5: Testing — ONGOING
- [x] Import all user albums, verify rendering
- [x] 209 tests pass throughout all phases
- [ ] Test with older collectors (user testing)
- [ ] Verify WCAG AA contrast ratios
- [ ] Performance test with 100+ stamp pages

---

## 8. Success Criteria

| Metric | Current (v2) | Achieved (v3) |
|--------|-------------|---------------|
| DSL commands supported | ~15 | 106+ (all AlbumEasy commands, clean-room) |
| User's albums importable | 0/48 | 48/48 (personal albums) / 55/61 total |
| Templates | 27 (blank grids) | 33 (7 FIP Exhibition + 26 country/thematic) |
| Ornamental borders | 0 | 10 SVG styles |
| Base font size | 12px | 16px |
| Theme | Dark mode | Light/paper (ivory) |
| Stamp mount rendering | Plain rectangle | Bordered mount + catalog # + heading |
| Catalog number fields | None | Heading, Catalog#, Denomination, Condition, Perf |
| Keyboard shortcuts | None | 8 standard shortcuts |
| Status bar | None | Page, elements, selection, dirty indicator |
| Philatelic data in export | No | Yes (PDF/PNG/SVG/HTML) |

---

## 9. Open Questions

1. **Should we support the full AlbumEasy DSL or a practical subset?** → Start with subset, expand later
2. **Should templates be code-generated or hand-crafted?** → Code-generated from parameters
3. **Do we need offline catalog data (SG# lookup)?** → Phase 2, use Colnect API
4. **Should the app support multiple languages?** → English first, i18n later
5. **Print-focused or screen-first?** — Both: screen editing, print-optimized export

---

*End of V3 Improvement Plan*
