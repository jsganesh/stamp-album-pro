"use strict";
(function(){
var S = window.StampAlbum;

// ── Undo/redo system ──
var _undoStack = [], _redoStack = [], _undoMax = 50, _undoPaused = false;

function pushUndo() {
    if (_undoPaused) return;
    _undoStack.push(JSON.stringify(S.E));
    if (_undoStack.length > _undoMax) _undoStack.shift();
    _redoStack = [];
    S._dirty = true;
    S.updateTitle();
}
function undo() {
    if (_undoStack.length < 2) return;
    _redoStack.push(_undoStack.pop());
    var state = JSON.parse(_undoStack.pop());
    loadElements(state);
    S.updateTitle();
}
function redo() {
    if (_redoStack.length === 0) return;
    _undoStack.push(JSON.stringify(S.E));
    var state = JSON.parse(_redoStack.pop());
    loadElements(state);
    S.updateTitle();
}
function loadElements(arr) {
    S.E = arr; S.sel = null; S.switchPage(S._currentPage, true); render(); S.updateProps();
}
function loadElementsNoPush(arr) { _undoPaused = true; loadElements(arr); _undoPaused = false; }

S.pushUndo = pushUndo;
S.undo = undo;
S.redo = redo;
S.loadElements = loadElements;
S.loadElementsNoPush = loadElementsNoPush;

})();
