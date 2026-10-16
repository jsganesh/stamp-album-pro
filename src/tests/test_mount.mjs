// Stamp mounts and FIP sheets in the editor core (Node, no browser). Run: node src/tests/test_mount.mjs
// The album's mount overhang plus its gap to the frame sets how far out a stamp's frame is drawn.
// An album that doesn't say is 0 + 1 mm, as before; new albums start at 1.5 + 1.
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const C = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}
const near = (a, b) => Math.abs(a - b) < 1e-9;
const PT = 25.4 / 72;
const thin = { t: "stamp", s: "rectangle", bdr: "solid", bdrW: 0.5 };

// ── The rule ──
check("choices: overhang 0 to 3 mm, gap 1 to 3 mm",
  JSON.stringify(C.MOUNT_OVERHANG_CHOICES) === "[0,1,1.5,2,2.5,3]" && JSON.stringify(C.MOUNT_GAP_CHOICES) === "[1,1.5,2,2.5,3]");
check("a new album's mount is 1.5 + 1", C.NEW_ALBUM_MOUNT.overhang === 1.5 && C.NEW_ALBUM_MOUNT.gap === 1);
check("until an album says, frames are 1 mm out as before", near(C.frameClearance(thin), 1), C.frameClearance(thin));
check("setMount(1.5, 1) puts the frame line 2.5 mm out", C.setMount(1.5, 1) && near(C.frameClearance(thin), 2.5));
check("the thin line's centre sits 2.5 mm + half its width out", near(C.frameLines(thin)[0].offset, 2.5 + 0.25 * PT));
check("frameOutset follows", near(C.frameOutset(thin), 2.5 + 0.5 * PT));
check("a double frame starts 2.5 mm out too", near(C.frameLines({ t: "stamp", bdr: "double", bdrW: 0.5 })[0].offset, 2.5 + 0.25 * PT));
check("a free shape keeps no clearance", C.frameClearance({ t: "freehand", bdr: "solid", bdrW: 0.5 }) === 0);
check("a stamp without a frame has none", C.frameClearance({ t: "stamp", bdr: "none", bdrW: 0 }) === 0);
check("bad values are refused and change nothing",
  !C.setMount(-1, 1) && !C.setMount(1, 0) && !C.setMount("x", 1) && !C.setMount(1, 50) && near(C.frameClearance(thin), 2.5));
check("getMount returns a copy", (() => { const m = C.getMount(); m.gap = 9; return C.getMount().gap === 1; })());

// ── The file ──
let st = C.parseDSL("ALBUM_PAGES_SIZE(210 297)\nPAGE_START\n");
check("a file without ALBUM_MOUNT opens at 0 + 1 mm", st.mount.overhang === 0 && st.mount.gap === 1, JSON.stringify(st.mount));
st = C.parseDSL("ALBUM_MOUNT(1.5 1)\nALBUM_PAGES_SIZE(210 297)\nPAGE_START\n");
check("ALBUM_MOUNT is read", st.mount.overhang === 1.5 && st.mount.gap === 1, JSON.stringify(st.mount));
st = C.parseDSL("ALBUM_MOUNT(2 99)\nPAGE_START\n");
check("an impossible ALBUM_MOUNT is ignored", st.mount.overhang === 0 && st.mount.gap === 1, JSON.stringify(st.mount));
let dsl = C.buildDSL({ pages: [[]], pw: 210, ph: 297, mount: { overhang: 2, gap: 1.5 } });
check("the album's mount is written", /^ALBUM_MOUNT\(2 1\.5\)$/m.test(dsl), dsl);
check("and read back", JSON.stringify(C.parseDSL(dsl).mount) === JSON.stringify({ overhang: 2, gap: 1.5 }));
dsl = C.buildDSL({ pages: [[]], pw: 210, ph: 297, mount: { overhang: 0, gap: 1 } });
check("an old album keeps 0 + 1 when saved", /^ALBUM_MOUNT\(0 1\)$/m.test(dsl), dsl);

// ── FIP sheets ──
check("FIP sheets are paper sizes", JSON.stringify([C.PAPER_MM.fip23, C.PAPER_MM.fip31, C.PAPER_MM.fip46]) ===
  JSON.stringify([[230, 297], [310, 297], [460, 297]]));
let d = C.describePageSize(230, 297);
check("a 230 × 297 mm page is an FIP sheet, used as listed", d.name === "fip23" && d.fixed && !d.landscape, JSON.stringify(d));
d = C.describePageSize(460, 297);
check("so is a 460 × 297 mm one, not a landscape page", d.name === "fip46" && d.fixed && !d.landscape, JSON.stringify(d));
d = C.describePageSize(297, 230);
check("an FIP sheet on its side is just a custom size", d.name === null, JSON.stringify(d));
const n = C.normalizePageSize(230, 297);
check("opening an FIP-sized album keeps its size", n.pw === 230 && n.ph === 297 && !n.migrated, JSON.stringify(n));

if (failures) { console.log(failures + " failed"); process.exit(1); }
console.log("all passed");
