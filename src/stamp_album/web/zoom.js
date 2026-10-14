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
//
// A pinch (two fingers, a trackpad pinch, Ctrl/Cmd + wheel, Ctrl/Cmd + = and -)
// sets a free zoom ("custom", 25% to 400%) that keeps the point being zoomed at
// in place. It lasts for this session only: the next start uses the last fit mode.
(function(root){

var MODES = ["fit-width", "fit-page", "actual"];
var MIN_ZOOM = 0.1;
var PINCH_MIN = 0.25, PINCH_MAX = 4;
var SNAP_TO_100 = 0.05;  // a free zoom within 5% of 100% becomes exactly 100%
// Ctrl/Cmd + = and - step through these.
var STEPS = [0.25, 0.33, 0.5, 0.67, 0.75, 0.8, 0.9, 1, 1.1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4];

// The scale that fits a pageW × pageH page into availW × availH (all px).
// Rounded down to 1/1000 so the scaled page never overflows the space.
function fitZoom(availW, availH, pageW, pageH, mode) {
    if (mode === "actual" || !(pageW > 0) || !(availW > 0)) return 1;
    var z = availW / pageW;
    if (mode === "fit-page" && pageH > 0 && availH > 0) z = Math.min(z, availH / pageH);
    z = Math.min(1, z);
    return Math.max(MIN_ZOOM, Math.floor(z * 1000 + 1e-9) / 1000);
}

// A free zoom kept in 25%..400%, snapped to 100% when close to it.
function clampZoom(z) {
    if (!(z > 0)) return 1;
    z = Math.max(PINCH_MIN, Math.min(PINCH_MAX, z));
    if (Math.abs(z - 1) <= SNAP_TO_100) return 1;
    return Math.round(z * 1000) / 1000;
}

// The next step up (dir > 0) or down from z.
function stepZoom(z, dir) {
    var i;
    if (dir > 0) {
        for (i = 0; i < STEPS.length; i++) if (STEPS[i] > z + 1e-6) return STEPS[i];
        return PINCH_MAX;
    }
    for (i = STEPS.length - 1; i >= 0; i--) if (STEPS[i] < z - 1e-6) return STEPS[i];
    return PINCH_MIN;
}

// The scroll position that puts page point p (canvas px) at screen position c,
// along one axis: scroll is the scroller's position now, edge the page's screen
// position now (both at the new zoom z).
function anchorScroll(scroll, edge, p, z, c) {
    return scroll + edge + p * z - c;
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = { fitZoom: fitZoom, clampZoom: clampZoom, stepZoom: stepZoom,
                       anchorScroll: anchorScroll, MODES: MODES,
                       PINCH_MIN: PINCH_MIN, PINCH_MAX: PINCH_MAX };
}
if (!root || !root.document || !root.StampAlbum) return;

var S = root.StampAlbum, $ = S.$;
var KEY = "stampalbum-zoom";
var LABELS = { "fit-width": "ui.fit_width", "fit-page": "ui.fit_whole_page", "actual": "msg.zoom_actual",
               "custom": "msg.zoom_custom" };
var _mode = "fit-width", _z = 1, _custom = 1;

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
    var z = _mode === "custom" ? _custom : fitZoom(aw, ah, S._pw, S._ph, _mode);
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
        var fitted = _mode === "fit-width" || _mode === "fit-page";
        var p = { mode: S.t(LABELS[_mode]), pct: pct };
        sb.title = S.t(fitted ? "msg.zoom_title_to_actual" : "msg.zoom_title_to_fit", p);
        sb.setAttribute("aria-label", S.t(fitted ? "msg.zoom_label_to_actual" : "msg.zoom_label_to_fit", p));
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

// Set a free zoom and scroll so page point p (canvas px) is at screen point (cx, cy).
// A page narrower (or shorter) than the canvas stays centred, so along that axis the
// scroll can't move and only the page's middle stays put.
function zoomKeeping(z, p, cx, cy) {
    _custom = clampZoom(z);
    _mode = "custom";  // not saved: a free zoom lasts for this session only
    applyZoom();
    var wrap = $("page-wrap"), r = $("page").getBoundingClientRect();
    wrap.scrollLeft = anchorScroll(wrap.scrollLeft, r.left, p.x, _z, cx);
    wrap.scrollTop = anchorScroll(wrap.scrollTop, r.top, p.y, _z, cy);
}

// Zoom to z keeping the page point under screen point (cx, cy) where it is.
// Without a point, the middle of the visible canvas area.
function zoomAt(z, cx, cy) {
    if (cx == null) {
        var w = $("page-wrap").getBoundingClientRect();
        cx = w.left + w.width / 2; cy = w.top + w.height / 2;
    }
    zoomKeeping(z, toPagePx(cx, cy), cx, cy);
}
function zoomStep(dir) { zoomAt(stepZoom(_z, dir)); }

// ── Pinch with two fingers on the canvas area ──
// The page point between the fingers at the start stays between them, so moving
// both fingers also pans. Touches are tracked by id from where they started:
// a touch on a stamp keeps sending its events to that stamp's element even after
// a redraw has removed it, and those events no longer reach the document, so
// init.js forwards them here (S.pinchEvent). An event may arrive both ways.
var _onCanvas = {}, _pinch = null;

function inCanvas(t) { var w = $("page-wrap"); return !!(w && t && t.nodeType && w.contains(t)); }
function canvasTouches(e) {
    var out = [];
    for (var i = 0; i < e.touches.length; i++) if (_onCanvas[e.touches[i].identifier]) out.push(e.touches[i]);
    return out;
}
function mid(a, b) { return { x: (a.clientX + b.clientX) / 2, y: (a.clientY + b.clientY) / 2 }; }
function dist(a, b) { return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY); }

function pinchEvent(e) {
    if (e.__pinchSeen) return;
    e.__pinchSeen = true;
    var i, ct = e.changedTouches || [];
    if (e.type === "touchstart") {
        for (i = 0; i < ct.length; i++) if (inCanvas(e.target)) _onCanvas[ct[i].identifier] = true;
    }
    if (e.type === "touchend" || e.type === "touchcancel") {
        for (i = 0; i < ct.length; i++) delete _onCanvas[ct[i].identifier];
    }
    var ts = canvasTouches(e);
    if (ts.length < 2) { _pinch = null; return; }
    var a = ts[0], b = ts[1];
    if (!_pinch || _pinch.a !== a.identifier || _pinch.b !== b.identifier) {
        // A new pinch (or a different pair of fingers): start from here.
        if (S.cancelTouchDrag) S.cancelTouchDrag();  // a stamp drag gives way, and goes back
        var m = mid(a, b);
        _pinch = { a: a.identifier, b: b.identifier, z: _z, d: dist(a, b) || 1, p: toPagePx(m.x, m.y) };
        if (e.cancelable) e.preventDefault();
        return;
    }
    if (e.type === "touchmove") {
        var m2 = mid(a, b);
        zoomKeeping(_pinch.z * dist(a, b) / _pinch.d, _pinch.p, m2.x, m2.y);
        if (e.cancelable) e.preventDefault();
    }
}
function pinching() { return !!_pinch; }

// ── Ctrl/Cmd + wheel, and a trackpad pinch (Chrome, Edge and Firefox send it as a
// wheel with ctrlKey) ──
function onWheel(e) {
    if (!(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();  // not the browser's zoom of the whole app
    var dy = e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1);
    dy = Math.max(-100, Math.min(100, dy));  // one notch of a mouse wheel is about 100
    zoomAt(_z * Math.exp(-dy * 0.0025), e.clientX, e.clientY);
}

// ── Safari's trackpad pinch (gesture events, also in the Mac app's WebKit view) and
// iOS Safari's own pinch, which would zoom the whole app ──
var _gesture = null;
function onGesture(e) {
    if (!inCanvas(e.target) && !_gesture && !_pinch) return;
    e.preventDefault();
    if (_pinch) return;  // fingers on a touch screen: the touch events zoom
    if (e.type === "gesturestart") {
        _gesture = { z: _z, p: toPagePx(e.clientX, e.clientY) };
    } else if (e.type === "gesturechange" && _gesture) {
        zoomKeeping(_gesture.z * e.scale, _gesture.p, e.clientX, e.clientY);
    } else if (e.type === "gestureend") {
        _gesture = null;
    }
}

// ── Ctrl/Cmd + = and - step the zoom; Ctrl/Cmd + 0 fits the width ──
function onKey(e) {
    if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
    var t = e.target, tag = t && t.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (t && t.isContentEditable)) return;
    if (e.key === "=" || e.key === "+") { e.preventDefault(); zoomStep(1); }
    else if (e.key === "-" || e.key === "_") { e.preventDefault(); zoomStep(-1); }
    else if (e.key === "0") { e.preventDefault(); setZoomMode("fit-width"); }
}

Object.defineProperties(S, {
    zoom: { get: function(){ return _z; } },
    zoomMode: { get: function(){ return _mode; } },
    applyZoom: { value: applyZoom },
    setZoomMode: { value: setZoomMode },
    toPagePx: { value: toPagePx },
    fitZoom: { value: fitZoom },
    zoomAt: { value: zoomAt },
    zoomStep: { value: zoomStep },
    pinchEvent: { value: pinchEvent },
    pinching: { value: pinching },
});

function start() {
    loadMode();
    var wrap = $("page-wrap");
    if (wrap && root.ResizeObserver) new root.ResizeObserver(function() { applyZoom(); }).observe(wrap);
    root.addEventListener("resize", applyZoom); // rotation, a new screen
    var sb = $("sb-zoom");
    if (sb) sb.addEventListener("click", function() {
        setZoomMode(_mode === "fit-width" || _mode === "fit-page" ? "actual" : "fit-width");
    });
    // Capture, so the pinch sees a touch before a stamp's handlers redraw the page.
    ["touchstart", "touchmove", "touchend", "touchcancel"].forEach(function(t) {
        document.addEventListener(t, pinchEvent, { capture: true, passive: false });
    });
    if (wrap) wrap.addEventListener("wheel", onWheel, { passive: false });
    ["gesturestart", "gesturechange", "gestureend"].forEach(function(t) {
        document.addEventListener(t, onGesture, { capture: true, passive: false });
    });
    document.addEventListener("keydown", onKey);
    applyZoom(); // the View menu's zoom items are wired in toolbar.js
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
else start();

})(typeof window !== "undefined" ? window : null);
