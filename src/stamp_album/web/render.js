"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, mm = S.mm, showToast = S.showToast;

// ── Font population ──
function populateFonts() {
    var pfnt = $("pfnt");
    if (!pfnt) return;
    pfnt.innerHTML = "";
    var stdFonts = [
        { v: "HN", t: "Helvetica" },
        { v: "HB", t: "Helvetica Bold" },
        { v: "HI", t: "Helvetica Italic" },
        { v: "HS", t: "Helvetica Bold Italic" },
        { v: "TN", t: "Times New Roman" },
        { v: "TB", t: "Times New Roman Bold" },
        { v: "TI", t: "Times New Roman Italic" },
        { v: "TS", t: "Times New Roman Bold Italic" },
        { v: "CN", t: "Courier New" },
        { v: "CB", t: "Courier New Bold" },
        { v: "CI", t: "Courier New Italic" },
        { v: "CS", t: "Courier New Bold Italic" },
    ];
    var og = document.createElement("optgroup");
    og.label = "Standard Fonts";
    stdFonts.forEach(function(f) { var o = document.createElement("option"); o.value = f.v; o.textContent = f.t; og.appendChild(o); });
    pfnt.appendChild(og);
    if (S.SYSTEM_FONTS && S.SYSTEM_FONTS.length) {
        var og2 = document.createElement("optgroup");
        og2.label = "System Fonts";
        S.SYSTEM_FONTS.forEach(function(f) { var o = document.createElement("option"); o.value = f; o.textContent = f; og2.appendChild(o); });
        pfnt.appendChild(og2);
    }
    var ws = document.createElement("optgroup");
    ws.label = "Web Safe";
    ["Arial","Helvetica","Times New Roman","Courier New","Georgia","Verdana","Trebuchet MS","Impact","Comic Sans MS"].forEach(function(f) { var o = document.createElement("option"); o.value = f; o.textContent = f; ws.appendChild(o); });
    pfnt.appendChild(ws);
}

// ── Alignment guide lines + snap + labels ──
var _guideLines = [];
var _guideLabels = [];
var GUIDE_THRESHOLD = 5;  // px tolerance for snapping
var SNAP_ENABLED = true;
S.GUIDE_THRESHOLD = GUIDE_THRESHOLD;

