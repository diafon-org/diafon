#!/usr/bin/env python3
"""Generate docs/master.html — the master tables.

The universal table: every input form in use, grouped by keystroke count,
with its glyph and its readings from the most to the least used (languages ·
native speakers). Then one table per language — IPA, frequency, input form,
glyph — stamped with the mapping's review state (non-reviewed · reviewed ·
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

C_POINTS = {'sj','zj','tq','dq','tc','dc','kx','gx','kq','hx','rc','tx','dx','nx','py','ky','gy'}
RETRO = {'ty','dy','ny','ly','ry'}
SPECIAL2 = {'tcy','tqy','dqy','tyy','dyy','ryy'}
V_POINTS = {'ij','ej','uj','oj','aj','ic','ec','uc','oc','ac','eq','iq','aq'}
SEQ = {'aix','aux','ojix','eix','oux','ojicx','ejix','eqicx','ajux'}
STATES = {'native': ('native-reviewed', 'st-nat'),
          'reviewed': ('reviewed', 'st-rev'),
          None: ('non-reviewed', 'st-non')}


def form_type(f):
    if len(f) == 1: return 'base'
    if f in C_POINTS or f in V_POINTS: return 'point'
    if f.endswith('yx') or f in SPECIAL2: return 'special'
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
    return cons, vows, over, merges, review


def load_languages():
    langs = {}
    for path in sorted(glob.glob(os.path.join(ROOT, 'data', 'languages', '*.yaml'))):
        d = yaml.safe_load(open(path))
        langs[d['code']] = d
    return langs


def aggregate():
    cons, vows, over, merges, _ = load_mapping()
    langs = load_languages()
    agg, errors = {}, []
    for code, d in langs.items():
        native = d['speakers']['native']
        taken = {}
        for sec, table in (('consonants', cons), ('vowels', vows)):
            for ipa, freq in d[sec].items():
                if freq == 'X':
                    continue
                key = nfd(ipa)
                form = over.get(code, {}).get(key) or table.get(key)
                if not form:
                    errors.append(f'{code}: unmapped {ipa}')
                    continue
                if form in taken:
                    pair = {key, nfd(taken[form])}
                    if pair not in merges.get(code, []):
                        errors.append(f'{code}: {ipa} and {taken[form]} both on {form}')
                        continue
                taken[form] = ipa
                e = agg.setdefault(form, {}).setdefault(ud.normalize('NFC', ipa), [0, 0.0])
                e[0] += 1
                e[1] += native
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
<title>Diaphone — Master Tables</title>
<style>
:root{
  --paper:#f5f6f8; --card:#ffffff; --sunken:#eef0f4; --ink:#1a1d24; --muted:#5b6472; --line:#dde1e8;
  --accent:#0e7c86; --good:#2f8f66; --warn:#b06f14;
  --serif:"Diaphone","Charis SIL","Gentium Plus","Noto Serif","Times New Roman",Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  --mono:"SF Mono","JetBrains Mono","Menlo","Consolas",monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#14161b; --card:#1b1e25; --sunken:#101216; --ink:#e9ecf1; --muted:#98a1b0; --line:#2a2e37;
  --accent:#3ec8cf; --good:#4fc79a; --warn:#e0a44a;
}}
:root[data-theme="dark"]{
  --paper:#14161b; --card:#1b1e25; --sunken:#101216; --ink:#e9ecf1; --muted:#98a1b0; --line:#2a2e37;
  --accent:#3ec8cf; --good:#4fc79a; --warn:#e0a44a;
}
@font-face{font-family:"Diaphone";src:url(diaphone.woff2) format("woff2");font-display:swap}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.55;font-size:15px}
.wrap{max-width:1020px;margin:0 auto;padding:clamp(1.4rem,4vw,3rem) clamp(1rem,4vw,2rem) 4rem}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(1.7rem,4.5vw,2.3rem);margin:0 0 .2rem}
h2{font-family:var(--serif);font-weight:600;font-size:1.3rem;margin:2.4rem 0 .4rem}
.lede{color:var(--muted);margin:.2rem 0 0;max-width:74ch}
a{color:var(--accent)}
code{font:600 .78em/1.4 var(--mono);color:var(--accent);background:var(--sunken);padding:.1em .32em;border-radius:.32em}
.ug{font-family:var(--serif)}
.opswrap{overflow-x:auto;margin:.8rem 0 0;border:1px solid var(--line);border-radius:14px;background:var(--card)}
table{border-collapse:collapse;width:100%;min-width:640px}
th{font:600 .66rem/1.1 var(--mono);letter-spacing:.04em;text-transform:uppercase;color:var(--muted);padding:.5rem .8rem;background:var(--sunken);text-align:left}
td{padding:.42rem .8rem;border-top:1px solid var(--line);vertical-align:top}
td.g{font-family:var(--serif);font-size:1.15rem}
.st{font:600 .68rem/1.3 var(--mono);color:var(--muted);white-space:nowrap}
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
.xrow{color:var(--muted);opacity:.6}
footer{margin-top:3.5rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.85rem}
</style>
</head>
<body>
<main class="wrap">
<header>
  <h1>Master tables</h1>
  <p class="lede">The universal table — every input form in use, its glyph and
  its readings — and every language's own table, stamped with the review state
  of its mapping. A language reaches full confidence only with a native or
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


def universal_table(agg):
    rows = []
    for form, reads in agg.items():
        if form in SEQ or 'w' in form:
            continue    # sequences are two forms in a row; w is length riding free
        rd = sorted(reads.items(), key=lambda kv: -kv[1][1])
        total = sum(s for _, (_, s) in reads.items())
        rows.append((len(form), -total, form, form_type(form), rd))
    rows.sort()
    max_r = max(len(r[4]) for r in rows)
    out = ['<section id="sec-universal">', '<h2>The universal table</h2>',
           '<p class="lede">The form inventory: base + up to two operators. '
           'Length (<code>w</code>) rides free on any of these, and diphthongs are '
           'two forms in a row — neither is a form of its own.</p>',
           '<div class="opswrap"><table>',
           '<tr><th>input</th><th>glyph</th><th>type</th>' +
           ''.join(f'<th>reading {i}</th>' for i in range(1, max_r + 1)) + '</tr>']
    grp = 0
    for keys, _, form, t, rd in rows:
        if keys != grp:
            grp = keys
            out.append(f'<tr class="grp"><th colspan="{3 + max_r}">'
                       f'{keys} keystroke{"s" if keys > 1 else ""}</th></tr>')
        cells = ''.join(f'<td><span class="ug">{ipa}</span> <span class="st">{n}·{fmt(s)}</span></td>'
                        for ipa, (n, s) in rd) + '<td></td>' * (max_r - len(rd))
        out.append(f'<tr><td><code>{form}</code></td><td class="g">{engine.render(form)}</td>'
                   f'<td class="tt">{t}</td>{cells}</tr>')
    out.append('</table></div></section>')
    return '\n'.join(out)


def language_tables():
    cons, vows, over, merges, review = load_mapping()
    langs = load_languages()
    order = sorted(langs, key=lambda c: -langs[c]['speakers']['native'])
    toc, secs = [], []
    for code in order:
        d = langs[code]
        label, cls = STATES.get(review.get(code), STATES[None])
        toc.append(f'<a href="#{code}" class="{cls}"><b>{code}</b> {d["name"]}</a>')
        rows = []
        for sec, table in (('consonants', cons), ('vowels', vows)):
            for ipa, freq in d[sec].items():
                key = nfd(ipa)
                if freq == 'X':
                    rows.append(f'<tr class="xrow"><td class="g">{ud.normalize("NFC", ipa)}</td>'
                                f'<td class="tt">X</td><td>—</td><td></td></tr>')
                    continue
                form = over.get(code, {}).get(key) or table.get(key)
                rows.append(f'<tr><td class="g">{ud.normalize("NFC", ipa)}</td>'
                            f'<td class="tt">{freq}</td><td><code>{form}</code></td>'
                            f'<td class="g">{engine.render(form)}</td></tr>')
        secs.append(
            f'<section id="sec-{code}" hidden data-name="{d["name"]}" data-state="{label}" data-cls="{cls}">'
            f'<h2>{d["name"]} <span class="tt">{code} · '
            f'{fmt(d["speakers"]["native"])} native</span>'
            f'<span class="badge {cls}">{label}</span></h2>\n'
            '<div class="opswrap"><table>'
            '<tr><th>ipa</th><th>freq</th><th>input</th><th>glyph</th></tr>'
            + ''.join(rows) + '</table></div></section>')
    return ('', '\n'.join(secs))


def main():
    agg = aggregate()  # validates
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
sel.value='universal';
sel.addEventListener('change', show);
show();
</script>"""
    html = (HEAD + universal_table(agg) + '\n' + secs +
            '\n<footer>Diaphone — master tables · <a href="index.html">description</a> · '
            '<a href="play.html">playground</a> · <a href="fonts.html">fonts</a></footer>\n</main>'
            + js + '\n</body>\n</html>\n')
    out = os.path.join(ROOT, 'docs', 'master.html')
    open(out, 'w').write(html)
    print(f'mapping valid · {out}: {len(agg)} forms, {len(load_languages())} languages')


if __name__ == '__main__':
    main()
