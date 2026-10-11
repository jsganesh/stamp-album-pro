"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast;
var CORE = window.StampAlbumDSL || {};

// ── Fit prompt: offered when an opened album has elements past the page edge ──
// Nothing moves unless the person chooses "Move inside". Moving uses Page setup's
// fitToPage (same margin, sizes never change) and is one undo step. The album is
// asked about every time it is opened; the file format is unchanged.

var MARGIN_MM = 15;  // as Page setup
var _returnFocus = null;

function plural(n, word) { return n + " " + word + (n === 1 ? "" : "s"); }

// Every page of the open album, with the current page's live elements.
function allPages() {
    var pages = S._pages.slice();
    pages[S._currentPage] = S.E;
    return pages;
}

function isOpen() { return $("fit-prompt-overlay").classList.contains("open"); }

function close() {
    $("fit-prompt-overlay").classList.remove("open");
    if (_returnFocus && _returnFocus.focus) _returnFocus.focus();
    _returnFocus = null;
}

// Called after an album has been opened from a file. Returns true if the prompt was shown.
function checkFitOnOpen() {
    var r = CORE.findOutside(allPages(), S._pw, S._ph);
    if (!r.count) return false;
    var used = S._pages.filter(function(p, i) { return (i === S._currentPage ? S.E : p).length; }).length;
    $("fp-note").textContent = plural(r.count, "element") + (used > 1 ? " on " + plural(r.pages, "page") : "") +
        (r.count === 1 ? " sits" : " sit") + " past the page edge. Move " + (r.count === 1 ? "it" : "them") +
        " inside the page? Sizes stay the same, and you can undo the move.";
    _returnFocus = document.activeElement;
    $("fit-prompt-overlay").classList.add("open");
    $("fp-leave").focus();
    return true;
}

function moveInside() {
    close();
    var r = CORE.fitToPage(allPages(), S._pw, S._ph, MARGIN_MM * S._sc);
    S._pages[S._currentPage] = S.E;
    S.pushUndo();
    S.render();
    S.updateProps();
    if (S.schedulePreviewRefresh) S.schedulePreviewRefresh();
    var msg = plural(r.moved, "element") + " moved inside the page";
    if (r.overlaps) msg += "; some now overlap, so check the layout";
    showToast(msg, r.overlaps ? "info" : "success");
}

function wireFitPrompt() {
    $("fp-leave").addEventListener("click", close);
    $("fp-move").addEventListener("click", moveInside);
    $("fit-prompt-overlay").addEventListener("keydown", function(e) {
        if (e.key === "Escape") { e.stopPropagation(); close(); }
        else if (e.key === "Tab") {
            // Keep focus on the two buttons while the dialog is open.
            var a = $("fp-leave"), b = $("fp-move");
            if (e.shiftKey && document.activeElement === a) { e.preventDefault(); b.focus(); }
            else if (!e.shiftKey && document.activeElement === b) { e.preventDefault(); a.focus(); }
        }
    });
}

// ── Exports ──
S.checkFitOnOpen = checkFitOnOpen;
S.fitPromptOpen = isOpen;
S.wireFitPrompt = wireFitPrompt;

})();
