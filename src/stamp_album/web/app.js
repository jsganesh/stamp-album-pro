"use strict";
(function(){
var E = [], sel = null, nid = 1, _sc = 2.5, _sn = 5, _pw = 595, _ph = 842, _init = false;
var _drg = false, _dragEl = null, _dragH = null, _ds = {};
var _defBdr = "solid", _defBdrC = "#666", _defFillC = "#fff";
var _collapsed = { sb: false, rp: false };
var _currentFile = null, _currentPage = 0, _pages = [ [] ];
var _dirty = false;
var _colMode = 1, _colGap = 10.0;  // Column layout mode and gap (mm)

// ── Undo/redo system ──
var _undoStack = [], _redoStack = [], _undoMax = 50, _undoPaused = false;
function pushUndo() {
    if (_undoPaused) return;
    _undoStack.push(JSON.stringify(E));
    if (_undoStack.length > _undoMax) _undoStack.shift();
    _redoStack = [];
    _dirty = true;
    updateTitle();
}
function undo() {
    if (_undoStack.length < 2) return;
    _redoStack.push(_undoStack.pop());
    var state = JSON.parse(_undoStack.pop());
    loadElements(state);
    updateTitle();
}
function redo() {
    if (_redoStack.length === 0) return;
    _undoStack.push(JSON.stringify(E));
    var state = JSON.parse(_redoStack.pop());
    loadElements(state);
    updateTitle();
}
function loadElements(arr) { E = arr; sel = null; switchPage(_currentPage, true); render(); updateProps(); }
function loadElementsNoPush(arr) { _undoPaused = true; loadElements(arr); _undoPaused = false; }

// ── Font CSS resolver ──
function fontCSS(fid) {
    var F = {
        "HN": { family: "Helvetica,Arial,sans-serif", weight: "normal", style: "normal" },
        "HB": { family: "Helvetica,Arial,sans-serif", weight: "bold", style: "normal" },
        "HI": { family: "Helvetica,Arial,sans-serif", weight: "normal", style: "italic" },
        "HS": { family: "Helvetica,Arial,sans-serif", weight: "bold", style: "italic" },
        "TN": { family: "'Times New Roman',Times,serif", weight: "normal", style: "normal" },
        "TB": { family: "'Times New Roman',Times,serif", weight: "bold", style: "normal" },
        "TI": { family: "'Times New Roman',Times,serif", weight: "normal", style: "italic" },
        "TS": { family: "'Times New Roman',Times,serif", weight: "bold", style: "italic" },
        "CN": { family: "Courier,monospace", weight: "normal", style: "normal" },
        "CB": { family: "Courier,monospace", weight: "bold", style: "normal" },
        "CI": { family: "Courier,monospace", weight: "normal", style: "italic" },
        "CS": { family: "Courier,monospace", weight: "bold", style: "italic" },
    };
    return F[fid] || { family: fid, weight: "normal", style: "normal" };
}

// ── Toast ──
function showToast(msg, type) {
    type = type || "info";
    var c = document.getElementById("toast-container");
    if (!c) return;
    var t = document.createElement("div");
    t.className = "toast " + type;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(function(){ t.remove(); }, 3000);
}

// ── Utility ──
function $(id) { return document.getElementById(id); }
function mm(px) { return Math.round(px / _sc * 10) / 10; }
function px(mm) { return Math.round(mm * _sc); }
function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

// ── Escape user strings for DSL embedding ──
function escapeDSL(s) {
    return String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

// ── System Fonts ──
var SYSTEM_FONTS = [];
function detectFonts() {
    var testStr = "mmmmmmmmmmlli";
    var testSize = "72px";
    var defaults = { serif: "serif", sansSerif: "sans-serif", monospace: "monospace" };
    var testSpan = document.createElement("span");
    testSpan.style.fontSize = testSize;
    testSpan.style.position = "absolute";
    testSpan.style.left = "-9999px";
    testSpan.innerHTML = testStr;
    document.body.appendChild(testSpan);
    var defaultWidth = {};
    for (var d in defaults) { testSpan.style.fontFamily = defaults[d]; defaultWidth[d] = testSpan.offsetWidth; }
    var candidates = ["Arial","Arial Black","Arial Narrow","Calibri","Cambria","Candara","Comic Sans MS","Consolas","Courier New","Franklin Gothic","Garamond","Georgia","Helvetica","Impact","Lucida Console","Lucida Sans","Microsoft Sans Serif","Palatino","Segoe UI","Tahoma","Times New Roman","Trebuchet MS","Verdana","Bookman Old Style","Century Gothic","Gill Sans","Rockwell","Perpetua","Baskerville","Didot","Optima","Futura","Avant Garde","Goudy","American Typewriter","Andale Mono","Apple Chancery","Brush Script MT","Chalkduster","Copperplate","Herculanum","Luminari","Marker Felt","Noteworthy","Papyrus","Zapfino"];
    SYSTEM_FONTS = [];
    for (var i = 0; i < candidates.length; i++) {
        testSpan.style.fontFamily = "'" + candidates[i] + "',sans-serif";
        if (testSpan.offsetWidth !== defaultWidth.sansSerif) { SYSTEM_FONTS.push(candidates[i]); }
    }
    testSpan.remove();
    SYSTEM_FONTS.sort();
}
detectFonts();

// ── Update title bar ──
function updateTitle() {
    var fn = $("file-name");
    if (fn) {
        var name = _currentFile || "Untitled";
        fn.textContent = (_dirty ? "● " : "") + name;
    }
}

// ── Page management ──
function switchPage(idx, silent) {
    if (idx < 0 || idx >= _pages.length) return;
    if (!silent) pushUndo();
    _pages[_currentPage] = JSON.parse(JSON.stringify(E));
    _currentPage = idx;
    E = _pages[idx] ? JSON.parse(JSON.stringify(_pages[idx])) : [];
    sel = null;
    renderPageDots();
    render();
    updateProps();
}
function addPage() {
    pushUndo();
    _pages.push([]);
    switchPage(_pages.length - 1, true);
    showToast("Page added", "success");
}
function deletePage() {
    if (_pages.length <= 1) { showToast("Cannot delete last page", "error"); return; }
    pushUndo();
    _pages.splice(_currentPage, 1);
    if (_currentPage >= _pages.length) _currentPage = _pages.length - 1;
    E = JSON.parse(JSON.stringify(_pages[_currentPage]));
    sel = null;
    renderPageDots();
    render();
    updateProps();
    showToast("Page deleted", "success");
}
function renderPageDots() {
    var c = $("pg-dots");
    if (!c) return;
    c.innerHTML = "";
    for (var i = 0; i < _pages.length; i++) {
        var dot = document.createElement("span");
        dot.className = "pg-dot" + (i === _currentPage ? " active" : "");
        dot.textContent = i + 1;
        dot.title = "Page " + (i + 1);
        (function(idx) {
            dot.addEventListener("click", function() { switchPage(idx); });
        })(i);
        c.appendChild(dot);
    }
    var addDot = document.createElement("span");
    addDot.className = "pg-dot add";
    addDot.textContent = "+";
    addDot.title = "Add page";
    addDot.addEventListener("click", addPage);
    c.appendChild(addDot);
}

// ── Grid lines ──
function updateGrid() {
    var svg = $("grid-overlay");
    if (!svg) return;
    var pattern = svg.querySelector("#grid-pattern");
    if (!pattern) return;
    if (_sn > 0) {
        var gs = _sn * _sc;
        pattern.setAttribute("width", gs);
        pattern.setAttribute("height", gs);
        var path = pattern.querySelector("path");
        if (path) {
            path.setAttribute("d", "M " + gs + " 0 L 0 0 0 " + gs);
        }
        svg.style.display = "block";
    } else {
        svg.style.display = "none";
    }
}

// ── Canvas init ──
function init() {
    if (_init) return;
    _init = true;
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
        // Check for image file drop
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            for (var i = 0; i < e.dataTransfer.files.length; i++) {
                var f = e.dataTransfer.files[i];
                if (f.type.startsWith("image/")) {
                    uploadImageFile(f, function(imgName) {
                        var r = pg.getBoundingClientRect();
                        var x = Math.max(0, Math.min(Math.round((e.clientX - r.left) / _sn) * _sn, _pw - 40));
                        var y = Math.max(0, Math.min(Math.round((e.clientY - r.top) / _sn) * _sn, _ph - 30));
                        add({ t: "image", s: "rectangle", x: x, y: y, w: 80, h: 60,
                            lbl: f.name, img: "/images/" + imgName,
                            bdr: "solid", bdrC: "#999", bdrW: 0.5, fill: "#fff", fillA: 100, font: "HN", fs: 12 });
                    });
                    return;
                }
            }
        }
        // Palette/text/row drop
        var d;
        try { d = JSON.parse(e.dataTransfer.getData("text/plain")); } catch (_) { return; }
        var r = pg.getBoundingClientRect();
        var x = Math.max(0, Math.min(Math.round((e.clientX - r.left) / _sn) * _sn, _pw - 40));
        var y = Math.max(0, Math.min(Math.round((e.clientY - r.top) / _sn) * _sn, _ph - 30));
        var w = d.w || 80, h = d.h || 60;
        if (d.t === "text") { w = 120; h = d.st === "heading" ? 24 : d.st === "desc" ? 16 : 18; }
        if (d.t === "freehand") { w = 100; h = 80; }
        add({ t: d.t || "stamp", s: d.s || "rectangle", x: x, y: y, w: w, h: h,
            lbl: d.t === "text" ? (d.st === "heading" ? "Heading" : d.st === "desc" ? "Description" : "Label") : "",
            font: d.font || "HN", fs: d.st === "heading" ? 16 : d.st === "desc" ? 10 : 12,
            bdr: _defBdr, bdrC: _defBdrC, bdrW: 1, fill: _defFillC, fillA: 100, img: "" });
    });

    // Mouse on canvas
    pg.addEventListener("mousedown", function(e) {
        var el = e.target.closest(".cel");
        if (!el) { sel = null; render(); return; }
        var obj = E.find(function(x) { return x.id === el.dataset.id; });
        if (!obj) return;
        if (e.target.classList.contains("rh")) { _dragH = e.target.dataset.h; } else { _dragH = "move"; }
        select(obj.id);
        _drg = true;
        _dragEl = obj;
        _ds = { x: e.clientX, y: e.clientY, ox: obj.x, oy: obj.y, ow: obj.w, oh: obj.h };
        e.preventDefault();
        e.stopPropagation();
    });

    document.addEventListener("mousemove", function(e) {
        if (!_drg || !_dragEl) return;
        var dx = Math.round((e.clientX - _ds.x) / _sn) * _sn;
        var dy = Math.round((e.clientY - _ds.y) / _sn) * _sn;
        var h = _dragH, x = _ds.ox, y = _ds.oy, w = _ds.ow, oh = _ds.oh;
        if (h === "move") { x += dx; y += dy; } else {
            if (h.indexOf("w") >= 0) { x += dx; w -= dx; }
            if (h.indexOf("e") >= 0) { w += dx; }
            if (h.indexOf("n") >= 0) { y += dy; oh -= dy; }
            if (h.indexOf("s") >= 0) { oh += dy; }
            if (w < 10) w = 10;
            if (oh < 10) oh = 10;
        }
        _dragEl.x = Math.max(0, Math.min(x, _pw - _dragEl.w));
        _dragEl.y = Math.max(0, Math.min(y, _ph - _dragEl.h));
        _dragEl.w = Math.min(w, _pw - _dragEl.x);
        _dragEl.h = Math.min(oh, _ph - _dragEl.y);
        render();
        updateProps();
        if (h === "move") drawAlignmentGuides(_dragEl);
    });

    document.addEventListener("mouseup", function() {
        if (_drg && _dragEl) { pushUndo(); }
        _drg = false;
        _dragEl = null;
        _dragH = null;
        clearAlignmentGuides();
    });

    // ── Props Panel ──
    function bindProp(id, key, transform) {
        $(id).addEventListener("change", function() {
            var el = E.find(function(x) { return x.id === sel; });
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
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        el.lbl = this.value; pushUndo(); render();
    });
    $("pbs").addEventListener("change", function() {
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        el.bdr = this.value; pushUndo(); render();
    });
    $("pbc").addEventListener("change", function() {
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        el.bdrC = this.value; pushUndo(); render();
    });
    $("pbw").addEventListener("change", function() {
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        el.bdrW = parseFloat(this.value) || 0; pushUndo(); render();
    });
    $("pfc").addEventListener("change", function() {
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        el.fill = this.value; pushUndo(); render();
    });
    $("pfa").addEventListener("input", function() {
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        el.fillA = parseInt(this.value); $("pfa-v").textContent = this.value + "%";
    });
    $("pfa").addEventListener("change", function() { pushUndo(); render(); });
    $("pfnt").addEventListener("change", function() {
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        el.font = this.value; pushUndo(); render();
    });
    $("pfs").addEventListener("change", function() {
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        el.fs = parseFloat(this.value) || 12; pushUndo(); render();
    });

    // ── Buttons ──
    $("btn-new").addEventListener("click", newAlbum);
    $("btn-open").addEventListener("click", function() { $("file-inp").click(); });
    $("btn-save").addEventListener("click", saveFile);
    $("btn-dup").addEventListener("click", function() {
        if (!sel) { showToast("Select an element first", "error"); return; }
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        add(Object.assign({}, el, { id: "el" + (nid++), x: el.x + 20, y: el.y + 20 }));
    });
    $("btn-grid").addEventListener("click", function() {
        if (!sel) { showToast("Select a stamp to duplicate in grid", "error"); return; }
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        var cols = parseInt(prompt("Number of columns:", "3")) || 3;
        var rows = parseInt(prompt("Number of rows:", "3")) || 3;
        var gapX = parseFloat(prompt("Horizontal gap (mm):", "5")) || 5;
        var gapY = parseFloat(prompt("Vertical gap (mm):", "5")) || 5;
        var startX = el.x, startY = el.y;
        for (var r = 0; r < rows; r++) {
            for (var c = 0; c < cols; c++) {
                if (r === 0 && c === 0) continue;
                add(Object.assign({}, el, { id: "el" + (nid++),
                    x: startX + c * (el.w + px(gapX)),
                    y: startY + r * (el.h + px(gapY)),
                    lbl: el.label ? el.label + " (" + (r + 1) + "," + (c + 1) + ")" : "" }));
            }
        }
    });
    $("btn-del").addEventListener("click", function() {
        if (!sel) return;
        E = E.filter(function(x) { return x.id !== sel; });
        sel = null;
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
    $("btn-dsl").addEventListener("click", function() {
        $("dsl-panel").classList.toggle("open");
        if ($("dsl-panel").classList.contains("open")) {
            $("dsl-ta").value = buildDSL();
        }
    });
    $("btn-app-dsl").addEventListener("click", function() {
        parseDSL($("dsl-ta").value);
        pushUndo();
        render();
        showToast("DSL applied", "success");
    });
    $("btn-cls-dsl").addEventListener("click", function() { $("dsl-panel").classList.remove("open"); });

    // ── Preview ──
    $("btn-preview").addEventListener("click", openPreview);
    $("btn-preview-close").addEventListener("click", function() { $("preview-overlay").classList.remove("open"); });
    $("btn-preview-refresh").addEventListener("click", openPreview);
    $("btn-preview-export").addEventListener("click", exportPDF);

    // ── Export ──
    $("btn-export").addEventListener("click", exportPDF);

    // ── Image Upload ──
    $("img-upl-btn").addEventListener("click", function() { $("upl-inp").click(); });
    $("upl-inp").addEventListener("change", function(e) {
        if (e.target.files.length === 0) return;
        var f = e.target.files[0];
        uploadImageFile(f, function(imgName) {
            var r = $("page").getBoundingClientRect();
            var x = 50, y = 50;
            add({ t: "image", s: "rectangle", x: x, y: y, w: 80, h: 60,
                lbl: f.name, img: "/images/" + imgName,
                bdr: "solid", bdrC: "#999", bdrW: 0.5, fill: "#fff", fillA: 100, font: "HN", fs: 12 });
            loadImageList();
        });
        e.target.value = "";
    });

    // ── Change / Remove Image ──
    $("btn-chg-img").addEventListener("click", function() {
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        var inp = document.createElement("input"); inp.type = "file"; inp.accept = "image/*";
        inp.onchange = function(ev) {
            var f = ev.target.files[0]; if (!f) return;
            uploadImageFile(f, function(imgName) {
                el.img = "/images/" + imgName;
                pushUndo();
                render();
                loadImageList();
            });
        };
        inp.click();
    });
    $("btn-rm-img").addEventListener("click", function() {
        var el = E.find(function(x) { return x.id === sel; }); if (!el) return;
        el.img = ""; pushUndo(); render();
    });

    // ── Page Size / Grid ──
    $("pg-size").addEventListener("change", function() {
        var s = { a4: [595, 842], letter: [612, 792], a3: [842, 1191] };
        var v = s[this.value] || s.a4;
        _pw = v[0]; _ph = v[1];
        $("page").className = "page " + this.value;
        render();
        updateGrid();
    });
    $("grid").addEventListener("change", function() {
        _sn = parseInt(this.value) || 0;
        updateGrid();
    });

    // ── Column layout ──
    $("col-mode").addEventListener("change", function() {
        _colMode = parseInt(this.value) || 1;
        render();
    });
    $("col-gap").addEventListener("change", function() {
        _colGap = parseFloat(this.value) || 10.0;
        render();
    });

    // ── Default colors ──
    $("def-bdr").addEventListener("change", function() { _defBdr = this.value; });
    $("def-bdr-c").addEventListener("change", function() { _defBdrC = this.value; });
    $("def-fill-c").addEventListener("change", function() { _defFillC = this.value; });

    // ── Collapsible Panels ──
    $("sb-toggle").addEventListener("click", function() {
        _collapsed.sb = !_collapsed.sb;
        $("sidebar").classList.toggle("collapsed", _collapsed.sb);
        this.textContent = _collapsed.sb ? "▶" : "◀";
    });
    $("rp-toggle").addEventListener("click", function() {
        _collapsed.rp = !_collapsed.rp;
        $("rp").classList.toggle("collapsed", _collapsed.rp);
        this.textContent = _collapsed.rp ? "◀" : "▶";
    });
    $("sb-handle").addEventListener("click", function() { $("sb-toggle").click(); });
    $("rp-handle").addEventListener("click", function() { $("rp-toggle").click(); });

    // ── Collapsible sections ──
    $("file-toggle").addEventListener("click", function() {
        var b = $("file-body");
        b.classList.toggle("collapsed");
        this.textContent = b.classList.contains("collapsed") ? "▶" : "▼";
    });
    $("img-toggle").addEventListener("click", function() {
        var b = $("img-body");
        b.classList.toggle("collapsed");
        this.textContent = b.classList.contains("collapsed") ? "▶" : "▼";
    });

    // ── File input ──
    $("file-inp").addEventListener("change", function(e) {
        if (e.target.files.length === 0) return;
        var f = e.target.files[0];
        var reader = new FileReader();
        reader.onload = function(ev) {
            var dsl = ev.target.result;
            _currentFile = f.name;
            parseDSL(dsl);
            _dirty = false;
            updateTitle();
            loadFileList();
            showToast("Opened " + f.name, "success");
        };
        reader.readAsText(f);
        e.target.value = "";
    });

    // ── Keyboard shortcuts ──
    document.addEventListener("keydown", function(e) {
        if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") return;
        if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) { e.preventDefault(); undo(); return; }
        if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.key === "z" && e.shiftKey))) { e.preventDefault(); redo(); return; }
        if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); saveFile(); return; }
        if ((e.ctrlKey || e.metaKey) && e.key === "o") { e.preventDefault(); $("file-inp").click(); return; }
        if (e.key === "Delete" || e.key === "Backspace") {
            if (sel) { E = E.filter(function(x) { return x.id !== sel; }); sel = null; pushUndo(); render(); updateProps(); }
        }
        if (e.key === "Escape") { sel = null; render(); updateProps(); }
        if ((e.ctrlKey || e.metaKey) && e.key === "d" && sel) {
            e.preventDefault();
            var el = E.find(function(x) { return x.id === sel; }); if (el) add(Object.assign({}, el, { id: "el" + (nid++), x: el.x + 20, y: el.y + 20 }));
        }
        if (e.key === "F5") { e.preventDefault(); openPreview(); }
        if (e.key === "?") { e.preventDefault(); $("help-overlay").classList.toggle("open"); }
    });

    // ── Help overlay ──
    $("btn-help").addEventListener("click", function() { $("help-overlay").classList.toggle("open"); });
    $("btn-help-close").addEventListener("click", function() { $("help-overlay").classList.remove("open"); });
    $("help-overlay").addEventListener("click", function(e) {
        if (e.target === this) this.classList.remove("open");
    });

    // ── Font population ──
    populateFonts();

    // ── Load templates ──
    loadTemplateList();
    // Auto-load template on selection change
    $("wiz-template").addEventListener("change", function() {
        var val = this.value;
        if (val && val !== "blank") {
            $("btn-wiz-template").click();
        }
    });

    // ── Wizard Apply ──
    $("btn-wiz-apply").addEventListener("click", applyWizard);
    $("btn-app-wiz").addEventListener("click", applyWizard);
    $("btn-wiz-template").addEventListener("click", function() {
        var selTpl = $("wiz-template").value;
        if (selTpl && selTpl !== "blank") {
            fetch("/api/templates/" + selTpl)
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.dsl) {
                        parseDSL(data.dsl);
                        pushUndo();
                        render();
                        showToast("Template loaded: " + data.name, "success");
                        $("wizard-panel").classList.remove("open");
                    }
                })
                .catch(function(err) { showToast("Failed to load template: " + err, "error"); });
        }
    });

    // ── New file button ──
    $("btn-new-file").addEventListener("click", newAlbum);

    // ── Touch / Pointer support for iPad ──
    // Palette drag via touch (iPad Safari lacks HTML DnD)
    document.querySelectorAll(".p-item[draggable]").forEach(function(it) {
        it.addEventListener("touchstart", function(e) {
            var touch = e.touches[0];
            _ds = { t: it.dataset.t, s: it.dataset.s || "rectangle", st: it.dataset.st || "",
                w: parseFloat(it.dataset.w) || 80, h: parseFloat(it.dataset.h) || 60,
                font: "HN", fs: 12, tx: touch.clientX, ty: touch.clientY };
            e.preventDefault();
        }, { passive: false });
    });
    document.addEventListener("touchmove", function(e) {
        if (!_ds || !_ds.t) return;
        e.preventDefault();
    }, { passive: false });
    document.addEventListener("touchend", function(e) {
        if (!_ds || !_ds.t) return;
        var touch = e.changedTouches[0];
        var pg = $("page");
        if (pg) {
            var r = pg.getBoundingClientRect();
            var cx = touch.clientX, cy = touch.clientY;
            if (cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom) {
                var x = Math.max(0, Math.min(Math.round((cx - r.left) / _sn) * _sn, _pw - 40));
                var y = Math.max(0, Math.min(Math.round((cy - r.top) / _sn) * _sn, _ph - 30));
                var d = _ds;
                var w = d.w || 80, h = d.h || 60;
                if (d.t === "text") { w = 120; h = d.st === "heading" ? 24 : d.st === "desc" ? 16 : 18; }
                if (d.t === "freehand") { w = 100; h = 80; }
                add({ t: d.t || "stamp", s: d.s || "rectangle", x: x, y: y, w: w, h: h,
                    lbl: d.t === "text" ? (d.st === "heading" ? "Heading" : d.st === "desc" ? "Description" : "Label") : "",
                    font: d.font || "HN", fs: d.st === "heading" ? 16 : d.st === "desc" ? 10 : 12,
                    bdr: _defBdr, bdrC: _defBdrC, bdrW: 1, fill: _defFillC, fillA: 100, img: "" });
            }
        }
        _ds = {};
    });
    // Canvas element touch drag (iPad)
    document.addEventListener("touchstart", function(e) {
        var el = e.target.closest(".cel");
        if (!el) return;
        var obj = E.find(function(x) { return x.id === el.dataset.id; });
        if (!obj) return;
        var touch = e.touches[0];
        _dragH = e.target.classList.contains("rh") ? e.target.dataset.h : "move";
        select(obj.id);
        _drg = true;
        _dragEl = obj;
        _ds = { x: touch.clientX, y: touch.clientY, ox: obj.x, oy: obj.y, ow: obj.w, oh: obj.h };
    }, { passive: true });
    document.addEventListener("touchmove", function(e) {
        if (!_drg || !_dragEl) return;
        var touch = e.touches[0];
        var dx = Math.round((touch.clientX - _ds.x) / _sn) * _sn;
        var dy = Math.round((touch.clientY - _ds.y) / _sn) * _sn;
        var h = _dragH, x = _ds.ox, y = _ds.oy, w = _ds.ow, oh = _ds.oh;
        if (h === "move") { x += dx; y += dy; } else {
            if (h.indexOf("w") >= 0) { x += dx; w -= dx; }
            if (h.indexOf("e") >= 0) { w += dx; }
            if (h.indexOf("n") >= 0) { y += dy; oh -= dy; }
            if (h.indexOf("s") >= 0) { oh += dy; }
            if (w < 10) w = 10;
            if (oh < 10) oh = 10;
        }
        _dragEl.x = Math.max(0, Math.min(x, _pw - _dragEl.w));
        _dragEl.y = Math.max(0, Math.min(y, _ph - _dragEl.h));
        _dragEl.w = Math.min(w, _pw - _dragEl.x);
        _dragEl.h = Math.min(oh, _ph - _dragEl.y);
        render();
        updateProps();
        e.preventDefault();
    }, { passive: false });
    document.addEventListener("touchend", function() {
        if (_drg && _dragEl) { pushUndo(); }
        _drg = false;
        _dragEl = null;
        _dragH = null;
    });

    // ── Before unload ──
    window.addEventListener("beforeunload", function(e) {
        if (_dirty) { e.preventDefault(); e.returnValue = ""; }
    });

    // ── Init ──
    renderPageDots();
    updateGrid();
    loadFileList();
    loadImageList();
    updateTitle();

    // ── First-run tutorial ──
    initTutorial();

    console.log("StampAlbum Pro: ready");
}

