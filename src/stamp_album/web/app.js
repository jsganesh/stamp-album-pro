"use strict";
(function(){
var E = [], sel = null, nid = 1, _sc = 2.5, _sn = 5, _pw = 595, _ph = 842, _init = false;
var _drg = false, _dragEl = null, _dragH = null, _ds = {};
var _defBdr = "solid", _defBdrC = "#666", _defFillC = "#fff";
var _collapsed = { sb: false, rp: false };
var _currentFile = null, _currentPage = 0, _pages = [ [] ];
var _dirty = false;
var _colMode = 1, _colGap = 10.0, _pageBorder = "double", _pageBorderC = "";  // Column layout mode, gap (mm), page border style

// ── Forward references (set by render.js after load) ──
var render = function() { S.render(); };
var updateProps = function() { S.updateProps(); };

// ── Undo/redo system (defined in undo.js) ──
var _undoStack = [], _redoStack = [], _undoPaused = false;

// ── localStorage draft persistence ──
var _draftTimer = null;
var _draftKey = "stampalbum.draft";
var _draftFileKey = "stampalbum.currentFile";
var _draftDebounceMs = 500;

function saveDraft() {
    try {
        var state = { v: 1, pages: _pages, currentPage: _currentPage, elements: E };
        localStorage.setItem(_draftKey, JSON.stringify(state));
        if (_currentFile) localStorage.setItem(_draftFileKey, _currentFile);
        else localStorage.removeItem(_draftFileKey);
    } catch (_) { /* quota exceeded — silent */ }
}
function scheduleDraftSave() {
    if (_draftTimer) clearTimeout(_draftTimer);
    _draftTimer = setTimeout(function() { _draftTimer = null; saveDraft(); }, _draftDebounceMs);
}
function loadDraft() {
    try {
        var raw = localStorage.getItem(_draftKey);
        if (!raw) return false;
        var state = JSON.parse(raw);
        if (!state || !state.pages || !state.pages.length) return false;
        _pages = state.pages;
        _currentPage = state.currentPage || 0;
        if (_currentPage >= _pages.length) _currentPage = _pages.length - 1;
        E = _pages[_currentPage] || [];
        sel = null;
        var savedFile = localStorage.getItem(_draftFileKey);
        if (savedFile) _currentFile = savedFile;
        return true;
    } catch (_) { return false; }
}
function clearDraft() {
    localStorage.removeItem(_draftKey);
    localStorage.removeItem(_draftFileKey);
}

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
    if (!silent) S.pushUndo();
    _pages[_currentPage] = JSON.parse(JSON.stringify(E));
    _currentPage = idx;
    E = _pages[idx] ? JSON.parse(JSON.stringify(_pages[idx])) : [];
    sel = null;
    renderPageDots();
    render();
    if (S.renderPageBorder) S.renderPageBorder(_pageBorder || "double");
    updateProps();
}
function addPage() {
    S.pushUndo();
    _pages.push([]);
    switchPage(_pages.length - 1, true);
    showToast("Page added", "success");
}
function deletePage() {
    if (_pages.length <= 1) { showToast("Cannot delete last page", "error"); return; }
    S.pushUndo();
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
            var h = gs / 2;
            path.setAttribute("d", "M " + h + " 0 L " + h + " " + gs + " M 0 " + h + " L " + gs + " " + h);
        }
        svg.style.display = "block";
    } else {
        svg.style.display = "none";
    }
}




// ── New album ──
function newAlbum() {
    if (_dirty && !confirm("Discard unsaved changes?")) return;
    clearDraft();
    E = [];
    sel = null;
    _currentFile = null;
    _currentPage = 0;
    _pages = [[]];
    _dirty = false;
    _undoStack = [];
    _redoStack = [];
    _undoStack.push(JSON.stringify(E));
    render();
    updateProps();
    renderPageDots();
    updateTitle();
    showToast("New album created", "success");
}

// ── File/image management functions defined in files.js ──

