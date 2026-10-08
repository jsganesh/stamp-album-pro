"use strict";
// Palette: click, keyboard or tap adds an item at the page centre (each repeat
// steps 10 mm right and down), and a short hint that hides after the first add
// and comes back when the user seems stuck.
(function(){
var S = window.StampAlbum;
var $ = S.$;

var OFFSET_MM = 10;           // step between repeated adds
var SAME_SPOT_MM = 2;         // two items whose centres are this close count as stacked
var BLANK_CLICKS = 3;         // clicks on an empty page...
var BLANK_CLICK_WINDOW = 4000; // ...within this many ms bring the hint back
S.paletteHintIdleMs = 20000;  // idle time on an empty page before the hint returns

// ── Building an element from a palette item ──

// What a palette item describes, read from its data attributes.
function itemSpec(it) {
    return { t: it.dataset.t, s: it.dataset.s || "rectangle", st: it.dataset.st || "",
        w: parseFloat(it.dataset.w) || 80, h: parseFloat(it.dataset.h) || 60, font: "HN", fs: 12 };
}

// The element a palette item adds, placed at (x, y). Shared by drag, touch and click.
function elementFrom(d, x, y) {
    var w = d.w || 80, h = d.h || 60;
    if (d.t === "text") { w = 120; h = d.st === "heading" ? 24 : d.st === "desc" ? 16 : 18; }
    if (d.t === "freehand") { w = 100; h = 80; }
    return { t: d.t || "stamp", s: d.s || "rectangle", x: x, y: y, w: w, h: h,
        lbl: d.t === "text" ? (d.st === "heading" ? "Heading" : d.st === "desc" ? "Description" : "Label") : "",
        font: d.font || "HN", fs: d.st === "heading" ? 16 : d.st === "desc" ? 10 : 12,
        bdr: S._defBdr, bdrC: S._defBdrC, bdrW: 1, fill: S._defFillC, fillA: 100, img: "" };
}

// Round a page position (px) to the snap grid, which is set in mm. Grid Off leaves it.
function onGrid(px) {
    var step = (S._sn || 0) * S._sc;
    return step > 0 ? Math.round(px / step) * step : px;
}

// Where a w × h item goes: the page centre, or 10 mm further along the diagonal
// for each item already there. Down-right first, then up-left, always inside the page.
function centrePlace(w, h) {
    var pw = S._pw, ph = S._ph, off = OFFSET_MM * S._sc, tol = SAME_SPOT_MM * S._sc;
    var x0 = (pw - w) / 2, y0 = (ph - h) / 2;
    function at(k) { return { x: onGrid(x0 + k * off), y: onGrid(y0 + k * off) }; }
    function fits(p) { return p.x >= 0 && p.y >= 0 && p.x + w <= pw + 0.01 && p.y + h <= ph + 0.01; }
    function taken(p) {
        var cx = p.x + w / 2, cy = p.y + h / 2;
        return S.E.some(function(e) {
            return Math.abs(e.x + e.w / 2 - cx) < tol && Math.abs(e.y + e.h / 2 - cy) < tol;
        });
    }
    var k, p;
    for (k = 0; fits(p = at(k)); k++) if (!taken(p)) return p;
    for (k = -1; fits(p = at(k)); k--) if (!taken(p)) return p;
    // Every spot on the diagonal is used (or the item is bigger than the page): the centre.
    p = at(0);
    return { x: Math.max(0, Math.min(p.x, pw - w)), y: Math.max(0, Math.min(p.y, ph - h)) };
}

// Add an element (already built) at the page centre.
function addAtCentre(props) {
    var p = centrePlace(props.w, props.h);
    props.x = p.x;
    props.y = p.y;
    S.add(props);
}

function addItem(it) { addAtCentre(elementFrom(itemSpec(it), 0, 0)); }

// ── Hint ──

var _hintSeenAdd = false, _idleTimer = null, _blankClicks = [];

function hint() { return $("palette-hint"); }
function showHint() {
    var h = hint();
    if (h && h.hidden) { h.hidden = false; }
}
function hideHint() {
    var h = hint();
    if (h) h.hidden = true;
}
function pageIsEmpty() { return S.E.length === 0; }

// Restart the idle clock on any real input. When it runs out on an empty page,
// the user has stopped and nothing is there yet, so point them at the palette.
function noteActivity() {
    clearTimeout(_idleTimer);
    _idleTimer = setTimeout(function() {
        if (pageIsEmpty()) showHint();
    }, S.paletteHintIdleMs);
}

function wire() {
    var items = document.querySelectorAll(".p-item");
    items.forEach(function(it) {
        it.addEventListener("click", function() { addItem(it); });
        it.addEventListener("keydown", function(e) {
            if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") {
                e.preventDefault();
                e.stopPropagation();
                addItem(it);
            }
        });
        // A drag let go away from the page: they tried, so show how it works.
        it.addEventListener("dragend", function(e) {
            if (!e.dataTransfer || e.dataTransfer.dropEffect === "none") showHint();
        });
    });

    // Clicking around a blank page, again and again, looks like "how do I add things?"
    var pg = $("page");
    if (pg) {
        pg.addEventListener("mousedown", function(e) {
            if (e.target.closest(".cel") || !pageIsEmpty()) { _blankClicks = []; return; }
            var now = Date.now();
            _blankClicks = _blankClicks.filter(function(t) { return now - t < BLANK_CLICK_WINDOW; });
            _blankClicks.push(now);
            if (_blankClicks.length >= BLANK_CLICKS) { _blankClicks = []; showHint(); }
        });
    }

    ["pointerdown", "keydown", "wheel", "dragstart", "touchstart"].forEach(function(ev) {
        document.addEventListener(ev, noteActivity, { passive: true, capture: true });
    });
    noteActivity();
    if (_hintSeenAdd) hideHint();
}

// Any add (palette, drop, image, duplicate) hides the hint; it only comes back
// through the triggers above.
var _add = S.add;
S.add = function(p) {
    _add(p);
    _hintSeenAdd = true;
    hideHint();
};

S.paletteElement = elementFrom;
S.paletteItemSpec = itemSpec;
S.addAtCentre = addAtCentre;
S.showPaletteHint = showHint;
S.wirePalette = wire;
})();