// ── First-run tutorial ──
var _tutorialStep = 1;
var _tutorialMax = 4;

function initTutorial() {
    // Only show if user has never completed or skipped it
    if (localStorage.getItem("stampalbum-tutorial-done")) return;

    // Auto-load a sample album so the canvas isn't empty
    var sampleDSL = [
        'ALBUM_TITLE("My First Album")',
        'ALBUM_PAGES_SIZE(210.0 297.0)',
        'ALBUM_PAGES_MARGINS(15 15 15 15)',
        'PAGE_START',
        'PAGE_TEXT_CENTRE("HB" 16 "Great Britain — Victorian Era")',
        'PAGE_TEXT_CENTRE("HN" 10 "A sample album page to get you started")',
        'PAGE_VSPACE(8)',
        'ROW_START_FS("HN" 8 6.0 6.0)',
        'STAMP_ADD_AT(15.0 40.0 60.0 45.0 "Penny Black — 1840" "rectangle" "solid" "#fff")',
        'STAMP_ADD_AT(81.0 40.0 60.0 45.0 "Penny Red — 1841" "rectangle" "solid" "#fff")',
        'STAMP_ADD_AT(147.0 40.0 60.0 45.0 "Twopence Blue — 1840" "rectangle" "solid" "#fff")',
    ].join("\n");
    parseDSL(sampleDSL);
    _dirty = false;
    updateTitle();

    // Show the tutorial overlay
    var overlay = $("tutorial-overlay");
    if (overlay) {
        overlay.classList.add("open");
        _tutorialStep = 1;
        _showTutorialStep();
    }
}

