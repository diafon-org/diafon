#!/usr/bin/env python3
"""Generate docs/font-coverage.html — every uni glyph, rendered natively in the fonts people have.

`check_font_coverage.py` answers "is the codepoint in the cmap". This answers the question that
actually matters: *does it look right*. A font can carry U+0329 and still place it badly, and the
only way to see that is to render it. So each cell here is the real glyph in the real font, and the
browser does the work — open it on the machine whose rendering you care about.

Rows are ordered by how likely they are to fail: bare letters first, then precomposed characters,
then the combining sequences that have no precomposed form, rarest mark last.

    python scripts/gen_font_table.py        # -> docs/font-coverage.html
"""
import base64
import io
import os
import sys
import unicodedata
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from diaphone.loader import load                    # noqa: E402
from diaphone.uni import uni_labels                 # noqa: E402
from diaphone.render import ipa_labels              # noqa: E402
from diaphone.notation import _label_maps, full_label, point_labels   # noqa: E402
from diaphone.derive import derive                      # noqa: E402
from diaphone.merges import apply_merges                # noqa: E402
from check_font_coverage import covered, font_files     # noqa: E402
from gen_uni_page import wiki_url, serif_prose                       # noqa: E402  (one source for the URLs)

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data")

# The columns: each platform's DEFAULT UI font, then the classic web faces. `stack` is what the
# browser is told to use; `scan` is the local file we can inspect with fontTools, so coverage is
# stated as fact rather than guessed from the rendering; `os` groups the header.
#
# Deliberately absent: "System UI", because it resolves to a different font on every machine — a
# tick in that column would mean nothing portable. And Verdana, whose coverage is so thin it tells
# you about Verdana rather than about the notation (`check_font_coverage.py` still reports it).
FONTS = [
    ("SF Pro",    "'SF Pro Text','SF Pro',-apple-system,BlinkMacSystemFont", "SFNS",             "iOS · macOS"),
    ("Roboto",    "Roboto, sans-serif",                                      "Roboto-Regular",   "Android"),
    ("Noto Sans", "'Noto Sans', sans-serif",                                 "NotoSans-Regular", "Android"),
    ("Segoe UI",  "'Segoe UI', sans-serif",                                  "segoeui",          "Windows"),
    ("Helvetica", "Helvetica,'Helvetica Neue',sans-serif",                   "Helvetica",        "classic"),
    ("Arial",     "Arial, sans-serif",                                       "Arial",            "classic"),
    ("Times",     "'Times New Roman', Times, serif",                         "Times New Roman",  "classic"),
    ("Georgia",   "Georgia, serif",                                          "Georgia",          "classic"),
    ("Mono",      "ui-monospace, Menlo, Consolas, monospace",                "Menlo",            "mono"),
    ("Diaphone",  "'Diaphone', serif",                                       None,               "ours"),
]


MOD_WIKI = {
    "long": "Length_(phonetics)", "nasal": "Nasal_vowel",
    "aspirated": "Aspirated_consonant", "palatalized": "Palatalization_(phonetics)",
    "pharyngealized": "Pharyngealization", "retroflex": "Retroflex_consonant",
    "rhotic": "R-colored_vowel", "nonsyllabic": "Semivowel",
}
CAT_ORDER = ["base point", "point · c", "point · j", "point · q", "point · x",
             "long", "nasal", "aspirated", "palatalized", "pharyngealized",
             "retroflex", "rhotic", "nonsyllabic"]


def category(label, mods, points):
    """Second-level grouping: what KIND of thing this glyph is — a point (by the operator
    that formed it) or a modifier riding on one. Availability is the major axis; this says
    which part of the system a gap would actually cost you."""
    if mods:
        return " + ".join(sorted(mods))
    if label in points and len(label) > 1:
        return "point · " + label[1:]
    return "base point"


