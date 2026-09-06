#!/usr/bin/env python3
"""Generate docs/master.html, the master tables.

The universal table: every input form in use, grouped by keystroke count,
with its glyph and its readings from the most to the least used (languages ·
native speakers). Then one table per language (IPA, frequency, input form,
glyph), stamped with the mapping's review state (non-reviewed · reviewed ·
native-reviewed) from data/mapping.yaml.

Validation as before: every non-X phoneme mapped; no within-language form
collision outside `merges`.
"""
import glob
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine
import ipa_names

C_POINTS = {'sj','zj','tq','dq','tc','dc','kx','gx','kq','hx','rc','tx','dx','nx','py','ky','gy'}
RETRO = {'ty','dy','ny'}
SPECIAL2 = {'tcy','dcy'}
V_POINTS = {'ij','ej','uj','oj','aj','ic','ec','uc','oc','ac','eq','iq','aq'}
SEQ = {'aix','aux','ojix','eix','oux','ojicx','ejix','eqicx','ajux','tyh','dyh','rch','pf'}
STATES = {'native': ('native-reviewed', 'st-nat'),
          'reviewed': ('reviewed', 'st-rev'),
          None: ('non-reviewed', 'st-non')}


def form_type(f):
    if len(f) == 1: return 'base'
    if f in C_POINTS or f in V_POINTS: return 'point'
    if f.endswith('xy') or f in SPECIAL2: return 'special'
    if f in RETRO: return 'retro'
    if f in SEQ: return 'sequence'
    if f in {'ix','ux','icx'}: return 'glide'
    if f.endswith('w'): return 'long'
    if f.endswith('y'): return 'nasal'
    if f.endswith('x'): return 'shift'
    if f.endswith('j'): return 'soft'
    return '?'


def nfd(s):
    return ud.normalize('NFD', s)


def load_mapping():
    m = yaml.safe_load(open(os.path.join(ROOT, 'data', 'mapping.yaml')))
    cons = {nfd(k): v for k, v in m['consonants'].items()}
    vows = {nfd(k): v for k, v in m['vowels'].items()}
    over = {c: {nfd(k): v for k, v in d.items()} for c, d in m['overrides'].items()}
    merges = {c: [{nfd(a), nfd(b)} for a, b in pairs]
              for c, pairs in (m.get('merges') or {}).items()}
    review = m.get('review') or {}
    shares = {f: {nfd(i): v for i, v in d.items()}
              for f, d in (m.get('shares') or {}).items()}
    return cons, vows, over, merges, review, shares


def load_languages():
    langs = {}
    for path in sorted(glob.glob(os.path.join(ROOT, 'data', 'languages', '*.yaml'))):
        d = yaml.safe_load(open(path))
        langs[d['code']] = d
    return langs


def aggregate():
    cons, vows, over, merges, _, shares = load_mapping()
    langs = load_languages()
    agg, errors = {}, []
    for code, d in langs.items():
        native = d['speakers']['native']
        taken = {}
        for sec, table in (('consonants', cons), ('vowels', vows)):
            for ipa, freq in d[sec].items():
                key = nfd(ipa)
                form = over.get(code, {}).get(key) or table.get(key)
                if not form:
                    errors.append(f'{code}: unmapped {ipa}')
                    continue
                if freq == 'X':
                    continue    # writable, but out of the stats and the injectivity check
                if form in taken:
                    pair = {key, nfd(taken[form])}
                    if pair not in merges.get(code, []):
                        errors.append(f'{code}: {ipa} and {taken[form]} both on {form}')
                        continue
                taken[form] = ipa
                e = agg.setdefault(form, {}).setdefault(ud.normalize('NFC', ipa), [0, 0.0, []])
                e[0] += 1
                e[1] += native
                e[2].append(code)
    # one reading per regular form: polyvalence belongs to y / yx / the grave
    def polyvalent_ok(f):
        return (f.endswith('y') or f.endswith('xy'))
    for form, reads in agg.items():
        if len(reads) < 2 or polyvalent_ok(form) or form in SEQ:
            continue
        allowed = set(shares.get(form, {}))
        extra = {i for i in map(nfd, reads) if i not in allowed}
        if extra or not allowed:
            errors.append(f'unlisted share on {form}: {sorted(reads)}')
    if errors:
        print('MAPPING INVALID:', *errors, sep='\n  ')
        sys.exit(1)
    return agg


def fmt(m):
    return f'{m/1000:.1f}B' if m >= 1000 else f'{m:.0f}M'


