"""Generate docs/viz/notation.html — the whole-system visualisation:
  · consonants as an IPA-style place×manner grid (IPA · input · native per point; voiceless first)
  · vowels as the triangle (IPA · input · native per chip)
  · modifiers reference
  · a language-specific tryout: pick a target (native, IPA, HU, ZH, EN), toggle lazy, read
    per-language help below — the conversions are a faithful JS port of decode.py.
A subset of Charis SIL (SIL OFL, see fonts/OFL.txt) is embedded so the combining marks align.
Self-contained; run from repo root.  Validate the JS port with:  node scripts/check_js.mjs
"""
import base64
import json
import os
import sys
import unicodedata
from io import BytesIO

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
DATA = os.path.join(ROOT, "data")
FONT_TTF = os.path.join(ROOT, "fonts", "CharisSIL-Regular.ttf")

from diaphone.loader import load
from diaphone.derive import derive
from diaphone.merges import apply_merges
from diaphone.labeler import load_labels, attach
from diaphone.render import ipa_labels
from diaphone.native import native_labels
from diaphone.decode import load_orth, en_dict, LAZY_ALIASES, EN_CANON, _ZH_RETRO, _TONE_MARKS

NFC = lambda s: unicodedata.normalize("NFC", s)

PLACE = [("bilabial", "bilab"), ("labiodental", "labio"), ("dental", "dent"), ("alveolar", "alv"),
         ("postalveolar", "post"), ("palatal", "pal"), ("velar", "vel"), ("uvular", "uvu"),
         ("pharyngeal", "phar"), ("glottal", "glot")]
MANNER = [("plosive", "plosive"), ("affricate", "affricate"), ("fricative", "fricative"),
          ("nasal", "nasal"), ("trill", "trill"), ("tap", "tap"),
          ("lateral-approximant", "lateral"), ("approximant", "approx")]
GEO = {"i": (159, 150), "y": (211, 150), "ɯ": (629, 150), "u": (681, 150),
       "ɪ": (226, 262), "ʏ": (278, 262), "ʊ": (614, 262),
       "e": (281, 374), "ø": (333, 374), "ɤ": (527, 374), "o": (579, 374), "ə": (430, 436),
       "ɛ": (345, 500), "œ": (397, 500), "ɔ": (520, 500), "a": (404, 598), "ɑ": (456, 598)}
NASAL_IPA = {"ɛ", "œ", "ɔ", "ɑ"}

# language-specific tryout help (notes + example inputs; outputs are rendered live in the page)
HELP = {
    "native": {"name": "native",
               "note": "The universal view — one glyph per point, Latin plus diacritics. One line below = "
                       "palatal (t̩ s̩); two lines = soft (p͈). Dot above = aspirated (ṗ); dot below = "
                       "a fricativised consonant (ṭ ḳ) or a lowered vowel (ẹ ọ). Diaeresis flips a vowel "
                       "front↔back (ü ö · ï ë ä). Tilde = nasal (ã).",
               "ex": [["sjok sewp njawr", "sok szép nyár"], ["pjatj", "Russian пять"],
                      ["ty dy sy zy", "the Arabic emphatics"],
                      ["ejdj kisj kutjac aclsik acz acstacl aclactt", "a whole sentence (HU)"]]},
    "ipa": {"name": "IPA",
            "note": "The IPA value of each code, for reference. Modifiers appear as the standard "
                    "diacritics; a trailing digit becomes a tone superscript.",
            "ex": [["sjan1 kxaxn3 kau1", "shān hěn gāo"], ["pjatj njawrw", "soft + long"],
                   ["ojw", "a long lowered o"], ["ejdj kisj kutjac aclsik acz acstacl aclactt", "a whole sentence"]]},
    "hu": {"name": "HU",
           "note": "Hungarian, in both forms: its native view (á/a — the dark a reads as plain a here, since "
                   "Hungarian has no other short a; the universal view keeps ä) and the spelling, which is "
                   "near-phonemic and round-trips exactly (`w` doubles the previous letter, sz → ssz). "
                   "Loose input frees the bare letters a and e for the Hungarian short a and e.",
           "ex": [["sjok sewp njawr", "sok szép nyár"], ["kecsecnecm sewpejn", "köszönöm szépen"],
                  ["aclmac", "alma"], ["hoswuw", "hosszú"],
                  ["ejdj kisj kutjac aclsik acz acstacl aclactt", "egy kis kutya alszik az asztal alatt"]]},
    "zh": {"name": "ZH",
           "note": "Mandarin, in both forms: its native view (its r shows the retroflex underdot, ṛ — Mandarin "
                   "has no tapped r, so it stays unambiguous) and Pinyin. End a syllable with 1–4 for its tone "
                   "(5 or none = neutral); before a front vowel the hush series is spelled j/q/x, otherwise "
                   "zh/ch/sh. Loose input lets you type Pinyin directly (xiao, shi, zhong).",
           "ex": [["sjan1 kxaxn3 kau1", "shān hěn gāo"], ["nic3", "nǚ"], ["raxn2", "rén"],
                  ["tqi1 sji1 tquc1 sjuc4", "jī xī zhī shì"],
                  ["tqonx1 kuo2 tqha2 kxaxn3 kxau3", "zhōng guó chá hěn hǎo"]]},
    "en": {"name": "EN",
           "note": "English, in both forms: the native view and a spelling. Loose input adds the familiar "
                   "digraphs — sh ch zh ng th dh and bare j y w (all free letters in English) — so you can "
                   "type shijp for ship. The dictionary switch looks each word up (28k words, frequency-"
                   "ranked) and writes the real spelling; unknown words fall back to the respelling, and "
                   "either spelling of a word (shijp/sjijp) finds it.",
           "ex": [["shij sejlz fijsh", "she sells fish"], ["baqd", "bird"], ["haxlo waqld", "hello world"],
                  ["dxax kat sijts acn dxax mat", "the cat sits on the mat"]]},
}