function drawAlignmentGuides(el) {
    clearAlignmentGuides();
    if (!el) return;
    var guides = [];
    var pg = $("page");
    if (!pg) return;
    var pw = S._pw || 595;
    var ph = S._ph || 842;

    // Collect all edges: the dragged element + all other elements + page center
    var edges = [
        { pos: el.x, type: "v", src: el.id },
        { pos: el.x + el.w, type: "v", src: el.id },
        { pos: el.x + el.w / 2, type: "v", src: el.id },
        { pos: el.y, type: "h", src: el.id },
        { pos: el.y + el.h, type: "h", src: el.id },
        { pos: el.y + el.h / 2, type: "h", src: el.id },
    ];

    // Page center and quarter lines (always present as reference)
    var pageGuides = [
        { pos: pw / 2, type: "v", label: "Page Center" },
        { pos: ph / 2, type: "h", label: "Page Center" },
        { pos: pw * 0.25, type: "v", label: "¼" },
        { pos: pw * 0.75, type: "v", label: "¾" },
    ];

    // Other elements on page
    S.E.forEach(function(other) {
        if (other.id === el.id) return;
        edges.push({ pos: other.x, type: "v", src: other.id });
        edges.push({ pos: other.x + other.w, type: "v", src: other.id });
        edges.push({ pos: other.x + other.w / 2, type: "v", src: other.id });
        edges.push({ pos: other.y, type: "h", src: other.id });
        edges.push({ pos: other.y + other.h, type: "h", src: other.id });
        edges.push({ pos: other.y + other.h / 2, type: "h", src: other.id });
    });

    // Find snaps: compare dragged element edges against all other edges + page guides
    var snapped = { v: null, h: null };
    var vLabel = null, hLabel = null;

    // Vertical edges of dragged element
    var vEdges = [
        { pos: el.x, label: "Left edge" },
        { pos: el.x + el.w / 2, label: "Center" },
        { pos: el.x + el.w, label: "Right edge" },
    ];
    var hEdges = [
        { pos: el.y, label: "Top edge" },
        { pos: el.y + el.h / 2, label: "Middle" },
        { pos: el.y + el.h, label: "Bottom edge" },
    ];

    vEdges.forEach(function(ve) {
        // Check against page center first
        pageGuides.forEach(function(pg) {
            if (pg.type !== "v") return;
            if (Math.abs(ve.pos - pg.pos) < GUIDE_THRESHOLD) {
                guides.push({ pos: pg.pos, dir: "v", label: pg.label, isPage: true });
                snapped.v = pg.pos;
                vLabel = pg.label + " ↔ " + ve.label;
            }
        });
        // Check other elements
        S.E.forEach(function(other) {
            if (other.id === el.id) return;
            [other.x, other.x + other.w / 2, other.x + other.w].forEach(function(op) {
                if (Math.abs(ve.pos - op) < GUIDE_THRESHOLD) {
                    guides.push({ pos: op, dir: "v", label: "Aligned", isPage: false });
                    snapped.v = op;
                    vLabel = alignmentLabel(ve.pos, op, other, "v");
                }
            });
        });
    });

    hEdges.forEach(function(he) {
        pageGuides.forEach(function(pg) {
            if (pg.type !== "h") return;
            if (Math.abs(he.pos - pg.pos) < GUIDE_THRESHOLD) {
                guides.push({ pos: pg.pos, dir: "h", label: pg.label, isPage: true });
                snapped.h = pg.pos;
                hLabel = pg.label + " ↔ " + he.label;
            }
        });
        S.E.forEach(function(other) {
            if (other.id === el.id) return;
            [other.y, other.y + other.h / 2, other.y + other.h].forEach(function(op) {
                if (Math.abs(he.pos - op) < GUIDE_THRESHOLD) {
                    guides.push({ pos: op, dir: "h", label: "Aligned", isPage: false });
                    snapped.h = op;
                    hLabel = alignmentLabel(he.pos, op, other, "h");
                }
            });
        });
    });

    // Draw guide lines
    guides.forEach(function(g) {
        var line = document.createElement("div");
        line.className = "guide-line" + (g.isPage ? " guide-page" : "");
        if (g.dir === "v") {
            line.style.left = g.pos + "px";
            line.style.top = "0px";
            line.style.width = "1px";
            line.style.height = "100%";
        } else {
            line.style.left = "0px";
            line.style.top = g.pos + "px";
            line.style.width = "100%";
            line.style.height = "1px";
        }
        pg.appendChild(line);
        _guideLines.push(line);
    });

    // Draw alignment labels
    if (vLabel) {
        var lbl = document.createElement("div");
        lbl.className = "guide-label";
        lbl.textContent = vLabel;
        lbl.style.left = (snapped.v + 4) + "px";
        lbl.style.top = (el.y - 18) + "px";
        pg.appendChild(lbl);
        _guideLabels.push(lbl);
    }
    if (hLabel) {
        var lbl = document.createElement("div");
        lbl.className = "guide-label";
        lbl.textContent = hLabel;
        lbl.style.left = (el.x + el.w / 2 - 30) + "px";
        lbl.style.top = (snapped.h + 4) + "px";
        pg.appendChild(lbl);
        _guideLabels.push(lbl);
    }

    // Store snap targets for the drag handler to consume
    S._snapTarget = snapped;
}

function alignmentLabel(myPos, otherPos, otherEl, dir) {
    var diff = Math.abs(myPos - otherPos);
    if (diff > GUIDE_THRESHOLD) return null;
    var dirLabel = (dir === "v") ? "↕" : "↔";
    if (otherEl && otherEl.lbl) {
        return dirLabel + " " + otherEl.lbl;
    }
    return dirLabel + " Aligned";
}

function clearAlignmentGuides() {
    _guideLines.forEach(function(l) { if (l.parentNode) l.parentNode.removeChild(l); });
    _guideLabels.forEach(function(l) { if (l.parentNode) l.parentNode.removeChild(l); });
    _guideLines = [];
    _guideLabels = [];
    S._snapTarget = { v: null, h: null };
}

