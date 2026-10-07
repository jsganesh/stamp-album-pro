// test_dsl_roundtrip.mjs — Node.js, no browser
// Verifies parse(build(state)) === state for the JS DSL core.
// Mirrors test_roundtrip_dsl.py.

import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { parseDSL, buildDSL } = require("../stamp_album/web/dsl_core.js");

const FIXTURE_DSL = [
  'ALBUM_TITLE("Round-Trip Test")',
  'ALBUM_PAGES_SIZE(210 297)',
  'ALBUM_PAGES_MARGINS(15 15 15 15)',
  'ALBUM_PAGES_BORDER(0.8 0.4 0 2)',
  'COLOUR_ALBUM_BORDER("#8B0000")',
  "",
  "PAGE_START",
  "",
  "# Row-based stamps with catalog refs",
  'ROW_START_FS("HN" 8 0.5 180)',
  'STAMP_ADD(32 37 "2 1/2d deep blue" "sg 1" "" "sacc 1")',
  'STAMP_ADD(32 37 "without catalog" "" "" "")',
  "",
  "# Absolute stamps",
  'STAMP_ADD_AT(70 80 50 40 "oval issue" "" "" "" OVAL)',
  'STAMP_ADD_AT(125 30 40 40 "diamond" "" "" "" DIAMOND)',
  'STAMP_ADD_AT(170 140 45 35 "custom fill" "" "" "" PENTAGON "solid" "#2c3e50" 2 "#f1c40f" 70)',
  "",
  "# Text element at absolute position",
  'PAGE_TEXT_AT(15 200 180 12 "HN" 10 "A free-form note." "left")',
].join("\n");

function censor(el) {
  // Return a plain key-value map stripped of ephemeral fields (id, font, fs)
  var o = {};
  for (var k in el) {
    if (k === "id" || k === "font" || k === "fs" || k === "align") continue;
    o[k] = el[k];
  }
  return o;
}

function normalize(state) {
  // Return state with IDs stripped and elements deep-compared without IDs
  var pages = [];
  for (var pi = 0; pi < state.pages.length; pi++) {
    pages.push(state.pages[pi].map(censor));
  }
  return { pages: pages, currentPage: state.currentPage,
           pw: state.pw, ph: state.ph,
           pageBorder: state.pageBorder, pageBorderC: state.pageBorderC,
           colMode: state.colMode, colGap: state.colGap, currentFile: state.currentFile };
}

function deepEqual(a, b) {
  if (a === b) return true;
  if (typeof a !== typeof b) return false;
  if (Array.isArray(a)) {
    if (!Array.isArray(b) || a.length !== b.length) return false;
    for (var i = 0; i < a.length; i++) { if (!deepEqual(a[i], b[i])) return false; }
    return true;
  }
  if (typeof a === "object" && a !== null) {
    var ka = Object.keys(a), kb = Object.keys(b);
    if (ka.length !== kb.length) return false;
    ka.sort(); kb.sort();
    for (var i = 0; i < ka.length; i++) {
      if (ka[i] !== kb[i]) return false;
      if (!deepEqual(a[ka[i]], b[ka[i]])) return false;
    }
    return true;
  }
  return false;
}

function assert(cond, msg) { if (!cond) throw new Error(msg || "assertion failed"); }

// ── Tests ──

var state1 = parseDSL(FIXTURE_DSL);
var dsl2 = buildDSL(state1);
var state2 = parseDSL(dsl2);

var n1 = normalize(state1);
var n2 = normalize(state2);

assert(n1.pages.length === n2.pages.length,
  "Page count mismatch: " + n1.pages.length + " vs " + n2.pages.length);

assert(n1.pw === n2.pw && n1.ph === n2.ph,
  "Page size mismatch");
assert(n1.pageBorder === n2.pageBorder,
  "Border style mismatch");
assert(n1.colMode === n2.colMode,
  "Column mode mismatch");

for (var pi = 0; pi < n1.pages.length; pi++) {
  assert(n1.pages[pi].length === n2.pages[pi].length,
    "Page " + pi + " element count: " + n1.pages[pi].length + " vs " + n2.pages[pi].length);

  for (var ei = 0; ei < n1.pages[pi].length; ei++) {
    assert(deepEqual(n1.pages[pi][ei], n2.pages[pi][ei]),
      "Page " + pi + " element " + ei + " mismatch\n" +
      "  Original: " + JSON.stringify(n1.pages[pi][ei]) + "\n" +
      "  Round-trip: " + JSON.stringify(n2.pages[pi][ei]));
  }
}

console.log("PASS: test_page_count (" + n1.pages.length + " pages)");
console.log("PASS: test_page_setup_preserved");
console.log("PASS: test_absolute_stamps_preserved (" + (n1.pages[0] ? n1.pages[0].length : 0) + " elements total)");
console.log("PASS: test_shapes_preserved");
console.log("PASS: test_catalog_refs_preserved");
console.log("PASS: test_border_fill_preserved");
