"use strict";
// ── Print preview ──
// The album drawn by the same code as the exports (POST /render-from-state), one
// page at a time, so what is shown here is what will print. It opens on the page
// being edited and is drawn fresh each time it opens (and when the paper changes
// while it is open), so there is nothing to refresh.
//
// The page is shown whole, as large as the window allows (up to FIT_MAX, as in
// the editor's Fit whole page).
// Page arrows (and the ← → keys) step through the pages; Escape closes.
(function(root){

var FIT_MAX = 2;

// The scale that fits a w × h page into availW × availH, rounded down so it never
// overflows; at most FIT_MAX. Pure, for the tests.
function fitScale(availW, availH, w, h) {
    if (!(w > 0) || !(h > 0) || !(availW > 0) || !(availH > 0)) return 1;
    var z = Math.min(FIT_MAX, availW / w, availH / h);
    return Math.max(0.05, Math.floor(z * 1000 + 1e-9) / 1000);
}

// The printed page that shows editor page `current`: the export leaves out empty
// pages before the first page with something on it and after the last, so the
// index moves back by the empty pages in front and stays within the printed pages.
function printedIndex(pageSizes, current, printedCount) {
    var first = 0;
    while (first < pageSizes.length && pageSizes[first] === 0) first++;
    var i = current - first;
    return Math.max(0, Math.min(printedCount - 1, i));
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = { fitScale: fitScale, printedIndex: printedIndex, FIT_MAX: FIT_MAX };
}
if (!root || !root.document || !root.StampAlbum) return;

var S = root.StampAlbum, $ = S.$;
var _idx = 0, _count = 0, _w = 0, _h = 0, _timer = null, _seq = 0, _opener = null;

function isOpen() {
    var o = $("preview-overlay");
    return !!(o && o.classList.contains("open"));
}

function frameDoc() {
    var f = $("preview-frame");
    try { return f && f.contentDocument; } catch (_) { return null; }
}

function setLoading(on) {
    var n = $("pv-loading");
    if (n) n.hidden = !on;
    var box = $("pv-box");
    if (box) box.style.visibility = on ? "hidden" : "";
}

// The page sizes of the album as it is now (the page being edited may have
// changed since it was last stored in S._pages).
function pageSizes() {
    return S._pages.map(function(p, i) { return (i === S._currentPage ? S.E : p).length; });
}

// Show printed page _idx only, sized to fit.
function showPage() {
    var doc = frameDoc();
    if (!doc) return;
    var pages = doc.querySelectorAll(".page");
    _count = pages.length;
    _idx = Math.max(0, Math.min(_count - 1, _idx));
    for (var i = 0; i < pages.length; i++) pages[i].style.display = i === _idx ? "" : "none";
    var pg = pages[_idx];
    if (pg) { _w = pg.offsetWidth; _h = pg.offsetHeight; }
    syncPager();
    applySize();
}

// Size the drawing: the iframe holds the page at its CSS size and is scaled.
function applySize() {
    var body = $("preview-body"), box = $("pv-box"), f = $("preview-frame");
    if (!body || !box || !f || !(_w > 0)) return;
    var cs = root.getComputedStyle(body);
    var aw = body.clientWidth - (parseFloat(cs.paddingLeft) || 0) - (parseFloat(cs.paddingRight) || 0);
    var ah = body.clientHeight - (parseFloat(cs.paddingTop) || 0) - (parseFloat(cs.paddingBottom) || 0);
    var z = fitScale(aw, ah, _w, _h);
    f.style.width = _w + "px";
    f.style.height = _h + "px";
    f.style.transform = z === 1 ? "" : "scale(" + z + ")";
    box.style.width = _w * z + "px";
    box.style.height = _h * z + "px";
    box.dataset.scale = String(z);
}

function syncPager() {
    var nav = $("pv-pager");
    if (!nav) return;
    nav.hidden = _count < 2;
    $("pv-count").textContent = S.t("msg.page_n_of", { n: _idx + 1, total: _count });
    $("pv-prev").disabled = _idx <= 0;
    $("pv-next").disabled = _idx >= _count - 1;
}

function goPage(i) {
    if (i < 0 || i >= _count || i === _idx) return;
    _idx = i;
    showPage();
    $("preview-body").scrollTop = 0;
}

// Draw the album again. `keepPage`: stay on the printed page shown now
// (a redraw while open); otherwise go to the page being edited.
function draw(keepPage) {
    if (!isOpen()) return Promise.resolve();
    var seq = ++_seq;
    setLoading(true);
    var state = S.buildCanvasState("html");
    return fetch("/render-from-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
    })
    .then(function(r) {
        if (!r.ok) throw new Error(S.t("msg.render_failed_status", { status: r.status }));
        return r.text();
    })
    .then(function(html) {
        if (seq !== _seq) return;  // a newer drawing has started
        return new Promise(function(resolve) {
            var f = $("preview-frame");
            f.onload = function() {
                f.onload = null;
                if (seq !== _seq) { resolve(); return; }
                var doc = frameDoc();
                var n = doc ? doc.querySelectorAll(".page").length : 0;
                if (!keepPage) _idx = printedIndex(pageSizes(), S._currentPage, n);
                setLoading(false);
                showPage();
                resolve();
            };
            f.srcdoc = html;
        });
    })
    .catch(function(err) {
        if (seq !== _seq) return;
        setLoading(false);
        var msg = err.message || String(err);
        var net = /NetworkError|Load failed|Failed to fetch/.test(msg);
        S.showToast(net ? S.t("msg.preview_failed_network") : S.t("msg.preview_failed", { msg: msg }), "error");
    });
}

function openPreview() {
    var o = $("preview-overlay");
    if (!o) return Promise.resolve();
    if (!isOpen()) _opener = document.activeElement;
    o.classList.add("open");
    var close = $("btn-preview-close");
    if (close) close.focus();
    return draw(false);
}

function closePreview() {
    var o = $("preview-overlay");
    if (!o || !isOpen()) return;
    o.classList.remove("open");
    _seq++;  // a drawing still on its way is not wanted
    if (_opener && _opener.focus && document.contains(_opener)) _opener.focus();
    _opener = null;
}

// A change made while the preview is open (the paper size) redraws it.
function schedulePreviewRefresh() {
    if (!isOpen()) return;
    if (_timer) clearTimeout(_timer);
    _timer = setTimeout(function() { _timer = null; draw(true); }, 400);
}

// The preview's keys. Also called by the editor's key handler while the preview
// is open and the focus is outside it, so the editor's shortcuts never act
// on the page underneath.
function onKey(e) {
    if (e.key === "Escape") { e.preventDefault(); closePreview(); return; }
    if (e.target && e.target.closest && e.target.closest(".export-dd")) return;  // the Export menu's keys
    if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); goPage(_idx - 1); }
    else if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); goPage(_idx + 1); }
    else if (e.key === "Home") { e.preventDefault(); goPage(0); }
    else if (e.key === "End") { e.preventDefault(); goPage(_count - 1); }
}

function wire() {
    var o = $("preview-overlay");
    if (!o) return;
    $("btn-preview-close").addEventListener("click", closePreview);
    $("pv-prev").addEventListener("click", function() { goPage(_idx - 1); });
    $("pv-next").addEventListener("click", function() { goPage(_idx + 1); });
    // The preview is a dialog: its keys stay inside it.
    o.addEventListener("keydown", function(e) { onKey(e); e.stopPropagation(); });
    if (root.ResizeObserver) new root.ResizeObserver(function() { if (isOpen()) applySize(); }).observe($("preview-body"));
    root.addEventListener("resize", function() { if (isOpen()) applySize(); });
}

S.openPreview = openPreview;
S.closePreview = closePreview;
S.previewOpen = isOpen;
S.previewKey = onKey;
S.schedulePreviewRefresh = schedulePreviewRefresh;
S.refreshPreview = function() { return draw(true); };
S.previewPage = function() { return { index: _idx, count: _count }; };
S.syncPreviewLanguage = function() { if (isOpen()) syncPager(); };

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire);
else wire();

})(typeof window !== "undefined" ? window : null);
