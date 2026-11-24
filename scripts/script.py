#!/usr/bin/env python3
"""The script: points <-> glyphs, from data/script.yaml.

A composition is a letter and its marks, (letter, marks); a point is a
composition with a name, its canonical IPA value (split.md). The text is
the composition itself, normalized (NFC): where Unicode has a precomposed
letter for the pair (ș ṭ ä á) it appears, elsewhere the sequence stands
(t̤ k̦ ȁ).

- A consonant's mark sits below, floating above on the small letters that
  descend; no capital descends, so a capital wears its mark below (p̓ P̦).
- A vowel wears the flip or the underdot; long, the acute (the
  flip and the acute fuse into the double acute).
- A long consonant doubles its letter, and only the first is capitalized
  (Șș); with join=True a zero width joiner sits between the two, which the
  Diafon fonts draw fused. Two equal consonant letters in a row are the long
  point: the joiner marks a drawing, never a meaning. A nasal that is a
  syllable before its own letter wears the double dot above (m̈ma, n̈ne), so
  it is never read as the long one.
- A tone is a sign after the syllable; the unmarked contour writes nothing.

A text is a list of tokens (Tok): a point, with its length, case and tones,
or a raw character. write(tokens) is the text; read(text) is the tokens,
longest match first, a letter with its marks before a doubling.

Usage: script.py "text"   -> the points of a text, by name.
"""
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_S = yaml.safe_load(open(os.path.join(ROOT, 'data', 'script.yaml'), encoding='utf-8'))
CONSONANTS = set(_S['letters']['consonants'])
VOWELS = set(_S['letters']['vowels'])
DESC = set(_S['descenders'])
MARKS = _S['marks']
C_MARKS = ('anchor', 'dot', 'twodots')                 # a consonant wears one of these
V_MARKS = ('flip', 'underdot')                         # a vowel one of these
ZWJ = '‍'
LONG = 'ː'

TONES = {str(t['number']): t['sign'] for t in _S['tones'].values()}        # tone number -> its sign
TONE_OF = {sign: n for n, sign in TONES.items() if sign}                   # and back (the unmarked reads as none)
CONTOUR = {str(t['number']): name for name, t in _S['tones'].items()}

# name -> composition, and back
POINTS = {str(name): (spec.split()[0], tuple(spec.split()[1:])) for name, spec in _S['points'].items()}
NAME = {}
for _name, _comp in POINTS.items():
    assert _comp not in NAME, f'{_name} and {NAME[_comp]}: one composition'
    assert _name == ud.normalize('NFC', _name), f'{_name}: not NFC'
    NAME[_comp] = _name


class Tok:
    """One token of a text: a point (comp, long, caps, tones) or a raw
    character (raw). `tones` is a string of tone numbers; `src` the letters
    it was read from, where it was read."""
    __slots__ = ('comp', 'long', 'caps', 'tones', 'raw', 'src')

    def __init__(self, comp=None, long=False, caps=False, tones='', raw=None, src=None):
        self.comp, self.long, self.caps, self.tones, self.raw, self.src = comp, long, caps, tones, raw, src

    @property
    def point(self):
        return self.raw is None

    @property
    def name(self):
        """The point's name (ʃ, ʃː), or None for an open composition."""
        n = NAME.get(self.comp)
        return n and n + (LONG if self.long else '')

    @property
    def vowel(self):
        return self.raw is None and self.comp[0] in VOWELS

    def __repr__(self):
        if self.raw is not None:
            return f'<{self.raw!r}>'
        return f'<{self.name or "+".join((self.comp[0],) + self.comp[1])}{"^" if self.caps else ""}{self.tones}>'


def valid(comp):
    """Whether a letter and marks compose. A consonant wears at most one of
    the anchor, the dot and the double dot below: no double dot on the thin stems l r f,
    only the dot on j w. The flip stands on w r m n, alone (and on the
    dotted r). A vowel wears the flip or the underdot, not both."""
    letter, marks = comp
    if len(set(marks)) != len(marks):
        return False
    if letter in VOWELS:
        return all(m in V_MARKS for m in marks) and not ('flip' in marks and 'underdot' in marks)
    if letter not in CONSONANTS:
        return False
    rest = [m for m in marks if m != 'flip']
    if len(rest) > 1 or not all(m in C_MARKS for m in rest):
        return False
    if 'twodots' in rest and letter in 'lrf':
        return False
    if rest and rest != ['dot'] and letter in 'jw':
        return False
    if 'flip' in marks:
        return letter in 'wrmn' and (not rest or (letter == 'r' and rest == ['dot']))
    return True


def vocalic(comp):
    """The vowels, and the points that stand with them: the glides on j and
    w, the vocalic r (r̈) and the syllabic nasals (m̈ n̈). A spelling's rules
    for consonants (a doubled letter when long, soft before a vowel) leave
    these out."""
    letter, marks = comp
    return letter in VOWELS or letter in 'jw' or (letter in 'rmn' and 'flip' in marks)


