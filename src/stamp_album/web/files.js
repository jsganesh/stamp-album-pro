"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast, parseDSL = S.parseDSL, updateTitle = S.updateTitle;
var pushUndo = S.pushUndo, render = S.render;

// ── File management ──
function loadFileList() {
    var c = $("file-list");
    if (!c) return;
    fetch("/files")
        .then(function(r) { return r.json(); })
        .then(function(files) {
            c.innerHTML = "";
            files.forEach(function(f) {
                // A row holds two buttons: the name opens the file, the ✕ deletes it
                var item = document.createElement("div");
                item.className = "file-item" + (f === S._currentFile ? " active" : "");
                var openBtn = document.createElement("button");
                openBtn.type = "button";
                openBtn.className = "file-open";
                openBtn.setAttribute("aria-label", "Open " + f);
                if (f === S._currentFile) openBtn.setAttribute("aria-current", "true");
                var icon = document.createElement("span");
                icon.className = "favicon";
                icon.setAttribute("aria-hidden", "true");
                icon.textContent = f.endsWith(".slbum") ? "📖" : "📄";
                var nameSpan = document.createElement("span");
                nameSpan.className = "fn";
                nameSpan.textContent = f;
                openBtn.appendChild(icon);
                openBtn.appendChild(nameSpan);
                var delBtn = document.createElement("button");
                delBtn.type = "button";
                delBtn.className = "fdel";
                delBtn.textContent = "✕";
                delBtn.title = "Delete " + f;
                delBtn.setAttribute("aria-label", "Delete " + f);
                delBtn.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (confirm("Delete " + f + "?")) {
                        fetch("/files/" + encodeURIComponent(f), { method: "DELETE" })
                            .then(function() { loadFileList(); showToast("Deleted " + f, "success"); });
                    }
                });
                item.appendChild(openBtn);
                item.appendChild(delBtn);
                openBtn.addEventListener("click", function() {
                    fetch("/files/" + encodeURIComponent(f))
                        .then(function(r) { return r.text(); })
                        .then(function(content) {
                            S._currentFile = f;
                            parseDSL(content);
                            S._dirty = false;
                            updateTitle();
                            loadFileList();
                            showToast("Opened " + f, "success");
                        });
                });
                c.appendChild(item);
            });
        })
        .catch(function() { c.innerHTML = "<div style='padding:8px;color:var(--text2);font-size:11px'>No files yet</div>"; });
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
            throw new Error("Save failed");
        }).then(function(data) {
            S._dirty = false;
            S.clearDraft();
            updateTitle();
            if (S.updateStatusBar) S.updateStatusBar();
            showToast("Saved to " + (data.path || S._currentFile), "success");
        }).catch(function() { showToast("Save failed", "error"); });
    } else {
        var name = prompt("File name:", "album.slbum");
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
            throw new Error("Upload failed");
        })
        .then(function(data) {
            showToast("Uploaded " + data.filename, "success");
            if (callback) callback(data.filename);
            loadImageList();
        })
        .catch(function(err) { showToast("Upload failed: " + err, "error"); });
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
                addBtn.setAttribute("aria-label", "Add image " + img);
                addBtn.title = "Click to add " + img + " at the page centre";
                var im = document.createElement("img");
                im.src = "/images/" + encodeURIComponent(img);
                im.alt = "";
                addBtn.appendChild(im);
                var del = document.createElement("button");
                del.type = "button";
                del.className = "img-del";
                del.textContent = "✕";
                del.setAttribute("aria-label", "Delete image " + img);
                del.title = "Delete " + img;
                del.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (confirm("Delete " + img + "?")) {
                        fetch("/images/" + encodeURIComponent(img), { method: "DELETE" })
                            .then(function() { loadImageList(); showToast("Deleted " + img, "success"); });
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
            c.innerHTML = "<div style='padding:8px;color:var(--text2);font-size:11px'>No images yet</div>";
        });
}

// ── Exports ──
S.loadFileList = loadFileList;
S.saveFile = saveFile;
S.uploadImageFile = uploadImageFile;
S.loadImageList = loadImageList;

})();
