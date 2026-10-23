"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$;
var NS = "http://www.w3.org/2000/svg";

// ── The pages, as small pictures beside the page ──
// A column down the canvas's left edge (one row across the bottom on a phone). Each page is
// a button with a simple drawing of it: the border, a box for each stamp or picture and grey
// lines for text. Not a miniature: at this size captions would only be specks. The open
// page's picture is redrawn from render() as it changes. Each page has a ⋯ menu with
// Move earlier, Move later and Delete page.

var _menuFor = null;  // the page index whose ⋯ menu is open

function el(name, attrs) {
    var n = document.createElementNS(NS, name);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
}

// The open album's page, as drawPage takes it: items in canvas px.
function openAlbumPage() {
    return { pw: S._pw / S._sc, ph: S._ph / S._sc, border: S._pageBorder, color: S.themeColor(),
             mount: null, unit: S._sc, inset: S.CORE.getBorderInset() };
}

// The drawing of one page's items, in mm. `page` gives the paper ({pw, ph} in mm), the
// border style, the theme colour, the mounts (null: the open album's) and `unit`, the items'
// units per mm (2.5 for the editor's px, 1 for a parsed file's mm). Without it, the open album.
// Used by the page strip and the template gallery (S.drawPageThumb).
function drawPage(svg, items, page) {
    var pg = page || openAlbumPage();
    var sc = pg.unit || 1, pw = pg.pw, ph = pg.ph, color = pg.color;
    var before = pg.mount ? S.CORE.getMount() : null;
    if (before) S.CORE.setMount(pg.mount.overhang, pg.mount.gap);  // frame outsets for this page
    try {
        drawItems(svg, items, sc, pw, ph, pg.border, color, pg.inset);
    } finally {
        if (before) S.CORE.setMount(before.overhang, before.gap);
    }
}

function drawItems(svg, items, sc, pw, ph, border, color, inset) {
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", "0 0 " + pw + " " + ph);
    svg.appendChild(el("rect", { x: 0, y: 0, width: pw, height: ph, fill: "#fff" }));
    if (border && border !== "none") {
        var m = inset != null ? inset : S.CORE.OLD_ALBUM_BORDER_INSET;  // the album's border distance, mm
        var frame = el("rect", { x: m, y: m, width: pw - 2 * m, height: ph - 2 * m, fill: "none",
                                 stroke: color, "stroke-width": 0.8 });
        frame.setAttribute("class", "pg-border");
        svg.appendChild(frame);
    }
    (items || []).forEach(function(it) {
        var x = it.x / sc, y = it.y / sc, w = it.w / sc, h = it.h / sc;
        if (it.t === "text") {
            // Grey bars where the lines of text sit; a heading darker
            var lh = Math.max(1.5, (it.fs || 12) * 25.4 / 72 * 1.3);
            var n = Math.max(1, Math.min(12, Math.floor(h / lh)));
            var bar = Math.max(1, lh * 0.55), fill = it.role === "heading" ? color : "#B8B2A7";
            for (var i = 0; i < n; i++) {
                var bw = (i === n - 1 && n > 1) ? w * 0.6 : w * 0.92;
                var bx = it.align === "center" ? x + (w - bw) / 2 : it.align === "right" ? x + w - bw : x;
                var line = el("rect", { x: bx, y: y + i * lh + (lh - bar) / 2, width: bw, height: bar, fill: fill, rx: bar / 3 });
                line.setAttribute("class", "pg-text" + (it.role === "heading" ? " pg-heading" : ""));
                svg.appendChild(line);
            }
            return;
        }
        // The stamp's own shape at its frame's outer edge, from the outline the page and the
        // exports draw (shapeOutline); a free shape is a dashed box, as on the page.
        var look = { fill: it.t === "image" ? "#E4E0D7" : "#fff", stroke: "#3F3A33", "stroke-width": 0.7 };
        if (it.t === "freehand") look["stroke-dasharray"] = "2 1.5";
        var o = S.CORE.frameOutset(it);
        var shape = it.t === "stamp" ? it.s : "rectangle";
        var g = S.CORE.shapeOutline(shape, x, y, w, h, o), n;
        if (g.kind === "ellipse") n = el("ellipse", { cx: g.cx, cy: g.cy, rx: g.rx, ry: g.ry });
        else if (g.kind === "polygon") n = el("polygon", { points: g.points.map(function(p) { return p[0] + "," + p[1]; }).join(" ") });
        else n = el("rect", { x: g.x, y: g.y, width: g.w, height: g.h });
        for (var k in look) n.setAttribute(k, look[k]);
        n.setAttribute("class", "pg-shape pg-shape-" + g.kind);
        svg.appendChild(n);
    });
}

