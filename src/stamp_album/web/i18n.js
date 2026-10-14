// The editor's words, in the user's language.
//
// Every word the editor shows comes from a phrase list, one per language,
// written in src/stamp_album/locales/<lang>.json and turned into web/locales.js
// by tools/locales.py. English is the only language so far; it is also the
// fallback for any phrase another language is missing.
//
// In the page:  <button data-i18n="menu.file.new">New album</button>
//               <button data-i18n-attr="title:tb.undo_title;aria-label:tb.undo">…</button>
//               <span data-i18n-html="tut.step1">Click a <b>shape</b>…</span>
// In scripts:   S.t("toast.page_added"), S.t("toast.opened", { name: f }),
//               S.t("count.element", { count: 3 })  // plural forms: "one", "other"…
//
// The language is the one chosen in View › Language (stored in localStorage),
// else the computer's language if there is a phrase list for it, else English.
// ?lang=<code> in the address overrides both for that visit, without storing it;
// ?lang=pseudo shows every phrase accented and lengthened, to find text that
// isn't translated yet and layouts that break with longer words.
"use strict";
(function(root) {

var STORE_KEY = "stampalbum-lang";
var FALLBACK = "en";
var PSEUDO = "pseudo";
// Shown in the Language menu, in their own language.
var NATIVE_NAMES = { en: "English", de: "Deutsch", fr: "Français", es: "Español", it: "Italiano",
                     nl: "Nederlands", pt: "Português", zh: "中文", ja: "日本語" };

var _lang = FALLBACK;
var _missing = {};

function catalogs() {
    return (root && root.StampAlbumLocales) || _nodeCatalogs || {};
}
var _nodeCatalogs = null;

// Languages with a phrase list (not the pseudo-language).
function available() {
    return Object.keys(catalogs()).filter(function(k) { return k !== PSEUDO; }).sort(function(a, b) {
        return a === FALLBACK ? -1 : b === FALLBACK ? 1 : a < b ? -1 : 1;
    });
}

// The best available language for a list of preferences such as navigator.languages:
// an exact match ("pt-BR"), else the same language ("pt"), else English.
function pick(prefs, have) {
    have = have || available();
    prefs = (prefs || []).filter(Boolean);
    for (var i = 0; i < prefs.length; i++) {
        var p = String(prefs[i]).toLowerCase();
        if (p === PSEUDO) return PSEUDO;
        for (var j = 0; j < have.length; j++) if (have[j].toLowerCase() === p) return have[j];
        var base = p.split(/[-_]/)[0];
        for (var k = 0; k < have.length; k++) if (have[k].toLowerCase() === base) return have[k];
    }
    return FALLBACK;
}

function raw(lang, key) {
    var cat = catalogs()[lang];
    return cat && Object.prototype.hasOwnProperty.call(cat, key) ? cat[key] : undefined;
}

function pluralForm(lang, n) {
    try { return new Intl.PluralRules(lang).select(n); }
    catch (e) { return n === 1 ? "one" : "other"; }
}

// {name} placeholders; unknown ones are left as written.
function fill(str, params) {
    if (!params) return str;
    return str.replace(/\{(\w+)\}/g, function(m, name) {
        return Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : m;
    });
}

// Accented and about 35% longer, keeping {placeholders} and <tags> intact.
var ACCENTS = { a: "à", e: "ë", i: "ï", o: "ö", u: "ü", y: "ÿ", c: "ç", n: "ñ", s: "š", z: "ž",
                A: "À", E: "Ë", I: "Ï", O: "Ö", U: "Ü", Y: "Ÿ", C: "Ç", N: "Ñ", S: "Š", Z: "Ž" };
function pseudo(str) {
    var letters = 0;
    var out = String(str).replace(/(\{\w+\}|<[^>]*>|&\w+;)|([^{<&]+)/g, function(m, keep, text) {
        if (keep) return keep;
        letters += text.length;
        return text.replace(/[A-Za-z]/g, function(ch) { return ACCENTS[ch] || ch; });
    });
    return "[" + out + " " + new Array(Math.max(1, Math.round(letters * 0.35)) + 1).join("·") + "]";
}

// The phrase for key (the right plural form), before placeholders are filled.
function phrase(lang, key, params) {
    var v = raw(lang, key);
    if (v === undefined && lang !== FALLBACK) v = raw(FALLBACK, key);
    if (v === undefined) {
        _missing[key] = true;
        if (typeof console !== "undefined") console.warn("i18n: no phrase for " + key);
        return key;
    }
    if (typeof v === "object") { // plural forms
        var n = params && typeof params.count === "number" ? params.count : 0;
        var form = pluralForm(lang === PSEUDO ? FALLBACK : lang, n);
        v = v[form] !== undefined ? v[form] : v.other;
    }
    return v;
}

function t(key, params) {
    // Pseudo changes the phrase, never what fills it (a file name stays as it is).
    if (_lang === PSEUDO) return fill(pseudo(phrase(FALLBACK, key, params)), params);
    return fill(phrase(_lang, key, params), params);
}

// The first text node directly inside el that isn't only spaces; keeps the
// element's icons, shortcut labels and other child elements as they are.
function ownText(el) {
    for (var n = el.firstChild; n; n = n.nextSibling) {
        if (n.nodeType === 3 && /\S/.test(n.nodeValue)) return n;
    }
    return null;
}

// Phrases with markup (the tutorial's steps) may only hold these inline tags; the rest
// of the phrase is always text. Built as elements, never through innerHTML.
var RICH_TAGS = ["b", "strong", "i", "em", "kbd", "br"];
var RICH_TAG = /<(\/?)([a-z]+)\s*\/?>/gi;
var ENTITIES = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", "#39": "'", nbsp: "\u00a0" };
function decode(s) {
    return s.replace(/&(#39|\w+);/g, function(m, name) { return ENTITIES[name] || m; });
}
function setRich(el, phrase) {
    var doc = el.ownerDocument, open = [el], last = 0, m;
    el.textContent = "";
    function text(s) { if (s) open[open.length - 1].appendChild(doc.createTextNode(decode(s))); }
    RICH_TAG.lastIndex = 0;
    while ((m = RICH_TAG.exec(phrase)) !== null) {
        var name = m[2].toLowerCase();
        if (RICH_TAGS.indexOf(name) === -1) continue;  // not markup: stays in the text
        text(phrase.slice(last, m.index));
        last = RICH_TAG.lastIndex;
        if (name === "br") open[open.length - 1].appendChild(doc.createElement("br"));
        else if (!m[1]) open.push(open[open.length - 1].appendChild(doc.createElement(name)));
        else if (open.length > 1 && open[open.length - 1].localName === name) open.pop();
    }
    text(phrase.slice(last));
}

function setText(el, text) {
    var n = ownText(el);
    if (n) {
        var m = /^(\s*)[\s\S]*?(\s*)$/.exec(n.nodeValue);
        n.nodeValue = m[1] + text + m[2];
    } else {
        el.insertBefore(el.ownerDocument.createTextNode(text), el.firstChild);
    }
}

function apply(scope) {
    var doc = root && root.document;
    scope = scope || doc;
    if (!scope || !scope.querySelectorAll) return;
    var i, els;
    els = scope.querySelectorAll("[data-i18n]");
    for (i = 0; i < els.length; i++) setText(els[i], t(els[i].getAttribute("data-i18n")));
    els = scope.querySelectorAll("[data-i18n-html]");
    for (i = 0; i < els.length; i++) setRich(els[i], t(els[i].getAttribute("data-i18n-html")));
    els = scope.querySelectorAll("[data-i18n-attr]");
    for (i = 0; i < els.length; i++) {
        els[i].getAttribute("data-i18n-attr").split(";").forEach(function(pair) {
            var at = pair.indexOf(":");
            if (at > 0) els[i].setAttribute(pair.slice(0, at).trim(), t(pair.slice(at + 1).trim()));
        });
    }
    if (doc && (scope === doc)) doc.documentElement.setAttribute("lang", _lang === PSEUDO ? "en-XA" : _lang);
}

function stored() {
    try { return root.localStorage.getItem(STORE_KEY); } catch (e) { return null; }
}

// Chooses the language at startup: ?lang=, then the stored choice, then the computer's.
function detect() {
    var prefs = [];
    try {
        var q = new URLSearchParams(root.location.search).get("lang");
        if (q) prefs.push(q);
    } catch (e) { /* no location (Node) */ }
    var s = stored();
    if (s) prefs.push(s);
    var nav = root && root.navigator;
    if (nav) prefs = prefs.concat(nav.languages && nav.languages.length ? nav.languages : [nav.language]);
    return pick(prefs);
}

function setLanguage(lang, remember) {
    _lang = lang === PSEUDO ? PSEUDO : pick([lang]);
    if (remember) {
        try { root.localStorage.setItem(STORE_KEY, _lang); } catch (e) { /* storage blocked */ }
    }
    apply();
    return _lang;
}

var I18n = {
    t: t,
    apply: apply,
    available: available,
    pick: pick,
    pseudo: pseudo,
    setLanguage: setLanguage,
    detect: detect,
    nativeName: function(lang) { return NATIVE_NAMES[lang] || lang; },
    language: function() { return _lang; },
    missing: function() { return Object.keys(_missing); },
    STORE_KEY: STORE_KEY,
    RICH_TAGS: RICH_TAGS,
    // Node tests: use these phrase lists instead of window.StampAlbumLocales.
    _useCatalogs: function(c, lang) { _nodeCatalogs = c; _lang = lang || FALLBACK; _missing = {}; },
};

if (typeof module !== "undefined" && module.exports) module.exports = I18n;
if (root) {
    root.StampAlbumI18n = I18n;
    _lang = detect();
    // The page above this script is already parsed: put it in the chosen language
    // before the editor's scripts start reading and changing it.
    if (root.document && root.document.body) apply();
}

})(typeof window !== "undefined" ? window : null);
