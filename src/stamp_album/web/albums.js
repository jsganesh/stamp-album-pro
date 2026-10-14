"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast;

// ── Saved albums: File › Open recent and File › Manage saved albums… ──
// Both list the albums saved in the StampAlbum folder, newest first. Opening one
// asks first when the open album has unsaved changes.

var RECENT_LIMIT = 10;
var _returnFocus = null;

// True when the open album may be replaced: nothing unsaved, or the person agrees.
function okToDiscard() {
    return !S._dirty || confirm(S.t("msg.discard_unsaved"));
}

// An album's name as shown: the file name without ".slbum".
function displayName(file) {
    return file.replace(/\.slbum$/i, "");
}

function fetchAlbums(limit) {
    return fetch("/files?sort=recent" + (limit ? "&limit=" + limit : ""))
        .then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); });
}

// Open a saved album by its file name.
function openSaved(file) {
    if (!okToDiscard()) return Promise.resolve(false);
    return fetch("/files/" + encodeURIComponent(file))
        .then(function(r) { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then(function(content) { S.openAlbum(file, content); return true; })
        .catch(function() { showToast(S.t("msg.open_failed", { name: displayName(file) }), "error"); return false; });
}

// ── Open recent (a submenu of File; toolbar.js opens and closes it) ──
// Fills the submenu; calls done() once its items are in place.
function fillRecent(list, done) {
    fetchAlbums(RECENT_LIMIT).then(function(files) {
        list.textContent = "";
        if (!files.length) {
            var none = document.createElement("button");
            none.className = "mi";
            none.setAttribute("role", "menuitem");
            none.disabled = true;
            none.textContent = S.t("msg.no_saved_albums");
            list.appendChild(none);
        }
        files.forEach(function(f) {
            var b = document.createElement("button");
            b.className = "mi";
            b.setAttribute("role", "menuitem");
            b.dataset.file = f;
            b.textContent = displayName(f);
            if (f === S._currentFile) b.setAttribute("aria-current", "true");
            b.addEventListener("click", function() {
                if (S.closeMenu) S.closeMenu();
                openSaved(f);
            });
            list.appendChild(b);
        });
        if (done) done();
    }).catch(function() {
        list.textContent = "";
        if (done) done();
    });
}

// ── Manage saved albums… (a dialog to open or delete them) ──
function isOpen() { return $("albums-overlay").classList.contains("open"); }

function close() {
    $("albums-overlay").classList.remove("open");
    if (_returnFocus && _returnFocus.focus) _returnFocus.focus();
    _returnFocus = null;
}

function fillDialog(focusFirst) {
    var ul = $("alb-list");
    return fetchAlbums(0).then(function(files) {
        ul.textContent = "";
        if (!files.length) {
            var li = document.createElement("li");
            li.className = "alb-none";
            li.textContent = S.t("msg.no_saved_albums");
            ul.appendChild(li);
        }
        files.forEach(function(f) {
            var li = document.createElement("li");
            li.className = "alb-row";
            if (f === S._currentFile) li.classList.add("current");
            var name = document.createElement("span");
            name.className = "alb-name";
            name.textContent = displayName(f);
            var open = document.createElement("button");
            open.type = "button";
            open.className = "alb-open";
            open.textContent = S.t("msg.open_album");
            open.setAttribute("aria-label", S.t("msg.open_file", { name: displayName(f) }));
            open.addEventListener("click", function() {
                openSaved(f).then(function(ok) { if (ok) close(); });
            });
            var del = document.createElement("button");
            del.type = "button";
            del.className = "alb-del";
            del.textContent = S.t("msg.delete_album");
            del.setAttribute("aria-label", S.t("msg.delete_name", { name: displayName(f) }));
            del.addEventListener("click", function() { deleteSaved(f); });
            li.appendChild(name);
            li.appendChild(open);
            li.appendChild(del);
            ul.appendChild(li);
        });
        if (focusFirst) {
            var first = ul.querySelector("button") || $("alb-done");
            first.focus();
        }
    }).catch(function() { showToast(S.t("msg.list_failed"), "error"); });
}

function deleteSaved(f) {
    if (!confirm(S.t("msg.delete_confirm", { name: displayName(f) }))) return;
    fetch("/files/" + encodeURIComponent(f), { method: "DELETE" })
        .then(function(r) {
            if (!r.ok) throw new Error(r.status);
            if (f === S._currentFile) {
                // The open album stays on screen, now with no file behind it.
                S._currentFile = null;
                S._dirty = true;
                S.updateTitle();
            }
            showToast(S.t("msg.deleted", { name: displayName(f) }), "success");
            fillDialog(true);
        })
        .catch(function() { showToast(S.t("msg.delete_failed", { name: displayName(f) }), "error"); });
}

function openManage() {
    _returnFocus = document.activeElement;
    $("albums-overlay").classList.add("open");
    $("alb-done").focus();
    fillDialog(true);
}

function focusables() {
    return Array.prototype.slice.call($("albums-overlay").querySelectorAll("button:not([disabled])"));
}

function wireAlbums() {
    $("alb-close").addEventListener("click", close);
    $("alb-done").addEventListener("click", close);
    $("albums-overlay").addEventListener("mousedown", function(e) { if (e.target === this) close(); });
    $("albums-overlay").addEventListener("keydown", function(e) {
        if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); }
        else if (e.key === "Tab") {
            // Keep focus inside the dialog while it is open.
            var f = focusables(), i = f.indexOf(document.activeElement);
            if (!f.length) return;
            if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
            else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); }
        }
    });
}

// ── Exports ──
S.okToDiscard = okToDiscard;
S.openSaved = openSaved;
S.fillRecent = fillRecent;
S.openManageAlbums = openManage;
S.albumsDialogOpen = isOpen;
S.wireAlbums = wireAlbums;

})();
