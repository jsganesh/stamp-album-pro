"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, mm = S.mm, px = S.px, showToast = S.showToast;
var render = S.render;

// ── Escape user strings for DSL embedding ──
function escapeDSL(s) {
    return String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

// ── DSL round-trip ──
function buildDSL() {
    var lines = [
        'ALBUM_TITLE("' + (S._currentFile ? S._currentFile.replace(/\.(slbum|txt)$/, "") : "") + '")',
        "ALBUM_PAGES_SIZE(" + mm(S._pw) + " " + mm(S._ph) + ")",
        "ALBUM_PAGES_MARGINS(15 15 15 15)",
        "PAGE_START"
    ];

    if (S._colMode > 1) {
        lines.push("PAGE_COLUMN_START(" + S._colMode + " " + S._colGap.toFixed(1) + ")");
    }

    S.E.forEach(function(el) {
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

    if (S._colMode > 1) {
        lines.push("PAGE_COLUMN_STOP");
    }

    for (var i = 1; i < S._pages.length; i++) {
        var pgEls = S._pages[i];
        if (pgEls && pgEls.length > 0) {
            lines.push("PAGE_START");
            if (S._colMode > 1) {
                lines.push("PAGE_COLUMN_START(" + S._colMode + " " + S._colGap.toFixed(1) + ")");
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
            if (S._colMode > 1) {
                lines.push("PAGE_COLUMN_STOP");
            }
        }
    }
    return lines.join("\n");
}

function parseDSL(dsl) {
    S.E = [];
    var lines = dsl.split("\n");
    S._pages = [[]];
    S._currentPage = 0;
    var _rowX = 0, _rowY = 12, _rowSpacing = 6, _pageMargin = 15;
    for (var i = 0; i < lines.length; i++) {
        var t = lines[i].trim();
        if (!t || t.charAt(0) === "#") continue;
        var mSize = t.match(/^ALBUM_PAGES_SIZE\(\s*([\d.]+)\s+([\d.]+)\)/);
        if (mSize) {
            S._pw = px(parseFloat(mSize[1]));
            S._ph = px(parseFloat(mSize[2]));
            $("pg-size").value = "a4";
            continue;
        }
        var mMargin = t.match(/^ALBUM_PAGES_MARGINS\(\s*([\d.]+)\s/);
        if (mMargin) {
            _pageMargin = parseFloat(mMargin[1]);
            continue;
        }
        if (t.match(/^PAGE_START/)) {
            if (S.E.length > 0) {
                S._pages[S._currentPage] = JSON.parse(JSON.stringify(S.E));
                S.E = [];
            }
            S._pages.push([]);
            S._currentPage = S._pages.length - 1;
            _rowX = _pageMargin;
            _rowY = 12;
            continue;
        }
        var mColStart = t.match(/^PAGE_COLUMN_START\(\s*(\d+)(?:\s+([\d.]+))?\)/);
        if (mColStart) {
            S._colMode = parseInt(mColStart[1]) || 1;
            S._colGap = mColStart[2] ? parseFloat(mColStart[2]) : 10.0;
            $("col-mode").value = S._colMode;
            $("col-gap").value = S._colGap;
            continue;
        }
        if (t.match(/^PAGE_COLUMN_NEXT/)) { continue; }
        if (t.match(/^PAGE_COLUMN_STOP/)) {
            S._colMode = 1;
            S._colGap = 10.0;
            $("col-mode").value = 1;
            $("col-gap").value = 10.0;
            continue;
        }
        var mVspace = t.match(/^PAGE_VSPACE\(\s*([\d.]+)\)/);
        if (mVspace) {
            _rowY += parseFloat(mVspace[1]);
            continue;
        }
        var mRow = t.match(/^ROW_START_FS\(\s*"([^"]*)"\s+(\d+)\s+([\d.]+)\s+([\d.]+)\)/);
        if (mRow) {
            _rowX = _pageMargin;
            _rowSpacing = parseFloat(mRow[4]);
            continue;
        }
        var m = t.match(/^(STAMP_ADD_AT|STAMP_ADD_IMG)\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"\s+"([^"]*)"/);
        if (m) {
            var isImg = m[1] === "STAMP_ADD_IMG";
            S.E.push({ id: "el" + (S.nid++), t: isImg ? "image" : "stamp", s: m[7] || "rectangle", x: px(parseFloat(m[2])), y: px(parseFloat(m[3])), w: px(parseFloat(m[4])), h: px(parseFloat(m[5])), lbl: m[6] || "", bdr: "solid", bdrC: "#666", bdrW: 1, fill: "#fff", fillA: 100, img: isImg ? m[6] : "", font: "HN", fs: 12 });
            continue;
        }
        var mRowStamp = t.match(/^STAMP_ADD\(\s*([\d.]+)\s+([\d.]+)\s+"([^"]*)"(?:\s+"([^"]*)")?(?:\s+"([^"]*)")?\)/);
        if (mRowStamp) {
            S.E.push({ id: "el" + (S.nid++), t: "stamp", s: "rectangle", x: px(_rowX), y: px(_rowY), w: px(parseFloat(mRowStamp[1])), h: px(parseFloat(mRowStamp[2])), lbl: mRowStamp[3] || "", bdr: "solid", bdrC: "#666", bdrW: 1, fill: "#fff", fillA: 100, img: "", font: "HN", fs: 12 });
            _rowX += parseFloat(mRowStamp[1]) + _rowSpacing;
            continue;
        }
        var m2 = t.match(/^(PAGE_TEXT|PAGE_TEXT_CENTRE|PAGE_TEXT_CENTER|PAGE_TEXT_RIGHT)\(\s*"([^"]*)"\s+(\d+)\s+"([^"]*)"\)/);
        if (m2) {
            var align = m2[1] === "PAGE_TEXT_CENTRE" || m2[1] === "PAGE_TEXT_CENTER" ? "center" : m2[1] === "PAGE_TEXT_RIGHT" ? "right" : "left";
            S.E.push({ id: "el" + (S.nid++), t: "text", s: "text", x: 10, y: _rowY > 12 ? _rowY + 2 : 10, w: 100, h: 20, lbl: m2[4] || "Text", font: m2[2] || "HN", fs: parseFloat(m2[3]) || 12, align: align, bdr: "none", fill: "transparent", fillA: 0 });
            _rowY += 8;
        }
    }
    if (S.E.length > 0 || S._pages.length === 0) {
        S._pages[S._currentPage] = JSON.parse(JSON.stringify(S.E));
    }
    while (S._pages.length > 1 && S._pages[S._pages.length - 1].length === 0) {
        S._pages.pop();
    }
    if (S._currentPage >= S._pages.length) S._currentPage = S._pages.length - 1;
    S.E = JSON.parse(JSON.stringify(S._pages[S._currentPage]));
    S.sel = null;
    S.renderPageDots();
    render();
    S.updateProps();
    S.updateGrid();
    S.updateTitle();
}

// ── Exports ──
S.escapeDSL = escapeDSL;
S.buildDSL = buildDSL;
S.parseDSL = parseDSL;

})();