def tiers(uni, ipa, lang_of, mods_of, points):
    """Group every distinct uni glyph by how hard it is to render, easiest first.

    Excluded: the long/geminate labels (a doubled letter shows nothing a single one does not)
    and any label no language attests — the systematic glide slot `ucx` /ɰ/ is the only one.
    """
    scanned = {name: covered(p) for p in font_files([])
               for name in [os.path.splitext(os.path.basename(p))[0]]}
    rows = defaultdict(list)
    seen = set()
    for label, glyph in sorted(uni.items()):
        if label.endswith("w") or label not in lang_of:      # geminates · unattested slots
            continue
        g = unicodedata.normalize("NFC", glyph)
        if g in seen:
            continue
        seen.add(g)
        nfd = unicodedata.normalize("NFD", g)
        marks = [c for c in nfd if unicodedata.category(c) == "Mn"]
        if len(g) == 1 and ord(g) < 128:
            tier, key = 0, (0, g)
        elif len(g) == 1 and ord(g) < 0x250:
            tier, key = 1, (0, g)
        elif len(g) == 1:
            tier, key = 2, (0, g)
        else:
            # combining: order by how many scanned fonts lack the mark — the rarest last
            rare = max((sum(1 for cov in scanned.values() if m not in cov) for m in marks),
                       default=0)
            tier, key = 3, (rare, g)
        cat = category(label, mods_of.get(label, frozenset()), points)
        rows[tier].append((key, cat, label, g, ipa.get(label, "?"),
                           " ".join(sorted(lang_of.get(label, ()))),
                           " ".join(f"U+{ord(c):04X}" for c in marks)))
    order = {c: i for i, c in enumerate(CAT_ORDER)}
    for t in rows:
        rows[t].sort(key=lambda r: (order.get(r[1], 99), r[1], r[0]))
    return rows, scanned


TIER_NAME = {
    0: ("Bare letters", "Plain ASCII. Renders in anything that renders text at all."),
    1: ("Precomposed, Latin-1 / Extended-A", "Single codepoints every Latin font has carried for decades."),
    2: ("Precomposed, Latin Extended Additional",
        "Single codepoints in the U+1E00 block. Broad, though not quite universal."),
    3: ("Combining sequences", "No precomposed form exists, so the font must carry the mark AND place it. "
        "This is where the view is actually at risk; rarest mark last."),
}