# The seven operators — one mechanism, all base-dependent. Four (c j q x) can form new points; any of
# them reads as a modifier where base+letter isn't a point. Examples carry LABELS; the native glyph for
# each is computed in build(), so the table can never drift from the engine.
OPS_SPEC = [
    ("c", None, "affricate; on k/g (no affricate) rounded; on h: pharyngeal (deeper)",
     ["tc", "dc", "kc", "hc"],
     "flip front↔back, keeping rounding (at the open apex: mark back)",
     ["ic", "ec", "uc", "oc", "ac"]),
    ("j", None, "palatal; where no palatal point exists: soft; on h: the glottal stop",
     ["sj", "tj", "nj", "pj", "hj"],
     "lower one step",
     ["ij", "ej", "uj", "oj"]),
    ("q", "= c + j", "hush affricate; on h: the voiced pharyngeal (deeper + marked)",
     ["tq", "dq", "hq"],
     "c + j (rounded + lowered); on the schwa: the r-coloured vowel",
     ["iq", "eq", "aq"]),
    ("x", None, "the fricative one step back — dental on t/d, velar on k/g",
     ["tx", "dx", "kx", "gx"],
     "centralise → the schwa",
     ["ax"]),
    ("w", None, "long (a doubled letter)", ["tw", "sw"], "long", ["aw", "iw"]),
    ("h", None, "aspirated", ["ph", "th", "kh"], "— (unused; h is also a base sound)", []),
    ("y", None, "emphatic (throat-darkened) — see the glossary", ["ty", "dy", "sy", "zy"],
     "nasal", ["ay", "ey", "oy"]),
]
# the modifier features that ride on top of a finished point (labels; glyphs computed in build())
MODS_SPEC = [
    ("long", "w", "holds the sound longer; a consonant doubles", ["tw", "aw"]),
    ("nasal", "y on a vowel", "air also flows through the nose", ["ay", "oy"]),
    ("aspirated", "h on a consonant", "a puff of breath after the release", ["ph", "kh"]),
    ("soft (palatalised)", "j — but jj on s/z", "a secondary raise toward the palate; Russian's soft series", ["pj", "sjj"]),
    ("rounded (labialised)", "c on k/g", "lip rounding on the consonant", ["kc", "gc"]),
    ("emphatic (pharyngealised)", "y on a consonant", "a secondary squeeze deep in the throat; Arabic", ["ty", "sy"]),
    ("r-coloured (rhotic)", "q on the schwa", "the tongue holds an r-shape through the vowel; written aq", ["aq"]),
]
# what the features actually are, in plain words. Examples: (label, real word) — glyphs computed.
GLOSS_SPEC = [
    ("affricate", "A stop released straight into a fricative at the same place — t then s, fused into one sound.",
     [("tc", "cats"), ("tq", "church")]),
    ("palatal", "The tongue body humps up against the hard palate, the roof of the mouth.",
     [("nj", "Spanish niño"), ("tj", "Hungarian tyúk")]),
    ("hush", "The hushing s-sounds, made a little further back with a domed tongue.",
     [("sj", "ship"), ("zj", "measure")]),
    ("dental · velar", "The x operator picks the fricative one step back from its base: at the teeth on t/d, at the soft palate on k/g.",
     [("tx", "thin"), ("dx", "this"), ("kx", "Scottish loch")]),
    ("pharyngeal", "Made deep in the throat by pulling the tongue root toward the back wall — Arabic ح and ع.",
     [("hc", "Muḥammad"), ("hq", "ʿarab")]),
    ("emphatic", "A normal consonant plus a second, deep-throat squeeze: the tongue root pulls back and the whole syllable darkens. This alone separates Arabic صاد from س — صار 'became' vs سار 'walked'.",
     [("ty", "Arabic ط"), ("sy", "Arabic ص")]),
    ("aspirated", "A puff of breath right after a stop's release — hold a hand to your mouth on English pin.",
     [("ph", "pin"), ("kh", "kin")]),
    ("nasal", "The soft palate lowers, so air flows through the nose as well as the mouth.",
     [("ay", "French banc"), ("oy", "bon")]),
    ("r-coloured", "The tongue bunches or curls as for an r, right through the vowel — a vocalic r.",
     [("aq", "American bird = bṙd")]),
    ("rounded", "Lip rounding on top of a consonant.",
     [("kc", "Latin quis")]),
    ("soft", "A secondary raise of the tongue toward the palate on a normal consonant — Russian's soft series.",
     [("pj", "Russian пять"), ("sjj", "Russian ось")]),
    ("long", "The sound is held longer; a long consonant is written doubled.",
     [("aw", "Hungarian ház"), ("tw", "Italian fatto")]),
]


def wiki_url(kind, a, b, c):
    """Wikipedia article for a point, derived from its features (redirects cover naming variants)."""
    if kind == "C":
        place, manner, voice = a, b, c
        manner = {"lateral-approximant": "lateral approximant", "tap": "tap and flap"}.get(manner, manner)
        name = f"{place} {manner}" if manner == "nasal" else \
            f"{'Voiceless' if voice == 'vl' else 'Voiced'} {place} {manner}"
    else:
        hi, bk, rd = a, b, c
        name = "Mid central vowel" if (hi, bk) == ("mid", "central") else \
            f"{hi} {bk} {'rounded' if rd else 'unrounded'} vowel"
    return "https://en.wikipedia.org/wiki/" + (name[0].upper() + name[1:]).replace(" ", "_")


