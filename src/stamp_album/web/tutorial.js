"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast, parseDSL = S.parseDSL, updateTitle = S.updateTitle;

// ── First-run tutorial ──
var _tutorialStep = 1;
var _tutorialMax = 4;

function initTutorial() {
    if (localStorage.getItem("stampalbum-tutorial-done")) return;

    // Auto-load a sample album so the canvas isn't empty
    var sampleDSL = [
        'ALBUM_TITLE("My First Album")',
        'ALBUM_PAGES_SIZE(210.0 297.0)',
        'ALBUM_PAGES_MARGINS(15 15 15 15)',
        'PAGE_START',
        'PAGE_TEXT_CENTRE("HB" 16 "Great Britain — Victorian Era")',
        'PAGE_TEXT_CENTRE("HN" 10 "A sample album page to get you started")',
        'PAGE_VSPACE(8)',
        'ROW_START_FS("HN" 8 6.0 6.0)',
        'STAMP_ADD_AT(15.0 40.0 60.0 45.0 "Penny Black — 1840" "rectangle" "solid" "#fff")',
        'STAMP_ADD_AT(81.0 40.0 60.0 45.0 "Penny Red — 1841" "rectangle" "solid" "#fff")',
        'STAMP_ADD_AT(147.0 40.0 60.0 45.0 "Twopence Blue — 1840" "rectangle" "solid" "#fff")',
    ].join("\n");
    parseDSL(sampleDSL);
    S._dirty = false;
    updateTitle();

    var overlay = $("tutorial-overlay");
    if (overlay) {
        overlay.classList.add("open");
        _tutorialStep = 1;
        _showTutorialStep();
    }
}

function _showTutorialStep() {
    var overlay = $("tutorial-overlay");
    if (!overlay) return;
    overlay.querySelectorAll(".tutorial-step").forEach(function(el) {
        el.classList.toggle("active", parseInt(el.dataset.step) === _tutorialStep);
    });
    var nextBtn = $("btn-tutorial-next");
    if (nextBtn) {
        nextBtn.textContent = _tutorialStep >= _tutorialMax ? "Get Started" : "Next";
    }
}

// Event handlers (wired in init.js after DOM ready)
function _wireTutorialEvents() {
    $("btn-tutorial-next").addEventListener("click", function() {
        _tutorialStep++;
        if (_tutorialStep > _tutorialMax) {
            $("tutorial-overlay").classList.remove("open");
            localStorage.setItem("stampalbum-tutorial-done", "1");
        } else {
            _showTutorialStep();
        }
    });
    $("btn-tutorial-skip").addEventListener("click", function() {
        $("tutorial-overlay").classList.remove("open");
        localStorage.setItem("stampalbum-tutorial-done", "1");
    });
}

// ── Exports ──
S.initTutorial = initTutorial;
S._wireTutorialEvents = _wireTutorialEvents;

})();
