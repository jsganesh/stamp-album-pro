// The editor's phrase lookup (web/i18n.js), without a browser. Run: node src/tests/test_i18n.mjs
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const I18n = require("../stamp_album/web/i18n.js");
const LOCALES = require("../stamp_album/web/locales.js");

let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("PASS: " + name);
  else { failures++; console.log("FAIL: " + name + " " + (detail === undefined ? "" : JSON.stringify(detail))); }
}

const TEST = {
  en: {
    "msg.hello": "Hello",
    "msg.opened": "Opened {name}",
    "msg.count": { one: "{count} stamp", other: "{count} stamps" },
    "msg.only_en": "Only in English",
    "ui.tut": "<b>Add stamps</b> at {size}",
  },
  de: {
    "msg.hello": "Hallo",
    "msg.opened": "{name} geöffnet",
    "msg.count": { one: "{count} Marke", other: "{count} Marken" },
  },
  pl: { "msg.count": { one: "{count} znaczek", few: "{count} znaczki", many: "{count} znaczków", other: "{count} znaczka" } },
  "pt-BR": { "msg.hello": "Olá" },
};

// ── Lookups ──
I18n._useCatalogs(TEST, "en");
check("plain phrase", I18n.t("msg.hello") === "Hello");
check("placeholder filled", I18n.t("msg.opened", { name: "album.slbum" }) === "Opened album.slbum");
check("unknown placeholder left as written", I18n.t("msg.opened", {}) === "Opened {name}");
check("one", I18n.t("msg.count", { count: 1 }) === "1 stamp", I18n.t("msg.count", { count: 1 }));
check("other", I18n.t("msg.count", { count: 3 }) === "3 stamps");
check("zero is plural in English", I18n.t("msg.count", { count: 0 }) === "0 stamps");
check("nothing missing yet", I18n.missing().length === 0, I18n.missing());
check("a missing key shows the key", I18n.t("msg.nope") === "msg.nope");
check("and is recorded", I18n.missing().indexOf("msg.nope") !== -1, I18n.missing());

I18n._useCatalogs(TEST, "de");
check("German phrase", I18n.t("msg.hello") === "Hallo");
check("German word order", I18n.t("msg.opened", { name: "a.slbum" }) === "a.slbum geöffnet");
check("German plural", I18n.t("msg.count", { count: 2 }) === "2 Marken");
check("untranslated phrase falls back to English", I18n.t("msg.only_en") === "Only in English");
check("fallback is not counted as missing", I18n.missing().length === 0, I18n.missing());

I18n._useCatalogs(TEST, "pl");
check("Polish 'few' (2–4)", I18n.t("msg.count", { count: 3 }) === "3 znaczki", I18n.t("msg.count", { count: 3 }));
check("Polish 'many' (5+)", I18n.t("msg.count", { count: 5 }) === "5 znaczków", I18n.t("msg.count", { count: 5 }));
check("Polish 'one'", I18n.t("msg.count", { count: 1 }) === "1 znaczek");

// ── Choosing a language ──
I18n._useCatalogs(TEST, "en");
check("available: English first, then the rest", I18n.available().join() === "en,de,pl,pt-BR", I18n.available());
check("exact match", I18n.pick(["pt-BR"]) === "pt-BR");
check("case doesn't matter", I18n.pick(["PT-br"]) === "pt-BR");
check("regional variant uses the language", I18n.pick(["de-AT"]) === "de");
check("first available preference wins", I18n.pick(["fr-FR", "de-CH", "en"]) === "de");
check("nothing available: English", I18n.pick(["fr", "ja"]) === "en");
check("no preferences: English", I18n.pick([]) === "en");
check("pseudo can be asked for", I18n.pick(["pseudo"]) === "pseudo");
check("pseudo is not offered", I18n.available().indexOf("pseudo") === -1);
check("native names", I18n.nativeName("de") === "Deutsch" && I18n.nativeName("xx") === "xx");

// ── Pseudo-language ──
const p = I18n.pseudo("Hello {name}, see <b>Page border</b>");
check("pseudo accents letters", p.indexOf("Hëllö") !== -1, p);
check("pseudo keeps placeholders", p.indexOf("{name}") !== -1, p);
check("pseudo keeps tags", p.indexOf("<b>") !== -1 && p.indexOf("</b>") !== -1, p);
check("pseudo is bracketed", p[0] === "[" && p[p.length - 1] === "]", p);
const plain = "Export as PDF";
const longer = I18n.pseudo(plain).length / plain.length;
check("pseudo is about a third longer, plus its brackets", longer >= 1.3 && longer <= 1.75, longer);
I18n._useCatalogs(TEST, "pseudo");
check("pseudo leaves what fills a phrase as it is", I18n.t("msg.opened", { name: "a.slbum" }).indexOf("a.slbum") !== -1,
      I18n.t("msg.opened", { name: "a.slbum" }));
check("pseudo plurals use English rules", I18n.t("msg.count", { count: 1 }).indexOf("1 štàmp") !== -1,
      I18n.t("msg.count", { count: 1 }));

// ── The shipped phrase lists ──
check("English is shipped", !!LOCALES.en);
check("translators' notes are not shipped", !Object.keys(LOCALES.en).some((k) => k.startsWith("_")));
I18n._useCatalogs(LOCALES, "en");
check("a real phrase", I18n.t("msg.page_added") === "Page added");
check("a real plural", I18n.t("msg.count_elements", { count: 1 }) === "1 element" &&
      I18n.t("msg.count_elements", { count: 4 }) === "4 elements");
for (const [lang, phrases] of Object.entries(LOCALES)) {
  for (const [k, v] of Object.entries(phrases)) {
    if (typeof v === "object") check(`${lang} ${k} has "other"`, typeof v.other === "string");
  }
}

if (failures) { console.log(failures + " failed"); process.exit(1); }
console.log("all passed");
