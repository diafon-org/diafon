"""Generate docs/viz/notation.html — the summary page (consonants, vowels: code · IPA · native · U+)
plus a live tryout (native + IPA, done in-browser). Self-contained; run from repo root."""
import json
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
DATA = os.path.join(ROOT, "data")

from diaphone.loader import load
from diaphone.derive import derive
from diaphone.merges import apply_merges
from diaphone.labeler import load_labels, attach
from diaphone.render import ipa_labels
from diaphone.native import native_labels


def codepoints(s):
    return " ".join("U+%04X" % ord(c) for c in s)


def name_of(s):
    return " + ".join(unicodedata.name(c, "?") for c in s)


PAGE = r"""<title>diaphone — notation</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{
  --paper:#f6f4ee; --card:#fdfcf8; --ink:#211f1b; --muted:#736c62; --line:#e3ddd0;
  --accent:#3d5a8a; --vtint:#8a5a2b; --code:#2f2b25; --code-bg:#ece7db; --shadow:0 1px 2px rgba(40,34,24,.06),0 8px 24px rgba(40,34,24,.05);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#161512; --card:#1e1c18; --ink:#ece6da; --muted:#9a9184; --line:#302c25;
  --accent:#8fb0e6; --vtint:#e0a86a; --code:#e7e0d2; --code-bg:#26241f; --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}}
:root[data-theme="dark"]{
  --paper:#161512; --card:#1e1c18; --ink:#ece6da; --muted:#9a9184; --line:#302c25;
  --accent:#8fb0e6; --vtint:#e0a86a; --code:#e7e0d2; --code-bg:#26241f; --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrap{max-width:62rem;margin:0 auto;padding:clamp(1.2rem,4vw,3rem) clamp(1rem,4vw,2rem) 5rem;}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;}
.serif{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Times New Roman",serif;}
h1{font-family:"Iowan Old Style",Palatino,Georgia,serif;font-weight:600;font-size:clamp(1.9rem,5vw,2.7rem);
  letter-spacing:-.01em;margin:.2em 0 .1em;text-wrap:balance;}
h2{font-family:"Iowan Old Style",Palatino,Georgia,serif;font-weight:600;font-size:1.5rem;margin:2.6rem 0 .3rem;
  display:flex;align-items:baseline;gap:.6rem;}
h2 .n{font:400 .8rem/1 ui-monospace,Menlo,monospace;color:var(--muted);}
.lede{color:var(--muted);font-size:1.06rem;max-width:44rem;margin:.2rem 0 0;}
.tag{display:inline-block;font:600 .72rem/1 ui-monospace,Menlo,monospace;letter-spacing:.04em;
  text-transform:uppercase;color:var(--accent);}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;}
.toggle{border:1px solid var(--line);background:var(--card);color:var(--muted);border-radius:999px;
  padding:.35rem .8rem;font:600 .72rem/1 ui-monospace,Menlo,monospace;cursor:pointer;letter-spacing:.03em;}
.toggle:hover{color:var(--ink);border-color:var(--accent);}
.stats{display:flex;flex-wrap:wrap;gap:.4rem;margin:1rem 0 0;}
.chip{border:1px solid var(--line);border-radius:.5rem;padding:.3rem .6rem;background:var(--card);
  font:600 .78rem/1 ui-monospace,Menlo,monospace;color:var(--muted);}
.chip b{color:var(--ink);}
/* tryout */
.try{margin:1.6rem 0 0;background:var(--card);border:1px solid var(--line);border-radius:1rem;
  padding:1.1rem 1.1rem 1.2rem;box-shadow:var(--shadow);}
.try label{display:block;font:600 .72rem/1 ui-monospace,Menlo,monospace;letter-spacing:.05em;
  text-transform:uppercase;color:var(--muted);margin-bottom:.5rem;}
#in{width:100%;border:1px solid var(--line);border-radius:.6rem;background:var(--paper);color:var(--ink);
  padding:.7rem .8rem;font:1.05rem ui-monospace,Menlo,monospace;}
#in:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:transparent;}
.ex{display:flex;flex-wrap:wrap;gap:.4rem;margin:.6rem 0 0;}
.ex button{border:1px dashed var(--line);background:transparent;color:var(--accent);border-radius:.5rem;
  padding:.25rem .55rem;font:.8rem ui-monospace,Menlo,monospace;cursor:pointer;}
.ex button:hover{border-style:solid;}
.out{display:grid;grid-template-columns:1fr;gap:.7rem;margin-top:1rem;}
.orow{display:flex;align-items:baseline;gap:.9rem;flex-wrap:wrap;padding:.6rem .2rem;border-top:1px solid var(--line);}
.orow .k{font:600 .72rem/1 ui-monospace,Menlo,monospace;letter-spacing:.05em;text-transform:uppercase;
  color:var(--muted);min-width:4.5rem;}
.orow .v{font-size:1.7rem;line-height:1.35;}
.orow.native .v{font-family:"Iowan Old Style",Palatino,Georgia,serif;}
.orow .brk{color:var(--muted);font:.78rem ui-monospace,Menlo,monospace;}
/* tables */
.scroll{overflow-x:auto;margin:.7rem 0 0;border:1px solid var(--line);border-radius:.9rem;background:var(--card);}
table{border-collapse:collapse;width:100%;font-size:.92rem;}
th,td{text-align:left;padding:.5rem .8rem;border-bottom:1px solid var(--line);white-space:nowrap;}
thead th{position:sticky;top:0;background:var(--card);z-index:1;font:600 .68rem/1.2 ui-monospace,Menlo,monospace;
  letter-spacing:.06em;text-transform:uppercase;color:var(--muted);}
tbody tr:last-child td{border-bottom:none;}
tbody tr:hover{background:color-mix(in srgb,var(--accent) 7%,transparent);}
td.code{font-family:ui-monospace,Menlo,monospace;color:var(--accent);font-weight:600;}
td.ipa{font-family:"Iowan Old Style",Palatino,Georgia,serif;color:var(--ink);}
td.glyph{font-family:"Iowan Old Style",Palatino,Georgia,serif;font-size:1.5rem;padding-left:1rem;padding-right:1rem;}
td.uni{font-family:ui-monospace,Menlo,monospace;font-size:.78rem;color:var(--muted);}
td.desc{color:var(--muted);font-size:.85rem;white-space:normal;}
.V td.code{color:var(--vtint);}
.note{color:var(--muted);font-size:.9rem;margin:.6rem 0 0;max-width:44rem;}
a{color:var(--accent);}
</style>

<div class="wrap">
  <div class="top">
    <div>
      <span class="tag">diaphone · native view</span>
      <h1>Notation &amp; the native look</h1>
    </div>
    <button class="toggle" id="tt" aria-label="toggle theme">theme</button>
  </div>
  <p class="lede">One ASCII <b>code</b> per cross-linguistic point, one <b>IPA</b> value, and one
  <b>native</b> glyph (Latin&nbsp;+&nbsp;diacritics, existing Unicode codepoints — a bespoke font later).
  Type a code below to see it render.</p>
  <div class="stats" id="stats"></div>

  <div class="try">
    <label for="in">tryout — type notation (space-separated; trailing 1–5 = tone)</label>
    <input id="in" class="mono" spellcheck="false" value="sjok sewp njawr">
    <div class="ex" id="ex"></div>
    <div class="out">
      <div class="orow native"><span class="k">native</span><span class="v" id="oNat"></span><span class="brk" id="bNat"></span></div>
      <div class="orow"><span class="k">IPA</span><span class="v serif" id="oIpa"></span><span class="brk" id="bIpa"></span></div>
    </div>
    <p class="note">Native and IPA are <i>universal</i> targets (pure code→glyph). Language spellings
    (Hungarian, Mandarin…) are algorithmic — use <span class="mono">diaphone render hu/zh …</span>.</p>
  </div>

  <h2>Consonants <span class="n" id="cN"></span></h2>
  <div class="scroll"><table><thead><tr>
    <th>Code</th><th>IPA</th><th>Native</th><th>Unicode</th><th>Place · manner · voice</th><th>Langs</th>
  </tr></thead><tbody id="cBody"></tbody></table></div>

  <h2>Vowels <span class="n" id="vN"></span></h2>
  <div class="scroll"><table><thead><tr>
    <th>Code</th><th>IPA</th><th>Native</th><th>Unicode</th><th>Height · backness · round</th><th>Langs</th>
  </tr></thead><tbody id="vBody"></tbody></table></div>

  <h2>Modifiers <span class="n">ride on top</span></h2>
  <div class="scroll"><table><thead><tr>
    <th>Modifier</th><th>Example code</th><th>IPA</th><th>Native</th><th>Unicode</th><th>Mark</th>
  </tr></thead><tbody id="mBody"></tbody></table></div>
  <p class="note">Combining marks render differently across system fonts — the double-vertical-line-below
  (<span class="mono">U+0348</span>, soft consonants) and stacked below-dots are exactly what the bespoke
  font will regularise.</p>
</div>

<script type="application/json" id="data">/*DATA*/</script>
<script>
const D=JSON.parse(document.getElementById("data").textContent);
const TONE={"1":"¹","2":"²","3":"³","4":"⁴","5":"⁵"};
const KEYS=D.keys;
function tok(w){const t=[];let i=0;while(i<w.length){let m=null;
  for(const k of KEYS){if(k.length<=w.length-i&&w.substr(i,k.length)===k){m=k;break;}}
  if(m){t.push(m);i+=m.length;}else{t.push(w[i]);i++;}}return t;}
function rend(text,map){return text.trim().split(/\s+/).filter(Boolean).map(w=>{
  let tn="";if(w.length>1&&TONE[w.slice(-1)]){tn=TONE[w.slice(-1)];w=w.slice(0,-1);}
  return tok(w).map(x=>map[x]!==undefined?map[x]:x).join("")+tn;}).join(" ");}
function brk(text){return text.trim().split(/\s+/).filter(Boolean).map(w=>{
  if(w.length>1&&TONE[w.slice(-1)])w=w.slice(0,-1);return tok(w).join("·");}).join("  ");}
function run(){const v=document.getElementById("in").value;
  document.getElementById("oNat").textContent=rend(v,D.nat);
  document.getElementById("oIpa").textContent=rend(v,D.ipa);
  document.getElementById("bNat").textContent=brk(v);
  document.getElementById("bIpa").textContent="";}
const esc=s=>s.replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
function rows(arr,vowel){return arr.map(r=>`<tr class="${vowel?'V':'C'}">
  <td class="code">${esc(r.label)}</td><td class="ipa">${esc(r.ipa)}</td>
  <td class="glyph">${esc(r.native)}</td><td class="uni">${esc(r.uni)}</td>
  <td class="desc">${esc(r.a)} · ${esc(r.b)} · ${esc(r.c)}</td><td class="uni">${r.langs}</td></tr>`).join("");}
document.getElementById("cBody").innerHTML=rows(D.cons,false);
document.getElementById("vBody").innerHTML=rows(D.vows,true);
document.getElementById("mBody").innerHTML=D.mods.map(m=>`<tr>
  <td class="desc" style="color:var(--ink)">${esc(m.name)}</td><td class="code">${esc(m.label)}</td>
  <td class="ipa">${esc(m.ipa)}</td><td class="glyph">${esc(m.native)}</td>
  <td class="uni">${esc(m.uni)}</td><td class="desc">${esc(m.gloss)}</td></tr>`).join("");
document.getElementById("cN").textContent=D.counts.C+" points";
document.getElementById("vN").textContent=D.counts.V+" points";
document.getElementById("stats").innerHTML=
  `<span class="chip"><b>${D.counts.total}</b> general points</span>`+
  `<span class="chip"><b>${D.counts.C}</b> consonants</span>`+
  `<span class="chip"><b>${D.counts.V}</b> vowels</span>`+
  `<span class="chip"><b>7</b> modifiers</span>`+
  `<span class="chip"><b>16</b> languages</span>`;
const EX=["sjok sewp njawr","pjatj","sjj zjj","kc gc","tqx dqx","ph th kh","raxn2","kxaxn3 kau1"];
document.getElementById("ex").innerHTML=EX.map(e=>`<button>${esc(e)}</button>`).join("");
document.getElementById("ex").addEventListener("click",e=>{
  if(e.target.tagName==="BUTTON"){document.getElementById("in").value=e.target.textContent;run();}});
document.getElementById("in").addEventListener("input",run);
// theme toggle: cycle system -> light -> dark
const tt=document.getElementById("tt");
tt.addEventListener("click",()=>{const r=document.documentElement;const c=r.getAttribute("data-theme");
  r.setAttribute("data-theme",c==="dark"?"light":c==="light"?"":"dark");
  tt.textContent=r.getAttribute("data-theme")||"theme";});
run();
</script>
"""


