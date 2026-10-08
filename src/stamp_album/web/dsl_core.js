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
    // The header is written even for an empty album, so a new landscape or
    // non-A4 album keeps its page size before anything is placed on it.
    var title = state.currentFile ? state.currentFile.replace(/\.(slbum|txt)$/, "") : "";
    lines.push('ALBUM_TITLE("' + title + '")');
    lines.push("ALBUM_PAGES_SIZE(" + (state.pw || 210) + " " + (state.ph || 297) + ")");
    lines.push("ALBUM_PAGES_MARGINS(15 15 15 15)");

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
        // The editor keeps one column setting for the album, which buildDSL writes
        // around each page; STOP ends that block but must not clear the setting,
        // or every album with columns loses them on its next save.
        if (t.match(/^PAGE_COLUMN_STOP/)) { continue; }

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

// ── Page sizes (mm) ──
var PAPER_MM = { a4: [210, 297], a5: [148, 210], a3: [297, 420], letter: [215.9, 279.4], legal: [215.9, 355.6] };
// Up to v0.2.0 the editor treated PDF points as pixels at 2.5 px/mm, so albums saved
// from it carry (points / 2.5) instead of millimetres.
var LEGACY_PAGE_MM = { a4: [238.0, 336.8], a5: [168.0, 238.0], a3: [336.8, 476.4], letter: [244.8, 316.8], legal: [244.8, 403.6] };
var PAGE_TOL_MM = 0.5;

function sizeNear(w, h, size) {
    return Math.abs(w - size[0]) <= PAGE_TOL_MM && Math.abs(h - size[1]) <= PAGE_TOL_MM;
}

// Map a page size read from a file onto a real paper size.
// Returns { name, pw, ph, migrated, landscape }; name is a paper key for portrait pages, else null.
function normalizePageSize(pw, ph) {
    var groups = [{ table: PAPER_MM, migrated: false }, { table: LEGACY_PAGE_MM, migrated: true }];
    for (var g = 0; g < groups.length; g++) {
        var names = Object.keys(groups[g].table);
        for (var i = 0; i < names.length; i++) {
            var name = names[i], size = groups[g].table[name], paper = PAPER_MM[name];
            if (sizeNear(pw, ph, size)) {
                return { name: name, pw: paper[0], ph: paper[1], migrated: groups[g].migrated, landscape: false };
            }
            if (sizeNear(pw, ph, [size[1], size[0]])) {
                return { name: null, pw: paper[1], ph: paper[0], migrated: groups[g].migrated, landscape: true };
            }
        }
    }
    return { name: null, pw: pw, ph: ph, migrated: false, landscape: false };
}

// Count elements (in mm) that extend past a width x height page.
function countOutside(pages, width, height) {
    var n = 0;
    for (var pi = 0; pi < pages.length; pi++) {
        for (var ei = 0; ei < pages[pi].length; ei++) {
            var el = pages[pi][ei];
            if (el.x + el.w > width + 0.5 || el.y + el.h > height + 0.5) n++;
        }
    }
    return n;
}

// Name a page size for people: "A4 · Landscape", or "200 × 150 mm" for a custom size.
var PAPER_LABEL = { a4: "A4", a5: "A5", a3: "A3", letter: "Letter", legal: "Legal" };
function describePageSize(pw, ph) {
    var names = Object.keys(PAPER_MM);
    for (var i = 0; i < names.length; i++) {
        var size = PAPER_MM[names[i]];
        if (sizeNear(pw, ph, size)) return { name: names[i], landscape: false, label: PAPER_LABEL[names[i]] + " · Portrait" };
        if (sizeNear(pw, ph, [size[1], size[0]])) return { name: names[i], landscape: true, label: PAPER_LABEL[names[i]] + " · Landscape" };
    }
    var r = function(v) { return Math.round(v * 10) / 10; };
    return { name: null, landscape: pw > ph, label: r(pw) + " × " + r(ph) + " mm" };
}