function _showTutorialStep() {
    var overlay = $("tutorial-overlay");
    if (!overlay) return;
    overlay.querySelectorAll(".tutorial-step").forEach(function(el) {
        el.classList.toggle("active", parseInt(el.dataset.step) === _tutorialStep);
    });
    var nextBtn = $("btn-tutorial-next");
    if (nextBtn) {
        nextBtn.textContent = _tutorialStep >= _tutorialMax ? "Get Started" : "Next";
    }
}

$("btn-tutorial-next").addEventListener("click", function() {
    _tutorialStep++;
    if (_tutorialStep > _tutorialMax) {
        $("tutorial-overlay").classList.remove("open");
        localStorage.setItem("stampalbum-tutorial-done", "1");
    } else {
        _showTutorialStep();
    }
});

$("btn-tutorial-skip").addEventListener("click", function() {
    $("tutorial-overlay").classList.remove("open");
    localStorage.setItem("stampalbum-tutorial-done", "1");
});

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
    if (SYSTEM_FONTS && SYSTEM_FONTS.length) {
        var og2 = document.createElement("optgroup");
        og2.label = "System Fonts";
        SYSTEM_FONTS.forEach(function(f) { var o = document.createElement("option"); o.value = f; o.textContent = f; og2.appendChild(o); });
        pfnt.appendChild(og2);
    }
    var ws = document.createElement("optgroup");
    ws.label = "Web Safe";
    ["Arial","Helvetica","Times New Roman","Courier New","Georgia","Verdana","Trebuchet MS","Impact","Comic Sans MS"].forEach(function(f) { var o = document.createElement("option"); o.value = f; o.textContent = f; ws.appendChild(o); });
    pfnt.appendChild(ws);
}