// ── Build canvas state for direct render/export ──
function buildCanvasState(format) {
    var allPages = _pages.slice();
    allPages[_currentPage] = JSON.parse(JSON.stringify(E));
    var firstIdx = 0;
    while (firstIdx < allPages.length && allPages[firstIdx].length === 0) {
        firstIdx++;
    }
    var firstPage = firstIdx < allPages.length ? allPages[firstIdx] : [];
    var restPages = allPages.slice(firstIdx + 1);
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
        title: (_currentFile || "").replace(/\.(slbum|txt)$/, ""),
        author: "",
        border_style: _pageBorder || "",
        border_color: _pageBorderC || ""
    };
}

// ── Preview (direct — no DSL parser) ──
var _previewTimer = null;
function refreshPreview() {
    var frame = $("preview-frame");
    if (!frame) return;
    var overlay = $("preview-overlay");
    if (!overlay || !overlay.classList.contains("open")) return;
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
        frame.srcdoc = html;
        frame.onload = function() {
            frame.onload = null;
            try {
                var doc = frame.contentDocument;
                if (!doc) return;
                var page = doc.querySelector(".page");
                if (!page) return;
                var w = page.offsetWidth, h = page.offsetHeight;
                if (w > 0 && h > 0) {
                    frame.style.width = w + "px";
                    frame.style.height = h + "px";
                }
            } catch(_) {}
        };
        showToast("Preview ready", "success");
    })
    .catch(function(err) {
        var msg = err.message || String(err);
        if (msg.indexOf("NetworkError") !== -1 || msg.indexOf("Load failed") !== -1 || msg.indexOf("Failed to fetch") !== -1) {
            showToast("Preview failed — network error. Try a normal reload (Cmd+R) and if it persists, click ⟳ Reset.", "error");
        } else {
            showToast("Preview failed: " + msg, "error");
        }
    });
}
function schedulePreviewRefresh() {
    if (_previewTimer) clearTimeout(_previewTimer);
    _previewTimer = setTimeout(refreshPreview, 400);
}
function openPreview() {
    var overlay = $("preview-overlay");
    if (!overlay) return;
    overlay.classList.add("open");
    refreshPreview();
}

