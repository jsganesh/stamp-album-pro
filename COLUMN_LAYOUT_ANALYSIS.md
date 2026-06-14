# Column Layout Support: Visual Builder vs DSL Analysis

## Current Status

### ✅ **What WORKS with the fixes:**

**DSL-based workflow** (users write/edit code):
```
PAGE_COLUMN_START (2 10.0)
PAGE_TEXT (HN 10 "Column 1")
STAMP_ADD (32.0 37.0 "Stamp" "" "" "")
PAGE_COLUMN_NEXT
PAGE_TEXT (HN 10 "Column 2")
STAMP_ADD (32.0 37.0 "Stamp" "" "" "")
```

✅ Parses correctly (PAGE_COLUMN_NEXT fix)
✅ Gap configurable (column gap fix)
✅ PDF renders proper column layout with custom gaps
✅ Can be saved and loaded

**Limitation:** Users must understand DSL syntax or copy/paste templates

---

### ❌ **What DOESN'T WORK:**

**Visual Drag-and-Drop Builder** (layout mode):
- No UI control for setting up columns
- Canvas uses free-form absolute positioning (x, y coordinates)
- `buildDSL()` function generates `STAMP_ADD_AT()` commands (free-form)
- Does NOT generate `PAGE_COLUMN_START/NEXT/STOP` commands
- **Result:** Philatelists cannot create column layouts without writing DSL

**Current flow:**
```
[Visual drag-drop] → [buildDSL()] → STAMP_ADD_AT (free-form only)
                                       ↓
                                  [No columns support]
```

---

## What's Missing for Full Visual Support

### **Issue 1: No Column Mode Toggle**
- Visual builder has NO UI to enable "column layout mode"
- No way to select: 1, 2, or 3 columns
- No way to set column gap (5mm, 10mm, 15mm, etc.)

### **Issue 2: Canvas Elements Don't Track Column Info**
Canvas element structure:
```javascript
{
  t: "stamp|text|image|freehand",
  x: 100,           // pixel x
  y: 50,            // pixel y
  w: 120,           // pixel width
  h: 140,           // pixel height
  lbl: "France 1",  // label
  // Missing: column_index, row_info, etc.
}
```

- Elements only have absolute coordinates
- No concept of "which column" an element belongs to
- No row grouping information

### **Issue 3: buildDSL() Bypasses Row/Column System**
Current implementation:
```javascript
function buildDSL() {
  E.forEach(function(el) {
    if (el.t === "image") {
      lines.push('STAMP_ADD_IMG(...absolute x,y...)');  // ← Always absolute
    } else if (el.t === "text") {
      lines.push('PAGE_TEXT_CENTRE(...)');               // ← Page level, no row
    }
    // Never generates: ROW_START_FS, PAGE_COLUMN_START, PAGE_COLUMN_NEXT
  });
}
```

---

## Solution: Enable Visual Builder Column Support

### **Phase 1: Add Column Mode UI (Priority: HIGH)**

```html
<!-- Add to layout editor toolbar -->
<div class="layout-options">
  <label>Layout Mode:</label>
  <select id="column-mode">
    <option value="1">Single Column (free-form)</option>
    <option value="2">Two Columns</option>
    <option value="3">Three Columns</option>
  </select>
  
  <label>Column Gap (mm):</label>
  <input type="number" id="column-gap" min="2" max="20" value="10">
</div>
```

**Code change location:** `src/stamp_album/web/app.js` (UI panel section)

### **Phase 2: Store Column Info in Canvas State**

Add column metadata to page/element:
```javascript
// Global state in app.js
var _pageColumns = { mode: 1, gap: 10.0 };  // NEW

// In canvas element:
{
  t: "stamp",
  x: 100,
  y: 50,
  column_idx: 1,     // NEW: which column (0-2)
  row_idx: 0,        // NEW: which row within column
  // ...
}
```

**Code change location:** `src/stamp_album/web/app.js` (global state + element objects)

### **Phase 3: Update buildDSL() to Generate Column Commands**

```javascript
function buildDSL() {
  var lines = [...];
  
  // NEW: Add column layout if set
  if (_pageColumns.mode > 1) {
    lines.push("PAGE_COLUMN_START(" + _pageColumns.mode + " " + _pageColumns.gap + ")");
  }
  
  // Group elements by column and row
  var columnGroups = groupByColumn(E, _pageColumns.mode);
  columnGroups.forEach(function(col, idx) {
    if (idx > 0) lines.push("PAGE_COLUMN_NEXT");  // NEW
    col.forEach(function(el) {
      // Generate stamp DSL...
    });
  });
  
  if (_pageColumns.mode > 1) {
    lines.push("PAGE_COLUMN_STOP");  // NEW
  }
  
  return lines.join("\n");
}
```

**Code change location:** `src/stamp_album/web/app.js` (buildDSL function)

### **Phase 4: Update Canvas Rendering**

Visual grid should show column boundaries when column mode is enabled:
```javascript
function render() {
  // Draw column guides
  if (_pageColumns.mode > 1) {
    drawColumnGuides(ctx, _pw, _ph, _pageColumns.mode, _pageColumns.gap);
  }
  // ... render elements ...
}
```

**Code change location:** `src/stamp_album/web/app.js` (render function)

---

## Implementation Roadmap

| Step | Feature | Effort | Impact |
|------|---------|--------|--------|
| 1 | Column mode selector UI | 1-2h | Philatelists can choose 2/3 columns |
| 2 | Column gap input | 30min | Customizable spacing |
| 3 | Column metadata in elements | 2-3h | Track which element is in which column |
| 4 | buildDSL() updates | 2h | Generate PAGE_COLUMN_START/NEXT/STOP |
| 5 | Visual column guides | 1h | Show boundaries while dragging |
| 6 | Parse column DSL back to visual | 2h | Load column layouts into visual editor |
| **Total** | | **8-10h** | **Full visual column support** |

---

## Current Recommendation for Philatelists

**Until visual builder support is added:**

### ✅ **Option A: Use Templates**
1. Create a 2-column template once in DSL:
   ```
   PAGE_COLUMN_START (2 10.0)
   PAGE_TEXT (HN 10 "Column 1")
   STAMP_ADD (32.0 37.0 "..." "" "" "")
   PAGE_COLUMN_NEXT
   PAGE_TEXT (HN 10 "Column 2")
   STAMP_ADD (32.0 37.0 "..." "" "" "")
   PAGE_COLUMN_STOP
   PAGE_END
   ```
2. Save as `template-2col.slbum`
3. Duplicate and edit for future albums
4. Keep DSL visible in split-pane, preview updates live

### ✅ **Option B: Pure DSL Workflow**
- Write DSL directly (CodeMirror editor is quite good)
- Use DSL keywords for columns, rows, text
- Save reusable DSL files for different layouts
- No need for visual editor at all

### ❌ **Option C: Visual Builder (Current)**
- Works for free-form stamp placement
- NOT suitable for structured multi-column albums yet
- Cannot save/replicate column layouts easily

---

## Summary

**Your fixes work perfectly for:**
✅ DSL-based users who write column code
✅ Philatelists who copy/paste templates
✅ PDF export with proper column spacing

**Still needed for true visual support:**
⏳ Column mode UI in layout editor
⏳ Column metadata in canvas elements
⏳ DSL generation for PAGE_COLUMN_START/NEXT/STOP

Would you like me to implement visual builder column support? (Estimated 8-10 hours)
