"""Generate docs/viz/notation.html — the whole-system visualisation:
  · consonants as an IPA-style place×manner grid (IPA · input · native per point)
  · vowels as the triangle (IPA · input · native per chip)
  · modifiers reference
  · a tryout that converts one input across every regime (native, IPA, HU/·lazy, ZH/·lazy, EN)
The language conversions are a faithful JS port of decode.py, embedded and data-driven.
Self-contained; run from repo root.  Validate the JS port with:  node scripts/check_js.mjs
"""
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
from diaphone.decode import load_orth, LAZY_ALIASES, _ZH_RETRO, _TONE_MARKS

NFC = lambda s: unicodedata.normalize("NFC", s)
UNI = lambda s: " ".join("U+%04X" % ord(c) for c in s)

# consonant chart axes (only the used cells are rendered; abbreviations for the column heads)
PLACE = [("bilabial", "bilab"), ("labiodental", "labio"), ("dental", "dent"), ("alveolar", "alv"),
         ("postalveolar", "post"), ("palatal", "pal"), ("velar", "vel"), ("uvular", "uvu"),
         ("pharyngeal", "phar"), ("glottal", "glot")]
MANNER = [("plosive", "plosive"), ("affricate", "affricate"), ("fricative", "fricative"),
          ("nasal", "nasal"), ("trill", "trill"), ("tap", "tap"),
          ("lateral-approximant", "lateral"), ("approximant", "approx")]

# vowel triangle geometry, keyed by IPA (positions carried over from vowel-triangle.html; labels come
# from the live data so a relabel never desyncs). nasal = can carry the French nasal layer.
GEO = {
    "i": (159, 150), "y": (211, 150), "ɯ": (629, 150), "u": (681, 150),
    "ɪ": (226, 262), "ʏ": (278, 262), "ʊ": (614, 262),
    "e": (281, 374), "ø": (333, 374), "ɤ": (527, 374), "o": (579, 374),
    "ə": (430, 436),
    "ɛ": (345, 500), "œ": (397, 500), "ɔ": (520, 500),
    "a": (404, 598), "ɑ": (456, 598),
}
NASAL_IPA = {"ɛ", "œ", "ɔ", "ɑ"}


def build():
    features, languages, all_ph = load(DATA)
    points, *_ = derive(all_ph, features)
    general, _ = apply_merges(points)
    general = attach(general, load_labels(DATA))
    nat = {k: NFC(v) for k, v in native_labels(all_ph, features, DATA).items()}
    ipa = ipa_labels(all_ph, features, DATA)

    cons, ipa2vow = [], {}
    for p in general.values():
        lab = p.get("label")
        if not lab:
            continue
        if p["kind"] == "C":
            _, place, manner, voice = p["base"]
            cons.append({"label": lab, "ipa": p["canonical_ipa"], "native": nat.get(lab, "?"),
                         "place": place, "manner": manner, "voice": voice})
        else:
            ipa2vow[p["canonical_ipa"]] = {"label": lab, "native": nat.get(lab, "?")}

    # triangle chips: geometry (by IPA) + live label/native; category = the vowel operator
    vows = []
    for ip, (x, y) in GEO.items():
        v = ipa2vow.get(ip, {"label": "?", "native": "?"})
        lab = v["label"]
        cat = "base" if len(lab) == 1 else lab[1]
        vows.append({"ipa": ip, "label": lab, "native": v["native"], "x": x, "y": y,
                     "cat": cat, "nasal": 1 if ip in NASAL_IPA else 0})
    nasals = [{"ipa": s, "label": lab, "native": nat.get(lab, "?")}
              for s, lab in [("ɛ̃", "ejh"), ("ɑ̃", "ach"), ("ɔ̃", "ajh"), ("œ̃", "eqh")]]

    mod_examples = [
        ("long (Cː)", "tw", "geminate"), ("long (Vː)", "aw", "acute"),
        ("nasal (Ṽ)", "ejh", "tilde"), ("aspirated", "ph", "dot above"),
        ("labialised", "kc", "diaeresis"), ("pharyngealised", "tqx", "two dots below"),
        ("soft (palatalised)", "pj", "double line below U+0348"), ("rhotic (V˞)", "axr", "hook"),
    ]
    mods = [{"name": nm, "label": lab, "native": nat.get(lab, "?"), "ipa": ipa.get(lab, "?"),
             "gloss": gloss} for nm, lab, gloss in mod_examples]

    keys = sorted(set(nat) | set(ipa), key=len, reverse=True)
    orth = {lg: load_orth(lg, DATA) for lg in ("hu", "zh", "en")}
    return {
        "cons": cons, "place": PLACE, "manner": MANNER,
        "vows": vows, "nasals": nasals, "mods": mods,
        "nat": nat, "ipa": ipa, "keys": keys,
        "orth": orth, "lazy": LAZY_ALIASES, "zhRetro": _ZH_RETRO, "tone": _TONE_MARKS,
        "counts": {"C": len(cons), "V": len(vows), "total": len(cons) + len(vows)},
    }