def build():
    feats, _raw, all_ph = load(DATA)
    uni = uni_labels(all_ph, feats, DATA)
    ipa = ipa_labels(all_ph, feats, DATA)
    lob, mm = _label_maps(all_ph, feats, DATA)
    # the article for each GENERAL point, keyed by its label (fold sources share the label)
    general, _folded = apply_merges(derive(all_ph, feats)[0])
    wiki_of_point = {lob[bt]: wiki_url(*bt) for bt in general if bt in lob}
    lang_of, mods_of, point_of = defaultdict(set), {}, {}
    for L, phs in all_ph.items():
        for ph in phs:
            pl = lob.get(ph["base"])
            if pl:
                lab = full_label(pl, ph["mods"], mm, DATA)
                lang_of[lab].add(L)
                mods_of[lab] = ph["mods"]
                point_of[lab] = pl

    rows, scanned = tiers(uni, ipa, lang_of, mods_of, point_labels(DATA))
    # every row links its IPA value: a point to its own article, a modified point to its base's
    wiki_of = {lab: wiki_of_point.get(point_of.get(lab, lab)) for lab in uni}

    with open(os.path.join(ROOT, "fonts", "Diaphone-Regular.ttf"), "rb") as f:
        fb64 = base64.b64encode(f.read()).decode("ascii")

    # per-font verdict for the fonts we can actually inspect
    verdict = {}
    for name, _stack, scan, _os in FONTS:
        if not scan or scan not in scanned:
            verdict[name] = None
            continue
        missing = {c for label, g in uni.items()
                   for c in unicodedata.normalize("NFC", g) if c not in scanned[scan]}
        verdict[name] = sorted(missing)

    out = [HEAD.replace("__FONT__", fb64)]
    out.append('<header><h1>Which fonts can render the view</h1>')
    out.append('<p class="lede">Every distinct glyph in the uni view, drawn in the fonts a reader is '
               'likely to have. Each cell shows the glyph <em>and its capital</em>, as live text rather '
               'than screenshots — <strong>what you see is what your machine does</strong>. Rows run '
               'easiest to hardest.</p>')
    out.append('<p class="note">Coverage flags come from reading each font file\'s character map; '
               'the rendering next to them is the browser\'s. They can disagree — a font may carry a '
               'mark and still place it badly, which is exactly what the eye is for. A '
               '<span class="miss-k">·</span> means the font file has no such codepoint — nothing '
               'to render, so nothing is drawn. Each IPA value links to what the sound is; a '
               'modified point links to its base, and the sub-group heading links to the modifier '
               'itself.</p></header>')

    # the summary of what is actually at risk
    out.append('<section class="risk"><h2>What is at risk</h2><table class="t risk-t"><thead><tr>'
               '<th>mark</th><th>glyphs</th><th>used by</th></tr></thead><tbody>')
    RISK = [("̦", "the palatal comma — ș ț n̦ and the whole soft series (s and t precompose)"),
            ("͈", "the doubled comma — s͈ z͈, the soft consonants whose single comma already spells a point (ș z̦ = ʃ ʒ); Unicode has no double comma, so this one cannot match the single mark's shape"),
            ("̖", "the retroflex tail — t̖ n̖ l̖ r̖"),
            ("̓", "the comma above, on the descenders p g — p̓ g̓")]
    for mark, desc in RISK:
        langs = sorted({L for label, g in uni.items() if mark in unicodedata.normalize("NFD", g)
                        for L in lang_of.get(label, ())})
        out.append(f'<tr><td class="cp">U+{ord(mark):04X}</td><td>{serif_prose(desc)}</td>'
                   f'<td class="langs">{" ".join(langs) or "—"}</td></tr>')
    out.append('</tbody></table>'
               '<p class="note">Only <strong>ET RU TA UK</strong> lose a glyph on the Apple/Android '
               'system font; the other 19 languages render completely as plain Unicode text.</p></section>')

    out.append('<div class="scroll"><table class="t main"><thead>')
    out.append('<tr class="osrow"><th colspan="2"></th>')
    i = 0
    while i < len(FONTS):
        span = 1
        while i + span < len(FONTS) and FONTS[i + span][3] == FONTS[i][3]:
            span += 1
        out.append(f'<th class="os" colspan="{span}">{FONTS[i][3]}</th>')
        i += span
    out.append('<th></th></tr>')
    out.append('<tr><th class="lab">label</th><th class="ip">IPA</th>')
    for name, stack, _scan, _os in FONTS:
        out.append(f'<th class="fh" data-probe="{stack}" data-name="{name}">{name}</th>')
    out.append('<th class="lang">languages</th></tr></thead><tbody>')

    def header_row(cls="rep"):
        cells = "".join(f'<td class="fh">{n}</td>' for n, _s, _c, _o in FONTS)
        return (f'<tr class="{cls}"><td class="lab">label</td><td class="ip">IPA</td>'
                f'{cells}<td class="lang">languages</td></tr>')

    for t in sorted(rows):
        title, blurb = TIER_NAME[t]
        out.append(f'<tr class="grp"><td colspan="{len(FONTS)+3}"><span class="gt">{title}</span>'
                   f'<span class="gb">{blurb}</span></td></tr>')
        out.append(header_row())          # the full header repeats per SECTION, nowhere else
        cur = None
        for _key, cat, label, g, ip, langs, cps in rows[t]:
            if cat != cur:
                cur = cat
                mw = MOD_WIKI.get(cat)
                lbl = (f'<a class="wref" href="https://en.wikipedia.org/wiki/{mw}" '
                       f'target="_blank" rel="noopener">{cat}</a>') if mw else cat
                out.append(f'<tr class="sub"><td colspan="{len(FONTS)+3}">{lbl}</td></tr>')
            cap = unicodedata.normalize("NFC", g[:1].upper() + g[1:])
            w = wiki_of.get(label)
            ipc = (f'<a class="wref" href="{w}" target="_blank" rel="noopener" '
                   f'title="what this sound is">{ip}</a>') if w else ip
            out.append(f'<tr><td class="lab"><code>{label}</code></td><td class="ip">{ipc}</td>')
            for name, stack, scan, _os in FONTS:
                cov = scanned.get(scan)
                if cov is not None and any(c not in cov for c in g + cap):
                    out.append('<td class="gl miss" title="codepoint absent from the font">·</td>')
                else:
                    out.append(f'<td class="gl" style="font-family:{stack}">{g}<i>{cap}</i></td>')
            out.append(f'<td class="lang">{langs}<span class="cp">{cps}</span></td></tr>')
    out.append('</tbody><tfoot><tr><td class="lab">missing</td><td></td>')
    for name, _stack, scan, _os in FONTS:
        v = verdict[name]
        if v is None:
            out.append('<td class="vd na">—</td>')
        elif not v:
            out.append('<td class="vd ok">0</td>')
        else:
            out.append(f'<td class="vd bad">{len(v)}</td>')
    out.append('<td class="lang">codepoints absent from the font file</td></tr></tfoot></table></div>')
    out.append('<footer>Generated by <code>scripts/gen_font_table.py</code> · the coverage numbers '
               'come from <code>scripts/check_font_coverage.py</code></footer>')
    out.append(PROBE)
    return "\n".join(out)


