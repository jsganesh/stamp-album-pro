"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast;

var LABELS = { pdf: "PDF", png: "PNG", svg: "SVG", html: "HTML" };

// ── Export (PDF / PNG / SVG / HTML) ──
// On the computer the app runs on, a saved album's exports go into its own folder
// (StampAlbum/<album>/exports, the latest of each kind), with a button to show the file. An album
// not saved yet is offered a save first. On a phone or tablet on the Wi-Fi, exports download.
function exportFormat(fmt) {
    if (S.commitPanelEdit) S.commitPanelEdit();  // a field still being typed in counts first
    if (!S.exportsToFolder()) return download(fmt);
    if (S._currentFile && /\.slbum$/i.test(S._currentFile)) return toFolder(fmt);
    if (!confirm(S.t("msg.export_save_first"))) return download(fmt);
    return Promise.resolve(S.saveFile()).then(function(ok) { return ok ? toFolder(fmt) : download(fmt); });
}

// Whether this is the computer the app runs on (exports can go in the album's folder there).
function exportsToFolder() {
    var h = location.hostname;
    return h === "127.0.0.1" || h === "localhost" || h === "::1" || h === "[::1]";
}

// "Show in Finder" on a Mac, "Show in Explorer" on Windows.
function revealLabel() {
    var p = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "";
    if (/mac/i.test(p)) return S.t("ui.show_in_finder");
    if (/win/i.test(p)) return S.t("ui.show_in_explorer");
    return S.t("ui.show_the_file");
}

function toFolder(fmt) {
    showToast(S.t("msg.generating_format", { format: LABELS[fmt] || fmt }), "info");
    var state = S.buildCanvasState(fmt);
    state.save = true;
    var album = S._currentFile;
    return fetch("/export-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
    })
    .then(function(r) {
        if (!r.ok) throw new Error(S.t("msg.export_failed_status", { status: r.status }));
        return r.json();
    })
    .then(function(data) {
        var msg = S.t("msg.export_in_folder", { format: LABELS[fmt] || fmt, name: data.name,
                                                 folder: album.replace(/\.slbum$/i, "") });
        if (fmt === "pdf") msg += " " + S.t("msg.print_at_100");
        S.showToastAction(msg + S.missingFontsNote(), "success", revealLabel(), function() {
            fetch("/exports/reveal", { method: "POST", headers: { "Content-Type": "application/json" },
                                       body: JSON.stringify({ album: album, format: fmt }) });
        });
        return data;
    })
    .catch(function(err) { showToast(S.t("msg.export_failed", { msg: err.message || err }), "error"); });
}

// Send the export to the browser to download (a phone, or an album not saved).
function download(fmt) {
    var labels = LABELS;
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
S.exportsToFolder = exportsToFolder;

})();