// ── Snap during drag ──
function applySnap(el, x, y, w, h) {
    if (!S._snapEnabled) return { x: x, y: y };
    var snap = S._snapTarget || { v: null, h: null };
    var GUIDE_THRESHOLD = S.GUIDE_THRESHOLD || 5;

    // Calculate where edges would be after move
    var newLeft = x, newRight = x + w, newCenterX = x + w / 2;
    var newTop = y, newBottom = y + h, newCenterY = y + h / 2;

    // Snap vertical edges to guide
    if (snap.v !== null) {
        if (Math.abs(newLeft - snap.v) < GUIDE_THRESHOLD) { x = snap.v; }
        else if (Math.abs(newRight - snap.v) < GUIDE_THRESHOLD) { x = snap.v - w; }
        else if (Math.abs(newCenterX - snap.v) < GUIDE_THRESHOLD) { x = snap.v - w / 2; }
    }
    // Snap horizontal edges to guide
    if (snap.h !== null) {
        if (Math.abs(newTop - snap.h) < GUIDE_THRESHOLD) { y = snap.h; }
        else if (Math.abs(newBottom - snap.h) < GUIDE_THRESHOLD) { y = snap.h - h; }
        else if (Math.abs(newCenterY - snap.h) < GUIDE_THRESHOLD) { y = snap.h - h / 2; }
    }
    return { x: x, y: y };
}

// ── Add element ──
function add(p) {
    var s = {
        id: "el" + (S.nid++),
        t: p.t || "stamp",
        s: p.s || "rectangle",
        x: p.x != null ? p.x : 50, y: p.y != null ? p.y : 50,  // 0 is a real position
        w: p.w || 80, h: p.h || 60,
        lbl: p.lbl || "",
        font: p.font || "HN",
        fs: p.fs || 12,
        align: p.align || "left",
        bdr: p.bdr || "solid",
        bdrC: p.bdrC || "#000",
        bdrW: p.bdrW || 0.5,
        fill: p.fill || "#FEFEFE",
        fillA: p.fillA || 100,
        img: p.img || "",
        /* Philatelic metadata */
        hdg: p.hdg || "",
        cat: p.cat || "",
        denom: p.denom || "",
        cond: p.cond || "",
        perf: p.perf || ""
    };
    if (p.role) s.role = p.role;  // a duplicated heading stays a heading
    S.CORE.normalizeStamp(s);     // stamps: black frame, no fill
    S.E.push(s);
    S.pushUndo();
    select(s.id);
    render();
}

// On screen the page is drawn at under one pixel per point, so 0.5 pt and 1 pt frames would
// both round to one pixel. Each frame gets a fixed screen width instead, so they look different;
// the exports draw the true point widths.
var FRAME_PX = { thin: 1, medium: 2, double: 3 };
function frameCSS(el) {
    var frame = S.CORE.frameOf(el), colour = el.bdrC || "#000000";
    if (frame === "none") return "none";
    return FRAME_PX[frame] + "px " + (frame === "double" ? "double " : "solid ") + colour;
}

