"use strict";
// Keyboard access to the items on the page.
//
// - Every item is a tab stop (render.js sets tabindex and a spoken name), so Tab
//   and Shift+Tab move between them; focusing an item selects it.
// - Arrow keys move the selected item one grid step (1 mm with the grid off);
//   Shift+arrow moves it 10 mm. Each press is one undo step.
// - Enter jumps to the item's properties (X position first); Escape and Delete
//   are handled by the shortcuts in init.js.
(function(){
var S = window.StampAlbum;
var $ = S.$;

var NUDGE_BIG_MM = 10;

function stepMm(big) {
    if (big) return NUDGE_BIG_MM;
    var grid = parseFloat(($("grid") || {}).value);
    return grid > 0 ? grid : 1;
}

// Arrow keys act when focus is on the page or nowhere in particular (after a mouse
// click on an item), never in a form field, menu, dialog or an editable label.
function arrowsBelongToPage(target) {
    if (!target || target === document.body || target === document.documentElement) return true;
    if (target.isContentEditable) return false;
    return $("page").contains(target);
}

function nudge(id, dxMm, dyMm) {
    var el = S.E.find(function(x) { return x.id === id; });
    if (!el) return;
    var x = Math.max(0, Math.min(el.x + dxMm * S._sc, S._pw - el.w));
    var y = Math.max(0, Math.min(el.y + dyMm * S._sc, S._ph - el.h));
    if (x === el.x && y === el.y) return;  // already against the page edge
    el.x = x;
    el.y = y;
    S.pushUndo();
    S.render();
    S.updateProps();
}

function wirePageKeys() {
    var pg = $("page");

    // Focusing an item selects it. render() puts focus back on the rebuilt element
    // with S._refocusing set, which must not undo a deselection (Escape).
    pg.addEventListener("focusin", function(e) {
        if (S._refocusing) return;
        var cel = e.target.closest && e.target.closest(".cel");
        if (!cel || cel !== e.target) return;
        if (S.sel !== cel.dataset.id) S.select(cel.dataset.id);
    });

    document.addEventListener("keydown", function(e) {
        if (e.ctrlKey || e.metaKey || e.altKey) return;
        if ($("page-setup-overlay").classList.contains("open")) return;
        var onItem = e.target.classList && e.target.classList.contains("cel") ? e.target : null;

        if (e.key === "Enter" && onItem) {
            e.preventDefault();
            if (S.sel !== onItem.dataset.id) S.select(onItem.dataset.id);
            if (S._collapsed.rp) $("rp-toggle").click();
            $("px").focus();
            return;
        }

        var d = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key];
        if (!d || !arrowsBelongToPage(e.target)) return;
        if (onItem && S.sel !== onItem.dataset.id) S.select(onItem.dataset.id);
        if (!S.sel) return;
        e.preventDefault();  // don't scroll the page area
        var step = stepMm(e.shiftKey);
        nudge(S.sel, d[0] * step, d[1] * step);
    });
}

S.wirePageKeys = wirePageKeys;
S.NUDGE_BIG_MM = NUDGE_BIG_MM;
})();
