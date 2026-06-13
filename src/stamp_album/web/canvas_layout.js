/**
 * Free-form visual layout canvas (Phase 2 UX overhaul).
 *
 * Renders an mm-accurate page canvas over the preview area. Users can:
 * - Drag stamps from the sidebar onto the canvas at any position
 * - Move stamps by dragging them on the canvas
 * - Resize stamps via corner/edge handles
 * - Click to select, Delete/Backspace to remove
 * - Stamps snap to an optional mm grid
 * - Shapes: rectangle, oval, diamond, triangle, hexagon, octagon, pentagon
 *
 * Bidirectional sync with the DSL editor:
 * - Canvas changes → insert STAMP_ADD_AT commands in the DSL
 * - DSL changes → canvas re-renders absolute-positioned stamps
 *
 * The existing row/column system remains as an optional "scaffold" overlay.
 */


    "use strict";
    console.log("canvas_layout.js: init");

    // ── State ──────────────────────────────────────────────────────────
    var canvasEl = null;
    var canvasWrapper = null;
    var canvasStamps = [];   // [{ id, x, y, w, h, shape, description, el, selected }]
    var canvasActive = false;
    var canvasDrag = null;   // { stampId, handle, startX, startY, origX, origY, origW, origH }
    var canvasScale = 3.78;  // px per mm at default zoom (96dpi / 25.4)
    var canvasSnapMm = 5;    // snap-to-grid interval in mm (0 = off)
    var canvasPageW = 210;   // default A4
    var canvasPageH = 297;
    var nextStampId = 1;
    var canvasScaffold = false;  // show row guides
    var canvasUndoStack = [];
    var canvasRedoStack = [];

    // ── Initialise ──────────────────────────────────────────────────────
    function initCanvas() {
    // Use the existing visual-overlay as the canvas surface
    canvasWrapper = document.getElementById("visual-overlay");
    if (!canvasWrapper) return;

        // Build the canvas DOM once
        buildCanvasDOM();
        resizeCanvasToPage(canvasPageW, canvasPageH);

        // Toggle button in toolbar
        var btn = document.getElementById("toggle-layout");
        if (btn) {
            btn.addEventListener("change", function(e) {
                canvasActive = e.target.checked;
                if (canvasActive) enableCanvasMode();
                else disableCanvasMode();
            });
        }

        // Keyboard shortcuts
        document.addEventListener("keydown", onCanvasKey);
    }

    function buildCanvasDOM() {
        canvasEl = document.createElement("div");
        canvasEl.id = "layout-canvas";
        canvasEl.className = "layout-canvas";
        canvasEl.style.cssText =
            "position:absolute; top:0; left:0; " +
            "background: repeating-linear-gradient(0deg, transparent, transparent 9px, rgba(128,128,128,0.08) 10px), " +
            "repeating-linear-gradient(90deg, transparent, transparent 9px, rgba(128,128,128,0.08) 10px);";

        // Drop zone (catches sidebar palette drags)
        canvasEl.addEventListener("dragover", onCanvasDragOver);
        canvasEl.addEventListener("dragleave", onCanvasDragLeave);
        canvasEl.addEventListener("drop", onCanvasDrop);
        canvasEl.addEventListener("click", onCanvasClick);
        canvasEl.addEventListener("mousedown", onCanvasMouseDown);
        document.addEventListener("mousemove", onCanvasMouseMove);
        document.addEventListener("mouseup", onCanvasMouseUp);

        canvasWrapper.appendChild(canvasEl);
    }

    function resizeCanvasToPage(wMm, hMm) {
        canvasPageW = wMm;
        canvasPageH = hMm;
        if (!canvasEl) return;
        canvasEl.style.width = (wMm * canvasScale) + "px";
        canvasEl.style.height = (hMm * canvasScale) + "px";
    }

    // ── Mode toggle ────────────────────────────────────────────────────
    function enableCanvasMode() {
        canvasActive = true;
        document.body.classList.add("layout-mode");
        canvasEl.style.pointerEvents = "auto";
        // Disable the preview iframe clicks
        var frame = document.getElementById("preview-frame");
        if (frame) frame.style.pointerEvents = "none";
        // Re-render stamps from any existing DSL
        syncCanvasFromDSL();
        showToast("Layout mode: drag stamps from the sidebar, or click elements to add them", "info");
    }

    function disableCanvasMode() {
        canvasActive = false;
        document.body.classList.remove("layout-mode");
        canvasEl.style.pointerEvents = "none";
        var frame = document.getElementById("preview-frame");
        if (frame) frame.style.pointerEvents = "auto";
        // Don't clear stamps — keep them so re-enabling shows them again
    }

    // ── Stamp creation ─────────────────────────────────────────────────
    function addStampToCanvas(shape, wMm, hMm, xMm, yMm, description) {
        description = description || "";
        xMm = xMm != null ? xMm : 10;
        yMm = yMm != null ? yMm : 10;
        wMm = wMm || 40;
        hMm = hMm || 30;

        var stamp = {
            id: "cs_" + (nextStampId++),
            shape: shape || "rectangle",
            x: xMm,
            y: yMm,
            w: wMm,
            h: hMm,
            description: description,
            el: null,
            selected: false,
        };

        createStampDOM(stamp);
        canvasStamps.push(stamp);
        selectStamp(stamp.id);
        pushUndo();
        syncDSLFromCanvas();
        return stamp;
    }

    function createStampDOM(stamp) {
        var el = document.createElement("div");
        el.className = "canvas-stamp";
        el.dataset.stampId = stamp.id;
        positionStampDOM(stamp, el);

        // Label
        var label = document.createElement("span");
        label.className = "canvas-stamp-label";
        label.textContent = stamp.description || stamp.shape;
        el.appendChild(label);

        // Resize handles
        var handles = ["nw", "ne", "sw", "se", "n", "s", "e", "w"];
        handles.forEach(function(h) {
            var handle = document.createElement("div");
            handle.className = "canvas-handle canvas-handle-" + h;
            handle.dataset.handle = h;
            handle.dataset.stampId = stamp.id;
            el.appendChild(handle);
        });

        stamp.el = el;
        canvasEl.appendChild(el);
    }

    function positionStampDOM(stamp, el) {
        if (!el) el = stamp.el;
        if (!el) return;
        var x = stamp.x * canvasScale;
        var y = stamp.y * canvasScale;
        var w = stamp.w * canvasScale;
        var h = stamp.h * canvasScale;
        el.style.left = x + "px";
        el.style.top = y + "px";
        el.style.width = w + "px";
        el.style.height = h + "px";

        // Shape classes
        el.classList.remove("shape-rectangle", "shape-oval", "shape-diamond",
            "shape-triangle", "shape-hexagon", "shape-octagon", "shape-pentagon");
        el.classList.add("shape-" + (stamp.shape || "rectangle"));

        // Label text
        var label = el.querySelector(".canvas-stamp-label");
        if (label) label.textContent = stamp.description || stamp.shape;
    }

    // ── Selection ──────────────────────────────────────────────────────
    function selectStamp(id) {
        canvasStamps.forEach(function(s) {
            s.selected = (s.id === id);
            if (s.el) s.el.classList.toggle("selected", s.id === id);
        });
    }

    function getSelectedStamp() {
        for (var i = 0; i < canvasStamps.length; i++) {
            if (canvasStamps[i].selected) return canvasStamps[i];
        }
        return null;
    }

    // ── Drag (move) ────────────────────────────────────────────────────
    function onCanvasMouseDown(e) {
        if (!canvasActive) return;
        var target = e.target;

        // Resize handle?
        if (target.classList.contains("canvas-handle")) {
            var stampId = target.dataset.stampId;
            var handle = target.dataset.handle;
            var stamp = findStamp(stampId);
            if (!stamp) return;
            selectStamp(stampId);
            canvasDrag = {
                stampId: stampId,
                handle: handle,
                startX: e.clientX,
                startY: e.clientY,
                origX: stamp.x,
                origY: stamp.y,
                origW: stamp.w,
                origH: stamp.h,
            };
            e.preventDefault();
            e.stopPropagation();
            return;
        }

        // Stamp body?
        var stampEl = target.closest(".canvas-stamp");
        if (stampEl) {
            var id = stampEl.dataset.stampId;
            var stamp = findStamp(id);
            if (!stamp) return;
            selectStamp(id);
            canvasDrag = {
                stampId: id,
                handle: "move",
                startX: e.clientX,
                startY: e.clientY,
                origX: stamp.x,
                origY: stamp.y,
                origW: stamp.w,
                origH: stamp.h,
            };
            e.preventDefault();
            e.stopPropagation();
            return;
        }

        // Click on empty canvas — deselect
        if (target === canvasEl) {
            selectStamp(null);
        }
    }

    function onCanvasMouseMove(e) {
        if (!canvasDrag || !canvasActive) return;
        var stamp = findStamp(canvasDrag.stampId);
        if (!stamp) return;

        var dx = (e.clientX - canvasDrag.startX) / canvasScale;
        var dy = (e.clientY - canvasDrag.startY) / canvasScale;

        dx = snapMm(dx);
        dy = snapMm(dy);

        var handle = canvasDrag.handle;
        var x = canvasDrag.origX, y = canvasDrag.origY;
        var w = canvasDrag.origW, h = canvasDrag.origH;

        if (handle === "move") {
            x = canvasDrag.origX + dx;
            y = canvasDrag.origY + dy;
        } else {
            // Resize handles
            if (handle.indexOf("w") >= 0) { x = canvasDrag.origX + dx; w = canvasDrag.origW - dx; }
            if (handle.indexOf("e") >= 0) { w = canvasDrag.origW + dx; }
            if (handle.indexOf("n") >= 0) { y = canvasDrag.origY + dy; h = canvasDrag.origH - dy; }
            if (handle.indexOf("s") >= 0) { h = canvasDrag.origH + dy; }
            if (w < 5) w = 5;
            if (h < 5) h = 5;
        }

        // Constrain within page
        var px = x * canvasScale, py = y * canvasScale;
        var pw = Math.min(w * canvasScale, canvasPageW * canvasScale - px);
        var ph = Math.min(h * canvasScale, canvasPageH * canvasScale - py);
        stamp.x = px / canvasScale;
        stamp.y = py / canvasScale;
        stamp.w = pw / canvasScale;
        stamp.h = ph / canvasScale;

        positionStampDOM(stamp);
        syncDSLFromCanvas();
    }

    function onCanvasMouseUp(e) {
        if (canvasDrag) {
            pushUndo();
            canvasDrag = null;
        }
    }

    // ── Drop from sidebar palette ─────────────────────────────────────
    function onCanvasDragOver(e) {
        if (!canvasActive) return;
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = "copy";
        canvasEl.classList.add("drop-target");
    }

    function onCanvasDragLeave(e) {
        canvasEl.classList.remove("drop-target");
    }

    function onCanvasDrop(e) {
        if (!canvasActive) return;
        e.preventDefault();
        e.stopPropagation();
        canvasEl.classList.remove("drop-target");

        var rect = canvasEl.getBoundingClientRect();
        var xMm = (e.clientX - rect.left) / canvasScale;
        var yMm = (e.clientY - rect.top) / canvasScale;
        xMm = snapMm(xMm);
        yMm = snapMm(yMm);

        var shape = "rectangle", w = 40, h = 30;
        var raw = e.dataTransfer.getData("text/plain");
        if (raw) {
            try {
                var data = JSON.parse(raw);
                shape = data.shape || shape;
                w = data.width || w;
                h = data.height || h;
            } catch (_) {}
        }

        addStampToCanvas(shape, w, h, xMm, yMm, "");
    }

    function onCanvasClick(e) {
        if (!canvasActive) return;
        if (e.target === canvasEl) selectStamp(null);
    }

    // ── Keyboard ───────────────────────────────────────────────────────
    function onCanvasKey(e) {
        if (!canvasActive) return;
        var stamp = getSelectedStamp();
        if (!stamp) return;
        if (e.key === "Delete" || e.key === "Backspace") {
            removeStamp(stamp.id);
        }
        if (e.key === "Escape") {
            selectStamp(null);
        }
        // Arrow keys nudge selected stamp by snap interval
        var nudge = e.shiftKey ? canvasSnapMm * 5 : canvasSnapMm;
        if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].indexOf(e.key) >= 0 && canvasSnapMm > 0) {
            if (e.key === "ArrowLeft") stamp.x = Math.max(0, stamp.x - nudge);
            if (e.key === "ArrowRight") stamp.x = Math.min(canvasPageW - stamp.w, stamp.x + nudge);
            if (e.key === "ArrowUp") stamp.y = Math.max(0, stamp.y - nudge);
            if (e.key === "ArrowDown") stamp.y = Math.min(canvasPageH - stamp.h, stamp.y + nudge);
            positionStampDOM(stamp);
            syncDSLFromCanvas();
            pushUndo();
        }
    }

    // ── Remove ─────────────────────────────────────────────────────────
    function removeStamp(id) {
        var idx = -1;
        for (var i = 0; i < canvasStamps.length; i++) {
            if (canvasStamps[i].id === id) { idx = i; break; }
        }
        if (idx < 0) return;
        var stamp = canvasStamps[idx];
        if (stamp.el) stamp.el.remove();
        canvasStamps.splice(idx, 1);
        pushUndo();
        syncDSLFromCanvas();
    }

    function clearCanvasStamps() {
        canvasStamps.forEach(function(s) { if (s.el) s.el.remove(); });
        canvasStamps = [];
    }

    // ── Undo / Redo ────────────────────────────────────────────────────
    function pushUndo() {
        var state = canvasStamps.map(function(s) {
            return { id: s.id, shape: s.shape, x: s.x, y: s.y, w: s.w, h: s.h, description: s.description };
        });
        canvasUndoStack.push(JSON.stringify(state));
        if (canvasUndoStack.length > 50) canvasUndoStack.shift();
        canvasRedoStack = [];
    }

    function undoCanvas() {
        if (!canvasUndoStack.length) return;
        canvasRedoStack.push(JSON.stringify(canvasStamps.map(function(s) {
            return { id: s.id, shape: s.shape, x: s.x, y: s.y, w: s.w, h: s.h, description: s.description };
        })));
        var prev = JSON.parse(canvasUndoStack.pop());
        restoreCanvasState(prev);
    }

    function redoCanvas() {
        if (!canvasRedoStack.length) return;
        pushUndo();
        var next = JSON.parse(canvasRedoStack.pop());
        restoreCanvasState(next);
    }

    function restoreCanvasState(state) {
        clearCanvasStamps();
        state.forEach(function(s) {
            addStampToCanvas(s.shape, s.w, s.h, s.x, s.y, s.description || "");
        });
        // Pop the undo entry that addStampToCanvas just pushed
        if (canvasUndoStack.length) canvasUndoStack.pop();
        syncDSLFromCanvas();
    }

    // ── Snap ───────────────────────────────────────────────────────────
    function snapMm(val) {
        if (canvasSnapMm <= 0) return Math.round(val * 10) / 10;
        return Math.round(val / canvasSnapMm) * canvasSnapMm;
    }

    // ── Bidirectional DSL sync ─────────────────────────────────────────
    function syncDSLFromCanvas() {
        if (!editor) return;
        var dsl = editor.getValue();
        var lines = dsl.split("\n");

        // Remove all existing STAMP_ADD_AT lines
        var newLines = [];
        for (var i = 0; i < lines.length; i++) {
            var t = lines[i].trim();
            if (!t.startsWith("STAMP_ADD_AT(") && !t.startsWith("STAMP_TEXT_AT(")) {
                newLines.push(lines[i]);
            }
        }

        // Find insertion point: after the last non-absolute-position command
        var insertIdx = newLines.length;
        for (var j = newLines.length - 1; j >= 0; j--) {
            var lt = newLines[j].trim();
            if (lt === "PAGE_START" || lt.startsWith("PAGE_TEXT") || lt.startsWith("ROW_START") || lt.startsWith("STAMP_ADD")) {
                insertIdx = j + 1;
                break;
            }
        }

        // Insert canvas stamp DSL
        var stampLines = canvasStamps.map(function(s) {
            var shapeCmd = s.shape === "rectangle" ? "STAMP_ADD_AT" : "STAMP_ADD_AT";
            return shapeCmd + "(" + s.x.toFixed(1) + " " + s.y.toFixed(1) + " " +
                s.w.toFixed(1) + " " + s.h.toFixed(1) + " \"" + (s.description || "") + "\" \"\" \"\" \"\")";
        });

        for (var k = 0; k < stampLines.length; k++) {
            newLines.splice(insertIdx + k, 0, stampLines[k]);
        }

        editor.setValue(newLines.join("\n"));
        saveUndoState();
        schedulePreview();
    }

    function syncCanvasFromDSL() {
        if (!editor) return;
        var dsl = editor.getValue();
        var lines = dsl.split("\n");
        clearCanvasStamps();

        for (var i = 0; i < lines.length; i++) {
            var t = lines[i].trim();
            var m = t.match(/^STAMP_ADD_AT\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"/);
            if (m) {
                addStampToCanvas("rectangle", parseFloat(m[3]), parseFloat(m[4]),
                    parseFloat(m[1]), parseFloat(m[2]), m[5] || "");
            }
        }

        // Pop the undo entries that sync created
        canvasUndoStack = [];
        canvasRedoStack = [];
    }

    // ── Helpers ────────────────────────────────────────────────────────
    function findStamp(id) {
        for (var i = 0; i < canvasStamps.length; i++) {
            if (canvasStamps[i].id === id) return canvasStamps[i];
        }
        return null;
    }

    // expose globally for the build-item click-to-add
    window.addStampToCanvas = addStampToCanvas;
    window.undoCanvas = undoCanvas;
    window.redoCanvas = redoCanvas;

    // DOMContentLoaded may have already fired if this script loads late
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initCanvas);
    } else {
        initCanvas();
    }

