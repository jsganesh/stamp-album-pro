"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast, parseDSL = S.parseDSL, updateTitle = S.updateTitle;
var pushUndo = S.pushUndo, render = S.render;

// ── File management ──
// Open an album read from a file (File › Open, Open recent or Saved albums). Starts a
// fresh undo history, then offers to move any elements past the page edge inside it.
function openAlbum(name, content) {
    if (S.hideRestoreNote) S.hideRestoreNote();
    S._currentFile = name;
    parseDSL(content);
    S._dirty = false;
    S.resetUndo();
    updateTitle();
    showToast(S.t("msg.opened", { name: name }), "success");
    if (S.checkFitOnOpen) S.checkFitOnOpen();
}

// Start a new, unnamed album from a template or the wizard. It has no file yet, so Save asks
// for a name rather than writing over the album that was open; it is Not saved until then.
// The caller has already asked about unsaved work (S.okToDiscard).
function startAlbum(content) {
    if (S.hideRestoreNote) S.hideRestoreNote();
    S._currentFile = null;
    parseDSL(content);
    S.resetUndo();
    S._dirty = true;
    updateTitle();
    S.scheduleDraftSave();
}

function saveFile() {
    var dsl = S.buildDSL();
    if (S._currentFile) {
        fetch("/files/" + encodeURIComponent(S._currentFile), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: dsl })
        }).then(function(r) {
            if (r.ok) { return r.json(); }
            throw new Error(S.t("msg.save_failed"));
        }).then(function(data) {
            S._dirty = false;
            if (S.hideRestoreNote) S.hideRestoreNote();
            S.clearDraft();
            updateTitle();
            if (S.updateStatusBar) S.updateStatusBar();
            showToast(S.t("msg.saved_to", { path: data.path || S._currentFile }), "success");
        }).catch(function() { showToast(S.t("msg.save_failed"), "error"); });
    } else {
        var name = prompt(S.t("msg.file_name"), "album.slbum");
        if (!name) return;
        if (!name.endsWith(".slbum") && !name.endsWith(".txt")) name += ".slbum";
        S._currentFile = name;
        saveFile();
    }
}

// ── Image management ──
// Images live in the StampAlbum folder's images folder; an album refers to them
// by name. The Images section lists the images the open album uses, on any page.
function uploadImageFile(file, callback) {
    var formData = new FormData();
    formData.append("file", file);
    fetch("/images", { method: "POST", body: formData })
        .then(function(r) {
            if (r.ok) return r.json();
            throw new Error(S.t("msg.upload_failed_plain"));
        })
        .then(function(data) {
            showToast(S.t("msg.attached", { name: data.filename }), "success");
            if (callback) callback(data.filename);
        })
        .catch(function(err) { showToast(S.t("msg.upload_failed", { msg: err }), "error"); });
}

// An image element for the page, sized to the picture's own shape (the longer side 40 mm).
function imageElement(imgUrl, name, natW, natH) {
    var w = 100, h = 75;  // canvas px (2.5 px/mm)
    if (natW > 0 && natH > 0) {
        if (natW >= natH) { h = Math.round(w * natH / natW); }
        else { h = 100; w = Math.round(h * natW / natH); }
    }
    // No frame, as the exports draw it: a picture prints as itself (and its caption).
    return { t: "image", s: "rectangle", w: w, h: h, lbl: name, img: imgUrl,
        bdr: "none", bdrC: "transparent", bdrW: 0, fill: "transparent", fillA: 0, font: "HN", fs: 12 };
}

// Place an image from the images folder on the current page, centred and selected.
function placeImage(name) {
    var url = "/images/" + encodeURIComponent(name);
    var probe = new Image();
    var done = false;
    function place() {
        if (done) return;
        done = true;
        S.addAtCentre(imageElement("/images/" + name, name, probe.naturalWidth, probe.naturalHeight));
    }
    probe.onload = place;
    probe.onerror = place;  // still placed, at the usual size
    probe.src = url;
}

// An image's file name, as the exports find it: the last part of the stored path.
function imageName(img) {
    return String(img || "").split("/").pop().split("\\").pop();
}

// The images the open album uses, in the order they first appear (every page).
function albumImages() {
    var seen = {}, out = [];
    S._pages.forEach(function(page, i) {
        (i === S._currentPage ? S.E : page).forEach(function(el) {
            var name = imageName(el.img);
            if (!name) return;
            if (!seen[name]) { seen[name] = true; out.push(name); }
        });
    });
    return out;
}

var _shownImages = null;
// Redraw the Images section when the album's images change (render() calls this).
function syncImageList(force) {
    var c = $("img-grid");
    if (!c) return;
    var names = albumImages(), key = names.join("\n");
    if (!force && key === _shownImages) return;
    _shownImages = key;
    c.textContent = "";
    $("img-empty").hidden = names.length > 0;
    c.hidden = names.length === 0;
    names.forEach(function(name) {
        // A tile adds another copy of the image; to take one off, delete it on the page.
        var item = document.createElement("div");
        item.className = "img-item";
        item.setAttribute("role", "listitem");
        var addBtn = document.createElement("button");
        addBtn.type = "button";
        addBtn.className = "img-add";
        addBtn.setAttribute("aria-label", S.t("msg.add_image", { name: name }));
        addBtn.title = S.t("msg.add_image_title", { name: name });
        var im = document.createElement("img");
        im.alt = "";
        im.addEventListener("error", function() {
            // The file has gone from the images folder: say so in words.
            item.classList.add("missing");
            addBtn.disabled = true;
            addBtn.setAttribute("aria-label", S.t("msg.image_not_found_name", { name: name }));
            addBtn.title = S.t("msg.image_not_found_name", { name: name });
            addBtn.textContent = "";
            var note = document.createElement("span");
            note.className = "img-missing";
            note.textContent = S.t("msg.image_not_found");
            addBtn.appendChild(note);
        });
        im.src = "/images/" + encodeURIComponent(name);
        addBtn.appendChild(im);
        addBtn.addEventListener("click", function() { placeImage(name); });
        item.appendChild(addBtn);
        c.appendChild(item);
    });
}
function loadImageList() { syncImageList(true); }

// ── Exports ──
S.openAlbum = openAlbum;
S.startAlbum = startAlbum;
S.saveFile = saveFile;
S.uploadImageFile = uploadImageFile;
S.loadImageList = loadImageList;
S.syncImageList = syncImageList;
S.placeImage = placeImage;
S.albumImages = albumImages;

})();
