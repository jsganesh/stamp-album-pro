# Architect decisions

- [DISCOVERED] Python FastAPI app (`src/stamp_album/api.py`) serving a plain-JS editor (`web/`); exports
  (PDF ReportLab, PNG Pillow, SVG, HTML) are built server-side from the editor's canvas state
  (`POST /export-from-state`). Shared geometry lives in paired Python/JS modules (see the handoff's
  "Shared code").
- system-fonts: one font finder for the Font list and every export (ADR-001).
