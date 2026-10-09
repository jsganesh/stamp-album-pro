// Stamp frames, album themes and heading marks in the DSL core (Node, no browser).
// Run: node src/tests/test_themes.mjs
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { buildDSL, parseDSL, THEMES, FRAMES, frameOf, applyFrame, themeColor } = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}
const show = (v) => JSON.stringify(v);
const stamp = (extra) => Object.assign({ t: "stamp", s: "rectangle", x: 20, y: 30, w: 40, h: 30, lbl: "S",
  bdr: "solid", bdrC: "#000000", bdrW: 0.5, fill: "#ffffff", fillA: 100 }, extra);
const text = (extra) => Object.assign({ t: "text", s: "text", x: 20, y: 10, w: 120, h: 12, lbl: "T",
  font: "HB", fs: 16, align: "left", bdr: "none", fill: "transparent", fillA: 0 }, extra);
const reopen = (state) => parseDSL(buildDSL(Object.assign({ pw: 210, ph: 297 }, state)));

// ── The theme list ──
check("five themes, Exhibition first", show(Object.keys(THEMES)) === show(["exhibition", "green", "maroon", "navy", "brown"]), show(Object.keys(THEMES)));
check("Exhibition is black", THEMES.exhibition.color === "#000000", THEMES.exhibition.color);

// ── Frames ──
check("four frames", show(Object.keys(FRAMES)) === show(["none", "thin", "medium", "double"]), show(Object.keys(FRAMES)));
check("thin is 0.5 pt solid", show(applyFrame(stamp({}), "thin")) === show(stamp({ bdr: "solid", bdrW: 0.5 })), show(applyFrame(stamp({}), "thin")));
check("medium is 1 pt solid", (() => { const e = applyFrame(stamp({}), "medium"); return e.bdr === "solid" && e.bdrW === 1; })());
check("double", (() => { const e = applyFrame(stamp({}), "double"); return e.bdr === "double"; })());
check("none", (() => { const e = applyFrame(stamp({}), "none"); return e.bdr === "none"; })());
check("frames are always black", applyFrame(stamp({ bdrC: "#ff0000" }), "medium").bdrC === "#000000");
check("frameOf reads them back", ["none", "thin", "medium", "double"].every((f) => frameOf(applyFrame(stamp({}), f)) === f));

// ── Older albums: colours, fills and dashed or dotted frames are tidied on open ──
let st = reopen({ pages: [[
  stamp({ s: "oval", bdr: "dashed", bdrC: "#c62828", bdrW: 2, fill: "#fff9c4", fillA: 40 }),
  stamp({ bdr: "dotted", bdrC: "#6a1b9a", bdrW: 0.5 }),
  stamp({ bdr: "none", bdrW: 1 }),
  stamp({ bdr: "double", bdrC: "#1565c0", bdrW: 3 }),
  text({ lbl: "Untouched" }),
]] });
const [a, b, c, d, t] = st.pages[0];
check("a 2 pt dashed red frame becomes a black medium frame", frameOf(a) === "medium" && a.bdrC === "#000000", show(a));
check("a 0.5 pt dotted frame becomes thin", frameOf(b) === "thin" && b.bdrC === "#000000", show(b));
check("no frame stays no frame", frameOf(c) === "none", show(c));
check("a coloured double frame stays double, in black", frameOf(d) === "double" && d.bdrC === "#000000", show(d));
check("stamp fills are dropped", a.fill === "#ffffff" && a.fillA === 100 && b.fill === "#ffffff", show([a.fill, a.fillA, b.fill]));
check("text items keep their transparent box", t.fill === "transparent" && t.bdr === "none", show(t));

// ── Themes are saved and reopened ──
st = reopen({ pages: [[stamp({})]], pageBorder: "double", theme: "green" });
check("theme is saved", buildDSL({ pages: [[]], pw: 210, ph: 297, theme: "green" }).indexOf('ALBUM_THEME("green")') !== -1);
check("theme reopens", st.theme === "green", st.theme);
check("page border colour follows the theme", buildDSL({ pages: [[]], pw: 210, ph: 297, pageBorder: "double", theme: "green" }).indexOf('COLOUR_ALBUM_BORDER("' + THEMES.green.color + '")') !== -1);
check("a theme is kept with no page border", reopen({ pages: [[]], theme: "navy" }).theme === "navy");

// ── Albums from before themes ──
st = parseDSL(['ALBUM_PAGES_BORDER(0.5 0 0 1)', 'COLOUR_ALBUM_BORDER("#ff0000")', 'PAGE_START'].join("\n"));
check("a custom border colour becomes the Custom theme", st.theme === "custom" && st.pageBorderC === "#ff0000", show([st.theme, st.pageBorderC]));
check("Custom survives a save", reopen(Object.assign({ pages: [[]] }, { pageBorder: "solid", theme: "custom", pageBorderC: "#ff0000" })).theme === "custom");
st = parseDSL("PAGE_START");
check("no colour means Exhibition", st.theme === "exhibition", st.theme);

// ── themeColor ──
check("themeColor of a named theme", themeColor({ theme: "maroon" }) === THEMES.maroon.color);
check("themeColor of Custom", themeColor({ theme: "custom", pageBorderC: "#123456" }) === "#123456");
check("themeColor defaults to Exhibition", themeColor({}) === "#000000");

// ── Heading marks ──
st = reopen({ pages: [[text({ lbl: "Marked", role: "heading" }), text({ lbl: "Bold but not marked" })]] });
check("a marked heading reopens marked", st.pages[0][0].role === "heading", show(st.pages[0][0]));
check("bold 16 pt text is not a heading unless marked", !st.pages[0][1].role, show(st.pages[0][1]));
check("the mark is its own line after the text", buildDSL({ pages: [[text({ role: "heading" })]], pw: 210, ph: 297 }).indexOf('\nPAGE_TEXT_ROLE("heading")') !== -1);

// ── Text sizes with a decimal (10.5 pt) used to drop the text on open ──
st = reopen({ pages: [[text({ fs: 10.5, lbl: "Half point" })]] });
check("10.5 pt text survives a save", st.pages[0].length === 1 && st.pages[0][0].fs === 10.5, show(st.pages[0]));

if (failures) { console.log(failures + " failure(s)"); process.exit(1); }
console.log("All theme checks passed");
