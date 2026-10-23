"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$;
var CORE = window.StampAlbumDSL || {};

// ── Title and plan page ──
// A form for an exhibit's first page (FIP: title, purpose, scope, plan in chapters, important
// items, research, references). It makes ordinary text items, each marked with its part
// (el.part, PAGE_TEXT_PART in the file), and reads its answers back from them, so the page is
// the only record: an edit made on the page shows here, and the album needs nothing else saved.
// Applying again replaces only the items it made; anything else on that page stays.

// The fields for each section of the page (dsl_core.js PLAN_SECTIONS, plan aside).
var FIELDS = { purpose: "tp-purpose", scope: "tp-scope", important: "tp-important",
               research: "tp-research", references: "tp-references" };

// The section names as printed on the page, in the editor's language.
function labels() {
    return { purpose: S.t("ui.purpose"), scope: S.t("ui.scope"), plan: S.t("ui.plan_of_the_exhibit"),
             important: S.t("ui.important_items"), research: S.t("ui.research"), references: S.t("ui.references") };
}

// Every page of the open album, the current page's live items included.
function allPages() {
    var pages = S._pages.slice();
    pages[S._currentPage] = S.E;
    return pages;
}
function isPlanItem(el) {
    return !!el && el.t === "text" && CORE.PLAN_PART_NAMES.indexOf(el.part) !== -1;
}
// The index of the page holding the title and plan, or -1.
function planPage(pages) {
    for (var i = 0; i < pages.length; i++) {
        if ((pages[i] || []).some(isPlanItem)) return i;
    }
    return -1;
}

// Text widths in mm, as the exports set them (Helvetica, or Arial where it is missing, which
// has the same widths), with a little to spare so a box never comes out a line short.
var _ctx = null;
function measure(text, font, sizePt) {
    if (!_ctx) _ctx = document.createElement("canvas").getContext("2d");
    var f = S.fontCSS(font || "HN");
    _ctx.font = f.style + " " + f.weight + " " + sizePt + "pt " + f.family;
    return _ctx.measureText(String(text)).width * 25.4 / 96 * 1.04;
}

// ── The plan's chapters and sections ──
function chapterRows() {
    return Array.prototype.map.call(document.querySelectorAll("#tp-plan-list li"), function(li) {
        return { level: li.classList.contains("section") ? 2 : 1, text: li.querySelector("input").value };
    });
}
// Number the rows as the page will (1, 1.1, 1.2, 2…) and name each field and Remove button.
function renumber() {
    var ch = 0, sec = 0;
    document.querySelectorAll("#tp-plan-list li").forEach(function(li) {
        var num;
        if (li.classList.contains("section") && ch > 0) { sec++; num = ch + "." + sec; }
        else { ch++; sec = 0; num = String(ch); li.classList.remove("section"); }
        li.querySelector(".tp-num").textContent = num;
        li.querySelector("input").setAttribute("aria-label",
            S.t(li.classList.contains("section") ? "msg.section_n" : "msg.chapter_n", { n: num }));
        li.querySelector("button").setAttribute("aria-label", S.t("msg.remove_n", { n: num }));
    });
}
function addRow(level, text, focus, after) {
    var li = document.createElement("li");
    if (level === 2) li.className = "section";
    var num = document.createElement("span");
    num.className = "tp-num";
    num.setAttribute("aria-hidden", "true");
    var input = document.createElement("input");
    input.type = "text";
    input.value = text || "";
    input.addEventListener("input", updateNote);
    var rm = document.createElement("button");
    rm.type = "button";
    rm.textContent = S.t("ui.remove");
    rm.addEventListener("click", function() {
        var next = li.nextElementSibling || li.previousElementSibling;
        li.remove();
        renumber();
        updateNote();
        (next ? next.querySelector("input") : $("tp-add-chapter")).focus();
    });
    li.appendChild(num); li.appendChild(input); li.appendChild(rm);
    $("tp-plan-list").insertBefore(li, after ? after.nextElementSibling : null);
    renumber();
    if (focus) input.focus();
    return li;
}

// A text box grows with its text, so nothing in it is hidden (rows= is the least it shows).
function fitBox(ta) {
    ta.style.height = "auto";
    ta.style.height = (ta.scrollHeight + ta.offsetHeight - ta.clientHeight) + "px";
}
function fitBoxes() { Object.keys(FIELDS).forEach(function(n) { fitBox($(FIELDS[n])); }); }

// ── Reading and writing the form ──
function answers() {
    var a = { title: $("tp-title").value, by: $("tp-by").value, chapters: chapterRows() };
    Object.keys(FIELDS).forEach(function(name) { a[name] = $(FIELDS[name]).value; });
    return a;
}
function fill(items) {
    var text = function(part) {
        var el = items.find(function(x) { return x.part === part; });
        return el ? el.lbl || "" : "";
    };
    $("tp-title").value = text("title");
    $("tp-by").value = text("by");
    Object.keys(FIELDS).forEach(function(name) { $(FIELDS[name]).value = text(name); });
    $("tp-plan-list").textContent = "";
    CORE.planChapters(text("plan")).forEach(function(c) { addRow(c.level, c.text); });
}

