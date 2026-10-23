"use strict";
(function(){
var S = window.StampAlbum, $ = S.$;

// ── The phone layout (UI review item 7) ──
// At phone width a bar along the bottom has Add, Undo, Properties and Page. Add, Properties
// and Page open a sheet from the bottom that holds the panel they stand for: the panel's own
// part is moved into the sheet while it is open and put back when it closes, so every field
// keeps its id, its handlers and its place on a computer. Undo acts at once. Properties opens
// only from its button (owner's choice), and Page also holds the pages, so the page strip
// leaves the screen; with more than one page a small pager floats over the page.

var PHONE = "(max-width: 600px)";
var KINDS = {
    add:   { btn: "pb-add",   parts: ["sb-body"],             title: function() { return S.t("ui.add_to_the_page"); } },
    props: { btn: "pb-props", parts: ["rp-content"],          title: function() { return $("rp-title").textContent; }, acts: true },
    page:  { btn: "pb-page",  parts: ["pg-strip", "rp-none"], title: function() { return S.t("ui.pages_and_album"); } }
};
var _kind = null, _opener = null, _homes = [];

function isPhone() { return !!(window.matchMedia && window.matchMedia(PHONE).matches); }
function hasSel() { return !!(S.sel && S.E && S.E.some(function(x) { return x.id === S.sel; })); }
function canUndo() { return !!(S._undoStack && S._undoStack.length >= 2); }

function openSheet(kind) {
    if (_kind === kind) { closeSheet(); return; }
    if (_kind) closeSheet(true);
    var k = KINDS[kind], body = $("sheet-body");
    _kind = kind;
    _opener = $(k.btn);
    k.parts.forEach(function(id) {
        var el = $(id), mark = document.createComment(" " + id + " ");
        el.parentNode.insertBefore(mark, el);
        _homes.push([el, mark]);
        body.appendChild(el);
    });
    $("sheet-acts").hidden = !k.acts;
    $("sheet").setAttribute("data-kind", kind);
    $("sheet-title").textContent = k.title();
    // The sheet rises from just above the bar, which stays in view to change sheet or undo.
    var above = $("phone-bar").getBoundingClientRect().height + "px";
    $("sheet").style.bottom = above;
    $("sheet-scrim").style.bottom = above;
    $("sheet").hidden = false;
    $("sheet-scrim").hidden = false;
    _opener.setAttribute("aria-expanded", "true");
    body.scrollTop = 0;
    $("sheet-title").focus();
}

// Put the panels back where they live. quiet: leave the focus where it is.
function closeSheet(quiet) {
    if (!_kind) return;
    if (S.commitPanelEdit) S.commitPanelEdit();  // the Properties sheet's edit, before it closes
    _homes.forEach(function(h) { h[1].parentNode.insertBefore(h[0], h[1]); h[1].remove(); });
    _homes = [];
    $("sheet").hidden = true;
    $("sheet-scrim").hidden = true;
    $("sheet").removeAttribute("data-kind");
    var b = _opener;
    _kind = null;
    _opener = null;
    if (b) {
        b.setAttribute("aria-expanded", "false");
        if (!quiet && isPhone()) b.focus();
    }
}

// The bar's states, the pager and the sheet's title, after anything that may change them.
function sync() {
    if (!$("pb-undo")) return;
    $("pb-undo").setAttribute("aria-disabled", canUndo() ? "false" : "true");
    $("pb-props").setAttribute("aria-disabled", hasSel() ? "false" : "true");
    var n = S._pages ? S._pages.length : 1, i = S._currentPage || 0;
    $("pb-page-lbl").textContent = n > 1 ? S.t("ui.page_n", { n: i + 1 }) : S.t("ui.page");
    $("pg-pager").hidden = n < 2;
    $("pg-pager-label").textContent = S.t("msg.page_n_of", { n: i + 1, total: n });
    $("pg-pager-prev").disabled = i === 0;
    $("pg-pager-next").disabled = i >= n - 1;
    if (_kind === "props" && !hasSel()) closeSheet();
    else if (_kind) $("sheet-title").textContent = KINDS[_kind].title();
}

function after(name) {
    var orig = S[name];
    if (typeof orig !== "function") return;
    S[name] = function() {
        var r = orig.apply(this, arguments);
        sync();
        return r;
    };
}
["render", "select", "updateSelectionUI"].forEach(after);  // the page strip calls sync itself

// An item added from the Add sheet: back to the page to drag it into place.
var _add = S.add;
S.add = function(p) {
    var r = _add.apply(this, arguments);
    if (_kind === "add") {
        closeSheet();
        S.showToast(S.t("msg.added_drag_it"), "info");
    }
    return r;
};

function wire() {
    $("pb-add").addEventListener("click", function() { openSheet("add"); });
    $("pb-page").addEventListener("click", function() { openSheet("page"); });
    $("pb-props").addEventListener("click", function() {
        if (!hasSel()) {
            closeSheet(true);
            S.showToast(S.t("msg.tap_an_item_first"), "info");
            return;
        }
        openSheet("props");
    });
    $("pb-undo").addEventListener("click", function() {
        if (!canUndo()) { S.showToast(S.t("msg.nothing_to_undo"), "info"); return; }
        S.undo();
        sync();
    });
    $("sheet-close").addEventListener("click", function() { closeSheet(); });
    $("sheet-scrim").addEventListener("click", function() { closeSheet(); });
    $("sheet-dup").addEventListener("click", function() { $("btn-dup").click(); });
    $("sheet-del").addEventListener("click", function() { $("btn-del").click(); });

    // The Page sheet: going to a page, or adding one, shows that page.
    $("pg-list").addEventListener("click", function(e) {
        if (_kind === "page" && e.target.closest(".pg-thumb")) closeSheet();
    });
    $("pg-add").addEventListener("click", function() {
        if (_kind !== "page") return;
        closeSheet();  // the new page is open, with its own "Page added" message
    });
    $("pg-pager-prev").addEventListener("click", function() {
        if (S._currentPage > 0) S.switchPage(S._currentPage - 1);
    });
    $("pg-pager-next").addEventListener("click", function() {
        if (S._currentPage < S._pages.length - 1) S.switchPage(S._currentPage + 1);
    });

    // Escape closes the sheet first (not a menu or dialog of its own on top of it).
    document.addEventListener("keydown", function(e) {
        if (!_kind || e.key !== "Escape") return;
        if (!$("pg-menu").hidden) return;
        var a = document.activeElement;
        if (a && a !== document.body && !$("sheet").contains(a) && a !== _opener) return;
        e.preventDefault();
        e.stopImmediatePropagation();
        closeSheet();
    }, true);
    // Tab stays within the open sheet.
    $("sheet").addEventListener("keydown", function(e) {
        if (e.key !== "Tab") return;
        var all = [].filter.call($("sheet").querySelectorAll(
            "button, input, select, textarea, [tabindex]:not([tabindex='-1'])"),
            function(x) { return !x.disabled && x.getClientRects().length > 0; });
        if (!all.length) return;
        var first = all[0], last = all[all.length - 1];
        if (e.shiftKey && (document.activeElement === first || document.activeElement === $("sheet-title"))) {
            e.preventDefault(); last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault(); first.focus();
        }
    });
    // A wider window has the panels back.
    if (window.matchMedia) {
        var mq = window.matchMedia(PHONE), shut = function(e) { if (!e.matches) closeSheet(true); };
        if (mq.addEventListener) mq.addEventListener("change", shut);
        else if (mq.addListener) mq.addListener(shut);
    }
    sync();
}

wire();

S.openSheet = openSheet;
S.closeSheet = closeSheet;
S.syncPhoneBar = sync;
Object.defineProperty(S, "sheetKind", { get: function() { return _kind; } });
})();
