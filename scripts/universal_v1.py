#!/usr/bin/env python3
"""universal-v1: the typing Diafon had before the split (split.md), as a
bridge. TEMPORARY: it keeps the site's typing pages building until the
site is split (split.md, P4; tests/test_no_input.py lists what is pending).
The typing itself lives in diafon-input, as the profile universal-v1.

The grammar: 20 bases, 6 operators; an operator never starts a segment, a
base always does. A form carries at most two of c j q x y; w (length) rides
free after them; trailing digits are tones. Case is orthographic: an
uppercase base letter capitalizes its point, operators read the same in
either case.

  comp(form)        a form -> (composition, long, caps), by the grammar
  points(text)      typed text -> the script's tokens (script.Tok)
  form(tok)         a token -> the form that types it
  typed(tokens)     tokens -> typed text
  render(text)      typed text -> script text: script.write(points(text))

and the old engine's names (segments, tokenize, glyph, inventory,
script_table, read, stream), for the callers that still think in forms.

Usage: universal_v1.py "typed text"   -> prints the script.
"""
import os
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import script
from script import Tok

C_BASES = set('bdfghklmnprstvz')
V_BASES = set('aeiou')
BASES = C_BASES | V_BASES
OPS = set('cjqxwy')

# forms that type a whole letter of the script, not a mark on their base
WHOLE = {'tc': ('c', ()), 'dc': ('x', ()), 'tq': ('c', ('anchor',)), 'dq': ('x', ('anchor',)), 'kq': ('q', ()),
         'ix': ('j', ()), 'ux': ('w', ()), 'icx': ('j', ('flip',)), 'ucx': ('w', ('flip',)), 'aq': ('r', ('flip',))}
PARTNER = {'i': 'u', 'u': 'i', 'e': 'o', 'o': 'e', 'a': 'a'}     # c on a vowel: the flip, on the partner letter
VOWEL_OPS = ('', 'j', 'c', 'q', 'y', 'jy', 'cy', 'qy')          # one of j c q, then y: one typed form per letter

MARKS, DESC, ZWJ = script.MARKS, script.DESC, script.ZWJ
TONES, TONE_OF, tone_signs = script.TONES, script.TONE_OF, script.tone_signs


class ParseError(ValueError):
    pass


def segments(text, strict=True):
    """-> list of segments, each a dict: kind 'form' | 'raw' | 'err', src (the
    typed characters), and for forms: form (base case kept) and tones.

    strict=True raises ParseError on ill-formed input (the reference reading);
    strict=False marks the offending characters 'err' and goes on: input
    methods pass them through as typed, since a person may be typing a
    language the system does not describe.
    """
    out, i, n = [], 0, len(text)
    while i < n:
        raw, ch = text[i], text[i].lower()
        if ch not in BASES:
            if ch in OPS or ch.isdigit():
                if strict:
                    raise ParseError(f'position {i}: {text[i]!r} cannot start a segment')
                out.append({'kind': 'err', 'src': text[i]})
            else:
                out.append({'kind': 'raw', 'src': text[i]})
            i += 1
            continue
        j = i + 1
        ops = ''
        while j < n and text[j].lower() in OPS:
            ops += text[j].lower()
            j += 1
        w = 'w' in ops
        core = ops.replace('w', '')
        bad = None
        if len(core) > 2:
            bad = f'{text[i:j]}: more than two operators'
        elif ops.count('w') > 1 or (w and not ops.endswith('w')):
            bad = f'{text[i:j]}: w must come last, once'
        tones = ''
        while j < n and text[j].isdigit():
            tones += text[j]
            j += 1
        if bad:
            if strict:
                raise ParseError(bad)
            out.append({'kind': 'err', 'src': text[i:j]})
        else:
            out.append({'kind': 'form', 'src': text[i:j],
                        'form': raw + core + ('w' if w else ''), 'tones': tones})
        i = j
    return out


def tokenize(text):
    """-> list of ('form', form, tones) and ('raw', char) tokens (strict)."""
    return [('raw', s['src']) if s['kind'] == 'raw' else ('form', s['form'], s['tones'])
            for s in segments(text)]


def _core(core):
    """A core form (lowercase, no length) -> its composition (letter, marks)."""
    base, ops = core[0], core[1:]
    if core in WHOLE:
        return WHOLE[core]
    if core[:2] in WHOLE and len(core) == 3:
        letter, marks = WHOLE[core[:2]]
        op2 = core[2]
        if op2 == 'x':                      # the dot on an unmarked whole letter
            if any(m in script.C_MARKS for m in marks):
                raise ParseError(f'{core}: the dot cannot stack on a marked form')
            return letter, ('dot',) + marks
        if op2 == 'y' and 'anchor' in marks:   # y flips the anchored affricate
            return letter, ('reverse',)
        raise ParseError(f'{core}: {op2} cannot be secondary')
    if base in V_BASES:
        return _vowel(base, ops)
    return _consonant(base, ops)


