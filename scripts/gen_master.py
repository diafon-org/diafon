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
SEQ = {'aix','aux','ojix','oix','oicx','ecicx','ocux','eix','oux','ojicx','ejix','eqicx','ajux','tyh','dyh','rch','pf','ph','th','kh','bh','dh','gh','tch','tqh','dqh','tqyh'}
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
    area_rule(m, vows, over, merges, shares)
    return cons, vows, over, merges, review, shares


def quality(ipa):
    """The vowel quality a symbol's area is decided by: length and nasality
    stripped, a sequence by its nucleus."""
    return ipa.replace('ː', '').replace('\u0303', '')[0]


def area_rule(m, vows, over, merges, shares):
    """The vowel areas (mapping.yaml `areas`): a vowel writes its area's form
    unless its language contrasts it with another vowel on that same form;
    then the one listed under the area's `split` takes the split form, through
    length and nasality. Fills `over`, and the readings each area form and
    split form carries into `shares`."""
    areas = m.get('areas') or {}
    split = {}                                  # quality -> (area form, split form)
    for area, a in areas.items():
        for sf, qs in (a.get('split') or {}).items():
            for q in qs:
                split[nfd(q)] = (area, sf)

    def primary(form, ipa):
        reads = shares.setdefault(form, {})
        if not any(v == 'primary' for v in reads.values()):
            reads[ipa] = 'primary'
    for ipa, f in vows.items():
        q = quality(ipa)
        if areas.get(vows.get(q), {}).get('core') == q:
            primary(f, ipa)
        if q in split:
            area, sf = split[q]
            if nfd(areas[area]['split'][sf][0]) == q:     # the split's reference value
                primary(sf + f[len(area):], ipa)

    for code, d in load_languages().items():
        lang = over.setdefault(code, {})
        byform = {}
        for ipa, freq in d['vowels'].items():
            k = nfd(ipa)
            f = lang.get(k) or vows.get(k)
            if f and freq != 'X':
                byform.setdefault(f, []).append(k)
        for f, ks in byform.items():
            if len(ks) < 2 or (len(ks) == 2 and set(ks) in merges.get(code, [])):
                continue
            for k in ks:
                if k in lang or quality(k) not in split:
                    continue
                area, sf = split[quality(k)]
                assert f.startswith(area), f'{code}: {k} on {f}, outside its area {area}'
                lang[k] = sf + f[len(area):]
        # a split, once the language makes it, is how it writes that vowel
        # everywhere: German ɔ is ọ in Gott and in Leute (ọj̈) alike
        splitq = {quality(k) for k, f in lang.items() if quality(k) in split
                  and f.startswith(split[quality(k)][1])}
        for ipa in d['vowels']:
            k = nfd(ipa)
            if k in lang or quality(k) not in splitq:
                continue
            area, sf = split[quality(k)]
            f = vows.get(k)
            if f and f.startswith(area):
                lang[k] = sf + f[len(area):]
        for ipa in d['vowels']:
            k = nfd(ipa)
            f = lang.get(k) or vows.get(k)
            reads = shares.get(f, {})
            if f and reads.get(k) != 'primary':
                area = vows.get(quality(k))
                shares.setdefault(f, {}).setdefault(k, {}).setdefault(code, f'the {area} area')


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
    """Speakers, in millions, as the rough figure it is: ~3.8B, ~13M, ~1.1M."""
    if not m:
        return 'none'
    if m >= 1000:
        return f'~{m/1000:.1f}B'
    return f'~{m:.1f}M' if m < 10 else f'~{m:.0f}M'


def facts(groups):
    """A row of small figure tiles in labelled groups: [(label, [(value, what), ...]), ...]."""
    out = ''.join(f'<div class="fgroup"><span class="flabel">{label}</span><div class="ftiles">'
                  + ''.join(f'<div class="ft"><b>{v}</b><span>{w}</span></div>' for v, w in tiles)
                  + '</div></div>' for label, tiles in groups)
    return f'<div class="facts">{out}</div>'


def lang_name(d, tag='span'):
    """A language by its own name, its English name small after it."""
    own, en = d.get('native_name') or d['name'], d['name']
    return own if own == en else f'{own} <{tag} class="en-name">{en}</{tag}>'