HEAD = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diaphone · Master Tables</title>
<style>
:root{
  --paper:#f5f6f8; --card:#ffffff; --sunken:#eef0f4; --ink:#1a1d24; --muted:#5b6472; --line:#dde1e8;
  --accent:#0e7c86; --good:#2f8f66; --warn:#b06f14;
  --c-c:#b06f14; --j-c:#3f5bc0; --q-c:#8a4bb0; --x-c:#2f8f66; --y-c:#c0468a;
  --serif:"Diaphone","Charis SIL","Gentium Plus","Noto Serif","Times New Roman",Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  --mono:"SF Mono","JetBrains Mono","Menlo","Consolas",monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#14161b; --card:#1b1e25; --sunken:#101216; --ink:#e9ecf1; --muted:#98a1b0; --line:#2a2e37;
  --accent:#3ec8cf; --good:#4fc79a; --warn:#e0a44a;
  --c-c:#e0a44a; --j-c:#8b9ff0; --q-c:#c08ee0; --x-c:#4fc79a; --y-c:#e88ac0;
}}
:root[data-theme="dark"]{
  --paper:#14161b; --card:#1b1e25; --sunken:#101216; --ink:#e9ecf1; --muted:#98a1b0; --line:#2a2e37;
  --accent:#3ec8cf; --good:#4fc79a; --warn:#e0a44a;
  --c-c:#e0a44a; --j-c:#8b9ff0; --q-c:#c08ee0; --x-c:#4fc79a; --y-c:#e88ac0;
}
@font-face{font-family:"Diaphone";src:url(diaphone.woff2) format("woff2");font-display:swap}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.55;font-size:15px}
.wrap{max-width:1020px;margin:0 auto;padding:clamp(1.4rem,4vw,3rem) clamp(1rem,4vw,2rem) 4rem}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(1.7rem,4.5vw,2.3rem);margin:0 0 .2rem}
h2{font-family:var(--serif);font-weight:600;font-size:1.3rem;margin:2.4rem 0 .4rem}
.lede{color:var(--muted);margin:.2rem 0 0;max-width:74ch}
a{color:var(--accent)}
a.wref{color:inherit;text-decoration:none;border-bottom:1px dotted var(--line)}
a.wref:hover{border-bottom-color:var(--accent)}
code{font:600 .78em/1.4 var(--mono);color:var(--accent);background:var(--sunken);padding:.1em .32em;border-radius:.32em}
.ug{font-family:var(--serif)}
.opswrap{overflow-x:auto;margin:.8rem 0 0;border:1px solid var(--line);border-radius:14px;background:var(--card)}
table{border-collapse:collapse;width:100%;min-width:640px}
th{font:600 .66rem/1.1 var(--mono);letter-spacing:.04em;text-transform:uppercase;color:var(--muted);padding:.5rem .8rem;background:var(--sunken);text-align:left}
td{padding:.42rem .8rem;border-top:1px solid var(--line);vertical-align:top}
td.g{font-family:var(--serif);font-size:1.15rem}
.st{font:600 .68rem/1.3 var(--mono);color:var(--muted);white-space:nowrap}
.rname{display:block;font:500 .64rem/1.3 var(--mono);color:var(--muted);margin-top:1px}
.just{display:block;font-size:.74rem;line-height:1.35;color:var(--muted);margin-top:2px;max-width:26ch}
.just b{color:var(--ink);font:600 .68rem var(--mono)}
.rgroup{margin-bottom:.55rem}
.rgroup:last-child{margin-bottom:0}
.just{max-width:none}
.tt{font:600 .68rem/1.4 var(--mono);color:var(--muted)}
tr.grp th{background:var(--sunken);color:var(--accent)}
.badge{display:inline-block;font:600 .66rem/1 var(--mono);letter-spacing:.05em;text-transform:uppercase;
  border-radius:999px;padding:.28rem .6rem;vertical-align:2px;margin-left:.5rem;border:1px solid var(--line)}
.st-nat{color:var(--good);border-color:var(--good)}
.st-rev{color:var(--warn);border-color:var(--warn)}
.st-non{color:var(--muted)}
.toc{display:flex;flex-wrap:wrap;gap:.4rem;margin:1rem 0 0}
.toc a{font:600 .72rem/1 var(--mono);text-decoration:none;border:1px solid var(--line);border-radius:.5rem;
  padding:.34rem .55rem;background:var(--card);color:var(--muted)}