function pageItems(i) { return i === S._currentPage ? S.E : (S._pages[i] || []); }

// Redraw the open page's picture (called from render()).
function updateThumb() {
    var b = document.querySelector('#pg-list .pg-thumb[aria-current="page"] svg');
    if (b) drawPage(b, S.E);
}

function renderPageStrip() {
    if (S.syncPhoneBar) S.syncPhoneBar();  // the phone's Page button and pager
    var list = $("pg-list");
    if (!list) return;
    closeMenu();
    var focused = list.contains(document.activeElement) ? document.activeElement : null;
    var focusIdx = focused ? Number(focused.closest(".pg-item").dataset.idx) : null;
    var focusMore = focused ? focused.classList.contains("pg-more") : false;
    list.innerHTML = "";
    var count = S._pages.length;
    for (var i = 0; i < count; i++) {
        var li = document.createElement("li");
        li.className = "pg-item";
        li.dataset.idx = i;
        var b = document.createElement("button");
        b.type = "button";
        b.className = "pg-thumb";
        b.setAttribute("aria-label", S.t("msg.page_n", { n: i + 1 }));
        if (i === S._currentPage) b.setAttribute("aria-current", "page");
        var svg = el("svg", { "aria-hidden": "true", preserveAspectRatio: "xMidYMid meet" });
        svg.setAttribute("class", "pg-pic");
        drawPage(svg, pageItems(i));
        b.appendChild(svg);
        var num = document.createElement("span");
        num.className = "pg-num";
        num.textContent = String(i + 1);
        b.appendChild(num);
        b.addEventListener("click", (function(idx) { return function() {
            if (idx !== S._currentPage) S.switchPage(idx);
        }; })(i));
        b.addEventListener("keydown", thumbKeys);
        li.appendChild(b);
        var more = document.createElement("button");
        more.type = "button";
        more.className = "pg-more";
        more.setAttribute("aria-label", S.t("msg.page_n_options", { n: i + 1 }));
        more.setAttribute("aria-haspopup", "menu");
        more.setAttribute("aria-expanded", "false");
        more.setAttribute("aria-controls", "pg-menu");
        more.appendChild(S.icon("more"));
        more.addEventListener("click", (function(idx) { return function(e) {
            e.stopPropagation();
            if (_menuFor === idx) closeMenu(true); else openMenu(idx, e.detail === 0);
        }; })(i));
        li.appendChild(more);
        list.appendChild(li);
    }
    if (focusIdx !== null) {
        var item = list.querySelector('.pg-item[data-idx="' + Math.min(focusIdx, count - 1) + '"]');
        if (item) item.querySelector(focusMore ? ".pg-more" : ".pg-thumb").focus();
    }
    var cur = list.querySelector('.pg-thumb[aria-current="page"]');
    if (cur && cur.scrollIntoView && !focused) cur.scrollIntoView({ block: "nearest", inline: "nearest" });
}

// Arrow keys move between pages (up/down in the column, left/right in the phone's row).
function thumbKeys(e) {
    var idx = Number(this.closest(".pg-item").dataset.idx), to = null;
    if (e.key === "ArrowDown" || e.key === "ArrowRight") to = idx + 1;
    else if (e.key === "ArrowUp" || e.key === "ArrowLeft") to = idx - 1;
    else if (e.key === "Home") to = 0;
    else if (e.key === "End") to = S._pages.length - 1;
    if (to === null) return;
    e.preventDefault();
    if (to < 0 || to >= S._pages.length || to === idx) return;
    S.switchPage(to);
    var b = document.querySelector('#pg-list .pg-item[data-idx="' + to + '"] .pg-thumb');
    if (b) b.focus();
}

