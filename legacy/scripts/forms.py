#!/usr/bin/env python3
"""The alphabet's mapping by typed form (universal-v1): which form writes
which sound of which language, with the vowel areas applied, and the form
classes the tables and the lessons sort by. The sounds and points are the
alphabet's (its data/mapping.yaml and data/languages, through alphabet_ref);
only the forms are this repository's.

  load_mapping()     (consonants, vowels, overrides, merges, review, shares) by form
  load_languages()   the alphabet's language files
  aggregate()        {form: {ipa: [languages, speakers, codes]}}
  form_type(form)    base, point, special, retro, sequence, glide, long, nasal, shift, soft
"""
import glob
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import alphabet_ref
import universal_v1

C_POINTS = {'sj','zj','tq','dq','tc','dc','kx','gx','kq','hx','rc','tx','dx','nx','py','ky','gy'}
RETRO = {'ty','dy','ny','sjy','zjy','tqy','dqy'}  # the stops and the flipped hush
SPECIAL2 = {'tcy','dcy'}
V_POINTS = {'ij','ej','uj','oj','aj','ic','ec','uc','oc','ac','eq','iq','aq'}
SEQ = {'aix','aux','ojix','oix','oicx','ecicx','ocux','eix','oux','ojicx','ejix','eqicx','ajux','tyh','dyh','rch','pf','ph','th','kh','bh','dh','gh','tch','tqh','dqh','tqyh'}
STATES = {'reviewed': ('reviewed', 'st-rev'),
          None: ('not reviewed', 'st-non')}


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
    m = universal_v1.legacy_mapping()
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
    for path in sorted(glob.glob(os.path.join(alphabet_ref.PATH, 'data', 'languages', '*.yaml'))):
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


_C_BASES = 'ptkbdgfvszmnlrh'
_V_BASES = 'aeiou'
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


