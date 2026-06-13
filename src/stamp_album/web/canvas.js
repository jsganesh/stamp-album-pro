"use strict";
console.log("canvas.js: loading");

var _overlay = null, _canvasEl = null, _stamps = [], _active = false, _drag = null;
var _scale = 2.5, _snap = 5, _pw = 210, _ph = 297, _nextId = 1;

function initCanvas() {
    _overlay = document.getElementById("visual-overlay");
    if (!_overlay) return;

    _canvasEl = document.createElement("div");
    _canvasEl.id = "layout-canvas";
    _canvasEl.className = "layout-canvas";
    _canvasEl.style.width = (_pw * _scale) + "px";
    _canvasEl.style.height = (_ph * _scale) + "px";
    _overlay.appendChild(_canvasEl);

    _canvasEl.addEventListener("dragover", function(e) { if (!_active) return; e.preventDefault(); _canvasEl.classList.add("drop-target"); });
    _canvasEl.addEventListener("dragleave", function() { _canvasEl.classList.remove("drop-target"); });
    _canvasEl.addEventListener("drop", onCanvasDrop);
    _canvasEl.addEventListener("mousedown", onCanvasMouseDown);
    document.addEventListener("mousemove", onCanvasMouseMove);
    document.addEventListener("mouseup", onCanvasMouseUp);
    document.addEventListener("keydown", onCanvasKey);

    var t = document.getElementById("toggle-layout");
    if (t) t.addEventListener("change", function(e) {
        _active = e.target.checked;
        if (_active) {
            document.body.classList.add("layout-mode");
            _canvasEl.style.pointerEvents = "auto";
            var f = document.getElementById("preview-frame");
            if (f) f.style.pointerEvents = "none";
            if (typeof showToast === "function") showToast("Layout mode ON — click or drag stamps", "info");
        } else {
            document.body.classList.remove("layout-mode");
            _canvasEl.style.pointerEvents = "none";
            var f2 = document.getElementById("preview-frame");
            if (f2) f2.style.pointerEvents = "auto";
        }
    });

    console.log("canvas.js: init complete");
}

function snapMm(v) { return _snap > 0 ? Math.round(v / _snap) * _snap : Math.round(v * 10) / 10; }

function onCanvasDrop(e) {
    if (!_active) return;
    e.preventDefault();
    _canvasEl.classList.remove("drop-target");
    // Calculate mm position relative to canvas, clamped to page bounds
    var r = _canvasEl.getBoundingClientRect();
    var xm = snapMm((e.clientX - r.left) / _scale);
    var ym = snapMm((e.clientY - r.top) / _scale);
    xm = Math.max(0, Math.min(xm, _pw - 40));
    ym = Math.max(0, Math.min(ym, _ph - 30));

    var shape = "rectangle", w = 40, h = 30, type = "stamp";
    try {
        var d = JSON.parse(e.dataTransfer.getData("text/plain"));
        if (d) { type = d.type || "stamp"; shape = d.shape || "rectangle"; w = d.width || 40; h = d.height || 30; }
    } catch (_) {}

    if (type === "text") addTextElement(xm, ym, d.align || "left");
    else if (type === "row") addRowElement(xm, ym, d.style || "FS");
    else addStamp(shape, w, h, xm, ym, "");
}

function addStamp(shape, w, h, x, y, desc) {
    addElement({ type: "stamp", shape: shape || "rectangle", x: x, y: y, w: w || 40, h: h || 30, description: desc || "" });
}

function addTextElement(x, y, align) {
    addElement({ type: "text", shape: "text", x: x, y: y, w: 60, h: 10, description: "Text", align: align || "left" });
}

function addRowElement(x, y, style) {
    addElement({ type: "row", shape: "row", x: x, y: y, w: 180, h: 30, description: "Row", style: style || "FS" });
}