// ── Alignment guide lines ──
var _guideLines = [];
var GUIDE_THRESHOLD = 5;

function drawAlignmentGuides(el) {
    clearAlignmentGuides();
    if (!el) return;
    var guides = [];
    var edges = [
        { pos: el.x, type: "v" },                          // left
        { pos: el.x + el.w, type: "v" },                   // right
        { pos: el.x + el.w / 2, type: "v" },               // h-center
        { pos: el.y, type: "h" },                          // top
        { pos: el.y + el.h, type: "h" },                   // bottom
        { pos: el.y + el.h / 2, type: "h" },               // v-center
    ];
    E.forEach(function(other) {
        if (other.id === el.id) return;
        var oEdges = [
            { pos: other.x, type: "v" },
            { pos: other.x + other.w, type: "v" },
            { pos: other.x + other.w / 2, type: "v" },
            { pos: other.y, type: "h" },
            { pos: other.y + other.h, type: "h" },
            { pos: other.y + other.h / 2, type: "h" },
        ];
        edges.forEach(function(e) {
            oEdges.forEach(function(oe) {
                if (e.type !== oe.type) return;
                if (Math.abs(e.pos - oe.pos) > GUIDE_THRESHOLD) return;
                guides.push({ pos: oe.pos, dir: e.type === "v" ? "v" : "h",
                    spanStart: Math.min(e.type === "v" ? el.y : el.x, oe.type === "v" ? other.y : other.x),
                    spanEnd: Math.max(e.type === "v" ? el.y + el.h : el.x + el.w, oe.type === "v" ? other.y + other.h : other.x + other.w) });
            });
        });
    });
    var pg = $("page");
    if (!pg) return;
    guides.forEach(function(g) {
        // Extend span across the page for clarity
        var line = document.createElement("div");
        line.className = "guide-line";
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
}

function clearAlignmentGuides() {
    _guideLines.forEach(function(l) { if (l.parentNode) l.parentNode.removeChild(l); });
    _guideLines = [];
}

// ── Add element ──
function add(p) {
    var s = {
        id: "el" + (nid++),
        t: p.t || "stamp",
        s: p.s || "rectangle",
        x: p.x || 50, y: p.y || 50, w: p.w || 80, h: p.h || 60,
        lbl: p.lbl || "",
        font: p.font || "HN",
        fs: p.fs || 12,
        align: p.align || "left",
        bdr: p.bdr || "solid",
        bdrC: p.bdrC || "#666",
        bdrW: p.bdrW || 1,
        fill: p.fill || "#fff",
        fillA: p.fillA || 100,
        img: p.img || ""
    };
    E.push(s);
    pushUndo();
    select(s.id);
    render();
}

// ── Select ──
function select(id) {
    sel = id;
    render();
    var el = E.find(function(x) { return x.id === id; });
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
    $("pbs").value = el.bdr || "solid";
    $("pbc").value = el.bdrC || "#666";
    $("pbw").value = el.bdrW || 1;
    $("pfc").value = el.fill || "#fff";
    $("pfa").value = el.fillA || 100;
    $("pfa-v").textContent = (el.fillA || 100) + "%";
    $("pfnt").value = el.font || "HN";
    $("pfs").value = el.fs || 12;
    var isImg = el.t === "image";
    $("img-sec").style.display = isImg ? "block" : "none";
    $("img-row").style.display = isImg ? "flex" : "none";
}

function updateProps() {
    var el = E.find(function(x) { return x.id === sel; });
    if (!el) return;
    $("px").value = mm(el.x);
    $("py").value = mm(el.y);
    $("pw").value = mm(el.w);
    $("ph").value = mm(el.h);
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

// ── Render canvas ──
function render() {
    var pg = $("page");
    pg.querySelectorAll(".cel").forEach(function(el) { el.remove(); });
    E.forEach(function(el) {
        var d = document.createElement("div");
        d.className = "cel shape-" + (el.s || "rectangle") + (el.id === sel ? " selected" : "");
        d.dataset.id = el.id;
        d.style.left = el.x + "px";
        d.style.top = el.y + "px";
        d.style.width = el.w + "px";
        d.style.height = el.h + "px";

        if (el.s && el.s !== "rectangle" && el.s !== "text" && el.s !== "freehand") {
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
            path.setAttribute("stroke", el.bdrC || "#666");
            path.setAttribute("stroke-width", (el.bdrW || 1) * 2);
            if (el.bdr === "dashed") path.setAttribute("stroke-dasharray", "4,2");
            if (el.bdr === "dotted") path.setAttribute("stroke-dasharray", "1,2");
            if (el.bdr === "double") {
                path.setAttribute("stroke-width", 1);
                var path2 = path.cloneNode();
                path2.setAttribute("transform", "translate(3,3) scale(0.95)");
                path2.setAttribute("fill", "none");
                path2.setAttribute("stroke-width", 1);
                svg.appendChild(path2);
            }
            svg.appendChild(path);
            d.appendChild(svg);
            d.style.border = "none";
        } else {
            d.style.border = (el.bdrW || 0) + "pt " + (el.bdr || "solid") + " " + (el.bdrC || "#666");
            d.style.backgroundColor = el.fill || "transparent";
        }
        if (el.fillA !== undefined && el.fillA < 100) d.style.opacity = el.fillA / 100;

        if (el.img) {
            var img = document.createElement("img");
            img.className = "eimg";
            img.src = el.img;
            d.appendChild(img);
        } else if (el.lbl) {
            var l = document.createElement("span");
            l.className = "elbl";
            l.textContent = el.lbl;
            l.contentEditable = "true";
            l.spellcheck = false;
            var fc = fontCSS(el.font || "HN");
            l.style.fontFamily = fc.family;
            l.style.fontSize = (el.fs || 12) + "px";
            l.style.fontWeight = fc.weight;
            l.style.fontStyle = fc.style;
            l.addEventListener("blur", function() {
                el.lbl = this.textContent;
                var p = this.parentNode;
                this.style.minHeight = "";
                var nh = this.scrollHeight + 4;
                if (nh > p.offsetHeight) p.style.height = nh + "px";
                pushUndo();
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
            e.stopPropagation();
            select(el.id);
            _drg = true;
            _dragEl = el;
            _dragH = "move";
            _ds = { x: e.clientX, y: e.clientY, ox: el.x, oy: el.y, ow: el.w, oh: el.h };
        });

        pg.appendChild(d);
    });

    // Draw column guides if columns are enabled
    if (_colMode > 1) {
        var pageWidth = _pw - 30 * _sc; // Content width (approx)
        var pageMargin = 20 * _sc; // Page margin
        var colWidth = (pageWidth - (_colMode - 1) * _colGap * _sc) / _colMode;

        for (var i = 1; i < _colMode; i++) {
            var guide = document.createElement("div");
            guide.className = "col-guide";
            guide.style.position = "absolute";
            guide.style.left = (pageMargin + i * (colWidth + _colGap * _sc)) + "px";
            guide.style.top = "0";
            guide.style.width = "1px";
            guide.style.height = _ph + "px";
            guide.style.backgroundColor = "rgba(100, 150, 255, 0.3)";
            guide.style.pointerEvents = "none";
            guide.style.zIndex = "1";
            pg.appendChild(guide);
        }
    }
}

// ── New album ──
function newAlbum() {
    if (_dirty && !confirm("Discard unsaved changes?")) return;
    E = [];
    sel = null;
    _currentFile = null;
    _currentPage = 0;
    _pages = [[]];
    _dirty = false;
    _undoStack = [];
    _redoStack = [];
    render();
    updateProps();
    renderPageDots();
    updateTitle();
    showToast("New album created", "success");
}

// ── File management ──
function loadFileList() {
    var c = $("file-list");
    if (!c) return;
    fetch("/files")
        .then(function(r) { return r.json(); })
        .then(function(files) {
            c.innerHTML = "";
            files.forEach(function(f) {
                var item = document.createElement("div");
                item.className = "file-item" + (f === _currentFile ? " active" : "");
                var icon = document.createElement("span");
                icon.className = "favicon";
                icon.textContent = f.endsWith(".slbum") ? "📖" : "📄";
                var nameSpan = document.createElement("span");
                nameSpan.className = "fn";
                nameSpan.textContent = f;
                var delBtn = document.createElement("span");
                delBtn.className = "fdel";
                delBtn.textContent = "✕";
                delBtn.title = "Delete";
                delBtn.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (confirm("Delete " + f + "?")) {
                        fetch("/files/" + encodeURIComponent(f), { method: "DELETE" })
                            .then(function() { loadFileList(); showToast("Deleted " + f, "success"); });
                    }
                });
                item.appendChild(icon);
                item.appendChild(nameSpan);
                item.appendChild(delBtn);
                item.addEventListener("click", function() {
                    fetch("/files/" + encodeURIComponent(f))
                        .then(function(r) { return r.text(); })
                        .then(function(content) {
                            _currentFile = f;
                            parseDSL(content);
                            _dirty = false;
                            updateTitle();
                            loadFileList();
                            showToast("Opened " + f, "success");
                        });
                });
                c.appendChild(item);
            });
        })
        .catch(function() { c.innerHTML = "<div style='padding:8px;color:var(--text2);font-size:11px'>No files yet</div>"; });
}

function saveFile() {
    var dsl = buildDSL();
    if (_currentFile) {
        fetch("/files/" + encodeURIComponent(_currentFile), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: dsl })
        }).then(function(r) {
            if (r.ok) {
                return r.json();
            }
            throw new Error("Save failed");
        }).then(function(data) {
            _dirty = false;
            updateTitle();
            showToast("Saved to " + (data.path || _currentFile), "success");
        }).catch(function() { showToast("Save failed", "error"); });
    } else {
        var name = prompt("File name:", "album.slbum");
        if (!name) return;
        if (!name.endsWith(".slbum") && !name.endsWith(".txt")) name += ".slbum";
        _currentFile = name;
        saveFile();
    }
}

