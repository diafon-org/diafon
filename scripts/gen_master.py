#!/usr/bin/env python3
"""Generate the master tables: docs/.include/master-tables.html, the body of
the Master tables page (docs/master.md, where the try-out and the font switch
live; docs/assets/master.js drives them).

The universal table: every input form in use, grouped by keystroke count,
with its glyph and its readings from the most to the least used (languages ·
native speakers). Then one table per language (IPA, frequency, input form,
glyph), stamped with the mapping's review state (non-reviewed · reviewed ·
native-reviewed) from data/mapping.yaml.

Validation as before: every non-X phoneme mapped; no within-language form
collision outside `merges`.
"""
import glob
import json
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine
import ipa_names

C_POINTS = {'sj','zj','tq','dq','tc','dc','kx','gx','kq','hx','rc','tx','dx','nx','py','ky','gy'}
RETRO = {'ty','dy','ny','sjy','zjy','tqy','dqy'}  # the stops and the flipped hush
SPECIAL2 = {'tcy','dcy'}
V_POINTS = {'ij','ej','uj','oj','aj','ic','ec','uc','oc','ac','eq','iq','aq'}
SEQ = {'aix','aux','ojix','eix','oux','ojicx','ejix','eqicx','ajux','tyh','dyh','rch','pf','ph','th','kh','bh','dh','gh','tch','tqh','dqh','tqyh'}
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