def main():
    payload = build()
    out = os.path.join(ROOT, "docs", "viz", "notation.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(PAGE.replace("/*DATA*/", json.dumps(payload, ensure_ascii=False)))
    print("wrote", out, "·", payload["counts"], "· keys", len(payload["keys"]))


PAGE = r"""<title>diaphone — the whole system</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{
  --paper:#f5f6f8; --card:#ffffff; --sunken:#eef0f4; --ink:#1a1d24; --muted:#5b6472; --line:#dde1e8;
  --accent:#0e7c86; --vl:#0e7c86; --vd:#b06f14;
  --base-c:#0e7c86; --c-c:#b06f14; --j-c:#3f5bc0; --q-c:#8a4bb0; --x-c:#2f8f66; --n-c:#c0468a;
  --base-t:#0e7c8615; --c-t:#b06f1418; --j-t:#3f5bc016; --q-t:#8a4bb016; --x-t:#2f8f6618; --n-t:#c0468a1a;
  --serif:"Charter","Iowan Old Style","Palatino Linotype",Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  --mono:"SF Mono","JetBrains Mono","Menlo","Consolas",monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#14161b; --card:#1b1e25; --sunken:#101216; --ink:#e9ecf1; --muted:#98a1b0; --line:#2a2e37;
  --accent:#3ec8cf; --vl:#3ec8cf; --vd:#e0a44a;
  --base-c:#3ec8cf; --c-c:#e0a44a; --j-c:#8b9ff0; --q-c:#c08ee0; --x-c:#4fc79a; --n-c:#e88ac0;
  --base-t:#3ec8cf1e; --c-t:#e0a44a22; --j-t:#8b9ff01e; --q-t:#c08ee01e; --x-t:#4fc79a22; --n-t:#e88ac022;
}}
:root[data-theme="dark"]{
  --paper:#14161b; --card:#1b1e25; --sunken:#101216; --ink:#e9ecf1; --muted:#98a1b0; --line:#2a2e37;
  --accent:#3ec8cf; --vl:#3ec8cf; --vd:#e0a44a;
  --base-c:#3ec8cf; --c-c:#e0a44a; --j-c:#8b9ff0; --q-c:#c08ee0; --x-c:#4fc79a; --n-c:#e88ac0;
  --base-t:#3ec8cf1e; --c-t:#e0a44a22; --j-t:#8b9ff01e; --q-t:#c08ee01e; --x-t:#4fc79a22; --n-t:#e88ac022;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.55;
  -webkit-font-smoothing:antialiased;font-size:15px}
.wrap{max-width:1020px;margin:0 auto;padding:clamp(1.4rem,4vw,3rem) clamp(1rem,4vw,2rem) 4rem}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(1.9rem,5vw,2.7rem);letter-spacing:-.01em;margin:0 0 .3rem;text-wrap:balance}
h2{font-family:var(--serif);font-weight:600;font-size:1.35rem;margin:2.4rem 0 .3rem;display:flex;align-items:baseline;gap:.6rem}
h2 .n{font:400 .78rem/1 var(--mono);color:var(--muted)}
.tag{display:inline-block;font:600 .7rem/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.lede{color:var(--muted);max-width:70ch;margin:.2rem 0 0}
.lede code{font-family:var(--mono);color:var(--ink)}
.toggle{border:1px solid var(--line);background:var(--card);color:var(--muted);border-radius:999px;
  padding:.35rem .8rem;font:600 .72rem/1 var(--mono);cursor:pointer}
.toggle:hover{color:var(--ink);border-color:var(--accent)}
.stats{display:flex;flex-wrap:wrap;gap:.4rem;margin:1rem 0 0}
.chip{border:1px solid var(--line);border-radius:.5rem;padding:.3rem .6rem;background:var(--card);font:600 .78rem/1 var(--mono);color:var(--muted)}
.chip b{color:var(--accent)}
/* consonant grid */
.scroll{overflow-x:auto;margin:.7rem 0 0;border:1px solid var(--line);border-radius:14px;background:var(--card)}
table.grid{border-collapse:collapse;width:100%;min-width:760px}
.grid th,.grid td{border:1px solid var(--line);padding:0;text-align:center;vertical-align:top}
.grid thead th{font:600 .66rem/1.1 var(--mono);letter-spacing:.04em;text-transform:uppercase;color:var(--muted);padding:.5rem .3rem;background:var(--sunken)}
.grid tbody th{font:600 .68rem/1.1 var(--mono);color:var(--muted);text-align:left;padding:.5rem .6rem;background:var(--sunken);white-space:nowrap}
.cell{display:flex;gap:2px;justify-content:center;min-height:100%}
.pt{flex:1;padding:.4rem .2rem;display:flex;flex-direction:column;align-items:center;gap:1px}
.pt.vl{background:var(--base-t)} .pt.vd{background:var(--c-t)}
.pt .ipa{font-family:var(--serif);font-size:1.3rem;line-height:1.1}
.pt .lab{font:600 .72rem/1 var(--mono);color:var(--accent)}
.pt .nat{font-family:var(--serif);font-size:1.15rem;color:var(--muted);line-height:1.2}
.klegend{display:flex;flex-wrap:wrap;gap:.5rem 1.3rem;margin:.8rem 0 0;font-size:.85rem;color:var(--muted)}
.klegend .sw{display:inline-block;width:14px;height:14px;border-radius:4px;vertical-align:-2px;margin-right:.3rem}
.klegend b{color:var(--ink)}
/* triangle */
figure{margin:.9rem 0 0;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:.5rem}
svg{width:100%;height:auto;display:block}
.edge{stroke:var(--line);stroke-width:2;fill:none;opacity:.7}
.edgelab{fill:var(--muted);font-family:var(--mono);font-size:13px;letter-spacing:.06em;text-transform:uppercase}
.centre-ring{fill:none;stroke:var(--x-c);stroke-width:1;opacity:.4}
.chip-g .ipa{font-family:var(--serif);font-size:20px;text-anchor:middle;dominant-baseline:middle;fill:var(--ink)}
.chip-g .lab{font-family:var(--mono);font-size:11px;text-anchor:middle;dominant-baseline:middle;font-weight:600}
.chip-g .nat{font-family:var(--serif);font-size:14px;text-anchor:middle;dominant-baseline:middle;fill:var(--muted)}
.chip-g .til{fill:var(--n-c);font-family:var(--serif);font-size:14px;text-anchor:middle}
.cat-base rect{fill:var(--base-t);stroke:var(--base-c)} .cat-base .lab{fill:var(--base-c)}
.cat-c rect{fill:var(--c-t);stroke:var(--c-c)} .cat-c .lab{fill:var(--c-c)}
.cat-j rect{fill:var(--j-t);stroke:var(--j-c)} .cat-j .lab{fill:var(--j-c)}
.cat-q rect{fill:var(--q-t);stroke:var(--q-c)} .cat-q .lab{fill:var(--q-c)}
.cat-x rect{fill:var(--x-t);stroke:var(--x-c);stroke-dasharray:4 3} .cat-x .lab{fill:var(--x-c)}
.chip-g rect{stroke-width:1.6}
.legend{display:flex;flex-wrap:wrap;gap:.5rem 1.3rem;margin:1rem 0 0;font-size:.88rem}
.leg{display:flex;align-items:center;gap:.45rem;color:var(--muted)}
.leg .sw{width:15px;height:15px;border-radius:5px;border:1.6px solid}
.leg code{font-family:var(--mono);color:var(--ink)}
.sw-base{background:var(--base-t);border-color:var(--base-c)} .sw-c{background:var(--c-t);border-color:var(--c-c)}
.sw-j{background:var(--j-t);border-color:var(--j-c)} .sw-q{background:var(--q-t);border-color:var(--q-c)}
.sw-x{background:var(--x-t);border-color:var(--x-c)} .sw-n{background:var(--n-t);border-color:var(--n-c)}
.nasal-row{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.7rem}
.ntile{background:var(--n-t);border:1.6px solid var(--n-c);border-radius:10px;padding:.4rem .7rem;text-align:center;min-width:62px}
.ntile .s{font-family:var(--serif);font-size:1.35rem;color:var(--ink)}
.ntile .l{font-family:var(--mono);font-size:.75rem;color:var(--n-c);font-weight:600;margin-top:.1rem}
.ntile .nat{font-family:var(--serif);font-size:.95rem;color:var(--muted)}
/* modifiers */
.mods{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.5rem;margin:.7rem 0 0}
.mtile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:.6rem .7rem}
.mtile .nm{font:600 .72rem/1.2 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
.mtile .big{display:flex;align-items:baseline;gap:.5rem;margin-top:.35rem}
.mtile .lab{font:600 .95rem/1 var(--mono);color:var(--accent)}
.mtile .ipa{font-family:var(--serif);font-size:1.15rem}
.mtile .nat{font-family:var(--serif);font-size:1.3rem;color:var(--ink)}
.mtile .gl{font-size:.78rem;color:var(--muted);margin-top:.25rem}
/* tryout */
.try{margin:.9rem 0 0;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:1.1rem}
.try label{display:block;font:600 .72rem/1 var(--mono);letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin-bottom:.5rem}
#in{width:100%;border:1px solid var(--line);border-radius:.6rem;background:var(--sunken);color:var(--ink);padding:.7rem .8rem;font:1.1rem var(--mono)}
#in:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:transparent}
.ex{display:flex;flex-wrap:wrap;gap:.4rem;margin:.6rem 0 0}
.ex button{border:1px dashed var(--line);background:transparent;color:var(--accent);border-radius:.5rem;padding:.25rem .55rem;font:.8rem var(--mono);cursor:pointer}
.ex button:hover{border-style:solid}
.out{margin-top:1rem;display:grid;gap:0}
.orow{display:grid;grid-template-columns:6.5rem 1fr;gap:.9rem;align-items:baseline;padding:.55rem .2rem;border-top:1px solid var(--line)}
.orow .k{font:600 .7rem/1.2 var(--mono);letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.orow .k .sub{color:var(--accent);opacity:.85}
.orow .v{font-size:1.5rem;line-height:1.3;word-break:break-word}
.orow.nat .v,.orow.uni .v{font-family:var(--serif)}
.orow.lang .v{font-family:var(--serif)}
.orow .brk{font:.75rem var(--mono);color:var(--muted);margin-left:.6rem}
.note{color:var(--muted);font-size:.85rem;margin:.7rem 0 0;max-width:72ch}
.note code{font-family:var(--mono);color:var(--ink)}
footer{margin-top:2.4rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.78rem;font-family:var(--mono)}
</style>

<div class="wrap">
  <div class="top">
    <div><span class="tag">diaphone</span><h1>The whole system</h1></div>
    <button class="toggle" id="tt" aria-label="toggle theme">theme</button>
  </div>
  <p class="lede">Every cross-linguistic point in three views at once — its <b>IPA</b> value, the ASCII
  <b>input</b> combo you type, and the <b>native</b> Latin+diacritics glyph. Consonants on the articulatory
  grid, vowels on the triangle, then a tryout that converts one input across every regime.</p>
  <div class="stats" id="stats"></div>

  <h2>Consonants <span class="n" id="cN"></span></h2>
  <div class="scroll"><table class="grid"><thead id="cHead"></thead><tbody id="cBody"></tbody></table></div>
  <div class="klegend">
    <span><span class="sw" style="background:var(--base-t);border:1.6px solid var(--base-c)"></span><b>voiceless</b></span>
    <span><span class="sw" style="background:var(--c-t);border:1.6px solid var(--c-c)"></span><b>voiced</b></span>
    <span>each tile — <b>IPA</b> · <code>input</code> · <span style="font-family:var(--serif)">native</span></span>
    <span>off-grid gutturals sit in the pharyngeal/glottal columns (ʔ=<code>hj</code> ħ=<code>hq</code> ʕ=<code>hx</code>)</span>
  </div>

  <h2>Vowels <span class="n" id="vN"></span></h2>
  <figure><svg id="tri" viewBox="0 0 840 700" role="img" aria-label="Vowel triangle"></svg></figure>
  <div class="legend" id="legend"></div>
  <p class="lede" style="margin-top:1rem">Nasalisation is the <code>h</code> modifier on any vowel — orthogonal to
  the triangle. In the 16 languages only <b>French</b> carries it, on these four:</p>
  <div class="nasal-row" id="nasals"></div>

  <h2>Modifiers <span class="n">ride on top — never new points</span></h2>
  <div class="mods" id="mBody"></div>

  <h2>Tryout <span class="n">one input · every regime</span></h2>
  <div class="try">
    <label for="in">type notation — space-separated words · trailing 1–5 = Mandarin tone</label>
    <input id="in" spellcheck="false" value="sjok sewp njawr">
    <div class="ex" id="ex"></div>
    <div class="out" id="out"></div>
    <p class="note"><b>native</b> and <b>IPA</b> are universal (pure code→glyph). <b>HU/ZH/EN</b> decode to that
    language's spelling; <b>·lazy</b> adds typing shortcuts (HU bare <code>a/e</code>; ZH ≈ type Pinyin). English is
    non-phonemic, so it recovers a pronunciation spelling, not the dictionary form.</p>
  </div>

  <footer id="foot"></footer>
</div>

<script type="application/json" id="data">/*DATA*/</script>
<script>
const D=JSON.parse(document.getElementById("data").textContent);
const esc=s=>String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));

/* ---------- universal render (native / IPA), greedy tokenise ---------- */
const TONE={"1":"¹","2":"²","3":"³","4":"⁴","5":"⁵"};
const UKEYS=D.keys;
function utok(w){const t=[];let i=0;while(i<w.length){let m=null;
  for(const k of UKEYS){if(k.length<=w.length-i&&w.substr(i,k.length)===k){m=k;break;}}
  if(m){t.push(m);i+=m.length;}else{t.push(w[i]);i++;}}return t;}
function urend(text,map){return text.trim().split(/\s+/).filter(Boolean).map(w=>{
  let tn="";if(w.length>1&&TONE[w.slice(-1)]){tn=TONE[w.slice(-1)];w=w.slice(0,-1);}
  return utok(w).map(x=>map[x]!==undefined?map[x]:x).join("")+tn;}).join(" ");}
function ubrk(text){return text.trim().split(/\s+/).filter(Boolean).map(w=>{
  if(w.length>1&&TONE[w.slice(-1)])w=w.slice(0,-1);return utok(w).join("·");}).join("  ");}

/* ---------- language decode: faithful port of decode.py ---------- */
const VOWELS=new Set(["a","e","i","o","u"]);
const isV=t=>!!t&&VOWELS.has(t[0]);
function tokenize(word,labels){const labs=[...labels].sort((a,b)=>b.length-a.length);
  const toks=[];let i=0;while(i<word.length){let m=null;
    for(const L of labs){if(word.startsWith(L,i)){m=L;break;}}
    if(m){toks.push(m);i+=m.length;}else{toks.push(word[i]);i++;}}return toks;}
function applyTone(py,tone){if(tone===0||tone===5||tone==null)return py;
  const put=(s,i)=>s.slice(0,i)+D.tone[s[i]][tone-1]+s.slice(i+1);
  if(py.includes("a"))return put(py,py.indexOf("a"));
  if(py.includes("e"))return put(py,py.indexOf("e"));
  if(py.includes("ou"))return put(py,py.indexOf("o"));
  for(let i=py.length-1;i>=0;i--)if(D.tone[py[i]])return put(py,i);return py;}
function decodeWord(word,orth,lang){let tone=null;
  if(lang==="zh"&&word.length>1&&"012345".includes(word.slice(-1))){tone=+word.slice(-1);word=word.slice(0,-1);}
  const toks=tokenize(word,Object.keys(orth));const out=[];
  for(let k=0;k<toks.length;k++){const t=toks[k],nxt=k+1<toks.length?toks[k+1]:null,prv=k?toks[k-1]:null;
    if(t==="w"&&out.length){out[out.length-1]=out[out.length-1][0]+out[out.length-1];continue;}
    let g=orth[t]!==undefined?orth[t]:t;
    if(lang==="hu"&&t==="i"&&isV(nxt)){g="j";}
    else if(lang==="zh"){
      if(D.zhRetro[t]){g=D.zhRetro[t][(nxt==="i"||nxt==="ic")?1:0];}
      else if(t==="ic"&&D.zhRetro[prv]){g="u";}
      else if(t==="i"&&k===0&&isV(nxt)){g="y";}
      else if(t==="u"&&prv==="a"){g="o";}}
    out.push(g);}
  const res=out.join("");return tone!=null?applyTone(res,tone):res;}
function decode(text,lang,lazy){let orth={...D.orth[lang]};
  if(lazy&&D.lazy[lang])orth={...orth,...D.lazy[lang]};
  return text.trim().split(/\s+/).filter(Boolean).map(w=>decodeWord(w,orth,lang)).join(" ");}

window.__engine={urend,decode,natMap:()=>D.nat,ipaMap:()=>D.ipa};  // exposed for node validation

/* ---------- tryout wiring ---------- */
const REGIMES=[
  {k:"native",cls:"nat",fn:v=>urend(v,D.nat),brk:true},
  {k:"IPA",cls:"uni",fn:v=>urend(v,D.ipa)},
  {k:"HU",cls:"lang",fn:v=>decode(v,"hu",false)},
  {k:"HU",sub:"lazy",cls:"lang",fn:v=>decode(v,"hu",true)},
  {k:"ZH",cls:"lang",fn:v=>decode(v,"zh",false)},
  {k:"ZH",sub:"lazy",cls:"lang",fn:v=>decode(v,"zh",true)},
  {k:"EN",cls:"lang",fn:v=>decode(v,"en",false)},
];
function run(){const v=document.getElementById("in").value;
  document.getElementById("out").innerHTML=REGIMES.map(r=>{
    let val="";try{val=r.fn(v);}catch(e){val="—";}
    const b=r.brk?`<span class="brk">${esc(ubrk(v))}</span>`:"";
    const sub=r.sub?` <span class="sub">·${esc(r.sub)}</span>`:"";
    return `<div class="orow ${r.cls}"><span class="k">${esc(r.k)}${sub}</span><span class="v">${esc(val)}${b}</span></div>`;
  }).join("");}

/* ---------- consonant grid ---------- */
(function(){
  const byCell={};for(const c of D.cons){(byCell[c.manner+"|"+c.place]=byCell[c.manner+"|"+c.place]||[]).push(c);}
  const head="<tr><th></th>"+D.place.map(([,ab])=>`<th>${esc(ab)}</th>`).join("")+"</tr>";
  document.getElementById("cHead").innerHTML=head;
  const rows=D.manner.filter(([m])=>D.cons.some(c=>c.manner===m)).map(([m,ml])=>{
    const tds=D.place.map(([pl])=>{const pts=(byCell[m+"|"+pl]||[]).sort((a,b)=>a.voice.localeCompare(b.voice));
      if(!pts.length)return "<td></td>";
      const tiles=pts.map(p=>`<div class="pt ${p.voice==="vl"?"vl":"vd"}"><span class="ipa">${esc(p.ipa)}</span><span class="lab">${esc(p.label)}</span><span class="nat">${esc(p.native)}</span></div>`).join("");
      return `<td><div class="cell">${tiles}</div></td>`;}).join("");
    return `<tr><th>${esc(ml)}</th>${tds}</tr>`;});
  document.getElementById("cBody").innerHTML=rows.join("");
})();

/* ---------- vowel triangle ---------- */
(function(){
  const NS="http://www.w3.org/2000/svg";
  const el=(n,at)=>{const e=document.createElementNS(NS,n);for(const k in at)e.setAttribute(k,at[k]);return e;};
  const svg=document.getElementById("tri");
  const I=[150,155],U=[690,155],A=[430,618];
  svg.appendChild(el("path",{class:"edge",d:`M${I[0]},${I[1]} L${U[0]},${U[1]} L${A[0]},${A[1]} Z`}));
  svg.appendChild(el("circle",{class:"centre-ring",cx:430,cy:436,r:42}));
  const lab=(x,y,text,rot,sz)=>{const t=el("text",{class:"edgelab",x,y,"text-anchor":"middle",transform:`rotate(${rot} ${x} ${y})`});if(sz)t.setAttribute("font-size",sz);t.textContent=text;svg.appendChild(t);};
  lab(420,132,"close",0);lab(240,400,"front · unrounded",52);lab(620,400,"back · rounded",-52);lab(430,652,"open",0);lab(430,398,"centre",0,11);
  for(const v of D.vows){const g=el("g",{class:"chip-g cat-"+v.cat});
    g.appendChild(el("rect",{x:v.x-27,y:v.y-30,width:54,height:60,rx:11}));
    const ip=el("text",{class:"ipa",x:v.x,y:v.y-13});ip.textContent=v.ipa;g.appendChild(ip);
    const lb=el("text",{class:"lab",x:v.x,y:v.y+3});lb.textContent=v.label;g.appendChild(lb);
    const nt=el("text",{class:"nat",x:v.x,y:v.y+19});nt.textContent=v.native;g.appendChild(nt);
    if(v.nasal){const t=el("text",{class:"til",x:v.x+20,y:v.y-17});t.textContent="˜";g.appendChild(t);}
    svg.appendChild(g);}
  const LEG=[["base","base","i e a o u"],["c","c","toggle rounding"],["j","j","step to in-between"],
             ["q","q","c + j (front-round)"],["x","x","centralise → ə"],["n","˜","nasal (+h)"]];
  document.getElementById("legend").innerHTML=LEG.map(([cls,code,desc])=>
    `<div class="leg"><span class="sw sw-${cls}"></span><code>${esc(code)}</code> <span>${esc(desc)}</span></div>`).join("");
  document.getElementById("nasals").innerHTML=D.nasals.map(n=>
    `<div class="ntile"><div class="s">${esc(n.ipa)}</div><div class="l">${esc(n.label)}</div><div class="nat">${esc(n.native)}</div></div>`).join("");
})();

/* ---------- modifiers ---------- */
document.getElementById("mBody").innerHTML=D.mods.map(m=>
  `<div class="mtile"><div class="nm">${esc(m.name)}</div><div class="big"><span class="lab">${esc(m.label)}</span><span class="ipa">${esc(m.ipa)}</span><span class="nat">${esc(m.native)}</span></div><div class="gl">${esc(m.gloss)}</div></div>`).join("");

/* ---------- stats, examples, theme ---------- */
document.getElementById("cN").textContent=D.counts.C+" points";
document.getElementById("vN").textContent=D.counts.V+" points";
document.getElementById("stats").innerHTML=
  `<span class="chip"><b>${D.counts.total}</b> points</span><span class="chip"><b>${D.counts.C}</b> consonants</span>`+
  `<span class="chip"><b>${D.counts.V}</b> vowels</span><span class="chip"><b>7</b> modifiers</span><span class="chip"><b>16</b> languages</span>`;
document.getElementById("foot").textContent="diaphone · "+D.counts.total+" general points · IPA · input · native · one input across every regime";
const EX=["sjok sewp njawr","pjatj","kxaxn3 kau1","tqix1 sjuc4","kecsecnecm","raxn2","sjj zjj kc gc"];
document.getElementById("ex").innerHTML=EX.map(e=>`<button>${esc(e)}</button>`).join("");
document.getElementById("ex").addEventListener("click",e=>{if(e.target.tagName==="BUTTON"){document.getElementById("in").value=e.target.textContent;run();}});
document.getElementById("in").addEventListener("input",run);
const tt=document.getElementById("tt");
tt.addEventListener("click",()=>{const r=document.documentElement,c=r.getAttribute("data-theme");
  r.setAttribute("data-theme",c==="dark"?"light":c==="light"?"":"dark");tt.textContent=r.getAttribute("data-theme")||"theme";});
run();
</script>
"""


if __name__ == "__main__":
    main()