def _consonant(base, ops):
    if not ops:
        return base, ()
    op1 = ops[0]
    if op1 == 'y' and base in 'lrf':
        raise ParseError(f'{base}{ops}: no reverse anchor on the thin stems l r f')
    # one typed form per letter: the dot is x, but the tap is rc; s̖ z̖ are sjy zjy
    if op1 == 'c' and base != 'r':
        raise ParseError(f'{base}{ops}: c on a consonant only in the tap rc and the whole letters (tc dc)')
    if op1 == 'x' and base == 'r':
        raise ParseError(f'{base}{ops}: the tap is typed rc')
    if op1 == 'y' and base in 'sz':
        raise ParseError(f'{base}{ops}: the reverse anchor on {base} is typed {base}jy')
    if op1 == 'q':
        raise ParseError(f'{base}{ops}: no such form')  # q-forms are whole letters
    if op1 not in 'jxyc':
        raise ParseError(f'{base}{ops}: no such form')
    mark = {'j': 'anchor', 'x': 'dot', 'y': 'reverse', 'c': 'dot'}[op1]    # the tap rc = ṛ
    if len(ops) == 1:
        return base, (mark,)
    op2 = ops[1]
    if op2 == 'x':
        raise ParseError(f'{base}{ops}: x cannot follow {op1}')
    if op2 == 'y' and op1 == 'j' and base in 'sz':      # y flips the anchored hush
        return base, ('reverse',)
    raise ParseError(f'{base}{ops}: {op2} cannot be secondary')


def _vowel(base, ops):
    if 'x' in ops:
        raise ParseError(f'{base}{ops}: x composes only in the glides')
    if ops not in VOWEL_OPS:
        raise ParseError(f'{base}{ops}: on a vowel, one of j c q, then y (c and j together is q)')
    letter = PARTNER[base] if ops[:1] in ('c', 'q') else base
    marks = {'': (), 'j': ('underdot',), 'c': ('flip',), 'q': ('flip', 'underdot')}[ops.rstrip('y')]
    return letter, marks + (('grave',) if ops.endswith('y') else ())


def comp(form):
    """A form -> (composition, long, caps). Raises ParseError for a form the
    grammar does not type."""
    caps = form[0].isupper()
    form = form[0].lower() + form[1:]
    long = form.endswith('w')
    c = _core(form[:-1] if long else form)
    if long and c[0] not in script.VOWELS and form[0] in V_BASES and (form[:-1] not in WHOLE):
        raise ParseError(f'{form}: no long form')        # a dotted glide (ixx uxx aqx) has none
    return c, long, caps


def points(text, strict=True):
    """Typed text -> tokens. strict=False passes ill-formed characters and
    forms the grammar does not type through as typed."""
    out = []
    for seg in segments(text, strict):
        if seg['kind'] != 'form':
            out += [Tok(raw=ch) for ch in seg['src']]
            continue
        try:
            c, long, caps = comp(seg['form'])
        except ParseError:
            if strict:
                raise
            out += [Tok(raw=ch) for ch in seg['src']]
            continue
        out.append(Tok(c, long, caps, seg['tones'], src=seg['src']))
    return out


_FORM = None


def form(tok):
    """The form that types a token (base case kept, tones after), or its raw character."""
    global _FORM
    if tok.raw is not None:
        return tok.raw
    if _FORM is None:
        _FORM = {}
        for f in inventory():
            c, long, _ = comp(f)
            _FORM[c, long] = f
    f = _FORM[tok.comp, tok.long]
    return (f[0].upper() + f[1:] if tok.caps else f) + tok.tones


def typed(tokens):
    return ''.join(form(t) for t in tokens)


def glyph(form, join=False):
    """Script glyph for one segment form."""
    c, long, caps = comp(form)
    return script.glyph(c, long, caps, join)


def compositions(form):
    """(small, capital) glyphs of a form's letter, a vowel's length with it,
    a consonant's doubling left out: what the font draws for that letter."""
    c, long, _ = comp(form[0].lower() + form[1:])
    return script.compose(c, long), script.compose(c, long, caps=True)


def render(text, strict=True, join=False):
    """The script form of a typed text."""
    return script.write(points(text, strict), join)


def inventory():
    """Every valid single-segment form of the grammar, lowercase."""
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
    first (script.match: a letter takes its marks with it), tones attached to
    the form before them; anything the table does not cover is raw. -> list
    of ('form', form, tones, matched) and ('raw', ch)."""
    text = ud.normalize('NFC', text)
    maxlen = max((len(k) for k in table), default=1)
    out, i, n = [], 0, len(text)
    while i < n:
        s = script.match(text, i, table, maxlen)
        if s is None:
            out.append(('raw', text[i]))
            i += 1
            continue
        tones, i = script.read_tones(text, i + len(s))
        out.append(('form', table[s], tones, s))
    return out


def stream(buffer):
    """The streaming commit rule, for input methods: -> (committed, pending).

    A segment can still grow only while it is the last thing typed and it is
    a form (an operator, w or a tone digit may follow). Everything before the
    last segment is final, and so is a last segment that is not a form. The
    caller commits `committed` in place, keeps `pending` as the typed tail
    (shown as composing text), and calls again with pending + the next key.
    Lenient by design: an ill-formed tail passes through as typed.
    """
    segs = segments(buffer, strict=False)
    if not segs:
        return '', ''
    if segs[-1]['kind'] == 'form':
        head, tail = segs[:-1], segs[-1]['src']
    else:
        head, tail = segs, ''
    return render(''.join(s['src'] for s in head), strict=False), tail


def legacy_script():
    """data/script.yaml as the ports knew it before the split: the whole
    letters and the flip partners by form, the tones by digit."""
    whole = {f: script.compose(c) for f, c in WHOLE.items()}
    return {'descenders': sorted(script.DESC), 'whole_letters': whole, 'marks': script.MARKS,
            'flip_partner': dict(PARTNER),
            'tones': {n: {'contour': script.CONTOUR[n], 'sign': s} for n, s in script.TONES.items()}}


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
    m = yaml.safe_load(open(os.path.join(ROOT, 'data', 'mapping.yaml'), encoding='utf-8'))

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
    import gen_master
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
            import gen_master
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
    """The lexicons as the site's typing engine reads them, in typed forms: <code>.json."""
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