// The page's items for the form as it stands, in mm.
function layout() {
    return CORE.exhibitPlanLayout(answers(), labels(), S._pw / S._sc, S._ph / S._sc, measure);
}

// Where the page will go, whether it fits, and what the button says.
function updateNote() {
    var pages = allPages(), idx = planPage(pages), r = layout();
    var note = $("tp-note"), apply = $("tp-apply");
    apply.textContent = S.t(idx === -1 ? "ui.make_the_page" : "ui.update_the_page");
    var warn = !String($("tp-title").value).trim() || !r.fits;
    note.classList.toggle("warn", warn);
    if (!String($("tp-title").value).trim()) note.textContent = S.t("msg.tp_empty");
    else if (!r.fits) note.textContent = S.t("msg.tp_too_long", { mm: Math.ceil(r.bottom - r.limit) });
    else if (idx !== -1) note.textContent = S.t("msg.tp_update_page", { n: idx + 1 });
    else if (!(pages[0] || []).length) note.textContent = S.t("msg.tp_use_page_1");
    else note.textContent = S.t("msg.tp_new_page");
    apply.disabled = warn;
}

function openExhibitPlan() {
    var pages = allPages(), idx = planPage(pages);
    fill(idx === -1 ? [] : pages[idx].filter(isPlanItem));
    if (!document.querySelector("#tp-plan-list li")) addRow(1, "");
    updateNote();
    $("plan-overlay").classList.add("open");
    fitBoxes();
    $("tp-title").focus();
}
function closeExhibitPlan() {
    $("plan-overlay").classList.remove("open");
}

// Make or update the page: one undo step.
function applyExhibitPlan() {
    var r = layout();
    if (!r.fits || !String($("tp-title").value).trim()) { updateNote(); return; }
    var pages = allPages().map(function(p) { return (p || []).slice(); });
    var idx = planPage(pages), made = idx === -1;
    var items = r.items.map(function(it) {
        var el = { id: "el" + (S.nid++), t: "text", s: "text", x: S.px(it.x), y: S.px(it.y), w: S.px(it.w), h: S.px(it.h),
                   lbl: it.lbl, font: it.font, fs: it.fs, align: it.align, bdr: "none", fill: "transparent", fillA: 0, part: it.part };
        if (it.role) el.role = it.role;
        return el;
    });
    if (!made) {
        pages[idx] = pages[idx].filter(function(el) { return !isPlanItem(el); }).concat(items);
    } else if (!pages[0].length) {
        idx = 0;
        pages[0] = items;
    } else {
        idx = 0;
        pages.unshift(items);
    }
    closeExhibitPlan();
    S._pages = pages;
    S._currentPage = idx;
    S.E = JSON.parse(JSON.stringify(pages[idx]));
    S.sel = null;
    S.pushUndo();
    S.renderPageDots();
    S.render();
    S.updateProps();
    if (S.schedulePreviewRefresh) S.schedulePreviewRefresh();
    S.showToast(S.t(made ? "msg.tp_made" : "msg.tp_updated"), "success");
}

function wireExhibitPlan() {
    $("btn-exhibit-plan").addEventListener("click", openExhibitPlan);
    $("tp-cancel").addEventListener("click", closeExhibitPlan);
    $("tp-close").addEventListener("click", closeExhibitPlan);
    $("tp-apply").addEventListener("click", applyExhibitPlan);
    $("tp-add-chapter").addEventListener("click", function() { addRow(1, "", true); updateNote(); });
    $("tp-add-section").addEventListener("click", function() { addRow(2, "", true); updateNote(); });
    ["tp-title", "tp-by"].forEach(function(id) { $(id).addEventListener("input", updateNote); });
    Object.keys(FIELDS).forEach(function(n) {
        $(FIELDS[n]).addEventListener("input", function() { fitBox(this); updateNote(); });
    });
    $("plan-overlay").addEventListener("click", function(e) {
        if (e.target === this) closeExhibitPlan();
    });
    $("plan-overlay").addEventListener("keydown", function(e) {
        if (e.key === "Escape") { e.stopPropagation(); closeExhibitPlan(); }
        // Enter in a chapter or section adds the next row below it, at the same level.
        else if (e.key === "Enter" && e.target.closest && e.target.closest("#tp-plan-list")) {
            e.preventDefault();
            var li = e.target.closest("li");
            addRow(li.classList.contains("section") ? 2 : 1, "", true, li);
            updateNote();
        }
    });
}

// ── Exports ──
S.openExhibitPlan = openExhibitPlan;
S.applyExhibitPlan = applyExhibitPlan;
S.wireExhibitPlan = wireExhibitPlan;

})();
