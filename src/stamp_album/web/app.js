"use strict";
(function(){
var E = [], sel = null, nid = 1, _sc = 2.5, _sn = 5, _pw = 595, _ph = 842, _init = false;
var _drg = false, _dragEl = null, _dragH = null, _ds = {};
var _defBdr = "solid", _defBdrC = "#666", _defFillC = "#fff";
var _collapsed = { sb: false, rp: false };
var _currentFile = null, _currentPage = 0, _pages = [ [] ];
var _dirty = false;
var _colMode = 1, _colGap = 10.0, _pageBorder = "double", _pageBorderC = "";  // Column layout mode, gap (mm), page border style

// ── Forward references (set by render.js after load) ──
var render = function() { S.render(); };
var updateProps = function() { S.updateProps(); };

// ── Undo/redo system ──
var _undoStack = [], _redoStack = [], _undoMax = 50, _undoPaused = false;
function pushUndo() {
    if (_undoPaused) return;
    _undoStack.push(JSON.stringify(E));
    if (_undoStack.length > _undoMax) _undoStack.shift();
    _redoStack = [];
    _dirty = true;
    updateTitle();
    scheduleDraftSave();
}
function undo() {
    if (_undoStack.length < 2) return;
    _redoStack.push(_undoStack.pop());
    var state = JSON.parse(_undoStack.pop());
    loadElements(state);
    updateTitle();
}
function redo() {
    if (_redoStack.length === 0) return;
    _undoStack.push(JSON.stringify(E));
    var state = JSON.parse(_redoStack.pop());
    loadElements(state);
    updateTitle();
}
function loadElements(arr) { E = arr; sel = null; switchPage(_currentPage, true); render(); updateProps(); }
function loadElementsNoPush(arr) { _undoPaused = true; loadElements(arr); _undoPaused = false; }

// ── localStorage draft persistence ──
var _draftTimer = null;
var _draftKey = "stampalbum.draft";
var _draftFileKey = "stampalbum.currentFile";
var _draftDebounceMs = 500;

function saveDraft() {
    try {
        var state = { v: 1, pages: _pages, currentPage: _currentPage, elements: E };
        localStorage.setItem(_draftKey, JSON.stringify(state));
        if (_currentFile) localStorage.setItem(_draftFileKey, _currentFile);
        else localStorage.removeItem(_draftFileKey);
    } catch (_) { /* quota exceeded — silent */ }
}
function scheduleDraftSave() {
    if (_draftTimer) clearTimeout(_draftTimer);
    _draftTimer = setTimeout(function() { _draftTimer = null; saveDraft(); }, _draftDebounceMs);
}
function loadDraft() {
    try {
        var raw = localStorage.getItem(_draftKey);
        if (!raw) return false;
        var state = JSON.parse(raw);
        if (!state || !state.pages || !state.pages.length) return false;
        _pages = state.pages;
        _currentPage = state.currentPage || 0;
        if (_currentPage >= _pages.length) _currentPage = _pages.length - 1;
        E = _pages[_currentPage] || [];
        sel = null;
        var savedFile = localStorage.getItem(_draftFileKey);
        if (savedFile) _currentFile = savedFile;
        return true;
    } catch (_) { return false; }
}
function clearDraft() {
    localStorage.removeItem(_draftKey);
    localStorage.removeItem(_draftFileKey);
}

// ── Font CSS resolver ──
function fontCSS(fid) {
    var F = {
        "HN": { family: "Helvetica,Arial,sans-serif", weight: "normal", style: "normal" },
        "HB": { family: "Helvetica,Arial,sans-serif", weight: "bold", style: "normal" },
        "HI": { family: "Helvetica,Arial,sans-serif", weight: "normal", style: "italic" },
        "HS": { family: "Helvetica,Arial,sans-serif", weight: "bold", style: "italic" },
        "TN": { family: "'Times New Roman',Times,serif", weight: "normal", style: "normal" },
        "TB": { family: "'Times New Roman',Times,serif", weight: "bold", style: "normal" },
        "TI": { family: "'Times New Roman',Times,serif", weight: "normal", style: "italic" },
        "TS": { family: "'Times New Roman',Times,serif", weight: "bold", style: "italic" },
        "CN": { family: "Courier,monospace", weight: "normal", style: "normal" },
        "CB": { family: "Courier,monospace", weight: "bold", style: "normal" },
        "CI": { family: "Courier,monospace", weight: "normal", style: "italic" },
        "CS": { family: "Courier,monospace", weight: "bold", style: "italic" },
    };
    return F[fid] || { family: fid, weight: "normal", style: "normal" };
}

// ── Toast ──
function showToast(msg, type) {
    type = type || "info";
    var c = document.getElementById("toast-container");
    if (!c) return;
    var t = document.createElement("div");
    t.className = "toast " + type;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(function(){ t.remove(); }, 3000);
}

// ── Utility ──
function $(id) { return document.getElementById(id); }
function mm(px) { return Math.round(px / _sc * 10) / 10; }
function px(mm) { return Math.round(mm * _sc); }
function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

// ── System Fonts ──
var SYSTEM_FONTS = [];
function detectFonts() {
    var testStr = "mmmmmmmmmmlli";
    var testSize = "72px";
    var defaults = { serif: "serif", sansSerif: "sans-serif", monospace: "monospace" };
    var testSpan = document.createElement("span");
    testSpan.style.fontSize = testSize;
    testSpan.style.position = "absolute";
    testSpan.style.left = "-9999px";
    testSpan.innerHTML = testStr;
    document.body.appendChild(testSpan);
    var defaultWidth = {};
    for (var d in defaults) { testSpan.style.fontFamily = defaults[d]; defaultWidth[d] = testSpan.offsetWidth; }
    var candidates = ["Arial","Arial Black","Arial Narrow","Calibri","Cambria","Candara","Comic Sans MS","Consolas","Courier New","Franklin Gothic","Garamond","Georgia","Helvetica","Impact","Lucida Console","Lucida Sans","Microsoft Sans Serif","Palatino","Segoe UI","Tahoma","Times New Roman","Trebuchet MS","Verdana","Bookman Old Style","Century Gothic","Gill Sans","Rockwell","Perpetua","Baskerville","Didot","Optima","Futura","Avant Garde","Goudy","American Typewriter","Andale Mono","Apple Chancery","Brush Script MT","Chalkduster","Copperplate","Herculanum","Luminari","Marker Felt","Noteworthy","Papyrus","Zapfino"];
    SYSTEM_FONTS = [];
    for (var i = 0; i < candidates.length; i++) {
        testSpan.style.fontFamily = "'" + candidates[i] + "',sans-serif";
        if (testSpan.offsetWidth !== defaultWidth.sansSerif) { SYSTEM_FONTS.push(candidates[i]); }
    }
    testSpan.remove();
    SYSTEM_FONTS.sort();
}
detectFonts();

// ── Update title bar ──
function updateTitle() {
    var fn = $("file-name");
    if (fn) {
        var name = _currentFile || "Untitled";
        fn.textContent = (_dirty ? "● " : "") + name;
    }
}

// ── Page management ──
function switchPage(idx, silent) {
    if (idx < 0 || idx >= _pages.length) return;
    if (!silent) pushUndo();
    _pages[_currentPage] = JSON.parse(JSON.stringify(E));
    _currentPage = idx;
    E = _pages[idx] ? JSON.parse(JSON.stringify(_pages[idx])) : [];
    sel = null;
    renderPageDots();
    render();
    if (S.renderPageBorder) S.renderPageBorder(_pageBorder || "double");
    updateProps();
}
function addPage() {
    pushUndo();
    _pages.push([]);
    switchPage(_pages.length - 1, true);
    showToast("Page added", "success");
}
function deletePage() {
    if (_pages.length <= 1) { showToast("Cannot delete last page", "error"); return; }
    pushUndo();
    _pages.splice(_currentPage, 1);
    if (_currentPage >= _pages.length) _currentPage = _pages.length - 1;
    E = JSON.parse(JSON.stringify(_pages[_currentPage]));
    sel = null;
    renderPageDots();
    render();
    updateProps();
    showToast("Page deleted", "success");
}
function renderPageDots() {
    var c = $("pg-dots");
    if (!c) return;
    c.innerHTML = "";
    for (var i = 0; i < _pages.length; i++) {
        var dot = document.createElement("span");
        dot.className = "pg-dot" + (i === _currentPage ? " active" : "");
        dot.textContent = i + 1;
        dot.title = "Page " + (i + 1);
        (function(idx) {
            dot.addEventListener("click", function() { switchPage(idx); });
        })(i);
        c.appendChild(dot);
    }
    var addDot = document.createElement("span");
    addDot.className = "pg-dot add";
    addDot.textContent = "+";
    addDot.title = "Add page";
    addDot.addEventListener("click", addPage);
    c.appendChild(addDot);
}

// ── Grid lines ──
function updateGrid() {
    var svg = $("grid-overlay");
    if (!svg) return;
    var pattern = svg.querySelector("#grid-pattern");
    if (!pattern) return;
    if (_sn > 0) {
        var gs = _sn * _sc;
        pattern.setAttribute("width", gs);
        pattern.setAttribute("height", gs);
        var path = pattern.querySelector("path");
        if (path) {
            var h = gs / 2;
            path.setAttribute("d", "M " + h + " 0 L " + h + " " + gs + " M 0 " + h + " L " + gs + " " + h);
        }
        svg.style.display = "block";
    } else {
        svg.style.display = "none";
    }
}




// ── New album ──
function newAlbum() {
    if (_dirty && !confirm("Discard unsaved changes?")) return;
    clearDraft();
    E = [];
    sel = null;
    _currentFile = null;
    _currentPage = 0;
    _pages = [[]];
    _dirty = false;
    _undoStack = [];
    _redoStack = [];
    _undoStack.push(JSON.stringify(E));
    render();
    updateProps();
    renderPageDots();
    updateTitle();
    showToast("New album created", "success");
}

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
                item.className = "file-item" + (f === _currentFile ? " active" : "");
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
                            _currentFile = f;
                            parseDSL(content);
                            _dirty = false;
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
    var dsl = buildDSL();
    if (_currentFile) {
        fetch("/files/" + encodeURIComponent(_currentFile), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: dsl })
        }).then(function(r) {
            if (r.ok) {
                return r.json();
            }
            throw new Error("Save failed");
        }).then(function(data) {
            _dirty = false;
            updateTitle();
            clearDraft();
            showToast("Saved to " + (data.path || _currentFile), "success");
        }).catch(function() { showToast("Save failed", "error"); });
    } else {
        var name = prompt("File name:", "album.slbum");
        if (!name) return;
        if (!name.endsWith(".slbum") && !name.endsWith(".txt")) name += ".slbum";
        _currentFile = name;
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
                    var r = $("page").getBoundingClientRect();
                    var x = 50, y = 50;
                    add({ t: "image", s: "rectangle", x: x, y: y, w: 80, h: 60,
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

// ── Build canvas state for direct render/export ──
function buildCanvasState(format) {
    var allPages = _pages.slice();
    allPages[_currentPage] = JSON.parse(JSON.stringify(E));
    var firstPage = allPages.length > 0 ? allPages[0] : [];
    var restPages = allPages.slice(1);
    while (restPages.length > 0 && restPages[restPages.length - 1].length === 0) {
        restPages.pop();
    }
    return {
        elements: firstPage,
        pages: restPages,
        page_width_px: _pw, page_height_px: _ph,
        scale: _sc,
        source_path: _currentFile || "album.slbum",
        format: format || "html",
        title: (_currentFile || "My Album").replace(/\.(slbum|txt)$/, ""),
        author: ""
    };
}

// ── Preview (direct — no DSL parser) ──
function openPreview() {
    var overlay = $("preview-overlay");
    var frame = $("preview-frame");
    if (!overlay || !frame) return;
    overlay.classList.add("open");
    showToast("Generating preview...", "info");
    var state = buildCanvasState("html");
    fetch("/render-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
    })
    .then(function(r) {
        if (!r.ok) throw new Error("Render failed (" + r.status + ")");
        return r.text();
    })
    .then(function(html) {
        frame.contentDocument.open();
        frame.contentDocument.write(html);
        frame.contentDocument.close();
        var body = frame.contentDocument.body;
        if (body) {
            var firstPage = body.querySelector(".page");
            if (firstPage) {
                frame.style.width = firstPage.offsetWidth + "px";
                frame.style.height = firstPage.offsetHeight + "px";
            }
        }
        showToast("Preview ready", "success");
    })
    .catch(function(err) {
        showToast("Preview failed: " + err, "error");
    });
}

// ── Export PDF (direct — no DSL parser) ──
function exportPDF() {
    showToast("Generating PDF...", "info");
    var filename = _currentFile ? _currentFile.replace(/\.(slbum|txt)$/, ".pdf") : "album.pdf";
    var state = buildCanvasState("pdf");
    fetch("/export-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
    })
    .then(function(r) {
        if (!r.ok) throw new Error("Export failed (" + r.status + ")");
        return r.blob();
    })
    .then(function(b) {
        var a = document.createElement("a");
        a.href = URL.createObjectURL(b);
        a.download = filename;
        a.click();
        setTimeout(function() { URL.revokeObjectURL(a.href); }, 100);
        showToast("PDF saved to Downloads/" + filename, "success");
    })
    .catch(function(err) { showToast("Export failed: " + err, "error"); });
}

// ── Template list ──
function loadTemplateList() {
    var sel = $("wiz-template");
    if (!sel) return;
    fetch("/api/templates")
        .then(function(r) { return r.json(); })
        .then(function(templates) {
            sel.innerHTML = '<option value="blank">Blank Page</option>';
            templates.forEach(function(t) {
                var o = document.createElement("option");
                o.value = t.id;
                o.textContent = t.name;
                sel.appendChild(o);
            });
        })
        .catch(function() { /* ignore — template endpoint may not exist */ });
}

// ── Wizard ──
function applyWizard() {
    var title = $("wiz-title").value || "My Album";
    var author = $("wiz-author").value || "";
    var pgSize = $("wiz-pg-size").value || "a4";
    var orient = $("wiz-orient").value || "portrait";
    var border = $("wiz-border").value || "solid";
    var columns = parseInt($("wiz-columns").value) || 0;
    var tpl = $("wiz-template").value;

    if (tpl && tpl !== "blank") {
        // Quick Apply button on template section
        $("btn-wiz-template").click();
        return;
    }

    var lines = [];
    lines.push('ALBUM_TITLE("' + title + '")');
    if (author) lines.push('ALBUM_AUTHOR("' + author + '")');

    var w = pgSize === "a4" ? 210 : pgSize === "letter" ? 216 : 297;
    var h = pgSize === "a4" ? 297 : pgSize === "letter" ? 279 : 420;
    if (orient === "landscape") { var t = w; w = h; h = t; }
    lines.push("ALBUM_PAGES_SIZE(" + w + " " + h + ")");
    lines.push("ALBUM_PAGES_MARGINS(15 15 15 15)");

    if (border !== "none") {
        lines.push('ALBUM_PAGES_BORDER(0.1 0.5 0.1 1.0)');
        lines.push('COLOUR_ALBUM_BORDER("#666")');
    }

    if (title) lines.push('PAGE_TEXT_CENTRE("HB" 16 "' + title + '")');

    if (columns > 1) {
        lines.push("PAGE_COLUMN_START(" + columns + ")");
    }

    parseDSL(lines.join("\n"));
    pushUndo();
    render();
    // Apply ornamental border if selected
    _pageBorder = border;
    if (S.renderPageBorder) S.renderPageBorder(border);
    $("wizard-panel").classList.remove("open");
    showToast("Album created from wizard", "success");
}

// ── Escape user strings for DSL embedding ──
function escapeDSL(s) {
    return String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

// ── DSL round-trip ──
function buildDSL() {
    var lines = [
        'ALBUM_TITLE("' + escapeDSL(_currentFile ? _currentFile.replace(/\.(slbum|txt)$/, "") : "My Album") + '")',
        "ALBUM_PAGES_SIZE(" + mm(_pw) + " " + mm(_ph) + ")",
        "ALBUM_PAGES_MARGINS(15 15 15 15)",
    ];
    if (_pageBorder && _pageBorder !== "none" && _pageBorder !== "double") {
        lines.push('ALBUM_PAGES_BORDER(0.1 0.5 0.1 1.0)');
        if (_pageBorderC) lines.push('COLOUR_ALBUM_BORDER("' + _pageBorderC + '")');
    }
    lines.push("PAGE_START");

    // Add column start if columns enabled
    if (_colMode > 1) {
        lines.push("PAGE_COLUMN_START(" + _colMode + " " + _colGap.toFixed(1) + ")");
    }

    function pushElement(el) {
        if (el.t === "image") {
            lines.push('STAMP_ADD_IMG(' + mm(el.x).toFixed(1) + ' ' + mm(el.y).toFixed(1) + ' ' + mm(el.w).toFixed(1) + ' ' + mm(el.h).toFixed(1) + ' "' + (el.img || "") + '" "' + escapeDSL(el.lbl || "") + '")');
        } else if (el.t === "text") {
            lines.push('STAMP_ADD_AT(' + mm(el.x).toFixed(1) + ' ' + mm(el.y).toFixed(1) + ' ' + mm(el.w).toFixed(1) + ' ' + mm(el.h).toFixed(1) + ' "' + escapeDSL(el.lbl || "") + '" "text" "' + (el.bdr || "none") + '" "' + (el.bdrC || "transparent") + '" ' + (el.bdrW || 0) + ' "' + (el.fill || "transparent") + '" ' + (el.fillA || 0) + ' "' + (el.font || "HN") + '" ' + (el.fs || 12) + ' "' + (el.align || "left") + '")');
        } else if (el.t === "freehand") {
            lines.push('STAMP_ADD_AT(' + mm(el.x).toFixed(1) + ' ' + mm(el.y).toFixed(1) + ' ' + mm(el.w).toFixed(1) + ' ' + mm(el.h).toFixed(1) + ' "' + escapeDSL(el.lbl || "") + '" "freehand" "' + (el.bdr || "solid") + '" "' + (el.bdrC || "#666") + '" ' + (el.bdrW || 1) + ' "' + (el.fill || "#fff") + '" ' + (el.fillA || 100) + ' "' + (el.font || "HN") + '" ' + (el.fs || 12) + ' "' + (el.align || "left") + '")');
        } else {
            lines.push('STAMP_ADD_AT(' + mm(el.x).toFixed(1) + ' ' + mm(el.y).toFixed(1) + ' ' + mm(el.w).toFixed(1) + ' ' + mm(el.h).toFixed(1) + ' "' + escapeDSL(el.lbl || "") + '" "' + (el.s || "rectangle") + '" "' + (el.bdr || "solid") + '" "' + (el.bdrC || "#666") + '" ' + (el.bdrW || 1) + ' "' + (el.fill || "#fff") + '" ' + (el.fillA || 100) + ' "' + (el.font || "HN") + '" ' + (el.fs || 12) + ' "' + (el.align || "left") + '" "' + (el.cat || "") + '" "' + (el.denom || "") + '" "' + (el.perf || "") + '")');
        }
    }

    E.forEach(pushElement);

    // Add column stop if columns were enabled
    if (_colMode > 1) {
        lines.push("PAGE_COLUMN_STOP");
    }

    // Add page management DSL
    for (var i = 1; i < _pages.length; i++) {
        var pgEls = _pages[i];
        if (pgEls && pgEls.length > 0) {
            lines.push("PAGE_START");

            // Add column start for additional pages
            if (_colMode > 1) {
                lines.push("PAGE_COLUMN_START(" + _colMode + " " + _colGap.toFixed(1) + ")");
            }

            pgEls.forEach(pushElement);

            // Add column stop for additional pages
            if (_colMode > 1) {
                lines.push("PAGE_COLUMN_STOP");
            }
        }
    }
    return lines.join("\n");
}

function parseDSL(dsl) {
    E = [];
    var lines = dsl.split("\n");
    _pages = [[]];
    _currentPage = 0;
    var _rowX = 0, _rowY = 12, _rowSpacing = 6, _pageMargin = 15;
    for (var i = 0; i < lines.length; i++) {
        var t = lines[i].trim();
        if (!t || t.charAt(0) === "#") continue;
        // Page setup commands
        var mSize = t.match(/^ALBUM_PAGES_SIZE\(\s*([\d.]+)\s+([\d.]+)\)/);
        if (mSize) {
            _pw = px(parseFloat(mSize[1]));
            _ph = px(parseFloat(mSize[2]));
            $("pg-size").value = "a4";
            continue;
        }
        var mMargin = t.match(/^ALBUM_PAGES_MARGINS\(\s*([\d.]+)\s/);
        if (mMargin) {
            _pageMargin = parseFloat(mMargin[1]);
            continue;
        }
        var mBorder = t.match(/^ALBUM_PAGES_BORDER\(/);
        if (mBorder) {
            continue;
        }
        var mBorderC = t.match(/^COLOUR_ALBUM_BORDER\(\s*"([^"]*)"\s*\)/);
        if (mBorderC) {
            _pageBorderC = mBorderC[1];
            continue;
        }
        // PAGE_START — new page
        if (t.match(/^PAGE_START/)) {
            if (E.length > 0) {
                _pages[_currentPage] = JSON.parse(JSON.stringify(E));
                E = [];
            }
            _pages.push([]);
            _currentPage = _pages.length - 1;
            _rowX = _pageMargin;
            _rowY = 12;
            continue;
        }
        // PAGE_COLUMN_START — set column mode
        var mColStart = t.match(/^PAGE_COLUMN_START\(\s*(\d+)(?:\s+([\d.]+))?\)/);
        if (mColStart) {
            _colMode = parseInt(mColStart[1]) || 1;
            _colGap = mColStart[2] ? parseFloat(mColStart[2]) : 10.0;
            $("col-mode").value = _colMode;
            $("col-gap").value = _colGap;
            continue;
        }
        // PAGE_COLUMN_NEXT — column break marker (no-op in visual builder)
        if (t.match(/^PAGE_COLUMN_NEXT/)) {
            continue;
        }
        // PAGE_COLUMN_STOP — reset to single column
        if (t.match(/^PAGE_COLUMN_STOP/)) {
            _colMode = 1;
            _colGap = 10.0;
            $("col-mode").value = 1;
            $("col-gap").value = 10.0;
            continue;
        }
        // PAGE_VSPACE — vertical spacing in row layout
        var mVspace = t.match(/^PAGE_VSPACE\(\s*([\d.]+)\)/);
        if (mVspace) {
            _rowY += parseFloat(mVspace[1]);
            continue;
        }
        // ROW_START_FS — start a row of stamps
        var mRow = t.match(/^ROW_START_FS\(\s*"([^"]*)"\s+(\d+)\s+([\d.]+)\s+([\d.]+)\)/);
        if (mRow) {
            _rowX = _pageMargin;
            _rowSpacing = parseFloat(mRow[4]);
            continue;
        }
        // Commands — STAMP_ADD_AT with full properties or STAMP_ADD_IMG
        var m = t.match(/^(STAMP_ADD_AT|STAMP_ADD_IMG)\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"\s+"([^"]*)"(?:\s+"([^"]*)"\s+"([^"]*)"\s+([\d.]+)\s+"([^"]*)"\s+([\d.]+)\s+"([^"]*)"\s+([\d.]+)\s+"([^"]*)"(?:\s+"([^"]*)"\s+"([^"]*)"\s+"([^"]*)")?)?\)/);
        if (m) {
            var isImg = m[1] === "STAMP_ADD_IMG";
            E.push({ id: "el" + (nid++), t: isImg ? "image" : (m[7] === "text" ? "text" : m[7] === "freehand" ? "freehand" : "stamp"), s: isImg ? "rectangle" : m[7] || "rectangle", x: px(parseFloat(m[2])), y: px(parseFloat(m[3])), w: px(parseFloat(m[4])), h: px(parseFloat(m[5])), lbl: m[6] || "", bdr: m[8] || "solid", bdrC: m[9] || "#666", bdrW: parseFloat(m[10]) || 1, fill: m[11] || "#fff", fillA: parseFloat(m[12]) !== undefined ? parseFloat(m[12]) : 100, font: m[13] || "HN", fs: parseFloat(m[14]) || 12, align: m[15] || "left", cat: m[16] || "", denom: m[17] || "", perf: m[18] || "", img: isImg ? m[6] : "" });
            continue;
        }
        // STAMP_ADD — row-based stamp (from template DSL)
        var mRowStamp = t.match(/^STAMP_ADD\(\s*([\d.]+)\s+([\d.]+)\s+"([^"]*)"(?:\s+"([^"]*)")?(?:\s+"([^"]*)")?(?:\s+"([^"]*)")?\)/);
        if (mRowStamp) {
            E.push({ id: "el" + (nid++), t: "stamp", s: "rectangle", x: px(_rowX), y: px(_rowY), w: px(parseFloat(mRowStamp[1])), h: px(parseFloat(mRowStamp[2])), lbl: mRowStamp[3] || "", cat: mRowStamp[4] || "", denom: mRowStamp[5] || "", perf: mRowStamp[6] || "", bdr: "solid", bdrC: "#666", bdrW: 1, fill: "#fff", fillA: 100, img: "", font: "HN", fs: 12 });
            _rowX += parseFloat(mRowStamp[1]) + _rowSpacing;
            continue;
        }
        var m2 = t.match(/^(PAGE_TEXT|PAGE_TEXT_CENTRE|PAGE_TEXT_CENTER|PAGE_TEXT_RIGHT)\(\s*"([^"]*)"\s+(\d+)\s+"([^"]*)"\)/);
        if (m2) {
            var align = m2[1] === "PAGE_TEXT_CENTRE" || m2[1] === "PAGE_TEXT_CENTER" ? "center" : m2[1] === "PAGE_TEXT_RIGHT" ? "right" : "left";
            E.push({ id: "el" + (nid++), t: "text", s: "text", x: 10, y: _rowY > 12 ? _rowY + 2 : 10, w: 100, h: 20, lbl: m2[4] || "Text", font: m2[2] || "HN", fs: parseFloat(m2[3]) || 12, align: align, bdr: "none", fill: "transparent", fillA: 0 });
            _rowY += 8;
        }
    }
    // Save current page
    if (E.length > 0 || _pages.length === 0) {
        _pages[_currentPage] = JSON.parse(JSON.stringify(E));
    }
    // Remove empty trailing pages
    while (_pages.length > 1 && _pages[_pages.length - 1].length === 0) {
        _pages.pop();
    }
    E = JSON.parse(JSON.stringify(_pages[_currentPage]));
    sel = null;
    renderPageDots();
    render();
    if (S.renderPageBorder) S.renderPageBorder(_pageBorder || "double");
    updateProps();
    updateGrid();
    updateTitle();
}

// ── Exports (shared state + functions for render.js, events.js, init.js) ──
var S = {};
Object.defineProperties(S, {
    E: { get: function(){ return E; }, set: function(v){ E = v; } },
    sel: { get: function(){ return sel; }, set: function(v){ sel = v; } },
    nid: { get: function(){ return nid; }, set: function(v){ nid = v; } },
    _sc: { get: function(){ return _sc; }, set: function(v){ _sc = v; } },
    _sn: { get: function(){ return _sn; }, set: function(v){ _sn = v; } },
    _pw: { get: function(){ return _pw; }, set: function(v){ _pw = v; } },
    _ph: { get: function(){ return _ph; }, set: function(v){ _ph = v; } },
    _drg: { get: function(){ return _drg; }, set: function(v){ _drg = v; } },
    _dragEl: { get: function(){ return _dragEl; }, set: function(v){ _dragEl = v; } },
    _dragH: { get: function(){ return _dragH; }, set: function(v){ _dragH = v; } },
    _ds: { get: function(){ return _ds; }, set: function(v){ _ds = v; } },
    _defBdr: { get: function(){ return _defBdr; }, set: function(v){ _defBdr = v; } },
    _defBdrC: { get: function(){ return _defBdrC; }, set: function(v){ _defBdrC = v; } },
    _defFillC: { get: function(){ return _defFillC; }, set: function(v){ _defFillC = v; } },
    _collapsed: { get: function(){ return _collapsed; }, set: function(v){ _collapsed = v; } },
    _currentFile: { get: function(){ return _currentFile; }, set: function(v){ _currentFile = v; } },
    _currentPage: { get: function(){ return _currentPage; }, set: function(v){ _currentPage = v; } },
    _pages: { get: function(){ return _pages; }, set: function(v){ _pages = v; } },
    _dirty: { get: function(){ return _dirty; }, set: function(v){ _dirty = v; } },
    _colMode: { get: function(){ return _colMode; }, set: function(v){ _colMode = v; } },
    _colGap: { get: function(){ return _colGap; }, set: function(v){ _colGap = v; } },
    _pageBorder: { get: function(){ return _pageBorder; }, set: function(v){ _pageBorder = v; } },
    _pageBorderC: { get: function(){ return _pageBorderC; }, set: function(v){ _pageBorderC = v; } },
    _init: { get: function(){ return _init; }, set: function(v){ _init = v; } },
    SYSTEM_FONTS: { get: function(){ return SYSTEM_FONTS; }, set: function(v){ SYSTEM_FONTS = v; } },
    $: { value: $ }, mm: { value: mm }, px: { value: px }, clamp: { value: clamp },
    fontCSS: { value: fontCSS }, showToast: { value: showToast },
    pushUndo: { value: pushUndo }, undo: { value: undo }, redo: { value: redo },
    loadElements: { value: loadElements }, loadElementsNoPush: { value: loadElementsNoPush },
    saveDraft: { value: saveDraft }, loadDraft: { value: loadDraft }, clearDraft: { value: clearDraft },
    updateTitle: { value: updateTitle }, switchPage: { value: switchPage },
    addPage: { value: addPage }, deletePage: { value: deletePage },
    renderPageDots: { value: renderPageDots }, updateGrid: { value: updateGrid },
    newAlbum: { value: newAlbum }, loadFileList: { value: loadFileList }, saveFile: { value: saveFile },
    uploadImageFile: { value: uploadImageFile }, loadImageList: { value: loadImageList },
    buildCanvasState: { value: buildCanvasState }, openPreview: { value: openPreview },
    exportPDF: { value: exportPDF }, loadTemplateList: { value: loadTemplateList },
    applyWizard: { value: applyWizard }, escapeDSL: { value: escapeDSL }, buildDSL: { value: buildDSL }, parseDSL: { value: parseDSL },
    // ── Alignment functions ──
    alignSelected: { value: alignSelected },
    distributeSelected: { value: distributeSelected },
    matchSize: { value: matchSize },
    toggleAlignGroup: { value: toggleAlignGroup },
    toggleSnap: { value: toggleSnap },
});

// ── Alignment functions ──
function getSelectedElements() {
    if (!S.sel) return [];
    return S.E.filter(function(el) { return el.id === S.sel; });
}

function alignSelected(direction) {
    if (!S.sel) { showToast("Select an element first", "error"); return; }
    var el = S.E.find(function(x) { return x.id === S.sel; });
    if (!el) return;
    var pw = S._pw, ph = S._ph;
    switch (direction) {
        case "left": el.x = 20; break;
        case "center": el.x = Math.round((pw - el.w) / 2); break;
        case "right": el.x = pw - el.w - 20; break;
        case "top": el.y = 20; break;
        case "middle": el.y = Math.round((ph - el.h) / 2); break;
        case "bottom": el.y = ph - el.h - 20; break;
    }
    S.pushUndo();
    S.render();
    S.updateProps();
    showToast("Aligned: " + direction, "success");
}

function distributeSelected(axis) {
    if (!S.sel) { showToast("Select elements first", "error"); return; }
    var sel = S.E.filter(function(el) { return el.id === S.sel; });
    if (sel.length < 2) { showToast("Select at least 2 elements to distribute", "error"); return; }
    var sorted = sel.slice().sort(function(a, b) {
        return axis === "h" ? a.x - b.x : a.y - b.y;
    });
    var first = sorted[0], last = sorted[sorted.length - 1];
    var span = axis === "h" ? (last.x + last.w - first.x) : (last.y + last.h - first.y);
    var totalSize = sorted.reduce(function(s, el) {
        return s + (axis === "h" ? el.w : el.h);
    }, 0);
    var gap = (span - totalSize) / (sorted.length - 1);
    var cursor = axis === "h" ? first.x : first.y;
    sorted.forEach(function(el) {
        if (axis === "h") { el.x = Math.round(cursor); cursor += el.w + gap; }
        else { el.y = Math.round(cursor); cursor += el.h + gap; }
    });
    S.pushUndo();
    S.render();
    showToast("Distributed: " + (axis === "h" ? "horizontally" : "vertically"), "success");
}

function matchSize(axis) {
    if (!S.sel) { showToast("Select elements first", "error"); return; }
    var sel = S.E.filter(function(el) { return el.id === S.sel; });
    if (sel.length < 2) { showToast("Select at least 2 elements to match", "error"); return; }
    var ref = sel[0];
    sel.forEach(function(el) {
        if (el.id === ref.id) return;
        if (axis === "w") { el.w = ref.w; }
        else { el.h = ref.h; }
    });
    S.pushUndo();
    S.render();
    S.updateProps();
    showToast("Matched: " + (axis === "w" ? "width" : "height"), "success");
}

function toggleAlignGroup() {
    var group = document.getElementById("align-group");
    if (!group) return;
    var isVisible = group.style.display !== "none";
    group.style.display = isVisible ? "none" : "flex";
}

function toggleSnap() {
    var btn = document.getElementById("btn-snap");
    if (!btn) return;
    btn.classList.toggle("active");
    S._snapEnabled = btn.classList.contains("active");
    showToast(S._snapEnabled ? "Snap-to-guide ON" : "Snap-to-guide OFF", "info");
}
window.StampAlbum = S;

// ── Init (events.js provides S.init) ──
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function(){ if (S.init) S.init(); });
else if (S.init) S.init();
})();