def plain_name(d):
    own, en = d.get('native_name') or d['name'], d['name']
    return own if own == en else f'{own} · {en}'


def kind(form):
    """consonant, vowel or glide: the kind of sound, in plain words."""
    if form in {'ix', 'ux', 'icx', 'ucx'}:
        return 'glide'
    return 'vowel' if form[0] in _V_BASES else 'consonant'


import functools


@functools.lru_cache(None)
def _op_gloss():
    """Each operator's job, as the main page states it: on a consonant · on a vowel."""
    from gen_site import OPS
    out = {}
    for op, (cons, vow) in OPS.items():
        out[op] = cons[0] if not vow or vow[0] == cons[0] else f'{cons[0]} · {vow[0]}'
    out['h'] = 'aspirated or breathy'
    return out



def group_rows(form, state, cols):
    """The group headers a row opens: the keystrokes, then the operator the form ends in."""
    keys, last = len(form), (form[-1] if len(form) > 1 else '')
    out = []
    if keys != state.get('keys'):
        state['keys'], state['last'] = keys, None
        out.append(f'<tr class="grp"><th colspan="{cols}">{keys} keystroke{"s" if keys > 1 else ""}</th></tr>')
    if keys > 1 and last != state.get('last'):
        state['last'] = last
        out.append(f'<tr class="sub"><th colspan="{cols}"><span class="op op-{last}">{last}</span> {_op_gloss().get(last, "")}</th></tr>')
    return out


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
    langs = load_languages()
    name = lambda c: lang_name(langs[c]) if c in langs else c
    total = sum(d['speakers']['native'] for d in langs.values())
    out = ['<section id="sec-universal" data-name="Diafon">', '<h2 id="universal">Diafon: every letter in use</h2>',
           facts([('covers', [(len(langs), 'languages'), (fmt(total), 'native speakers')]),
                  ('letters in use', [(len(rows), 'letters')])]),
           '<p class="lede">Every letter any language uses, grouped by how many keys it takes, then by '
           'operator. Long sounds and diphthongs are not listed: a long sound adds '
           '<code>w</code>, and a diphthong is two letters in a row.</p>',
           '<div class="mt-wrap"><table class="mt">',
           '<tr><th>typed</th><th>Diafon</th><th>kind</th>'
           '<th>main reading</th><th>other readings</th></tr>']
    state = {}
    for key, form, t, rd in rows:
        out += group_rows(form, state, 5)
        sh = shares.get(form, {})
        ipa, (n, s, codes) = rd[0]
        primary = (f'<a class="wref ug" href="{ipa_names.url(ipa)}" target="_blank">/{ipa}/</a>'
                   f'<a class="rname" href="{ipa_names.url(ipa)}" target="_blank">{ipa_names.name(ipa)}</a>'
                   f'<span class="st">{n} language{"s" if n > 1 else ""} · {fmt(s)} native speakers</span>')
        groups = ''
        for ipa, (n, s, codes) in rd[1:]:
            lines = f'<span class="just">{", ".join(name(c) for c in sorted(codes, key=lambda c: langs[c]["name"] if c in langs else c))}</span>'
            groups += (f'<div class="rgroup">'
                       f'<a class="wref ug" href="{ipa_names.url(ipa)}" target="_blank">/{ipa}/</a>'
                       f'<a class="rname" href="{ipa_names.url(ipa)}" target="_blank">{ipa_names.name(ipa)}</a>{lines}</div>')
        shown = form_cell(form)
        out.append(f'<tr data-form="{form}"><td>{shown}</td>{glyph_cell(form)}'
                   f'<td class="tt">{kind(form)}</td><td>{primary}</td><td>{groups}</td></tr>')
    out.append('</table></div>')
    out.append(overview())
    out.append('</section>')
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
    """The languages at a glance, inside the Diafon view: a row opens that language."""
    review = load_mapping()[4]
    langs = load_languages()
    rows = []
    for code in sorted(langs, key=lambda c: -langs[c]['speakers']['native']):
        d = langs[code]
        n_c = sum(1 for v in d['consonants'].values() if v != 'X')
        n_v = sum(1 for v in d['vowels'].values() if v != 'X')
        tag = ' <span class="rev">reviewed</span>' if review.get(code) else ''
        rows.append(f'<tr data-goto="{code}"><td><b>{lang_name(d)}</b>{tag}</td>'
                    f'<td class="tt">{fmt(d["speakers"]["native"])}</td><td class="tt">{fmt(d["speakers"]["total"])}</td>'
                    f'<td class="tt">{n_c}</td><td class="tt">{n_v}</td></tr>')
    return ('<h2 id="languages">The languages</h2>\n'
            f'<p class="lede">{len(langs)} languages so far. Pick one for its own table. A mapping marked '
            '<span class="rev">reviewed</span> has been checked against the literature or by a native speaker.</p>\n'
            '<div class="mt-wrap"><table class="mt langs">'
            '<tr><th rowspan="2">language</th><th colspan="2">speakers</th><th colspan="2">phonemes used</th></tr>'
            '<tr><th>native</th><th>overall</th><th>consonants</th><th>vowels</th></tr>' + ''.join(rows) + '</table></div>')