function addElement(params) {
    var s = { id: "cs" + (_nextId++), type: params.type, shape: params.shape, x: params.x, y: params.y, w: params.w, h: params.h, description: params.description || "" };
    if (params.align) s.align = params.align;
    if (params.style) s.style = params.style;
    buildStampDOM(s);
    _stamps.push(s);
    selectStamp(s.id);
    syncToDSL();
    trySyncWhenReady();
}

function buildStampDOM(s) {
    var el = document.createElement("div");
    el.className = "canvas-stamp shape-" + (s.shape || "rectangle");
    el.dataset.stampId = s.id;
    positionStamp(s, el);
    var lbl = document.createElement("span");
    lbl.className = "canvas-stamp-label";
    lbl.textContent = s.description || s.shape;
    el.appendChild(lbl);
    ["nw","ne","sw","se","n","s","e","w"].forEach(function(h) {
        var handle = document.createElement("div");
        handle.className = "canvas-handle canvas-handle-" + h;
        handle.dataset.handle = h;
        handle.dataset.stampId = s.id;
        el.appendChild(handle);
    });
    s.el = el;
    _canvasEl.appendChild(el);
}

function positionStamp(s, el) {
    if (!el) el = s.el;
    if (!el) return;
    el.style.left = (s.x * _scale) + "px";
    el.style.top = (s.y * _scale) + "px";
    el.style.width = (s.w * _scale) + "px";
    el.style.height = (s.h * _scale) + "px";
    el.className = "canvas-stamp shape-" + (s.shape || "rectangle") + (s.selected ? " selected" : "");
    var lbl = el.querySelector(".canvas-stamp-label");
    if (lbl) lbl.textContent = s.description || s.shape || "";
}

function selectStamp(id) {
    _stamps.forEach(function(s) { s.selected = (s.id === id); positionStamp(s); });
}
function findStamp(id) { for (var i = 0; i < _stamps.length; i++) if (_stamps[i].id === id) return _stamps[i]; return null; }
function getSelected() { for (var i = 0; i < _stamps.length; i++) if (_stamps[i].selected) return _stamps[i]; return null; }

function removeStamp(id) {
    var s = findStamp(id);
    if (!s) return;
    if (s.el) s.el.remove();
    _stamps = _stamps.filter(function(x) { return x.id !== id; });
    syncToDSL();
}

function onCanvasMouseDown(e) {
    if (!_active) return;
    var t = e.target;
    if (t.classList.contains("canvas-handle")) {
        var s = findStamp(t.dataset.stampId);
        if (!s) return;
        selectStamp(s.id);
        _drag = { id: s.id, handle: t.dataset.handle, sx: e.clientX, sy: e.clientY, ox: s.x, oy: s.y, ow: s.w, oh: s.h };
        e.preventDefault(); e.stopPropagation();
        return;
    }
    var el = t.closest(".canvas-stamp");
    if (el) {
        var s2 = findStamp(el.dataset.stampId);
        if (!s2) return;
        selectStamp(s2.id);
        _drag = { id: s2.id, handle: "move", sx: e.clientX, sy: e.clientY, ox: s2.x, oy: s2.y, ow: s2.w, oh: s2.h };
        e.preventDefault(); e.stopPropagation();
        return;
    }
    if (t === _canvasEl) selectStamp(null);
}

function onCanvasMouseMove(e) {
    if (!_drag || !_active) return;
    var s = findStamp(_drag.id);
    if (!s) return;
    var dx = snapMm((e.clientX - _drag.sx) / _scale);
    var dy = snapMm((e.clientY - _drag.sy) / _scale);
    var h = _drag.handle, x = _drag.ox, y = _drag.oy, w = _drag.ow, oh = _drag.oh;
    if (h === "move") { x += dx; y += dy; }
    else {
        if (h.indexOf("w") >= 0) { x += dx; w -= dx; }
        if (h.indexOf("e") >= 0) { w += dx; }
        if (h.indexOf("n") >= 0) { y += dy; oh -= dy; }
        if (h.indexOf("s") >= 0) { oh += dy; }
        if (w < 5) w = 5; if (oh < 5) oh = 5;
    }
    s.x = Math.max(0, x); s.y = Math.max(0, y);
    s.w = Math.min(w, _pw - s.x); s.h = Math.min(oh, _ph - s.y);
    positionStamp(s);
    syncToDSL();
}

