"use strict";
(function(){
// ── Shared state ──
// All modules access these via window.StampAlbum
window.StampAlbum = {
    E: [], sel: null, nid: 1, _sc: 2.5, _sn: 5, _pw: 595, _ph: 842,
    _init: false,
    _drg: false, _dragEl: null, _dragH: null, _ds: {},
    _defBdr: "solid", _defBdrC: "#666", _defFillC: "#fff",
    _collapsed: { sb: false, rp: false },
    _currentFile: null, _currentPage: 0, _pages: [ [] ],
    _dirty: false,
    _colMode: 1, _colGap: 10.0
};

var S = window.StampAlbum;

// ── Utility ──
function $(id) { return document.getElementById(id); }
function mm(px) { return Math.round(px / S._sc * 10) / 10; }
function px(mm) { return Math.round(mm * S._sc); }
function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

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
        var name = S._currentFile || "Untitled";
        fn.textContent = (S._dirty ? "● " : "") + name;
    }
}

// ── Page management ──
function switchPage(idx, silent) {
    if (idx < 0 || idx >= S._pages.length) return;
    if (!silent) pushUndo();
    S._pages[S._currentPage] = JSON.parse(JSON.stringify(S.E));
    S._currentPage = idx;
    S.E = S._pages[idx] ? JSON.parse(JSON.stringify(S._pages[idx])) : [];
    S.sel = null;
    renderPageDots();
    render();
    updateProps();
}
function addPage() {
    pushUndo();
    S._pages.push([]);
    switchPage(S._pages.length - 1, true);
    showToast("Page added", "success");
}
function deletePage() {
    if (S._pages.length <= 1) { showToast("Cannot delete last page", "error"); return; }
    pushUndo();
    S._pages.splice(S._currentPage, 1);
    if (S._currentPage >= S._pages.length) S._currentPage = S._pages.length - 1;
    S.E = JSON.parse(JSON.stringify(S._pages[S._currentPage]));
    S.sel = null;
    renderPageDots();
    render();
    updateProps();
    showToast("Page deleted", "success");
}
function renderPageDots() {
    var c = $("pg-dots");
    if (!c) return;
    c.innerHTML = "";
    for (var i = 0; i < S._pages.length; i++) {
        var dot = document.createElement("span");
        dot.className = "pg-dot" + (i === S._currentPage ? " active" : "");
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
    if (S._sn > 0) {
        var gs = S._sn * S._sc;
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

// ── Exports ──
window.StampAlbum.$ = $;
window.StampAlbum.mm = mm;
window.StampAlbum.px = px;
window.StampAlbum.clamp = clamp;
window.StampAlbum.fontCSS = fontCSS;
window.StampAlbum.showToast = showToast;
window.StampAlbum.SYSTEM_FONTS = SYSTEM_FONTS;
window.StampAlbum.updateTitle = updateTitle;
window.StampAlbum.switchPage = switchPage;
window.StampAlbum.addPage = addPage;
window.StampAlbum.deletePage = deletePage;
window.StampAlbum.renderPageDots = renderPageDots;
window.StampAlbum.updateGrid = updateGrid;
window.StampAlbum.populateFonts = populateFonts;

})();
