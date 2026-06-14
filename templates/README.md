# Stamp Album Templates

Pre-made layouts for common philatelist use cases. Copy and customize for your collection.

## Available Templates

### 🌍 **Two-Column: Europe** (`template-2col-europe.slbum`)
- **Layout:** 2 columns with 10mm gap
- **Use case:** Display stamps from different European countries side-by-side
- **Features:** 
  - Country headings with Scott catalogue references
  - Organized by region (France, Belgium, Germany, Italy)
  - Easy to duplicate for multiple pages
  - 4 stamps per country (2×2 grid per column)

**Best for:** Continental groupings, comparative layouts

---

### 🌏 **Three-Column: Worldwide** (`template-3col-worldwide.slbum`)
- **Layout:** 3 columns with 8mm gap
- **Use case:** Display three different regions on one page
- **Features:**
  - Americas, Europe, Asia-Pacific columns
  - Compact spacing (8mm gap) fits more content
  - 4 stamps per region (2×2 grid per column)
  - Good for: cataloging world issues, themed collections

**Best for:** Showing multiple regions per page, dense collections

---

### 📦 **Compact Two-Column** (`template-2col-compact.slbum`)
- **Layout:** 2 columns with 5mm gap (narrow)
- **Use case:** Maximize stamps per page
- **Features:**
  - Very tight 5mm column gap
  - Equal-space row distribution (3 stamps per row)
  - 18 stamps per page (9 per column)
  - Reduced margins (12-15mm)

**Best for:** Large collections, fitting many stamps, space-efficient displays

---

### 📊 **Single Column with Quadrille** (`template-1col-quadrille.slbum`)
- **Layout:** Single column with graph paper background
- **Use case:** Traditional album look with grid reference
- **Features:**
  - 5mm quadrille grid background
  - Two sections: Regular Issues and Commemoratives
  - Clean, professional appearance
  - Graph paper helps with alignment

**Best for:** Classic album aesthetic, organized chronological collections

---

## How to Use

### **Option 1: Quick Copy-Paste**
1. Open the template file in the editor
2. Select all (`Ctrl+A`)
3. Copy (`Ctrl+C`)
4. Create new album
5. Paste template (`Ctrl+V`)
6. Edit country names, catalog numbers, stamp labels
7. Save with your collection name

### **Option 2: Open and Modify**
1. File → Open → Select template file
2. Edit stamps, add/remove rows
3. File → Save As → Your collection name
4. Add more pages by duplicating PAGE_START...PAGE_END blocks

### **Option 3: Load from Browser**
1. In the web app, sidebar shows all `.slbum` files
2. Templates appear in list
3. Click to load and start editing

---

## Template Customization

### **Change Column Count**
```dsl
# Current (2 columns)
PAGE_COLUMN_START (2 10.0)

# To 3 columns
PAGE_COLUMN_START (3 8.0)

# To 1 column
# Just remove PAGE_COLUMN_START and PAGE_COLUMN_STOP
```

### **Change Gap Size**
```dsl
# Current (10mm gap)
PAGE_COLUMN_START (2 10.0)

# Wider gap (15mm)
PAGE_COLUMN_START (2 15.0)

# Narrower gap (5mm)
PAGE_COLUMN_START (2 5.0)
```

### **Add More Rows**
Copy and paste existing `ROW_START_FS` block:
```dsl
ROW_START_FS (HN 8 1.0 40.0)
STAMP_ADD (32.0 37.0 "New 1" "NEW-1" "" "")
STAMP_ADD (32.0 37.0 "New 2" "NEW-2" "" "")
ROW_END
```

### **Change Stamp Size**
```dsl
# Current: 32.0mm × 37.0mm
STAMP_ADD (32.0 37.0 "Label" "Catalog" "" "")

# Smaller: 28.0mm × 33.0mm
STAMP_ADD (28.0 33.0 "Label" "Catalog" "" "")

# Larger: 40.0mm × 50.0mm
STAMP_ADD (40.0 50.0 "Label" "Catalog" "" "")
```

### **Change Font**
```dsl
# Font codes:
# HN = Helvetica Normal
# HB = Helvetica Bold
# TN = Times Normal
# TB = Times Bold
# CN = Courier Normal
# CB = Courier Bold

PAGE_TEXT (HN 10 "Regular")   # Default
PAGE_TEXT (HB 12 "Bold")      # Larger, bold
PAGE_TEXT (TN 9 "Small Text") # Serif, smaller
```

---

## Recommended Workflow for Philatelists

1. **Start with template** that matches your collection
2. **Customize labels** (country names, issue years, catalog numbers)
3. **Adjust quantities** (add/remove rows for different collection sizes)
4. **Save as your collection** (e.g., `france-2024.slbum`)
5. **Export to PDF** for printing
6. **Keep saved file** for updating future issues

---

## Tips

- 📌 **Backup originals:** Never edit templates directly. Copy first, then customize.
- 🔄 **Reuse layouts:** Once you customize a template, duplicate it for similar pages.
- 📏 **Spacing:** 10mm gap is standard, 5-8mm for dense layouts, 12-15mm for spacious.
- 🎨 **Colors:** Edit `COLOUR_` commands to customize border colors, background, text.
- 📄 **Multiple pages:** Copy entire `PAGE_START...PAGE_END` blocks to add pages.

---

## Creating Your Own Templates

After customizing a template for your needs:
1. Perfect the layout in editor
2. Test PDF export
3. Save as `template-descriptive-name.slbum`
4. Share with other collectors!

