"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$;

// ── Ornamental Border Styles ──
// Each border is defined as SVG paths for corners + edge patterns
var BORDER_STYLES = {
    none: { name: "None", description: "No border" },
    solid: { name: "Solid", description: "Simple solid line" },
    double: { name: "Double", description: "Double-line rule" },
    dashed: { name: "Dashed", description: "Dashed line border" },
    dotted: { name: "Dotted", description: "Dotted line border" },
    // Ornamental styles
    classic: {
        name: "Classic Ornate",
        description: "Victorian-style corner flourishes with double rule",
        corners: true,
        pattern: "double",
        color: "#8B0000"
    },
    victorian: {
        name: "Victorian Filigree",
        description: "Elaborate Victorian scrollwork corners",
        corners: true,
        pattern: "ornate",
        color: "#4A3728"
    },
    artdeco: {
        name: "Art Deco",
        description: "Geometric 1920s-style stepped corners",
        corners: true,
        pattern: "geometric",
        color: "#1A3A6B"
    },
    greek_key: {
        name: "Greek Key",
        description: "Meander / Greek key pattern along edges",
        corners: false,
        pattern: "meander",
        color: "#2C2C2C"
    },
    rope: {
        name: "Rope Twist",
        description: "Twisted rope border pattern",
        corners: false,
        pattern: "rope",
        color: "#6B4423"
    },
    laurel: {
        name: "Laurel Wreath",
        description: "Leaf and berry corner ornaments",
        corners: true,
        pattern: "laurel",
        color: "#2D5016"
    },
    gothic: {
        name: "Gothic Arch",
        description: "Gothic cathedral-inspired pointed arches",
        corners: true,
        pattern: "gothic",
        color: "#333"
    },
    filigree: {
        name: "Filigree Gold",
        description: "Delicate gold filigree with corner rosettes",
        corners: true,
        pattern: "filigree",
        color: "#B8860B"
    }
};

// ── Ornament bounding boxes (width/height in SVG units) ──
var ORNAMENT_BBOX = {
    classic: { w: 62, h: 82 },
    victorian: { w: 42, h: 87 },
    artdeco: { w: 43, h: 85 },
    laurel: { w: 22, h: 62 },
    gothic: { w: 32, h: 85 },
    filigree: { w: 65, h: 65 }
};

