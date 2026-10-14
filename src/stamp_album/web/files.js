"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast, parseDSL = S.parseDSL, updateTitle = S.updateTitle;
var pushUndo = S.pushUndo, render = S.render;

// ── File management ──
// Open an album read from a file (the Saved files list or File > Open). Starts a
// fresh undo history, then offers to move any elements past the page edge inside it.
function openAlbum(name, content) {
    S._currentFile = name;
    parseDSL(content);
    S._dirty = false;
    S.resetUndo();
    updateTitle();
    loadFileList();
    showToast(S.t("msg.opened", { name: name }), "success");
    if (S.checkFitOnOpen) S.checkFitOnOpen();
}

function loadFileList() {
    var c = $("file-list");
    if (!c) return;
    fetch("/files")
        .then(function(r) { return r.json(); })
        .then(function(files) {
            c.innerHTML = "";
            files.forEach(function(f) {
                // A row holds two buttons: the name opens the file, the cross deletes it
                var item = document.createElement("div");
                item.className = "file-item" + (f === S._currentFile ? " active" : "");
                var openBtn = document.createElement("button");
                openBtn.type = "button";
                openBtn.className = "file-open";
                openBtn.setAttribute("aria-label", S.t("msg.open_file", { name: f }));
                if (f === S._currentFile) openBtn.setAttribute("aria-current", "true");
                var icon = S.icon(f.endsWith(".slbum") ? "album" : "file");
                icon.classList.add("favicon");
                var nameSpan = document.createElement("span");
                nameSpan.className = "fn";
                nameSpan.textContent = f;
                openBtn.appendChild(icon);
                openBtn.appendChild(nameSpan);
                var delBtn = document.createElement("button");
                delBtn.type = "button";
                delBtn.className = "fdel";
                delBtn.appendChild(S.icon("x"));
                delBtn.title = S.t("msg.delete_name", { name: f });
                delBtn.setAttribute("aria-label", S.t("msg.delete_name", { name: f }));
                delBtn.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (confirm(S.t("msg.delete_confirm", { name: f }))) {
                        fetch("/files/" + encodeURIComponent(f), { method: "DELETE" })
                            .then(function() { loadFileList(); showToast(S.t("msg.deleted", { name: f }), "success"); });
                    }
                });
                item.appendChild(openBtn);
                item.appendChild(delBtn);
                openBtn.addEventListener("click", function() {
                    fetch("/files/" + encodeURIComponent(f))
                        .then(function(r) { return r.text(); })
                        .then(function(content) {
                            openAlbum(f, content);
                        });
                });
                c.appendChild(item);
            });
        })
        .catch(function() { c.innerHTML = "<div style='padding:8px;color:var(--text2);font-size:11px'></div>"; c.firstChild.textContent = S.t("msg.no_files"); });
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
function uploadImageFile(file, callback) {
    var formData = new FormData();
    formData.append("file", file);
    fetch("/images", { method: "POST", body: formData })
        .then(function(r) {
            if (r.ok) return r.json();
            throw new Error(S.t("msg.upload_failed_plain"));
        })
        .then(function(data) {
            showToast(S.t("msg.uploaded", { name: data.filename }), "success");
            if (callback) callback(data.filename);
            loadImageList();
        })
        .catch(function(err) { showToast(S.t("msg.upload_failed", { msg: err }), "error"); });
}

function loadImageList() {
    var c = $("img-grid");
    if (!c) return;
    fetch("/images")
        .then(function(r) { return r.json(); })
        .then(function(images) {
            c.innerHTML = "";
            images.forEach(function(img) {
                // A tile holds two buttons: the thumbnail adds the image, the corner one deletes it
                var item = document.createElement("div");
                item.className = "img-item";
                var addBtn = document.createElement("button");
                addBtn.type = "button";
                addBtn.className = "img-add";
                addBtn.setAttribute("aria-label", S.t("msg.add_image", { name: img }));
                addBtn.title = S.t("msg.add_image_title", { name: img });
                var im = document.createElement("img");
                im.src = "/images/" + encodeURIComponent(img);
                im.alt = "";
                addBtn.appendChild(im);
                var del = document.createElement("button");
                del.type = "button";
                del.className = "img-del";
                del.appendChild(S.icon("x"));
                del.setAttribute("aria-label", S.t("msg.delete_image", { name: img }));
                del.title = S.t("msg.delete_name", { name: img });
                del.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (confirm(S.t("msg.delete_confirm", { name: img }))) {
                        fetch("/images/" + encodeURIComponent(img), { method: "DELETE" })
                            .then(function() { loadImageList(); showToast(S.t("msg.deleted", { name: img }), "success"); });
                    }
                });
                item.appendChild(addBtn);
                item.appendChild(del);
                addBtn.addEventListener("click", function() {
                    S.addAtCentre({ t: "image", s: "rectangle", w: 80, h: 60,
                        lbl: img, img: "/images/" + img,
                        bdr: "solid", bdrC: "#999", bdrW: 0.5, fill: "#fff", fillA: 100, font: "HN", fs: 12 });
                });
                c.appendChild(item);
            });
        })
        .catch(function() {
            c.innerHTML = "<div style='padding:8px;color:var(--text2);font-size:11px'></div>"; c.firstChild.textContent = S.t("msg.no_images");
        });
}

// ── Exports ──
S.loadFileList = loadFileList;
S.openAlbum = openAlbum;
S.saveFile = saveFile;
S.uploadImageFile = uploadImageFile;
S.loadImageList = loadImageList;

})();
