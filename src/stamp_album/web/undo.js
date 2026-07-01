"use strict";
(function(){
var S = window.StampAlbum;

// ── Undo/redo system — uses S._undoStack / S._redoStack / S._undoPaused ──

function pushUndo() {
    if (S._undoPaused) return;
    S._undoStack.push(JSON.stringify(S.E));
    if (S._undoStack.length > 50) S._undoStack.shift();
    S._redoStack = [];
    S._dirty = true;
    S.updateTitle();
    S.scheduleDraftSave();
}
function undo() {
    if (S._undoStack.length < 2) return;
    S._redoStack.push(S._undoStack.pop());
    var state = JSON.parse(S._undoStack.pop());
    loadElements(state);
    S.updateTitle();
}
function redo() {
    if (S._redoStack.length === 0) return;
    S._undoStack.push(JSON.stringify(S.E));
    var state = JSON.parse(S._redoStack.pop());
    loadElements(state);
    S.updateTitle();
}
function loadElements(arr) {
    S.E = arr; S.sel = null; S.switchPage(S._currentPage, true); S.render(); S.updateProps();
}
function loadElementsNoPush(arr) { S._undoPaused = true; loadElements(arr); S._undoPaused = false; }

S.pushUndo = pushUndo;
S.undo = undo;
S.redo = redo;
S.loadElements = loadElements;
S.loadElementsNoPush = loadElementsNoPush;

})();
