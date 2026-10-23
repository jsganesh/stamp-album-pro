// The title and plan page in the editor core (Node, no browser). Run: node src/tests/test_exhibit_plan.mjs
// The form's answers become text items, each marked with its part; the plan is numbered
// chapters and sections; the file keeps the parts; the page starts higher before it gives up.
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const C = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}
// About Helvetica's average width: 0.5 em a character.
const measure = (text, font, pt) => String(text).length * pt * 0.5 * 25.4 / 72;
const LABELS = { purpose: "Purpose", scope: "Scope", plan: "Plan of the exhibit",
                 important: "Important items", research: "Research", references: "References" };
const ANSWERS = { title: "Exhibit Title", by: "A traditional exhibit by Your Name",
                  purpose: "Why", scope: "Where", important: "Double frames", research: "Mine",
                  references: "Books",
                  chapters: [{ level: 1, text: "First" }, { level: 2, text: "A" }, { level: 2, text: "B" },
                             { level: 1, text: "Second" }] };

// ── Numbering ──
check("chapters and sections are numbered as a decimal plan",
  C.planText(ANSWERS.chapters) === "1. First\n1.1 A\n1.2 B\n2. Second", C.planText(ANSWERS.chapters));
check("a section before any chapter is a chapter",
  C.planText([{ level: 2, text: "X" }, { level: 2, text: "Y" }]) === "1. X\n1.1 Y");
check("empty rows are left out and don't take a number",
  C.planText([{ level: 1, text: " " }, { level: 1, text: "A" }]) === "1. A");
check("a plan reads back as the chapters it came from",
  JSON.stringify(C.planChapters(C.planText(ANSWERS.chapters))) === JSON.stringify(ANSWERS.chapters));
check("lines typed on the page without numbers read as chapters",
  JSON.stringify(C.planChapters("Intro\n2.1 Part")) === JSON.stringify([{ level: 1, text: "Intro" }, { level: 2, text: "Part" }]));

// ── Layout ──
const r = C.exhibitPlanLayout(ANSWERS, LABELS, 210, 297, measure);
const at = (part) => r.items.find(it => it.part === part);
check("every part has an item, in the page's order",
  r.items.map(it => it.part).join() === "title,by,purpose_label,purpose,scope_label,scope,plan_label,plan," +
    "important_label,important,research_label,research,references_label,references",
  r.items.map(it => it.part).join());
check("the title is a marked heading, 22 pt bold, centred, 40 mm down",
  at("title").role === "heading" && at("title").font === "HB" && at("title").fs === 22 &&
  at("title").align === "center" && at("title").y === 40);
check("as the Title page template: the first section's name 74 mm down, its text 83 mm",
  at("purpose_label").y === 74 && at("purpose").y === 83, at("purpose_label").y + " " + at("purpose").y);
check("every item spans 20 to 190 mm", r.items.every(it => it.x === 20 && it.w === 170));
check("the plan text is numbered", at("plan").lbl === "1. First\n1.1 A\n1.2 B\n2. Second");
check("the section names are as given", at("plan_label").lbl === "Plan of the exhibit");
check("items don't overlap, top to bottom",
  r.items.every((it, i) => i === 0 || it.y >= r.items[i - 1].y + r.items[i - 1].h - 1e-9));
check("it fits an A4 page", r.fits && r.bottom <= 277);
const few = C.exhibitPlanLayout({ title: "T", purpose: "P" }, LABELS, 210, 297, measure);
check("empty parts are left out", few.items.map(it => it.part).join() === "title,purpose_label,purpose",
  few.items.map(it => it.part).join());
const long = { title: "T", purpose: Array(140).fill("word").join(" "),
               chapters: Array.from({ length: 32 }, (_, i) => ({ level: 1, text: "Chapter " + i })) };
const tight = C.exhibitPlanLayout(long, LABELS, 210, 297, measure);
check("a page that is a little long starts higher, at 25 mm", tight.fits && tight.items[0].y === 25,
  tight.items[0].y + " " + tight.bottom);
const tooLong = C.exhibitPlanLayout(Object.assign({}, long, { chapters: long.chapters.concat(long.chapters) }),
  LABELS, 210, 297, measure);
check("a page too long for the paper says so", !tooLong.fits && tooLong.bottom > tooLong.limit);
const wide = C.exhibitPlanLayout(ANSWERS, LABELS, 460, 297, measure);
check("an FIP 46 cm sheet uses its width", wide.items.every(it => it.w === 420));

// ── The file ──
const els = r.items.map((it, i) => Object.assign({ id: "e" + i, t: "text", s: "text" }, it));
const dsl = C.buildDSL({ pages: [els.concat([{ id: "s", t: "stamp", s: "rectangle", x: 30, y: 250, w: 20, h: 24, lbl: "A",
                                               bdr: "solid", bdrW: 0.5, bdrC: "#000", fill: "#fff", fillA: 100 }])] });
check("each part is written after its text", /PAGE_TEXT_ROLE\("heading"\)\nPAGE_TEXT_PART\("title"\)/.test(dsl) &&
  /"left"\)\nPAGE_TEXT_PART\("plan"\)/.test(dsl));
const back = C.parseDSL(dsl).pages[0];
check("the parts read back", back.filter(el => el.part).map(el => el.part).join() === r.items.map(it => it.part).join());
check("the title is still a heading", back.find(el => el.part === "title").role === "heading");
check("other items have no part", back.find(el => el.t === "stamp").part === undefined);
check("an unknown part is ignored",
  C.parseDSL('PAGE_START\nPAGE_TEXT_AT(20 20 100 10 "HN" 10 "x" "left")\nPAGE_TEXT_PART("bogus")').pages[0][0].part === undefined);
check("a part is never written for a name it doesn't know",
  C.serializeEl({ t: "text", x: 1, y: 1, w: 1, h: 1, lbl: "x", part: "bogus" }).indexOf("PART") === -1);

console.log(failures ? failures + " FAILED" : "all passed");
process.exit(failures ? 1 : 0);
