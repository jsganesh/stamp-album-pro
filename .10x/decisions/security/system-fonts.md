# Security: system-fonts (2026-10-24)

- `GET /api/fonts` returns only family names from a fixed list of 46; no paths. The server binds
  localhost (0.0.0.0 only when the owner serves the iPhone); font names are not sensitive.
- No path comes from the request: a font id is only a key into the scanned index, so no traversal.
- Family names put into CSS (`@font-face`, `font-family`) have quotes, backslashes and `;` removed.
- Embedding licences respected: faces with OS/2 `fsType` restricted (0x0002) or bitmap-only are not offered.
- Font files parsed are the OS's own; any parse error skips the file.
