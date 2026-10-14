"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast;

// ── Build canvas state for direct render/export ──
function buildCanvasState(format) {
    var allPages = S._pages.slice();
    allPages[S._currentPage] = JSON.parse(JSON.stringify(S.E));
    // Skip empty leading pages (parseDSL creates an empty page at index 0
    // when PAGE_START is the first command)
    var firstIdx = 0;
    while (firstIdx < allPages.length && allPages[firstIdx].length === 0) {
        firstIdx++;
    }
    var firstPage = firstIdx < allPages.length ? allPages[firstIdx] : [];
    var restPages = allPages.slice(firstIdx + 1);
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
        title: (S._currentFile || "").replace(/\.(slbum|txt)$/, ""),
        author: "",
        border_style: S._pageBorder || "",
        border_color: S.themeColor(),
        theme_color: S.themeColor(),  // marked headings
        caption_heading: S._captionHeading
    };
}

// ── Preview (direct — no DSL parser) ──
function openPreview() {
    var overlay = $("preview-overlay");
    var frame = $("preview-frame");
    if (!overlay || !frame) return;
    overlay.classList.add("open");
    showToast(S.t("msg.generating_preview"), "info");
    var state = buildCanvasState("html");
    fetch("/render-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
    })
    .then(function(r) {
        if (!r.ok) throw new Error(S.t("msg.render_failed_status", { status: r.status }));
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
        showToast(S.t("msg.preview_ready"), "success");
    })
    .catch(function(err) {
        showToast(S.t("msg.preview_failed", { msg: err }), "error");
    });
}

// ── Export (PDF / PNG / SVG / HTML) ──
function exportFormat(fmt) {
    var labels = { pdf: "PDF", png: "PNG", svg: "SVG", html: "HTML" };
    var exts = { pdf: ".pdf", png: ".png", svg: ".svg", html: ".html" };
    showToast(S.t("msg.generating_format", { format: labels[fmt] || fmt }), "info");
    var filename = S._currentFile ? S._currentFile.replace(/\.(slbum|txt)$/, exts[fmt] || ".pdf") : "album" + (exts[fmt] || ".pdf");
    var state = buildCanvasState(fmt);
    fetch("/export-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
    })
    .then(function(r) {
        if (!r.ok) throw new Error(S.t("msg.export_failed_status", { status: r.status }));
        if (fmt === "html") return r.text();
        return r.blob();
    })
    .then(function(data) {
        if (fmt === "html") {
            var w = window.open("", "_blank");
            if (w) { w.document.write(data); w.document.close(); }
            else { showToast(S.t("msg.popup_blocked"), "error"); }
        } else {
            var a = document.createElement("a");
            a.href = URL.createObjectURL(data);
            a.download = filename;
            a.click();
            setTimeout(function() { URL.revokeObjectURL(a.href); }, 100);
        }
        showToast(S.t("msg.saved_to_downloads", { format: labels[fmt] || fmt, name: filename }), "success");
    })
    .catch(function(err) { showToast(S.t("msg.export_failed", { msg: err }), "error"); });
}

// ── Export ──
S.exportFormat = exportFormat;

})();
