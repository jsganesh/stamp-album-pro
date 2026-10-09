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
        theme: S._theme,
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
        // Map the file's page size onto a real paper size (also repairs albums saved by v0.2.0 and earlier)
        var size = CORE.normalizePageSize(state.pw, state.ph);
        var outside = size.migrated ? CORE.countOutside(state.pages, size.pw, size.ph) : 0;
        state.pw = size.pw; state.ph = size.ph;
        for (var pi = 0; pi < state.pages.length; pi++) {
            for (var ei = 0; ei < state.pages[pi].length; ei++) {
                var el = state.pages[pi][ei];
                el.x = px(el.x); el.y = px(el.y);
                el.w = px(el.w); el.h = px(el.h);
            }
        }
        S.applyPageSize(state.pw, state.ph);
        S._pageBorder = state.pageBorder;
        S._pageBorderC = state.pageBorderC;
        S._theme = state.theme;
        S._colMode = state.colMode;
        S._colGap = state.colGap;
        S._pages = JSON.parse(JSON.stringify(state.pages));
        S.E = S._pages[state.currentPage] || [];
        S._currentPage = state.currentPage;
        S.sel = null;
        // DOM updates (applyPageSize above sized the page and its label)
        $("page").className = "page";
        // Columns have no toolbar control; an album that has them keeps them (S._colMode).
        S.syncPageBar();
        S.renderPageDots();
        render();
        S.updateProps();
        S.updateGrid();
        S.updateTitle();
        if (size.migrated) {
            showToast("Page size corrected to " + size.pw + " x " + size.ph + " mm (older versions saved it oversized)." +
                (outside ? " " + outside + " element" + (outside === 1 ? "" : "s") + " now extend past the page edge." : ""), "info");
        }
    }
    applyState();
}

// ── Exports ──
S.escapeDSL = escapeDSL;
S.buildDSL = buildDSL;
S.parseDSL = parseDSL;

})();