.toc a b{color:var(--ink)}
.toc a.st-nat{border-color:var(--good)} .toc a.st-rev{border-color:var(--warn)}
.plus{font:600 .82rem var(--mono);margin-left:.2rem}
.prev{display:block;font-size:.72rem;color:var(--muted);margin-top:2px;white-space:nowrap}
.op-c{color:var(--c-c)} .op-j{color:var(--j-c)} .op-q{color:var(--q-c)} .op-x{color:var(--x-c)} .op-y{color:var(--y-c)}
footer{margin-top:3.5rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.85rem}
</style>
</head>
<body>
<main class="wrap">
<header>
  <h1>Master tables</h1>
  <p class="lede">The universal table lists every input form in use, with its
  glyph and readings; each language's own table follows, stamped with the
  review state of its mapping. A language reaches full confidence only with a native or
  expert reviewer. Generated from <code>data/</code> by
  <code>scripts/gen_master.py</code>; the system is defined in
  <a href="index.html">the description</a>, and the
  <a href="play.html">playground</a> renders it live.</p>
</header>
<div style="display:flex;gap:1rem;align-items:center;flex-wrap:wrap;margin:1.4rem 0 0">
  <label for="table" style="font:600 .72rem/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)">table</label>
  <select id="table" autocomplete="off" style="font:600 .85rem var(--sans);color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:.5rem;padding:.4rem .6rem"></select>
