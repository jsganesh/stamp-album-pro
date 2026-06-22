"use strict";
(function(){
var S = window.StampAlbum;
var showToast = S.showToast;

// ── Build canvas state for direct render/export ──
function buildCanvasState(format) {
    var allPages = S._pages.slice();
    allPages[S._currentPage] = JSON.parse(JSON.stringify(S.E));
    var firstPage = allPages.length > 0 ? allPages[0] : [];
    var restPages = allPages.slice(1);
    while (restPages.length > 0 && restPages[restPages.length - 1].length === 0) {
        restPages.pop();
    }
    return {
        elements: firstPage,
        pages: restPages,
        page_width_px: S._pw, page_height_px: S._ph,
        scale: S._sc,
        source_path: S._currentFile || "album.slbum",
        format: format || "html",
        title: (S._currentFile || "My Album").replace(/\.(slbum|txt)$/, ""),
        author: ""
    };
}

// ── Preview (direct — no DSL parser) ──
function openPreview() {
    var overlay = $("preview-overlay");
    var frame = $("preview-frame");
    if (!overlay || !frame) return;
    overlay.classList.add("open");
    showToast("Generating preview...", "info");
    var state = buildCanvasState("html");
    fetch("/render-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
    })
    .then(function(r) {
        if (!r.ok) throw new Error("Render failed (" + r.status + ")");
        return r.text();
    })
    .then(function(html) {
        frame.contentDocument.open();
        frame.contentDocument.write(html);
        frame.contentDocument.close();
        var body = frame.contentDocument.body;
        if (body) {
            var firstPage = body.querySelector(".page");
            if (firstPage) {
                frame.style.width = firstPage.offsetWidth + "px";
                frame.style.height = firstPage.offsetHeight + "px";
            }
        }
        showToast("Preview ready", "success");
    })
    .catch(function(err) {
        showToast("Preview failed: " + err, "error");
    });
}

// ── Export (PDF / PNG / SVG / HTML) ──
function exportFormat(fmt) {
    var labels = { pdf: "PDF", png: "PNG", svg: "SVG", html: "HTML" };
    var exts = { pdf: ".pdf", png: ".png", svg: ".svg", html: ".html" };
    showToast("Generating " + (labels[fmt] || fmt) + "...", "info");
    var filename = S._currentFile ? S._currentFile.replace(/\.(slbum|txt)$/, exts[fmt] || ".pdf") : "album" + (exts[fmt] || ".pdf");
    var state = buildCanvasState(fmt);
    fetch("/export-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
    })
    .then(function(r) {
        if (!r.ok) throw new Error("Export failed (" + r.status + ")");
        if (fmt === "html") return r.text();
        return r.blob();
    })
    .then(function(data) {
        if (fmt === "html") {
            var w = window.open("", "_blank");
            if (w) { w.document.write(data); w.document.close(); }
            else { showToast("Popup blocked — allow popups for HTML export", "error"); }
        } else {
            var a = document.createElement("a");
            a.href = URL.createObjectURL(data);
            a.download = filename;
            a.click();
            setTimeout(function() { URL.revokeObjectURL(a.href); }, 100);
        }
        showToast((labels[fmt] || fmt) + " saved to Downloads/" + filename, "success");
    })
    .catch(function(err) { showToast("Export failed: " + err, "error"); });
}

// ── Exports ──
S.buildCanvasState = buildCanvasState;
S.openPreview = openPreview;
S.exportFormat = exportFormat;

})();
