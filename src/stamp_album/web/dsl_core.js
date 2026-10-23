"use strict";
(function() {

// ── DSL Core — pure functions, no DOM/global dependencies ──
// All element position/size values are in mm.

function escapeDSL(s) {
    return String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
}
// The reverse of escapeDSL, in one pass so "\\n" stays a backslash and an n.
function unescapeDSL(s) {
    return String(s).replace(/\\(.)/g, function(_, c) { return c === "n" ? "\n" : c; });
}
// t.match(re) with every quoted field unescaped (the patterns accept \" and \\ inside quotes).
function matchDSL(t, re) {
    var m = t.match(re);
    if (m) for (var i = 1; i < m.length; i++) if (typeof m[i] === "string" && m[i].indexOf("\\") !== -1) m[i] = unescapeDSL(m[i]);
    return m;
}

// ── Album themes ──
// A theme colours the page border and headings marked as headings; everything else is black.
// Keep in step with stamp_album/core/themes.py.
var THEMES = {
    exhibition: { name: "Exhibition", color: "#000000" },
    green:      { name: "Green",      color: "#2E5E3A" },
    maroon:     { name: "Maroon",     color: "#7A1F2B" },
    navy:       { name: "Navy",       color: "#1F3A5F" },
    brown:      { name: "Brown",      color: "#5C4033" }
};
// The colour a state's theme gives the page border and headings. "custom" is an older
// album's own border colour, kept until a theme is chosen.
function themeColor(state) {
    state = state || {};
    if (state.theme === "custom") return state.pageBorderC || THEMES.exhibition.color;
    return (THEMES[state.theme] || THEMES.exhibition).color;
}

// ── Stamp frames ──
// Stamps are framed in black, as exhibition pages are: no frame, thin, medium or double.
var FRAMES = {
    none:   { bdr: "none",   bdrW: 0 },
    thin:   { bdr: "solid",  bdrW: 0.5 },
    medium: { bdr: "solid",  bdrW: 1 },
    double: { bdr: "double", bdrW: 1 }
};
var FRAME_COLOR = "#000000";
function frameOf(el) {
    if (!el || el.bdr === "none" || (el.bdr !== "double" && !(el.bdrW > 0))) return "none";
    if (el.bdr === "double") return "double";
    return el.bdrW > 0.75 ? "medium" : "thin";  // dashed and dotted frames from older albums too
}
function applyFrame(el, frame) {
    var f = FRAMES[frame] || FRAMES.thin;
    el.bdr = f.bdr;
    el.bdrW = f.bdrW;
    el.bdrC = FRAME_COLOR;
    return el;
}
// The frame is drawn outside the stamp: a stamp's w and h are its own size, as in the catalogue.
// Clear space all round (the album's mount overhang plus its gap to the frame), then the line
// or lines (points, inside out). Free shapes have no clearance: their outline is the frame.
// Keep in step with engines/frames.py.
var FRAME_CLEARANCE_MM = 1;  // an album from before mounts: 0 + 1 mm
var MOUNT_OVERHANG_CHOICES = [0, 1, 1.5, 2, 2.5, 3], MOUNT_GAP_CHOICES = [1, 1.5, 2, 2.5, 3];
var NEW_ALBUM_MOUNT = { overhang: 1.5, gap: 1 }, OLD_ALBUM_MOUNT = { overhang: 0, gap: 1 };
var MOUNT_MAX_MM = 10;
// The open album's mounts; until an album sets them, as albums were before mounts (0 + 1 mm).
var _mount = { overhang: OLD_ALBUM_MOUNT.overhang, gap: OLD_ALBUM_MOUNT.gap };
function validMount(o, g) {
    o = Number(o); g = Number(g);
    return isFinite(o) && isFinite(g) && o >= 0 && o <= MOUNT_MAX_MM && g > 0 && g <= MOUNT_MAX_MM;
}
function setMount(o, g) {
    if (!validMount(o, g)) return false;
    _mount = { overhang: Number(o), gap: Number(g) };
    return true;
}
function getMount() { return { overhang: _mount.overhang, gap: _mount.gap }; }

// ── Page border distance ──
// How far the page border sits from the paper's edge, in mm (ALBUM_BORDER_INSET). Printers can't
// print right up to the edge (often 10 to 13 mm at the top and bottom), so a border too close is
// cut off or the page gets shrunk to fit, shrinking every stamp box with it. New albums start at
// 13 mm; an album that doesn't say keeps 4.8 mm, as albums were drawn before.
// Keep in step with engines/page_border.py.
var BORDER_INSET_CHOICES = [4.8, 8, 10, 12, 13], NEW_ALBUM_BORDER_INSET = 13, OLD_ALBUM_BORDER_INSET = 4.8;
var BORDER_INSET_MAX_MM = 30;
var _borderInset = OLD_ALBUM_BORDER_INSET;
function validBorderInset(v) { v = Number(v); return isFinite(v) && v >= 0 && v <= BORDER_INSET_MAX_MM; }
function setBorderInset(v) {
    if (!validBorderInset(v)) return false;
    _borderInset = Number(v);
    return true;
}
function getBorderInset() { return _borderInset; }
var FRAME_LINES_PT = { none: [], thin: [0.5], medium: [1], double: [0.5, 0.5] };
var FRAME_DOUBLE_GAP_PT = 1;
var MM_PER_PT = 25.4 / 72;
function frameClearance(el) {
    return frameOf(el) === "none" || el.t === "freehand" ? 0 : _mount.overhang + _mount.gap;
}
// [{ offset, width }] in mm, inside out: offset runs from the stamp edge to the line's centre.
function frameLines(el) {
    if (!el || (el.t !== "stamp" && el.t !== "freehand")) return [];
    var out = [], edge = frameClearance(el);
    FRAME_LINES_PT[frameOf(el)].forEach(function(wPt, i) {
        if (i) edge += FRAME_DOUBLE_GAP_PT * MM_PER_PT;
        var w = wPt * MM_PER_PT;
        out.push({ offset: edge + w / 2, width: w });
        edge += w;
    });
    return out;
}
// Distance from the stamp edge to the frame's outer edge (mm); 0 with no frame.
function frameOutset(el) {
    var ls = frameLines(el), last = ls[ls.length - 1];
    return last ? last.offset + last.width / 2 : 0;
}
function frameBox(el, x, y, w, h) {
    var o = frameOutset(el);
    return { x: x - o, y: y - o, w: w + 2 * o, h: h + 2 * o };
}
// Stamp outlines on a 100 x 100 grid, as SHAPE_POLYGON_VIEWBOX in engines/borders.py.
var SHAPE_POLYGONS = {
    triangle: [[50, 0], [100, 100], [0, 100]],
    triangle_inverted: [[0, 0], [100, 0], [50, 100]],
    diamond: [[50, 0], [100, 50], [50, 100], [0, 50]],
    hexagon: [[25, 0], [75, 0], [100, 50], [75, 100], [25, 100], [0, 50]],
    octagon: [[30, 0], [70, 0], [100, 30], [100, 70], [70, 100], [30, 100], [0, 70], [0, 30]],
    pentagon: [[50, 0], [100, 38], [82, 100], [18, 100], [0, 38]]
};
// A convex polygon moved outward by d on every side, corners mitred.
function _offsetPolygon(pts, d) {
    if (!d) return pts.slice();
    var n = pts.length, cx = 0, cy = 0, edges = [], out = [];
    pts.forEach(function(p) { cx += p[0] / n; cy += p[1] / n; });
    for (var i = 0; i < n; i++) {
        var a = pts[i], b = pts[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1];
        var ln = Math.hypot(dx, dy) || 1, nx = dy / ln, ny = -dx / ln;
        if (nx * ((a[0] + b[0]) / 2 - cx) + ny * ((a[1] + b[1]) / 2 - cy) < 0) { nx = -nx; ny = -ny; }
        edges.push({ p: [a[0] + nx * d, a[1] + ny * d], v: [dx, dy] });
    }
    for (var j = 0; j < n; j++) {
        var e1 = edges[(j + n - 1) % n], e2 = edges[j];
        var den = e1.v[0] * e2.v[1] - e1.v[1] * e2.v[0];
        if (Math.abs(den) < 1e-12) { out.push(e2.p); continue; }
        var t = ((e2.p[0] - e1.p[0]) * e2.v[1] - (e2.p[1] - e1.p[1]) * e2.v[0]) / den;
        out.push([e1.p[0] + e1.v[0] * t, e1.p[1] + e1.v[1] * t]);
    }
    return out;
}
// The stamp's outline moved outward by d: { kind: "rect", x, y, w, h } |
// { kind: "ellipse", cx, cy, rx, ry } | { kind: "polygon", points: [[x, y], ...] }.
function shapeOutline(shape, x, y, w, h, d) {
    d = d || 0;
    if (shape === "oval") return { kind: "ellipse", cx: x + w / 2, cy: y + h / 2, rx: w / 2 + d, ry: h / 2 + d };
    var poly = SHAPE_POLYGONS[shape];
    if (poly) {
        var pts = poly.map(function(p) { return [x + p[0] / 100 * w, y + p[1] / 100 * h]; });
        return { kind: "polygon", points: _offsetPolygon(pts, d) };
    }
    return { kind: "rect", x: x - d, y: y - d, w: w + 2 * d, h: h + 2 * d };
}

// Older albums could colour, fill or dash a stamp's frame: open them with the nearest black frame, no fill.
function normalizeStamp(el) {
    if (el.t !== "stamp") return el;
    applyFrame(el, frameOf(el));
    el.fill = "#ffffff";
    el.fillA = 100;
    return el;
}

// Page border styles. The plain ones suit exhibition pages; the rest are for personal albums.
var PLAIN_BORDERS = ["none", "solid", "double"];

function serializeEl(el) {
    var E = escapeDSL;  // every text field is escaped, so quotes and backslashes survive a save
    if (el.t === "image") {
        return 'STAMP_ADD_IMG(' + el.x.toFixed(1) + ' ' + el.y.toFixed(1) + ' ' + el.w.toFixed(1) + ' ' + el.h.toFixed(1) + ' "' + E(el.img || "") + '" "' + E(el.lbl || "") + '" "' + E(el.cap || "") + '" "")';
    } else if (el.t === "freehand") {
        return 'STAMP_ADD_AT(' + el.x.toFixed(1) + ' ' + el.y.toFixed(1) + ' ' + el.w.toFixed(1) + ' ' + el.h.toFixed(1) + ' "' + E(el.lbl || "") + '" "freehand" "" "" ' + (el.s || "freehand") + ' "' + E(el.bdr || "solid") + '" "' + E(el.bdrC || "#000") + '" ' + (el.bdrW || 0.5) + ' "' + E(el.fill || "#FEFEFE") + '" ' + (el.fillA != null ? el.fillA : 100) + ')';
    } else if (el.t === "text") {
        var text = 'PAGE_TEXT_AT(' + el.x.toFixed(1) + ' ' + el.y.toFixed(1) + ' ' + el.w.toFixed(1) + ' ' + el.h.toFixed(1) + ' "' + E(el.font || "HN") + '" ' + (el.fs || 12) + ' "' + E(el.lbl || "Text") + '" "' + E(el.align || "left") + '")';
        // A heading mark is its own line, which older versions skip.
        if (el.role === "heading") text += '\nPAGE_TEXT_ROLE("heading")';
        // So is the part of the title and plan page the text is (exhibitPlanLayout).
        if (el.part && PLAN_PART_NAMES.indexOf(el.part) !== -1) text += '\nPAGE_TEXT_PART("' + el.part + '")';
        return text;
    } else {
        // Every stamp, rectangles included, is written in the extended format so its border
        // and fill are kept. The first catalogue field holds the catalogue number.
        var shape = el.s === "rect" ? "rectangle" : (el.s || "rectangle");
        var lines = ['STAMP_ADD_AT(' + el.x.toFixed(1) + ' ' + el.y.toFixed(1) + ' ' + el.w.toFixed(1) + ' ' + el.h.toFixed(1) + ' "' + E(el.lbl || "") + '" "' + E(el.cat || "") + '" "" "" ' + shape + ' "' + E(el.bdr || "solid") + '" "' + E(el.bdrC || "#000") + '" ' + (el.bdrW != null ? el.bdrW : 0.5) + ' "' + E(el.fill || "#FEFEFE") + '" ' + (el.fillA != null ? el.fillA : 100) + ')'];
        // Heading above the stamp (a command the Python parser and exports already read)
        if (el.hdg) lines.push('STAMP_HEADING("HN" 9 "' + E(el.hdg) + '")');
        // Denomination, condition, perforation. Older versions skip this line.
        if (el.denom || el.cond || el.perf) {
            lines.push('STAMP_DETAILS("' + E(el.denom || "") + '" "' + E(el.cond || "") + '" "' + E(el.perf || "") + '")');
        }
        return lines.join("\n");
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
        // The style by name, so Classic, Greek key and the others reopen as themselves
        lines.push('ALBUM_PAGES_BORDER_STYLE("' + state.pageBorder + '")');
        lines.push('COLOUR_ALBUM_BORDER("' + themeColor(state) + '")');
    }
    if (state.theme && state.theme !== "custom") lines.push('ALBUM_THEME("' + state.theme + '")');
    var mount = state.mount || getMount();
    lines.push("ALBUM_MOUNT(" + mount.overhang + " " + mount.gap + ")");
    lines.push("ALBUM_BORDER_INSET(" + (state.borderInset != null ? state.borderInset : getBorderInset()) + ")");
    if (state.captionHeading === "semibold") lines.push('CAPTION_HEADING("semibold")');  // bold is the default
    // The header is written even for an empty album, so a new landscape or
    // non-A4 album keeps its page size before anything is placed on it.
    var title = state.currentFile ? state.currentFile.replace(/\.(slbum|txt)$/, "") : "";
    lines.push('ALBUM_TITLE("' + escapeDSL(title) + '")');
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
        captionHeading: "bold",  // stamp caption headings: "bold" or "semibold"
        mount: { overhang: OLD_ALBUM_MOUNT.overhang, gap: OLD_ALBUM_MOUNT.gap },  // ALBUM_MOUNT, else as before
        borderInset: OLD_ALBUM_BORDER_INSET,  // ALBUM_BORDER_INSET, else 4.8 mm as before
        colMode: 1,
        colGap: 10.0,
        currentFile: ""
    };
    var _rowX = 0, _rowY = 12, _rowSpacing = 6, _pageMargin = 15;
    var currentElements = [];
    var nid = 0;
    var sawPageStart = false;
    var lastStamp = null;  // the stamp a STAMP_HEADING or STAMP_DETAILS line describes
    var lastText = null;   // the text a PAGE_TEXT_ROLE line marks

    var lines = dsl.split("\n");
    for (var i = 0; i < lines.length; i++) {
        var t = lines[i].trim();
        if (!t || t.charAt(0) === "#") continue;

        var mSize = matchDSL(t, /^ALBUM_PAGES_SIZE\(\s*([\d.]+)\s+([\d.]+)\)/);
        if (mSize) {
            state.pw = parseFloat(mSize[1]);
            state.ph = parseFloat(mSize[2]);
            continue;
        }

        var mMargin = matchDSL(t, /^ALBUM_PAGES_MARGINS\(\s*([\d.]+)\s/);
        if (mMargin) {
            _pageMargin = parseFloat(mMargin[1]);
            continue;
        }

        var mBorder = matchDSL(t, /^ALBUM_PAGES_BORDER\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\)/);
        if (mBorder) {
            state.pageBorder = parseFloat(mBorder[2]) > 0 ? "double" : "solid";
            continue;
        }

        var mBorderStyle = matchDSL(t, /^ALBUM_PAGES_BORDER_STYLE\(\s*"([\w-]+)"\s*\)/);
        if (mBorderStyle) {
            state.pageBorder = mBorderStyle[1];
            continue;
        }

        var mMount = matchDSL(t, /^ALBUM_MOUNT\(\s*([\d.]+)\s+([\d.]+)\s*\)/);
        if (mMount) {
            if (validMount(mMount[1], mMount[2])) state.mount = { overhang: Number(mMount[1]), gap: Number(mMount[2]) };
            continue;
        }
        var mInset = matchDSL(t, /^ALBUM_BORDER_INSET\(\s*([\d.]+)\s*\)/);
        if (mInset) {
            if (validBorderInset(mInset[1])) state.borderInset = Number(mInset[1]);
            continue;
        }
        var mHeading = matchDSL(t, /^CAPTION_HEADING\(\s*"(\w+)"\s*\)/);
        if (mHeading) {
            var hw = mHeading[1].toLowerCase();
            if (HEADING_WEIGHTS[hw]) state.captionHeading = hw;
            continue;
        }
        var mTheme = matchDSL(t, /^ALBUM_THEME\(\s*"(\w+)"\s*\)/);
        if (mTheme) {
            if (THEMES[mTheme[1]]) state.theme = mTheme[1];
            continue;
        }

        var mBorderColor = matchDSL(t, /^COLOUR_ALBUM_BORDER\(\s*"#?([^"]+)"\s*\)|^COLOR_ALBUM_BORDER\(\s*"#?([^"]+)"\s*\)/);
        if (mBorderColor) {
            state.pageBorderC = "#" + (mBorderColor[1] || mBorderColor[2]);
            continue;
        }

        if (matchDSL(t, /^PAGE_START/)) {
            if (currentElements.length > 0) {
                state.pages[state.currentPage] = currentElements;
                currentElements = [];
            }
            // The first PAGE_START fills the empty starting page; later ones add a page.
            if (sawPageStart || state.pages[state.currentPage].length > 0) {
                state.pages.push([]);
                state.currentPage = state.pages.length - 1;
            }
            sawPageStart = true;
            lastStamp = null;
            lastText = null;
            _rowX = _pageMargin;
            _rowY = 12;
            continue;
        }

        var mColStart = matchDSL(t, /^PAGE_COLUMN_START\(\s*(\d+)(?:\s+([\d.]+))?\)/);
        if (mColStart) {
            state.colMode = parseInt(mColStart[1]) || 1;
            state.colGap = mColStart[2] ? parseFloat(mColStart[2]) : 10.0;
            continue;
        }

        if (matchDSL(t, /^PAGE_COLUMN_NEXT/)) { continue; }
        // The editor keeps one column setting for the album, which buildDSL writes
        // around each page; STOP ends that block but must not clear the setting,
        // or every album with columns loses them on its next save.
        if (matchDSL(t, /^PAGE_COLUMN_STOP/)) { continue; }

        var mVspace = matchDSL(t, /^PAGE_VSPACE\(\s*([\d.]+)\)/);
        if (mVspace) {
            _rowY += parseFloat(mVspace[1]);
            continue;
        }

        var mRow = matchDSL(t, /^ROW_START_FS\(\s*"((?:[^"\\]|\\.)*)"\s+(\d+)\s+([\d.]+)\s+([\d.]+)\)/);
        if (mRow) {
            _rowX = _pageMargin;
            _rowSpacing = parseFloat(mRow[4]);
            continue;
        }

        var mImg = matchDSL(t, /^STAMP_ADD_IMG\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\)/);
        if (mImg) {
            currentElements.push({ id: "el" + (nid++), t: "image", s: "rectangle", x: parseFloat(mImg[1]), y: parseFloat(mImg[2]), w: parseFloat(mImg[3]), h: parseFloat(mImg[4]), lbl: mImg[6] || "", cap: mImg[7] || "", bdr: "none", bdrC: "transparent", bdrW: 0, fill: "transparent", fillA: 0, img: mImg[5] || "", font: "HN", fs: 12 });
            continue;
        }

        var mAt = matchDSL(t, /^STAMP_ADD_AT\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"(.*)\)/);
        if (mAt) {
            var suffix = mAt[9].trim();
            var ext = matchDSL(suffix, /^(\w+)\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\s+([\d.]+)\s+"((?:[^"\\]|\\.)*)"\s+([\d.]+)$/);
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
            lastStamp = { id: "el" + (nid++), t: "stamp", s: shape, x: parseFloat(mAt[1]), y: parseFloat(mAt[2]), w: parseFloat(mAt[3]), h: parseFloat(mAt[4]), lbl: mAt[5] || "", bdr: bdr, bdrC: bdrC, bdrW: bdrW, fill: fill, fillA: fillA, img: "", font: "HN", fs: 12 };
            // In the extended format the first catalogue field is the catalogue number
            // (free shapes use it for their marker).
            if (ext && shape !== "freehand" && mAt[6]) lastStamp.cat = mAt[6];
            currentElements.push(lastStamp);
            continue;
        }

        // Heading and details lines belong to the stamp just before them.
        var mHdg = matchDSL(t, /^STAMP_HEADING\(\s*"((?:[^"\\]|\\.)*)"\s+([\d.]+)\s+(?:"?\w+"?\s+)?"((?:[^"\\]|\\.)*)"\s*\)/);
        if (mHdg) {
            if (lastStamp) lastStamp.hdg = mHdg[3];
            continue;
        }
        var mDet = matchDSL(t, /^STAMP_DETAILS\(\s*"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\s*\)/);
        if (mDet) {
            if (lastStamp) {
                if (mDet[1]) lastStamp.denom = mDet[1];
                if (mDet[2]) lastStamp.cond = mDet[2];
                if (mDet[3]) lastStamp.perf = mDet[3];
            }
            continue;
        }

        var mRowStamp = matchDSL(t, /^STAMP_ADD\(\s*([\d.]+)\s+([\d.]+)\s+"((?:[^"\\]|\\.)*)"(?:\s+"((?:[^"\\]|\\.)*)")?(?:\s+"((?:[^"\\]|\\.)*)")?\)/);
        if (mRowStamp) {
            currentElements.push({ id: "el" + (nid++), t: "stamp", s: "rectangle", x: _rowX, y: _rowY, w: parseFloat(mRowStamp[1]), h: parseFloat(mRowStamp[2]), lbl: mRowStamp[3] || "", bdr: "solid", bdrC: "#666", bdrW: 1, fill: "#fff", fillA: 100, img: "", font: "HN", fs: 12 });
            _rowX += parseFloat(mRowStamp[1]) + _rowSpacing;
            continue;
        }

        var m2a = matchDSL(t, /^PAGE_TEXT_AT\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"((?:[^"\\]|\\.)*)"\s+([\d.]+)\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\)/);
        if (m2a) {
            lastText = { id: "el" + (nid++), t: "text", s: "text", x: parseFloat(m2a[1]), y: parseFloat(m2a[2]), w: parseFloat(m2a[3]), h: parseFloat(m2a[4]), lbl: m2a[7] || "Text", font: m2a[5] || "HN", fs: parseFloat(m2a[6]) || 12, align: m2a[8] === "center" ? "center" : m2a[8] === "right" ? "right" : "left", bdr: "none", fill: "transparent", fillA: 0 };
            currentElements.push(lastText);
            continue;
        }

        // A heading mark belongs to the text just before it.
        if (matchDSL(t, /^PAGE_TEXT_ROLE\(\s*"heading"\s*\)/)) {
            if (lastText) lastText.role = "heading";
            continue;
        }
        // So does the part of the title and plan page it is.
        var mPart = matchDSL(t, /^PAGE_TEXT_PART\(\s*"(\w+)"\s*\)/);
        if (mPart) {
            if (lastText && PLAN_PART_NAMES.indexOf(mPart[1]) !== -1) lastText.part = mPart[1];
            continue;
        }

        var m2 = matchDSL(t, /^(PAGE_TEXT|PAGE_TEXT_CENTRE|PAGE_TEXT_CENTER|PAGE_TEXT_RIGHT)\(\s*"((?:[^"\\]|\\.)*)"\s+([\d.]+)\s+"((?:[^"\\]|\\.)*)"\)/);
        if (m2) {
            var align = m2[1] === "PAGE_TEXT_CENTRE" || m2[1] === "PAGE_TEXT_CENTER" ? "center" : m2[1] === "PAGE_TEXT_RIGHT" ? "right" : "left";
            lastText = { id: "el" + (nid++), t: "text", s: "text", x: 10, y: _rowY > 12 ? _rowY + 2 : 10, w: 100, h: 20, lbl: m2[4] || "Text", font: m2[2] || "HN", fs: parseFloat(m2[3]) || 12, align: align, bdr: "none", fill: "transparent", fillA: 0 };
            currentElements.push(lastText);
            _rowY += 8;
        }
    }

    if (currentElements.length > 0 || state.pages.length === 0) {
        state.pages[state.currentPage] = currentElements;
    }
    while (state.pages.length > 1 && state.pages[state.pages.length - 1].length === 0) {
        state.pages.pop();
    }
    // An opened album starts on its first page.
    state.currentPage = 0;
    // Stamps get black frames and no fill.
    state.pages.forEach(function(p) { p.forEach(normalizeStamp); });
    // Theme: as saved; else an older album's own border colour ("custom"); else Exhibition.
    if (!state.theme) state.theme = state.pageBorderC ? "custom" : "exhibition";
    if (state.theme !== "custom") state.pageBorderC = THEMES[state.theme].color;

    return state;
}

