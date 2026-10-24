"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$;

// ── Toolbar: File / Edit / View / Help menus, selection tools, checkbox states ──

var IS_MAC = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || "");
var MENUS = ["file", "edit", "view", "help"];
var _open = null, _hoverOpened = null, _recentOpen = false;

function menuBtn(name) { return $("menu-" + name + "-btn"); }
function menuList(name) { return $("menu-" + name); }
function items(name) {
    // The menu's own items; those in a submenu (Open recent) are reached from it.
    return Array.prototype.slice.call(menuList(name).querySelectorAll(".mi")).filter(function(b) {
        return !b.disabled && !b.closest(".tb-submenu");
    });
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
    closeRecent();
    if (!_open) return;
    var name = _open;
    menuList(name).hidden = true;
    menuBtn(name).setAttribute("aria-expanded", "false");
    _open = null;
    if (returnFocus) menuBtn(name).focus();
}

// ── File › Open recent: a submenu, filled with the newest albums each time it opens ──
function recentItems() {
    return Array.prototype.slice.call($("menu-recent-list").querySelectorAll(".mi")).filter(function(b) { return !b.disabled; });
}
function openRecent(focusFirst) {
    var list = $("menu-recent-list");
    _recentOpen = true;
    $("menu-recent").setAttribute("aria-expanded", "true");
    list.hidden = false;
    S.fillRecent(list, function() {
        if (!_recentOpen) return;
        if (focusFirst) { var it = recentItems(); (it[0] || $("menu-recent")).focus(); }
    });
}
function closeRecent(returnFocus) {
    if (!_recentOpen) return;
    _recentOpen = false;
    $("menu-recent").setAttribute("aria-expanded", "false");
    $("menu-recent-list").hidden = true;
    if (returnFocus) $("menu-recent").focus();
}
function wireRecent() {
    var btn = $("menu-recent"), list = $("menu-recent-list");
    // A click toggles it, except the click that ends the hover which just opened it.
    var hoverOpened = false;
    btn.addEventListener("click", function() {
        if (hoverOpened) { hoverOpened = false; return; }
        if (_recentOpen) closeRecent(); else openRecent(false);
    });
    btn.addEventListener("mouseenter", function() {
        if (!_recentOpen) { openRecent(false); hoverOpened = true; }
    });
    btn.addEventListener("mouseleave", function() { hoverOpened = false; });
    btn.addEventListener("keydown", function(e) {
        if (e.key === "ArrowRight" || e.key === "Enter" || e.key === " ") {
            e.preventDefault(); e.stopPropagation(); openRecent(true);
        }
    });
    // Moving to another File item closes the submenu.
    menuList("file").querySelectorAll(".mi").forEach(function(b) {
        if (b === btn || b.closest(".tb-submenu")) return;
        b.addEventListener("mouseenter", function() { closeRecent(); });
        b.addEventListener("focus", function() { closeRecent(); });
    });
    list.addEventListener("keydown", function(e) {
        var it = recentItems(), i = it.indexOf(document.activeElement);
        if (e.key === "ArrowDown" && it.length) { e.preventDefault(); it[(i + 1) % it.length].focus(); }
        else if (e.key === "ArrowUp" && it.length) { e.preventDefault(); it[(i - 1 + it.length) % it.length].focus(); }
        else if (e.key === "Home" && it.length) { e.preventDefault(); it[0].focus(); }
        else if (e.key === "End" && it.length) { e.preventDefault(); it[it.length - 1].focus(); }
        else if (e.key === "ArrowLeft") { e.preventDefault(); closeRecent(true); }
        else if (e.key === "Tab") { closeMenu(); return; }
        else return;
        e.stopPropagation();
    });
}

// Run a menu item's action after closing the menu, so dialogs it opens get focus.
function onItem(id, fn, el) {
    var b = el || $(id);
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
    ["standard", "large", "xlarge"].forEach(function(k) {
        var it = $("menu-text-" + k);
        if (it) it.setAttribute("aria-checked", Number(it.dataset.size) === S.textSize ? "true" : "false");
    });
}