// ── Select ──
function select(id) {
    S.sel = id;
    render();
    var el = S.E.find(function(x) { return x.id === id; });
    if (!el) {
        $("rp-content").style.display = "none";
        $("rp-none").style.display = "block";
        return;
    }
    $("rp-content").style.display = "block";
    $("rp-none").style.display = "none";
    $("px").value = mm(el.x);
    $("py").value = mm(el.y);
    $("pw").value = mm(el.w);
    $("ph").value = mm(el.h);
    $("plbl").value = el.lbl || "";
    // Stamps and free shapes have a frame; text items can be marked as a heading.
    var framed = el.t === "stamp" || el.t === "freehand";
    $("frame-sec").style.display = framed ? "block" : "none";
    $("frame-row").style.display = framed ? "flex" : "none";
    $("pbs").value = S.CORE.frameOf(el);
    $("phead-row").style.display = el.t === "text" ? "flex" : "none";
    $("phead").checked = el.role === "heading";
    $("pfnt").value = el.font || "HN";
    $("pfs").value = el.fs || 12;
    var isImg = el.t === "image";
    $("img-sec").style.display = isImg ? "block" : "none";
    $("img-row").style.display = isImg ? "flex" : "none";
    /* Philatelic fields — show for stamp type */
    var isStamp = el.t === "stamp";
    $("phil-sec").style.display = isStamp ? "block" : "none";
    $("phil-hdg-row").style.display = isStamp ? "flex" : "none";
    $("phil-cat-row").style.display = isStamp ? "flex" : "none";
    $("phil-denom-row").style.display = isStamp ? "flex" : "none";
    $("phil-cond-row").style.display = isStamp ? "flex" : "none";
    $("phil-perf-row").style.display = isStamp ? "flex" : "none";
    if (isStamp) {
        $("phdg").value = el.hdg || "";
        $("pcat").value = el.cat || "";
        $("pdenom").value = el.denom || "";
        $("pcond").value = el.cond || "";
        $("pperf").value = el.perf || "";
    }
}

function updateProps() {
    var el = S.E.find(function(x) { return x.id === S.sel; });
    if (!el) return;
    $("px").value = mm(el.x);
    $("py").value = mm(el.y);
    $("pw").value = mm(el.w);
    $("ph").value = mm(el.h);
}

// ── Status bar ──
function updateStatusBar() {
    if (!window.StampAlbum) return;
    var E = S.E;
    var sel = S.sel;
    // Page info
    if ($("sb-page")) {
        $("sb-page").textContent = "Page " + (S._currentPage + 1) + " of " + (S._pages ? S._pages.length : 1);
    }
    // Element count
    if ($("sb-elements")) {
        var n = E.length;
        $("sb-elements").textContent = n + " element" + (n !== 1 ? "s" : "");
    }
    // Selection info
    if ($("sb-selection")) {
        if (!sel) {
            $("sb-selection").textContent = "No selection";
        } else {
            var el = E.find(function(x) { return x.id === sel; });
            if (el) {
                var label = el.lbl || el.hdg || (el.t === "text" ? "Text" : "Stamp");
                $("sb-selection").textContent = el.t + " — " + label.substring(0, 30);
            }
        }
    }
    // Alignment info — show position + alignment state
    if ($("sb-align")) {
        if (!sel) {
            $("sb-align").textContent = "";
        } else {
            var el = E.find(function(x) { return x.id === sel; });
            if (el) {
                var pw = S._pw || 595, ph = S._ph || 842;
                var centerX = el.x + el.w / 2, centerY = el.y + el.h / 2;
                var hPos = centerX < pw * 0.35 ? "Left" : centerX > pw * 0.65 ? "Right" : "Center";
                var vPos = centerY < ph * 0.35 ? "Top" : centerY > ph * 0.65 ? "Bottom" : "Middle";
                var alignLabel = vPos + " " + hPos;
                if (S._snapTarget && (S._snapTarget.v !== null || S._snapTarget.h !== null)) {
                    alignLabel += " • Snapped";
                }
                $("sb-align").textContent = alignLabel;
            }
        }
    }
    // Dirty indicator
    var dirtyEl = $("sb-dirty");
    if (dirtyEl) {
        if (S._dirty) {
            dirtyEl.classList.remove("sb-dirty-hidden");
        } else {
            dirtyEl.classList.add("sb-dirty-hidden");
        }
    }
    // Zoom
    var zoomEl = $("sb-zoom");
    if (zoomEl) {
        zoomEl.textContent = Math.round(S._sc / 2.5 * 100) + "%";
    }
}

