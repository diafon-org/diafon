// Validate the embedded JS conversion engine against the Python CLI, across every regime.
// Usage: python3 scripts/gen_uni_page.py && node scripts/check_js.mjs
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";

const html = readFileSync(new URL("../docs/index.html", import.meta.url), "utf8");
const D = JSON.parse(html.match(/id="data">(.*?)<\/script>/s)[1]);

// --- re-implement the page's engine here (kept byte-identical in intent to the <script>) ---
const TONE = { "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵" };
const UKEYS = D.keys;
function utok(w) { const t = []; let i = 0; while (i < w.length) { let m = null;
  for (const k of UKEYS) { if (k.length <= w.length - i && w.substr(i, k.length) === k) { m = k; break; } }
  if (m) { t.push(m); i += m.length; } else { t.push(w[i]); i++; } } return t; }
// capitalise the first character that HAS a capital; a glyph with none (the apostrophe /ʔ/) comes
// back unchanged and the caller carries the capital to the next glyph — 'Alif, not 'alif
const capF = g => { if (!g) return g; for (let i = 0; i < g.length; i++) { const c = g[i];
  if (c.toUpperCase() !== c) return g.slice(0, i) + c.toUpperCase() + g.slice(i + 1); } return g; };
const isVTok = t => !!t && "aeiou".includes(t[0]);
function toneSign(glyphs, toks, d) { // LAST vowel group: first a-, else e-, else o-based, else LAST vowel (= Pinyin); 0/5 neutral
  if (d === "0" || d === "5") return "";
  const mark = D.toneSigns[d]; if (mark === undefined) return d;
  let group = [];
  toks.forEach((t, i) => { if (isVTok(t)) { if (group.length && group[group.length - 1] === i - 1) group.push(i); else group = [i]; } });
  if (!group.length) return d;
  let pick = group[group.length - 1];
  outer: for (const b of ["a", "e", "o"]) { for (const i of group) { if (toks[i][0] === b) { pick = i; break outer; } } }
  glyphs[pick] = (glyphs[pick] + mark).normalize("NFC"); return "";
}
function urend(text, map, useCaps = true, useSup = false, useTones = false) { // superscript tones: IPA only
  const segParts = w => { const low = w.toLowerCase(), toks = utok(low); let i = 0; const glyphs = [];
    const shout = w === w.toUpperCase() && w !== low;
    let pending = false;
    for (const x of toks) { const g = map[x] !== undefined ? map[x] : x;
      if (useCaps && (/[A-Z]/.test(w[i]) || pending)) { const c = shout ? g.toUpperCase() : capF(g); pending = (c === g); glyphs.push(c); }
      else glyphs.push(g);
      i += x.length; } return [toks, glyphs]; };
  return text.trim().split(/\s+/).filter(Boolean).map(w => {
    let piece = "", seg = "";
    for (const ch of w) {
      if (ch === "0" || TONE[ch]) {
        const [toks, glyphs] = segParts(seg);
        if (useSup) piece += glyphs.join("") + (TONE[ch] || ch);
        else if (useTones) { const trail = toneSign(glyphs, toks, ch); piece += glyphs.join("") + trail; }
        else piece += glyphs.join("") + ch;
        seg = "";
      } else seg += ch; }
    const [, glyphs] = segParts(seg);
    return piece + glyphs.join(""); }).join(" "); }
const VOWELS = new Set(["a", "e", "i", "o", "u"]);
const isV = t => !!t && VOWELS.has(t[0]);
function tokenize(word, labels) { const labs = [...labels].sort((a, b) => b.length - a.length);
  const toks = []; let i = 0; while (i < word.length) { let m = null;
    for (const L of labs) { if (word.startsWith(L, i)) { m = L; break; } }
    if (m) { toks.push(m); i += m.length; } else { toks.push(word[i]); i++; } } return toks; }
function applyTone(py, tone) { if (tone === 0 || tone === 5 || tone == null) return py;
  const put = (s, i) => s.slice(0, i) + D.tone[s[i]][tone - 1] + s.slice(i + 1);
  if (py.includes("a")) return put(py, py.indexOf("a"));
  if (py.includes("e")) return put(py, py.indexOf("e"));
  if (py.includes("ou")) return put(py, py.indexOf("o"));
  for (let i = py.length - 1; i >= 0; i--) if (D.tone[py[i]]) return put(py, i); return py; }
function ruleG(rules, t, prv, nxt, k) { // first matching context rule's grapheme, or null
  for (const r of rules) {
    if (r.t !== t) continue;
    if (r.next && !(nxt && r.next.includes(nxt))) continue;
    if (r.next_vowel && !isV(nxt)) continue;
    if (r.prev && !(prv && r.prev.includes(prv))) continue;
    if (r.first && k !== 0) continue;
    return r.g; }
  return null; }
function decodeWord(word, orth, lang, rules, tones) { let tone = null;
  if (tones && lang === "zh" && word.length > 1 && "012345".includes(word.slice(-1))) { tone = +word.slice(-1); word = word.slice(0, -1); }
  const low = word.toLowerCase();
  const toks = tokenize(low, Object.keys(orth)); const out = [];
  const caps = []; { let ci = 0; for (const t of toks) { caps.push(/[A-Z]/.test(word[ci])); ci += t.length; } }
  const shout = word === word.toUpperCase() && word !== low; let pending = false;
  for (let k = 0; k < toks.length; k++) { const t = toks[k], nxt = k + 1 < toks.length ? toks[k + 1] : null, prv = k ? toks[k - 1] : null;
    if (t === "w" && out.length) { out[out.length - 1] = out[out.length - 1][0] + out[out.length - 1]; continue; }
    const rg = ruleG(rules, t, prv, nxt, k);
    const g = rg !== null ? rg : (orth[t] !== undefined ? orth[t] : t);
    if (caps[k] || pending) { const c = shout ? g.toUpperCase() : capF(g); pending = (c === g); out.push(c); }
    else out.push(g); }
  const res = out.join(""); return tone != null ? applyTone(res, tone) : res; }