PROBE = """<script>
/* A font the machine does not have falls back silently, which would read as a pass. Measure a
   probe string against a deliberately-different fallback: equal widths = the font is not here. */
(function(){
  const S="\u0219\u021Bn\u0326 MWil1", c=document.createElement("canvas").getContext("2d");
  const w=(f)=>{c.font="24px "+f;return c.measureText(S).width;};
  const base=w("monospace"), base2=w("serif");
  document.querySelectorAll("th.fh[data-probe]").forEach((th,ix)=>{
    const stack=th.dataset.probe;
    const here = w(stack+",monospace")!==base || w(stack+",serif")!==base2;
    if(here) return;
    th.classList.add("na-col");
    th.insertAdjacentHTML("beforeend","<small>not installed</small>");
    const col=[...th.parentNode.children].indexOf(th);
    document.querySelectorAll("table.main tbody tr").forEach(tr=>{
      const cell=tr.children[col]; if(cell) cell.classList.add("na-col");
    });
  });
})();
</script>"""

HEAD = """<title>Font Coverage Bench</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@font-face{font-family:"Diaphone";src:url(data:font/ttf;base64,__FONT__) format("truetype");font-display:swap}
:root{
  --paper:#faf9f7; --sunken:#f0eeea; --ink:#1c1a17; --dim:#6b6459; --line:#ddd8d0;
  --ok:#2f6f57; --bad:#a4442c; --accent:#3d5a80;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#16161a; --sunken:#1f1f25; --ink:#eceaea; --dim:#9a938c; --line:#33323a;
  --ok:#7fc4a4; --bad:#e08a6e; --accent:#8fb0d8;
}}
:root[data-theme="dark"]{
  --paper:#16161a; --sunken:#1f1f25; --ink:#eceaea; --dim:#9a938c; --line:#33323a;
  --ok:#7fc4a4; --bad:#e08a6e; --accent:#8fb0d8;
}
*{box-sizing:border-box}
body{margin:0;padding:2.5rem 1.5rem 4rem;background:var(--paper);color:var(--ink);
  font:16px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
  -webkit-text-size-adjust:100%}
header,section,footer,.scroll{max-width:78rem;margin:0 auto}
h1{font-size:1.9rem;line-height:1.15;margin:0 0 .6rem;letter-spacing:-.01em;text-wrap:balance}
h2{font-size:1.05rem;margin:2.5rem 0 .7rem;letter-spacing:.02em;text-transform:uppercase;color:var(--dim)}
.lede{max-width:44rem;margin:0 0 .8rem;font-size:1.05rem}
.note{max-width:44rem;margin:0 0 .4rem;color:var(--dim);font-size:.9rem}
code{font:600 .82em/1.4 ui-monospace,Menlo,Consolas,monospace;color:var(--accent);
  background:var(--sunken);padding:.1em .34em;border-radius:.3em}
.scroll{overflow-x:auto;margin-top:1.6rem;border:1px solid var(--line);border-radius:.5rem}
table.t{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
.t th,.t td{padding:.34rem .6rem;text-align:left;border-bottom:1px solid var(--line)}
.t thead th{position:sticky;top:0;background:var(--sunken);font-size:.72rem;letter-spacing:.06em;
  text-transform:uppercase;color:var(--dim);font-weight:600;z-index:2}
.lab code{background:none;padding:0}
.ip{color:var(--dim);font-size:.85rem;white-space:nowrap}
.gl{font-size:1.5rem;line-height:1.3;text-align:center;min-width:4.6rem;white-space:nowrap}
.gl i{font-style:normal;margin-left:.42em;opacity:.72}
.gl.miss{color:var(--bad);opacity:.45;font-size:1.1rem}
.miss-k{color:var(--bad);font-weight:700}
a.wref{color:inherit;text-decoration:none;border-bottom:1px dotted var(--line)}
a.wref:hover{color:var(--accent);border-bottom-color:var(--accent)}
tr.sub td{background:transparent;border-top:1px solid var(--line);border-bottom:none;
  padding:.62rem .6rem .2rem;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;
  color:var(--accent);font-weight:600}
tr.rep td{background:var(--sunken);font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;
  color:var(--dim);font-weight:600;padding:.28rem .6rem}
tr.rep td.lang,tr.rep td.ip,tr.rep td.lab{text-transform:uppercase}
.fh{text-align:center}
.lang{color:var(--dim);font-size:.72rem;letter-spacing:.03em;white-space:nowrap}
.lang .cp{display:block;background:none;padding:0;color:var(--dim);opacity:.65;font-size:.9em}
.grp td{background:var(--sunken);padding:.7rem .6rem}
.gt{font-weight:650;font-size:.9rem;margin-right:.7rem}
.gb{color:var(--dim);font-size:.82rem}
tfoot td{border-bottom:none;font-weight:650;background:var(--sunken)}
.vd{text-align:center}.vd.ok{color:var(--ok)}.vd.bad{color:var(--bad)}.vd.na{color:var(--dim)}
.risk-t{margin-top:.4rem;border:1px solid var(--line);border-radius:.5rem;overflow:hidden}
/* glyphs quoted in the PROSE, set in the project font so the explanation is legible. The sample
   cells below are deliberately untouched — showing how each system font copes is the whole point. */
.ug{font-family:'Diaphone', serif}
.risk-t td.cp{font:600 .82rem ui-monospace,Menlo,monospace;color:var(--accent);white-space:nowrap}
.risk-t td{font-size:.9rem}
footer{margin-top:2.5rem;color:var(--dim);font-size:.82rem}
.osrow th.os{background:var(--sunken);text-align:center;font-size:.66rem;letter-spacing:.1em;
  text-transform:uppercase;color:var(--dim);border-bottom:1px solid var(--line);font-weight:600}
th.fh small{display:block;font-weight:400;text-transform:none;letter-spacing:0;color:var(--bad);
  font-size:.9em;opacity:.85}
td.na-col,th.na-col{opacity:.34}
</style>
"""

if __name__ == "__main__":
    path = os.path.join(ROOT, "docs", "font-coverage.html")
    html = build()
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {path} · {len(html)} bytes")
