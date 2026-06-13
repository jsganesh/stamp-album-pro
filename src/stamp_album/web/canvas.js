"use strict";
console.log("canvas.js: loading");

var _overlay = document.getElementById("visual-overlay");
var _canvasEl = null, _stamps = [], _active = false;
var _scale = 3.78, _pw = 210, _ph = 297, _nextId = 1;

function initCanvas() {
    console.log("canvas.js: initCanvas called, overlay=" + !!_overlay);
    if (!_overlay) return;
    _canvasEl = document.createElement("div");
    _canvasEl.id = "layout-canvas";
    _canvasEl.className = "layout-canvas";
    _canvasEl.style.width = (_pw * _scale) + "px";
    _canvasEl.style.height = (_ph * _scale) + "px";
    _overlay.appendChild(_canvasEl);

    _canvasEl.addEventListener("dragover", function(e) { if (!_active) return; e.preventDefault(); _canvasEl.classList.add("drop-target"); });
    _canvasEl.addEventListener("dragleave", function() { _canvasEl.classList.remove("drop-target"); });
    _canvasEl.addEventListener("drop", function(e) {
        if (!_active) return;
        e.preventDefault();
        _canvasEl.classList.remove("drop-target");
        var r = _canvasEl.getBoundingClientRect();
        var xm = Math.round((e.clientX - r.left) / _scale / 5) * 5;
        var ym = Math.round((e.clientY - r.top) / _scale / 5) * 5;
        addStamp("rectangle", 40, 30, xm, ym, "");
    });

    _canvasEl.addEventListener("mousedown", function(e) {
        var el = e.target.closest(".canvas-stamp");
        if (el) {
            _stamps.forEach(function(s) { s.selected = (s.id === el.dataset.stampId); positionStamp(s); });
            e.preventDefault();
            e.stopPropagation();
        }
    });

    var t = document.getElementById("toggle-layout");
    if (t) {
        t.addEventListener("change", function(e) {
            _active = e.target.checked;
            if (_active) {
                document.body.classList.add("layout-mode");
                _canvasEl.style.pointerEvents = "auto";
                var f = document.getElementById("preview-frame");
                if (f) f.style.pointerEvents = "none";
                if (typeof showToast === "function") showToast("Layout mode: drag stamps here or click to add", "info");
            } else {
                document.body.classList.remove("layout-mode");
                _canvasEl.style.pointerEvents = "none";
                var f2 = document.getElementById("preview-frame");
                if (f2) f2.style.pointerEvents = "auto";
            }
        });
    }

    console.log("canvas.js: init complete, canvasEl=" + !!_canvasEl);
}

function positionStamp(s) {
    if (!s.el) return;
    s.el.style.left = (s.x * _scale) + "px";
    s.el.style.top = (s.y * _scale) + "px";
    s.el.style.width = (s.w * _scale) + "px";
    s.el.style.height = (s.h * _scale) + "px";
    s.el.className = "canvas-stamp shape-" + (s.shape || "rectangle") + (s.selected ? " selected" : "");
    var lbl = s.el.querySelector(".canvas-stamp-label");
    if (lbl) lbl.textContent = s.description || s.shape || "";
}

function addStamp(shape, w, h, x, y, desc) {
    var s = { id: "cs" + (_nextId++), shape: shape || "rectangle", x: x || 10, y: y || 10, w: w || 40, h: h || 30, description: desc || "" };
    var el = document.createElement("div");
    el.className = "canvas-stamp shape-" + s.shape;
    el.dataset.stampId = s.id;
    el.style.left = (s.x * _scale) + "px";
    el.style.top = (s.y * _scale) + "px";
    el.style.width = (s.w * _scale) + "px";
    el.style.height = (s.h * _scale) + "px";
    var lbl = document.createElement("span");
    lbl.className = "canvas-stamp-label";
    lbl.textContent = s.description || s.shape;
    el.appendChild(lbl);
    s.el = el;
    _canvasEl.appendChild(el);
    _stamps.push(s);
    syncToDSL();
}

function findStamp(id) {
    for (var i = 0; i < _stamps.length; i++) {
        if (_stamps[i].id === id) return _stamps[i];
    }
    return null;
}

function syncToDSL() {
    if (!window.editor) return;
    var lines = window.editor.getValue().split("\n");
    var out = [];
    for (var i = 0; i < lines.length; i++) {
        var t = lines[i].trim();
        if (!t.startsWith("STAMP_ADD_AT(")) out.push(lines[i]);
    }
    var ins = out.length;
    for (var j = out.length - 1; j >= 0; j--) {
        var lt = out[j].trim();
        if (lt === "PAGE_START" || lt.startsWith("ROW_START") || lt.startsWith("STAMP_ADD")) {
            ins = j + 1;
            break;
        }
    }
    _stamps.forEach(function(s) {
        out.splice(ins++, 0, 'STAMP_ADD_AT(' + s.x.toFixed(1) + ' ' + s.y.toFixed(1) + ' ' + s.w.toFixed(1) + ' ' + s.h.toFixed(1) + ' "' + (s.description || "") + '" "" "" "")');
    });
    window.editor.setValue(out.join("\n"));
}

window.addStampToCanvas = addStamp;

// Execute when DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCanvas);
} else {
    initCanvas();
}

console.log("canvas.js: bottom reached");