FREQ = {'L': 'frequent', 'M': 'ordinary', 'S': 'infrequent', 'X': 'marginal or in loans'}


def language_tables():
    cons, vows, over, merges, review, _ = load_mapping()
    langs = load_languages()
    stage, lexica = extras()
    order = sorted(langs, key=lambda c: -langs[c]['speakers']['native'])
    secs = []
    for code in order:
        d = langs[code]
        byform = {}
        for sec, table in (('consonants', cons), ('vowels', vows)):
            for ipa, freq in d[sec].items():
                key = nfd(ipa)
                form = over.get(code, {}).get(key) or table.get(key)
                byform.setdefault(form, []).append((ipa, freq))
        rows, state = [], {}
        rank = {'L': 0, 'M': 1, 'S': 2, 'X': 3}
        for form in sorted(byform, key=_order_key):
            rows += group_rows(form, state, 5)
            pairs = sorted(byform[form], key=lambda p: rank[p[1]])
            reading = ' = '.join(
                f'<a class="wref ug" href="{ipa_names.url(i)}" target="_blank">'
                f'/{ud.normalize("NFC", i)}/</a>' for i, _ in pairs)
            reading += (f'<a class="rname" href="{ipa_names.url(pairs[0][0])}"'
                        f' target="_blank">{ipa_names.name(pairs[0][0])}</a>')
            if len(pairs) > 1:
                reading += '<span class="rname">one phoneme, merged</span>'
            rows.append(f'<tr data-form="{form}"><td>{form_cell(form)}</td>{glyph_cell(form)}'
                        f'<td class="tt">{kind(form)}</td>'
                        f'<td>{reading}</td>'
                        f'<td class="tt">{FREQ.get(pairs[0][1], "")}</td></tr>')
        n_c = sum(1 for v in d['consonants'].values() if v != 'X')
        n_v = sum(1 for v in d['vowels'].values() if v != 'X')
        secs.append(
            f'<section id="sec-{code}" hidden data-name="{plain_name(d)}">'
            f'<h2 id="{code}">{lang_name(d)}</h2>\n'
            + facts([('speakers', [(fmt(d["speakers"]["native"]), 'native'), (fmt(d["speakers"]["total"]), 'overall')]),
                     ('phonemes used', [(n_c, 'consonants'), (n_v, 'vowels')])]) + '\n'
            '<div class="mt-wrap"><table class="mt">'
            '<tr><th>typed</th><th>Diafon</th><th>kind</th><th>reading</th><th>how common</th></tr>'
            + ''.join(rows) + '</table></div></section>')
    return '\n'.join(secs)


def main():
    agg = aggregate()  # validates
    shares = load_mapping()[5]
    html = universal_table(agg, shares) + '\n' + language_tables() + '\n'
    out = os.path.join(ROOT, 'docs', '.include', 'master-tables.html')
    open(out, 'w').write(html)
    print(f'mapping valid · {out}: {len(agg)} forms, {len(load_languages())} languages')


if __name__ == '__main__':
    main()