// ── Image management ──
function uploadImageFile(file, callback) {
    var formData = new FormData();
    formData.append("file", file);
    fetch("/images", { method: "POST", body: formData })
        .then(function(r) {
            if (r.ok) return r.json();
            throw new Error("Upload failed");
        })
        .then(function(data) {
            showToast("Uploaded " + data.filename, "success");
            if (callback) callback(data.filename);
            loadImageList();
        })
        .catch(function(err) { showToast("Upload failed: " + err, "error"); });
}

function loadImageList() {
    var c = $("img-grid");
    if (!c) return;
    fetch("/images")
        .then(function(r) { return r.json(); })
        .then(function(images) {
            c.innerHTML = "";
            images.forEach(function(img) {
                var item = document.createElement("div");
                item.className = "img-item";
                var im = document.createElement("img");
                im.src = "/images/" + encodeURIComponent(img);
                var del = document.createElement("button");
                del.className = "img-del";
                del.textContent = "✕";
                del.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (confirm("Delete " + img + "?")) {
                        fetch("/images/" + encodeURIComponent(img), { method: "DELETE" })
                            .then(function() { loadImageList(); showToast("Deleted " + img, "success"); });
                    }
                });
                item.appendChild(im);
                item.appendChild(del);
                item.addEventListener("click", function() {
                    var r = $("page").getBoundingClientRect();
                    var x = 50, y = 50;
                    add({ t: "image", s: "rectangle", x: x, y: y, w: 80, h: 60,
                        lbl: img, img: "/images/" + img,
                        bdr: "solid", bdrC: "#999", bdrW: 0.5, fill: "#fff", fillA: 100, font: "HN", fs: 12 });
                });
                c.appendChild(item);
            });
        })
        .catch(function() {
            c.innerHTML = "<div style='padding:8px;color:var(--text2);font-size:11px'>No images yet</div>";
        });
}

