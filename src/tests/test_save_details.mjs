// Stamp details survive save and reopen (Node, no browser). Run: node src/tests/test_save_details.mjs
// The album file used to drop each stamp's heading, catalogue number, denomination,
// condition and perforation, and a rectangle stamp's border settings.
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { buildDSL, parseDSL } = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}
const KEYS = ["t", "s", "x", "y", "w", "h", "lbl", "hdg", "cat", "denom", "cond", "perf", "bdr", "bdrC", "bdrW", "fill", "fillA"];
const pick = (el) => Object.fromEntries(KEYS.map((k) => [k, el[k] === undefined ? "" : el[k]]));
const reopen = (pages) => parseDSL(buildDSL({ pages, pw: 210, ph: 297 })).pages;
const show = (v) => JSON.stringify(v);

const full = { t: "stamp", s: "rectangle", x: 20, y: 30, w: 40, h: 30, lbl: "Penny Black — 1840",
  hdg: "Penny Black", cat: "SG#1", denom: "1/2D", cond: "Used", perf: "Imperforate",
  bdr: "double", bdrC: "#000000", bdrW: 1, fill: "#ffffff", fillA: 100 };

// ── A rectangle stamp with every detail ──
let back = reopen([[full]])[0][0];
check("rectangle stamp comes back identical", show(pick(back)) === show(pick(full)), "\n  got  " + show(pick(back)) + "\n  want " + show(pick(full)));

// ── The same on a shaped stamp ──
const oval = Object.assign({}, full, { s: "oval", lbl: "Oval", hdg: "Head", cat: "SC#5", denom: "2d", cond: "Mint NH", perf: "14" });
back = reopen([[oval]])[0][0];
check("oval stamp comes back identical", show(pick(back)) === show(pick(oval)), "\n  got  " + show(pick(back)) + "\n  want " + show(pick(oval)));

// ── Details are optional: an empty stamp gains nothing ──
const bare = { t: "stamp", s: "rectangle", x: 20, y: 30, w: 40, h: 30, lbl: "Bare", bdr: "solid", bdrC: "#000000", bdrW: 0.5, fill: "#ffffff", fillA: 100 };
const dsl = buildDSL({ pages: [[bare]], pw: 210, ph: 297 });
check("no heading or details lines for a bare stamp", dsl.indexOf("STAMP_HEADING") === -1 && dsl.indexOf("STAMP_DETAILS") === -1, dsl);
back = reopen([[bare]])[0][0];
check("bare stamp has empty details", !back.hdg && !back.cat && !back.denom && !back.cond && !back.perf, show(pick(back)));

// ── Only some details ──
const some = Object.assign({}, bare, { cond: "Used" });
back = reopen([[some]])[0][0];
check("condition alone survives", back.cond === "Used" && !back.denom && !back.perf, show(pick(back)));

// ── Each stamp keeps its own details on a page with several ──
const two = [Object.assign({}, full), Object.assign({}, bare, { x: 80, lbl: "Second" })];
back = reopen([two])[0];
check("details stay on the first stamp", back[0].hdg === "Penny Black" && back[0].cat === "SG#1", show(back.map(pick)));
check("second stamp gets none of them", !back[1].hdg && !back[1].cat && !back[1].denom, show(back.map(pick)));

// ── Across pages ──
back = reopen([[full], [Object.assign({}, full, { hdg: "Page two", cat: "SG#2" })]]);
check("each page keeps its stamps' details", back[0][0].hdg === "Penny Black" && back[1][0].hdg === "Page two" && back[1][0].cat === "SG#2", show(back.map((p) => p.map(pick))));

// ── Files written before this fix still open ──
const old = ['ALBUM_PAGES_SIZE(210 297)', 'PAGE_START', 'STAMP_ADD_AT(20.0 20.0 40.0 30.0 "Old" "" "" "")'].join("\n");
back = parseDSL(old).pages[0][0];
check("old short-format stamp still opens as a rectangle", back.s === "rectangle" && back.lbl === "Old", show(pick(back)));

if (failures) { console.log(failures + " failure(s)"); process.exit(1); }
console.log("All save-details checks passed");
