// Validate the embedded JS conversion engine against the Python CLI, across every regime.
// Usage: python3 scripts/gen_native_page.py && node scripts/check_js.mjs
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";

const html = readFileSync(new URL("../docs/viz/notation.html", import.meta.url), "utf8");
const D = JSON.parse(html.match(/id="data">(.*?)<\/script>/s)[1]);

// --- re-implement the page's engine here (kept byte-identical in intent to the <script>) ---
const TONE = { "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵" };
const UKEYS = D.keys;
function utok(w) { const t = []; let i = 0; while (i < w.length) { let m = null;
  for (const k of UKEYS) { if (k.length <= w.length - i && w.substr(i, k.length) === k) { m = k; break; } }
  if (m) { t.push(m); i += m.length; } else { t.push(w[i]); i++; } } return t; }
const capF = g => g ? g[0].toUpperCase() + g.slice(1) : g;
function urend(text, map, useCaps = true) { return text.trim().split(/\s+/).filter(Boolean).map(w => {
  let tn = ""; if (w.length > 1 && TONE[w.slice(-1)]) { tn = TONE[w.slice(-1)]; w = w.slice(0, -1); }
  const low = w.toLowerCase(), toks = utok(low); let i = 0, out = "";
  for (const x of toks) { const g = map[x] !== undefined ? map[x] : x;
    out += (useCaps && /[A-Z]/.test(w[i])) ? capF(g) : g; i += x.length; }
  return out + tn; }).join(" "); }
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
function decodeWord(word, orth, lang) { let tone = null;
  if (lang === "zh" && word.length > 1 && "012345".includes(word.slice(-1))) { tone = +word.slice(-1); word = word.slice(0, -1); }
  const low = word.toLowerCase();
  const toks = tokenize(low, Object.keys(orth)); const out = [];
  const caps = []; { let ci = 0; for (const t of toks) { caps.push(/[A-Z]/.test(word[ci])); ci += t.length; } }
  for (let k = 0; k < toks.length; k++) { const t = toks[k], nxt = k + 1 < toks.length ? toks[k + 1] : null, prv = k ? toks[k - 1] : null;
    if (t === "w" && out.length) { out[out.length - 1] = out[out.length - 1][0] + out[out.length - 1]; continue; }
    let g = orth[t] !== undefined ? orth[t] : t;
    if (lang === "hu" && t === "i" && isV(nxt)) { g = "j"; }
    else if (lang === "zh") {
      if (D.zhRetro[t]) { g = D.zhRetro[t][(nxt === "i" || nxt === "ic") ? 1 : 0]; }
      else if (t === "ic" && D.zhRetro[prv]) { g = "u"; }
      else if (t === "i" && k === 0 && isV(nxt)) { g = "y"; }
      else if (t === "u" && prv === "a") { g = "o"; } }
    out.push(caps[k] ? capF(g) : g); }
  const res = out.join(""); return tone != null ? applyTone(res, tone) : res; }
function decode(text, lang, lazy, endict) { let orth = { ...D.orth[lang] };
  if ((lazy || (endict && lang === "en")) && D.lazy[lang]) orth = { ...orth, ...D.lazy[lang] };
  const dict = (lang === "en" && endict) ? D.enDict : null;
  return text.trim().split(/\s+/).filter(Boolean).map(w => {
    if (dict) { const key = tokenize(w.toLowerCase(), Object.keys(orth)).map(t => D.enCanon[t] || t).join("");
      if (dict[key]) return /[A-Z]/.test(w[0]) ? capF(dict[key]) : dict[key]; }
    return decodeWord(w, orth, lang); }).join(" "); }

// --- test corpus ---
const WORDS = [
  "sjok sewp njawr", "pjatj", "kecsecnecm sewpejn", "acswonj", "hoswuw", "ejdj nacdj kutjac",
  "kxaxn3 kau1", "sjan1 kxaxn3 kau1", "tqix1 sjuc4", "tqi1 sji1 tqic1 sjic1", "tquc1 sjuc4 suc4",
  "nic3", "de5", "tou1 kxau3 kuo2", "raxn2", "sjj zjj kc gc", "tqx dqx", "ph th kh",
  "alma kert", "ni3 hao3", "xiao3", "zhong1 guo2", "ren2", "cai4", "bao3 dao4", "pa4",
  "berd werld show boy law", "dhuh kat sijts awn dhuh flawr",
  "Sjok Sewp Njawr", "Acswonj SJOK", "Dhuh kat Sijts", "Sjan1 kxaxn3",
];
const py = (sub, args) => execFileSync("python3", ["-m", "diaphone.cli", sub, ...args],
  { cwd: new URL("..", import.meta.url), env: { ...process.env, PYTHONPATH: "src" }, encoding: "utf8" }).trim();

let fail = 0, total = 0;
function check(name, got, want) { total++; if (got !== want) { fail++;
  console.log(`  MISMATCH [${name}]\n    js : ${JSON.stringify(got)}\n    py : ${JSON.stringify(want)}`); } }

for (const w of WORDS) {
  check(`native "${w}"`, urend(w, D.nat), py("render", ["native", w]));
  check(`nat-hu "${w}"`, urend(w, D.natHu), py("render", ["native-hu", w]));
  check(`nat-zh "${w}"`, urend(w, D.natZh), py("render", ["native-zh", w]));
  check(`ipa    "${w}"`, urend(w, D.ipa, false), py("render", ["ipa", w]));
  check(`hu     "${w}"`, decode(w, "hu", false), py("decode", ["hu", w]));
  check(`hu·lazy"${w}"`, decode(w, "hu", true), py("decode", ["hu", w, "--lazy"]));
  check(`zh     "${w}"`, decode(w, "zh", false), py("decode", ["zh", w]));
  check(`zh·lazy"${w}"`, decode(w, "zh", true), py("decode", ["zh", w, "--lazy"]));
  check(`en     "${w}"`, decode(w, "en", false), py("decode", ["en", w]));
  check(`en·lazy"${w}"`, decode(w, "en", true), py("decode", ["en", w, "--lazy"]));
  check(`en·dict"${w}"`, decode(w, "en", true, true), py("decode", ["en", w, "--lazy", "--dict"]));
}
console.log(`\n${total - fail}/${total} checks passed` + (fail ? `  — ${fail} MISMATCH` : "  — JS engine matches the Python CLI ✓"));
process.exit(fail ? 1 : 0);