// ── Page sizes (mm) ──
var PAPER_MM = { a4: [210, 297], a5: [148, 210], a3: [297, 420], letter: [215.9, 279.4], legal: [215.9, 355.6],
                 // FIP exhibit sheets (GREX 2026 Art. 6.1), width × height as listed: a frame holds 16 of the first
                 fip23: [230, 297], fip31: [310, 297], fip46: [460, 297] };
// Sheets used only as listed: no portrait or landscape
var FIXED_PAPERS = { fip23: true, fip31: true, fip46: true };
// How FIP sheets hang in an exhibition frame (GREX 2026 Art. 6.1): sheets to a row; a frame has 4 rows.
var FIP_FRAME_ROW = { fip23: 4, fip31: 3, fip46: 2 }, FIP_FRAME_ROWS = 4;
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
// Elements whose box sits past any edge of a width x height page (stamp boxes,
// not frames or captions, which have their own warnings). Half a unit of slack
// absorbs rounding. Returns { count, pages }.
function findOutside(pages, width, height) {
    var res = { count: 0, pages: 0 };
    for (var pi = 0; pi < pages.length; pi++) {
        var els = pages[pi] || [], here = 0;
        for (var ei = 0; ei < els.length; ei++) {
            var el = els[ei];
            if (el.x < -0.5 || el.y < -0.5 || el.x + el.w > width + 0.5 || el.y + el.h > height + 0.5) here++;
        }
        res.count += here;
        if (here) res.pages++;
    }
    return res;
}

