# ADR-001: One system-font finder for the Font list and every export

**Status:** Accepted (owner chose "Fix the exports", 2026-10-24)
**Date:** 2026-10-24
**Feature:** system-fonts
**Author:** 10x-Team (Architect + Staff Engineer)

## Context
Text items can use a font installed on the computer (Georgia, Palatino...). The editor shows
them, but exports didn't:
- The Font list came from the browser guessing which of 46 names it could draw.
- PDF and PNG looked for a file whose *name* resembled the font, in the top level of each
  font folder only. macOS keeps most such fonts in `/System/Library/Fonts/Supplemental`;
  names with spaces ("Times New Roman") never matched; `.ttc` collections and Windows
  folders were not handled. Anything not found silently became Helvetica.
- SVG and HTML always used Helvetica for any font that wasn't one of the twelve built in.
- `engines/font_manager.py` exists but is unused and has bugs (TTC handling loops over glyph
  names; loads whole fonts).

## Decision
A new module `engines/system_fonts.py` is the single source of truth:
- Scans the OS font folders recursively (macOS, Windows, Linux), reads each face's family
  and style from its `name` table (lazily), and keeps the **regular** face of each family.
  Only TrueType-outline faces (`glyf`) that allow embedding (OS/2 `fsType` not restricted)
  count, since ReportLab can embed nothing else. Cached per process.
- `available()`: the curated candidate names (moved from `app.js`) that are usable here.
  Served at `GET /api/fonts`; the editor's Font list is built from it.
- PDF: `reportlab_name(family)` registers the face (with its TTC index) once.
  PNG: `pillow_font(family, size)`. SVG and HTML export: `font_face(family, chars)` embeds a
  subset as `@font-face`, like the caption font; print preview names the family in CSS.
  All measure with the same font, so lines wrap the same everywhere.
- A family that isn't usable still falls back to Helvetica, but the editor now says so: the
  Font list marks it "(not on this computer)" and Export warns which fonts were replaced.

## Alternatives Considered
| Alternative | Pros | Cons | Why Not |
|---|---|---|---|
| Standard fonts only (drop system fonts) | Identical on every computer; least code | Fewer choices; old albums lose their look | Owner chose to fix the exports |
| Fix `FontManager` and use it | Reuses a class | Scans every glyph, wrong TTC handling, no style info; larger rewrite than a focused module | A small new module is clearer; `FontManager` left as is (unused) |
| Use `fc-match`/CoreText via subprocess | Exact OS matching | Not on Windows; extra dependency per OS | Not portable |
| Serve system font files to the browser | Editor = export even on the iPhone | Licensing of re-serving system fonts; browsers don't all read `.ttc` | Not needed for the Mac/Windows app |

## Consequences
### Positive
- What you see in the editor is what prints, for every listed font, in PDF, PNG, SVG, HTML.
- One place to fix font lookup; exporters no longer each guess.
### Negative
- First scan reads every font file's name table (~1–3 s on a Mac with many fonts); done once
  per run, on the first `/api/fonts` call when the editor opens.
- OpenType-CFF (`.otf`) fonts and fonts that forbid embedding are not offered.
### Risks
- An album made on one computer and exported on another without the font prints in Helvetica:
  mitigated by the "(not on this computer)" mark and the export warning.
- On the iPhone (served from the Mac) the Font list is the Mac's; the phone may draw a listed
  font differently on screen, but the export (made on the Mac) is right.

## Dependencies
- fontTools (already a dependency), ReportLab, Pillow.