// ── Build canvas state for direct render/export ──
function buildCanvasState(format) {
    var allPages = _pages.slice();
    allPages[_currentPage] = JSON.parse(JSON.stringify(E));
    var firstPage = allPages.length > 0 ? allPages[0] : [];
    var restPages = allPages.slice(1);
    while (restPages.length > 0 && restPages[restPages.length - 1].length === 0) {
        restPages.pop();
    }
    return {
        elements: firstPage,
        pages: restPages,
        page_width_px: _pw, page_height_px: _ph,
        scale: _sc,
        source_path: _currentFile || "album.slbum",
        format: format || "html",
        title: (_currentFile || "My Album").replace(/\.(slbum|txt)$/, ""),
        author: ""
    };
}

// ── Preview (direct — no DSL parser) ──
function openPreview() {
    var overlay = $("preview-overlay");
    var frame = $("preview-frame");
    if (!overlay || !frame) return;
    overlay.classList.add("open");
    showToast("Generating preview...", "info");
    var state = buildCanvasState("html");
    fetch("/render-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
    })
    .then(function(r) {
        if (!r.ok) throw new Error("Render failed (" + r.status + ")");
        return r.text();
    })
    .then(function(html) {
        frame.contentDocument.open();
        frame.contentDocument.write(html);
        frame.contentDocument.close();
        var body = frame.contentDocument.body;
        if (body) {
            var firstPage = body.querySelector(".page");
            if (firstPage) {
                frame.style.width = firstPage.offsetWidth + "px";
                frame.style.height = firstPage.offsetHeight + "px";
            }
        }
        showToast("Preview ready", "success");
    })
    .catch(function(err) {
        showToast("Preview failed: " + err, "error");
    });
}

