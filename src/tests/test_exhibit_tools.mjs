// Page headings linked to the plan, and Check exhibit (Node, no browser).
// Run: node src/tests/test_exhibit_tools.mjs
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const C = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}
const PLAN = "1. First printing\n1.1 Blued paper\n1.2 White paper\n2. Later printings";
const entries = C.planEntries(PLAN);

// ── The plan's numbered lines ──
check("entries carry their numbers", entries.map(e => e.num).join() === "1,1.1,1.2,2");
check("a heading's words, as the plan prints them",
  C.chapterHeading(entries[0]) === "1. First printing" && C.chapterHeading(entries[1]) === "1.1 Blued paper");
const moved = C.planEntries("1. Introduction\n2. First printing\n2.1 Blued paper\n2.2 White paper\n3. Later printings");
check("a chapter that moved keeps its heading, by name",
  C.chapterFor({ chapter: "1.1", lbl: "1.1 Blued paper" }, moved).num === "2.1");
const renamed = C.planEntries("1. First printing\n1.1 Bluish paper\n1.2 White paper");
check("a renamed chapter keeps its heading, by number",
  C.chapterHeading(C.chapterFor({ chapter: "1.1", lbl: "1.1 Blued paper" }, renamed)) === "1.1 Bluish paper");
check("a chapter that has gone has no entry",
  C.chapterFor({ chapter: "3", lbl: "3. Covers" }, entries) === null);
check("an item not linked has none", C.chapterFor({ lbl: "1. First printing" }, entries) === null);

// ── The file ──
const dsl = C.serializeEl({ t: "text", x: 1, y: 1, w: 10, h: 5, lbl: "1.1 Blued paper", role: "heading", chapter: "1.1" });
check("the link is written after the heading", /PAGE_TEXT_ROLE\("heading"\)\nPAGE_TEXT_CHAPTER\("1.1"\)$/.test(dsl), dsl);
check("it reads back", C.parseDSL("PAGE_START\n" + dsl).pages[0][0].chapter === "1.1");
check("a bad number is neither written nor read",
  C.serializeEl({ t: "text", x: 1, y: 1, w: 1, h: 1, lbl: "x", chapter: "1a" }).indexOf("CHAPTER") === -1 &&
  C.parseDSL('PAGE_START\nPAGE_TEXT_AT(1 1 1 1 "HN" 9 "x" "left")\nPAGE_TEXT_CHAPTER("x")').pages[0][0].chapter === undefined);

// ── Check exhibit ──
const codes = r => r.map(f => f.level + ":" + f.code + (f.page === null ? "" : "@" + f.page) + (f.n ? "x" + f.n : ""));
const planPage = [{ t: "text", part: "title", lbl: "T", role: "heading" }, { t: "text", part: "plan", lbl: PLAN }];
const good = [planPage,
  [{ t: "text", role: "heading", lbl: "1. First printing", chapter: "1" }, { t: "stamp", lbl: "Penny" }]];
const r1 = C.exhibitCheck({ pages: good, pw: 210, ph: 297, pageBorder: "solid", warnings: [0, 0] });
check("a tidy exhibit has nothing to fix", codes(r1).join() === "advice:framesx1", codes(r1).join());
check("frames: 2 pages of 16", r1[0].perFrame === 16 && r1[0].last === 2);
const r2 = C.exhibitCheck({ pages: [[{ t: "stamp", lbl: "" }, { t: "stamp", lbl: "", hdg: "1840" }], []],
                            pw: 215.9, ph: 279.4, pageBorder: "victorian", warnings: [3, 0] });
check("the problems a page can have", codes(r2).join() ===
  "fix:no_plan,fix:decorative_border,advice:no_heading@0,advice:unnamed_stamps@0x1,fix:caption_clash@0x3,advice:empty_page@1,advice:paper",
  codes(r2).join());
const r3 = C.exhibitCheck({ pages: [[{ t: "stamp", lbl: "x" }], planPage], pw: 230, ph: 297, warnings: [] });
check("a plan page that isn't first", codes(r3).indexOf("fix:plan_not_first@1") !== -1, codes(r3).join());
const r4 = C.exhibitCheck({ pages: [planPage, [{ t: "text", role: "heading", lbl: "3. Covers", chapter: "3" }]],
                            pw: 210, ph: 297, warnings: [] });
check("a heading whose chapter has gone", codes(r4).indexOf("fix:chapter_gone@1") !== -1, codes(r4).join());
const many = [planPage].concat(Array.from({ length: 23 }, () => [{ t: "text", role: "heading", lbl: "H" }]));
const r5 = C.exhibitCheck({ pages: many, pw: 310, ph: 297, warnings: [] });
const fr = r5.find(f => f.code.indexOf("frames") === 0);
check("31 cm sheets: 12 to a frame, 24 pages fill 2 exactly", fr.code === "frames_full" && fr.n === 2 && fr.perFrame === 12,
  JSON.stringify(fr));
const r6 = C.exhibitCheck({ pages: [[{ t: "text", part: "title", lbl: "T" }]], pw: 210, ph: 297 });
check("a plan page without chapters", codes(r6).indexOf("fix:plan_empty@0") !== -1, codes(r6).join());

console.log(failures ? failures + " FAILED" : "all passed");
process.exit(failures ? 1 : 0);