def point(name):
    """A point by name -> (composition, long)."""
    long = name.endswith(LONG)
    return POINTS[name[:-1] if long else name], long


def compose(comp, long=False, caps=False):
    """One letter of a composition: the glyph, without a consonant's doubling."""
    letter, marks = comp
    if letter in VOWELS:
        g = letter
        if 'flip' in marks:
            g += MARKS['double_acute' if long else 'flip']['above']
        if 'underdot' in marks:
            g += MARKS['underdot']['below']
        if long and 'flip' not in marks:
            g += MARKS['acute']['above']
    else:
        g = letter
        for m in marks:
            if m != 'flip':
                side = 'above' if (letter in DESC and not caps) else 'below'
                g += MARKS[m][side]
        if 'flip' in marks:
            g += MARKS['flip']['above']
    g = ud.normalize('NFC', g)
    return ud.normalize('NFC', g[0].upper() + g[1:]) if caps else g


def glyph(comp, long=False, caps=False, join=False):
    """The glyph of a composition (or of a point, by name)."""
    if isinstance(comp, str):
        if comp.endswith(LONG):
            comp, long = comp[:-1], True
        comp = POINTS[comp]
    if long and comp[0] not in VOWELS:
        first = compose(comp, caps=caps)             # the second letter is the first one, small: a capital's
        return first + (ZWJ if join else '') + ud.normalize('NFC', first[0].lower() + first[1:])   # mark stays below (G̦g̦)
    return compose(comp, long, caps)


def tone_signs(numbers):
    """The signs of a run of tone numbers (one outside the vocabulary stays a digit)."""
    return ''.join(TONES.get(d, d) for d in numbers)


def write(tokens, join=False):
    return ''.join(t.raw if t.raw is not None else glyph(t.comp, t.long, t.caps, join) + tone_signs(t.tones)
                   for t in tokens)


def compositions():
    """Every composition the script allows, the named points first."""
    out = list(NAME)
    for letter in sorted(CONSONANTS):
        for m in ((),) + tuple((x,) for x in C_MARKS):
            for flip in ((), ('flip',)):
                out.append((letter, m + flip))
    for letter in sorted(VOWELS):
        for bits in range(8):
            out.append((letter, tuple(m for k, m in enumerate(V_MARKS) if bits >> k & 1)))
    seen = {}
    for c in out:
        if valid(c):
            seen.setdefault(c, None)
    return list(seen)


_TABLE = None


def table():
    """The script read back: {glyph: (comp, long, caps)} over every
    composition, short and long, small and capital, a long consonant plain
    and joined. No two compositions share a glyph (tests/test_script.py)."""
    global _TABLE
    if _TABLE is None:
        t = {}
        for comp in compositions():
            for long in (False, True):
                for caps in (False, True):
                    for join in ((False, True) if long and comp[0] not in VOWELS else (False,)):
                        g = glyph(comp, long, caps, join)
                        assert t.setdefault(g, (comp, long, caps)) == (comp, long, caps), (g, comp, t[g])
        _TABLE = t
    return _TABLE


def _mark(ch):
    return ud.category(ch) == 'Mn'


def match(text, i, table, maxlen):
    """The longest key of a table at text[i:] that takes its marks with it:
    a match never ends before a combining mark, so a letter with marks is
    read before a doubling (dd̦ is d and d̦, not a long d and a stray mark)."""
    n = len(text)
    for L in range(min(maxlen, n - i), 0, -1):
        s = text[i:i + L]
        if s in table and not (i + L < n and _mark(text[i + L])):
            return s
    return None


def read_tones(text, i):
    """The tone numbers at text[i:] (signs, or digits) -> (numbers, next i)."""
    tones, n = '', len(text)
    while i < n and (text[i].isdigit() or text[i] in TONE_OF):
        tones += TONE_OF.get(text[i], text[i])
        i += 1
    return tones, i


def read(text):
    """A text -> tokens: the points it writes, anything else raw. NFC first,
    as the table is."""
    text = ud.normalize('NFC', text)
    t = table()
    maxlen = max(len(k) for k in t)
    out, i, n = [], 0, len(text)
    while i < n:
        s = match(text, i, t, maxlen)
        if s is None:
            out.append(Tok(raw=text[i]))
            i += 1
            continue
        comp, long, caps = t[s]
        tones, j = read_tones(text, i + len(s))
        out.append(Tok(comp, long, caps, tones, src=s))
        i = j
    return out


def capital(text):
    """A text with its first point capitalized: the letter's own capital (a
    mark that floated above sits below it), a long consonant's first letter."""
    toks = read(text)
    for t in toks:
        if t.point:
            t.caps = True
            break
    return write(toks, join=ZWJ in text)


def is_script(text):
    """Whether a text is points throughout (tones allowed)."""
    return bool(text) and all(t.point for t in read(text))


def names(text):
    return [t.name or repr(t) if t.point else t.raw for t in read(text)]


if __name__ == '__main__':
    print(' '.join(names(' '.join(sys.argv[1:]))))
