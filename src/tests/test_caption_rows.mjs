// Caption headings in a row (Node, no browser). Run: node src/tests/test_caption_rows.mjs
// Stamps in a row (frame bottoms within 1 mm, nothing standing between them) put their
// headings on one line, above the row's highest frame. Only stamps with a heading take part.
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const C = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}
const near = (a, b) => a !== null && b !== null && Math.abs(a - b) < 1e-6;
const measure = (t, f, s) => t.length * s * 0.5 * 25.4 / 72;
const box = (x, y, w, h, heading) => ({ x, y, w, h, heading: heading !== false });

check("captionRows is exported", typeof C.captionRows === "function");
check("the row tolerance is 1 mm", C.CAPTION.ROW_TOLERANCE_MM === 1);

// The Exhibition page template's second row: 36 x 25 beside 19 x 22, bottoms level.
let rows = C.captionRows([box(31, 143, 36, 25), box(80, 146, 19, 22), box(111, 146, 19, 22), box(143, 143, 36, 25)]);
check("a row of mixed heights shares the highest frame top", rows.every((t) => near(t, 143)), JSON.stringify(rows));

rows = C.captionRows([box(20, 40, 20, 30), box(50, 50.5, 20, 20)]);
check("bottoms within 1 mm make a row", near(rows[0], 40) && near(rows[1], 40), JSON.stringify(rows));

rows = C.captionRows([box(20, 40, 20, 30), box(50, 48, 20, 20)]);
check("bottoms more than 1 mm apart do not", near(rows[0], 40) && near(rows[1], 48), JSON.stringify(rows));

rows = C.captionRows([box(20, 40, 20, 30), box(50, 50, 20, 20, false), box(80, 50, 20, 20)]);
check("a stamp without a heading takes no part and returns null", rows[1] === null, JSON.stringify(rows));
check("...but doesn't break the row it stands in", near(rows[0], 40) && near(rows[2], 40), JSON.stringify(rows));

rows = C.captionRows([box(20, 50, 20, 20), box(50, 30, 20, 40, false), box(80, 50, 20, 20)]);
check("a taller stamp without a heading doesn't raise the line", near(rows[0], 50) && near(rows[2], 50), JSON.stringify(rows));

rows = C.captionRows([box(20, 40, 20, 30), box(45, 45, 20, 10, false), box(80, 50, 20, 20)]);
check("an item standing between them breaks the row", near(rows[0], 40) && near(rows[2], 50), JSON.stringify(rows));

rows = C.captionRows([box(20, 40, 20, 30), box(45, 10, 20, 10, false), box(80, 50, 20, 20)]);
check("an item above the row, in the gap, does not", near(rows[0], 40) && near(rows[2], 40), JSON.stringify(rows));

rows = C.captionRows([box(20, 40, 20, 30), box(25, 50, 20, 20)]);
check("overlapping stamps are not a row", near(rows[0], 40) && near(rows[1], 50), JSON.stringify(rows));

rows = C.captionRows([box(80, 50, 20, 20), box(20, 40, 20, 30), box(50, 60, 20, 10)]);
check("order on the page doesn't matter", rows.every((t) => near(t, 40)), JSON.stringify(rows));

// ── Layout with a row top ──
const el = { t: "stamp", hdg: "Heading", lbl: "Name" };
let own = C.captionLayout(el, 40, 60, 20, 22, measure);
let inRow = C.captionLayout(el, 40, 60, 20, 22, measure, { rowTop: 57 });
const ob = C.frameBox(el, 40, 60, 20, 22);
check("without a row top the heading sits 2 mm above its own frame", near(own[0].bottom, ob.y - 2), own[0].bottom);
check("with a row top it sits 2 mm above the row's top", near(inRow[0].bottom, 55), inRow[0].bottom);
check("captions below don't move", near(own[1].top, inRow[1].top), own[1].top + " " + inRow[1].top);
inRow = C.captionLayout(el, 40, 60, 20, 22, measure, { rowTop: 70 });
check("a row top below the frame is ignored", near(inRow[0].bottom, own[0].bottom), inRow[0].bottom);
const two = C.captionLayout({ t: "stamp", hdg: "A heading long enough to wrap over two lines" }, 40, 60, 20, 22, measure, { rowTop: 57 });
check("a wrapped heading grows upward from the row line", two.length > 1 && near(two[two.length - 1].bottom, 55), JSON.stringify(two.map((l) => l.bottom)));

if (failures) { console.log(failures + " failed"); process.exit(1); }
console.log("all passed");
