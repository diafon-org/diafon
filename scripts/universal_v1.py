#!/usr/bin/env python3
"""universal-v1 with the old names: the profile's engine (engine/, spec/
universal-v1.json) under the names the engine had before the split, and the
form-based view of the alphabet's stages, lexicons and mapping that the old
spec, the playground, the lessons and the ports' data are generated from.

  segments, tokenize, points, typed, form, render, glyph, inventory, stream
                      the profile engine
  stages, lexicon     the alphabet's stages and lexicons, in typed forms
                      (through the alphabet's Python reference: alphabet_ref)
  legacy_script, legacy_mapping, export
                      the script rules, the mapping and the lexicons as the
                      ports and the site's engine read them

The ports still carry this grammar in code (the whole letters, the flip
partners); they become table-driven with the next profile.

Usage: universal_v1.py "typed text"      -> prints the script
       universal_v1.py export <dir>      -> the lexicons in typed forms
"""
import os
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from engine import alphabet, profile
from engine.alphabet import Tok
from engine.engine import Engine, ParseError

ENGINE = Engine(profile.compiled('universal-v1'))

C_BASES = set('bdfghklmnprstvz')
V_BASES = set('aeiou')
BASES = C_BASES | V_BASES
OPS = set('cjqxwy')

# the grammar as the ports still carry it: forms that type a whole letter of
# the script, and the partner letter the flip is drawn on
WHOLE = {'tc': ('c', ()), 'dc': ('x', ()), 'tq': ('c', ('anchor',)), 'dq': ('x', ('anchor',)),
         'ix': ('j', ()), 'ux': ('w', ()), 'icx': ('w', ('flip',)), 'ucx': ('j', ('flip',)), 'aq': ('r', ('flip',))}
PARTNER = {'i': 'u', 'u': 'i', 'e': 'o', 'o': 'e', 'a': 'a'}

MARKS, ZWJ = alphabet.MARKS, alphabet.ZWJ
DESC = set(alphabet.SPEC['script']['descenders'])
TONES, TONE_OF, tone_signs = alphabet.TONES, alphabet.TONE_OF, alphabet.tone_signs

segments, tokenize, comp, points = ENGINE.segments, ENGINE.tokenize, ENGINE.comp, ENGINE.points
form, typed, glyph, render, stream = ENGINE.form, ENGINE.typed, ENGINE.glyph, ENGINE.render, ENGINE.stream


def compositions(form):
    """(small, capital) glyphs of a form's letter, a vowel's length with it,
    a consonant's doubling left out: what the font draws for that letter."""
    c, long, _ = comp(form[0].lower() + form[1:])
    long = long and c[0] in alphabet.VOWELS
    return alphabet.glyph(c, long), alphabet.glyph(c, long, caps=True)


def inventory():
    """Every valid single-segment form, lowercase, in the old engine's order."""
    out = []
    core_ops = sorted(OPS - {'w'})
    combos = [''] + core_ops + [a + b for a in core_ops for b in core_ops]
    for base in sorted(BASES):
        for ops in combos:
            for w in ('', 'w'):
                f = base + ops + w
                try:
                    comp(f)
                except ParseError:
                    continue
                out.append(f)
    return out


_SCRIPT_TABLE = {}


def script_table(used=()):
    """The script read back as forms: {glyph text: form} over the whole
    inventory, small and capitalized, a long consonant plain and joined."""
    key = frozenset(used)
    if key not in _SCRIPT_TABLE:
        table = {}
        inv = inventory()
        for f in [f for f in inv if f in key] + [f for f in inv if f not in key]:
            for x in (f, f[0].upper() + f[1:]):
                table.setdefault(glyph(x), x)
                table.setdefault(glyph(x, join=True), x)
        _SCRIPT_TABLE[key] = table
    return _SCRIPT_TABLE[key]


def read(text, table):
    """Read a text back through a {spelling: form} table, longest match
    first (a letter takes its marks with it), tones attached to the form
    before them; anything the table does not cover is raw. -> list of
    ('form', form, tones, matched) and ('raw', ch)."""
    text = ud.normalize('NFC', text)
    maxlen = max((len(k) for k in table), default=1)
    out, i, n = [], 0, len(text)
    while i < n:
        s = alphabet.match(text, i, table, maxlen)
        if s is None:
            out.append(('raw', text[i]))
            i += 1
            continue
        tones, i = alphabet.read_tones(text, i + len(s))
        out.append(('form', table[s], tones, s))
    return out


