// Page setup helpers in the DSL core (Node, no browser). Run: node src/tests/test_page_setup.mjs
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { buildDSL, parseDSL, fitToPage, describePageSize } = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}
const show = (r) => JSON.stringify(r);
const copy = (v) => JSON.parse(JSON.stringify(v));
const inside = (pages, w, h) => pages.every((p) => p.every((e) => e.x >= 0 && e.y >= 0 && e.x + e.w <= w + 1e-6 && e.y + e.h <= h + 1e-6));

// ── An empty album keeps its page size ──
let dsl = buildDSL({ pages: [[]], pw: 297, ph: 210 });
check("empty album writes its page size", dsl.indexOf("ALBUM_PAGES_SIZE(297 210)") !== -1, show(dsl));
let st = parseDSL(dsl);
check("empty landscape album round-trips", st.pw === 297 && st.ph === 210, show({ pw: st.pw, ph: st.ph }));

// ── describePageSize ──
check("A4 portrait label", describePageSize(210, 297).label === "A4 · Portrait", show(describePageSize(210, 297)));
let d = describePageSize(297, 210);
check("A4 landscape label", d.label === "A4 · Landscape" && d.name === "a4" && d.landscape, show(d));
check("custom label", describePageSize(200, 150).label === "200 × 150 mm", show(describePageSize(200, 150)));

// ── fitToPage: nothing moves when everything fits ──
let pages = [[{ x: 20, y: 20, w: 40, h: 30 }]];
let r = fitToPage(pages, 297, 210, 15);
check("fitting album is untouched", r.moved === 0 && pages[0][0].x === 20 && pages[0][0].y === 20, show(r));

// ── Portrait page with rows down to 280 mm, switched to landscape (210 high) ──
const rows = [];
for (let row = 0; row < 6; row++) for (let col = 0; col < 3; col++) rows.push({ x: 20 + col * 60, y: 20 + row * 45, w: 40, h: 30 });
pages = [copy(rows)];
r = fitToPage(pages, 297, 210, 15);
check("all elements end up inside the landscape page", inside(pages, 297, 210), show(pages[0].map((e) => [e.x, e.y])));
check("only the vertical axis changed", pages[0].every((e, i) => e.x === rows[i].x), "");
check("sizes are never changed", pages[0].every((e, i) => e.w === rows[i].w && e.h === rows[i].h), "");
const ys = [...new Set(pages[0].map((e) => e.y))];
check("rows keep their order and do not merge", ys.length === 6 && ys.every((y, i) => i === 0 || y > ys[i - 1]), show(ys));
check("rows stay inside the bottom margin", Math.max(...pages[0].map((e) => e.y + e.h)) <= 210 - 15 + 1e-6, "");
check("moved count reports elements whose position changed", r.moved === 15 && r.pages === 1, show(r));

// ── A group that fits is shifted as a block, keeping its spacing ──
pages = [[{ x: 20, y: 150, w: 40, h: 30 }, { x: 20, y: 200, w: 40, h: 30 }]];
r = fitToPage(pages, 297, 210, 15);
check("small group is shifted, spacing kept", pages[0][1].y - pages[0][0].y === 50 && pages[0][1].y + 30 <= 195 + 1e-6, show(pages[0]));

// ── Element bigger than the page goes to the top-left and is reported ──
pages = [[{ x: 10, y: 10, w: 400, h: 30 }]];
r = fitToPage(pages, 297, 210, 15);
check("oversized element placed at the edge", pages[0][0].x === 0 && r.tooBig === 1, show({ el: pages[0][0], r }));

// ── Only pages that overflow change; counts span pages ──
pages = [[{ x: 20, y: 20, w: 40, h: 30 }], [{ x: 250, y: 20, w: 40, h: 30 }]];
r = fitToPage(pages, 210, 297, 15);
check("second page fixed, first untouched", pages[0][0].x === 20 && pages[1][0].x + 40 <= 210 && r.pages === 1 && r.moved === 1, show({ pages, r }));

// ── Dry run: count without changing anything ──
pages = [copy(rows)];
r = fitToPage(pages, 297, 210, 15, { dryRun: true });
check("dry run counts but does not move", r.moved === 15 && pages[0][17].y === rows[17].y, show(r));

process.exit(failures ? 1 : 0);
