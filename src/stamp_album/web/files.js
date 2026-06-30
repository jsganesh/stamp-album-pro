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
                var item = document.createElement("div");
                item.className = "file-item" + (f === S._currentFile ? " active" : "");
                var icon = document.createElement("span");
                icon.className = "favicon";
                icon.textContent = f.endsWith(".slbum") ? "📖" : "📄";
                var nameSpan = document.createElement("span");
                nameSpan.className = "fn";
                nameSpan.textContent = f;
                var delBtn = document.createElement("span");
                delBtn.className = "fdel";
                delBtn.textContent = "✕";
                delBtn.title = "Delete";
                delBtn.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (confirm("Delete " + f + "?")) {
                        fetch("/files/" + encodeURIComponent(f), { method: "DELETE" })
                            .then(function() { loadFileList(); showToast("Deleted " + f, "success"); });
                    }
                });
                item.appendChild(icon);
                item.appendChild(nameSpan);
                item.appendChild(delBtn);
                item.addEventListener("click", function() {
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
                var item = document.createElement("div");
                item.className = "img-item";
                var im = document.createElement("img");
                im.src = "/images/" + encodeURIComponent(img);
                var del = document.createElement("button");
                del.className = "img-del";
                del.textContent = "✕";
                del.addEventListener("click", function(ev) {
                    ev.stopPropagation();
                    if (confirm("Delete " + img + "?")) {
                        fetch("/images/" + encodeURIComponent(img), { method: "DELETE" })
                            .then(function() { loadImageList(); showToast("Deleted " + img, "success"); });
                    }
                });
                item.appendChild(im);
                item.appendChild(del);
                item.addEventListener("click", function() {
                    S.add({ t: "image", s: "rectangle", x: 50, y: 50, w: 80, h: 60,
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
