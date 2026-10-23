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
    og.label = S.t("msg.fonts_standard");
    stdFonts.forEach(function(f) { var o = document.createElement("option"); o.value = f.v; o.textContent = f.t; og.appendChild(o); });
    pfnt.appendChild(og);
    if (S.SYSTEM_FONTS && S.SYSTEM_FONTS.length) {  // from the app: each one prints
        var og2 = document.createElement("optgroup");
        og2.label = S.t("msg.fonts_system");
        S.SYSTEM_FONTS.forEach(function(f) { var o = document.createElement("option"); o.value = f; o.textContent = f; og2.appendChild(o); });
        pfnt.appendChild(og2);
    }
    var el = _panelFor && S.E.find(function(x) { return x.id === _panelFor; });
    if (el && el.t === "text") showFont(el.font || "HN");  // the list was rebuilt under a text item
}

// Show a text item's font in the Font list. A font the album uses that this computer
// doesn't have (it was chosen on another computer) is listed as such: it prints in Helvetica.
function showFont(font) {
    var pfnt = $("pfnt");
    var old = pfnt.querySelector("option[data-missing]");
    if (old) old.remove();
    var known = [].some.call(pfnt.options, function(o) { return o.value === font; });
    if (!known) {
        var o = document.createElement("option");
        o.value = font;
        o.textContent = S.t("msg.font_not_on_this_computer", { name: font });
        o.setAttribute("data-missing", "");
        pfnt.appendChild(o);
    }
    pfnt.value = font;
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
        { pos: pw / 2, type: "v", label: S.t("msg.guide_page_center") },
        { pos: ph / 2, type: "h", label: S.t("msg.guide_page_center") },
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
        { pos: el.x, label: S.t("msg.guide_left_edge") },
        { pos: el.x + el.w / 2, label: S.t("msg.guide_center") },
        { pos: el.x + el.w, label: S.t("msg.guide_right_edge") },
    ];
    var hEdges = [
        { pos: el.y, label: S.t("msg.guide_top_edge") },
        { pos: el.y + el.h / 2, label: S.t("msg.guide_middle") },
        { pos: el.y + el.h, label: S.t("msg.guide_bottom_edge") },
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
                    guides.push({ pos: op, dir: "v", label: S.t("msg.guide_aligned"), isPage: false });
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
                    guides.push({ pos: op, dir: "h", label: S.t("msg.guide_aligned"), isPage: false });
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
        cap: p.cap || "",  // a picture's caption, printed below it
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
// both round to one pixel. Each frame line gets a fixed screen width instead, so they look
// different; the exports draw the true point widths. Lines sit where they print (see
// S.CORE.frameLines): the frame is outside the stamp, past the album's mount and gap.
var FRAME_PX = { thin: 1, medium: 2, double: 1 };
var FRAME_DOUBLE_STEP_PX = 2;  // centre to centre, so the two lines of a double frame stay apart
var SVG_NS = "http://www.w3.org/2000/svg";

function outlineNode(o, attrs) {
    var n;
    if (o.kind === "ellipse") {
        n = document.createElementNS(SVG_NS, "ellipse");
        n.setAttribute("cx", o.cx); n.setAttribute("cy", o.cy); n.setAttribute("rx", o.rx); n.setAttribute("ry", o.ry);
    } else if (o.kind === "polygon") {
        n = document.createElementNS(SVG_NS, "polygon");
        n.setAttribute("points", o.points.map(function(p) { return p[0] + "," + p[1]; }).join(" "));
    } else {
        n = document.createElementNS(SVG_NS, "rect");
        n.setAttribute("x", o.x); n.setAttribute("y", o.y); n.setAttribute("width", o.w); n.setAttribute("height", o.h);
    }
    Object.keys(attrs).forEach(function(k) { n.setAttribute(k, attrs[k]); });
    return n;
}

// A stamp's fill, its size guide and its frame, in canvas px relative to the stamp's box.
function stampFrameSVG(el) {
    var sc = S._sc, frame = S.CORE.frameOf(el), colour = el.bdrC || "#000000";
    var lines = S.CORE.frameLines(el).map(function(l) { return { offset: l.offset * sc, width: FRAME_PX[frame] }; });
    if (frame === "double" && lines.length === 2) lines[0].offset = lines[1].offset - FRAME_DOUBLE_STEP_PX;
    var reach = Math.max(S.CORE.frameOutset(el) * sc, lines.length ? lines[lines.length - 1].offset + 1 : 0) + 2;
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", "stamp-frame");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("viewBox", (-reach) + " " + (-reach) + " " + (el.w + 2 * reach) + " " + (el.h + 2 * reach));
    svg.style.cssText = "left:" + (-reach) + "px;top:" + (-reach) + "px;width:" + (el.w + 2 * reach) + "px;height:" + (el.h + 2 * reach) + "px;";
    var own = S.CORE.shapeOutline(el.s, 0, 0, el.w, el.h, 0);
    svg.appendChild(outlineNode(own, { "class": "stamp-fill", fill: el.fill || "#ffffff", stroke: "none" }));
    // The stamp's own size (from the catalogue): a faint dashed line, never printed
    svg.appendChild(outlineNode(own, { "class": "stamp-size-guide", fill: "none", stroke: "#8a8a8a",
        "stroke-width": 1, "stroke-dasharray": "3 2", "vector-effect": "non-scaling-stroke" }));
    // The mount's edge (the album's overhang), a fainter dotted line, never printed
    var over = S.CORE.getMount().overhang;
    if (lines.length && over > 0) {
        svg.appendChild(outlineNode(S.CORE.shapeOutline(el.s, 0, 0, el.w, el.h, over * sc), { "class": "mount-edge",
            fill: "none", stroke: "#a39b8e", "stroke-width": 1, "stroke-dasharray": "1 2", "vector-effect": "non-scaling-stroke" }));
    }
    lines.forEach(function(l) {
        svg.appendChild(outlineNode(S.CORE.shapeOutline(el.s, 0, 0, el.w, el.h, l.offset),
            { "class": "frame-line", fill: "none", stroke: colour, "stroke-width": l.width, "stroke-linejoin": "miter" }));
    });
    return svg;
}

// "Frame 24.4 × 27.4 mm: mount 1.5 mm, then 1 mm to the frame line" for the selected stamp.
function frameNote(el) {
    if (!el || el.t !== "stamp") return "";
    var sc = S._sc, o = S.CORE.frameOutset(el);
    var w = el.w / sc, h = el.h / sc;
    var f = function(v) { return (Math.round(v * 10) / 10).toString(); };
    if (!o) return S.t("msg.no_frame_note", { w: f(w), h: f(h) });
    var m = S.CORE.getMount();
    if (m.overhang > 0) {
        return S.t("msg.frame_note_mount", { fw: f(w + 2 * o), fh: f(h + 2 * o), over: f(m.overhang), gap: f(m.gap), w: f(w), h: f(h) });
    }
    return S.t("msg.frame_note", { fw: f(w + 2 * o), fh: f(h + 2 * o), clear: f(m.gap), w: f(w), h: f(h) });
}
function updateFrameNote() {
    var n = $("pframe-size");
    if (!n) return;
    n.textContent = frameNote(S.E.find(function(x) { return x.id === S.sel; }));
}

// ── Select ──
// The right panel names what is selected; with nothing selected it holds the
// album and page settings (page size, border, theme, headings, snap).
var PANEL_TITLES = { stamp: "msg.kind_stamp", text: "msg.kind_text", image: "msg.kind_image",
                     freehand: "msg.kind_freehand" };
function panelTitle(el) {
    return S.t(el ? (PANEL_TITLES[el.t] || "msg.kind_stamp") : "ui.album_and_page");
}
// The details a reader may not need, under More details (optional): Value,
// Condition, Perforation and Catalogue no.
var MORE_FIELDS = ["denom", "cond", "perf", "cat", "exp"];
function moreFilled(el) {
    return MORE_FIELDS.filter(function(k) { return el && el[k] && String(el[k]).trim(); }).length;
}
function updateMoreCount(el) {
    var n = moreFilled(el);
    $("more-count").textContent = n ? S.t("msg.n_filled_in", { count: n }) : S.t("msg.none_filled_in");
}
function setMoreOpen(open) {
    $("more-toggle").setAttribute("aria-expanded", open ? "true" : "false");
    $("more-body").hidden = !open;
}
function show(id, on) { $(id).hidden = !on; }

// Which item the panel shows (null: the album settings). Many paths clear or
// replace the selection directly (Escape, undo, a page switch, opening a file),
// so render() brings the panel in step whenever this no longer matches.
var _panelFor = null;

// The item the panel's fields belong to. Field handlers use this, not S.sel, because
// the selection can change (a click on another stamp) before a field's edit is counted.
function panelItem() {
    return _panelFor ? S.E.find(function(x) { return x.id === _panelFor; }) || null : null;
}

// Words typed in the panel are saved into the item as they are typed (S.panelTyped), so
// nothing is held back until the field is left. The undo step for them is recorded once,
// when the field is left or the panel moves on to another item (commitPanelEdit).
var _typed = false, _committing = false, _renderQueued = false;
function panelTyped() {
    if (!_typed) {
        _typed = true;
        S._dirty = true;
        S.updateTitle();
    }
    S.scheduleDraftSave();
    if (_renderQueued) return;  // one redraw per frame, however fast the typing
    _renderQueued = true;
    (window.requestAnimationFrame || setTimeout)(function() { _renderQueued = false; render(); });
}
function commitPanelEdit() {
    if (_committing) return;
    _committing = true;
    try {
        // A number half typed in a panel box (Position, Size, Font size) counts too.
        var a = document.activeElement;
        var typed = a && a.tagName === "INPUT" && (a.type === "number" || a.type === "text");
        if (typed && !a.hasAttribute("data-live") && $("rp-content").contains(a)) {
            a.dispatchEvent(new Event("change"));
        }
        if (_typed) {
            _typed = false;
            S.pushUndo();
        }
    } finally {
        _committing = false;
    }
}

function syncPanel() {
    var el = S.E.find(function(x) { return x.id === S.sel; });
    if ((el ? el.id : null) !== _panelFor) fillPanel(el, true);
}

function select(id) {
    var changed = id !== _panelFor;
    S.sel = id;
    render();
    fillPanel(S.E.find(function(x) { return x.id === id; }), changed);
}

function fillPanel(el, changed) {
    if ((el ? el.id : null) !== _panelFor) commitPanelEdit();  // the last item's edit, before its fields are replaced
    _panelFor = el ? el.id : null;
    $("rp-title").textContent = panelTitle(el);
    $("rp-content").hidden = !el;
    $("rp-none").hidden = !!el;
    if (!el) return;
    $("px").value = mm(el.x);
    $("py").value = mm(el.y);
    $("pw").value = mm(el.w);
    $("ph").value = mm(el.h);
    $("plbl").value = el.lbl || "";
    var isStamp = el.t === "stamp", isText = el.t === "text", isImg = el.t === "image";
    // Stamps and free shapes have a frame; text items can be marked as a heading.
    var framed = isStamp || el.t === "freehand";
    show("frame-sec", framed);
    show("frame-row", framed);
    $("pbs").value = S.CORE.frameOf(el);
    // A stamp's caption: Heading and Name (the description line under the stamp;
    // the file still calls it the label). A text item's words are its Text.
    $("cap-sec").textContent = S.t(isStamp || isImg ? "ui.caption" : isText ? "ui.text" : "ui.label");
    $("plbl-name").textContent = S.t(isStamp ? "ui.name" : isText ? "ui.text" : "ui.label");
    show("phil-hdg-row", isStamp);
    show("phead-row", isText);
    show("phead-hint", isText);
    // An image has a caption of its own (below it, 8 pt italic) instead of a label:
    // its label is the file's name, which is never printed.
    show("lbl-row", !isImg);
    show("pcap-row", isImg);
    show("pcap-note", isImg);
    $("pcap").value = el.cap || "";
    fillRepro(el, isImg);
    $("phead").checked = el.role === "heading";
    fillChapter(el, isText);
    showFont(el.font || "HN");
    $("pfs").value = el.fs || 12;
    // Font and Size are for text items only. Captions (stamps, free shapes) use the
    // bundled caption font at fixed sizes. Any values stored on an item are kept.
    show("font-row", isText);
    show("fsize-row", isText);
    show("pcapfont-note", isStamp);
    show("img-sec", isImg);
    show("img-row", isImg);
    show("img-file", isImg && !!el.img);
    if (isImg) $("img-file").textContent = S.t("msg.image_file", { name: String(el.img || "").split("/").pop() });
    show("more-wrap", isStamp);
    if (isStamp) {
        $("phdg").value = el.hdg || "";
        $("pcat").value = el.cat || "";
        $("pdenom").value = el.denom || "";
        $("pcond").value = el.cond || "";
        $("pperf").value = el.perf || "";
        $("pexp").checked = !!el.exp;
        updateMoreCount(el);
        // Folded unless one is filled in; a choice made by hand lasts while the stamp stays selected.
        if (changed) setMoreOpen(moreFilled(el) > 0);
    }
}

// A picture that is a copy of a real item: its original's size and how it compares (FIP: at
// least 25% larger or smaller).
function fillRepro(el, isImg) {
    var on = isImg && S.CORE.isReproduction(el);
    // The editor keeps sizes in canvas px; the comparison is in mm, as the original's size
    var inMm = Object.assign({}, el, { w: el.w / S._sc, h: el.h / S._sc });
    show("prepro-row", isImg);
    show("prepro-hint", isImg);
    show("porig-row", on);
    show("prepro-note", on);
    show("prepro-fit-row", on && S.CORE.reproTooClose(inMm));
    $("prepro").checked = on;
    if (!on) return;
    $("porig-w").value = el.origW;
    $("porig-h").value = el.origH;
    var pct = Math.round(S.CORE.reproScale(inMm) * 100);
    var close = S.CORE.reproTooClose(inMm), note = $("prepro-note");
    note.textContent = S.t(close ? "msg.repro_too_close" : "msg.repro_ok", { pct: pct });
    note.classList.toggle("warn", close);
}

// A text item's link to a plan chapter: offered when the album has a title and plan page,
// except on the items that page is made of.
function fillChapter(el, isText) {
    var entries = isText && !el.part && S.currentPlanEntries ? S.currentPlanEntries() : [];
    show("pchap-row", entries.length > 0);
    show("pchap-note", entries.length > 0);
    if (!entries.length) return;
    var sel = $("pchap");
    sel.innerHTML = "";
    var none = document.createElement("option");
    none.value = "";
    none.textContent = S.t("msg.not_linked");
    sel.appendChild(none);
    entries.forEach(function(e) {
        var o = document.createElement("option");
        o.value = e.num;
        o.textContent = S.CORE.chapterHeading(e);
        sel.appendChild(o);
    });
    var now = S.CORE.chapterFor(el, entries);
    sel.value = now ? now.num : "";
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
        $("sb-page").textContent = S.t("msg.page_n_of", { n: S._currentPage + 1, total: S._pages ? S._pages.length : 1 });
    }
    // Element count
    if ($("sb-elements")) {
        var n = E.length;
        $("sb-elements").textContent = S.t("msg.count_elements", { count: n });
    }
    // Selection info
    if ($("sb-selection")) {
        if (!sel) {
            $("sb-selection").textContent = S.t("msg.no_selection");
        } else {
            var el = E.find(function(x) { return x.id === sel; });
            if (el) {
                var label = el.lbl || el.hdg || S.t(el.t === "text" ? "msg.kind_text" : "msg.kind_stamp");
                $("sb-selection").textContent = S.t("msg.sel_" + (el.t === "text" || el.t === "image" || el.t === "freehand" ? el.t : "stamp")) + " — " + label.substring(0, 30);
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
                var hPos = centerX < pw * 0.35 ? "left" : centerX > pw * 0.65 ? "right" : "center";
                var vPos = centerY < ph * 0.35 ? "top" : centerY > ph * 0.65 ? "bottom" : "middle";
                var alignLabel = S.t("msg.pos_" + vPos + "_" + hPos);
                if (S._snapTarget && (S._snapTarget.v !== null || S._snapTarget.h !== null)) {
                    alignLabel += " • " + S.t("msg.snapped");
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
    // Zoom: zoom.js keeps #sb-zoom up to date
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
// (S.CORE.captionLayout, mirrored by engines/caption_layout.py). Measured with the bundled
// caption font's advance widths (caption_metrics.js), so the lines break as in the exports.
function stampCaptionLines(el) {
    if (!S.CORE.hasCaptions(el)) return [];
    var sc = S._sc;
    return S.CORE.captionLayout(el, el.x / sc, el.y / sc, el.w / sc, el.h / sc, null,
                                { headingWeight: S._captionHeading });
}

function captionNode(el, lines, d) {
    var sc = S._sc, first = lines[0];
    var lh = (first.bottom - first.top) * sc;
    var n = document.createElement("div");
    n.className = "caption caption-" + first.kind;
    n.textContent = lines.map(function(l) { return l.text; }).join("\n");
    // Children sit inside the frame, so offset by its width to line up with the box edge.
    n.style.cssText = "position:absolute;left:" + (-d.clientLeft) + "px;width:" + el.w + "px;" +
        "top:" + ((first.top - el.y / sc) * sc - d.clientTop) + "px;height:" + (lh * lines.length) + "px;" +
        "line-height:" + lh + "px;font-size:" + S.ptPx(first.sizePt) + "px;" +
        "font-weight:" + first.weight + ";font-style:" + (first.italic ? "italic" : "normal") + ";" +
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
        // The stamp's name and a picture's caption are edited in place, where they print.
        var field = g[0].kind === "description" ? "lbl" : g[0].kind === "picture" ? "cap" : null;
        if (field) {
            n.classList.add("elbl", "caption-editable");
            n.contentEditable = "true";
            n.spellcheck = false;
            n.style.pointerEvents = "auto";
            n.setAttribute("aria-label", S.t(field === "cap" ? "ui.caption_below_the_image" : "ui.name_below_the_stamp"));
            var before = null;
            n.addEventListener("focus", function() {
                before = el[field] || "";
                this.textContent = before;
                this.style.whiteSpace = "pre-wrap";
                this.style.height = "auto";
            });
            // Kept as typed, so a re-render (e.g. selecting another item) never loses the edit
            n.addEventListener("input", function() { el[field] = this.textContent; });
            n.addEventListener("blur", function() {
                var changed = before !== null && (el[field] || "") !== before;
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
        var msg = S.t("msg.warn_" + why.replace("-", "_") + (why.indexOf("border") !== -1 ? (inset ? "_border" : "_edge") : ""));
        it.node.classList.add("caption-warn");
        if (why.indexOf("frame") === 0) it.node.classList.add("frame-warn");
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
    var focusedDesc = active && active.classList && active.classList.contains("caption-editable") && pg.contains(active)
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
        if (el.t === "stamp") {
            // The fill and the frame chosen in Properties (none, thin, medium or double, in black),
            // drawn outside the stamp's own size, which shows as a dashed line.
            d.classList.add("stamp-el");
            if (!el.s || el.s === "rectangle") d.classList.add("stamp-mount");
            d.style.border = "none";
            d.style.backgroundColor = "transparent";
            d.appendChild(stampFrameSVG(el));
            // The selection outline goes round the frame, not through it
            d.style.outlineOffset = Math.round(S.CORE.frameOutset(el) * S._sc + 3) + "px";

            if (!el.s || el.s === "rectangle") {
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
        }
        else if (el.s && el.s !== "rectangle" && el.s !== "text" && el.s !== "freehand") {
            var svg = document.createElementNS(SVG_NS, "svg");
            svg.setAttribute("class", "shape-svg");
            svg.setAttribute("viewBox", "0 0 " + el.w + " " + el.h);
            svg.style.position = "absolute";
            svg.style.top = "0";
            svg.style.left = "0";
            svg.style.width = "100%";
            svg.style.height = "100%";
            var path = document.createElementNS(SVG_NS, "path");
            path.setAttribute("d", getShapePath(el.s, el.w, el.h));
            path.setAttribute("fill", el.fill || "#fff");
            path.setAttribute("stroke", "none");
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
            fh.textContent = S.t("ui.free_shape");
            fh.appendChild(document.createElement("br"));
            fh.appendChild(document.createElement("small")).textContent = S.t("msg.draw_custom_shape");
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
            if (e.target.classList.contains("caption-editable")) {
                // Clicking the name (or a picture's caption) edits it in place; it doesn't drag.
                e.stopPropagation();
                if (S.sel === el.id) return;  // already drawn: let the click place the caret
                e.preventDefault();
                select(el.id);  // redraws the page, so focus the new description
                var nd = $("page").querySelector('.cel[data-id="' + el.id + '"] .caption-editable');
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
            S._ds = { x: e.clientX, y: e.clientY, ox: el.x, oy: el.y, ow: el.w, oh: el.h, z: S.zoom || 1 };
        });

        pg.appendChild(d);
        var lines = stampCaptionLines(el);
        if (lines.length) drawCaptions(d, el, lines);
        // A stamp's outer edge is its frame's
        var box = S.CORE.frameBox(el, el.x / S._sc, el.y / S._sc, el.w / S._sc, el.h / S._sc);
        captionItems.push({ id: el.id, box: box, lines: lines, node: d, framed: el.t === "stamp" && box.w > el.w / S._sc });
    });
    markCaptionWarnings(captionItems);
    if (S.updateThumb) S.updateThumb();  // the open page's picture beside the page
    updateFrameNote();
    syncPanel();
    if (S.syncImageList) S.syncImageList();  // the Images section lists the album's images

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
        var desc = pg.querySelector('.cel[data-id="' + focusedDesc + '"] .caption-editable');
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
var SHAPES = ["rectangle", "oval", "diamond", "triangle", "hexagon", "octagon", "pentagon"];
function describeElement(el) {
    var kind;
    if (el.t === "text") kind = S.t("msg.kind_text");
    else if (el.t === "image") kind = S.t("msg.kind_image");
    else if (el.t === "freehand") kind = S.t("msg.kind_freehand");
    else kind = S.t("msg.stamp_" + (SHAPES.indexOf(el.s) !== -1 ? el.s : "rectangle"));
    var parts = [kind];
    var text = (el.lbl || el.hdg || "").trim();
    if (text) parts.push(text.length > 60 ? text.substring(0, 60) + "…" : text);
    parts.push(S.t("msg.size_at", { w: mm(el.w), h: mm(el.h), x: mm(el.x), y: mm(el.y) }));
    return parts.join(", ");
}

// ── Exports ──
S.populateFonts = populateFonts;
S.drawAlignmentGuides = drawAlignmentGuides;
S.clearAlignmentGuides = clearAlignmentGuides;
S.applySnap = applySnap;
S.add = add;
S.select = select;
S.panelItem = panelItem;
S.fillRepro = fillRepro;
S.panelTyped = panelTyped;
S.commitPanelEdit = commitPanelEdit;
S.updateMoreCount = updateMoreCount;
S.setMoreOpen = setMoreOpen;
S.panelTitle = panelTitle;
S.updateStatusBar = updateStatusBar;
S.updateProps = updateProps;
S.getShapePath = getShapePath;
S.render = render;
S.describeElement = describeElement;

})();