// ── SVG Corner Ornaments ──
function cornerOrnament(style, corner) {
    // corner: tl, tr, br, bl
    var bbox = ORNAMENT_BBOX[style] || { w: 60, h: 80 };
    var transforms = {
        tl: "",
        tr: "scale(-1,1) translate(-" + bbox.w + ",0)",
        br: "scale(-1,-1) translate(-" + bbox.w + ",-" + bbox.h + ")",
        bl: "scale(1,-1) translate(0,-" + bbox.h + ")"
    };
    var t = transforms[corner] || "";

    if (style === "classic") {
        return '<g transform="' + t + '">' +
            '<path d="M5,80 Q5,20 20,20 Q40,20 45,5 Q50,0 60,0" fill="none" stroke="COLOR" stroke-width="1.2"/>' +
            '<path d="M5,60 Q5,15 15,10 Q30,5 35,2" fill="none" stroke="COLOR" stroke-width="0.8"/>' +
            '<circle cx="8" cy="8" r="2" fill="COLOR"/>' +
            '<circle cx="20" cy="5" r="1.2" fill="COLOR"/>' +
            '</g>';
    }
    if (style === "victorian") {
        return '<g transform="' + t + '">' +
            '<path d="M0,85 C10,85 15,70 25,60 C35,50 30,35 20,25 C15,20 10,15 5,10 C10,12 15,18 25,22 C35,26 40,20 35,10" fill="none" stroke="COLOR" stroke-width="1.2"/>' +
            '<path d="M0,75 C8,75 12,65 20,58 C28,51 25,40 18,32 C14,28 10,24 8,18" fill="none" stroke="COLOR" stroke-width="0.7"/>' +
            '<circle cx="5" cy="5" r="2.5" fill="COLOR"/>' +
            '<circle cx="15" cy="12" r="1.5" fill="COLOR"/>' +
            '<circle cx="25" cy="8" r="1" fill="COLOR"/>' +
            '</g>';
    }
    if (style === "artdeco") {
        return '<g transform="' + t + '">' +
            '<rect x="0" y="60" width="40" height="3" fill="COLOR"/>' +
            '<rect x="0" y="50" width="30" height="3" fill="COLOR"/>' +
            '<rect x="0" y="40" width="20" height="3" fill="COLOR"/>' +
            '<rect x="0" y="30" width="10" height="3" fill="COLOR"/>' +
            '<rect x="40" y="60" width="3" height="25" fill="COLOR"/>' +
            '<rect x="30" y="50" width="3" height="15" fill="COLOR"/>' +
            '<rect x="20" y="40" width="3" height="5" fill="COLOR"/>' +
            '</g>';
    }
    if (style === "laurel") {
        return '<g transform="' + t + '">' +
            '<path d="M5,80 Q15,60 10,40 Q8,30 15,20" fill="none" stroke="COLOR" stroke-width="1"/>' +
            '<ellipse cx="12" cy="35" rx="4" ry="2.5" fill="COLOR" transform="rotate(-30 12 35)"/>' +
            '<ellipse cx="8" cy="45" rx="4" ry="2.5" fill="COLOR" transform="rotate(-20 8 45)"/>' +
            '<ellipse cx="15" cy="55" rx="4" ry="2.5" fill="COLOR" transform="rotate(-40 15 55)"/>' +
            '<ellipse cx="18" cy="28" rx="3.5" ry="2" fill="COLOR" transform="rotate(-45 18 28)"/>' +
            '<circle cx="14" cy="22" r="1.5" fill="COLOR"/>' +
            '<circle cx="10" cy="50" r="1.2" fill="COLOR"/>' +
            '</g>';
    }
    if (style === "gothic") {
        return '<g transform="' + t + '">' +
            '<path d="M0,85 L0,40 Q0,20 15,10 Q25,3 30,0" fill="none" stroke="COLOR" stroke-width="1.5"/>' +
            '<path d="M5,85 L5,45 Q5,28 18,18 Q25,12 28,8" fill="none" stroke="COLOR" stroke-width="0.8"/>' +
            '<path d="M15,0 Q20,5 22,12" fill="none" stroke="COLOR" stroke-width="0.6"/>' +
            '</g>';
    }
    if (style === "filigree") {
        return '<g transform="' + t + '">' +
            '<circle cx="20" cy="20" r="15" fill="none" stroke="COLOR" stroke-width="0.8"/>' +
            '<circle cx="20" cy="20" r="10" fill="none" stroke="COLOR" stroke-width="0.5"/>' +
            '<circle cx="20" cy="20" r="5" fill="none" stroke="COLOR" stroke-width="0.5"/>' +
            '<circle cx="20" cy="20" r="2" fill="COLOR"/>' +
            '<path d="M20,35 Q25,50 30,65" fill="none" stroke="COLOR" stroke-width="0.6"/>' +
            '<path d="M35,20 Q50,25 65,30" fill="none" stroke="COLOR" stroke-width="0.6"/>' +
            '<circle cx="30" cy="30" r="1.5" fill="COLOR"/>' +
            '<circle cx="35" cy="35" r="1" fill="COLOR"/>' +
            '</g>';
    }
    return "";
}

// ── Edge Pattern SVG ──
function edgePattern(style, edge, w, h) {
    // edge: top, bottom, left, right
    var color = BORDER_STYLES[style] ? BORDER_STYLES[style].color : "#333";
    var svg = "";

    if (style === "greek_key") {
        var step = 12;
        var count = Math.floor((edge === "top" || edge === "bottom" ? w : h) / step);
        var isH = edge === "top" || edge === "bottom";
        for (var i = 0; i < count; i++) {
            var x = isH ? i * step : 0;
            var y = isH ? 0 : i * step;
            svg += '<path d="M' + x + ',' + (isH ? 4 : 0) + ' l' + (step/4) + ',0 l0,' + (isH ? 0 : step/4) + ' l' + (step/2) + ',0 l0,-' + (isH ? 0 : step/4) + ' l' + (step/4) + ',0" fill="none" stroke="' + color + '" stroke-width="0.8"/>';
        }
    }
    else if (style === "rope") {
        var rStep = 8;
        var rCount = Math.floor((edge === "top" || edge === "bottom" ? w : h) / rStep);
        var rH = edge === "top" || edge === "bottom";
        for (var j = 0; j < rCount; j++) {
            var rx = rH ? j * rStep + rStep/2 : 2;
            var ry = rH ? 2 : j * rStep + rStep/2;
            svg += '<circle cx="' + rx + '" cy="' + ry + '" r="2" fill="none" stroke="' + color + '" stroke-width="0.7"/>';
        }
    }
    return svg;
}

