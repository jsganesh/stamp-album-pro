// Page-size normalisation (Node, no browser). Run: node src/tests/test_page_size_migration.mjs
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { normalizePageSize, countOutside } = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}
const close = (a, b) => Math.abs(a - b) < 0.01;
const show = (r) => JSON.stringify(r);

const PAPER = { a4: [210, 297], a5: [148, 210], a3: [297, 420], letter: [215.9, 279.4], legal: [215.9, 355.6] };
const LEGACY = { a4: [238, 336.8], a5: [168, 238], a3: [336.8, 476.4], letter: [244.8, 316.8], legal: [244.8, 403.6] };

for (const [name, [w, h]] of Object.entries(PAPER)) {
  const r = normalizePageSize(w, h);
  check("standard " + name, r.name === name && !r.migrated && close(r.pw, w) && close(r.ph, h), show(r));
}
for (const [name, [w, h]] of Object.entries(LEGACY)) {
  const r = normalizePageSize(w, h);
  check("legacy " + name + " is migrated", r.name === name && r.migrated && close(r.pw, PAPER[name][0]) && close(r.ph, PAPER[name][1]), show(r));
}
let r = normalizePageSize(216, 279);
check("wizard letter rounding snaps to exact", r.name === "letter" && !r.migrated && close(r.pw, 215.9) && close(r.ph, 279.4), show(r));
r = normalizePageSize(216, 356);
check("wizard legal rounding snaps to exact", r.name === "legal" && !r.migrated && close(r.ph, 355.6), show(r));
r = normalizePageSize(297, 210);
check("landscape A4 keeps its shape", r.name === null && r.landscape && !r.migrated && close(r.pw, 297) && close(r.ph, 210), show(r));
r = normalizePageSize(336.8, 238);
check("legacy landscape A4 is migrated", r.name === null && r.landscape && r.migrated && close(r.pw, 297) && close(r.ph, 210), show(r));
r = normalizePageSize(200, 200);
check("custom size is left alone", r.name === null && !r.migrated && close(r.pw, 200) && close(r.ph, 200), show(r));

const pages = [[{ x: 10, y: 10, w: 50, h: 50 }, { x: 180, y: 10, w: 50, h: 20 }, { x: 0, y: 290, w: 20, h: 20 }, { x: 160, y: 10, w: 50, h: 10 }]];
check("countOutside counts only elements past the edge", countOutside(pages, 210, 297) === 2, String(countOutside(pages, 210, 297)));

process.exit(failures ? 1 : 0);
