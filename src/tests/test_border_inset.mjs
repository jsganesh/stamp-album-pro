// The page border's distance from the paper's edge (Node, no browser). Run: node src/tests/test_border_inset.mjs
// Printers can't print right to the edge, so new albums put the border 13 mm in; an album that
// doesn't say keeps 4.8 mm, as albums were drawn before.
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const C = require("../stamp_album/web/dsl_core.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail || "")); }
}

check("choices: 4.8, 8, 10, 12, 13 mm", JSON.stringify(C.BORDER_INSET_CHOICES) === "[4.8,8,10,12,13]");
check("new albums 13 mm, older ones 4.8", C.NEW_ALBUM_BORDER_INSET === 13 && C.OLD_ALBUM_BORDER_INSET === 4.8);
check("until an album says, 4.8 mm", C.getBorderInset() === 4.8);
check("setBorderInset(13)", C.setBorderInset(13) && C.getBorderInset() === 13);
check("bad values are refused and change nothing",
  !C.setBorderInset(-1) && !C.setBorderInset(31) && !C.setBorderInset("x") && C.getBorderInset() === 13);
const dsl = C.buildDSL({ pages: [[]], pageBorder: "solid", borderInset: 10 });
check("the file says the distance", dsl.indexOf("ALBUM_BORDER_INSET(10)") !== -1, dsl);
check("without one in the state, the current setting is written",
  C.buildDSL({ pages: [[]] }).indexOf("ALBUM_BORDER_INSET(13)") !== -1);
check("it reads back", C.parseDSL(dsl).borderInset === 10);
check("an album without the line is 4.8 mm", C.parseDSL("ALBUM_PAGES_SIZE(210 297)\nPAGE_START").borderInset === 4.8);
check("a bad value in a file is ignored", C.parseDSL("ALBUM_BORDER_INSET(99)\nPAGE_START").borderInset === 4.8);

console.log(failures ? failures + " FAILED" : "all passed");
process.exit(failures ? 1 : 0);