// ── The ⋯ menu ──
function menuItems() {
    return Array.prototype.slice.call($("pg-menu").querySelectorAll(".mi")).filter(function(b) { return !b.disabled; });
}
function moreBtn(idx) { return document.querySelector('#pg-list .pg-item[data-idx="' + idx + '"] .pg-more'); }

function openMenu(idx, focusFirst) {
    closeMenu();
    var menu = $("pg-menu"), btn = moreBtn(idx);
    if (!menu || !btn) return;
    _menuFor = idx;
    menu.setAttribute("aria-label", S.t("msg.page_n_options", { n: idx + 1 }));
    $("pg-menu-earlier").disabled = idx === 0;
    $("pg-menu-later").disabled = idx === S._pages.length - 1;
    $("pg-menu-delete").disabled = S._pages.length <= 1;
    menu.hidden = false;
    btn.setAttribute("aria-expanded", "true");
    // Beside the button, kept on screen
    var r = btn.getBoundingClientRect(), mw = menu.offsetWidth, mh = menu.offsetHeight;
    var left = Math.min(r.right + 4, window.innerWidth - mw - 8), top = Math.min(r.top, window.innerHeight - mh - 8);
    if (left < 8) left = 8;
    menu.style.left = left + "px";
    menu.style.top = Math.max(8, top) + "px";
    if (focusFirst) { var it = menuItems(); if (it.length) it[0].focus(); }
}
function closeMenu(returnFocus) {
    if (_menuFor === null) return;
    var idx = _menuFor, menu = $("pg-menu");
    _menuFor = null;
    if (menu) menu.hidden = true;
    var btn = moreBtn(idx);
    if (btn) { btn.setAttribute("aria-expanded", "false"); if (returnFocus) btn.focus(); }
}
// Run a menu action after closing the menu (so a question it asks gets focus).
function act(fn) {
    return function() {
        var idx = _menuFor;
        if (idx === null) return;
        closeMenu();
        fn(idx);
    };
}
function focusThumb(idx) {
    var b = document.querySelector('#pg-list .pg-item[data-idx="' + idx + '"] .pg-thumb');
    if (b) b.focus();
}

function wire() {
    var menu = $("pg-menu");
    if (!menu) return;
    $("pg-add").addEventListener("click", function() { S.addPage(); focusThumb(S._currentPage); });
    $("pg-menu-earlier").addEventListener("click", act(function(i) { if (S.movePage(i, i - 1)) focusThumb(i - 1); }));
    $("pg-menu-later").addEventListener("click", act(function(i) { if (S.movePage(i, i + 1)) focusThumb(i + 1); }));
    $("pg-menu-delete").addEventListener("click", act(function(i) {
        if (S.deletePage(i)) focusThumb(S._currentPage); else focusThumb(i);
    }));
    menu.addEventListener("keydown", function(e) {
        var it = menuItems(), i = it.indexOf(document.activeElement);
        if (e.key === "ArrowDown" && it.length) it[(i + 1) % it.length].focus();
        else if (e.key === "ArrowUp" && it.length) it[(i - 1 + it.length) % it.length].focus();
        else if (e.key === "Home" && it.length) it[0].focus();
        else if (e.key === "End" && it.length) it[it.length - 1].focus();
        else if (e.key === "Escape") closeMenu(true);
        else if (e.key === "Tab") { closeMenu(); return; }
        else return;
        e.preventDefault();
        e.stopPropagation();
    });
    document.addEventListener("keydown", function(e) {
        if (e.key === "Escape" && _menuFor !== null) { e.preventDefault(); closeMenu(menu.contains(document.activeElement)); }
    }, true);
    document.addEventListener("mousedown", function(e) {
        if (_menuFor !== null && !menu.contains(e.target) && !e.target.closest(".pg-more")) closeMenu();
    });
    window.addEventListener("resize", function() { closeMenu(); });
    $("pg-strip").addEventListener("scroll", function() { closeMenu(); }, true);
}

Object.defineProperties(S, {
    renderPageStrip: { value: renderPageStrip },
    updateThumb: { value: updateThumb },
    drawPageThumb: { value: drawPage },
});

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire);
else wire();
})();