// ── Export PDF (direct — no DSL parser) ──
function exportPDF() {
    showToast("Generating PDF...", "info");
    var filename = _currentFile ? _currentFile.replace(/\.(slbum|txt)$/, ".pdf") : "album.pdf";
    var state = buildCanvasState("pdf");
    fetch("/export-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
    })
    .then(function(r) {
        if (!r.ok) throw new Error("Export failed (" + r.status + ")");
        return r.blob();
    })
    .then(function(b) {
        var a = document.createElement("a");
        a.href = URL.createObjectURL(b);
        a.download = filename;
        a.click();
        setTimeout(function() { URL.revokeObjectURL(a.href); }, 100);
        showToast("PDF saved to Downloads/" + filename, "success");
    })
    .catch(function(err) { showToast("Export failed: " + err, "error"); });
}

// ── Template list ──
function loadTemplateList() {
    var sel = $("wiz-template");
    if (!sel) return;
    fetch("/api/templates")
        .then(function(r) { return r.json(); })
        .then(function(templates) {
            sel.innerHTML = '<option value="blank">Blank Page</option>';
            templates.forEach(function(t) {
                var o = document.createElement("option");
                o.value = t.id;
                o.textContent = t.name;
                sel.appendChild(o);
            });
        })
        .catch(function() { /* ignore — template endpoint may not exist */ });
}

// ── Wizard ──
function applyWizard() {
    var title = $("wiz-title").value || "My Album";
    var author = $("wiz-author").value || "";
    var pgSize = $("wiz-pg-size").value || "a4";
    var orient = $("wiz-orient").value || "portrait";
    var border = $("wiz-border").value || "solid";
    var columns = parseInt($("wiz-columns").value) || 0;
    var tpl = $("wiz-template").value;

    if (tpl && tpl !== "blank") {
        // Quick Apply button on template section
        $("btn-wiz-template").click();
        return;
    }

    var lines = [];
    lines.push('ALBUM_TITLE("' + escapeDSL(title) + '")');
    if (author) lines.push('ALBUM_AUTHOR("' + escapeDSL(author) + '")');

    var w = pgSize === "a4" ? 210 : pgSize === "letter" ? 216 : 297;
    var h = pgSize === "a4" ? 297 : pgSize === "letter" ? 279 : 420;
    if (orient === "landscape") { var t = w; w = h; h = t; }
    lines.push("ALBUM_PAGES_SIZE(" + w + " " + h + ")");
    lines.push("ALBUM_PAGES_MARGINS(15 15 15 15)");

    if (border !== "none") {
        lines.push('ALBUM_PAGES_BORDER(0.1 0.5 0.1 1.0)');
        lines.push('COLOUR_ALBUM_BORDER("#666")');
    }

    if (title) lines.push('PAGE_TEXT_CENTRE("HB" 16 "' + escapeDSL(title) + '")');

    if (columns > 1) {
        lines.push("PAGE_COLUMN_START(" + columns + ")");
    }

    parseDSL(lines.join("\n"));
    pushUndo();
    render();
    $("wizard-panel").classList.remove("open");
    showToast("Album created from wizard", "success");
}

// ── DSL round-trip ──
function buildDSL() {
    var lines = [
        'ALBUM_TITLE("' + (_currentFile ? _currentFile.replace(/\.(slbum|txt)$/, "") : "My Album") + '")',
        "ALBUM_PAGES_SIZE(" + mm(_pw) + " " + mm(_ph) + ")",
        "ALBUM_PAGES_MARGINS(15 15 15 15)",
        "PAGE_START"
    ];

    // Add column start if columns enabled
    if (_colMode > 1) {
        lines.push("PAGE_COLUMN_START(" + _colMode + " " + _colGap.toFixed(1) + ")");
    }

    E.forEach(function(el) {
        if (el.t === "image") {
            lines.push('STAMP_ADD_IMG(' + mm(el.x).toFixed(1) + ' ' + mm(el.y).toFixed(1) + ' ' + mm(el.w).toFixed(1) + ' ' + mm(el.h).toFixed(1) + ' "' + (el.img || "") + '" "' + (el.lbl || "") + '" "" "")');
        } else if (el.t === "text") {
            var cmd = el.align === "center" ? "PAGE_TEXT_CENTRE" : el.align === "right" ? "PAGE_TEXT_RIGHT" : "PAGE_TEXT";
            lines.push(cmd + '("' + (el.font || "HN") + '" ' + (el.fs || 12) + ' "' + (el.lbl || "Text") + '")');
        } else if (el.t === "freehand") {
            lines.push('STAMP_ADD_AT(' + mm(el.x).toFixed(1) + ' ' + mm(el.y).toFixed(1) + ' ' + mm(el.w).toFixed(1) + ' ' + mm(el.h).toFixed(1) + ' "' + (el.lbl || "") + '" "freehand" "' + el.bdr + '" "' + el.fill + '")');
        } else {
            lines.push('STAMP_ADD_AT(' + mm(el.x).toFixed(1) + ' ' + mm(el.y).toFixed(1) + ' ' + mm(el.w).toFixed(1) + ' ' + mm(el.h).toFixed(1) + ' "' + (el.lbl || "") + '" "' + el.s + '" "' + el.bdr + '" "' + el.fill + '")');
        }
    });

    // Add column stop if columns were enabled
    if (_colMode > 1) {
        lines.push("PAGE_COLUMN_STOP");
    }

    // Add page management DSL
    for (var i = 1; i < _pages.length; i++) {
        var pgEls = _pages[i];
        if (pgEls && pgEls.length > 0) {
            lines.push("PAGE_START");

            // Add column start for additional pages
            if (_colMode > 1) {
                lines.push("PAGE_COLUMN_START(" + _colMode + " " + _colGap.toFixed(1) + ")");
            }

            pgEls.forEach(function(el) {
                if (el.t === "image") {
                    lines.push('STAMP_ADD_IMG(' + mm(el.x).toFixed(1) + ' ' + mm(el.y).toFixed(1) + ' ' + mm(el.w).toFixed(1) + ' ' + mm(el.h).toFixed(1) + ' "' + (el.img || "") + '" "' + (el.lbl || "") + '" "" "")');
                } else if (el.t === "text") {
                    var cmd = el.align === "center" ? "PAGE_TEXT_CENTRE" : el.align === "right" ? "PAGE_TEXT_RIGHT" : "PAGE_TEXT";
                    lines.push(cmd + '("' + (el.font || "HN") + '" ' + (el.fs || 12) + ' "' + (el.lbl || "Text") + '")');
                } else if (el.t === "freehand") {
                    lines.push('STAMP_ADD_AT(' + mm(el.x).toFixed(1) + ' ' + mm(el.y).toFixed(1) + ' ' + mm(el.w).toFixed(1) + ' ' + mm(el.h).toFixed(1) + ' "' + (el.lbl || "") + '" "freehand" "' + el.bdr + '" "' + el.fill + '")');
                } else {
                    lines.push('STAMP_ADD_AT(' + mm(el.x).toFixed(1) + ' ' + mm(el.y).toFixed(1) + ' ' + mm(el.w).toFixed(1) + ' ' + mm(el.h).toFixed(1) + ' "' + (el.lbl || "") + '" "' + el.s + '" "' + el.bdr + '" "' + el.fill + '")');
                }
            });

            // Add column stop for additional pages
            if (_colMode > 1) {
                lines.push("PAGE_COLUMN_STOP");
            }
        }
    }
    return lines.join("\n");
}