def legacy_script():
    """The script rules as the ports knew them before the split: the whole
    letters and the flip partners by form, the tones by digit."""
    S = alphabet.SPEC['script']
    whole = {f: alphabet.glyph(c) for f, c in WHOLE.items()}
    # the ports call the third consonant mark `reverse`, as it was before it became the double dot below
    marks = {('reverse' if k == 'twodots' else k): v for k, v in S['marks'].items()}
    return {'descenders': S['descenders'], 'whole_letters': whole, 'marks': marks,
            'flip_partner': dict(PARTNER),
            'tones': {str(t['number']): {'contour': name, 'sign': t['sign']} for name, t in S['tones'].items()}}


# everything below reads languages through the alphabet's Python reference
import alphabet_ref     # noqa: E402  (puts the alphabet checkout's scripts on the path)
import script           # noqa: E402


# ---- the stages and lexicons as they were before the split: in typed forms ----
#
# The alphabet's stages.py and lexicon.py work in points and script text.
# What still thinks in forms (the old spec, the playground, the lessons, the
# ports) reads them through these two namespaces, which keep the old names
# and the old meaning: `transport` is typed text.

import re as _re
import types as _types


def legacy_mapping():
    """data/mapping.yaml as it was before the split: every point name back
    to the form that types it (a sequence to its forms, joined)."""
    import yaml
    m = yaml.safe_load(open(os.path.join(alphabet_ref.PATH, 'data', 'mapping.yaml'), encoding='utf-8'))

    def f(value):
        names = value if isinstance(value, list) else [value]
        return ''.join(form(Tok(*script.point(str(n)))) for n in names)
    out = dict(m)
    for sec in ('consonants', 'vowels'):
        out[sec] = {k: f(v) for k, v in m[sec].items()}
    out['overrides'] = {c: {k: f(v) for k, v in d.items()} for c, d in m['overrides'].items()}
    out['areas'] = {f(a): dict(d, **({'split': {f(sf): qs for sf, qs in d['split'].items()}} if d.get('split') else {}))
                    for a, d in (m.get('areas') or {}).items()}
    out['shares'] = {f(k): d for k, d in (m.get('shares') or {}).items()}
    return out


def language_forms(code):
    """-> {form: [(ipa, frequency), ...]} for one language, from the mapping (X included)."""
    import forms as gen_master
    cons, vows, over, _, _, _ = gen_master.load_mapping()
    d = gen_master.load_languages()[code]
    byform = {}
    for sec, table in (('consonants', cons), ('vowels', vows)):
        for ipa, freq in d[sec].items():
            k = gen_master.nfd(ipa)
            f = over.get(code, {}).get(k) or table.get(k)
            byform.setdefault(f, []).append((ud.normalize('NFC', ipa), freq))
    return byform


def _key_form(k):
    return form(Tok(k[0], k[1]))


def _entry_form(entry):
    return ''.join(form(Tok(c, long, caps)) for c, long, caps in entry)


def typed_lexicon(n):
    """A lexicon (data/lexicon/<code>.json) with its Diafon words in typed forms."""
    T = lambda s: typed(script.read(s))
    pair = lambda v: [T(v[0]), v[1]]
    d = dict(n)
    if 'hand' in n:                                  # the loan dictionary
        d['hand'] = {k: pair(v) for k, v in n['hand'].items()}
        d['read'] = {lc: {k: T(v) for k, v in r.items()} for lc, r in n['read'].items()}
        d['hosts'] = {h: {'read': {k: pair(v) for k, v in e['read'].items()},
                          'write': {T(k): v for k, v in e['write'].items()}} for h, e in n['hosts'].items()}
    elif 'read' in n:
        d['read'] = {k: T(v) for k, v in n['read'].items()}
    for name in ('write', 'choices'):
        if name in n:
            d[name] = {T(k): v for k, v in n[name].items()}
    if 'sample' in n:
        d['sample'] = T(n['sample'])
    return d


