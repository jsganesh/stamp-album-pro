"use strict";
(function(){
var S = window.StampAlbum;

// ── Undo/redo system — uses S._undoStack / S._redoStack / S._undoPaused ──
// Each entry is a snapshot of the whole album (every page, the page size, page border
// and theme), so page-level changes such as Page setup or a theme undo in one step.
// The top of _undoStack is always the current state.

function snapshot() {
    var pages = S._pages.slice();
    pages[S._currentPage] = S.E;
    return JSON.stringify({ v: 2, pages: pages, cur: S._currentPage, pw: S._pw, ph: S._ph,
                            border: S._pageBorder || "", borderC: S._pageBorderC || "", theme: S._theme });
}

function pushUndo() {
    if (S._undoPaused) return;
    S._undoStack.push(snapshot());
    if (S._undoStack.length > 50) S._undoStack.shift();
    S._redoStack = [];
    S._dirty = true;
    S.updateTitle();
    S.scheduleDraftSave();
    if (S.updateSelectionUI) S.updateSelectionUI();
}
// Start a fresh history whose first entry is the album as it is now.
function resetUndo() {
    S._undoStack = [snapshot()];
    S._redoStack = [];
    if (S.updateSelectionUI) S.updateSelectionUI();
}
function undo() {
    if (S._undoStack.length < 2) return;
    S._redoStack.push(S._undoStack.pop());
    restore(S._undoStack[S._undoStack.length - 1]);
    S._dirty = true;
    S.updateTitle();
    S.scheduleDraftSave();
}
function redo() {
    if (S._redoStack.length === 0) return;
    var state = S._redoStack.pop();
    S._undoStack.push(state);
    restore(state);
    S._dirty = true;
    S.updateTitle();
    S.scheduleDraftSave();
}
function restore(json) {
    var st = JSON.parse(json);
    if (Array.isArray(st)) { loadElements(st); return; }  // older entry: current page only
    S._pages = st.pages.map(function(p) { return JSON.parse(JSON.stringify(p || [])); });
    S._currentPage = Math.min(st.cur || 0, S._pages.length - 1);
    S.E = S._pages[S._currentPage];
    if (st.pw !== S._pw || st.ph !== S._ph) S.applyPageSize(st.pw / S._sc, st.ph / S._sc);
    if (st.theme !== undefined) {  // entries from before themes leave these as they are
        S._pageBorder = st.border;
        S._pageBorderC = st.borderC;
        S._theme = st.theme;
        S.syncPageBar();
    }
    S.sel = null;
    S.renderPageDots();
    S.render();
    S.updateProps();
}
function loadElements(arr) {
    S.E = arr; S.sel = null; S.switchPage(S._currentPage, true); S.render(); S.updateProps();
}
function loadElementsNoPush(arr) { S._undoPaused = true; loadElements(arr); S._undoPaused = false; }

S.pushUndo = pushUndo;
S.resetUndo = resetUndo;
S.undo = undo;
S.redo = redo;
S.loadElements = loadElements;
S.loadElementsNoPush = loadElementsNoPush;

})();