function parseDSL(dsl) {
    E = [];
    var lines = dsl.split("\n");
    _pages = [[]];
    _currentPage = 0;
    var _rowX = 0, _rowY = 12, _rowSpacing = 6, _pageMargin = 15;
    for (var i = 0; i < lines.length; i++) {
        var t = lines[i].trim();
        if (!t || t.charAt(0) === "#") continue;
        // Page setup commands
        var mSize = t.match(/^ALBUM_PAGES_SIZE\(\s*([\d.]+)\s+([\d.]+)\)/);
        if (mSize) {
            _pw = px(parseFloat(mSize[1]));
            _ph = px(parseFloat(mSize[2]));
            $("pg-size").value = "a4";
            continue;
        }
        var mMargin = t.match(/^ALBUM_PAGES_MARGINS\(\s*([\d.]+)\s/);
        if (mMargin) {
            _pageMargin = parseFloat(mMargin[1]);
            continue;
        }
        // PAGE_START — new page
        if (t.match(/^PAGE_START/)) {
            if (E.length > 0) {
                _pages[_currentPage] = JSON.parse(JSON.stringify(E));
                E = [];
            }
            _pages.push([]);
            _currentPage = _pages.length - 1;
            _rowX = _pageMargin;
            _rowY = 12;
            continue;
        }
        // PAGE_COLUMN_START — set column mode
        var mColStart = t.match(/^PAGE_COLUMN_START\(\s*(\d+)(?:\s+([\d.]+))?\)/);
        if (mColStart) {
            _colMode = parseInt(mColStart[1]) || 1;
            _colGap = mColStart[2] ? parseFloat(mColStart[2]) : 10.0;
            $("col-mode").value = _colMode;
            $("col-gap").value = _colGap;
            continue;
        }
        // PAGE_COLUMN_NEXT — column break marker (no-op in visual builder)
        if (t.match(/^PAGE_COLUMN_NEXT/)) {
            continue;
        }
        // PAGE_COLUMN_STOP — reset to single column
        if (t.match(/^PAGE_COLUMN_STOP/)) {
            _colMode = 1;
            _colGap = 10.0;
            $("col-mode").value = 1;
            $("col-gap").value = 10.0;
            continue;
        }
        // PAGE_VSPACE — vertical spacing in row layout
        var mVspace = t.match(/^PAGE_VSPACE\(\s*([\d.]+)\)/);
        if (mVspace) {
            _rowY += parseFloat(mVspace[1]);
            continue;
        }
        // ROW_START_FS — start a row of stamps
        var mRow = t.match(/^ROW_START_FS\(\s*"([^"]*)"\s+(\d+)\s+([\d.]+)\s+([\d.]+)\)/);
        if (mRow) {
            _rowX = _pageMargin;
            _rowSpacing = parseFloat(mRow[4]);
            continue;
        }
        // Commands
        var m = t.match(/^(STAMP_ADD_AT|STAMP_ADD_IMG)\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"\s+"([^"]*)"/);
        if (m) {
            var isImg = m[1] === "STAMP_ADD_IMG";
            E.push({ id: "el" + (nid++), t: isImg ? "image" : "stamp", s: m[7] || "rectangle", x: px(parseFloat(m[2])), y: px(parseFloat(m[3])), w: px(parseFloat(m[4])), h: px(parseFloat(m[5])), lbl: m[6] || "", bdr: "solid", bdrC: "#666", bdrW: 1, fill: "#fff", fillA: 100, img: isImg ? m[6] : "", font: "HN", fs: 12 });
            continue;
        }
        // STAMP_ADD — row-based stamp (from template DSL)
        var mRowStamp = t.match(/^STAMP_ADD\(\s*([\d.]+)\s+([\d.]+)\s+"([^"]*)"(?:\s+"([^"]*)")?(?:\s+"([^"]*)")?\)/);
        if (mRowStamp) {
            E.push({ id: "el" + (nid++), t: "stamp", s: "rectangle", x: px(_rowX), y: px(_rowY), w: px(parseFloat(mRowStamp[1])), h: px(parseFloat(mRowStamp[2])), lbl: mRowStamp[3] || "", bdr: "solid", bdrC: "#666", bdrW: 1, fill: "#fff", fillA: 100, img: "", font: "HN", fs: 12 });
            _rowX += parseFloat(mRowStamp[1]) + _rowSpacing;
            continue;
        }
        var m2 = t.match(/^(PAGE_TEXT|PAGE_TEXT_CENTRE|PAGE_TEXT_CENTER|PAGE_TEXT_RIGHT)\(\s*"([^"]*)"\s+(\d+)\s+"([^"]*)"\)/);
        if (m2) {
            var align = m2[1] === "PAGE_TEXT_CENTRE" || m2[1] === "PAGE_TEXT_CENTER" ? "center" : m2[1] === "PAGE_TEXT_RIGHT" ? "right" : "left";
            E.push({ id: "el" + (nid++), t: "text", s: "text", x: 10, y: _rowY > 12 ? _rowY + 2 : 10, w: 100, h: 20, lbl: m2[4] || "Text", font: m2[2] || "HN", fs: parseFloat(m2[3]) || 12, align: align, bdr: "none", fill: "transparent", fillA: 0 });
            _rowY += 8;
        }
    }
    // Save current page
    if (E.length > 0 || _pages.length === 0) {
        _pages[_currentPage] = JSON.parse(JSON.stringify(E));
    }
    // Remove empty trailing pages
    while (_pages.length > 1 && _pages[_pages.length - 1].length === 0) {
        _pages.pop();
    }
    E = JSON.parse(JSON.stringify(_pages[_currentPage]));
    sel = null;
    renderPageDots();
    render();
    updateProps();
    updateGrid();
    updateTitle();
}

// ── Init ──
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
})();
