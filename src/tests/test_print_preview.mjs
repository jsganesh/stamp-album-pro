// Print preview: the fit and the page it opens on (Node, no browser).
// Run: node src/tests/test_print_preview.mjs
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { fitScale, printedIndex, FIT_MAX } = require("../stamp_album/web/print_preview.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}

const A4 = [793.7, 1122.5]; // 210 × 297 mm in CSS px

// ── fitScale: the whole page in view, as large as the window allows ──
let z = fitScale(1472, 860, ...A4);
check("a laptop window: the height decides", Math.abs(z - Math.floor(860 / 1122.5 * 1000) / 1000) < 1e-9, z);
check("never overflows", A4[0] * z <= 1472 && A4[1] * z <= 860, z);
z = fitScale(350, 1400, ...A4);
check("a narrow window: the width decides", A4[0] * z <= 350 && 350 - A4[0] * z < 1, z);
z = fitScale(5000, 5000, ...A4);
check("a huge window stops at FIT_MAX", z === FIT_MAX && FIT_MAX === 2, z);
check("no size yet: 1", fitScale(0, 0, ...A4) === 1 && fitScale(800, 800, 0, 0) === 1);

// ── printedIndex: the export leaves out empty pages at the start and the end ──
check("first page", printedIndex([3, 1, 2], 0, 3) === 0);
check("middle page", printedIndex([3, 1, 2], 1, 3) === 1);
check("an empty page in the middle still prints", printedIndex([3, 0, 2], 2, 3) === 2);
check("empty pages in front move the index back", printedIndex([0, 0, 4, 1], 3, 2) === 1);
check("an empty page at the end shows the last printed page", printedIndex([2, 1, 0], 2, 2) === 1);
check("an empty first page shows the first printed page", printedIndex([0, 5], 0, 1) === 0);
check("nothing printed: 0", printedIndex([0], 0, 1) === 0);

if (failures) { console.log(failures + " failed"); process.exit(1); }
console.log("All passed");