def glyph_cell(form):
    return (f'<td class="g"><span>{engine.render(form)}</span> '
            f'<span>{engine.render(form[0].upper() + form[1:])}</span></td>')


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
    out = ['<section id="sec-universal" data-name="universal">', '<h2 id="universal">The universal table</h2>',
           '<p class="lede">The form inventory: base + up to two operators. '
           'Length (<code>w</code>) rides free on any of these, and diphthongs are '
           'two forms in a row; neither is a form of its own.</p>',
           '<div class="mt-wrap"><table class="mt">',
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
        primary = (f'<a class="wref ug" href="{ipa_names.url(ipa)}" target="_blank">/{ipa}/</a>'
                   f'<a class="rname" href="{ipa_names.url(ipa)}" target="_blank">{ipa_names.name(ipa)}</a>'
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
                       f'<a class="wref ug" href="{ipa_names.url(ipa)}" target="_blank">/{ipa}/</a>'
                       f'<a class="rname" href="{ipa_names.url(ipa)}" target="_blank">{ipa_names.name(ipa)}</a>{lines}</div>')
        shown = form_cell(form)
        out.append(f'<tr data-form="{form}"><td>{shown}</td>{glyph_cell(form)}'
                   f'<td class="tt">{t}</td><td>{primary}</td><td>{groups}</td></tr>')
    out.append('</table></div></section>')
    return '\n'.join(out)


def extras():
    """Per language: its spelling stage's state and its lexicon, if any."""
    stage = {}
    for fn in glob.glob(os.path.join(ROOT, 'data', 'stages', '*.yaml')):
        d = yaml.safe_load(open(fn))
        stage[d['code']] = d.get('state', 'draft')
    lexica = {}
    for fn in glob.glob(os.path.join(ROOT, 'data', 'lexicon', '*.json')):
        d = json.load(open(fn))
        n = max(len(d.get('read') or {}), len(d.get('write') or {}))
        lexica[d['code']] = f'{d.get("kind", "")} lexicon, {n:,} entries'
    return stage, lexica


def overview():
    """The languages at a glance: what each has and how far it is reviewed."""
    review = load_mapping()[4]
    langs = load_languages()
    stage, lexica = extras()
    n_rev = sum(1 for c in langs if review.get(c))
    n_nat = sum(1 for c in langs if review.get(c) == 'native')
    rows = []
    for code in sorted(langs, key=lambda c: -langs[c]['speakers']['native']):
        d = langs[code]
        label, cls = STATES.get(review.get(code), STATES[None])
        n_c = sum(1 for v in d['consonants'].values() if v != 'X')
        n_v = sum(1 for v in d['vowels'].values() if v != 'X')
        rows.append(f'<tr data-goto="{code}"><td><b>{d["name"]}</b> <span class="tt">{code}</span></td>'
                    f'<td class="tt">{fmt(d["speakers"]["native"])}</td><td class="tt">{n_c} + {n_v}</td>'
                    f'<td><span class="badge {cls}">{label}</span></td>'
                    f'<td class="tt">{stage.get(code, "")}</td><td class="tt">{lexica.get(code, "")}</td></tr>')
    return ('<section id="sec-languages" hidden data-name="all languages: status">\n'
            '<h2 id="languages">The languages</h2>\n'
            f'<p class="lede">{len(langs)} languages carry a phoneme inventory and a mapping; '
            f'{n_rev} mappings are reviewed, {n_nat} of them by a native speaker; {len(stage)} '
            f'have a draft spelling stage; {len(lexica)} have a lexicon. A mapping is '
            '<b>non-reviewed</b> as drafted, <b>reviewed</b> against the literature, and '
            '<b>native-reviewed</b> once a native or expert reviewer has checked it; every '
            'language needs the last. Click a language for its table.</p>\n'
            '<div class="mt-wrap"><table class="mt">'
            '<tr><th>language</th><th>native speakers</th><th>phonemes (C + V)</th><th>mapping</th>'
            '<th>spelling stage</th><th>lexicon</th></tr>' + ''.join(rows) + '</table></div></section>')


def language_tables():
    cons, vows, over, merges, review, _ = load_mapping()
    langs = load_languages()
    stage, lexica = extras()
    order = sorted(langs, key=lambda c: -langs[c]['speakers']['native'])
    secs = []
    for code in order:
        d = langs[code]
        label, cls = STATES.get(review.get(code), STATES[None])
        has = [f'spelling stage: {stage[code]}' if code in stage else 'no spelling stage yet']
        if code in lexica:
            has.append(lexica[code])
        byform = {}
        for sec, table in (('consonants', cons), ('vowels', vows)):
            for ipa, freq in d[sec].items():
                key = nfd(ipa)
                form = over.get(code, {}).get(key) or table.get(key)
                byform.setdefault(form, []).append((ipa, freq))
        rows, grp = [], 0
        rank = {'L': 0, 'M': 1, 'S': 2, 'X': 3}
        for form in sorted(byform, key=_order_key):
            keys = _order_key(form)[0]
            if keys != grp:
                grp = keys
                rows.append(f'<tr class="grp"><th colspan="5">'
                            f'{keys} keystroke{"s" if keys > 1 else ""}</th></tr>')
            pairs = sorted(byform[form], key=lambda p: rank[p[1]])
            reading = ' = '.join(
                f'<a class="wref ug" href="{ipa_names.url(i)}" target="_blank">'
                f'/{ud.normalize("NFC", i)}/</a>' for i, _ in pairs)
            reading += (f'<a class="rname" href="{ipa_names.url(pairs[0][0])}"'
                        f' target="_blank">{ipa_names.name(pairs[0][0])}</a>')
            if len(pairs) > 1:
                reading += '<span class="rname">one phoneme, merged</span>'
            rows.append(f'<tr data-form="{form}"><td>{form_cell(form)}</td>{glyph_cell(form)}'
                        f'<td class="tt">{form_type(form)}</td>'
                        f'<td>{reading}</td>'
                        f'<td class="tt">{pairs[0][1]}</td></tr>')
        secs.append(
            f'<section id="sec-{code}" hidden data-name="{d["name"]}" data-state="{label}" data-cls="{cls}">'
            f'<h2 id="{code}">{d["name"]} <span class="tt">{code} · '
            f'{fmt(d["speakers"]["native"])} native</span>'
            f'<span class="badge {cls}">{label}</span></h2>\n'
            f'<p class="lede">{" · ".join(has)}</p>\n'
            '<div class="mt-wrap"><table class="mt">'
            '<tr><th>input</th><th>glyph</th><th>type</th><th>reading</th><th>freq</th></tr>'
            + ''.join(rows) + '</table></div></section>')
    return '\n'.join(secs)


def main():
    agg = aggregate()  # validates
    shares = load_mapping()[5]
    html = universal_table(agg, shares) + '\n' + overview() + '\n' + language_tables() + '\n'
    out = os.path.join(ROOT, 'docs', '.include', 'master-tables.html')
    open(out, 'w').write(html)
    print(f'mapping valid · {out}: {len(agg)} forms, {len(load_languages())} languages')


if __name__ == '__main__':
    main()
