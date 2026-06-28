"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, mm = S.mm, showToast = S.showToast;
var pushUndo = S.pushUndo;

// ── Font population ──
function populateFonts() {
    var pfnt = $("pfnt");
    if (!pfnt) return;
    pfnt.innerHTML = "";
    var stdFonts = [
        { v: "HN", t: "Helvetica" },
        { v: "HB", t: "Helvetica Bold" },
        { v: "HI", t: "Helvetica Italic" },
        { v: "HS", t: "Helvetica Bold Italic" },
        { v: "TN", t: "Times New Roman" },
        { v: "TB", t: "Times New Roman Bold" },
        { v: "TI", t: "Times New Roman Italic" },
        { v: "TS", t: "Times New Roman Bold Italic" },
        { v: "CN", t: "Courier New" },
        { v: "CB", t: "Courier New Bold" },
        { v: "CI", t: "Courier New Italic" },
        { v: "CS", t: "Courier New Bold Italic" },
    ];
    var og = document.createElement("optgroup");
    og.label = "Standard Fonts";
    stdFonts.forEach(function(f) { var o = document.createElement("option"); o.value = f.v; o.textContent = f.t; og.appendChild(o); });
    pfnt.appendChild(og);
    if (S.SYSTEM_FONTS && S.SYSTEM_FONTS.length) {
        var og2 = document.createElement("optgroup");
        og2.label = "System Fonts";
        S.SYSTEM_FONTS.forEach(function(f) { var o = document.createElement("option"); o.value = f; o.textContent = f; og2.appendChild(o); });
        pfnt.appendChild(og2);
    }
    var ws = document.createElement("optgroup");
    ws.label = "Web Safe";
    ["Arial","Helvetica","Times New Roman","Courier New","Georgia","Verdana","Trebuchet MS","Impact","Comic Sans MS"].forEach(function(f) { var o = document.createElement("option"); o.value = f; o.textContent = f; ws.appendChild(o); });
    pfnt.appendChild(ws);
}

// ── Alignment guide lines ──
var _guideLines = [];
var GUIDE_THRESHOLD = 5;

function drawAlignmentGuides(el) {
    clearAlignmentGuides();
    if (!el) return;
    var guides = [];
    var edges = [
        { pos: el.x, type: "v" },
        { pos: el.x + el.w, type: "v" },
        { pos: el.x + el.w / 2, type: "v" },
        { pos: el.y, type: "h" },
        { pos: el.y + el.h, type: "h" },
        { pos: el.y + el.h / 2, type: "h" },
    ];
    S.E.forEach(function(other) {
        if (other.id === el.id) return;
        var oEdges = [
            { pos: other.x, type: "v" },
            { pos: other.x + other.w, type: "v" },
            { pos: other.x + other.w / 2, type: "v" },
            { pos: other.y, type: "h" },
            { pos: other.y + other.h, type: "h" },
            { pos: other.y + other.h / 2, type: "h" },
        ];
        edges.forEach(function(e) {
            oEdges.forEach(function(oe) {
                if (e.type !== oe.type) return;
                if (Math.abs(e.pos - oe.pos) > GUIDE_THRESHOLD) return;
                guides.push({ pos: oe.pos, dir: e.type === "v" ? "v" : "h",
                    spanStart: Math.min(e.type === "v" ? el.y : el.x, oe.type === "v" ? other.y : other.x),
                    spanEnd: Math.max(e.type === "v" ? el.y + el.h : el.x + el.w, oe.type === "v" ? other.y + other.h : other.x + other.w) });
            });
        });
    });
    var pg = $("page");
    if (!pg) return;
    guides.forEach(function(g) {
        var line = document.createElement("div");
        line.className = "guide-line";
        if (g.dir === "v") {
            line.style.left = g.pos + "px";
            line.style.top = "0px";
            line.style.width = "1px";
            line.style.height = "100%";
        } else {
            line.style.left = "0px";
            line.style.top = g.pos + "px";
            line.style.width = "100%";
            line.style.height = "1px";
        }
        pg.appendChild(line);
        _guideLines.push(line);
    });
}

function clearAlignmentGuides() {
    _guideLines.forEach(function(l) { if (l.parentNode) l.parentNode.removeChild(l); });
    _guideLines = [];
}