// ── Render Page Border ──
function renderPageBorder(style) {
    var existing = $("page-border");
    if (existing) existing.remove();
    if (!style || style === "none") return;

    var pg = $("page");
    if (!pg) return;

    var w = S._pw || 595;
    var h = S._ph || 842;
    var margin = 12;
    var color = S._pageBorderC || (BORDER_STYLES[style] && BORDER_STYLES[style].color) || "#333";

    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.id = "page-border";
    svg.setAttribute("width", w);
    svg.setAttribute("height", h);
    svg.style.cssText = "position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:2;";

    var inner = '';

    if (style === "solid") {
        inner = '<rect x="' + margin + '" y="' + margin + '" width="' + (w - margin*2) + '" height="' + (h - margin*2) + '" fill="none" stroke="' + color + '" stroke-width="1"/>';
    }
    else if (style === "double") {
        inner = '<rect x="' + margin + '" y="' + margin + '" width="' + (w - margin*2) + '" height="' + (h - margin*2) + '" fill="none" stroke="' + color + '" stroke-width="1.2"/>' +
            '<rect x="' + (margin+4) + '" y="' + (margin+4) + '" width="' + (w - margin*2 - 8) + '" height="' + (h - margin*2 - 8) + '" fill="none" stroke="' + color + '" stroke-width="0.5"/>';
    }
    else if (style === "dashed") {
        inner = '<rect x="' + margin + '" y="' + margin + '" width="' + (w - margin*2) + '" height="' + (h - margin*2) + '" fill="none" stroke="' + color + '" stroke-width="1" stroke-dasharray="6,3"/>';
    }
    else if (style === "dotted") {
        inner = '<rect x="' + margin + '" y="' + margin + '" width="' + (w - margin*2) + '" height="' + (h - margin*2) + '" fill="none" stroke="' + color + '" stroke-width="1.2" stroke-dasharray="2,3"/>';
    }
    else if (BORDER_STYLES[style] && BORDER_STYLES[style].corners) {
        // Ornamental border with corners

        // Double rule frame
        inner += '<rect x="' + margin + '" y="' + margin + '" width="' + (w - margin*2) + '" height="' + (h - margin*2) + '" fill="none" stroke="' + color + '" stroke-width="1.2"/>';
        inner += '<rect x="' + (margin+4) + '" y="' + (margin+4) + '" width="' + (w - margin*2 - 8) + '" height="' + (h - margin*2 - 8) + '" fill="none" stroke="' + color + '" stroke-width="0.5"/>';

        // Corner ornaments — position each at the actual page corner (inside margin)
        var corners = { tl: [margin, margin], tr: [w - margin, margin], br: [w - margin, h - margin], bl: [margin, h - margin] };
        ["tl", "tr", "br", "bl"].forEach(function(c) {
            var orn = cornerOrnament(style, c).replace(/COLOR/g, color);
            inner += '<g transform="translate(' + corners[c][0] + ',' + corners[c][1] + ')">' + orn + '</g>';
        });
    }
    else if (style === "greek_key" || style === "rope") {
        // Edge pattern borders
        var pColor = BORDER_STYLES[style].color;
        // Top
        inner += '<g>' + edgePattern(style, "top", w, h).replace(/COLOR/g, pColor) + '</g>';
        // Bottom
        inner += '<g transform="translate(0,' + (h - 8) + ')">' + edgePattern(style, "bottom", w, h).replace(/COLOR/g, pColor) + '</g>';
        // Left
        inner += '<g transform="rotate(-90) translate(-' + h + ',0)">' + edgePattern(style, "left", h, w).replace(/COLOR/g, pColor) + '</g>';
        // Right
        inner += '<g transform="rotate(90) translate(0,-' + (w - 8) + ')">' + edgePattern(style, "right", h, w).replace(/COLOR/g, pColor) + '</g>';
    }

    svg.innerHTML = inner;
    pg.appendChild(svg);
}

// ── Get border style list for dropdown ──
function getBorderStyles() {
    return Object.keys(BORDER_STYLES).map(function(k) {
        return { id: k, name: BORDER_STYLES[k].name, description: BORDER_STYLES[k].description };
    });
}

// ── Exports ──
S.renderPageBorder = renderPageBorder;
S.getBorderStyles = getBorderStyles;
S.BORDER_STYLES = BORDER_STYLES;

})();
