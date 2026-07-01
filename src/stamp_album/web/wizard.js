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
    var columns = parseInt($("wiz-columns").value) || 0;
    var tpl = $("wiz-template").value;

    if (tpl && tpl !== "blank") {
        $("btn-wiz-template").click();
        return;
    }

    var lines = [];
    lines.push('ALBUM_TITLE("' + escapeDSL(title) + '")');
    if (author) lines.push('ALBUM_AUTHOR("' + escapeDSL(author) + '")');

    var w = pgSize === "a4" ? 210 : pgSize === "letter" ? 216 : 297;
    var h = pgSize === "a4" ? 297 : pgSize === "letter" ? 279 : 420;
    if (orient === "landscape") { var t = w; w = h; h = t; }
    lines.push("ALBUM_PAGES_SIZE(" + w + " " + h + ")");
    lines.push("ALBUM_PAGES_MARGINS(15 15 15 15)");

    if (title) lines.push('PAGE_TEXT_CENTRE("HB" 16 "' + escapeDSL(title) + '")');

    if (columns > 1) {
        lines.push("PAGE_COLUMN_START(" + columns + ")");
    }

    parseDSL(lines.join("\n"));
    pushUndo();
    render();
    $("wizard-panel").classList.remove("open");
    showToast("Album created from wizard", "success");
}

// ── Template list ──
function loadTemplateList() {
    var sel = $("wiz-template");
    if (!sel) return;
    fetch("/api/templates")
        .then(function(r) { return r.json(); })
        .then(function(templates) {
            sel.innerHTML = '<option value="blank">Blank Page</option>';
            templates.forEach(function(t) {
                var o = document.createElement("option");
                o.value = t.id;
                o.textContent = t.name;
                sel.appendChild(o);
            });
        })
        .catch(function() { /* ignore — template endpoint may not exist */ });
}

// ── Exports ──
S.applyWizard = applyWizard;
S.loadTemplateList = loadTemplateList;

})();