// ── Add element ──
function add(p) {
    var s = {
        id: "el" + (S.nid++),
        t: p.t || "stamp",
        s: p.s || "rectangle",
        x: p.x || 50, y: p.y || 50, w: p.w || 80, h: p.h || 60,
        lbl: p.lbl || "",
        font: p.font || "HN",
        fs: p.fs || 12,
        align: p.align || "left",
        bdr: p.bdr || "solid",
        bdrC: p.bdrC || "#2C2C2C",
        bdrW: p.bdrW || 0.5,
        fill: p.fill || "#FEFEFE",
        fillA: p.fillA || 100,
        img: p.img || "",
        /* Philatelic metadata */
        hdg: p.hdg || "",
        cat: p.cat || "",
        denom: p.denom || "",
        cond: p.cond || "",
        perf: p.perf || ""
    };
    S.E.push(s);
    pushUndo();
    select(s.id);
    render();
}

// ── Select ──
function select(id) {
    S.sel = id;
    render();
    var el = S.E.find(function(x) { return x.id === id; });
    if (!el) {
        $("rp-content").style.display = "none";
        $("rp-none").style.display = "block";
        return;
    }
    $("rp-content").style.display = "block";
    $("rp-none").style.display = "none";
    $("px").value = mm(el.x);
    $("py").value = mm(el.y);
    $("pw").value = mm(el.w);
    $("ph").value = mm(el.h);
    $("plbl").value = el.lbl || "";
    $("pbs").value = el.bdr || "solid";
    $("pbc").value = el.bdrC || "#2C2C2C";
    $("pbw").value = el.bdrW || 0.5;
    $("pfc").value = el.fill || "#FEFEFE";
    $("pfa").value = el.fillA || 100;
    $("pfa-v").textContent = (el.fillA || 100) + "%";
    $("pfnt").value = el.font || "HN";
    $("pfs").value = el.fs || 12;
    var isImg = el.t === "image";
    $("img-sec").style.display = isImg ? "block" : "none";
    $("img-row").style.display = isImg ? "flex" : "none";
    /* Philatelic fields — show for stamp type */
    var isStamp = el.t === "stamp";
    $("phil-sec").style.display = isStamp ? "block" : "none";
    $("phil-hdg-row").style.display = isStamp ? "flex" : "none";
    $("phil-cat-row").style.display = isStamp ? "flex" : "none";
    $("phil-denom-row").style.display = isStamp ? "flex" : "none";
    $("phil-cond-row").style.display = isStamp ? "flex" : "none";
    $("phil-perf-row").style.display = isStamp ? "flex" : "none";
    if (isStamp) {
        $("phdg").value = el.hdg || "";
        $("pcat").value = el.cat || "";
        $("pdenom").value = el.denom || "";
        $("pcond").value = el.cond || "";
        $("pperf").value = el.perf || "";
    }
}

function updateProps() {
    var el = S.E.find(function(x) { return x.id === S.sel; });
    if (!el) return;
    $("px").value = mm(el.x);
    $("py").value = mm(el.y);
    $("pw").value = mm(el.w);
    $("ph").value = mm(el.h);
}

// ── Status bar ──
function updateStatusBar() {
    if (!window.StampAlbum) return;
    var E = S.E;
    var sel = S.sel;
    // Page info
    if ($("sb-page")) {
        $("sb-page").textContent = "Page " + (S._currentPage + 1) + " of " + (S._pages ? S._pages.length : 1);
    }
    // Element count
    if ($("sb-elements")) {
        var n = E.length;
        $("sb-elements").textContent = n + " element" + (n !== 1 ? "s" : "");
    }
    // Selection info
    if ($("sb-selection")) {
        if (!sel) {
            $("sb-selection").textContent = "No selection";
        } else {
            var el = E.find(function(x) { return x.id === sel; });
            if (el) {
                var label = el.lbl || el.hdg || (el.t === "text" ? "Text" : "Stamp");
                $("sb-selection").textContent = el.t + " — " + label.substring(0, 30);
            }
        }
    }
}