// Name a page size for people: "A4 · Landscape", or "200 × 150 mm" for a custom size.
var PAPER_LABEL = { a4: "A4", a5: "A5", a3: "A3", letter: "Letter", legal: "Legal",
                    fip23: "FIP sheet 23 × 29.7 cm", fip31: "FIP sheet 31 × 29.7 cm", fip46: "FIP sheet 46 × 29.7 cm" };
function describePageSize(pw, ph) {
    var names = Object.keys(PAPER_MM);
    for (var i = 0; i < names.length; i++) {
        var size = PAPER_MM[names[i]];
        if (FIXED_PAPERS[names[i]]) {
            if (sizeNear(pw, ph, size)) return { name: names[i], landscape: false, fixed: true, label: PAPER_LABEL[names[i]] };
            continue;  // turned on its side it is just a custom size
        }
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

// ── Stamp captions ──
// One caption layout for every view. Keep in step with stamp_album/engines/caption_layout.py.
// Heading above the box (bold or semibold, as the album chooses, 9 pt); below it the description
// (8 pt), the details line (8 pt italic) and the catalogue number (8 pt italic). The nearest line box
// is GAP_MM from the frame's outer edge; lines are centred and wrapped to the frame's width;
// captions are black. Positions are mm from the page's top-left corner.
var CAPTION = { GAP_MM: 2, HEADING_PT: 9, CAPTION_PT: 8, LINE_HEIGHT: 1.3, FIRST_BASELINE: 1,
                MM_PER_PT: 25.4 / 72, COLOR: "#000000" };

// Every caption is set in the bundled Source Serif 4 Caption (web/fonts, SIL OFL), whatever the
// stamp's own font. Keep in step with stamp_album/engines/caption_fonts.py.
var CAPTION_FONTS = {
    FAMILY: "Source Serif 4 Caption",
    CapR:  { file: "SourceSerif4Caption-Regular.ttf",  weight: 400, style: "normal" },
    CapI:  { file: "SourceSerif4Caption-It.ttf",       weight: 400, style: "italic" },
    CapB:  { file: "SourceSerif4Caption-Bold.ttf",     weight: 700, style: "normal" },
    CapSB: { file: "SourceSerif4Caption-Semibold.ttf", weight: 600, style: "normal" }
};
var HEADING_WEIGHTS = { bold: "CapB", semibold: "CapSB" };  // the album's CAPTION_HEADING
function headingFont(weight) { return HEADING_WEIGHTS[String(weight || "").toLowerCase()] || HEADING_WEIGHTS.bold; }

// Advance widths from web/caption_metrics.js (generated from the TTFs by tools/caption_metrics.py).
var _captionAdv = null;
function _captionMetrics() {
    if (_captionAdv) return _captionAdv;
    var raw = (typeof window !== "undefined" && window.StampAlbumCaptionMetrics) ||
              (typeof require === "function" ? require("./caption_metrics.js") : null);
    if (!raw) throw new Error("caption_metrics.js is not loaded");
    _captionAdv = {};
    Object.keys(raw).forEach(function(fid) {
        var m = raw[fid], adv = {};
        m.runs.forEach(function(run) { for (var i = 1; i < run.length; i++) adv[run[0] + i - 1] = run[i]; });
        _captionAdv[fid] = { upm: m.upm, notdef: m.notdef, adv: adv };
    });
    return _captionAdv;
}

// Width in mm: the sum of the glyphs' advance widths, no kerning or ligatures (as the exports).
// A character the font lacks counts as its .notdef glyph.
function captionMeasure(text, fontId, sizePt) {
    var m = _captionMetrics()[fontId], units = 0;
    for (var ch of String(text)) {
        var a = m.adv[ch.codePointAt(0)];
        units += a === undefined ? m.notdef : a;
    }
    return units * sizePt / m.upm * CAPTION.MM_PER_PT;
}

// Greedy word wrap; honours newlines and breaks over-long words (as text_layout.wrap_lines).
function wrapLines(text, maxWidth, measure) {
    var out = [];
    String(text || "").split("\n").forEach(function(para) {
        if (!para.trim()) { out.push(""); return; }
        var line = "";
        para.split(" ").forEach(function(word) {
            var cand = line ? line + " " + word : word;
            if (measure(cand) <= maxWidth || !line) line = cand;
            else { out.push(line); line = word; }
            while (measure(line) > maxWidth && line.length > 1) {
                var cut = line.length - 1;
                while (cut > 1 && measure(line.slice(0, cut)) > maxWidth) cut--;
                out.push(line.slice(0, cut));
                line = line.slice(cut);
            }
        });
        out.push(line);
    });
    return out;
}

// The caption texts of an editor element, empty ones dropped.
// opts.headingWeight is the album's choice: "bold" (the default) or "semibold".
function captionParts(el, opts) {
    var above = [], below = [];
    var trim = function(v) { return String(v || "").trim(); };
    if (el.t === "image") {  // a picture: its own caption only (its label is the file's name)
        if (trim(el.cap)) below.push({ kind: "picture", text: trim(el.cap), fontId: "CapI", sizePt: CAPTION.CAPTION_PT });
        return { above: above, below: below };
    }
    if (trim(el.hdg)) above.push({ kind: "heading", text: trim(el.hdg), fontId: headingFont(opts && opts.headingWeight), sizePt: CAPTION.HEADING_PT });
    if (trim(el.lbl)) below.push({ kind: "description", text: trim(el.lbl), fontId: "CapR", sizePt: CAPTION.CAPTION_PT });
    var details = [el.denom, el.cond, el.perf].map(trim).filter(Boolean).join(" · ");
    if (details) below.push({ kind: "details", text: details, fontId: "CapI", sizePt: CAPTION.CAPTION_PT });
    if (trim(el.cat)) below.push({ kind: "catalogue", text: trim(el.cat), fontId: "CapI", sizePt: CAPTION.CAPTION_PT });
    return { above: above, below: below };
}

// Which elements carry captions: stamps (any shape), free shapes and pictures.
function hasCaptions(el) { return !!el && (el.t === "stamp" || el.t === "freehand" || el.t === "image"); }

// (x, y, w, h) is the stamp's own size; captions are placed around its frame.
// measure(text, fontId, sizePt) -> mm defaults to captionMeasure; opts as captionParts.
function captionLayout(el, x, y, w, h, measure, opts) {
    measure = measure || captionMeasure;
    var fb = frameBox(el, x, y, w, h);
    x = fb.x; y = fb.y; w = fb.w; h = fb.h;
    var parts = captionParts(el, opts), lh = function(r) { return r.sizePt * CAPTION.LINE_HEIGHT * CAPTION.MM_PER_PT; };
    function wrapped(list) {
        var rows = [];
        list.forEach(function(p) {
            wrapLines(p.text, Math.max(1, w), function(s) { return measure(s, p.fontId, p.sizePt); }).forEach(function(t) {
                if (t.trim()) rows.push({ kind: p.kind, text: t, fontId: p.fontId, sizePt: p.sizePt });
            });
        });
        return rows;
    }
    function place(r, top) {
        var tw = measure(r.text, r.fontId, r.sizePt);
        return { text: r.text, kind: r.kind, fontId: r.fontId, sizePt: r.sizePt, top: top, bottom: top + lh(r),
                 baseline: top + r.sizePt * CAPTION.FIRST_BASELINE * CAPTION.MM_PER_PT, width: tw, x: x + (w - tw) / 2,
                 weight: CAPTION_FONTS[r.fontId].weight, bold: CAPTION_FONTS[r.fontId].weight >= 600,
                 italic: CAPTION_FONTS[r.fontId].style === "italic" };
    }
    var out = [], rows = wrapped(parts.above);
    var top = y - CAPTION.GAP_MM - rows.reduce(function(a, r) { return a + lh(r); }, 0);
    rows.forEach(function(r) { var l = place(r, top); out.push(l); top = l.bottom; });
    top = y + h + CAPTION.GAP_MM;
    wrapped(parts.below).forEach(function(r) { var l = place(r, top); out.push(l); top = l.bottom; });
    return out;
}

function captionBounds(lines) {
    if (!lines || !lines.length) return null;
    var b = { l: Infinity, t: Infinity, r: -Infinity, b: -Infinity };
    lines.forEach(function(ln) {
        b.l = Math.min(b.l, ln.x); b.r = Math.max(b.r, ln.x + ln.width);
        b.t = Math.min(b.t, ln.top); b.b = Math.max(b.b, ln.bottom);
    });
    return b;
}

// Captions and frames that need attention. items: [{ id, box: {x, y, w, h}, lines, framed }] in mm,
// where box is the item's outer edge (a stamp's frame), lines its caption layout (empty for items
// without captions) and framed is true for items whose frame grows past their own size.
// area: {l, t, r, b}, the inside of the page border (or the page).
// Returns { id: "border" | "overlap" } for captions, or "frame-border" | "frame-overlap" when
// only the frame itself runs past the border or into another item.
function captionWarnings(items, area) {
    var res = {};
    var hit = function(a, b) { return a.l < b.r - 1e-6 && b.l < a.r - 1e-6 && a.t < b.b - 1e-6 && b.t < a.b - 1e-6; };
    var rect = function(bx) { return { l: bx.x, t: bx.y, r: bx.x + bx.w, b: bx.y + bx.h }; };
    var outside = function(b) {
        return area && (b.l < area.l - 1e-6 || b.t < area.t - 1e-6 || b.r > area.r + 1e-6 || b.b > area.b + 1e-6);
    };
    var caps = items.map(function(it) { return captionBounds(it.lines); });
    items.forEach(function(it, i) {
        var cb = caps[i], j;
        if (cb) {
            if (outside(cb)) { res[it.id] = "border"; return; }
            for (j = 0; j < items.length; j++) {
                if (j === i) continue;
                if (hit(cb, rect(items[j].box)) || (caps[j] && hit(cb, caps[j]))) { res[it.id] = "overlap"; return; }
            }
        }
        if (!it.framed) return;
        var fb = rect(it.box);
        if (outside(fb)) { res[it.id] = "frame-border"; return; }
        for (j = 0; j < items.length; j++) {
            if (j !== i && hit(fb, rect(items[j].box))) { res[it.id] = "frame-overlap"; return; }
        }
    });
    return res;
}

// ── Title and plan page ──
// An exhibit's first page, as FIP guidelines ask (GREV 3.3 and the class guidelines): the title,
// a line under it, then Purpose, Scope, the Plan in numbered chapters and sections, Important
// items, Research and References. The form (exhibit_plan.js) makes these as ordinary text items,
// each marked with its part (PAGE_TEXT_PART in the file), and reads its answers back from them,
// so the page is the only record and an edit made on the page shows in the form.
// Keep the section names in step with stamp_album/core/models.py PLAN_PARTS.
var PLAN_SECTIONS = ["purpose", "scope", "plan", "important", "research", "references"];
var PLAN_PART_NAMES = ["title", "by"].concat(PLAN_SECTIONS, PLAN_SECTIONS.map(function(n) { return n + "_label"; }));
var PLAN = { TOP_MM: 40, TOP_TIGHT_MM: 25, SIDE_MM: 20, BOTTOM_MM: 20, PAD_MM: 1, LINE_HEIGHT: 1.3,
             TITLE_PT: 22, BY_PT: 11, LABEL_PT: 11, BODY_PT: 10,
             TITLE_GAP_MM: 1, AFTER_HEAD_MM: 12, LABEL_H_MM: 8, LABEL_GAP_MM: 1, SECTION_GAP_MM: 6 };

// Chapters [{ level: 1 | 2, text }] numbered as a decimal plan: "1. Chapter", "1.1 Section".
// A section before any chapter is numbered as a chapter.
function planText(chapters) {
    var ch = 0, sec = 0, out = [];
    (chapters || []).forEach(function(c) {
        var text = String(c.text || "").trim();
        if (!text) return;
        if (c.level === 2 && ch > 0) { sec++; out.push(ch + "." + sec + " " + text); }
        else { ch++; sec = 0; out.push(ch + ". " + text); }
    });
    return out.join("\n");
}
// The reverse: a plan's lines back into chapters and sections; other lines are chapters.
function planChapters(text) {
    var out = [];
    String(text || "").split("\n").forEach(function(line) {
        line = line.trim();
        if (!line) return;
        var m = /^\d+\.\d+\.?\s+(.*)$/.exec(line);
        if (m) { out.push({ level: 2, text: m[1].trim() }); return; }
        m = /^\d+\.\s*(.*)$/.exec(line);
        out.push({ level: 1, text: (m ? m[1] : line).trim() });
    });
    return out;
}

// The page's text items, in mm: [{ part, x, y, w, h, font, fs, lbl, align, role }].
// answers: { title, by, purpose, scope, chapters, important, research, references };
// labels: the section names as printed ({ purpose: "Purpose", … }).
// measure(text, font, sizePt) -> width in mm. Empty sections are left out.
// Returns { items, bottom, limit, fits }; the page starts higher if that makes it fit.
function exhibitPlanLayout(answers, labels, pw, ph, measure) {
    answers = answers || {};
    var limit = ph - PLAN.BOTTOM_MM, w = pw - 2 * PLAN.SIDE_MM;
    var lineMm = function(pt) { return pt * PLAN.LINE_HEIGHT * 25.4 / 72; };
    var boxH = function(text, font, pt) {
        var lines = wrapLines(text, w - 2 * PLAN.PAD_MM, function(s) { return measure(s, font, pt); });
        return Math.ceil((lines.length * lineMm(pt) + 2 * PLAN.PAD_MM) * 10) / 10;
    };
    var body = function(name) {
        return name === "plan" ? planText(answers.chapters) : String(answers[name] || "").trim();
    };
    function build(top) {
        var items = [], y = top;
        var put = function(part, text, font, pt, align, minH, role) {
            var h = Math.max(minH || 0, boxH(text, font, pt));
            var it = { part: part, x: PLAN.SIDE_MM, y: Math.round(y * 10) / 10, w: w, h: h, font: font, fs: pt, lbl: text, align: align };
            if (role) it.role = role;
            items.push(it);
            y += h;
            return it;
        };
        var title = String(answers.title || "").trim(), by = String(answers.by || "").trim();
        if (title) { put("title", title, "HB", PLAN.TITLE_PT, "center", 13, "heading"); y += PLAN.TITLE_GAP_MM; }
        if (by) put("by", by, "HN", PLAN.BY_PT, "center", PLAN.LABEL_H_MM);
        if (title || by) y += PLAN.AFTER_HEAD_MM;
        PLAN_SECTIONS.forEach(function(name) {
            var text = body(name);
            if (!text) return;
            put(name + "_label", labels[name] || name, "HB", PLAN.LABEL_PT, "left", PLAN.LABEL_H_MM);
            y += PLAN.LABEL_GAP_MM;
            put(name, text, "HN", PLAN.BODY_PT, "left");
            y += PLAN.SECTION_GAP_MM;
        });
        var bottom = items.length ? Math.max.apply(null, items.map(function(it) { return it.y + it.h; })) : top;
        return { items: items, bottom: bottom, limit: limit, fits: bottom <= limit + 1e-6 };
    }
    var r = build(PLAN.TOP_MM);
    if (!r.fits) r = build(Math.min(PLAN.TOP_MM, PLAN.TOP_TIGHT_MM));
    return r;
}

// ── Exports ──
var EXPORTS = { THEMES: THEMES, themeColor: themeColor, FRAMES: FRAMES, frameOf: frameOf, applyFrame: applyFrame,
                FRAME_CLEARANCE_MM: FRAME_CLEARANCE_MM, MOUNT_OVERHANG_CHOICES: MOUNT_OVERHANG_CHOICES,
                MOUNT_GAP_CHOICES: MOUNT_GAP_CHOICES, NEW_ALBUM_MOUNT: NEW_ALBUM_MOUNT, OLD_ALBUM_MOUNT: OLD_ALBUM_MOUNT,
                validMount: validMount, setMount: setMount, getMount: getMount,
                BORDER_INSET_CHOICES: BORDER_INSET_CHOICES, NEW_ALBUM_BORDER_INSET: NEW_ALBUM_BORDER_INSET,
                OLD_ALBUM_BORDER_INSET: OLD_ALBUM_BORDER_INSET, validBorderInset: validBorderInset,
                setBorderInset: setBorderInset, getBorderInset: getBorderInset, frameClearance: frameClearance, frameLines: frameLines, frameOutset: frameOutset,
                frameBox: frameBox, SHAPE_POLYGONS: SHAPE_POLYGONS, shapeOutline: shapeOutline,
                normalizeStamp: normalizeStamp, PLAIN_BORDERS: PLAIN_BORDERS, escapeDSL: escapeDSL, unescapeDSL: unescapeDSL, serializeEl: serializeEl, buildDSL: buildDSL, parseDSL: parseDSL, normalizePageSize: normalizePageSize, findOutside: findOutside,
                describePageSize: describePageSize, fitToPage: fitToPage, PAPER_MM: PAPER_MM, FIXED_PAPERS: FIXED_PAPERS,
                FIP_FRAME_ROW: FIP_FRAME_ROW, FIP_FRAME_ROWS: FIP_FRAME_ROWS,
                CAPTION: CAPTION, CAPTION_FONTS: CAPTION_FONTS, HEADING_WEIGHTS: HEADING_WEIGHTS, headingFont: headingFont,
                captionMeasure: captionMeasure, wrapLines: wrapLines, captionParts: captionParts, hasCaptions: hasCaptions,
                captionLayout: captionLayout, captionBounds: captionBounds, captionWarnings: captionWarnings,
                PLAN: PLAN, PLAN_SECTIONS: PLAN_SECTIONS, PLAN_PART_NAMES: PLAN_PART_NAMES, planText: planText,
                planChapters: planChapters, exhibitPlanLayout: exhibitPlanLayout };
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EXPORTS;
}
if (typeof window !== 'undefined') {
    window.StampAlbumDSL = EXPORTS;
}

})();
