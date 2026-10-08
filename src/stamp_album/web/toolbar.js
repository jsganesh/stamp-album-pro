"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$;

// ── Toolbar: File / Edit / View menus, selection tools, checkbox states ──

var IS_MAC = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || "");
var MENUS = ["file", "edit", "view"];
var _open = null, _hoverOpened = null;

function menuBtn(name) { return $("menu-" + name + "-btn"); }
function menuList(name) { return $("menu-" + name); }
function items(name) {
    return Array.prototype.slice.call(menuList(name).querySelectorAll(".mi")).filter(function(b) { return !b.disabled; });
}

function openMenu(name, focusFirst) {
    if (_open && _open !== name) closeMenu();
    syncMenuState();
    menuList(name).hidden = false;
    menuBtn(name).setAttribute("aria-expanded", "true");
    _open = name;
    if (focusFirst) { var it = items(name); if (it.length) it[0].focus(); }
}
function closeMenu(returnFocus) {
    if (!_open) return;
    var name = _open;
    menuList(name).hidden = true;
    menuBtn(name).setAttribute("aria-expanded", "false");
    _open = null;
    if (returnFocus) menuBtn(name).focus();
}

// Run a menu item's action after closing the menu, so dialogs it opens get focus.
function onItem(id, fn) {
    var b = $(id);
    if (b) b.addEventListener("click", function(e) { closeMenu(); fn.call(this, e); });
}

// Enabled and checked states that depend on the album; refreshed on every open.
function syncMenuState() {
    var hasSel = !!S.sel;
    ["menu-dup", "menu-grid", "menu-del"].forEach(function(id) { $(id).disabled = !hasSel; });
    $("menu-undo").disabled = S._undoStack.length < 2;
    $("menu-redo").disabled = S._redoStack.length === 0;
    $("menu-del-page").disabled = S._pages.length <= 1;
    $("btn-snap").setAttribute("aria-checked", S._snapEnabled ? "true" : "false");
    $("btn-large-text").setAttribute("aria-checked", document.body.classList.contains("large-text") ? "true" : "false");
}

// Selected-stamp tools replace the page defaults in the page bar.
function updateSelectionUI() {
    var hasSel = !!(S.sel && S.E.some(function(x) { return x.id === S.sel; }));
    var tools = $("sel-tools"), defs = $("page-defaults");
    if (tools) tools.hidden = !hasSel;
    if (defs) defs.hidden = hasSel;
    $("btn-undo").disabled = S._undoStack.length < 2;
    $("btn-redo").disabled = S._redoStack.length === 0;
}

// Shortcut labels are written Mac-style; show Ctrl/Shift elsewhere.
function localiseShortcuts() {
    if (IS_MAC) return;
    document.querySelectorAll("#tb .mk, #tb [title]").forEach(function(el) {
        var attr = el.classList.contains("mk") ? null : "title";
        var v = attr ? el.getAttribute(attr) : el.textContent;
        if (v.indexOf("⌘") === -1 && v.indexOf("⇧") === -1) return;
        v = v.replace(/⇧⌘(\w)/g, "Ctrl+Shift+$1").replace(/⌘(\w)/g, "Ctrl+$1");
        if (attr) el.setAttribute(attr, v); else el.textContent = v;
    });
}

function wireToolbar() {
    MENUS.forEach(function(name) {
        var btn = menuBtn(name);
        btn.addEventListener("click", function() {
            // A menu opened by hovering across the bar stays open when the click lands.
            if (_hoverOpened === name) { _hoverOpened = null; return; }
            if (_open === name) closeMenu(); else openMenu(name, false);
        });
        btn.addEventListener("keydown", function(e) {
            if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") { e.preventDefault(); openMenu(name, true); }
        });
        // Hovering across the bar while a menu is open switches menus, like a desktop menu bar.
        btn.addEventListener("mouseenter", function() {
            if (_open && _open !== name) { openMenu(name, false); _hoverOpened = name; }
        });
        btn.addEventListener("mouseleave", function() { if (_hoverOpened === name) _hoverOpened = null; });
        menuList(name).addEventListener("keydown", function(e) {
            var it = items(name), i = it.indexOf(document.activeElement);
            if (e.key === "ArrowDown") { e.preventDefault(); it[(i + 1) % it.length].focus(); }
            else if (e.key === "ArrowUp") { e.preventDefault(); it[(i - 1 + it.length) % it.length].focus(); }
            else if (e.key === "Home") { e.preventDefault(); it[0].focus(); }
            else if (e.key === "End") { e.preventDefault(); it[it.length - 1].focus(); }
            else if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
                e.preventDefault();
                var next = MENUS[(MENUS.indexOf(name) + (e.key === "ArrowRight" ? 1 : MENUS.length - 1)) % MENUS.length];
                openMenu(next, true);
            }
            else if (e.key === "Tab") { closeMenu(); }
        });
    });
    // Escape closes the open menu; this runs before the editor's own shortcuts.
    document.addEventListener("keydown", function(e) {
        if (_open && e.key === "Escape") { e.preventDefault(); e.stopImmediatePropagation(); closeMenu(true); }
    }, true);
    document.addEventListener("mousedown", function(e) {
        if (_open && !e.target.closest(".tb-menu")) closeMenu();
    });

    // File
    onItem("btn-new", function() { S.newAlbum(); });
    onItem("btn-wizard", function() { $("wizard-panel").classList.add("open"); var t = $("wiz-title"); if (t) t.focus(); });
    onItem("menu-template", function() { $("btn-wiz-template").click(); });
    onItem("btn-open", function() { $("file-inp").click(); });
    onItem("btn-save", function() { S.saveFile(); });
    onItem("menu-page-setup", function() { S.openPageSetup(); });
    ["pdf", "png", "svg", "html"].forEach(function(fmt) {
        onItem("menu-export-" + fmt, function() { if (S.exportFormat) S.exportFormat(fmt); });
    });
    // Edit
    onItem("menu-undo", function() { S.undo(); });
    onItem("menu-redo", function() { S.redo(); });
    onItem("menu-dup", function() { $("btn-dup").click(); });
    onItem("menu-grid", function() { $("btn-grid").click(); });
    onItem("menu-del", function() { $("btn-del").click(); });
    onItem("menu-add-page", function() { S.addPage(); });
    onItem("menu-del-page", function() { S.deletePage(); });
    // View (btn-dsl keeps its handler in init.js)
    onItem("menu-preview", function() { S.openPreview(); });
    onItem("btn-snap", function() { S.toggleSnap(); });
    onItem("btn-large-text", function() { S.toggleLargeText(); });
    onItem("menu-tutorial", function() { if (S.showTutorial) S.showTutorial(); });
    onItem("btn-help", function() { $("help-overlay").classList.add("open"); });
    onItem("btn-reset", function() { S.resetApp(); });
    $("btn-help-tb").addEventListener("click", function() { $("help-overlay").classList.add("open"); });
    ["btn-dsl"].forEach(function(id) { $(id).addEventListener("click", function() { closeMenu(); }); });

    // Phone width: start with the side panels collapsed so the page has room;
    // their handles open them again.
    if (window.innerWidth <= 600) {
        if (!S._collapsed.sb) $("sb-toggle").click();
        if (!S._collapsed.rp) $("rp-toggle").click();
    }

    localiseShortcuts();
    updateSelectionUI();
}

// ── Exports ──
S.wireToolbar = wireToolbar;
S.updateSelectionUI = updateSelectionUI;
S.closeMenu = closeMenu;

})();