// ── Shape paths ──
function getShapePath(shape, w, h) {
    var hw = w / 2, hh = h / 2;
    if (shape === "oval") return "M " + hw + " 0 A " + hw + " " + hh + " 0 1 0 " + hw + " " + h + " A " + hw + " " + hh + " 0 1 0 " + hw + " 0 Z";
    if (shape === "diamond") return "M " + hw + " 0 L " + w + " " + hh + " L " + hw + " " + h + " L 0 " + hh + " Z";
    if (shape === "triangle") return "M " + hw + " 0 L " + w + " " + h + " L 0 " + h + " Z";
    if (shape === "hexagon") { var x1 = w * 0.25, x2 = w * 0.75, y2 = h * 0.5; return "M " + x1 + " 0 L " + x2 + " 0 L " + w + " " + y2 + " L " + x2 + " " + h + " L " + x1 + " " + h + " L 0 " + y2 + " Z"; }
    if (shape === "octagon") { var a = w * 0.3, b = h * 0.3; return "M " + a + " 0 L " + (w - a) + " 0 L " + w + " " + b + " L " + w + " " + (h - b) + " L " + (w - a) + " " + h + " L " + a + " " + h + " L 0 " + (h - b) + " L 0 " + b + " Z"; }
    if (shape === "pentagon") { var cx = w / 2; return "M " + cx + " 0 L " + w + " " + (h * 0.38) + " L " + (w * 0.82) + " " + h + " L " + (w * 0.18) + " " + h + " L 0 " + (h * 0.38) + " Z"; }
    return "M 0 0 L " + w + " 0 L " + w + " " + h + " L 0 " + h + " Z";
}