def main():
    features, languages, all_ph = load(DATA)
    points, *_ = derive(all_ph, features)
    general, _ = apply_merges(points)
    general = attach(general, load_labels(DATA))
    nat = native_labels(all_ph, features, DATA)
    ipa = ipa_labels(all_ph, features, DATA)

    cons, vows = [], []
    for k, p in general.items():
        lab = p.get("label")
        if not lab:
            continue
        g = unicodedata.normalize("NFC", nat.get(lab, "?"))
        _, x, y, z = p["base"]        # C: (place, manner, voice) · V: (height, backness, round)
        row = {
            "label": lab,
            "ipa": p["canonical_ipa"],
            "native": g,
            "uni": codepoints(g),
            "langs": len(p["languages"]),
        }
        if p["kind"] == "C":
            row["a"], row["b"], row["c"] = x, y, z
            cons.append(row)
        else:
            row["a"], row["b"] = x, y
            row["c"] = "round" if z else "unround"
            vows.append(row)

    order_c = ["p", "b", "t", "d", "k", "g"]
    cons.sort(key=lambda r: (r["label"] not in order_c, r["label"]))
    vows.sort(key=lambda r: r["label"])

    # modifier showcase — (name, example label, gloss)
    mod_examples = [
        ("long", "tw", "geminate / long"),
        ("long (vowel)", "aw", "á"),
        ("nasal (vowel)", "ejh", "tilde — French ɛ̃"),
        ("aspirated", "ph", "one dot above"),
        ("labialised", "kc", "diaeresis"),
        ("pharyngealised", "tqx", "two dots below"),
        ("palatalised / soft", "pj", "U+0348 double vertical line below"),
        ("palatalised s", "sjj", "on s/z"),
        ("rhotic (vowel)", "axr", "ɚ"),
    ]
    mods = []
    for nm, lab, gloss in mod_examples:
        g = unicodedata.normalize("NFC", nat.get(lab, "?"))
        mods.append({"name": nm, "label": lab, "native": g, "uni": codepoints(g),
                     "ipa": ipa.get(lab, "?"), "gloss": gloss})

    # full maps + greedy token order for the in-browser tryout
    keys = sorted(set(nat) | set(ipa), key=len, reverse=True)
    payload = {
        "cons": cons, "vows": vows, "mods": mods,
        "nat": {k: unicodedata.normalize("NFC", v) for k, v in nat.items()},
        "ipa": ipa, "keys": keys,
        "counts": {"C": len(cons), "V": len(vows), "total": len(cons) + len(vows)},
    }
    out = os.path.join(ROOT, "docs", "viz", "notation.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(PAGE.replace("/*DATA*/", json.dumps(payload, ensure_ascii=False)))
    print("wrote", out, "·", payload["counts"])


if __name__ == "__main__":
    main()