// ── Shape paths ──
function getShapePath(shape, w, h) {
    var hw = w / 2, hh = h / 2;
    if (shape === "oval") return "M " + hw + " 0 A " + hw + " " + hh + " 0 1 0 " + hw + " " + h + " A " + hw + " " + hh + " 0 1 0 " + hw + " 0 Z";
    if (shape === "diamond") return "M " + hw + " 0 L " + w + " " + hh + " L " + hw + " " + h + " L 0 " + hh + " Z";
    if (shape === "triangle") return "M " + hw + " 0 L " + w + " " + h + " L 0 " + h + " Z";
    if (shape === "hexagon") { var x1 = w * 0.25, x2 = w * 0.75, y2 = h * 0.5; return "M " + x1 + " 0 L " + x2 + " 0 L " + w + " " + y2 + " L " + x2 + " " + h + " L " + x1 + " " + h + " L 0 " + y2 + " Z"; }
    if (shape === "octagon") { var a = w * 0.3, b = h * 0.3; return "M " + a + " 0 L " + (w - a) + " 0 L " + w + " " + b + " L " + w + " " + (h - b) + " L " + (w - a) + " " + h + " L " + a + " " + h + " L 0 " + (h - b) + " L 0 " + b + " Z"; }
    if (shape === "pentagon") { var cx = w / 2; return "M " + cx + " 0 L " + w + " " + (h * 0.38) + " L " + (w * 0.82) + " " + h + " L " + (w * 0.18) + " " + h + " L 0 " + (h * 0.38) + " Z"; }
    return "M 0 0 L " + w + " 0 L " + w + " " + h + " L 0 " + h + " Z";
}

// ── Stamp captions ──
// Drawn where they print, from the same layout as the preview and exports
// (S.CORE.captionLayout, mirrored by engines/caption_layout.py).
var _measureCtx = null;
function captionMeasure(text, fontId, sizePt) {
    if (!_measureCtx) _measureCtx = document.createElement("canvas").getContext("2d");
    var fc = S.fontCSS(fontId);
    // Measure at 10 px per mm of font size, then convert back to mm
    _measureCtx.font = fc.style + " " + fc.weight + " " + (sizePt * S.CORE.CAPTION.MM_PER_PT * 10) + "px " + fc.family;
    return _measureCtx.measureText(text).width / 10;
}

function stampCaptionLines(el) {
    if (!S.CORE.hasCaptions(el)) return [];
    var sc = S._sc;
    return S.CORE.captionLayout(el, el.x / sc, el.y / sc, el.w / sc, el.h / sc, captionMeasure);
}

function captionNode(el, lines, d) {
    var sc = S._sc, first = lines[0];
    var lh = (first.bottom - first.top) * sc;
    var fc = S.fontCSS(first.fontId);
    var n = document.createElement("div");
    n.className = "caption caption-" + first.kind;
    n.textContent = lines.map(function(l) { return l.text; }).join("\n");
    // Children sit inside the frame, so offset by its width to line up with the box edge.
    n.style.cssText = "position:absolute;left:" + (-d.clientLeft) + "px;width:" + el.w + "px;" +
        "top:" + ((first.top - el.y / sc) * sc - d.clientTop) + "px;height:" + (lh * lines.length) + "px;" +
        "line-height:" + lh + "px;font-size:" + S.ptPx(first.sizePt) + "px;font-family:" + fc.family + ";" +
        "font-weight:" + (first.bold ? "bold" : "normal") + ";font-style:" + (first.italic ? "italic" : "normal") + ";" +
        "color:" + S.CORE.CAPTION.COLOR + ";text-align:center;white-space:pre;pointer-events:none;";
    return n;
}

function drawCaptions(d, el, lines) {
    d.classList.add("has-captions");
    var groups = [];
    lines.forEach(function(l) {
        var g = groups[groups.length - 1];
        if (g && g[0].kind === l.kind) g.push(l); else groups.push([l]);
    });
    groups.forEach(function(g) {
        var n = captionNode(el, g, d);
        if (g[0].kind === "description") {
            // The description is edited in place, below the box where it prints.
            n.classList.add("elbl");
            n.contentEditable = "true";
            n.spellcheck = false;
            n.style.pointerEvents = "auto";
            n.setAttribute("aria-label", "Description");
            var before = null;
            n.addEventListener("focus", function() {
                before = el.lbl || "";
                this.textContent = before;
                this.style.whiteSpace = "pre-wrap";
                this.style.height = "auto";
            });
            // Kept as typed, so a re-render (e.g. selecting another item) never loses the edit
            n.addEventListener("input", function() { el.lbl = this.textContent; });
            n.addEventListener("blur", function() {
                var changed = before !== null && (el.lbl || "") !== before;
                before = null;
                if (!changed) {  // put the printed lines back without a re-render, so Tab moves on
                    this.textContent = g.map(function(l) { return l.text; }).join("\n");
                    this.style.whiteSpace = "pre";
                    this.style.height = (g.length * (g[0].bottom - g[0].top) * S._sc) + "px";
                    return;
                }
                S.pushUndo();
                setTimeout(render, 0);  // after focus has moved, so render can put it back
            });
        }
        d.appendChild(n);
    });
}