function offLabels(lang, off) { const G = (D.groups || {})[lang] || {}; const s = new Set();
  for (const n of off || []) for (const l of (G[n] !== undefined ? G[n] : [n])) s.add(l); return s; }
function decode(text, lang, lazy, off) { let orth = { ...D.orth[lang] };
  if (lazy && D.lazy[lang]) orth = { ...orth, ...D.lazy[lang] };
  const skip = offLabels(lang, off);
  if (skip.size) for (const k of Object.keys(orth)) if (skip.has(k) && D.nat[k] !== undefined) orth[k] = D.nat[k];
  const rules = (D.rules[lang] || []).filter(r => !(off || []).includes(r.group) && !skip.has(r.t));
  const tones = !(off || []).includes("tones");
  return text.trim().split(/\s+/).filter(Boolean).map(w => {
    if (lang === "zh") { let piece = "", seg = "";
      for (const ch of w) { if (/[0-9]/.test(ch)) { piece += decodeWord(seg + ch, orth, lang, rules, tones); seg = ""; } else seg += ch; }
      return piece + (seg ? decodeWord(seg, orth, lang, rules, tones) : ""); }
    return decodeWord(w, orth, lang, rules, tones); }).join(" "); }

// --- test corpus ---
const WORDS = [
  "sjok sewp njawr", "pjatj", "kecsecnecm sewpejn", "acswonj", "hoswuw", "ejdj nacdj kutjac",
  "kxaxn3 kau1", "sjan1 kxaxn3 kau1", "tqix1 sjuc4", "tqi1 sji1 tqic1 sjic1", "tquc1 sjuc4 suc4",
  "nic3", "de5", "de0", "tou1 kxau3 kuo2", "hacix ixow fiuw", "ixejs uxejst", "ix ux icx ucx", "raxn2", "sy zy py ky", "tqx dqx", "py ty ky", "tqony1kuo2 niu2nai3", "tx nx lx rx tj dj nj lj pj kj", "TW Tw SJOKK h hx hj hq ax", "Hqalif hqalif HQALIF", "r rc rj rx aq", "SJOK SEWP NJAWR HOSWUW DYAX", "iu3 ui4 un2 u3 i1 ican2 puo1 aq2",
  "sjiau3 liu2 tou1",
  "alma kert", "ni3 hao3", "xiao3", "zhong1 guo2", "ren2", "cai4", "bao3 dao4", "pa4",
  "berd werld show boy law", "dhuh kat sijts awn dhuh flawr",
  "Sjok Sewp Njawr", "Acswonj SJOK", "Dhuh kat Sijts", "Sjan1 kxaxn3",
  "wo3 xi3huan1 pin1yin1, ni3 ne5?", "the kisj kutjac aclsik and zhong1 guo2",
];
const py = (sub, args) => execFileSync("python3", ["-m", "diaphone.cli", sub, ...args],
  { cwd: new URL("..", import.meta.url), env: { ...process.env, PYTHONPATH: "src" }, encoding: "utf8" }).trim();

let fail = 0, total = 0;
function check(name, got, want) { total++; if (got !== want) { fail++;
  console.log(`  MISMATCH [${name}]\n    js : ${JSON.stringify(got)}\n    py : ${JSON.stringify(want)}`); } }

for (const w of WORDS) {
  check(`uni    "${w}"`, urend(w, D.nat), py("render", ["uni", w]));
  check(`uni·ton"${w}"`, urend(w, D.nat, true, false, true), py("render", ["uni", w, "--tones"]));
  check(`ipa    "${w}"`, urend(w, D.ipa, false, true), py("render", ["ipa", w]));
  check(`hu     "${w}"`, decode(w, "hu", false), py("decode", ["hu", w]));
  check(`hu·lazy"${w}"`, decode(w, "hu", true), py("decode", ["hu", w, "--lazy"]));
  check(`zh     "${w}"`, decode(w, "zh", false), py("decode", ["zh", w]));
  check(`zh·lazy"${w}"`, decode(w, "zh", true), py("decode", ["zh", w, "--lazy"]));
  check(`en     "${w}"`, decode(w, "en", false), py("decode", ["en", w]));
  check(`en·lazy"${w}"`, decode(w, "en", true), py("decode", ["en", w, "--lazy"]));
  // the ADOPTION PROFILE: each group off on its own, and all of them at once (= the uni view)
  for (const lang of ["hu", "zh", "en"]) {
    const names = Object.keys((D.groups || {})[lang] || {});
    for (const g of [...names.map(n => [n]), names]) {
      if (!g.length) continue;
      check(`${lang}·off[${g.join(",")}] "${w}"`, decode(w, lang, false, g),
            py("decode", [lang, w, "--off", g.join(",")]));
    }
  }
}
console.log(`\n${total - fail}/${total} checks passed` + (fail ? `  — ${fail} MISMATCH` : "  — JS engine matches the Python CLI ✓"));
process.exit(fail ? 1 : 0);
