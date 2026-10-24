"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$;
var CORE = window.StampAlbumDSL || {};

// ── Check exhibit (View menu) ──
// Goes through the album for what FIP guidelines would mark down (dsl_core.js exhibitCheck):
// things to fix first, then advice, each with a button to go to its page.

function allPages() {
    var pages = S._pages.slice();
    pages[S._currentPage] = S.E;
    return pages;
}

// Each page's items in mm, as exhibitCheck takes them.
function pagesInMm(pages) {
    var sc = S._sc;
    return pages.map(function(p) {
        return (p || []).map(function(el) {
            return Object.assign({}, el, { x: el.x / sc, y: el.y / sc, w: el.w / sc, h: el.h / sc });
        });
    });
}

// For each page, how many items have captions or frames running past the border or into
// something: the editor's "!" badges (render.js markCaptionWarnings), counted on every page.
function warningsPerPage(pagesMm) {
    var inset = S.borderInsetPx ? S.borderInsetPx(S._pageBorder) / S._sc : 0;
    var area = { l: inset, t: inset, r: S._pw / S._sc - inset, b: S._ph / S._sc - inset };
    return pagesMm.map(function(p) {
        var items = p.map(function(el) {
            var lines = CORE.hasCaptions(el)
                ? CORE.captionLayout(el, el.x, el.y, el.w, el.h, null, { headingWeight: S._captionHeading }) : [];
            var box = CORE.frameBox(el, el.x, el.y, el.w, el.h);
            return { id: el.id, box: box, lines: lines, framed: el.t === "stamp" && box.w > el.w };
        });
        return Object.keys(CORE.captionWarnings(items, area)).length;
    });
}

function findings() {
    var pages = allPages(), mmPages = pagesInMm(pages);
    return CORE.exhibitCheck({ pages: mmPages, pw: S._pw / S._sc, ph: S._ph / S._sc,
                               pageBorder: S._pageBorder, warnings: warningsPerPage(mmPages) });
}

// The words for each finding (dsl_core.js exhibitCheck codes).
var PHRASES = {
    no_plan: "msg.check_no_plan", plan_not_first: "msg.check_plan_not_first", plan_empty: "msg.check_plan_empty",
    decorative_border: "msg.check_decorative_border", empty_page: "msg.check_empty_page",
    no_heading: "msg.check_no_heading", chapter_gone: "msg.check_chapter_gone",
    unnamed_stamps: "msg.check_unnamed_stamps", caption_clash: "msg.check_caption_clash",
    paper: "msg.check_paper", frames: "msg.check_frames", frames_full: "msg.check_frames_full"
};
function sentence(f) {
    return S.t(PHRASES[f.code], { count: f.n, per: f.perFrame || 0, last: f.last || 0 });
}

function row(f) {
    var li = document.createElement("li");
    li.className = "chk-item " + f.level;
    var where = document.createElement("span");
    where.className = "chk-where";
    where.textContent = f.page === null ? S.t("msg.check_album") : S.t("ui.page_n", { n: f.page + 1 });
    var text = document.createElement("span");
    text.className = "chk-text";
    text.textContent = sentence(f);
    li.appendChild(where); li.appendChild(text);
    if (f.page !== null) {
        var go = document.createElement("button");
        go.type = "button";
        go.textContent = S.t("msg.go_to_page_n", { n: f.page + 1 });
        go.addEventListener("click", function() {
            closeCheck();
            if (f.page !== S._currentPage) S.switchPage(f.page);
        });
        li.appendChild(go);
    } else if (f.code === "no_plan") {
        var make = document.createElement("button");
        make.type = "button";
        make.textContent = S.t("ui.title_and_plan_page");
        make.addEventListener("click", function() { closeCheck(); S.openExhibitPlan(); });
        li.appendChild(make);
    }
    return li;
}

function openCheck() {
    if (S.commitPanelEdit) S.commitPanelEdit();
    var fs = findings();
    var fix = fs.filter(function(f) { return f.level === "fix"; });
    var advice = fs.filter(function(f) { return f.level !== "fix"; });
    $("chk-summary").textContent = fix.length
        ? S.t("msg.check_summary_fix", { count: fix.length })
        : S.t("msg.check_summary_none");
    $("chk-summary").classList.toggle("warn", fix.length > 0);
    [["chk-fix", "chk-fix-h", fix], ["chk-advice", "chk-advice-h", advice]].forEach(function(g) {
        var list = $(g[0]);
        list.textContent = "";
        g[2].forEach(function(f) { list.appendChild(row(f)); });
        list.hidden = !g[2].length;
        $(g[1]).hidden = !g[2].length;
    });
    $("check-overlay").classList.add("open");
    $("chk-close").focus();
}
function closeCheck() {
    $("check-overlay").classList.remove("open");
}

function wireCheck() {
    $("chk-close").addEventListener("click", closeCheck);
    $("chk-done").addEventListener("click", closeCheck);
    $("check-overlay").addEventListener("click", function(e) { if (e.target === this) closeCheck(); });
    $("check-overlay").addEventListener("keydown", function(e) {
        if (e.key === "Escape") { e.stopPropagation(); closeCheck(); }
    });
}

S.openCheck = openCheck;
S.exhibitFindings = findings;
S.wireCheck = wireCheck;

})();