</div>
'''


_C_BASES = 'ptkbdgfvszmnlrh'
_V_BASES = 'aeiou'
_OPS_ORDER = ['', 'j', 'c', 'q', 'x', 'y', 'jx', 'cx', 'qx', 'cy', 'jy', 'qy', 'yy', 'xy']


_LAST_ORDER = ['', 'j', 'c', 'q', 'x', 'y']


def _order_key(form):
    base, ops = form[0], form[1:]
    isv = base in _V_BASES
    last = ops[-1] if ops else ''
    mid = ops[:-1]
    last_rank = _LAST_ORDER.index(last) if last in _LAST_ORDER else len(_LAST_ORDER)
    mid_rank = _LAST_ORDER.index(mid) if mid in _LAST_ORDER else len(_LAST_ORDER)
    base_rank = (_V_BASES if isv else _C_BASES).index(base)
    return (len(form), 1 if form in SEQ else 0, last_rank, isv, mid_rank, base_rank)


def form_cell(form):
    """Input shown as stem plus its last operator, with the previous form
    where the stem is itself modified; sequences show as plain letters."""
    if form in SEQ or len(form) == 1:
        return f'<code>{form}</code>'
    stem, last = form[:-1], form[-1]
    s = f'<code>{stem}</code><span class="plus op-{last}">+{last}</span>'
    if len(stem) >= 2 and not form.endswith('xy'):
        s += (f'<span class="prev">from <span class="ug">'
              f'{engine.render(stem)}</span></span>')
    return s


def universal_table(agg, shares):
    rows = []
    for form, reads in agg.items():
        if form in SEQ or 'w' in form:
            continue    # sequences are two forms in a row; w is length riding free
        sh = shares.get(form, {})
        prim = next((i for i, v in sh.items() if v == 'primary'), None)
        rd = sorted(reads.items(),
                    key=lambda kv: (0 if nfd(kv[0]) == prim else 1, -kv[1][1]))
        rows.append((_order_key(form), form, form_type(form), rd))
    rows.sort()
    out = ['<section id="sec-universal">', '<h2>The universal table</h2>',
           '<p class="lede">The form inventory: base + up to two operators. '
           'Length (<code>w</code>) rides free on any of these, and diphthongs are '
           'two forms in a row; neither is a form of its own.</p>',
           '<div class="opswrap"><table>',
           '<tr><th>input</th><th>glyph</th><th>type</th>'
           '<th>primary reading</th><th>other readings</th></tr>']
    grp = 0
    for key, form, t, rd in rows:
        keys = key[0]
        if keys != grp:
            grp = keys
            out.append(f'<tr class="grp"><th colspan="5">'
                       f'{keys} keystroke{"s" if keys > 1 else ""}</th></tr>')
        sh = shares.get(form, {})
        ipa, (n, s, codes) = rd[0]
        primary = (f'<a class="wref ug" href="{ipa_names.url(ipa)}" target="_blank">{ipa}</a>'
                   f'<span class="rname">{ipa_names.name(ipa)}</span>'
                   f'<span class="st" title="{" ".join(sorted(codes))}">'
                   f'{n} language{"s" if n > 1 else ""} · {fmt(s)} native</span>')
        groups = ''
        for ipa, (n, s, codes) in rd[1:]:
            just = sh.get(nfd(ipa))
            lines = (''.join(f'<span class="just"><b>{c}</b> {just.get(c, "")}</span>'
                             for c in sorted(codes))
                     if isinstance(just, dict)
                     else f'<span class="just">{" ".join(sorted(codes))}</span>')
            groups += (f'<div class="rgroup">'
                       f'<a class="wref ug" href="{ipa_names.url(ipa)}" target="_blank">{ipa}</a>'
                       f'<span class="rname">{ipa_names.name(ipa)}</span>{lines}</div>')
        shown = form_cell(form)
        out.append(f'<tr><td>{shown}</td><td class="g">{engine.render(form)}</td>'
                   f'<td class="tt">{t}</td><td>{primary}</td><td>{groups}</td></tr>')
    out.append('</table></div></section>')
    return '\n'.join(out)


def language_tables():
    cons, vows, over, merges, review, _ = load_mapping()
    langs = load_languages()
    order = sorted(langs, key=lambda c: -langs[c]['speakers']['native'])
    toc, secs = [], []
    for code in order:
        d = langs[code]
        label, cls = STATES.get(review.get(code), STATES[None])
        toc.append(f'<a href="#{code}" class="{cls}"><b>{code}</b> {d["name"]}</a>')
        entries = []
        for sec, table in (('consonants', cons), ('vowels', vows)):
            for ipa, freq in d[sec].items():
                key = nfd(ipa)
                form = over.get(code, {}).get(key) or table.get(key)
                entries.append((_order_key(form), form, ipa, freq))
        entries.sort()
        rows, grp = [], 0
        for okey, form, ipa, freq in entries:
            keys = okey[0]
            if keys != grp:
                grp = keys
                rows.append(f'<tr class="grp"><th colspan="5">'
                            f'{keys} keystroke{"s" if keys > 1 else ""}</th></tr>')
            reading = (f'<a class="wref ug" href="{ipa_names.url(ipa)}" target="_blank">'
                       f'{ud.normalize("NFC", ipa)}</a>'
                       f'<span class="rname">{ipa_names.name(ipa)}</span>')
            rows.append(f'<tr><td>{form_cell(form)}</td>'
                        f'<td class="g">{engine.render(form)}</td>'
                        f'<td class="tt">{form_type(form)}</td>'
                        f'<td>{reading}</td>'
                        f'<td class="tt">{freq}</td></tr>')
        secs.append(
            f'<section id="sec-{code}" hidden data-name="{d["name"]}" data-state="{label}" data-cls="{cls}">'
            f'<h2>{d["name"]} <span class="tt">{code} · '
            f'{fmt(d["speakers"]["native"])} native</span>'
            f'<span class="badge {cls}">{label}</span></h2>\n'
            '<div class="opswrap"><table>'
            '<tr><th>input</th><th>glyph</th><th>type</th><th>reading</th><th>freq</th></tr>'
            + ''.join(rows) + '</table></div></section>')
    return ('', '\n'.join(secs))


def main():
    agg = aggregate()  # validates
    shares = load_mapping()[5]
    _, secs = language_tables()
    js = """
<script>
'use strict';
const sel=document.getElementById('table');
const secs=[...document.querySelectorAll('section[id^=sec-]')];
sel.innerHTML='<option value="universal" selected>universal</option>'+
  secs.filter(x=>x.id!=='sec-universal').map(x=>{
    const c=x.id.slice(4);
    return `<option value="${c}">${x.dataset.name}</option>`;}).join('');
function show(){
  for(const x of secs) x.hidden = (x.id!=='sec-'+sel.value);
}
function apply(){
  const h=location.hash.slice(1);
  sel.value = (h && document.getElementById('sec-'+h)) ? h : 'universal';
  show();
}
sel.addEventListener('change', ()=>{ history.replaceState(null,'','#'+sel.value); show(); });
window.addEventListener('hashchange', apply);
apply();
</script>"""
    html = (HEAD + universal_table(agg, shares) + '\n' + secs +
            '\n<footer>Diaphone · master tables · <a href="index.html">description</a> · '
            '<a href="play.html">playground</a> · <a href="fonts.html">fonts</a></footer>\n</main>'
            + js + '\n</body>\n</html>\n')
    out = os.path.join(ROOT, 'docs', 'master.html')
    open(out, 'w').write(html)
    print(f'mapping valid · {out}: {len(agg)} forms, {len(load_languages())} languages')


if __name__ == '__main__':
    main()
