/**
 * Drag-and-Drop Visual Builder (P2-12)
 * Allows users to drag stamps from a palette onto the preview canvas.
 * Supports snap-to-grid, visual selection, and DSL sync.
 */

(function() {
    "use strict";

    var dndCanvas = null;
    var dndActive = false;
    var dndSelectedStamp = null;
    var dndDragOffset = { x: 0, y: 0 };
    var dndSnapGrid = 5; // mm
    var dndStamps = []; // [{ id, x, y, width, height, description, el }]

    function initDragDropBuilder() {
        // Add drag-drop toggle button to toolbar
        var toolbarRight = document.querySelector(".toolbar-right");
        if (!toolbarRight || document.getElementById("toggle-dragdrop")) return;

        var toggle = document.createElement("label");
        toggle.className = "toggle-visual";
        toggle.id = "toggle-dragdrop-label";
        toggle.innerHTML = '<input type="checkbox" id="toggle-dragdrop"><span>Build</span>';
        toolbarRight.insertBefore(toggle, toolbarRight.firstChild);

        document.getElementById("toggle-dragdrop").addEventListener("change", function(e) {
            dndActive = e.target.checked;
            if (dndActive) enableDragDropMode();
            else disableDragDropMode();
        });
    }

    function enableDragDropMode() {
        // Show the visual overlay
        var overlay = document.getElementById("visual-overlay");
        if (overlay) {
            overlay.classList.remove("visual-hidden");
            overlay.style.pointerEvents = "auto";
        }

        // Build the stamp palette
        buildStampPalette();

        // Add drop zone to preview
        var frame = document.getElementById("preview-frame");
        if (frame) {
            frame.addEventListener("dragover", handleDragOver);
            frame.addEventListener("drop", handleDrop);
        }

        // Add click handler for selecting stamps on canvas
        if (overlay) {
            overlay.addEventListener("click", handleCanvasClick);
        }

        // Add keyboard shortcuts
        document.addEventListener("keydown", handleDnDKeyboard);

        showToast("Drag-and-drop mode: Drag stamps from the palette onto the page", "info");
    }

    function disableDragDropMode() {
        var overlay = document.getElementById("visual-overlay");
        if (overlay) {
            overlay.classList.add("visual-hidden");
            overlay.style.pointerEvents = "none";
        }
        removeStampPalette();
        clearDnDStamps();
        dndSelectedStamp = null;
    }

    function buildStampPalette() {
        var panel = document.getElementById("visual-property-panel");
        if (!panel) return;

        // Check if palette already exists
        if (document.getElementById("dnd-palette")) return;

        var palette = document.createElement("div");
        palette.id = "dnd-palette";
        palette.style.cssText = "padding:12px;border-bottom:1px solid var(--border-color);";

        palette.innerHTML =
            '<div style="font-size:11px;font-weight:600;color:var(--text-secondary);margin-bottom:8px">Stamp Palette — Drag to page</div>' +
            '<div style="display:flex;flex-wrap:wrap;gap:6px;">' +
            '<div class="dnd-palette-item" draggable="true" data-shape="rectangle" data-w="40" data-h="30" style="width:50px;height:36px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:4px;cursor:grab;display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--text-muted);">Rect</div>' +
            '<div class="dnd-palette-item" draggable="true" data-shape="oval" data-w="40" data-h="30" style="width:50px;height:36px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:50%;cursor:grab;display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--text-muted);">Oval</div>' +
            '<div class="dnd-palette-item" draggable="true" data-shape="square" data-w="30" data-h="30" style="width:50px;height:36px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:4px;cursor:grab;display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--text-muted);">□</div>' +
            '<div class="dnd-palette-item" draggable="true" data-shape="diamond" data-w="35" data-h="35" style="width:50px;height:36px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:4px;cursor:grab;display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--text-muted);">◇</div>' +
            '</div>' +
            '<div style="margin-top:8px;display:flex;gap:6px;align-items:center;">' +
            '<label style="font-size:10px;color:var(--text-muted)">Snap:</label>' +
            '<select id="dnd-snap-grid" style="padding:2px 6px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:4px;color:var(--text-primary);font-size:10px;">' +
            '<option value="0">Off</option>' +
            '<option value="5" selected>5mm</option>' +
            '<option value="10">10mm</option>' +
            '</select>' +
            '<button id="dnd-sync-dsl" class="collection-action-btn" style="padding:2px 8px;font-size:10px;">→ DSL</button>' +
            '<button id="dnd-clear" class="collection-action-btn" style="padding:2px 8px;font-size:10px;">Clear</button>' +
            '</div>';

        // Insert before vpp-content
        var vppContent = panel.querySelector(".vpp-content");
        if (vppContent) {
            panel.insertBefore(palette, vppContent);
        } else {
            panel.appendChild(palette);
        }

        // Add drag start handlers
        palette.querySelectorAll(".dnd-palette-item").forEach(function(item) {
            item.addEventListener("dragstart", function(e) {
                e.dataTransfer.setData("text/plain", JSON.stringify({
                    shape: item.dataset.shape,
                    w: parseFloat(item.dataset.w),
                    h: parseFloat(item.dataset.h),
                }));
                e.dataTransfer.effectAllowed = "copy";
            });
        });

        // Snap grid selector
        var snapSelect = document.getElementById("dnd-snap-grid");
        if (snapSelect) {
            snapSelect.addEventListener("change", function() {
                dndSnapGrid = parseInt(this.value) || 0;
            });
        }

        // Sync to DSL button
        var syncBtn = document.getElementById("dnd-sync-dsl");
        if (syncBtn) {
            syncBtn.addEventListener("click", syncDnDToDSL);
        }

        // Clear button
        var clearBtn = document.getElementById("dnd-clear");
        if (clearBtn) {
            clearBtn.addEventListener("click", function() {
                clearDnDStamps();
                renderDnDStamps();
            });
        }
    }

    function removeStampPalette() {
        var palette = document.getElementById("dnd-palette");
        if (palette) palette.remove();
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = "copy";
    }

    function handleDrop(e) {
        e.preventDefault();
        var data = e.dataTransfer.getData("text/plain");
        if (!data) return;

        try {
            var stamp = JSON.parse(data);
        } catch (err) {
            return;
        }

        // Get drop position relative to preview frame
        var frame = document.getElementById("preview-frame");
        var frameRect = frame.getBoundingClientRect();
        var x = e.clientX - frameRect.left;
        var y = e.clientY - frameRect.top;

        // Convert pixels to mm (preview renders at actual size, roughly 1px ≈ 0.2645mm at 96dpi)
        // But the iframe content is rendered at mm scale, so we need to get the iframe's internal coordinates
        var iframeDoc = frame.contentDocument || frame.contentWindow.document;
        if (!iframeDoc) return;

        // Get the page content area
        var pageContent = iframeDoc.querySelector(".page-content") || iframeDoc.body;
        if (!pageContent) return;

        var pageRect = pageContent.getBoundingClientRect();
        var mmX = (x - pageRect.left) * 0.2645; // px to mm
        var mmY = (y - pageRect.top) * 0.2645;

        // Snap to grid
        if (dndSnapGrid > 0) {
            mmX = Math.round(mmX / dndSnapGrid) * dndSnapGrid;
            mmY = Math.round(mmY / dndSnapGrid) * dndSnapGrid;
        }

        // Add stamp
        var newStamp = {
            id: "dnd_" + Date.now(),
            x: Math.max(0, mmX),
            y: Math.max(0, mmY),
            width: stamp.w,
            height: stamp.h,
            shape: stamp.shape,
            description: "",
        };
        dndStamps.push(newStamp);
        renderDnDStamps();
    }

    function renderDnDStamps() {
        var overlay = document.getElementById("visual-overlay");
        if (!overlay) return;

        // Clear existing DND stamps (keep other overlay elements)
        overlay.querySelectorAll(".dnd-stamp").forEach(function(el) { el.remove(); });

        dndStamps.forEach(function(s) {
            var el = document.createElement("div");
            el.className = "dnd-stamp";
            el.dataset.stampId = s.id;
            var isSelected = dndSelectedStamp === s.id;
            var shapeStyle = "";
            if (s.shape === "oval") shapeStyle = "border-radius:50%;";
            else if (s.shape === "diamond") shapeStyle = "clip-path:polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);";

            el.style.cssText = "position:absolute;left:" + s.x + "mm;top:" + s.y + "mm;width:" + s.width + "mm;height:" + s.height + "mm;border:2px solid " + (isSelected ? "var(--accent)" : "rgba(128,128,128,0.5)") + ";background:rgba(255,255,255,0.8);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--text-muted);" + shapeStyle;
            el.title = s.description || "Stamp at " + s.x.toFixed(1) + ", " + s.y.toFixed(1) + "mm";

            el.addEventListener("click", function(e) {
                e.stopPropagation();
                dndSelectedStamp = s.id;
                renderDnDStamps();
            });

            overlay.appendChild(el);
        });
    }

    function handleCanvasClick(e) {
        // Deselect if clicking empty area
        if (e.target === document.getElementById("visual-overlay")) {
            dndSelectedStamp = null;
            renderDnDStamps();
        }
    }

    function handleDnDKeyboard(e) {
        if (!dndActive) return;
        if (e.key === "Delete" || e.key === "Backspace") {
            if (dndSelectedStamp) {
                dndStamps = dndStamps.filter(function(s) { return s.id !== dndSelectedStamp; });
                dndSelectedStamp = null;
                renderDnDStamps();
            }
        }
        if (e.key === "Escape") {
            dndSelectedStamp = null;
            renderDnDStamps();
        }
    }

    function clearDnDStamps() {
        dndStamps = [];
        dndSelectedStamp = null;
    }

    function syncDnDToDSL() {
        if (dndStamps.length === 0) {
            showToast("No stamps to sync — drag stamps from the palette first", "error");
            return;
        }

        // Get current DSL
        var dsl = editor.getValue();
        if (!dsl.trim()) {
            dsl = 'ALBUM_TITLE("My Album")\n';
        }

        // Ensure PAGE_START exists
        if (dsl.indexOf("PAGE_START") === -1) {
            dsl += "\nPAGE_START\n";
        }

        // Add STAMP_ADD_AT commands before the last empty line or at end
        var lines = dsl.split("\n");
        var insertIdx = lines.length;

        // Find the last PAGE_START and insert after it
        for (var i = lines.length - 1; i >= 0; i--) {
            if (lines[i].trim() === "PAGE_START") {
                insertIdx = i + 1;
                break;
            }
        }

        dndStamps.forEach(function(s) {
            var shapeCmd = s.shape === "rectangle" ? "STAMP_ADD_AT" : "STAMP_ADD_AT";
            lines.splice(insertIdx, 0, shapeCmd + "(" + s.x.toFixed(1) + " " + s.y.toFixed(1) + " " + s.width + " " + s.height + " \"\" \"\" \"\" \"\")");
            insertIdx++;
        });

        editor.setValue(lines.join("\n"));
        saveUndoState();
        schedulePreview();
        showToast("Synced " + dndStamps.length + " stamps to DSL", "success");
    }

    document.addEventListener("DOMContentLoaded", initDragDropBuilder);
})();