def build():
    features, languages, all_ph = load(DATA)
    points, *_ = derive(all_ph, features)
    general, _ = apply_merges(points)
    general = attach(general, load_labels(DATA))
    nat = {k: NFC(v) for k, v in native_labels(all_ph, features, DATA).items()}
    nat_hu = {k: NFC(v) for k, v in native_labels(all_ph, features, DATA, lang="hu").items()}
    nat_zh = {k: NFC(v) for k, v in native_labels(all_ph, features, DATA, lang="zh").items()}
    ipa = ipa_labels(all_ph, features, DATA)

    cons, ipa2vow = [], {}
    for p in general.values():
        lab = p.get("label")
        if not lab:
            continue
        if p["kind"] == "C":
            _, place, manner, voice = p["base"]
            cons.append({"label": lab, "ipa": p["canonical_ipa"], "native": nat.get(lab, "?"),
                         "place": place, "manner": manner, "voice": voice,
                         "wiki": wiki_url("C", place, manner, voice)})
        else:
            _, hi, bk, rd = p["base"]
            ipa2vow[p["canonical_ipa"]] = {"label": lab, "native": nat.get(lab, "?"),
                                           "wiki": wiki_url("V", hi, bk, rd)}

    vows = []
    for ip, (x, y) in GEO.items():
        v = ipa2vow.get(ip, {"label": "?", "native": "?", "wiki": ""})
        lab = v["label"]
        vows.append({"ipa": ip, "label": lab, "native": v["native"], "x": x, "y": y, "wiki": v["wiki"],
                     "cat": "base" if len(lab) == 1 else lab[1], "nasal": 1 if ip in NASAL_IPA else 0})
    nasals = [{"ipa": s, "label": lab, "native": nat.get(lab, "?")}
              for s, lab in [("ẽ", "ey"), ("ã", "ay"), ("õ", "oy")]]

    mod_examples = [("long (Cː)", "tw", "geminate"), ("long (Vː)", "aw", "acute"),
                    ("nasal (Ṽ)", "ay", "tilde (`y` operator)"), ("aspirated", "ph", "dot above"),
                    ("labialised", "kc", "diaeresis"), ("pharyngealised", "ty", "two dots below"),
                    ("soft (palatalised)", "pj", "double line below"), ("rhotic (V˞)", "aq", "vocalic r — dot above")]
    mods = [{"name": nm, "label": lab, "native": nat.get(lab, "?"), "ipa": ipa.get(lab, "?"), "gloss": gl}
            for nm, lab, gl in mod_examples]

    # spec tables → payload rows with computed native glyphs (never drift from the engine)
    pair = lambda lab: {"lab": lab, "nat": nat.get(lab, "?")}
    ops = [{"op": op, "note": note, "cons": cdesc, "cons_ex": [pair(l) for l in cl],
            "vowel": vdesc, "vowel_ex": [pair(l) for l in vl]}
           for op, note, cdesc, cl, vdesc, vl in OPS_SPEC]
    mods_ref = [{"name": nm, "char": ch, "desc": d, "ex": [pair(l) for l in ls]}
                for nm, ch, d, ls in MODS_SPEC]
    gloss = [{"title": t, "text": tx, "ex": [{**pair(l), "word": w} for l, w in ls]}
             for t, tx, ls in GLOSS_SPEC]

    keys = sorted(set(nat) | set(ipa), key=len, reverse=True)
    orth = {lg: load_orth(lg, DATA) for lg in ("hu", "zh", "en")}
    return {
        "cons": cons, "place": PLACE, "manner": MANNER, "vows": vows, "nasals": nasals, "mods": mods,
        "nat": nat, "natHu": nat_hu, "natZh": nat_zh, "ipa": ipa, "keys": keys, "orth": orth, "lazy": LAZY_ALIASES,
        "zhRetro": _ZH_RETRO, "tone": _TONE_MARKS, "help": HELP, "enDict": en_dict(DATA), "enCanon": EN_CANON,
        "ops": ops, "modsRef": mods_ref, "gloss": gloss,
        "counts": {"C": len(cons), "V": len(vows), "total": len(cons) + len(vows)},
    }


def subset_font_b64(payload):
    """Subset Charis SIL to exactly the codepoints the payload can display; return base64 woff2."""
    from fontTools.subset import Subsetter, Options, load_font, save_font
    cps = {ord(c) for c in json.dumps(payload, ensure_ascii=False)}
    cps |= set(range(0x20, 0x7F))                      # all printable ASCII, for safety
    opts = Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    opts.notdef_glyph = True
    opts.recommended_glyphs = True
    opts.drop_tables += ["Silt"]
    font = load_font(FONT_TTF, opts)
    ss = Subsetter(options=opts)
    ss.populate(unicodes=cps)
    ss.subset(font)
    buf = BytesIO()
    save_font(font, buf, opts)
    return base64.b64encode(buf.getvalue()).decode("ascii"), len(buf.getvalue())


