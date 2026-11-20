#!/usr/bin/env python3
"""universal-v1: the typing Diafon had before the split (split.md), as a
bridge. TEMPORARY: this is the only module of the alphabet that knows a
typed form; it keeps the build chain working through P1 and leaves for
diafon-input in P2, where it becomes the profile universal-v1.

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


if __name__ == '__main__':
    print(render(' '.join(sys.argv[1:])))
