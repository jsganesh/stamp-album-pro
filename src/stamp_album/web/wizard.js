"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast, pushUndo = S.pushUndo, render = S.render;
var parseDSL = S.parseDSL, escapeDSL = S.escapeDSL;

// ── Wizard ──
function applyWizard() {
    var title = $("wiz-title").value || "";
    var author = $("wiz-author").value || "";
    var pgSize = $("wiz-pg-size").value || "a4";
    var orient = $("wiz-orient").value || "portrait";
    var tpl = $("wiz-template").value;

    if (tpl && tpl !== "blank") {
        $("btn-wiz-template").click();
        return;
    }

    var lines = [];
    lines.push('ALBUM_TITLE("' + escapeDSL(title) + '")');
    if (author) lines.push('ALBUM_AUTHOR("' + escapeDSL(author) + '")');

    var PAPER = { a4: [210, 297], a5: [148, 210], a3: [297, 420], letter: [215.9, 279.4], legal: [215.9, 355.6] };
    var dims = PAPER[pgSize] || PAPER.a4;
    var w = dims[0], h = dims[1];
    if (orient === "landscape") { var t = w; w = h; h = t; }
    lines.push("ALBUM_PAGES_SIZE(" + w + " " + h + ")");
    lines.push("ALBUM_PAGES_MARGINS(15 15 15 15)");

    if (title) lines.push('PAGE_TEXT_CENTRE("HB" 16 "' + escapeDSL(title) + '")');

    parseDSL(lines.join("\n"));
    $("pg-size").value = PAPER[pgSize] ? pgSize : "a4";
    pushUndo();
    render();
    $("wizard-panel").classList.remove("open");
    showToast("Album created from wizard", "success");
}

// ── Exports ──
S.applyWizard = applyWizard;

})();