// Flag stamps whose captions run into another item or past the page border.
function markCaptionWarnings(items) {
    var sc = S._sc, inset = S.borderInsetPx ? S.borderInsetPx(S._pageBorder) : 0;
    var area = { l: inset / sc, t: inset / sc, r: (S._pw - inset) / sc, b: (S._ph - inset) / sc };
    var warn = S.CORE.captionWarnings(items, area);
    items.forEach(function(it) {
        var why = warn[it.id];
        if (!why) return;
        var msg = why === "border" ? (inset ? "Captions run past the page border" : "Captions run past the page edge")
                                   : "Captions run into another item";
        it.node.classList.add("caption-warn");
        it.node.setAttribute("aria-description", msg);
        var b = document.createElement("span");
        b.className = "caption-warn-badge";
        b.textContent = "!";
        b.title = msg;
        b.setAttribute("aria-hidden", "true");
        it.node.appendChild(b);
    });
}

// ── Render canvas ──
function render() {
    if (S.updateSelectionUI) S.updateSelectionUI();
    var pg = $("page");
    // Every render rebuilds the elements, so remember which one had keyboard focus
    // and put focus back on its replacement afterwards.
    var active = document.activeElement;
    var focusedId = active && active.classList && active.classList.contains("cel") && pg.contains(active) ? active.dataset.id : null;
    var focusedDesc = active && active.classList && active.classList.contains("caption-description") && pg.contains(active)
        ? active.closest(".cel").dataset.id : null;
    pg.querySelectorAll(".cel").forEach(function(el) { el.remove(); });
    pg.querySelectorAll(".col-guide").forEach(function(el) { el.remove(); });
    var captionItems = [];
    S.E.forEach(function(el) {
        var d = document.createElement("div");
        d.className = "cel shape-" + (el.s || "rectangle") + (el.id === S.sel ? " selected" : "");
        d.dataset.id = el.id;
        d.tabIndex = 0;
        d.setAttribute("role", "group");  // not "button": the editable label inside is its own control
        d.setAttribute("aria-roledescription", "page item");
        d.setAttribute("aria-label", describeElement(el));
        if (el.id === S.sel) d.setAttribute("aria-current", "true");
        d.style.left = el.x + "px";
        d.style.top = el.y + "px";
        d.style.width = el.w + "px";
        d.style.height = el.h + "px";

        /* ── Philatelic stamp mount rendering ── */
        if (el.t === "stamp" && el.s === "rectangle") {
            // The stamp's frame as chosen in Properties: none, thin, medium or double, in black
            d.style.border = frameCSS(el);
            d.style.backgroundColor = el.fill || "#ffffff";
            d.classList.add("stamp-mount");

            // Inner content area
            var inner = document.createElement("div");
            inner.className = "stamp-inner";
            inner.style.cssText = "position:absolute;inset:4pt;display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden;";

            if (el.img) {
                var img = document.createElement("img");
                img.className = "eimg";
                img.src = el.img;
                img.style.maxWidth = "92%";
                img.style.maxHeight = "60%";
                inner.appendChild(img);
            }

            d.appendChild(inner);

        }
        else if (el.s && el.s !== "rectangle" && el.s !== "text" && el.s !== "freehand") {
            var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svg.setAttribute("class", "shape-svg");
            svg.setAttribute("viewBox", "0 0 " + el.w + " " + el.h);
            svg.style.position = "absolute";
            svg.style.top = "0";
            svg.style.left = "0";
            svg.style.width = "100%";
            svg.style.height = "100%";
            var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", getShapePath(el.s, el.w, el.h));
            path.setAttribute("fill", el.fill || "#fff");
            // Frame widths are points; the drawing is in canvas pixels
            var frame = S.CORE.frameOf(el);
            path.setAttribute("stroke", frame === "none" ? "none" : (el.bdrC || "#000000"));
            path.setAttribute("stroke-width", frame === "medium" ? FRAME_PX.medium : 1);  // see FRAME_PX
            if (frame === "double") {
                var path2 = path.cloneNode();
                path2.setAttribute("transform", "translate(3,3) scale(0.95)");
                path2.setAttribute("fill", "none");
                svg.appendChild(path2);
            }
            svg.appendChild(path);
            d.appendChild(svg);
            d.style.border = "none";
        } else {
            d.style.border = (el.bdrW || 0) + "pt " + (el.bdr || "solid") + " " + (el.bdrC || "#666");
            d.style.backgroundColor = el.fill || "transparent";
        }
        // "Fill alpha" applies to the fill only. It used to be applied as the whole
        // element's opacity, so text and images loaded from a file (parsed with a
        // transparent fill, alpha 0) were completely invisible on the canvas.
        if (el.fillA !== undefined && el.fillA < 100 && el.t !== "stamp") {
            var fa = Math.max(0, el.fillA) / 100;
            var fsvg = d.querySelector(".shape-svg path");
            if (fsvg) fsvg.setAttribute("fill-opacity", fa);
            else if (el.fill && el.fill !== "transparent") d.style.backgroundColor = S.withAlpha(el.fill, fa);
        }

        if (el.img && el.t !== "stamp") {
            var img = document.createElement("img");
            img.className = "eimg";
            img.src = el.img;
            d.appendChild(img);
        } else if (el.lbl && el.t !== "stamp") {
            var l = document.createElement("span");
            l.className = "elbl";
            l.textContent = el.lbl;
            l.contentEditable = "true";
            l.spellcheck = false;
            var fc = S.fontCSS(el.font || "HN");
            l.style.fontFamily = fc.family;
            l.style.fontSize = S.ptPx(el.fs || 12) + "px";
            if (el.t === "text") {
                // Match the exports: text boxes are top-anchored, padded 1 mm and
                // aligned per the element's alignment (left by default).
                l.style.textAlign = el.align || "left";
                l.style.width = "100%";
                l.style.maxWidth = "100%";
                l.style.boxSizing = "border-box";
                l.style.padding = Math.round(S._sc) + "px";
                d.style.alignItems = "flex-start";
            }
            l.style.fontWeight = fc.weight;
            l.style.fontStyle = fc.style;
            if (el.role === "heading") l.style.color = S.themeColor();  // marked headings take the theme colour
            l.addEventListener("blur", function() {
                el.lbl = this.textContent;
                var p = this.parentNode;
                this.style.minHeight = "";
                var nh = this.scrollHeight + 4;
                if (nh > p.offsetHeight) p.style.height = nh + "px";
                S.pushUndo();
            });
            d.appendChild(l);
        }
        if (el.t === "freehand") {
            d.style.border = "1pt dashed #999";
            d.style.backgroundColor = "rgba(200,200,200,0.1)";
            var fh = document.createElement("div");
            fh.style.cssText = "position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:10px;color:#999;text-align:center;";
            fh.innerHTML = "✎ Free Shape<br><small>Draw custom shape</small>";
            d.appendChild(fh);
        }

        var dim = document.createElement("span");
        dim.className = "dim";
        dim.textContent = mm(el.w) + "×" + mm(el.h) + "mm";
        d.appendChild(dim);

        ["nw", "ne", "sw", "se", "n", "s", "e", "w"].forEach(function(h) {
            var ha = document.createElement("div");
            ha.className = "rh " + h;
            ha.dataset.h = h;
            d.appendChild(ha);
        });

        d.addEventListener("mousedown", function(e) {
            if (e.target.classList.contains("rh")) return;
            if (e.target.classList.contains("caption-description")) {
                // Clicking the description edits it in place; it doesn't drag the stamp.
                e.stopPropagation();
                if (S.sel === el.id) return;  // already drawn: let the click place the caret
                e.preventDefault();
                select(el.id);  // redraws the page, so focus the new description
                var nd = $("page").querySelector('.cel[data-id="' + el.id + '"] .caption-description');
                if (nd) {
                    nd.focus();
                    var r = document.createRange(); r.selectNodeContents(nd); r.collapse(false);
                    var sl = window.getSelection(); sl.removeAllRanges(); sl.addRange(r);
                }
                return;
            }
            e.stopPropagation();
            select(el.id);
            S._drg = true;
            S._dragEl = el;
            S._dragH = "move";
            S._ds = { x: e.clientX, y: e.clientY, ox: el.x, oy: el.y, ow: el.w, oh: el.h };
        });

        pg.appendChild(d);
        var lines = stampCaptionLines(el);
        if (lines.length) drawCaptions(d, el, lines);
        captionItems.push({ id: el.id, box: { x: el.x / S._sc, y: el.y / S._sc, w: el.w / S._sc, h: el.h / S._sc }, lines: lines, node: d });
    });
    markCaptionWarnings(captionItems);

    // Draw column guides if columns are enabled
    if (S._colMode > 1) {
        var pageWidth = S._pw - 30 * S._sc;
        var pageMargin = 20 * S._sc;
        var colWidth = (pageWidth - (S._colMode - 1) * S._colGap * S._sc) / S._colMode;
        for (var i = 1; i < S._colMode; i++) {
            var guide = document.createElement("div");
            guide.className = "col-guide";
            guide.style.position = "absolute";
            guide.style.left = (pageMargin + i * (colWidth + S._colGap * S._sc)) + "px";
            guide.style.top = "0";
            guide.style.width = "1px";
            guide.style.height = S._ph + "px";
            guide.style.backgroundColor = "rgba(100, 150, 255, 0.3)";
            guide.style.pointerEvents = "none";
            guide.style.zIndex = "1";
            pg.appendChild(guide);
        }
    }
    if (focusedDesc) {
        var desc = pg.querySelector('.cel[data-id="' + focusedDesc + '"] .caption-description');
        if (desc) desc.focus({ preventScroll: true });
    }
    if (focusedId) {
        var again = pg.querySelector('.cel[data-id="' + focusedId + '"]');
        if (again) {
            S._refocusing = true;  // page_keys.js must not treat this as a new selection
            try { again.focus({ preventScroll: true }); } finally { S._refocusing = false; }
        }
    }
    // Update status bar
    if (S.updateStatusBar) S.updateStatusBar();
}

