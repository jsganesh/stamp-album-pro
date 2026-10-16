"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast, pushUndo = S.pushUndo, render = S.render;
var parseDSL = S.parseDSL, escapeDSL = S.escapeDSL;

// ── Wizard ──
// The wizard always starts a new album; to change the open album's page use Page setup.
function applyWizard() {
    if (S._dirty && !confirm(S.t("msg.discard_unsaved"))) return;
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

    var dims = S.CORE.PAPER_MM[pgSize] || S.CORE.PAPER_MM.a4;
    var w = dims[0], h = dims[1];
    if (orient === "landscape" && !S.CORE.FIXED_PAPERS[pgSize]) { var t = w; w = h; h = t; }  // FIP sheets as listed
    lines.push("ALBUM_PAGES_SIZE(" + w + " " + h + ")");
    lines.push("ALBUM_PAGES_MARGINS(15 15 15 15)");
    var m = S.CORE.NEW_ALBUM_MOUNT;  // a new album's stamp mounts
    lines.push("ALBUM_MOUNT(" + m.overhang + " " + m.gap + ")");

    if (title) lines.push('PAGE_TEXT_CENTRE("HB" 16 "' + escapeDSL(title) + '")');

    parseDSL(lines.join("\n"));
    pushUndo();
    render();
    $("wizard-panel").classList.remove("open");
    showToast(S.t("msg.album_from_wizard"), "success");
}

// ── Exports ──
S.applyWizard = applyWizard;

})();
