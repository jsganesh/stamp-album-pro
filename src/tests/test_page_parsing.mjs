// Page counting in the DSL parser (Node, no browser). Run: node src/tests/test_page_parsing.mjs
// The parser used to start with an empty page and add another at the first PAGE_START,
// so every opened album gained a blank page 1 and opened on its last page.
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { buildDSL, parseDSL } = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}
const labels = (st) => JSON.stringify(st.pages.map((p) => p.map((e) => e.lbl)));
const stamp = (lbl) => `STAMP_ADD_AT(20 20 40 30 "${lbl}" "rectangle" "solid" "#fff")`;

// ── One page ──
let st = parseDSL(["ALBUM_PAGES_SIZE(210 297)", "PAGE_START", stamp("a")].join("\n"));
check("one PAGE_START gives one page", st.pages.length === 1, labels(st));
check("its stamp is on page 1", st.pages[0].length === 1 && st.pages[0][0].lbl === "a", labels(st));
check("opens on page 1", st.currentPage === 0, "currentPage=" + st.currentPage);

// ── Two pages ──
st = parseDSL(["PAGE_START", stamp("a"), "PAGE_START", stamp("b")].join("\n"));
check("two PAGE_STARTs give two pages", st.pages.length === 2, labels(st));
check("pages keep their own stamps", labels(st) === '[["a"],["b"]]', labels(st));
check("a two-page album opens on page 1", st.currentPage === 0, "currentPage=" + st.currentPage);

// ── Elements before any PAGE_START still land on page 1 ──
st = parseDSL([stamp("a"), "PAGE_START", stamp("b")].join("\n"));
check("content before the first PAGE_START is page 1", labels(st) === '[["a"],["b"]]', labels(st));

// ── A blank page in the middle survives ──
st = parseDSL(["PAGE_START", stamp("a"), "PAGE_START", "PAGE_START", stamp("c")].join("\n"));
check("an empty middle page is kept", labels(st) === '[["a"],[],["c"]]', labels(st));

// ── No PAGE_START at all: one empty page ──
st = parseDSL("ALBUM_PAGES_SIZE(297 210)");
check("no PAGE_START gives one empty page", st.pages.length === 1 && st.pages[0].length === 0, labels(st));

// ── Save and reopen keeps the page count ──
const pages = [[{ t: "stamp", s: "rectangle", x: 20, y: 20, w: 40, h: 30, lbl: "a" }],
               [{ t: "stamp", s: "rectangle", x: 20, y: 20, w: 40, h: 30, lbl: "b" }],
               [{ t: "stamp", s: "rectangle", x: 20, y: 20, w: 40, h: 30, lbl: "c" }]];
st = parseDSL(buildDSL({ pages, pw: 210, ph: 297 }));
check("a three-page album reopens with three pages", labels(st) === '[["a"],["b"],["c"]]', labels(st));
st = parseDSL(buildDSL({ pages: st.pages, pw: 210, ph: 297 }));
check("a second round trip does not add pages", labels(st) === '[["a"],["b"],["c"]]', labels(st));

if (failures) { console.log(failures + " failure(s)"); process.exit(1); }
console.log("All page parsing checks passed");
