"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast;
var CORE = window.StampAlbumDSL || {};

// ── Page setup: change the open album's paper size and orientation ──
// Elements that would fall outside the new page are moved back inside it;
// their sizes never change. The whole change is one undo step.

var MARGIN_MM = 15;

// Every page of the open album, with the current page's live elements.
function allPages() {
    var pages = S._pages.slice();
    pages[S._currentPage] = S.E;
    return pages;
}

// The size the dialog's controls describe, in mm.
function chosenSize() {
    var key = $("ps-size").value;
    var landscape = $("ps-orient-landscape").checked;
    var w, h;
    if (key === "custom") {
        w = parseFloat($("ps-size").dataset.w); h = parseFloat($("ps-size").dataset.h);
        if ((w > h) !== landscape) { var t = w; w = h; h = t; }
    } else {
        var p = CORE.PAPER_MM[key] || CORE.PAPER_MM.a4;
        w = landscape ? p[1] : p[0]; h = landscape ? p[0] : p[1];
    }
    return { w: w, h: h };
}

function plural(n, word) { return n + " " + word + (n === 1 ? "" : "s"); }

function updateNote() {
    var size = chosenSize();
    var pages = allPages();
    var r = CORE.fitToPage(pages, size.w * S._sc, size.h * S._sc, MARGIN_MM * S._sc, { dryRun: true });
    var note = $("ps-note");
    note.classList.toggle("warn", r.moved > 0);
    if (!r.moved) {
        note.textContent = "Everything on the album fits the new page.";
        return;
    }
    var used = pages.filter(function(p) { return p && p.length; }).length;
    var msg = plural(r.moved, "element") + (used > 1 ? " on " + plural(r.pages, "page") : "") +
        " would fall outside the new page and will be moved inside it. Sizes stay the same.";
    if (r.tooBig) msg += " " + plural(r.tooBig, "element") + (r.tooBig === 1 ? " is" : " are") + " larger than the page.";
    if (r.overlaps) msg += " Some will overlap; check the layout after applying.";
    note.textContent = msg;
}

function openPageSetup() {
    var wmm = S._pw / S._sc, hmm = S._ph / S._sc;
    var d = CORE.describePageSize(wmm, hmm);
    var sel = $("ps-size");
    var custom = sel.querySelector('option[value="custom"]');
    if (d.name) {
        if (custom) custom.remove();
        sel.value = d.name;
    } else {
        if (!custom) {
            custom = document.createElement("option");
            custom.value = "custom";
            sel.appendChild(custom);
        }
        custom.textContent = "Custom (" + d.label + ")";
        sel.dataset.w = Math.min(wmm, hmm); sel.dataset.h = Math.max(wmm, hmm);
        sel.value = "custom";
    }
    $(d.landscape ? "ps-orient-landscape" : "ps-orient-portrait").checked = true;
    updateNote();
    $("page-setup-overlay").classList.add("open");
    sel.focus();
}

function closePageSetup() {
    $("page-setup-overlay").classList.remove("open");
}

function applyPageSetup() {
    var size = chosenSize();
    closePageSetup();
    if (Math.abs(size.w * S._sc - S._pw) < 0.01 && Math.abs(size.h * S._sc - S._ph) < 0.01) return;
    var r = CORE.fitToPage(allPages(), size.w * S._sc, size.h * S._sc, MARGIN_MM * S._sc);
    S._pages[S._currentPage] = S.E;
    S.applyPageSize(size.w, size.h);
    S.pushUndo();
    S.render();
    S.updateProps();
    S.schedulePreviewRefresh();
    var label = CORE.describePageSize(size.w, size.h).label;
    showToast("Page set to " + label + (r.moved ? "; " + plural(r.moved, "element") + " moved to fit" : ""), "success");
}

function wirePageSetup() {
    $("btn-page-setup").addEventListener("click", openPageSetup);
    $("ps-cancel").addEventListener("click", closePageSetup);
    $("ps-close").addEventListener("click", closePageSetup);
    $("ps-apply").addEventListener("click", applyPageSetup);
    ["ps-size", "ps-orient-portrait", "ps-orient-landscape"].forEach(function(id) {
        $(id).addEventListener("change", updateNote);
    });
    $("page-setup-overlay").addEventListener("click", function(e) {
        if (e.target === this) closePageSetup();
    });
    $("page-setup-overlay").addEventListener("keydown", function(e) {
        if (e.key === "Escape") { e.stopPropagation(); closePageSetup(); }
        else if (e.key === "Enter" && e.target.tagName !== "BUTTON") { e.preventDefault(); applyPageSetup(); }
    });
}

// ── Exports ──
S.openPageSetup = openPageSetup;
S.applyPageSetup = applyPageSetup;
S.wirePageSetup = wirePageSetup;

})();
