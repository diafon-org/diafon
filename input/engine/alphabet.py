"""The alphabet, as the typing knows it: the published docs/alphabet-spec.json
and nothing else. The script is a table there: every letter with marks the
alphabet allows, with its glyphs small and capital, long and joined.

A composition is (letter, marks); a point is a composition with a name. A
text is a list of tokens (Tok): a point with its length, case and tones, or
a raw character. write(tokens) is the text, read(text) the tokens.
"""
import json
import os
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(os.path.dirname(ROOT), 'docs', 'alphabet-spec.json'), encoding='utf-8'))
VERSION = SPEC['version']
MAJOR = int(VERSION.split('.')[0])

LONG = SPEC['script']['long']
ZWJ = SPEC['script']['joiner']
VOWELS = set(SPEC['script']['letters']['vowels'])
MARKS = SPEC['script']['marks']
TONES = {str(t['number']): t['sign'] for t in SPEC['script']['tones'].values()}     # tone number -> its sign
TONE_OF = {sign: n for n, sign in TONES.items() if sign}

COMPS = {(c['letter'], tuple(c['marks'])): c for c in SPEC['compositions']}
NAME = {comp: c['id'] for comp, c in COMPS.items() if c['id']}
POINTS = {name: comp for comp, name in NAME.items()}


class Tok:
    """One token of a text: a point (comp, long, caps, tones) or a raw
    character (raw). `tones` is a string of tone numbers; `src` what it was
    typed or read from."""
    __slots__ = ('comp', 'long', 'caps', 'tones', 'raw', 'src')

    def __init__(self, comp=None, long=False, caps=False, tones='', raw=None, src=None):
        self.comp, self.long, self.caps, self.tones, self.raw, self.src = comp, long, caps, tones, raw, src

    @property
    def point(self):
        return self.raw is None

    @property
    def vowel(self):
        return self.raw is None and self.comp[0] in VOWELS

    @property
    def name(self):
        n = NAME.get(self.comp)
        return n and n + (LONG if self.long else '')

    def __repr__(self):
        if self.raw is not None:
            return f'<{self.raw!r}>'
        return f'<{self.name or "+".join((self.comp[0],) + self.comp[1])}{"^" if self.caps else ""}{self.tones}>'


def target(text):
    """A profile's target -> (composition, long): a point name (ʃ, ʃː), or
    letter+mark for a composition no point names (b+reverse)."""
    long = text.endswith(LONG)
    if long:
        text = text[:-1]
    if text in POINTS:
        return POINTS[text], long
    letter, *marks = text.split('+')
    comp = (letter, tuple(marks))
    if comp not in COMPS:
        raise KeyError(f'{text}: neither a point nor a composition of the alphabet')
    return comp, long


def target_name(comp):
    return NAME.get(comp) or '+'.join((comp[0],) + comp[1])


ALL = 2      # a token's caps: every letter of a long consonant a capital (both its keys were)


def glyph(comp, long=False, caps=False, join=False):
    c = COMPS[comp]
    if long and caps == ALL and 'joined' in c:
        return c['capital'] + ('\u200d' if join else '') + c['capital']
    if long and join and 'joined' in c:
        return c['joined_capital' if caps else 'joined']
    if long:
        return c['long_capital' if caps else 'long']
    return c['capital' if caps else 'glyph']


def tone_signs(numbers):
    return ''.join(TONES.get(d, d) for d in numbers)


def write(tokens, join=False):
    return ''.join(t.raw if t.raw is not None else glyph(t.comp, t.long, t.caps, join) + tone_signs(t.tones)
                   for t in tokens)


_TABLE = None


def table():
    """{glyph: (comp, long, caps)} over the whole script."""
    global _TABLE
    if _TABLE is None:
        t = {}
        for comp, c in COMPS.items():
            for field, long, caps in (('glyph', False, False), ('capital', False, True), ('long', True, False),
                                      ('long_capital', True, True), ('joined', True, False), ('joined_capital', True, True)):
                if field in c:
                    t.setdefault(c[field], (comp, long, caps))
        _TABLE = t
    return _TABLE


def match(text, i, table, maxlen):
    """The longest key of a table at text[i:] that takes its marks with it."""
    n = len(text)
    for L in range(min(maxlen, n - i), 0, -1):
        s = text[i:i + L]
        if s in table and not (i + L < n and ud.category(text[i + L]) == 'Mn'):
            return s
    return None


def read_tones(text, i):
    tones, n = '', len(text)
    while i < n and (text[i].isdigit() or text[i] in TONE_OF):
        tones += TONE_OF.get(text[i], text[i])
        i += 1
    return tones, i


def read(text):
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
