# CONTEXT.md — stamp-album-pro

## What this project is
A web-based stamp album designer with an InDesign-like free-form page layout feel. Stamp collectors design and print album pages with visual canvas interaction as the primary mode, and a DSL (Domain Specific Language) as an advanced toggle. Built with Python FastAPI backend and a browser-based frontend.

## Owner / developer profile
- Stamp collector — thinks in collector workflows: grid layouts, free-form stamp positioning, direct text input
- Wants an InDesign-like feel: drag, drop, resize, annotate freely on a page canvas
- Prefers iterative refinement over big-bang rewrites
- Batches medium-complexity items in one session and commits at natural boundaries

## Tech stack
- Backend: Python / FastAPI
- Frontend: Browser-based visual canvas (SVG shapes, contentEditable text)
- Entry point: `stamp-album` (open in browser)
- Tests: 199 tests (maintain this coverage — do not break existing tests)
- DSL: advanced toggle, not the default mode

## Current version state (v3)
- SVG shape rendering on canvas
- contentEditable text elements (direct inline editing)
- Collapsible panels in the UI
- Grid fill tool for batch stamp placement
- System fonts support
- Visual canvas is the default; DSL is an advanced opt-in

## Key conventions
- Visual-first: all new features default to canvas interaction, not DSL
- Free-form positioning is a first-class feature — do not regress to row-based or grid-forced layouts
- `stamp-album` is the browser entry point — test by opening this, not via unit tests alone
- Run the full test suite (`pytest` or equivalent) before committing any change
- Commit at logical boundaries, not mid-feature

## Web dev debug patterns (critical — check these before assuming a bug)
1. Browser tool may be stale — hard-refresh before reporting a bug (Cmd+Shift+R)
2. Verify static files with `curl`, not the browser, to bypass cache
3. `nosniff` header + wrong `Content-Type` = browser silently refuses `.js` files
4. Same-named JS functions overwrite each other via hoisting — use IIFEs to isolate scope
5. CodeMirror 5 drag-and-drop: use `editor.on("drop", ...) + CodeMirror.e_stop(e)`
6. Inline `<script>` blocks may not execute if loaded late — prefer external `<script src="...">`
7. `DOMContentLoaded` may have already fired for late-injected scripts — check `document.readyState` first

## Hermes-specific instructions
- Start every session: `read README.md and list any open TODOs or known issues`
- Before any JS change, check for same-named functions that could conflict (hoisting trap)
- After each feature batch is committed, ask Hermes to create a skill summarising what was built
- Use local Qwen 3.5 4B for: bug investigation, reading existing code, small isolated fixes
- Escalate to owl-alpha for: FastAPI architectural changes, complex canvas/SVG logic, test suite design
- Preferred workflow: discuss change → confirm → implement → test in browser → commit
- Never auto-commit — always show the diff and ask for confirmation first