// The selected item's tools show in the page bar beside the pages.
function updateSelectionUI() {
    var hasSel = !!(S.sel && S.E.some(function(x) { return x.id === S.sel; }));
    var tools = $("sel-tools");
    if (tools) tools.hidden = !hasSel;
    $("btn-undo").disabled = S._undoStack.length < 2;
    $("btn-redo").disabled = S._redoStack.length === 0;
}

// View › Language: shown once there is more than one language. A choice is
// remembered on this device and takes effect at once; the album is untouched.
function buildLanguageMenu() {
    var I18n = window.StampAlbumI18n, group = $("menu-lang");
    if (!I18n || !group) return;
    var langs = I18n.available();
    group.textContent = "";
    group.hidden = $("menu-lang-sep").hidden = langs.length < 2;
    if (langs.length < 2) return;
    langs.forEach(function(lang) {
        var b = document.createElement("button");
        b.className = "mi";
        b.id = "menu-lang-" + lang;
        b.setAttribute("role", "menuitemradio");
        b.setAttribute("lang", lang);
        b.setAttribute("aria-checked", lang === I18n.language() ? "true" : "false");
        var mark = document.createElement("span");
        mark.className = "mcheck";
        mark.setAttribute("aria-hidden", "true");
        b.appendChild(mark);
        b.appendChild(document.createTextNode(I18n.nativeName(lang)));
        onItem(b.id, function() { chooseLanguage(lang); }, b);
        group.appendChild(b);
    });
}
function chooseLanguage(lang) {
    var I18n = window.StampAlbumI18n;
    if (lang === I18n.language()) return;
    I18n.setLanguage(lang, true);  // the page's own words
    localiseShortcuts();            // they came back Mac-style
    buildLanguageMenu();
    S.refreshLanguage();            // the words the scripts wrote
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
    // In Open recent it closes the submenu only.
    document.addEventListener("keydown", function(e) {
        if (!_open || e.key !== "Escape") return;
        e.preventDefault(); e.stopImmediatePropagation();
        if (_recentOpen) closeRecent(true); else closeMenu(true);
    }, true);
    document.addEventListener("mousedown", function(e) {
        if (_open && !e.target.closest(".tb-menu")) closeMenu();
    });

    // File
    onItem("btn-new", function() { S.newAlbum(); });
    onItem("btn-wizard", function() { $("wizard-panel").classList.add("open"); var t = $("wiz-title"); if (t) t.focus(); });
    onItem("menu-template", function() { $("btn-wiz-template").click(); });
    onItem("btn-open", function() { if (S.okToDiscard()) $("file-inp").click(); });
    wireRecent();
    onItem("menu-manage", function() { S.openManageAlbums(); });
    onItem("btn-save", function() { S.saveFile(); });
    onItem("menu-page-setup", function() { S.openPageSetup(); });
    onItem("menu-exhibit-plan", function() { S.openExhibitPlan(); });
    onItem("menu-check", function() { S.openCheck(); });
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
    ["standard", "large", "xlarge"].forEach(function(k) {
        onItem("menu-text-" + k, function() { S.setTextSize($("menu-text-" + k).dataset.size); });
    });
    ["fit-width", "fit-page", "actual"].forEach(function(m) {
        onItem("menu-zoom-" + m, function() { S.setZoomMode(m); });
    });
    onItem("menu-zoom-in", function() { S.zoomStep(1); });
    onItem("menu-zoom-out", function() { S.zoomStep(-1); });
    onItem("btn-reset", function() { S.resetApp(); });
    // Help
    onItem("menu-tutorial", function() { if (S.showTutorial) S.showTutorial(); });
    onItem("btn-help", function() { $("help-overlay").classList.add("open"); });
    onItem("menu-calibration", function() { S.openCalibration(); });
    ["btn-dsl"].forEach(function(id) { $(id).addEventListener("click", function() { closeMenu(); }); });

    // Phone width: start with the side panels collapsed so the page has room;
    // their handles open them again.
    if (window.innerWidth <= 600) {
        if (!S._collapsed.sb) $("sb-toggle").click();
        if (!S._collapsed.rp) $("rp-toggle").click();
    }

    buildLanguageMenu();
    localiseShortcuts();
    updateSelectionUI();
}

// ── Exports ──
S.wireToolbar = wireToolbar;
S.updateSelectionUI = updateSelectionUI;
S.closeMenu = closeMenu;

})();
