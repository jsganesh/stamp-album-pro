# SDE: caption-typing

**Date:** 2026-10-24 · **Branch:** fix/caption-typing · **Owner's choice:** save as you type

## Problem (owner's report)
Caption details typed in the right panel were lost on moving to the next stamp unless the
field was left with Tab/Enter first. Cause: fields saved on `change` (fired on blur), but a
click on another stamp ran `select()` in `mousedown`, before the blur, and `fillPanel()`
overwrote the field with the next stamp's value, so `change` never fired. Had it fired late,
it would have used `S.sel` (the new stamp).

## What was built
- `render.js`: `panelItem()` (the item the panel was filled for, `_panelFor`), `panelTyped()`
  (marks unsaved, schedules the draft save, one redraw per frame), `commitPanelEdit()`
  (a half-typed number box fires its `change`; typed words get one `pushUndo`).
  `fillPanel()` commits before switching items. Exposed as `S.panelItem`, `S.panelTyped`,
  `S.commitPanelEdit`.
- `init.js`: word fields (`plbl phdg pcap pcat pdenom pcond pperf`, marked `data-live`) write
  on `input`; `change` commits. All panel handlers act on `S.panelItem()`, not `S.sel`.
  Number boxes skip a `change` that leaves the shown value as it was.
- Commit is also called first by `undo`, `redo`, phone `closeSheet`, `saveFile`,
  `exportFormat`, `exportPDF`.
- `mouseup`: a click that moves nothing pushes no undo step (was an empty step).

## Tests
`src/tests/test_caption_typing.py` (9; 8 fail on the old code).

## Tech debt
- `render()` runs once per animation frame while typing; fine for album pages (tens of items).
