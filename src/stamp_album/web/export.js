"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast;

// ── Export (PDF / PNG / SVG / HTML) ──
function exportFormat(fmt) {
    if (S.commitPanelEdit) S.commitPanelEdit();  // a field still being typed in counts first
    var labels = { pdf: "PDF", png: "PNG", svg: "SVG", html: "HTML" };
    var exts = { pdf: ".pdf", png: ".png", svg: ".svg", html: ".html" };
    showToast(S.t("msg.generating_format", { format: labels[fmt] || fmt }), "info");
    var filename = S._currentFile ? S._currentFile.replace(/\.(slbum|txt)$/, exts[fmt] || ".pdf") : "album" + (exts[fmt] || ".pdf");
    var state = S.buildCanvasState(fmt);
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
        // A PDF is for printing: at 100%, or the stamp boxes shrink with the page
        showToast(S.t("msg.saved_to_downloads", { format: labels[fmt] || fmt, name: filename }) +
                  (fmt === "pdf" ? " " + S.t("msg.print_at_100") : "") + S.missingFontsNote(), "success");
    })
    .catch(function(err) { showToast(S.t("msg.export_failed", { msg: err }), "error"); });
}

// ── Export ──
S.exportFormat = exportFormat;

})();
