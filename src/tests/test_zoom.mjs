// Editor zoom: the fit calculation (Node, no browser). Run: node src/tests/test_zoom.mjs
// Zoom only scales how the page is shown; fitZoom picks the scale for a mode.
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { fitZoom, clampZoom, stepZoom, anchorScroll, MODES, PINCH_MIN, PINCH_MAX } = require("../stamp_album/web/zoom.js");

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

// ── Free zoom (pinch, Ctrl/Cmd + wheel and keys) ──
check("free zoom range is 25% to 400%", PINCH_MIN === 0.25 && PINCH_MAX === 4);
check("pinch stops at 400%", clampZoom(9) === 4);
check("pinch stops at 25%", clampZoom(0.1) === 0.25);
check("near 100% snaps to 100%", clampZoom(0.96) === 1 && clampZoom(1.04) === 1);
check("away from 100% is kept", clampZoom(0.9) === 0.9 && clampZoom(1.5) === 1.5);
check("nonsense zoom is 100%", clampZoom(NaN) === 1 && clampZoom(0) === 1 && clampZoom(-2) === 1);
check("free zoom rounded to 1/1000", clampZoom(1.23456) === 1.235, clampZoom(1.23456));

check("step in from a fit lands on the next step", stepZoom(0.64, 1) === 0.67);
check("step out from a fit lands on the step below", stepZoom(0.64, -1) === 0.5);
check("step in from 100%", stepZoom(1, 1) === 1.1);
check("step out from 100%", stepZoom(1, -1) === 0.9);
check("no step past 400%", stepZoom(4, 1) === 4);
check("no step below 25%", stepZoom(0.25, -1) === 0.25);

// The page point stays under the pointer: page edge at 20 px, point 100 px into the
// page, now at 2× (200 px on screen), wanted at 150 px: scroll on by 70 px.
check("anchor scroll", anchorScroll(30, 20, 100, 2, 150) === 100);
check("anchor scroll needs no move when already there", anchorScroll(5, 50, 50, 2, 150) === 5);

if (failures) { console.log(failures + " failed"); process.exit(1); }
console.log("all passed");