def _legacy_stages():
    import stages as S
    import lexicon as X
    loaded, lexes, used = {}, {}, []

    def load(code):
        if code not in loaded:
            n = S.load(code)
            d = dict(n)
            d['forms'] = {_key_form(k): sp for k, sp in n['spell'].items()}
            for name in ('caps', 'before_i', 'before_vowel'):
                d[name] = {_key_form(k): sp for k, sp in n[name].items()}
            d['sample'] = typed(script.read(n['sample']))
            d['read'] = {sp: typed(script.read(v)) for sp, v in n['read'].items()}
            d['lexicon'] = lex(code)
            for name in ('points', 'spell'):
                d.pop(name)
            loaded[code] = d
        return loaded[code]

    def new(stage):
        return S.load(stage if isinstance(stage, str) else stage['code'])

    def render(text, code, strict=False):
        try:
            return S.render(points(text, strict), new(code), strict)
        except S.StageError as e:
            raise ParseError(str(e))

    def render_letters(text, stage, strict=False):
        return S.render_letters(points(text, strict), new(stage), strict)

    def spell(stage, f):
        c, long, caps = comp(f)
        return S.spell(new(stage), Tok(c, long, caps))

    def table(stage, fallback=True, aliases=True):
        return {sp: _entry_form(e) for sp, e in S.table(new(stage), fallback, aliases).items()}

    def read_letters(text, tbl):
        return ''.join(t[1] if t[0] == 'raw' else t[1] + t[2] for t in read(text, tbl))

    def read_word(word, stage):
        toks, how = S.read_word(word, new(stage))
        return typed(toks), how

    def parse(text, source):
        return text if source == 'transport' else typed(S.parse(text, source))

    def convert(text, source, target):
        if source == target and source.startswith('stage:'):
            return S.convert(text, source, target)
        toks = points(text, strict=False) if source == 'transport' else S.parse(text, source)
        return typed(toks) if target == 'transport' else S.write(toks, target)

    def sources():
        return ['transport'] + S.sources()

    def _typed_score(text):
        letters = lambda s: sum(1 for ch in s if ud.category(ch)[0] in 'LM')
        total = letters(ud.normalize('NFC', text)) or 1
        segs = segments(text, strict=False)
        covered = sum(letters(s['src']) for s in segs if s['kind'] == 'form')
        wins = covered == total and any(s['kind'] == 'form' and len(s['form']) > 1 for s in segs)
        return [('transport', covered / total, wins)]

    def detect(text, prefer=None):
        return S.detect(text, prefer, other=_typed_score(text))

    def source_for(text, target, prefer=None):
        return S.source_for(text, target, prefer, other=_typed_score(text))

    def used_forms():
        if not used:
            import forms as gen_master
            used.append(frozenset(gen_master.aggregate()))
        return used[0]

    def lex(code):
        """A lexicon with its Diafon words in typed forms."""
        if code not in lexes:
            n = X.lex(code)
            lexes[code] = None if n is None else typed_lexicon(n)
        return lexes[code]

    def lex_read_word(word, code):
        t = X.read_word(word, code)
        return None if t is None else typed(script.read(t))

    def lex_write_word(t, code):
        hit = X.write_word(points(t, strict=False), code)
        return (hit[0], typed(hit[1])) if isinstance(hit, tuple) else hit

    def loan(word, code):
        hit = X.loan(word, code)
        return None if hit is None else (typed(script.read(hit[0])), hit[1])

    def choices(t_tone, code='zh'):
        return X.choices(script.write(points(t_tone, strict=False)), code)

    stages = _types.SimpleNamespace(
        codes=S.codes, load=load, render=render, render_letters=render_letters, spell=spell, table=table,
        read_letters=read_letters, read_word=read_word, parse=parse, convert=convert, sources=sources,
        detect=detect, source_for=source_for, validate=S.validate, language_forms=language_forms,
        used_forms=used_forms, script_table=lambda: script_table(used_forms()))
    lexicon = _types.SimpleNamespace(
        codes=X.codes, lex=lex, read_word=lex_read_word, write_word=lex_write_word, loan=loan, choices=choices,
        recase=lambda out, original: (out[0].upper() + out[1:]) if out and original and original[0].isupper() else out,
        WORD=X.WORD, WORD_T=_re.compile(r'[A-Za-z]+\d*'), LEX=X.LEX)
    return stages, lexicon


_LEGACY = None


def __getattr__(name):
    """universal_v1.stages and universal_v1.lexicon: built on first use."""
    global _LEGACY
    if name in ('stages', 'lexicon'):
        if _LEGACY is None:
            _LEGACY = _legacy_stages()
        return _LEGACY[0] if name == 'stages' else _LEGACY[1]
    raise AttributeError(name)


def export(out_dir):
    """The lexicons in typed forms: <code>.json, for the JavaScript engine and the ports' vector checks."""
    import json
    import lexicon as X
    os.makedirs(out_dir, exist_ok=True)
    for code in X.codes():
        d = typed_lexicon(json.load(open(os.path.join(X.LEX, f'{code}.json'), encoding='utf-8')))
        json.dump(d, open(os.path.join(out_dir, f'{code}.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, separators=(',', ':'))
    print(f'{out_dir}: {len(X.codes())} lexicons in typed forms')


if __name__ == '__main__':
    if sys.argv[1:2] == ['export']:
        export(sys.argv[2])
    else:
        print(render(' '.join(sys.argv[1:])))
