# Handoff

Two fixes from the owner's use of v0.5.0 (2026-10-24), each on its own branch from `main`:
1. `fix/caption-typing` — see `decisions/sde/caption-typing.md`.
2. `fix/system-fonts` — see ADR-001 and `decisions/sde/system-fonts.md`.

Owner checks on the Mac: pick Georgia/Palatino for a text item, export PDF/PNG/SVG, compare
with the editor; type a stamp's Name, click the next stamp, check it stayed.
Next role (DevOps): CI runs the full suite on each PR; no packaging change (fontTools,
ReportLab, Pillow already bundled).