// ── Export PDF (direct — no DSL parser) ──
function exportPDF() {
    showToast("Generating PDF...", "info");
    var filename = _currentFile ? _currentFile.replace(/\.(slbum|txt)$/, ".pdf") : "album.pdf";
    var state = buildCanvasState("pdf");
    var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timeout = setTimeout(function() {
        if (controller) controller.abort();
        showToast("Export timed out — try with fewer stamps", "error");
    }, 30000);
    fetch("/export-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state),
        signal: controller ? controller.signal : undefined
    })
    .then(function(r) {
        clearTimeout(timeout);
        if (!r.ok) throw new Error("Server returned " + r.status);
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
    .catch(function(err) {
        clearTimeout(timeout);
        var msg = err.message || String(err);
        if (msg.indexOf("abort") !== -1) return;
        if (msg.indexOf("NetworkError") !== -1 || msg.indexOf("Load failed") !== -1 || msg.indexOf("Failed to fetch") !== -1) {
            showToast("Export failed — network error. Try a normal reload (Cmd+R) and if it persists, click ⟳ Reset.", "error");
        } else {
            showToast("Export failed: " + msg, "error");
        }
    });
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
    var title = $("wiz-title").value || "";
    var author = $("wiz-author").value || "";
    var pgSize = $("wiz-pg-size").value || "a4";
    var orient = $("wiz-orient").value || "portrait";
    var columns = parseInt($("wiz-columns").value) || 0;
    var tpl = $("wiz-template").value;

    if (tpl && tpl !== "blank") {
        // Quick Apply button on template section
        $("btn-wiz-template").click();
        return;
    }

    var lines = [];
    lines.push('ALBUM_TITLE("' + title + '")');
    if (author) lines.push('ALBUM_AUTHOR("' + author + '")');

    var w = pgSize === "a4" ? 210 : pgSize === "letter" ? 216 : 297;
    var h = pgSize === "a4" ? 297 : pgSize === "letter" ? 279 : 420;
    if (orient === "landscape") { var t = w; w = h; h = t; }
    lines.push("ALBUM_PAGES_SIZE(" + w + " " + h + ")");
    lines.push("ALBUM_PAGES_MARGINS(15 15 15 15)");

    if (title) lines.push('PAGE_TEXT_CENTRE("HB" 16 "' + title + '")');

    if (columns > 1) {
        lines.push("PAGE_COLUMN_START(" + columns + ")");
    }

    S.parseDSL(lines.join("\n"));
    S.pushUndo();
    render();
    $("wizard-panel").classList.remove("open");
    showToast("Album created from wizard", "success");
}

// ── DSL functions (escapeDSL, buildDSL, parseDSL) defined in dsl.js ──

// ── Exports (shared state + functions for render.js, events.js, init.js) ──
var S = {};
Object.defineProperties(S, {
    E: { get: function(){ return E; }, set: function(v){ E = v; } },
    sel: { get: function(){ return sel; }, set: function(v){ sel = v; } },
    nid: { get: function(){ return nid; }, set: function(v){ nid = v; } },
    _sc: { get: function(){ return _sc; }, set: function(v){ _sc = v; } },
    _sn: { get: function(){ return _sn; }, set: function(v){ _sn = v; } },
    _pw: { get: function(){ return _pw; }, set: function(v){ _pw = v; } },
    _ph: { get: function(){ return _ph; }, set: function(v){ _ph = v; } },
    _drg: { get: function(){ return _drg; }, set: function(v){ _drg = v; } },
    _dragEl: { get: function(){ return _dragEl; }, set: function(v){ _dragEl = v; } },
    _dragH: { get: function(){ return _dragH; }, set: function(v){ _dragH = v; } },
    _ds: { get: function(){ return _ds; }, set: function(v){ _ds = v; } },
    _defBdr: { get: function(){ return _defBdr; }, set: function(v){ _defBdr = v; } },
    _defBdrC: { get: function(){ return _defBdrC; }, set: function(v){ _defBdrC = v; } },
    _defFillC: { get: function(){ return _defFillC; }, set: function(v){ _defFillC = v; } },
    _collapsed: { get: function(){ return _collapsed; }, set: function(v){ _collapsed = v; } },
    _currentFile: { get: function(){ return _currentFile; }, set: function(v){ _currentFile = v; } },
    _currentPage: { get: function(){ return _currentPage; }, set: function(v){ _currentPage = v; } },
    _pages: { get: function(){ return _pages; }, set: function(v){ _pages = v; } },
    _dirty: { get: function(){ return _dirty; }, set: function(v){ _dirty = v; } },
    _colMode: { get: function(){ return _colMode; }, set: function(v){ _colMode = v; } },
    _colGap: { get: function(){ return _colGap; }, set: function(v){ _colGap = v; } },
    _pageBorder: { get: function(){ return _pageBorder; }, set: function(v){ _pageBorder = v; } },
    _pageBorderC: { get: function(){ return _pageBorderC; }, set: function(v){ _pageBorderC = v; } },
    _undoStack: { get: function(){ return _undoStack; }, set: function(v){ _undoStack = v; } },
    _redoStack: { get: function(){ return _redoStack; }, set: function(v){ _redoStack = v; } },
    _undoPaused: { get: function(){ return _undoPaused; }, set: function(v){ _undoPaused = v; } },
    _init: { get: function(){ return _init; }, set: function(v){ _init = v; } },
    SYSTEM_FONTS: { get: function(){ return SYSTEM_FONTS; }, set: function(v){ SYSTEM_FONTS = v; } },
    $: { value: $ }, mm: { value: mm }, px: { value: px }, clamp: { value: clamp },
    fontCSS: { value: fontCSS }, showToast: { value: showToast },
    // pushUndo/undo/redo/loadElements defined in undo.js
    saveDraft: { value: saveDraft }, scheduleDraftSave: { value: scheduleDraftSave },
    loadDraft: { value: loadDraft }, clearDraft: { value: clearDraft },
    updateTitle: { value: updateTitle }, switchPage: { value: switchPage },
    addPage: { value: addPage }, deletePage: { value: deletePage },
    renderPageDots: { value: renderPageDots }, updateGrid: { value: updateGrid },
    newAlbum: { value: newAlbum },     // loadFileList/saveFile/uploadImageFile/loadImageList defined in files.js
    buildCanvasState: { value: buildCanvasState }, openPreview: { value: openPreview },
    schedulePreviewRefresh: { value: schedulePreviewRefresh }, refreshPreview: { value: refreshPreview },
    exportPDF: { value: exportPDF }, loadTemplateList: { value: loadTemplateList },
    applyWizard: { value: applyWizard },
    // ── Alignment functions ──
    alignSelected: { value: alignSelected },
    distributeSelected: { value: distributeSelected },
    matchSize: { value: matchSize },
    toggleAlignGroup: { value: toggleAlignGroup },
    toggleSnap: { value: toggleSnap },
    toggleLargeText: { value: toggleLargeText },
    resetApp: { value: resetApp },
});

// ── Alignment functions ──
function getSelectedElements() {
    if (!S.sel) return [];
    return S.E.filter(function(el) { return el.id === S.sel; });
}

function alignSelected(direction) {
    if (!S.sel) { showToast("Select an element first", "error"); return; }
    var el = S.E.find(function(x) { return x.id === S.sel; });
    if (!el) return;
    var pw = S._pw, ph = S._ph;
    switch (direction) {
        case "left": el.x = 20; break;
        case "center": el.x = Math.round((pw - el.w) / 2); break;
        case "right": el.x = pw - el.w - 20; break;
        case "top": el.y = 20; break;
        case "middle": el.y = Math.round((ph - el.h) / 2); break;
        case "bottom": el.y = ph - el.h - 20; break;
    }
    S.pushUndo();
    S.render();
    S.updateProps();
    showToast("Aligned: " + direction, "success");
}

function distributeSelected(axis) {
    if (!S.sel) { showToast("Select elements first", "error"); return; }
    var sel = S.E.filter(function(el) { return el.id === S.sel; });
    if (sel.length < 2) { showToast("Select at least 2 elements to distribute", "error"); return; }
    var sorted = sel.slice().sort(function(a, b) {
        return axis === "h" ? a.x - b.x : a.y - b.y;
    });
    var first = sorted[0], last = sorted[sorted.length - 1];
    var span = axis === "h" ? (last.x + last.w - first.x) : (last.y + last.h - first.y);
    var totalSize = sorted.reduce(function(s, el) {
        return s + (axis === "h" ? el.w : el.h);
    }, 0);
    var gap = (span - totalSize) / (sorted.length - 1);
    var cursor = axis === "h" ? first.x : first.y;
    sorted.forEach(function(el) {
        if (axis === "h") { el.x = Math.round(cursor); cursor += el.w + gap; }
        else { el.y = Math.round(cursor); cursor += el.h + gap; }
    });
    S.pushUndo();
    S.render();
    showToast("Distributed: " + (axis === "h" ? "horizontally" : "vertically"), "success");
}

function matchSize(axis) {
    if (!S.sel) { showToast("Select elements first", "error"); return; }
    var sel = S.E.filter(function(el) { return el.id === S.sel; });
    if (sel.length < 2) { showToast("Select at least 2 elements to match", "error"); return; }
    var ref = sel[0];
    sel.forEach(function(el) {
        if (el.id === ref.id) return;
        if (axis === "w") { el.w = ref.w; }
        else { el.h = ref.h; }
    });
    S.pushUndo();
    S.render();
    S.updateProps();
    showToast("Matched: " + (axis === "w" ? "width" : "height"), "success");
}

function toggleAlignGroup() {
    var group = document.getElementById("align-group");
    if (!group) return;
    var isVisible = group.style.display !== "none";
    group.style.display = isVisible ? "none" : "flex";
}

function toggleSnap() {
    var btn = document.getElementById("btn-snap");
    if (!btn) return;
    btn.classList.toggle("active");
    S._snapEnabled = btn.classList.contains("active");
    showToast(S._snapEnabled ? "Snap-to-guide ON" : "Snap-to-guide OFF", "info");
}

function toggleLargeText() {
    var btn = document.getElementById("btn-large-text");
    if (!btn) return;
    btn.classList.toggle("active");
    document.body.classList.toggle("large-text");
    showToast(document.body.classList.contains("large-text") ? "Large Text ON" : "Large Text OFF", "info");
}

function resetApp() {
    if (!confirm("Reset App — this will clear all saved drafts and reload the page. Continue?")) return;
    clearDraft();
    localStorage.removeItem(_draftKey);
    localStorage.removeItem(_draftFileKey);
    location.reload();
}
window.StampAlbum = S;

// ── Init (events.js provides S.init) ──
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function(){ if (S.init) S.init(); });
else if (S.init) S.init();
})();
