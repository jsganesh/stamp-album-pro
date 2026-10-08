"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, mm = S.mm, px = S.px, showToast = S.showToast;
var render = S.render;
var CORE = window.StampAlbumDSL || {};

// ── Delegate to core, add S/DOM integration ──

function escapeDSL(s) {
    return CORE.escapeDSL(s);
}

function _serializeEl(el) {
    var elMM = {
        x: mm(el.x), y: mm(el.y), w: mm(el.w), h: mm(el.h),
        t: el.t, s: el.s,
        lbl: el.lbl, img: el.img,
        bdr: el.bdr, bdrC: el.bdrC, bdrW: el.bdrW,
        fill: el.fill, fillA: el.fillA,
        font: el.font, fs: el.fs, align: el.align
    };
    return CORE.serializeEl(elMM);
}

function buildDSL() {
    // Gather state from S (convert px → mm), delegate to core
    var allPages = [];
    for (var pi = 0; pi < S._pages.length; pi++) {
        allPages.push(pi === S._currentPage
            ? JSON.parse(JSON.stringify(S.E))
            : JSON.parse(JSON.stringify(S._pages[pi] || [])));
    }
    // Convert all elements px → mm
    for (var pi = 0; pi < allPages.length; pi++) {
        for (var ei = 0; ei < allPages[pi].length; ei++) {
            var el = allPages[pi][ei];
            el.x = mm(el.x); el.y = mm(el.y);
            el.w = mm(el.w); el.h = mm(el.h);
        }
    }
    var state = {
        pages: allPages,
        pw: mm(S._pw), ph: mm(S._ph),
        pageBorder: S._pageBorder,
        pageBorderC: S._pageBorderC,
        colMode: S._colMode || 1,
        colGap: S._colGap || 10,
        currentFile: S._currentFile || ""
    };
    return CORE.buildDSL(state);
}

function parseDSL(dsl) {
    var state = CORE.parseDSL(dsl);
    // Apply state to S (convert mm → px)
    function applyState() {
        for (var pi = 0; pi < state.pages.length; pi++) {
            for (var ei = 0; ei < state.pages[pi].length; ei++) {
                var el = state.pages[pi][ei];
                el.x = px(el.x); el.y = px(el.y);
                el.w = px(el.w); el.h = px(el.h);
            }
        }
        S._pw = state.pw * S._sc;
        S._ph = state.ph * S._sc;
        S._pageBorder = state.pageBorder;
        S._pageBorderC = state.pageBorderC;
        S._colMode = state.colMode;
        S._colGap = state.colGap;
        S._pages = JSON.parse(JSON.stringify(state.pages));
        S.E = S._pages[state.currentPage] || [];
        S._currentPage = state.currentPage;
        S.sel = null;
        // DOM updates
        if (state.pw === 210 && state.ph === 297) {
            $("pg-size").value = "a4";
        }
        if (state.colMode > 1) {
            $("col-mode").value = state.colMode;
            $("col-gap").value = state.colGap;
        } else {
            $("col-mode").value = 1;
            $("col-gap").value = 10.0;
        }
        S.renderPageDots();
        render();
        S.updateProps();
        S.updateGrid();
        S.updateTitle();
    }
    applyState();
}

// ── Exports ──
S.escapeDSL = escapeDSL;
S.buildDSL = buildDSL;
S.parseDSL = parseDSL;

})();
