"use strict";
(function(){
var S = window.StampAlbum;
var $ = S.$, showToast = S.showToast, parseDSL = S.parseDSL, updateTitle = S.updateTitle;

// ── First-run tutorial ──
var _tutorialStep = 1;
var _tutorialMax = 4;

// draftRestored: the user's own work was restored, so don't replace it with the sample.
function initTutorial(draftRestored) {
    if (localStorage.getItem("stampalbum-tutorial-done")) return;
    if (!draftRestored) loadSampleAlbum();
    showTutorial();
}

// Open the tutorial overlay at step 1 (also View > Show tutorial again).
function showTutorial() {
    var overlay = $("tutorial-overlay");
    if (overlay) {
        overlay.classList.add("open");
        _tutorialStep = 1;
        _showTutorialStep();
    }
}

// Auto-load a sample album so the canvas isn't empty: an exhibition-style page with three
// stamps at their size (3/4 x 7/8 inch, 19 x 22 mm), so their frames show the 1 mm clearance.
// Numbers and dates are StampWorld's (Great Britain 1 to 3).
// The screenshot script (tools/screenshots.py) uses the same page.
var SAMPLE_DSL = [
    'ALBUM_PAGES_BORDER(0.5 0 0 1)',
    'ALBUM_PAGES_BORDER_STYLE("solid")',
    'COLOUR_ALBUM_BORDER("#000000")',
    'ALBUM_THEME("exhibition")',
    'ALBUM_TITLE("My First Album")',
    'ALBUM_PAGES_SIZE(210 297)',
    'ALBUM_PAGES_MARGINS(15 15 15 15)',
    'PAGE_START',
    'PAGE_TEXT_AT(20.0 18.0 170.0 12.0 "HB" 16 "Great Britain: The First Stamps" "center")',
    'PAGE_TEXT_ROLE("heading")',
    'PAGE_TEXT_AT(20.0 31.0 170.0 8.0 "HN" 10 "Line-engraved issues, 1840 to 1841" "center")',
    'STAMP_ADD_AT(51.5 55.0 19.0 22.0 "Penny Black" "StampWorld 1" "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)',
    'STAMP_HEADING("HN" 9 "1840")',
    'STAMP_DETAILS("1d" "Used" "Imperforate")',
    'STAMP_ADD_AT(95.5 55.0 19.0 22.0 "Twopence Blue" "StampWorld 2" "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)',
    'STAMP_HEADING("HN" 9 "1840")',
    'STAMP_DETAILS("2d" "Used" "Imperforate")',
    'STAMP_ADD_AT(139.5 55.0 19.0 22.0 "Penny Red" "StampWorld 3" "" "" rectangle "solid" "#000000" 0.5 "#ffffff" 100)',
    'STAMP_HEADING("HN" 9 "1841")',
    'STAMP_DETAILS("1d" "Used" "Imperforate")'
].join("\n");

function loadSampleAlbum() {
    parseDSL(SAMPLE_DSL);
    S._dirty = false;
    updateTitle();
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
S.loadSampleAlbum = loadSampleAlbum;
S.showTutorial = showTutorial;
S._wireTutorialEvents = _wireTutorialEvents;

})();