def main():
    payload = build()
    fb64, fsize = subset_font_b64(payload)
    html = PAGE.replace("__FONTB64__", fb64).replace("/*DATA*/", json.dumps(payload, ensure_ascii=False))
    out = os.path.join(ROOT, "docs", "viz", "notation.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("wrote", out, "·", payload["counts"], "· font subset", fsize, "bytes")


PAGE = r"""<title>diaphone — the whole system</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@font-face{font-family:"DiaCharis";src:url(data:font/woff2;base64,__FONTB64__) format("woff2");font-display:swap}
:root{
  --paper:#f5f6f8; --card:#ffffff; --sunken:#eef0f4; --ink:#1a1d24; --muted:#5b6472; --line:#dde1e8;
  --accent:#0e7c86; --base-c:#0e7c86; --c-c:#b06f14; --j-c:#3f5bc0; --q-c:#8a4bb0; --x-c:#2f8f66; --n-c:#c0468a;
  --base-t:#0e7c8615; --c-t:#b06f1418; --j-t:#3f5bc016; --q-t:#8a4bb016; --x-t:#2f8f6618; --n-t:#c0468a1a;
  --serif:"DiaCharis","Charis SIL","Gentium Plus",Charter,"Iowan Old Style",Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  --mono:"SF Mono","JetBrains Mono","Menlo","Consolas",monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#14161b; --card:#1b1e25; --sunken:#101216; --ink:#e9ecf1; --muted:#98a1b0; --line:#2a2e37;
  --accent:#3ec8cf; --base-c:#3ec8cf; --c-c:#e0a44a; --j-c:#8b9ff0; --q-c:#c08ee0; --x-c:#4fc79a; --n-c:#e88ac0;
  --base-t:#3ec8cf1e; --c-t:#e0a44a22; --j-t:#8b9ff01e; --q-t:#c08ee01e; --x-t:#4fc79a22; --n-t:#e88ac022;
}}
:root[data-theme="dark"]{
  --paper:#14161b; --card:#1b1e25; --sunken:#101216; --ink:#e9ecf1; --muted:#98a1b0; --line:#2a2e37;
  --accent:#3ec8cf; --base-c:#3ec8cf; --c-c:#e0a44a; --j-c:#8b9ff0; --q-c:#c08ee0; --x-c:#4fc79a; --n-c:#e88ac0;
  --base-t:#3ec8cf1e; --c-t:#e0a44a22; --j-t:#8b9ff01e; --q-t:#c08ee01e; --x-t:#4fc79a22; --n-t:#e88ac022;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.55;-webkit-font-smoothing:antialiased;font-size:15px}
.wrap{max-width:1020px;margin:0 auto;padding:clamp(1.4rem,4vw,3rem) clamp(1rem,4vw,2rem) 4rem}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(1.9rem,5vw,2.7rem);letter-spacing:-.01em;margin:0 0 .3rem;text-wrap:balance}
h2{font-family:var(--serif);font-weight:600;font-size:1.35rem;margin:2.4rem 0 .3rem;display:flex;align-items:baseline;gap:.6rem}
h2 .n{font:400 .78rem/1 var(--mono);color:var(--muted)}
.tag{display:inline-block;font:600 .7rem/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.lede{color:var(--muted);max-width:70ch;margin:.2rem 0 0}.lede code{font-family:var(--mono);color:var(--ink)}
.toggle{border:1px solid var(--line);background:var(--card);color:var(--muted);border-radius:999px;padding:.35rem .8rem;font:600 .72rem/1 var(--mono);cursor:pointer}
.toggle:hover{color:var(--ink);border-color:var(--accent)}
.stats{display:flex;flex-wrap:wrap;gap:.4rem;margin:1rem 0 0}
.chip{border:1px solid var(--line);border-radius:.5rem;padding:.3rem .6rem;background:var(--card);font:600 .78rem/1 var(--mono);color:var(--muted)}.chip b{color:var(--accent)}
.scroll{overflow-x:auto;margin:.7rem 0 0;border:1px solid var(--line);border-radius:14px;background:var(--card)}
table.grid{border-collapse:collapse;width:100%;min-width:760px}
.grid th,.grid td{border:1px solid var(--line);padding:0;text-align:center;vertical-align:top}
.grid thead th{font:600 .66rem/1.1 var(--mono);letter-spacing:.04em;text-transform:uppercase;color:var(--muted);padding:.5rem .3rem;background:var(--sunken)}
.grid tbody th{font:600 .68rem/1.1 var(--mono);color:var(--muted);text-align:left;padding:.5rem .6rem;background:var(--sunken);white-space:nowrap}
.cell{display:flex;gap:2px;justify-content:center;min-height:100%}
.pt{flex:1;padding:.4rem .2rem;display:flex;flex-direction:column;align-items:center;gap:1px}
.pt.vl{background:var(--base-t)}.pt.vd{background:var(--c-t)}
.pt .nat{font-family:var(--serif);font-size:1.35rem;color:var(--ink);line-height:1.15}
.pt .lab{font:600 .74rem/1 var(--mono);color:var(--accent)}
.pt .ipa{font-family:var(--serif);font-size:.82rem;line-height:1.1;color:var(--muted)}
a.wref{color:var(--muted);text-decoration:none;border-bottom:1px dotted var(--line)}
a.wref:hover{color:var(--accent);border-bottom-color:var(--accent)}
.klegend{display:flex;flex-wrap:wrap;gap:.5rem 1.3rem;margin:.8rem 0 0;font-size:.85rem;color:var(--muted)}
.klegend .sw{display:inline-block;width:14px;height:14px;border-radius:4px;vertical-align:-2px;margin-right:.3rem}
.klegend b{color:var(--ink)}.klegend code{font-family:var(--mono);color:var(--ink)}
figure{margin:.9rem 0 0;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:.5rem}
svg{width:100%;height:auto;display:block}
.edge{stroke:var(--line);stroke-width:2;fill:none;opacity:.7}
.edgelab{fill:var(--muted);font-family:var(--mono);font-size:13px;letter-spacing:.06em;text-transform:uppercase}
.centre-ring{fill:none;stroke:var(--x-c);stroke-width:1;opacity:.4}
.chip-g .nat{font-family:var(--serif);font-size:20px;text-anchor:middle;dominant-baseline:middle;fill:var(--ink)}
.chip-g .lab{font-family:var(--mono);font-size:11px;text-anchor:middle;dominant-baseline:middle;font-weight:600}
.chip-g .ipa{font-family:var(--serif);font-size:12px;text-anchor:middle;dominant-baseline:middle;fill:var(--muted)}
.chip-g .til{fill:var(--n-c);font-family:var(--serif);font-size:14px;text-anchor:middle}
.cat-base rect{fill:var(--base-t);stroke:var(--base-c)}.cat-base .lab{fill:var(--base-c)}
.cat-c rect{fill:var(--c-t);stroke:var(--c-c)}.cat-c .lab{fill:var(--c-c)}
.cat-j rect{fill:var(--j-t);stroke:var(--j-c)}.cat-j .lab{fill:var(--j-c)}
.cat-q rect{fill:var(--q-t);stroke:var(--q-c)}.cat-q .lab{fill:var(--q-c)}
.cat-x rect{fill:var(--x-t);stroke:var(--x-c);stroke-dasharray:4 3}.cat-x .lab{fill:var(--x-c)}
.chip-g rect{stroke-width:1.6}
.legend{display:flex;flex-wrap:wrap;gap:.5rem 1.3rem;margin:1rem 0 0;font-size:.88rem}
.leg{display:flex;align-items:center;gap:.45rem;color:var(--muted)}.leg .sw{width:15px;height:15px;border-radius:5px;border:1.6px solid}.leg code{font-family:var(--mono);color:var(--ink)}
.sw-base{background:var(--base-t);border-color:var(--base-c)}.sw-c{background:var(--c-t);border-color:var(--c-c)}.sw-j{background:var(--j-t);border-color:var(--j-c)}.sw-q{background:var(--q-t);border-color:var(--q-c)}.sw-x{background:var(--x-t);border-color:var(--x-c)}.sw-n{background:var(--n-t);border-color:var(--n-c)}
.nasal-row{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.7rem}
.ntile{background:var(--n-t);border:1.6px solid var(--n-c);border-radius:10px;padding:.4rem .7rem;text-align:center;min-width:62px}
.ntile .nat{font-family:var(--serif);font-size:1.35rem;color:var(--ink)}.ntile .l{font-family:var(--mono);font-size:.75rem;color:var(--n-c);font-weight:600;margin-top:.1rem}.ntile .s{font-family:var(--serif);font-size:.85rem;color:var(--muted)}
.mods{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.5rem;margin:.7rem 0 0}
.mtile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:.6rem .7rem}
.mtile .nm{font:600 .72rem/1.2 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
.mtile .big{display:flex;align-items:baseline;gap:.5rem;margin-top:.35rem}
.mtile .nat{font-family:var(--serif);font-size:1.4rem;color:var(--ink)}.mtile .lab{font:600 .95rem/1 var(--mono);color:var(--accent)}.mtile .ipa{font-family:var(--serif);font-size:.85rem;color:var(--muted)}.mtile .gl{font-size:.78rem;color:var(--muted);margin-top:.25rem}
.try{margin:.9rem 0 0;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:1.1rem}
.tabs{display:flex;flex-wrap:wrap;gap:.35rem;margin-bottom:.8rem}
.tab{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:999px;padding:.35rem .85rem;font:600 .8rem/1 var(--mono);cursor:pointer}
.tab:hover{color:var(--ink)}.tab.on{background:var(--accent);border-color:var(--accent);color:#fff}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]) .tab.on{color:#0b0d11}}
:root[data-theme="dark"] .tab.on{color:#0b0d11}
#in{width:100%;border:1px solid var(--line);border-radius:.6rem;background:var(--sunken);color:var(--ink);padding:.7rem .8rem;font:1.1rem var(--mono)}
#in:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:transparent}
.lazy{display:none;align-items:center;gap:.4rem;margin:.6rem 0 0;font:.8rem var(--mono);color:var(--muted);cursor:pointer}
.lazy.show{display:flex}.lazy input{accent-color:var(--accent);cursor:pointer}.lazy .hint{opacity:.8}
.toggles{display:flex;flex-wrap:wrap;gap:.4rem 1.4rem}
.outs{margin:1rem 0 0;border-top:1px solid var(--line)}
.orow{display:flex;align-items:baseline;gap:.9rem;flex-wrap:wrap;padding:.6rem .2rem;border-bottom:1px solid var(--line);min-height:3rem}
.orow .k{font:600 .68rem/1.2 var(--mono);letter-spacing:.05em;text-transform:uppercase;color:var(--muted);min-width:5rem}
.orow .v{font-family:var(--serif);font-size:1.9rem;line-height:1.35;word-break:break-word}
.orow .brk{font:.78rem var(--mono);color:var(--muted)}
.help{margin:.9rem 0 0;color:var(--muted);font-size:.9rem}.help .note{max-width:74ch}
.exs{display:flex;flex-wrap:wrap;gap:.4rem;margin:.7rem 0 0}
.exs button{border:1px dashed var(--line);background:transparent;color:var(--accent);border-radius:.5rem;padding:.3rem .55rem;font:.8rem var(--mono);cursor:pointer;text-align:left}
.exs button:hover{border-style:solid}.exs .g{color:var(--muted);margin-left:.4rem}
table.ops{border-collapse:collapse;width:100%;min-width:520px}
.ops th,.ops td{border:1px solid var(--line);padding:.55rem .8rem;text-align:left;vertical-align:top;font-size:.9rem}
.ops thead th{font:600 .66rem/1.2 var(--mono);letter-spacing:.05em;text-transform:uppercase;color:var(--muted);background:var(--sunken)}
.ops td b{color:var(--ink);font-weight:600}
.ops .opc{font:700 1.35rem/1 var(--mono);color:var(--accent);text-align:center;white-space:nowrap}
.ops .on{display:block;font:600 .62rem/1.3 var(--mono);color:var(--muted)}
.ops .opex{font-family:var(--serif);color:var(--muted);font-size:.95rem}
.ops .mc{font:600 .85rem/1 var(--mono);color:var(--accent);white-space:nowrap}
.gloss{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.6rem;margin:.7rem 0 0}
.gitem{border:1px solid var(--line);border-radius:12px;padding:.7rem .85rem;background:var(--card)}
.gt{font:600 .95rem/1.25 var(--sans);color:var(--ink)}
.gw{color:var(--muted);font-size:.88rem;margin-top:.3rem}
.ge{font-family:var(--serif);font-size:.9rem;color:var(--accent);margin-top:.35rem}
footer{margin-top:2.4rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.78rem;font-family:var(--mono)}
</style>

<div class="wrap">
  <div class="top"><div><span class="tag">diaphone</span><h1>The whole system</h1></div>
    <button class="toggle" id="tt" aria-label="toggle theme">theme</button></div>
  <p class="lede">Every cross-linguistic point in three forms: the <b>native glyph</b> (how it's written),
  the <b>input</b> you type, and — small, for reference — its IPA value, linked to Wikipedia. Consonants on
  the articulatory grid, vowels on the triangle, then a tryout that converts your input into any target.</p>
  <div class="stats" id="stats"></div>

  <h2>The seven operators <span class="n">c j q x w h y — one mechanism, base-dependent</span></h2>
  <p class="lede">A label is a <b>base letter</b> plus attaching operators. Every operator is
  <b>base-dependent</b> — the same letter does one thing on a consonant, another on a vowel
  (<code>x</code> = dental on t, velar on k; <code>y</code> = emphatic on t, nasal on a). Four of them
  (<code>c j q x</code>) can form <i>new points</i>; the rule that decides each case:
  <b>base+letter is that point if it exists, otherwise the letter rides on top as a modifier</b>
  (<code>sj</code> → <span style="font-family:var(--serif)">s̩</span> is a point, <code>pj</code> →
  <span style="font-family:var(--serif)">p͈</span> a modifier; <code>tc</code> →
  <span style="font-family:var(--serif)">c</span> a point, <code>kc</code> →
  <span style="font-family:var(--serif)">k̈</span> a modifier).</p>
  <div class="scroll"><table class="ops"><thead><tr><th>op</th><th>on a consonant</th><th>on a vowel</th></tr></thead><tbody id="opsBody"></tbody></table></div>

  <h2>Consonants <span class="n" id="cN"></span></h2>
  <div class="scroll"><table class="grid"><thead id="cHead"></thead><tbody id="cBody"></tbody></table></div>
  <div class="klegend">
    <span><span class="sw" style="background:var(--base-t);border:1.6px solid var(--base-c)"></span><b>voiceless</b> (left)</span>
    <span><span class="sw" style="background:var(--c-t);border:1.6px solid var(--c-c)"></span><b>voiced</b> (right)</span>
    <span>each tile — <span style="font-family:var(--serif)"><b>native</b></span> · <code>input</code> · ipa (→ Wikipedia)</span>
    <span>gutturals are a 2×2 on <code>h</code>: ḥ=<code>hj</code> · ħ=<code>hc</code> · ħ̣=<code>hq</code></span>
  </div>

  <h2>Vowels <span class="n" id="vN"></span></h2>
  <figure><svg id="tri" viewBox="0 0 840 700" role="img" aria-label="Vowel triangle"></svg></figure>
  <div class="legend" id="legend"></div>
  <p class="lede" style="margin-top:1rem">Nasalisation is the <code>y</code> operator on any vowel — orthogonal
  to the triangle. In the 16 languages only <b>French</b> carries it; modelled as three nasalised cardinals:</p>
  <div class="nasal-row" id="nasals"></div>

  <h2>Modifiers <span class="n">the features that ride on top — never new points, one operator each</span></h2>
  <p class="lede">The phonological layer: seven <b>features</b> that never create a point — they're stripped
  off to find the base. Each maps to one of the operators above, read in its modifier role.</p>
  <div class="mods" id="mBody"></div>
  <div class="scroll" style="margin-top:.7rem"><table class="ops"><thead><tr><th>modifier</th><th>char</th><th>what it does</th><th>example</th></tr></thead><tbody id="modsRefBody"></tbody></table></div>

  <h2>The sounds, in words <span class="n">what the features mean</span></h2>
  <div class="gloss" id="glossBody"></div>

  <h2>Tryout <span class="n">pick a target · read its help</span></h2>
  <div class="try">
    <div class="tabs" id="tabs" role="tablist"></div>
    <input id="in" spellcheck="false" value="sjok sewp njawr">
    <div class="toggles">
      <label class="lazy" id="liwrap"><input type="checkbox" id="li"> loose input <span class="hint" id="lihint"></span></label>
      <label class="lazy" id="lvwrap"><input type="checkbox" id="lv"> <span id="lvText">loose view</span> <span class="hint" id="lvhint"></span></label>
    </div>
    <div class="outs" id="outs"></div>
    <div class="help"><p class="note" id="note"></p><div class="exs" id="exs"></div></div>
  </div>

  <footer id="foot"></footer>
</div>

<script type="application/json" id="data">/*DATA*/</script>
<script>
const D=JSON.parse(document.getElementById("data").textContent);
const esc=s=>String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));

/* universal render (native / IPA) */
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

/* language decode: faithful port of decode.py */
const VOWELS=new Set(["a","e","i","o","u"]);const isV=t=>!!t&&VOWELS.has(t[0]);
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
function decode(text,lang,lazy,endict){let orth={...D.orth[lang]};
  if((lazy||(endict&&lang==="en"))&&D.lazy[lang])orth={...orth,...D.lazy[lang]};
  const dict=(lang==="en"&&endict)?D.enDict:null;
  return text.trim().split(/\s+/).filter(Boolean).map(w=>{
    if(dict){const key=tokenize(w.toLowerCase(),Object.keys(orth)).map(t=>D.enCanon[t]||t).join("");
      if(dict[key])return dict[key];}
    return decodeWord(w,orth,lang);}).join(" ");}
window.__engine={urend,decode};

/* tryout: one tab per language; the two simplifications are inner switches —
   LOOSE INPUT (typing shortcuts) and LOOSE VIEW (that language's native-glyph reading). */
const TARGETS=[
  {key:"native",name:"native",rows:v=>[{k:"native",v:urend(v,D.nat),brk:true}]},
  {key:"ipa",name:"IPA",rows:v=>[{k:"ipa",v:urend(v,D.ipa)}]},
  {key:"hu",name:"HU",li:"bare a = ɒ · e = ɛ",
   rows:(v,li,lv)=>[{k:"native",v:urend(v,D.natHu),brk:true},{k:"spelling",v:decode(v,"hu",li)}]},
  {key:"zh",name:"ZH",li:"type Pinyin (xiao, shi)",
   rows:(v,li,lv)=>[{k:"native",v:urend(v,D.natZh),brk:true},{k:"spelling",v:decode(v,"zh",li)}]},
  {key:"en",name:"EN",li:"sh ch zh ng th dh · j y w",lv:"real spelling (28k words)",lvLabel:"dictionary",
   rows:(v,li,lv)=>[{k:"native",v:urend(v,D.nat),brk:true},{k:"spelling",v:decode(v,"en",li,lv)}]},
];
let CUR="native";
const $=id=>document.getElementById(id);
function run(){const T=TARGETS.find(t=>t.key===CUR),H=D.help[CUR],v=$("in").value;
  let rows=[];try{rows=T.rows(v,$("li").checked,$("lv").checked);}catch(e){rows=[{k:"",v:"—"}];}
  $("outs").innerHTML=rows.map(r=>`<div class="orow"><span class="k">${esc(r.k)}</span><span class="v">${esc(r.v)}</span>${r.brk?`<span class="brk">${esc(ubrk(v))}</span>`:""}</div>`).join("");
  $("note").innerHTML=esc(H.note);
  $("liwrap").className="lazy"+(T.li?" show":"");
  $("lvwrap").className="lazy"+(T.lv?" show":"");
  $("lihint").textContent=T.li?"· "+T.li:"";
  $("lvhint").textContent=T.lv?"· "+T.lv:"";
  $("lvText").textContent=T.lvLabel||"loose view";
  $("exs").innerHTML=H.ex.map(([inp,gl])=>`<button data-in="${esc(inp)}"><b>${esc(inp)}</b><span class="g">${esc(gl)}</span></button>`).join("");
}
function draw(){$("tabs").innerHTML=TARGETS.map(t=>`<button class="tab${t.key===CUR?" on":""}" data-k="${t.key}">${esc(t.name)}</button>`).join("");}
$("tabs").addEventListener("click",e=>{const b=e.target.closest(".tab");if(b){CUR=b.dataset.k;$("li").checked=false;$("lv").checked=false;draw();run();}});
$("exs").addEventListener("click",e=>{const b=e.target.closest("button");if(b){$("in").value=b.dataset.in;run();}});
$("in").addEventListener("input",run);$("li").addEventListener("change",run);$("lv").addEventListener("change",run);
draw();run();

/* consonant grid — voiceless first */
(function(){const byCell={};for(const c of D.cons){(byCell[c.manner+"|"+c.place]=byCell[c.manner+"|"+c.place]||[]).push(c);}
  $("cHead").innerHTML="<tr><th></th>"+D.place.map(([,ab])=>`<th>${esc(ab)}</th>`).join("")+"</tr>";
  const rank=v=>v==="vl"?0:1;
  const rows=D.manner.filter(([m])=>D.cons.some(c=>c.manner===m)).map(([m,ml])=>{
    const tds=D.place.map(([pl])=>{const pts=(byCell[m+"|"+pl]||[]).sort((a,b)=>rank(a.voice)-rank(b.voice));
      if(!pts.length)return "<td></td>";
      const tiles=pts.map(p=>`<div class="pt ${p.voice==="vl"?"vl":"vd"}"><span class="nat">${esc(p.native)}</span><span class="lab">${esc(p.label)}</span><span class="ipa"><a class="wref" href="${esc(p.wiki)}" target="_blank" rel="noopener">${esc(p.ipa)}</a></span></div>`).join("");
      return `<td><div class="cell">${tiles}</div></td>`;}).join("");
    return `<tr><th>${esc(ml)}</th>${tds}</tr>`;});
  $("cBody").innerHTML=rows.join("");})();

/* vowel triangle */
(function(){const NS="http://www.w3.org/2000/svg";const el=(n,at)=>{const e=document.createElementNS(NS,n);for(const k in at)e.setAttribute(k,at[k]);return e;};
  const svg=$("tri");const I=[150,155],U=[690,155],A=[430,618];
  svg.appendChild(el("path",{class:"edge",d:`M${I[0]},${I[1]} L${U[0]},${U[1]} L${A[0]},${A[1]} Z`}));
  svg.appendChild(el("circle",{class:"centre-ring",cx:430,cy:436,r:42}));
  const lab=(x,y,text,rot,sz)=>{const t=el("text",{class:"edgelab",x,y,"text-anchor":"middle",transform:`rotate(${rot} ${x} ${y})`});if(sz)t.setAttribute("font-size",sz);t.textContent=text;svg.appendChild(t);};
  lab(420,132,"close",0);lab(240,400,"front · unrounded",52);lab(620,400,"back · rounded",-52);lab(430,652,"open",0);lab(430,398,"centre",0,11);
  for(const v of D.vows){const g=el("g",{class:"chip-g cat-"+v.cat});
    g.appendChild(el("rect",{x:v.x-27,y:v.y-30,width:54,height:60,rx:11}));
    const nt=el("text",{class:"nat",x:v.x,y:v.y-13});nt.textContent=v.native;g.appendChild(nt);
    const lb=el("text",{class:"lab",x:v.x,y:v.y+3});lb.textContent=v.label;g.appendChild(lb);
    const a=el("a",{href:v.wiki,target:"_blank",rel:"noopener"});
    const ip=el("text",{class:"ipa",x:v.x,y:v.y+19});ip.textContent=v.ipa;a.appendChild(ip);g.appendChild(a);
    if(v.nasal){const t=el("text",{class:"til",x:v.x+20,y:v.y-17});t.textContent="˜";g.appendChild(t);}
    svg.appendChild(g);}
  const LEG=[["base","base","i e a o u"],["c","c","flip front↔back"],["j","j","lower one step"],["q","q","c + j (front-round)"],["x","x","centralise → ə"],["n","˜","nasal (+y)"]];
  $("legend").innerHTML=LEG.map(([cls,code,desc])=>`<div class="leg"><span class="sw sw-${cls}"></span><code>${esc(code)}</code> <span>${esc(desc)}</span></div>`).join("");
  $("nasals").innerHTML=D.nasals.map(n=>`<div class="ntile"><div class="nat">${esc(n.native)}</div><div class="l">${esc(n.label)}</div><div class="s">${esc(n.ipa)}</div></div>`).join("");})();

/* operators + modifiers reference + glossary */
const pairHTML=p=>`<b class="serif" style="font-family:var(--serif)">${esc(p.nat)}</b> <code>${esc(p.lab)}</code>`;
const pairsHTML=ps=>ps.map(pairHTML).join(" · ");
$("opsBody").innerHTML=D.ops.map(o=>`<tr><td class="opc">${esc(o.op)}${o.note?`<span class="on">${esc(o.note)}</span>`:""}</td><td><b>${esc(o.cons)}</b><br><span class="opex">${pairsHTML(o.cons_ex)}</span></td><td><b>${esc(o.vowel)}</b><br><span class="opex">${pairsHTML(o.vowel_ex)}</span></td></tr>`).join("");
$("modsRefBody").innerHTML=D.modsRef.map(m=>`<tr><td><b>${esc(m.name)}</b></td><td class="mc">${esc(m.char)}</td><td>${esc(m.desc)}</td><td class="opex">${pairsHTML(m.ex)}</td></tr>`).join("");
$("glossBody").innerHTML=D.gloss.map(g=>`<div class="gitem"><div class="gt">${esc(g.title)}</div><div class="gw">${esc(g.text)}</div><div class="ge">${g.ex.map(e=>`${pairHTML(e)}${e.word?` <span style="color:var(--muted)">— ${esc(e.word)}</span>`:""}`).join(" · ")}</div></div>`).join("");
/* modifiers + stats + theme */
$("mBody").innerHTML=D.mods.map(m=>`<div class="mtile"><div class="nm">${esc(m.name)}</div><div class="big"><span class="nat">${esc(m.native)}</span><span class="lab">${esc(m.label)}</span><span class="ipa">${esc(m.ipa)}</span></div><div class="gl">${esc(m.gloss)}</div></div>`).join("");
$("cN").textContent=D.counts.C+" points";$("vN").textContent=D.counts.V+" points";
$("stats").innerHTML=`<span class="chip"><b>${D.counts.total}</b> points</span><span class="chip"><b>${D.counts.C}</b> consonants</span><span class="chip"><b>${D.counts.V}</b> vowels</span><span class="chip"><b>7</b> modifiers</span><span class="chip"><b>16</b> languages</span>`;
$("foot").textContent="diaphone · "+D.counts.total+" general points · native · input · ipa · one input, any target";
const tt=$("tt");tt.addEventListener("click",()=>{const r=document.documentElement,c=r.getAttribute("data-theme");r.setAttribute("data-theme",c==="dark"?"light":c==="light"?"":"dark");tt.textContent=r.getAttribute("data-theme")||"theme";});
</script>
"""


if __name__ == "__main__":
    main()
