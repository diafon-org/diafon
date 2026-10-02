#!/usr/bin/env python3
"""The Diafon engine: input form -> tokens -> script glyphs.

Implements the grammar of docs/index.html:
- 20 bases, 6 operators; an operator never starts a segment, a base always does.
- The two-operator law: a form carries at most two of c j q x y; w (length)
  rides free after them; trailing digits are tones.
- Glyphs compose from data/script.yaml: whole letters, per-operator marks,
  the float rule (descenders take their mark above), secondary x flips the
  mark already there, the special (secondary y / the pair xy) is the double
  dot on the free side, w doubles a consonant glyph / draws the vowel acute.
- The text is the composition itself, normalized (NFC): a base letter plus
  the system's own combining marks, one meaning per mark on every letter;
  where Unicode has a precomposed letter for the pair (ș ṭ ä á) it appears,
  elsewhere the sequence stands (t̤ k̦ ȁ).
- Case is orthographic, not phonemic: an uppercase base letter capitalizes
  its point (Sjan -> Șan); operators read the same in either case, so
  all-caps text works point by point; the float rule reads the capital's own
  shape, and no capital in the system has a descender, so a capital always
  wears its mark below (p̓ P̦, ġ G̣); a long consonant capitalizes only its
  first letter (Sjw -> Șș).

Input methods use segments(strict=False), render(strict=False) and stream():
ill-formed input passes through as typed, and a segment commits the moment
the keystroke stream can no longer change it.

Usage: engine.py "input text"   -> prints the script form.
"""
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

C_BASES = set('bdfghklmnprstvz')
V_BASES = set('aeiou')
BASES = C_BASES | V_BASES
OPS = set('cjqxwy')

_S = yaml.safe_load(open(os.path.join(ROOT, 'data', 'script.yaml')))
DESC = set(_S['descenders'])
WHOLE = _S['whole_letters']
MARKS = _S['marks']
PARTNER = _S['flip_partner']


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


def _mark(glyph, base, kind, caps=False):
    """Attach a mark to a glyph, by the float rule and one-per-side. The rule
    reads the rendered letter: no capital has a descender, so caps never
    float their mark above."""
    m = MARKS[kind]
    below, above = m.get('below'), m.get('above')
    has_below = any(v.get('below') and v['below'] in glyph
                    for v in MARKS.values() if isinstance(v, dict))
    if below and (caps or base not in DESC) and not has_below:
        return glyph + below
    if above:
        return glyph + above
    return glyph + (below or '')


def glyph(form):
    """Script glyph for one segment form. An uppercase base letter
    capitalizes the glyph; the float rule reads the capital's own shape."""
    caps = form[0].isupper()
    if caps:
        form = form[0].lower() + form[1:]
    w = form.endswith('w')
    core = form[:-1] if w else form
    base = core[0]
    long_vowel = w and base in V_BASES and core not in WHOLE

    def compose(cap):
        g = _compose(core, cap)
        if long_vowel:
            flip = MARKS['flip']['above']
            g = (g.replace(flip, MARKS['double_acute']['above']) if flip in g
                 else g + MARKS['acute']['above'])
        return ud.normalize('NFC', g)

    g = compose(caps)
    if w and not long_vowel:
        g += g                  # long consonant doubles its letter
    g = ud.normalize('NFC', g)  # one codepoint per visual representation
    if caps:
        g = ud.normalize('NFC', g[0].upper() + g[1:])
    return g


def compositions(form):
    """(small, capital) composed glyphs of a form, marks as combining
    characters, before the web letter: what the font draws for that letter.
    Length is left out (a long consonant doubles the letter)."""
    form = form[0].lower() + form[1:]
    w = form.endswith('w')
    core = form[:-1] if w else form
    long_vowel = w and core[0] in V_BASES and core not in WHOLE
    out = []
    for cap in (False, True):
        g = _compose(core, cap)
        if long_vowel:
            flip = MARKS['flip']['above']
            g = (g.replace(flip, MARKS['double_acute']['above']) if flip in g
                 else g + MARKS['acute']['above'])
        g = ud.normalize('NFC', g)
        out.append(ud.normalize('NFC', g[0].upper() + g[1:]) if cap else g)
    return tuple(out)


def _compose(core, caps):
    """The composed glyph of a core form (no length), marks as combining
    characters, before the web letter and before case."""
    base, ops = core[0], core[1:]
    if core in WHOLE:
        return WHOLE[core]
    if core[:2] in WHOLE and len(core) == 3:
        g = WHOLE[core[:2]]
        op2 = core[2]
        if op2 == 'x':                      # the dot on an unmarked whole letter
            if any(v.get('below') and v['below'] in g
                   for v in MARKS.values() if isinstance(v, dict)):
                raise ParseError(f'{core}: the dot cannot stack on a marked form')
            return _mark(g, g[0], 'dot', caps)
        if op2 == 'y':
            if MARKS['anchor']['below'] in g:   # y flips the anchored affricate
                return g.replace(MARKS['anchor']['below'], MARKS['reverse']['below'])
            if any(v.get('below') and v['below'] in g
                   for v in MARKS.values() if isinstance(v, dict)):
                raise ParseError(f'{core}: the special cannot stack on a marked form')
            return _special(g, g[0], caps)      # the special on a bare whole letter
        raise ParseError(f'{core}: {op2} cannot be secondary')
    if base in V_BASES:
        return _vowel(base, ops)
    return _consonant(base, ops, caps)


