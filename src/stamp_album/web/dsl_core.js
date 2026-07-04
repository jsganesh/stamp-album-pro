"use strict";
(function() {

// ── DSL Core — pure functions, no DOM/global dependencies ──
// All element position/size values are in mm.

function escapeDSL(s) {
    return String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

function serializeEl(el) {
    if (el.t === "image") {
        return 'STAMP_ADD_IMG(' + el.x.toFixed(1) + ' ' + el.y.toFixed(1) + ' ' + el.w.toFixed(1) + ' ' + el.h.toFixed(1) + ' "' + (el.img || "") + '" "' + (el.lbl || "") + '" "" "")';
    } else if (el.t === "freehand") {
        return 'STAMP_ADD_AT(' + el.x.toFixed(1) + ' ' + el.y.toFixed(1) + ' ' + el.w.toFixed(1) + ' ' + el.h.toFixed(1) + ' "' + (el.lbl || "") + '" "freehand" "" "" ' + (el.s || "freehand") + ' "' + (el.bdr || "solid") + '" "' + (el.bdrC || "#000") + '" ' + (el.bdrW || 0.5) + ' "' + (el.fill || "#FEFEFE") + '" ' + (el.fillA != null ? el.fillA : 100) + ')';
    } else if (el.t === "text") {
        return 'PAGE_TEXT_AT(' + el.x.toFixed(1) + ' ' + el.y.toFixed(1) + ' ' + el.w.toFixed(1) + ' ' + el.h.toFixed(1) + ' "' + (el.font || "HN") + '" ' + (el.fs || 12) + ' "' + (el.lbl || "Text") + '" "' + (el.align || "left") + '")';
    } else {
        var shape = el.s || "rectangle";
        if (shape === "rectangle" || shape === "rect") {
            // Short format — no extended fields, so album default colors are used
            return 'STAMP_ADD_AT(' + el.x.toFixed(1) + ' ' + el.y.toFixed(1) + ' ' + el.w.toFixed(1) + ' ' + el.h.toFixed(1) + ' "' + (el.lbl || "") + '" "" "" "")';
        }
        return 'STAMP_ADD_AT(' + el.x.toFixed(1) + ' ' + el.y.toFixed(1) + ' ' + el.w.toFixed(1) + ' ' + el.h.toFixed(1) + ' "' + (el.lbl || "") + '" "" "" "" ' + shape + ' "' + (el.bdr || "solid") + '" "' + (el.bdrC || "#000") + '" ' + (el.bdrW || 0.5) + ' "' + (el.fill || "#FEFEFE") + '" ' + (el.fillA != null ? el.fillA : 100) + ')';
    }
}

function buildDSL(state) {
    // state = { pages: [[el,...],...], pw, ph, pageBorder, pageBorderC, colMode, colGap, currentFile }
    state = state || {};
    var pages = state.pages || [];
    var lines = [];
    var totalEls = 0;
    for (var pi = 0; pi < pages.length; pi++) {
        totalEls += (pages[pi] || []).length;
    }
    var hasBorder = state.pageBorder && state.pageBorder !== "none";
    if (totalEls === 0 && !hasBorder) return "";

    if (hasBorder) {
        var outer = 0.5, inner1 = 0, inner2 = 0, spacing = 1.0;
        if (state.pageBorder === "double" || state.pageBorder === "classic" ||
            state.pageBorder === "victorian" || state.pageBorder === "artdeco" ||
            state.pageBorder === "laurel" || state.pageBorder === "gothic" ||
            state.pageBorder === "filigree") {
            inner1 = 0.3;
        }
        lines.push("ALBUM_PAGES_BORDER(" + outer + " " + inner1 + " " + inner2 + " " + spacing + ")");
        if (state.pageBorderC) {
            lines.push('COLOUR_ALBUM_BORDER("' + state.pageBorderC + '")');
        }
    }
    if (totalEls > 0) {
        var title = state.currentFile ? state.currentFile.replace(/\.(slbum|txt)$/, "") : "";
        lines.push('ALBUM_TITLE("' + title + '")');
        lines.push("ALBUM_PAGES_SIZE(" + state.pw + " " + state.ph + ")");
        lines.push("ALBUM_PAGES_MARGINS(15 15 15 15)");
    }

    for (var pi = 0; pi < pages.length; pi++) {
        var els = pages[pi];
        if (!els || els.length === 0) continue;
        if (lines.length > 0) lines.push("PAGE_START");
        if (state.colMode > 1) {
            lines.push("PAGE_COLUMN_START(" + state.colMode + " " + (state.colGap || 10).toFixed(1) + ")");
        }
        for (var ei = 0; ei < els.length; ei++) {
            lines.push(serializeEl(els[ei]));
        }
        if (state.colMode > 1) {
            lines.push("PAGE_COLUMN_STOP");
        }
    }
    return lines.join("\n");
}

function parseDSL(dsl) {
    var state = {
        pages: [[]],
        currentPage: 0,
        pw: 210, ph: 297,
        pageBorder: null,
        pageBorderC: null,
        colMode: 1,
        colGap: 10.0,
        currentFile: ""
    };
    var _rowX = 0, _rowY = 12, _rowSpacing = 6, _pageMargin = 15;
    var currentElements = [];
    var nid = 0;

    var lines = dsl.split("\n");
    for (var i = 0; i < lines.length; i++) {
        var t = lines[i].trim();
        if (!t || t.charAt(0) === "#") continue;

        var mSize = t.match(/^ALBUM_PAGES_SIZE\(\s*([\d.]+)\s+([\d.]+)\)/);
        if (mSize) {
            state.pw = parseFloat(mSize[1]);
            state.ph = parseFloat(mSize[2]);
            continue;
        }

        var mMargin = t.match(/^ALBUM_PAGES_MARGINS\(\s*([\d.]+)\s/);
        if (mMargin) {
            _pageMargin = parseFloat(mMargin[1]);
            continue;
        }

        var mBorder = t.match(/^ALBUM_PAGES_BORDER\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\)/);
        if (mBorder) {
            state.pageBorder = parseFloat(mBorder[2]) > 0 ? "double" : "solid";
            continue;
        }

        var mBorderColor = t.match(/^COLOUR_ALBUM_BORDER\(\s*"#?([^"]+)"\s*\)|^COLOR_ALBUM_BORDER\(\s*"#?([^"]+)"\s*\)/);
        if (mBorderColor) {
            state.pageBorderC = "#" + (mBorderColor[1] || mBorderColor[2]);
            continue;
        }

        if (t.match(/^PAGE_START/)) {
            if (currentElements.length > 0) {
                state.pages[state.currentPage] = currentElements;
                currentElements = [];
            }
            state.pages.push([]);
            state.currentPage = state.pages.length - 1;
            _rowX = _pageMargin;
            _rowY = 12;
            continue;
        }

        var mColStart = t.match(/^PAGE_COLUMN_START\(\s*(\d+)(?:\s+([\d.]+))?\)/);
        if (mColStart) {
            state.colMode = parseInt(mColStart[1]) || 1;
            state.colGap = mColStart[2] ? parseFloat(mColStart[2]) : 10.0;
            continue;
        }

        if (t.match(/^PAGE_COLUMN_NEXT/)) { continue; }
        if (t.match(/^PAGE_COLUMN_STOP/)) {
            state.colMode = 1;
            state.colGap = 10.0;
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

        var mImg = t.match(/^STAMP_ADD_IMG\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"\s+"([^"]*)"\s+"([^"]*)"\s+"([^"]*)"\)/);
        if (mImg) {
            currentElements.push({ id: "el" + (nid++), t: "image", s: "rectangle", x: parseFloat(mImg[1]), y: parseFloat(mImg[2]), w: parseFloat(mImg[3]), h: parseFloat(mImg[4]), lbl: mImg[6] || "", bdr: "none", bdrC: "transparent", bdrW: 0, fill: "transparent", fillA: 0, img: mImg[5] || "", font: "HN", fs: 12 });
            continue;
        }

        var mAt = t.match(/^STAMP_ADD_AT\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"\s+"([^"]*)"\s+"([^"]*)"\s+"([^"]*)"(.*)\)/);
        if (mAt) {
            var suffix = mAt[9].trim();
            var ext = suffix.match(/^(\w+)\s+"([^"]*)"\s+"([^"]*)"\s+([\d.]+)\s+"([^"]*)"\s+([\d.]+)$/);
            var shape, bdr, bdrC, bdrW, fill, fillA;
            if (ext) {
                shape = ext[1];
                bdr = ext[2];
                bdrC = ext[3];
                bdrW = parseFloat(ext[4]);
                fill = ext[5];
                fillA = parseFloat(ext[6]);
            } else if (suffix) {
                shape = suffix;
                bdr = mAt[7] || "solid";
                bdrC = "#000";
                bdrW = 0.5;
                fill = "#FEFEFE";
                fillA = 100;
            } else {
                shape = mAt[6] || "rectangle";
                bdr = mAt[7] || "solid";
                bdrC = "#000";
                bdrW = 0.5;
                fill = mAt[8] || "#FEFEFE";
                fillA = 100;
            }
            currentElements.push({ id: "el" + (nid++), t: "stamp", s: shape, x: parseFloat(mAt[1]), y: parseFloat(mAt[2]), w: parseFloat(mAt[3]), h: parseFloat(mAt[4]), lbl: mAt[5] || "", bdr: bdr, bdrC: bdrC, bdrW: bdrW, fill: fill, fillA: fillA, img: "", font: "HN", fs: 12 });
            continue;
        }

        var mRowStamp = t.match(/^STAMP_ADD\(\s*([\d.]+)\s+([\d.]+)\s+"([^"]*)"(?:\s+"([^"]*)")?(?:\s+"([^"]*)")?\)/);
        if (mRowStamp) {
            currentElements.push({ id: "el" + (nid++), t: "stamp", s: "rectangle", x: _rowX, y: _rowY, w: parseFloat(mRowStamp[1]), h: parseFloat(mRowStamp[2]), lbl: mRowStamp[3] || "", bdr: "solid", bdrC: "#666", bdrW: 1, fill: "#fff", fillA: 100, img: "", font: "HN", fs: 12 });
            _rowX += parseFloat(mRowStamp[1]) + _rowSpacing;
            continue;
        }

        var m2a = t.match(/^PAGE_TEXT_AT\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"\s+(\d+)\s+"([^"]*)"\s+"([^"]*)"\)/);
        if (m2a) {
            currentElements.push({ id: "el" + (nid++), t: "text", s: "text", x: parseFloat(m2a[1]), y: parseFloat(m2a[2]), w: parseFloat(m2a[3]), h: parseFloat(m2a[4]), lbl: m2a[7] || "Text", font: m2a[5] || "HN", fs: parseFloat(m2a[6]) || 12, align: m2a[8] === "center" ? "center" : m2a[8] === "right" ? "right" : "left", bdr: "none", fill: "transparent", fillA: 0 });
            continue;
        }

        var m2 = t.match(/^(PAGE_TEXT|PAGE_TEXT_CENTRE|PAGE_TEXT_CENTER|PAGE_TEXT_RIGHT)\(\s*"([^"]*)"\s+(\d+)\s+"([^"]*)"\)/);
        if (m2) {
            var align = m2[1] === "PAGE_TEXT_CENTRE" || m2[1] === "PAGE_TEXT_CENTER" ? "center" : m2[1] === "PAGE_TEXT_RIGHT" ? "right" : "left";
            currentElements.push({ id: "el" + (nid++), t: "text", s: "text", x: 10, y: _rowY > 12 ? _rowY + 2 : 10, w: 100, h: 20, lbl: m2[4] || "Text", font: m2[2] || "HN", fs: parseFloat(m2[3]) || 12, align: align, bdr: "none", fill: "transparent", fillA: 0 });
            _rowY += 8;
        }
    }

    if (currentElements.length > 0 || state.pages.length === 0) {
        state.pages[state.currentPage] = currentElements;
    }
    while (state.pages.length > 1 && state.pages[state.pages.length - 1].length === 0) {
        state.pages.pop();
    }
    if (state.currentPage >= state.pages.length) {
        state.currentPage = state.pages.length - 1;
    }

    return state;
}

// ── Exports ──
var EXPORTS = { escapeDSL: escapeDSL, serializeEl: serializeEl, buildDSL: buildDSL, parseDSL: parseDSL };
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EXPORTS;
}
if (typeof window !== 'undefined') {
    window.StampAlbumDSL = EXPORTS;
}

})();