// ── Render canvas ──
function render() {
    var pg = $("page");
    pg.querySelectorAll(".cel").forEach(function(el) { el.remove(); });
    S.E.forEach(function(el) {
        var d = document.createElement("div");
        d.className = "cel shape-" + (el.s || "rectangle") + (el.id === S.sel ? " selected" : "");
        d.dataset.id = el.id;
        d.style.left = el.x + "px";
        d.style.top = el.y + "px";
        d.style.width = el.w + "px";
        d.style.height = el.h + "px";

        /* ── Philatelic stamp mount rendering ── */
        if (el.t === "stamp" && el.s === "rectangle") {
            // Mount: thick black border (the album mount border)
            d.style.border = "1.5pt solid " + (el.bdrC || "#2C2C2C");
            d.style.backgroundColor = el.fill || "#FEFEFE";
            d.style.boxShadow = "inset 0 0 0 3pt " + (el.fill || "#FEFEFE");
            d.classList.add("stamp-mount");

            // Inner content area
            var inner = document.createElement("div");
            inner.className = "stamp-inner";
            inner.style.cssText = "position:absolute;inset:4pt;display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden;";

            if (el.img) {
                var img = document.createElement("img");
                img.className = "eimg";
                img.src = el.img;
                img.style.maxWidth = "92%";
                img.style.maxHeight = "60%";
                inner.appendChild(img);
            }

            // Label text (color, catalog #)
            if (el.lbl) {
                var l = document.createElement("span");
                l.className = "elbl";
                l.textContent = el.lbl;
                l.contentEditable = "true";
                l.spellcheck = false;
                var fc = S.fontCSS(el.font || "HN");
                l.style.fontFamily = fc.family;
                l.style.fontSize = Math.max(9, (el.fs || 10)) + "px";
                l.style.fontWeight = fc.weight;
                l.style.fontStyle = fc.style;
                l.style.marginTop = "2px";
                l.addEventListener("blur", function() {
                    el.lbl = this.textContent;
                    pushUndo();
                });
                inner.appendChild(l);
            }

            // Denomination below label
            if (el.denom) {
                var denom = document.createElement("span");
                denom.className = "stamp-denom";
                denom.textContent = el.denom;
                denom.style.cssText = "font-size:9px;font-weight:600;color:#333;margin-top:1px;";
                inner.appendChild(denom);
            }

            d.appendChild(inner);

            // Heading below mount
            if (el.hdg) {
                var hdg = document.createElement("div");
                hdg.className = "stamp-hdg";
                hdg.textContent = el.hdg;
                hdg.style.cssText = "position:absolute;bottom:-18px;left:0;right:0;text-align:center;font-size:9px;color:#333;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;";
                d.appendChild(hdg);
            }
        }
        else if (el.s && el.s !== "rectangle" && el.s !== "text" && el.s !== "freehand") {
            var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svg.setAttribute("class", "shape-svg");
            svg.setAttribute("viewBox", "0 0 " + el.w + " " + el.h);
            svg.style.position = "absolute";
            svg.style.top = "0";
            svg.style.left = "0";
            svg.style.width = "100%";
            svg.style.height = "100%";
            var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", getShapePath(el.s, el.w, el.h));
            path.setAttribute("fill", el.fill || "#fff");
            path.setAttribute("stroke", el.bdrC || "#666");
            path.setAttribute("stroke-width", (el.bdrW || 1) * 2);
            if (el.bdr === "dashed") path.setAttribute("stroke-dasharray", "4,2");
            if (el.bdr === "dotted") path.setAttribute("stroke-dasharray", "1,2");
            if (el.bdr === "double") {
                path.setAttribute("stroke-width", 1);
                var path2 = path.cloneNode();
                path2.setAttribute("transform", "translate(3,3) scale(0.95)");
                path2.setAttribute("fill", "none");
                path2.setAttribute("stroke-width", 1);
                svg.appendChild(path2);
            }
            svg.appendChild(path);
            d.appendChild(svg);
            d.style.border = "none";
        } else {
            d.style.border = (el.bdrW || 0) + "pt " + (el.bdr || "solid") + " " + (el.bdrC || "#666");
            d.style.backgroundColor = el.fill || "transparent";
        }
        if (el.fillA !== undefined && el.fillA < 100 && el.t !== "stamp") d.style.opacity = el.fillA / 100;

        if (el.img && el.t !== "stamp") {
            var img = document.createElement("img");
            img.className = "eimg";
            img.src = el.img;
            d.appendChild(img);
        } else if (el.lbl && el.t !== "stamp") {
            var l = document.createElement("span");
            l.className = "elbl";
            l.textContent = el.lbl;
            l.contentEditable = "true";
            l.spellcheck = false;
            var fc = S.fontCSS(el.font || "HN");
            l.style.fontFamily = fc.family;
            l.style.fontSize = (el.fs || 12) + "px";
            l.style.fontWeight = fc.weight;
            l.style.fontStyle = fc.style;
            l.addEventListener("blur", function() {
                el.lbl = this.textContent;
                var p = this.parentNode;
                this.style.minHeight = "";
                var nh = this.scrollHeight + 4;
                if (nh > p.offsetHeight) p.style.height = nh + "px";
                pushUndo();
            });
            d.appendChild(l);
        }
        if (el.t === "freehand") {
            d.style.border = "1pt dashed #999";
            d.style.backgroundColor = "rgba(200,200,200,0.1)";
            var fh = document.createElement("div");
            fh.style.cssText = "position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:10px;color:#999;text-align:center;";
            fh.innerHTML = "✎ Free Shape<br><small>Draw custom shape</small>";
            d.appendChild(fh);
        }

        var dim = document.createElement("span");
        dim.className = "dim";
        dim.textContent = mm(el.w) + "×" + mm(el.h) + "mm";
        d.appendChild(dim);

        ["nw", "ne", "sw", "se", "n", "s", "e", "w"].forEach(function(h) {
            var ha = document.createElement("div");
            ha.className = "rh " + h;
            ha.dataset.h = h;
            d.appendChild(ha);
        });

        d.addEventListener("mousedown", function(e) {
            if (e.target.classList.contains("rh")) return;
            e.stopPropagation();
            select(el.id);
            S._drg = true;
            S._dragEl = el;
            S._dragH = "move";
            S._ds = { x: e.clientX, y: e.clientY, ox: el.x, oy: el.y, ow: el.w, oh: el.h };
        });

        pg.appendChild(d);
    });

    // Draw column guides if columns are enabled
    if (S._colMode > 1) {
        var pageWidth = S._pw - 30 * S._sc;
        var pageMargin = 20 * S._sc;
        var colWidth = (pageWidth - (S._colMode - 1) * S._colGap * S._sc) / S._colMode;
        for (var i = 1; i < S._colMode; i++) {
            var guide = document.createElement("div");
            guide.className = "col-guide";
            guide.style.position = "absolute";
            guide.style.left = (pageMargin + i * (colWidth + S._colGap * S._sc)) + "px";
            guide.style.top = "0";
            guide.style.width = "1px";
            guide.style.height = S._ph + "px";
            guide.style.backgroundColor = "rgba(100, 150, 255, 0.3)";
            guide.style.pointerEvents = "none";
            guide.style.zIndex = "1";
            pg.appendChild(guide);
        }
    }
    // Update status bar
    if (S.updateStatusBar) S.updateStatusBar();
}

// ── Exports ──
S.populateFonts = populateFonts;
S.drawAlignmentGuides = drawAlignmentGuides;
S.clearAlignmentGuides = clearAlignmentGuides;
S.add = add;
S.select = select;
S.updateStatusBar = updateStatusBar;
S.updateProps = updateProps;
S.getShapePath = getShapePath;
S.render = render;

})();
