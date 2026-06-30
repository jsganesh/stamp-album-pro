"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast;
var pushUndo = S.pushUndo, render = S.render, updateProps = S.updateProps;
var select = S.select, add = S.add, undo = S.undo, redo = S.redo;
var newAlbum = S.newAlbum, saveFile = S.saveFile, loadFileList = S.loadFileList;
var loadImageList = S.loadImageList, uploadImageFile = S.uploadImageFile;
var openPreview = S.openPreview, exportPDF = S.exportPDF;
var applyWizard = S.applyWizard, loadTemplateList = S.loadTemplateList, loadDraft = S.loadDraft;
var buildDSL = S.buildDSL, parseDSL = S.parseDSL;
var initTutorial = S.initTutorial, _wireTutorialEvents = S._wireTutorialEvents;
var drawAlignmentGuides = S.drawAlignmentGuides, clearAlignmentGuides = S.clearAlignmentGuides;

// ── Canvas init ──
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
            el[key] = transform ? transform(this.value) : S.mm(parseFloat(this.value) || 0);
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
                    lbl: el.label ? el.label + " (" + (r + 1) + "," + (c + 1) + ")" : "" }));
            }
        }
    });
    $("btn-del").addEventListener("click", function() {
        if (!S.sel) return;
        if (!confirm("Delete this element?")) return;
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
    // ── DSL Editor (CodeMirror 6) ──
    var _cmEditor = null;
    function initCodeMirror() {
        if (_cmEditor) return _cmEditor;
        if (typeof CodeMirror === "undefined") return null;
        var ta = $("dsl-ta");
        if (!ta) return null;
        _cmEditor = CodeMirror.fromTextArea(ta, {
            mode: "text/x-stampalbum",
            theme: "default",
            lineNumbers: true,
            lineWrapping: true,
            indentUnit: 2,
            tabSize: 2,
            autofocus: false,
            placeholder: '# Enter DSL commands here...\nALBUM_TITLE("My Album")\nPAGE_START\nSTAMP_ADD(40 30 "Description" "" "" "")',
        });
        // Custom DSL highlighting (simple keyword-based)
        CodeMirror.defineMode("text/x-stampalbum", function() {
            return {
                token: function(stream) {
                    if (stream.match(/^#.*/)) return "comment";
                    if (stream.match(/^(ALBUM_TITLE|ALBUM_AUTHOR|ALBUM_PAGES_SIZE|ALBUM_PAGES_MARGINS|ALBUM_PAGES_BORDER|ALBUM_PAGES_SPACING|ALBUM_PAGES_TITLE|ALBUM_DEFINE_FONT|PAGE_START|PAGE_TEXT|PAGE_TEXT_CENTRE|PAGE_TEXT_CENTER|PAGE_TEXT_RIGHT|PAGE_RULE_H|PAGE_VSPACE|PAGE_COLUMN_START|PAGE_COLUMN_NEXT|PAGE_COLUMN_STOP|ROW_START_FS|ROW_START_ES|ROW_START_JS|STAMP_ADD|STAMP_ADD_AT|STAMP_ADD_IMG|STAMP_ADD_TRIANGLE|STAMP_ADD_DIAMOND|STAMP_ADD_OVAL|STAMP_ADD_HEXAGON|STAMP_ADD_OCTAGON|STAMP_ADD_PENTAGON|STAMP_HEADING|COLOUR_|COLOR_|\$DEFINE|\$UNDEFINE|\$IFDEF|\$ELSEIF|\$ELSE|\$ENDIF|\$INCLUDE)/)) return "keyword";
                    if (stream.match(/^"[^"]*"/)) return "string";
                    if (stream.match(/^\d+(\.\d+)?/)) return "number";
                    stream.next();
                    return null;
                }
            };
        });
        _cmEditor.on("change", function() { _cmEditor.save(); });
        return _cmEditor;
    }
    $("btn-dsl").addEventListener("click", function() {
        $("dsl-panel").classList.toggle("open");
        if ($("dsl-panel").classList.contains("open")) {
            var cm = initCodeMirror();
            if (cm) { cm.setValue(buildDSL()); cm.refresh(); cm.focus(); }
            else { $("dsl-ta").value = buildDSL(); }
        }
    });
    $("btn-app-dsl").addEventListener("click", function() {
        var dsl = _cmEditor ? _cmEditor.getValue() : $("dsl-ta").value;
        parseDSL(dsl);
        pushUndo();
        render();
        showToast("DSL applied", "success");
    });
    $("btn-cls-dsl").addEventListener("click", function() {
        $("dsl-panel").classList.remove("open");
        if (_cmEditor) { _cmEditor.toTextArea(); _cmEditor = null; }
    });

    // ── DSL Reference Panel ──
    var dslRefBtn = $("btn-dsl-ref");
    if (dslRefBtn) {
        dslRefBtn.addEventListener("click", function() {
            var refPanel = $("dsl-ref-panel");
            if (refPanel) refPanel.classList.toggle("open");
        });
    }

    // ── Preview ──
    $("btn-preview").addEventListener("click", openPreview);
    $("btn-preview-close").addEventListener("click", function() { $("preview-overlay").classList.remove("open"); });
    $("btn-preview-refresh").addEventListener("click", openPreview);
    $("btn-preview-export").addEventListener("click", function() { if (exportPDF) exportPDF(); });

    // ── Export ──
    $("btn-export").addEventListener("click", function() { if (exportPDF) exportPDF(); });

    // ── Image Upload ──
    $("img-upl-btn").addEventListener("click", function() { $("upl-inp").click(); });
    $("upl-inp").addEventListener("change", function(e) {
        if (e.target.files.length === 0) return;
        var f = e.target.files[0];
        uploadImageFile(f, function(imgName) {
            var r = $("page").getBoundingClientRect();
            add({ t: "image", s: "rectangle", x: 50, y: 50, w: 80, h: 60,
                lbl: f.name, img: "/images/" + imgName,
                bdr: "solid", bdrC: "#999", bdrW: 0.5, fill: "#fff", fillA: 100, font: "HN", fs: 12 });
            loadImageList();
        });
        e.target.value = "";
    });

    // ── Change / Remove Image ──
    $("btn-chg-img").addEventListener("click", function() {
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
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
        var el = S.E.find(function(x) { return x.id === S.sel; }); if (!el) return;
        el.img = ""; pushUndo(); render();
    });

    // ── Page Size / Grid ──
    $("pg-size").addEventListener("change", function() {
        var s = { a4: [595, 842], letter: [612, 792], a3: [842, 1191] };
        var v = s[this.value] || s.a4;
        S._pw = v[0]; S._ph = v[1];
        $("page").className = "page " + this.value;
        render();
        S.updateGrid();
        if (S.renderPageBorder) S.renderPageBorder(S._pageBorder || "double");
    });
    $("grid").addEventListener("change", function() {
        S._sn = parseInt(this.value) || 0;
        S.updateGrid();
    });

    // ── Column layout ──
    $("col-mode").addEventListener("change", function() {
        S._colMode = parseInt(this.value) || 1;
        render();
    });
    $("col-gap").addEventListener("change", function() {
        S._colGap = parseFloat(this.value) || 10.0;
        render();
    });

    // ── Default colors — also update page border ──
    $("def-bdr").addEventListener("change", function() {
        S._defBdr = this.value;
        S._pageBorder = this.value;
        if (S.renderPageBorder) S.renderPageBorder(S._pageBorder);
    });
    $("def-bdr-c").addEventListener("change", function() {
        S._defBdrC = this.value;
        S._pageBorderC = this.value;
        if (S.renderPageBorder) S.renderPageBorder(S._pageBorder);
    });
    $("def-fill-c").addEventListener("change", function() { S._defFillC = this.value; });

    // ── Collapsible Panels ──
    $("sb-toggle").addEventListener("click", function() {
        S._collapsed.sb = !S._collapsed.sb;
        $("sidebar").classList.toggle("collapsed", S._collapsed.sb);
        this.textContent = S._collapsed.sb ? "▶" : "◀";
    });
    $("rp-toggle").addEventListener("click", function() {
        S._collapsed.rp = !S._collapsed.rp;
        $("rp").classList.toggle("collapsed", S._collapsed.rp);
        this.textContent = S._collapsed.rp ? "◀" : "▶";
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
            S._currentFile = f.name;
            parseDSL(dsl);
            S._dirty = false;
            S.updateTitle();
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
            if (S.sel) { $("btn-del").click(); }
        }
        if (e.key === "Escape") { S.sel = null; render(); updateProps(); }
        if ((e.ctrlKey || e.metaKey) && e.key === "d" && S.sel) {
            e.preventDefault();
            var el = S.E.find(function(x) { return x.id === S.sel; }); if (el) add(Object.assign({}, el, { id: "el" + (S.nid++), x: el.x + 20, y: el.y + 20 }));
        }
        if (e.key === "F5") { e.preventDefault(); openPreview(); }
        if (e.key === "?") { e.preventDefault(); $("help-overlay").classList.toggle("open"); }
    });

    // ── Help overlay ──
    var btnHelp = $("btn-help");
    var helpOverlay = $("help-overlay");
    var btnHelpClose = $("btn-help-close");
    if (btnHelp && helpOverlay) {
        btnHelp.addEventListener("click", function() { helpOverlay.classList.toggle("open"); });
    }
    if (btnHelpClose && helpOverlay) {
        btnHelpClose.addEventListener("click", function() { helpOverlay.classList.remove("open"); });
    }
    if (helpOverlay) {
        helpOverlay.addEventListener("click", function(e) {
            if (e.target === this) this.classList.remove("open");
        });
    }

    // ── Alignment toolbar ──
    $("btn-align-l").addEventListener("click", function() { if (S.alignSelected) S.alignSelected("left"); });
    $("btn-align-c").addEventListener("click", function() { if (S.alignSelected) S.alignSelected("center"); });
    $("btn-align-r").addEventListener("click", function() { if (S.alignSelected) S.alignSelected("right"); });
    $("btn-align-t").addEventListener("click", function() { if (S.alignSelected) S.alignSelected("top"); });
    $("btn-align-m").addEventListener("click", function() { if (S.alignSelected) S.alignSelected("middle"); });
    $("btn-align-b").addEventListener("click", function() { if (S.alignSelected) S.alignSelected("bottom"); });
    $("btn-dist-h").addEventListener("click", function() { if (S.distributeSelected) S.distributeSelected("h"); });
    $("btn-dist-v").addEventListener("click", function() { if (S.distributeSelected) S.distributeSelected("v"); });
    $("btn-match-w").addEventListener("click", function() { if (S.matchSize) S.matchSize("w"); });
    $("btn-match-h").addEventListener("click", function() { if (S.matchSize) S.matchSize("h"); });
    $("btn-snap").addEventListener("click", function() { if (S.toggleSnap) S.toggleSnap(); });

    // Show alignment group when element is selected
    var origSelect = S.select;
    S.select = function(id) {
        origSelect(id);
        var group = $("align-group");
        if (group) group.style.display = id ? "flex" : "none";
    };

    // ── Font population ──
    S.populateFonts();

    // ── Load templates ──
    loadTemplateList();
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
        openTemplateGallery();
    });

    // ── Template Gallery panel ──
    $("btn-tg-close").addEventListener("click", function() {
        $("template-gallery-panel").classList.remove("open");
    });

    function openTemplateGallery() {
        var grid = $("template-grid");
        if (!grid) return;
        grid.innerHTML = '<div class="tg-loading">Loading templates...</div>';
        $("template-gallery-panel").classList.add("open");
        fetch("/api/templates")
            .then(function(r) { return r.json(); })
            .then(function(templates) {
                grid.innerHTML = "";
                templates.forEach(function(t) {
                    var card = document.createElement("div");
                    card.className = "tg-card";
                    card.innerHTML = '<div class="tg-card-title">' + t.name + '</div>' +
                        '<div class="tg-card-desc">' + (t.description || "") + '</div>' +
                        '<div class="tg-card-cat">' + (t.category || "") + "</div>";
                    card.addEventListener("click", function() {
                        fetch("/api/templates/" + t.id)
                            .then(function(r) { return r.json(); })
                            .then(function(data) {
                                if (data.dsl) {
                                    parseDSL(data.dsl);
                                    pushUndo();
                                    render();
                                    showToast("Template loaded: " + data.name, "success");
                                    $("template-gallery-panel").classList.remove("open");
                                    $("wizard-panel").classList.remove("open");
                                }
                            })
                            .catch(function(err) { showToast("Failed to load: " + err, "error"); });
                    });
                    grid.appendChild(card);
                });
            })
            .catch(function() {
                grid.innerHTML = '<div class="tg-error">Could not load templates</div>';
            });
    }

    // ── New file button ──
    $("btn-new-file").addEventListener("click", newAlbum);

    // ── Large Text Mode ──
    $("btn-large-text").addEventListener("click", function() { if (S.toggleLargeText) S.toggleLargeText(); });

    // ── Reset App ──
    $("btn-reset").addEventListener("click", function() { if (S.resetApp) S.resetApp(); });

    // ── Help overlay ──
    $("btn-help").addEventListener("click", function() {
        var overlay = $("help-overlay");
        if (overlay) overlay.classList.toggle("open");
    });
    $("btn-help-close").addEventListener("click", function() {
        var overlay = $("help-overlay");
        if (overlay) overlay.classList.remove("open");
    });

    // ── CSV / Excel Import ──
    $("btn-import-csv").addEventListener("click", function() {
        $("imp-inp").accept = ".csv";
        $("imp-inp").click();
    });
    $("btn-import-excel").addEventListener("click", function() {
        $("imp-inp").accept = ".xlsx,.xls";
        $("imp-inp").click();
    });
    $("imp-inp").addEventListener("change", function() {
        var file = this.files[0];
        if (!file) return;
        var isExcel = file.name.toLowerCase().endsWith(".xlsx") || file.name.toLowerCase().endsWith(".xls");
        var endpoint = isExcel ? "/api/stamps/import-excel" : "/api/stamps/import";
        var fd = new FormData();
        fd.append("file", file);
        showToast("Importing " + file.name + "...", "info");
        fetch(endpoint, { method: "POST", body: fd })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.errors && data.errors.length > 0) {
                    showToast("Imported " + data.imported + " stamps (" + data.errors.length + " errors)", "info");
                } else {
                    showToast("Imported " + data.imported + " stamps", "success");
                }
            })
            .catch(function(err) { showToast("Import failed: " + err, "error"); });
        this.value = "";
    });

    // ── Touch / Pointer support for iPad ──
    document.querySelectorAll(".p-item[draggable]").forEach(function(it) {
        it.addEventListener("touchstart", function(e) {
            var touch = e.touches[0];
            S._ds = { t: it.dataset.t, s: it.dataset.s || "rectangle", st: it.dataset.st || "",
                w: parseFloat(it.dataset.w) || 80, h: parseFloat(it.dataset.h) || 60,
                font: "HN", fs: 12, tx: touch.clientX, ty: touch.clientY };
            e.preventDefault();
        }, { passive: false });
    });
    document.addEventListener("touchmove", function(e) {
        if (!S._ds || !S._ds.t) return;
        e.preventDefault();
    }, { passive: false });
    document.addEventListener("touchend", function(e) {
        if (!S._ds || !S._ds.t) return;
        var touch = e.changedTouches[0];
        var pg = $("page");
        if (pg) {
            var r = pg.getBoundingClientRect();
            var cx = touch.clientX, cy = touch.clientY;
            if (cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom) {
                var x = Math.max(0, Math.min(Math.round((cx - r.left) / S._sn) * S._sn, S._pw - 40));
                var y = Math.max(0, Math.min(Math.round((cy - r.top) / S._sn) * S._sn, S._ph - 30));
                var d = S._ds;
                var w = d.w || 80, h = d.h || 60;
                if (d.t === "text") { w = 120; h = d.st === "heading" ? 24 : d.st === "desc" ? 16 : 18; }
                if (d.t === "freehand") { w = 100; h = 80; }
                add({ t: d.t || "stamp", s: d.s || "rectangle", x: x, y: y, w: w, h: h,
                    lbl: d.t === "text" ? (d.st === "heading" ? "Heading" : d.st === "desc" ? "Description" : "Label") : "",
                    font: d.font || "HN", fs: d.st === "heading" ? 16 : d.st === "desc" ? 10 : 12,
                    bdr: S._defBdr, bdrC: S._defBdrC, bdrW: 1, fill: S._defFillC, fillA: 100, img: "" });
            }
        }
        S._ds = {};
    });
    document.addEventListener("touchstart", function(e) {
        var el = e.target.closest(".cel");
        if (!el) return;
        var obj = S.E.find(function(x) { return x.id === el.dataset.id; });
        if (!obj) return;
        var touch = e.touches[0];
        S._dragH = e.target.classList.contains("rh") ? e.target.dataset.h : "move";
        select(obj.id);
        S._drg = true;
        S._dragEl = obj;
        S._ds = { x: touch.clientX, y: touch.clientY, ox: obj.x, oy: obj.y, ow: obj.w, oh: obj.h };
    }, { passive: true });
    document.addEventListener("touchmove", function(e) {
        if (!S._drg || !S._dragEl) return;
        var touch = e.touches[0];
        var dx = Math.round((touch.clientX - S._ds.x) / S._sn) * S._sn;
        var dy = Math.round((touch.clientY - S._ds.y) / S._sn) * S._sn;
        var h = S._dragH, x = S._ds.ox, y = S._ds.oy, w = S._ds.ow, oh = S._ds.oh;
        if (h === "move") { x += dx; y += dy; } else {
            if (h.indexOf("w") >= 0) { x += dx; w -= dx; }
            if (h.indexOf("e") >= 0) { w += dx; }
            if (h.indexOf("n") >= 0) { y += dy; oh -= dy; }
            if (h.indexOf("s") >= 0) { oh += dy; }
            if (w < 10) w = 10;
            if (oh < 10) oh = 10;
        }
        S._dragEl.x = Math.max(0, Math.min(x, S._pw - S._dragEl.w));
        S._dragEl.y = Math.max(0, Math.min(y, S._ph - S._dragEl.h));
        S._dragEl.w = Math.min(w, S._pw - S._dragEl.x);
        S._dragEl.h = Math.min(oh, S._ph - S._dragEl.y);
        render();
        updateProps();
        e.preventDefault();
    }, { passive: false });
    document.addEventListener("touchend", function() {
        if (S._drg && S._dragEl) { pushUndo(); }
        S._drg = false;
        S._dragEl = null;
        S._dragH = null;
    });

    // ── Before unload ──
    window.addEventListener("beforeunload", function(e) {
        if (S._dirty) { e.preventDefault(); e.returnValue = ""; }
    });

    // ── Restore draft from localStorage ──
    if (loadDraft) {
        var _restored = loadDraft();
        if (_restored) console.log("StampAlbum Pro: restored draft from localStorage");
    }

    // ── Init ──
    S.renderPageDots();
    S.updateGrid();
    if (S.renderPageBorder) S.renderPageBorder(S._pageBorder || "double");
    loadFileList();
    loadImageList();
    S.updateTitle();

    // ── First-run tutorial ──
    if (initTutorial) initTutorial();
    if (_wireTutorialEvents) _wireTutorialEvents();

    console.log("StampAlbum Pro: ready");
}

// ── Exports ──
S.init = init;

// Auto-init when DOM is ready
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();

})();