function onCanvasMouseUp(e) { _drag = null; }
function onCanvasKey(e) { if (!_active) return; var s = getSelected(); if (!s) return; if (e.key === "Delete" || e.key === "Backspace") removeStamp(s.id); if (e.key === "Escape") selectStamp(null); }
function syncToDSL() {
    var ed = window.editor;
    if (!ed) return;
    var lines = ed.getValue().split("\n"), out = [];
    for (var i = 0; i < lines.length; i++) { var t = lines[i].trim(); if (!t.startsWith("STAMP_ADD_AT(") && !t.startsWith("PAGE_TEXT_AT(") && !t.startsWith("ROW_START_AT(")) out.push(lines[i]); }
    var ins = out.length;
    for (var j = out.length - 1; j >= 0; j--) { var lt = out[j].trim(); if (lt === "PAGE_START" || lt.startsWith("ROW_START") || lt.startsWith("STAMP_ADD") || lt.startsWith("PAGE_TEXT")) { ins = j + 1; break; } }
    _stamps.forEach(function(s) {
        if (s.type === "text") {
            var a = s.align === "center" ? "_CENTRE" : s.align === "right" ? "_RIGHT" : "";
            out.splice(ins++, 0, "PAGE_TEXT_AT(" + s.x.toFixed(1) + " " + s.y.toFixed(1) + " \"HN\" 12 \"" + (s.description || "Text") + "\"" + a + ")");
        } else if (s.type === "row") {
            out.splice(ins++, 0, "ROW_START_AT(" + s.x.toFixed(1) + " " + s.y.toFixed(1) + " \"" + (s.style || "FS") + "\" \"HN\" 10 5 180)");
        } else {
            out.splice(ins++, 0, "STAMP_ADD_AT(" + s.x.toFixed(1) + " " + s.y.toFixed(1) + " " + s.w.toFixed(1) + " " + s.h.toFixed(1) + " \"" + (s.description || "") + "\" \"\" \"\"\")");
        }
    });
    ed.setValue(out.join("\n"));
    if (typeof schedulePreview === "function") schedulePreview();
}

// Retry sync when editor becomes available
function trySyncWhenReady() {
    if (window.editor && _stamps.length > 0) {
        syncToDSL();
    } else if (_stamps.length > 0) {
        setTimeout(trySyncWhenReady, 200);
    }
}

function syncFromDSL() {
    if (!window.editor) return;
    _stamps.forEach(function(s) { if (s.el) s.el.remove(); });
    _stamps = [];
    var lines = window.editor.getValue().split("\n");
    for (var i = 0; i < lines.length; i++) {
        var t = lines[i].trim();
        var m = t.match(/^STAMP_ADD_AT\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"/);
        if (m) { addStamp("rectangle", parseFloat(m[3]), parseFloat(m[4]), parseFloat(m[1]), parseFloat(m[2]), m[5] || ""); continue; }
        var m2 = t.match(/^PAGE_TEXT_AT\(\s*([\d.]+)\s+([\d.]+)\s+"HN"\s+(\d+)\s+"([^"]*)"(\w*)/);
        if (m2) { addTextElement(parseFloat(m2[1]), parseFloat(m2[2]), m2[5] ? m2[5].replace("_CENTRE","center").replace("_RIGHT","right") : "left"); continue; }
        var m3 = t.match(/^ROW_START_AT\(\s*([\d.]+)\s+([\d.]+)\s+"(\w+)"/);
        if (m3) { addRowElement(parseFloat(m3[1]), parseFloat(m3[2]), m3[3]); }
    }
}

window.addStampToCanvas = addStamp;
window.addTextToCanvas = addTextElement;
window.addRowToCanvas = addRowElement;

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initCanvas);
else initCanvas();

console.log("canvas.js: bottom reached");
