// Editor zoom: the fit calculation (Node, no browser). Run: node src/tests/test_zoom.mjs
// Zoom only scales how the page is shown; fitZoom picks the scale for a mode.
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { fitZoom, MODES } = require("../stamp_album/web/zoom.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}

const A4 = [525, 742.5]; // 210 × 297 mm at 2.5 px/mm

check("three modes", MODES.join() === "fit-width,fit-page,actual", MODES.join());

// iPhone 13 portrait: about 336 × 426 px for the page
let z = fitZoom(336, 426, ...A4, "fit-width");
check("fit width on a phone fills the width", z <= 336 / 525 && 336 / 525 - z < 0.001, z);
check("scaled page never wider than the space", 525 * z <= 336, 525 * z);
z = fitZoom(336, 426, ...A4, "fit-page");
check("fit whole page uses the height when that is tighter", Math.abs(z - Math.floor(426 / 742.5 * 1000) / 1000) < 1e-9, z);
check("whole page fits both ways", 525 * z <= 336 && 742.5 * z <= 426);

// A wide window: the fits never enlarge the page
check("fit width stops at 100%", fitZoom(1000, 900, ...A4, "fit-width") === 1);
check("fit whole page stops at 100%", fitZoom(1000, 2000, ...A4, "fit-page") === 1);
check("fit width ignores the height", fitZoom(1000, 100, ...A4, "fit-width") === 1);
check("fit whole page shrinks for a short window", fitZoom(1000, 371.25, ...A4, "fit-page") === 0.5);

// Actual size is always 100%, even on a phone
check("actual size on a phone", fitZoom(336, 426, ...A4, "actual") === 1);

// Unusable sizes (hidden panel, page not sized yet) fall back to 100% or the floor
check("no space yet: 100%", fitZoom(0, 0, ...A4, "fit-width") === 1);
check("no page size yet: 100%", fitZoom(336, 426, 0, 0, "fit-width") === 1);
check("tiny space: not below 10%", fitZoom(10, 10, ...A4, "fit-page") === 0.1);

// Landscape A4 on the same phone
z = fitZoom(336, 426, 742.5, 525, "fit-width");
check("landscape page fits the width", 742.5 * z <= 336 && z > 0.45, z);

if (failures) { console.log(failures + " failed"); process.exit(1); }
console.log("all passed");