def _consonant(base, ops, caps=False):
    g = base
    if not ops:
        return g
    op1 = ops[0]
    if op1 in 'jy' and base in 'lrf':
        raise ParseError(f'{base}{ops}: no anchor on the thin stems l r f')
    if op1 == 'j':
        g = _mark(g, base, 'anchor', caps)
    elif op1 == 'x':
        g = _mark(g, base, 'dot', caps)
    elif op1 == 'y':
        g = _mark(g, base, 'reverse', caps)
    elif op1 == 'c':
        g = _mark(g, base, 'dot', caps)     # the tap rc = ṛ; other affricates are whole letters
    elif op1 == 'q':
        raise ParseError(f'{base}{ops}: no such form')  # q-forms are whole letters
    if len(ops) == 1:
        return g
    op2 = ops[1]
    if op2 == 'x':
        raise ParseError(f'{base}{ops}: x cannot follow {op1}')
    if op2 == 'y':
        if op1 == 'x':                      # the pair xy: y doubles the dot
            return _special(base, base, caps)
        if op1 == 'j' and base in 'sz':     # y flips the anchored hush
            a, r = MARKS['anchor'], MARKS['reverse']
            return g.replace(a['below'], r['below'])
        raise ParseError(f'{base}{ops}: the special cannot stack on a marked form')
    raise ParseError(f'{base}{ops}: {op2} cannot be secondary')


def _special(g, base, caps=False):
    sp = MARKS['special']
    has_below = any(v.get('below') and v['below'] in g
                    for v in MARKS.values() if isinstance(v, dict))
    if (caps or base not in DESC) and not has_below:
        return g + sp['below']
    return g + sp['above']


def _vowel(base, ops):
    g = base
    for i, op in enumerate(ops):
        if op == 'c':
            g = PARTNER[base] + MARKS['flip']['above']
        elif op == 'j':
            g += MARKS['underdot']['below']
        elif op == 'q':                     # c + j in one letter
            g = PARTNER[base] + MARKS['flip']['above'] + MARKS['underdot']['below']
        elif op == 'y':
            g += MARKS['grave']['above']
        elif op == 'x':
            raise ParseError(f'{base}{ops}: x composes only in the glides')
        else:
            raise ParseError(f'{base}{ops}: bad vowel operator {op}')
    return g


def render(text, strict=True):
    """Script form of a text. strict=False passes ill-formed characters and
    forms with no glyph through as typed (the input-method reading)."""
    out = []
    for seg in segments(text, strict):
        if seg['kind'] != 'form':
            out.append(seg['src'])
            continue
        try:
            out.append(glyph(seg['form']) + seg['tones'])
        except ParseError:
            if strict:
                raise
            out.append(seg['src'])
    return ''.join(out)


def inventory():
    """Every valid single-segment form of the grammar, lowercase: a base, up
    to two operators, w or not; whatever glyph() accepts."""
    out = []
    core_ops = sorted(OPS - {'w'})
    combos = [''] + core_ops + [a + b for a in core_ops for b in core_ops]
    for base in sorted(BASES):
        for ops in combos:
            for w in ('', 'w'):
                form = base + ops + w
                try:
                    glyph(form)
                except ParseError:
                    continue
                out.append(form)
    return out


_SCRIPT_TABLE = {}


def script_table(used=()):
    """The script read back: {glyph text: form} over the whole inventory,
    small and capitalized (Șș -> Sjw). Where two forms compose the same
    glyph (the dot of kx and kc; a vowel operator repeated, acc = ac) the
    reading is a form in `used` (the forms the languages use, from the
    master table) before any other, and the shorter form after that; the
    inventory lists shorter forms first."""
    key = frozenset(used)
    if key not in _SCRIPT_TABLE:
        table = {}
        inv = inventory()
        for form in [f for f in inv if f in key] + [f for f in inv if f not in key]:
            for f in (form, form[0].upper() + form[1:]):
                table.setdefault(glyph(f), f)
        _SCRIPT_TABLE[key] = table
    return _SCRIPT_TABLE[key]


def read(text, table):
    """Read a text back through a {spelling: form} table, longest match
    first, tone digits attached to the form before them; anything the table
    does not cover is raw. -> list of ('form', form, tones, matched) and
    ('raw', ch). The text is NFC-normalized first, as the table is."""
    text = ud.normalize('NFC', text)
    maxlen = max((len(k) for k in table), default=1)
    out, i, n = [], 0, len(text)
    while i < n:
        hit = None
        for L in range(min(maxlen, n - i), 0, -1):
            s = text[i:i + L]
            if s in table:
                hit = (s, table[s])
                break
        if hit is None:
            out.append(('raw', text[i]))
            i += 1
            continue
        i += len(hit[0])
        tones = ''
        while i < n and text[i].isdigit():
            tones += text[i]
            i += 1
        out.append(('form', hit[1], tones, hit[0]))
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


if __name__ == '__main__':
    print(render(' '.join(sys.argv[1:])))
