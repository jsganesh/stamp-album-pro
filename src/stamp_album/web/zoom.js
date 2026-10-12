"use strict";
// ── Editor zoom ──
// Zoom only changes how the page is shown on screen. The editor still works at
// 2.5 px per mm (S._sc): element positions, saved files and exports are the same
// at every zoom. The page is drawn with a CSS scale inside #page-zoom, a box that
// takes up the scaled size so the page can be centred and scrolled.
//
// Modes: "fit-width" (the default), "fit-page" and "actual" (100%). The fits
// never enlarge the page past 100%, so a wide window shows it at full size. The
// mode is remembered on this device, not in the album.
(function(root){

var MODES = ["fit-width", "fit-page", "actual"];
var MIN_ZOOM = 0.1;

// The scale that fits a pageW × pageH page into availW × availH (all px).
// Rounded down to 1/1000 so the scaled page never overflows the space.
function fitZoom(availW, availH, pageW, pageH, mode) {
    if (mode === "actual" || !(pageW > 0) || !(availW > 0)) return 1;
    var z = availW / pageW;
    if (mode === "fit-page" && pageH > 0 && availH > 0) z = Math.min(z, availH / pageH);
    z = Math.min(1, z);
    return Math.max(MIN_ZOOM, Math.floor(z * 1000 + 1e-9) / 1000);
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = { fitZoom: fitZoom, MODES: MODES };
}
if (!root || !root.document || !root.StampAlbum) return;

var S = root.StampAlbum, $ = S.$;
var KEY = "stampalbum-zoom";
var LABELS = { "fit-width": "Fit width", "fit-page": "Fit whole page", "actual": "Actual size" };
var _mode = "fit-width", _z = 1;

function loadMode() {
    try {
        var m = root.localStorage.getItem(KEY);
        if (MODES.indexOf(m) >= 0) _mode = m;
    } catch (_) { /* storage blocked: use the default */ }
}
function saveMode() {
    try { root.localStorage.setItem(KEY, _mode); } catch (_) { /* not remembered, still works */ }
}

function pad(cs, a, b) { return (parseFloat(cs[a]) || 0) + (parseFloat(cs[b]) || 0); }

// Size the page for the current mode and the space #page-wrap has now.
function applyZoom() {
    var wrap = $("page-wrap"), box = $("page-zoom"), pg = $("page");
    if (!wrap || !box || !pg) return;
    var cs = root.getComputedStyle(wrap);
    var aw = wrap.clientWidth - pad(cs, "paddingLeft", "paddingRight");
    var ah = wrap.clientHeight - pad(cs, "paddingTop", "paddingBottom");
    var z = fitZoom(aw, ah, S._pw, S._ph, _mode);
    _z = z;
    pg.style.transform = z === 1 ? "" : "scale(" + z + ")";
    box.style.width = S._pw * z + "px";
    box.style.height = S._ph * z + "px";
    // Handles and "!" badges keep their size on screen at any zoom.
    document.documentElement.style.setProperty("--inv-zoom", String(1 / z));
    syncControls();
    if (S.snapPageToPixels) S.snapPageToPixels();
}

function syncControls() {
    var pct = Math.round(_z * 100) + "%";
    var sb = $("sb-zoom");
    if (sb) {
        sb.textContent = pct;
        var next = _mode === "actual" ? "fit the width" : "show at actual size";
        sb.title = "Zoom: " + LABELS[_mode] + " (" + pct + "). Click to " + next + ".";
        sb.setAttribute("aria-label", "Zoom " + pct + ", " + LABELS[_mode] + ". Click to " + next + ".");
    }
    MODES.forEach(function(m) {
        var it = $("menu-zoom-" + m);
        if (it) it.setAttribute("aria-checked", m === _mode ? "true" : "false");
    });
}

function setZoomMode(mode) {
    if (MODES.indexOf(mode) < 0) return;
    _mode = mode;
    saveMode();
    applyZoom();
}

// A point on the screen (clientX/Y) as a position on the page, in canvas px.
function toPagePx(clientX, clientY) {
    var r = $("page").getBoundingClientRect();
    return { x: (clientX - r.left) / _z, y: (clientY - r.top) / _z };
}

Object.defineProperties(S, {
    zoom: { get: function(){ return _z; } },
    zoomMode: { get: function(){ return _mode; } },
    applyZoom: { value: applyZoom },
    setZoomMode: { value: setZoomMode },
    toPagePx: { value: toPagePx },
    fitZoom: { value: fitZoom },
});

function start() {
    loadMode();
    var wrap = $("page-wrap");
    if (wrap && root.ResizeObserver) new root.ResizeObserver(function() { applyZoom(); }).observe(wrap);
    root.addEventListener("resize", applyZoom); // rotation, a new screen
    var sb = $("sb-zoom");
    if (sb) sb.addEventListener("click", function() { setZoomMode(_mode === "actual" ? "fit-width" : "actual"); });
    applyZoom(); // the View menu's zoom items are wired in toolbar.js
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
else start();

})(typeof window !== "undefined" ? window : null);
