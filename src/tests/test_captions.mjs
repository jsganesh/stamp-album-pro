// Stamp captions in the editor core (Node, no browser). Run: node src/tests/test_captions.mjs
// The editor lays captions out like the exports and warns when they run into another
// item or past the page border.
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const C = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}
const near = (a, b) => Math.abs(a - b) < 1e-6;
const measure = (t, f, s) => t.length * s * 0.5 * 25.4 / 72;
const LINE = 8 * 1.3 * 25.4 / 72;

// ── Layout ──
const full = { t: "stamp", hdg: "Penny Black", lbl: "Plate 1a", denom: "1d", cond: "Used", perf: "Imperforate", cat: "SG 2" };
let lines = C.captionLayout(full, 40, 60, 40, 30, measure);
check("order: heading, description, details, catalogue",
  lines.map((l) => l.kind).join() === "heading,description,details,catalogue", lines.map((l) => l.kind).join());
check("heading line box ends 2 mm above the frame", near(lines[0].bottom, 58), lines[0].bottom);
check("description starts 2 mm below the frame", near(lines[1].top, 92), lines[1].top);
check("details follow the description without overlap", near(lines[2].top, lines[1].bottom) && near(lines[2].bottom - lines[2].top, LINE));
check("details line joins denomination, condition and perforation", lines[2].text === "1d · Used · Imperforate", lines[2].text);
check("heading bold 9 pt", lines[0].bold && !lines[0].italic && lines[0].sizePt === 9);
check("description regular 8 pt", !lines[1].bold && !lines[1].italic && lines[1].sizePt === 8);
check("details and catalogue italic 8 pt", lines[2].italic && lines[3].italic && lines[3].sizePt === 8);
check("captions are black", C.CAPTION.COLOR === "#000000");

lines = C.captionLayout({ t: "stamp", lbl: "A description that is far too long for one line of the box" }, 40, 60, 40, 30, measure);
check("long captions wrap to the box width", lines.length > 1 && lines.every((l) => l.width <= 40 + 1e-6), JSON.stringify(lines.map((l) => l.width)));
check("an empty stamp has no captions", C.captionLayout({ t: "stamp" }, 0, 0, 10, 10, measure).length === 0);
check("stamps and free shapes have captions; text and pictures do not",
  C.hasCaptions({ t: "stamp" }) && C.hasCaptions({ t: "freehand" }) && !C.hasCaptions({ t: "text" }) && !C.hasCaptions({ t: "image" }));

// ── Warnings ──
const item = (id, x, y, el) => ({ id, box: { x, y, w: 40, h: 30 }, lines: el ? C.captionLayout(el, x, y, 40, 30, measure) : [] });
const area = { l: 5, t: 5, r: 205, b: 292 };

let w = C.captionWarnings([item("a", 20, 40, full), item("b", 80, 40, full)], area);
check("well-spaced stamps: no warnings", Object.keys(w).length === 0, JSON.stringify(w));

w = C.captionWarnings([item("a", 20, 265, full)], area);
check("captions past the page border warn", w.a === "border", JSON.stringify(w));

w = C.captionWarnings([item("a", 20, 4, { t: "stamp", hdg: "Top" })], { l: 0, t: 0, r: 210, b: 297 });
check("a heading past the page edge warns (no border)", w.a === "border", JSON.stringify(w));

w = C.captionWarnings([item("a", 20, 40, full), item("b", 20, 80, null)], area);
check("captions running into the next box warn", w.a === "overlap" && !w.b, JSON.stringify(w));

w = C.captionWarnings([item("a", 20, 40, full), item("b", 20, 86, { t: "stamp", hdg: "Next" })], area);
check("captions running into the next stamp's heading warn", w.a === "overlap" && w.b === "overlap", JSON.stringify(w));

w = C.captionWarnings([item("a", 20, 40, null), item("b", 20, 72, null)], area);
check("items without captions never warn", Object.keys(w).length === 0, JSON.stringify(w));

console.log(failures ? failures + " failure(s)" : "all passed");
process.exit(failures ? 1 : 0);
