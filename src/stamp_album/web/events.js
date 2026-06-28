"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, mm = S.mm, showToast = S.showToast;
var pushUndo = S.pushUndo, render = S.render, select = S.select;
var updateProps = S.updateProps, drawAlignmentGuides = S.drawAlignmentGuides;
var clearAlignmentGuides = S.clearAlignmentGuides;
var add = S.add, undo = S.undo, redo = S.redo;
var newAlbum = S.newAlbum, saveFile = S.saveFile, loadFileList = S.loadFileList;
var uploadImageFile = S.uploadImageFile, buildDSL = S.buildDSL, parseDSL = S.parseDSL;

// ── Event initialization ──
function init() {
    if (S._init) return;
    S._init = true;
    var pg = $("page");
    if (!pg) return;

    // Palette drag
    document.querySelectorAll(".p-item[draggable]").forEach(function(it) {
        it.addEventListener("dragstart", function(e) {
            e.dataTransfer.setData("text/plain", JSON.stringify({
                t: it.dataset.t, s: it.dataset.s || "rectangle", st: it.dataset.st || "",
                w: parseFloat(it.dataset.w) || 80, h: parseFloat(it.dataset.h) || 60,
                font: "HN", fs: 12
            }));
            e.dataTransfer.effectAllowed = "copy";
        });
    });

    // Page drop
    pg.addEventListener("dragover", function(e) { e.preventDefault(); pg.classList.add("drag-over"); });
    pg.addEventListener("dragleave", function() { pg.classList.remove("drag-over"); });
    pg.addEventListener("drop", function(e) {
        e.preventDefault();
        pg.classList.remove("drag-over");
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            for (var i = 0; i < e.dataTransfer.files.length; i++) {
                var f = e.dataTransfer.files[i];
                if (f.type.startsWith("image/")) {
                    uploadImageFile(f, function(imgName) {
                        var r = pg.getBoundingClientRect();
                        var x = Math.max(0, Math.min(Math.round((e.clientX - r.left) / S._sn) * S._sn, S._pw - 40));
                        var y = Math.max(0, Math.min(Math.round((e.clientY - r.top) / S._sn) * S._sn, S._ph - 30));
                        add({ t: "image", s: "rectangle", x: x, y: y, w: 80, h: 60,
                            lbl: f.name, img: "/images/" + imgName,
                            bdr: "solid", bdrC: "#999", bdrW: 0.5, fill: "#fff", fillA: 100, font: "HN", fs: 12 });
                    });
                    return;
                }
            }
        }
        var d;
        try { d = JSON.parse(e.dataTransfer.getData("text/plain")); } catch (_) { return; }
        var r = pg.getBoundingClientRect();
        var x = Math.max(0, Math.min(Math.round((e.clientX - r.left) / S._sn) * S._sn, S._pw - 40));
        var y = Math.max(0, Math.min(Math.round((e.clientY - r.top) / S._sn) * S._sn, S._ph - 30));
        var w = d.w || 80, h = d.h || 60;
        if (d.t === "text") { w = 120; h = d.st === "heading" ? 24 : d.st === "desc" ? 16 : 18; }
        if (d.t === "freehand") { w = 100; h = 80; }
        add({ t: d.t || "stamp", s: d.s || "rectangle", x: x, y: y, w: w, h: h,
            lbl: d.t === "text" ? (d.st === "heading" ? "Heading" : d.st === "desc" ? "Description" : "Label") : "",
            font: d.font || "HN", fs: d.st === "heading" ? 16 : d.st === "desc" ? 10 : 12,
            bdr: S._defBdr, bdrC: S._defBdrC, bdrW: 1, fill: S._defFillC, fillA: 100, img: "" });
    });

    // Mouse on canvas
    pg.addEventListener("mousedown", function(e) {
        var el = e.target.closest(".cel");
        if (!el) { S.sel = null; render(); return; }
        var obj = S.E.find(function(x) { return x.id === el.dataset.id; });
        if (!obj) return;
        if (e.target.classList.contains("rh")) { S._dragH = e.target.dataset.h; } else { S._dragH = "move"; }
        select(obj.id);
        S._drg = true;
        S._dragEl = obj;
        S._ds = { x: e.clientX, y: e.clientY, ox: obj.x, oy: obj.y, ow: obj.w, oh: obj.h };
        e.preventDefault();
        e.stopPropagation();
    });

    document.addEventListener("mousemove", function(e) {
        if (!S._drg || !S._dragEl) return;
        var dx = Math.round((e.clientX - S._ds.x) / S._sn) * S._sn;
        var dy = Math.round((e.clientY - S._ds.y) / S._sn) * S._sn;
        var h = S._dragH, x = S._ds.ox, y = S._ds.oy, w = S._ds.ow, oh = S._ds.oh;
        if (h === "move") { x += dx; y += dy; } else {
            if (h.indexOf("w") >= 0) { x += dx; w -= dx; }
            if (h.indexOf("e") >= 0) { w += dx; }
            if (h.indexOf("n") >= 0) { y += dy; oh -= dy; }
            if (h.indexOf("s") >= 0) { oh += dy; }
            if (w < 10) w = 10;
            if (oh < 10) oh = 10;
        }

        // Snap-to-guide: use centralized applySnap
        if (h === "move") {
            var snapped = S.applySnap(S._dragEl, x, y, w, oh);
            x = snapped.x;
            y = snapped.y;
        }

        S._dragEl.x = Math.max(0, Math.min(x, S._pw - S._dragEl.w));
        S._dragEl.y = Math.max(0, Math.min(y, S._ph - S._dragEl.h));
        S._dragEl.w = Math.min(w, S._pw - S._dragEl.x);
        S._dragEl.h = Math.min(oh, S._ph - S._dragEl.y);
        render();
        updateProps();
        if (h === "move") drawAlignmentGuides(S._dragEl);
    });

    document.addEventListener("mouseup", function() {
        if (S._drg && S._dragEl) { pushUndo(); }
        S._drg = false;
        S._dragEl = null;
        S._dragH = null;
        clearAlignmentGuides();
    });

    // ── Props Panel ──
    function bindProp(id, key, transform) {
        $(id).addEventListener("change", function() {
            var el = S.E.find(function(x) { return x.id === S.sel; });
            if (!el) return;
            el[key] = transform ? transform(this.value) : mm(parseFloat(this.value) || 0);
            pushUndo();
            render();
        });
    }
    bindProp("px", "x");
    bindProp("py", "y");
    bindProp("pw", "w");
    bindProp("ph", "h");
    $("plbl").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.lbl = this.value; pushUndo(); render();
    });
    $("pbs").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.bdr = this.value; pushUndo(); render();
    });
    $("pbc").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.bdrC = this.value; pushUndo(); render();
    });
    $("pbw").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.bdrW = parseFloat(this.value) || 0; pushUndo(); render();
    });
    $("pfc").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.fill = this.value; pushUndo(); render();
    });
    $("pfa").addEventListener("input", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.fillA = parseInt(this.value); $("pfa-v").textContent = this.value + "%";
    });
    $("pfa").addEventListener("change", function() { pushUndo(); render(); });
    $("pfnt").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.font = this.value; pushUndo(); render();
    });
    $("pfs").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.fs = parseFloat(this.value) || 12; pushUndo(); render();
    });

    // ── Philatelic metadata fields ──
    $("phdg").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.hdg = this.value; pushUndo(); render();
    });
    $("pcat").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.cat = this.value; pushUndo(); render();
    });
    $("pdenom").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.denom = this.value; pushUndo(); render();
    });
    $("pcond").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.cond = this.value; pushUndo(); render();
    });
    $("pperf").addEventListener("change", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.perf = this.value; pushUndo(); render();
    });

    // ── Buttons ──
    $("btn-new").addEventListener("click", newAlbum);
    $("btn-open").addEventListener("click", function() { $("file-inp").click(); });
    $("btn-save").addEventListener("click", saveFile);
    $("btn-dup").addEventListener("click", function() {
        if (!S.sel) { showToast("Select an element first", "error"); return; }
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        add(Object.assign({}, el, { id: "el" + (S.nid++), x: el.x + 20, y: el.y + 20 }));
    });
    $("btn-grid").addEventListener("click", function() {
        if (!S.sel) { showToast("Select a stamp to duplicate in grid", "error"); return; }
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        var cols = parseInt(prompt("Number of columns:", "3")) || 3;
        var rows = parseInt(prompt("Number of rows:", "3")) || 3;
        var gapX = parseFloat(prompt("Horizontal gap (mm):", "5")) || 5;
        var gapY = parseFloat(prompt("Vertical gap (mm):", "5")) || 5;
        var startX = el.x, startY = el.y;
        for (var r = 0; r < rows; r++) {
            for (var c = 0; c < cols; c++) {
                if (r === 0 && c === 0) continue;
                add(Object.assign({}, el, { id: "el" + (S.nid++),
                    x: startX + c * (el.w + S.px(gapX)),
                    y: startY + r * (el.h + S.px(gapY)),
                    lbl: el.lbl ? el.lbl + " (" + (r + 1) + "," + (c + 1) + ")" : "" }));
            }
        }
    });
    $("btn-del").addEventListener("click", function() {
        if (!S.sel) return;
        S.E = S.E.filter(function(x) { return x.id !== S.sel; });
        S.sel = null;
        pushUndo();
        render();
        updateProps();
    });
    $("btn-undo").addEventListener("click", undo);
    $("btn-redo").addEventListener("click", redo);
    $("btn-wizard").addEventListener("click", function() {
        $("wizard-panel").classList.toggle("open");
    });
    $("btn-cls-wiz").addEventListener("click", function() {
        $("wizard-panel").classList.remove("open");
    });

    // ── Alignment toolbar ──
    $("btn-align-l").addEventListener("click", function() { S.alignSelected("left"); });
    $("btn-align-c").addEventListener("click", function() { S.alignSelected("center"); });
    $("btn-align-r").addEventListener("click", function() { S.alignSelected("right"); });
    $("btn-align-t").addEventListener("click", function() { S.alignSelected("top"); });
    $("btn-align-m").addEventListener("click", function() { S.alignSelected("middle"); });
    $("btn-align-b").addEventListener("click", function() { S.alignSelected("bottom"); });
    $("btn-dist-h").addEventListener("click", function() { S.distributeSelected("h"); });
    $("btn-dist-v").addEventListener("click", function() { S.distributeSelected("v"); });
    $("btn-match-w").addEventListener("click", function() { S.matchSize("w"); });
    $("btn-match-h").addEventListener("click", function() { S.matchSize("h"); });
    $("btn-snap").addEventListener("click", function() { S.toggleSnap(); });

    // Show alignment group when element is selected
    var origSelect = S.select;
    S.select = function(id) {
        origSelect(id);
        var group = $("align-group");
        if (group) {
            group.style.display = id ? "flex" : "none";
        }
    };

    // ── Keyboard shortcuts ──
    document.addEventListener("keydown", function(e) {
        // Don't trigger shortcuts while typing in inputs
        if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") return;
        var cmd = e.metaKey || e.ctrlKey;
        if (cmd && e.key === "z") { e.preventDefault(); if (S.undo) S.undo(); }
        else if (cmd && e.key === "y") { e.preventDefault(); if (S.redo) S.redo(); }
        else if (cmd && e.key === "s") { e.preventDefault(); if (S.saveFile) S.saveFile(); }
        else if (cmd && e.key === "n") { e.preventDefault(); if (S.newAlbum) S.newAlbum(); }
        else if (cmd && e.key === "o") { e.preventDefault(); var fi = $("file-inp"); if (fi) fi.click(); }
        else if (cmd && e.key === "p") { e.preventDefault(); if (S.previewAlbum) S.previewAlbum(); }
        else if (cmd && e.key === "d") { e.preventDefault(); $("btn-dup-el").click(); }
        else if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); if (S.sel) $("btn-del").click(); }
        else if (e.key === "Escape") { if (S.select) S.select(null); }
    });

    // ── Before unload ──
    window.addEventListener("beforeunload", function(e) {
        if (S._dirty) { e.preventDefault(); e.returnValue = ""; }
    });

    // ── Restore draft from localStorage ──
    var restored = S.loadDraft();
    if (restored) {
        console.log("StampAlbum Pro: restored draft from localStorage");
    }

    // ── Init ──
    S.renderPageDots();
    S.updateGrid();
    loadFileList();
    S.loadImageList();
    S.updateTitle();

    console.log("StampAlbum Pro: ready");
}

// ── Exports ──
S.init = init;

})();
