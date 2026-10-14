"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast;
var CORE = window.StampAlbumDSL || {};

// ── Print calibration page ──
// A one-page PDF (engines/calibration.py) to print at 100% and measure, to check
// the printer prints 1 mm as 1 mm. The paper size starts as the album's.

function openCalibration() {
    var d = CORE.describePageSize ? CORE.describePageSize(S._pw / S._sc, S._ph / S._sc) : {};
    $("cal-paper").value = d.name || "a4";
    $("calibration-overlay").classList.add("open");
    $("cal-paper").focus();
}

function closeCalibration() {
    $("calibration-overlay").classList.remove("open");
}

function downloadCalibration() {
    var paper = $("cal-paper").value;
    var filename = "calibration-" + paper + ".pdf";
    closeCalibration();
    showToast(S.t("msg.generating_calibration"), "info");
    return fetch("/calibration.pdf?paper=" + encodeURIComponent(paper))
    .then(function(r) {
        if (!r.ok) throw new Error("(" + r.status + ")");
        return r.blob();
    })
    .then(function(blob) {
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
        setTimeout(function() { URL.revokeObjectURL(a.href); }, 100);
        showToast(S.t("msg.calibration_saved", { name: filename }), "success");
    })
    .catch(function(err) { showToast(S.t("msg.calibration_failed", { msg: err.message }), "error"); });
}

function wireCalibration() {
    $("cal-cancel").addEventListener("click", closeCalibration);
    $("cal-close").addEventListener("click", closeCalibration);
    $("cal-download").addEventListener("click", downloadCalibration);
    $("calibration-overlay").addEventListener("click", function(e) {
        if (e.target === this) closeCalibration();
    });
    $("calibration-overlay").addEventListener("keydown", function(e) {
        if (e.key === "Escape") { e.stopPropagation(); closeCalibration(); }
        else if (e.key === "Enter" && e.target.tagName !== "BUTTON") { e.preventDefault(); downloadCalibration(); }
    });
}

// ── Exports ──
S.openCalibration = openCalibration;
S.downloadCalibration = downloadCalibration;
S.wireCalibration = wireCalibration;

})();