// Fit one axis of one page's elements inside [0, dim]. Sizes never change.
// The page's elements move as a group so their arrangement is kept: if the
// group fits inside the margin it is shifted, otherwise the gaps between
// elements are narrowed in proportion. Returns the new start positions.
function _fitAxis(els, pos, size, dim, margin) {
    var starts = els.map(function(el) { return el[pos]; });
    var overflow = els.some(function(el) { return el[pos] < -1e-6 || el[pos] + el[size] > dim + 1e-6; });
    if (!overflow) return starts;
    var bmin = Math.min.apply(null, starts);
    var bmax = Math.max.apply(null, els.map(function(el) { return el[pos] + el[size]; }));
    var biggest = Math.max.apply(null, els.map(function(el) { return el[size]; }));
    var end = dim - margin, top = Math.max(0, Math.min(bmin, margin));
    if (end - top < biggest) { top = 0; end = dim; }
    if (bmax - bmin <= end - top) {
        // Shift the whole group just enough to bring it inside the margin.
        var shift = bmax > end ? end - bmax : 0;
        if (bmin + shift < top) shift = top - bmin;
        return starts.map(function(p) { return p + shift; });
    }
    // Too tall/wide to shift: keep the first element where it is (or at the
    // margin) and narrow the gaps so the furthest element ends at the margin.
    var anchor = Math.max(0, Math.min(bmin, end - biggest));
    var k = 1;
    els.forEach(function(el) {
        var span = el[pos] - bmin;
        if (span > 1e-6) k = Math.min(k, Math.max(0, (end - anchor - el[size]) / span));
    });
    return els.map(function(el) {
        if (el[size] > dim) return 0;  // bigger than the page: pin to the edge
        var p = anchor + (el[pos] - bmin) * k;
        return Math.min(Math.max(p, 0), Math.max(0, dim - el[size]));
    });
}

function _overlaps(a, b) {
    return a.x < b.x + b.w - 1e-6 && b.x < a.x + a.w - 1e-6 && a.y < b.y + b.h - 1e-6 && b.y < a.y + a.h - 1e-6;
}

// Move elements that would fall outside a width x height page back inside it.
// Units are whatever the elements use (margin in the same units). Element
// sizes are never changed, because stamp mounts must match the real stamps.
// opts.dryRun counts without changing anything.
// Returns { moved, pages, tooBig, overlaps }.
function fitToPage(pages, width, height, margin, opts) {
    opts = opts || {};
    var res = { moved: 0, pages: 0, tooBig: 0, overlaps: 0 };
    var round = function(v) { return Math.round(v * 100) / 100; };
    for (var pi = 0; pi < pages.length; pi++) {
        var els = pages[pi] || [];
        if (!els.length) continue;
        var xs = _fitAxis(els, "x", "w", width, margin || 0);
        var ys = _fitAxis(els, "y", "h", height, margin || 0);
        var movedHere = 0, after = [];
        for (var ei = 0; ei < els.length; ei++) {
            var el = els[ei], nx = round(xs[ei]), ny = round(ys[ei]);
            if (el.w > width + 1e-6 || el.h > height + 1e-6) res.tooBig++;
            if (Math.abs(nx - el.x) > 1e-6 || Math.abs(ny - el.y) > 1e-6) movedHere++;
            after.push({ x: nx, y: ny, w: el.w, h: el.h, before: el });
        }
        if (!movedHere) continue;
        res.moved += movedHere;
        res.pages++;
        // Count overlaps the move created (not ones the page already had).
        for (var a = 0; a < after.length; a++) {
            for (var b = a + 1; b < after.length; b++) {
                if (_overlaps(after[a], after[b]) && !_overlaps(after[a].before, after[b].before)) res.overlaps++;
            }
        }
        if (!opts.dryRun) {
            after.forEach(function(n) { n.before.x = n.x; n.before.y = n.y; });
        }
    }
    return res;
}

// ── Exports ──
var EXPORTS = { escapeDSL: escapeDSL, serializeEl: serializeEl, buildDSL: buildDSL, parseDSL: parseDSL, normalizePageSize: normalizePageSize, countOutside: countOutside,
                describePageSize: describePageSize, fitToPage: fitToPage, PAPER_MM: PAPER_MM };
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EXPORTS;
}
if (typeof window !== 'undefined') {
    window.StampAlbumDSL = EXPORTS;
}

})();
