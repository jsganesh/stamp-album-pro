"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$;
var CORE = window.StampAlbumDSL || {};

// ── Frames (View menu) ──
// The album's pages as they hang in exhibition frames (GREX 2026 Art. 6.1): 4 rows of 23 cm
// sheets 4 to a row (A4 hangs the same), 31 cm sheets 3 to a row, 46 cm sheets 2 to a row.
// Balance across a frame counts towards presentation; clicking a page goes to it.

var ROWS = 4;

// Sheets to a row for the album's paper: an FIP sheet's own number, else 4.
function perRow() {
    var d = CORE.describePageSize(S._pw / S._sc, S._ph / S._sc);
    return (d.name && CORE.FIP_FRAME_ROW[d.name]) || 4;
}

function allPages() {
    var pages = S._pages.slice();
    pages[S._currentPage] = S.E;
    return pages;
}

function pageButton(items, idx) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "fv-page" + (idx === S._currentPage ? " current" : "");
    b.setAttribute("aria-label", S.t("msg.page_n_go", { n: idx + 1 }));
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("aria-hidden", "true");
    svg.style.aspectRatio = (S._pw / S._sc) + " / " + (S._ph / S._sc);
    S.drawPageThumb(svg, items || []);
    var n = document.createElement("span");
    n.className = "fv-num";
    n.textContent = String(idx + 1);
    b.appendChild(svg);
    b.appendChild(n);
    b.addEventListener("click", function() {
        closeFrames();
        if (idx !== S._currentPage) S.switchPage(idx);
    });
    return b;
}

function openFrames() {
    var pages = allPages(), row = perRow(), per = row * ROWS;
    var count = Math.max(1, Math.ceil(pages.length / per));
    $("fv-note").textContent = S.t("msg.frames_note", { count: count, per: row, frame: per });
    var host = $("fv-frames");
    host.textContent = "";
    for (var f = 0; f < count; f++) {
        var sec = document.createElement("section");
        sec.className = "fv-frame";
        var h = document.createElement("h3");
        h.textContent = S.t("msg.frame_n", { n: f + 1 });
        h.id = "fv-frame-" + (f + 1);
        sec.setAttribute("aria-labelledby", h.id);
        var grid = document.createElement("div");
        grid.className = "fv-grid";
        grid.style.gridTemplateColumns = "repeat(" + row + ", minmax(0, 1fr))";
        for (var i = f * per; i < Math.min(pages.length, (f + 1) * per); i++) grid.appendChild(pageButton(pages[i], i));
        sec.appendChild(h);
        sec.appendChild(grid);
        host.appendChild(sec);
    }
    $("frames-overlay").classList.add("open");
    $("fv-close").focus();
}
function closeFrames() {
    $("frames-overlay").classList.remove("open");
}

function wireFrames() {
    $("fv-close").addEventListener("click", closeFrames);
    $("fv-done").addEventListener("click", closeFrames);
    $("frames-overlay").addEventListener("click", function(e) { if (e.target === this) closeFrames(); });
    $("frames-overlay").addEventListener("keydown", function(e) {
        if (e.key === "Escape") { e.stopPropagation(); closeFrames(); }
    });
}

S.openFrames = openFrames;
S.wireFrames = wireFrames;

})();