// What a screen reader says for an item on the page, e.g.
// "Rectangle stamp, Penny Black, 40 × 30 mm at 20, 25 mm"
var SHAPE_WORDS = { rectangle: "Rectangle", oval: "Oval", diamond: "Diamond", triangle: "Triangle",
                    hexagon: "Hexagon", octagon: "Octagon", pentagon: "Pentagon" };
function describeElement(el) {
    var kind;
    if (el.t === "text") kind = "Text";
    else if (el.t === "image") kind = "Image";
    else if (el.t === "freehand") kind = "Free shape";
    else kind = (SHAPE_WORDS[el.s] || "Rectangle") + " stamp";
    var parts = [kind];
    var text = (el.lbl || el.hdg || "").trim();
    if (text) parts.push(text.length > 60 ? text.substring(0, 60) + "…" : text);
    parts.push(mm(el.w) + " × " + mm(el.h) + " mm at " + mm(el.x) + ", " + mm(el.y) + " mm");
    return parts.join(", ");
}

// ── Exports ──
S.populateFonts = populateFonts;
S.drawAlignmentGuides = drawAlignmentGuides;
S.clearAlignmentGuides = clearAlignmentGuides;
S.applySnap = applySnap;
S.add = add;
S.select = select;
S.updateStatusBar = updateStatusBar;
S.updateProps = updateProps;
S.getShapePath = getShapePath;
S.render = render;
S.describeElement = describeElement;

})();
