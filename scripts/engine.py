#!/usr/bin/env python3
"""The Diaphone engine: input form -> tokens -> script glyphs.

Implements the grammar of docs/index.html:
- 20 bases, 6 operators; an operator never starts a segment, a base always does.
- The two-operator law: a form carries at most two of c j q x y; w (length)
  rides free after them; trailing digits are tones.
- Glyphs compose from data/script.yaml: whole letters, per-operator marks,
  the float rule (descenders take their mark above), secondary x flips the
  mark already there, the special (secondary y / the pair xy) is the double
  dot on the free side, w doubles a consonant glyph / draws the vowel acute.

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


def tokenize(text):
    """-> list of ('form', form, tones) and ('raw', char) tokens."""
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i].lower()
        if ch not in BASES:
            if ch in OPS or ch.isdigit():
                raise ParseError(f'position {i}: {text[i]!r} cannot start a segment')
            out.append(('raw', text[i]))
            i += 1
            continue
        j = i + 1
        ops = ''
        while j < n and text[j].lower() in OPS:
            ops += text[j].lower()
            j += 1
        w = 'w' in ops
        core = ops.replace('w', '')
        if len(core) > 2:
            raise ParseError(f'{text[i:j]}: more than two operators')
        if ops.count('w') > 1 or (w and not ops.endswith('w')):
            raise ParseError(f'{text[i:j]}: w must come last, once')
        tones = ''
        while j < n and text[j].isdigit():
            tones += text[j]
            j += 1
        out.append(('form', ch + core + ('w' if w else ''), tones))
        i = j
    return out


def _mark(glyph, base, kind):
    """Attach a mark to a glyph, by the float rule and one-per-side."""
    m = MARKS[kind]
    below, above = m.get('below'), m.get('above')
    has_below = any(v.get('below') and v['below'] in glyph
                    for v in MARKS.values() if isinstance(v, dict))
    if below and base not in DESC and not has_below:
        return glyph + below
    if above:
        return glyph + above
    return glyph + (below or '')


def glyph(form):
    """Script glyph for one segment form."""
    w = form.endswith('w')
    core = form[:-1] if w else form
    base, ops = core[0], core[1:]
    if core in WHOLE:
        g = WHOLE[core]
    elif core[:2] in WHOLE and len(core) == 3:
        g = WHOLE[core[:2]]
        op2 = core[2]
        if op2 == 'x':                      # the dot on an unmarked whole letter
            if any(v.get('below') and v['below'] in g
                   for v in MARKS.values() if isinstance(v, dict)):
                raise ParseError(f'{core}: the dot cannot stack on a marked form')
            g = _mark(g, g[0], 'dot')
        elif op2 == 'y':
            if MARKS['anchor']['below'] in g:   # y flips the anchored affricate
                g = g.replace(MARKS['anchor']['below'], MARKS['reverse']['below'])
            elif any(v.get('below') and v['below'] in g
                     for v in MARKS.values() if isinstance(v, dict)):
                raise ParseError(f'{core}: the special cannot stack on a marked form')
            else:                               # the special on a bare whole letter
                g = _special(g, g[0])
        else:
            raise ParseError(f'{core}: {op2} cannot be secondary')
    elif base in V_BASES:
        g = _vowel(base, ops)
    else:
        g = _consonant(base, ops)
    if w:
        if base in V_BASES and core not in WHOLE:
            flip = MARKS['flip']['above']
            if flip in g:
                g = g.replace(flip, MARKS['double_acute']['above'])
            else:
                g += MARKS['acute']['above']
        else:
            g += g  # long consonant doubles its letter
    return ud.normalize('NFC', g)  # one codepoint per visual representation


def _consonant(base, ops):
    g = base
    if not ops:
        return g
    op1 = ops[0]
    if op1 in 'jy' and base in 'lrf':
        raise ParseError(f'{base}{ops}: no anchor on the thin stems l r f')
    if op1 == 'j':
        g = _mark(g, base, 'anchor')
    elif op1 == 'x':
        g = _mark(g, base, 'dot')
    elif op1 == 'y':
        g = _mark(g, base, 'reverse')
    elif op1 == 'c':
        g = _mark(g, base, 'dot')           # the tap rc = ṛ; other affricates are whole letters
    elif op1 == 'q':
        raise ParseError(f'{base}{ops}: no such form')  # q-forms are whole letters
    if len(ops) == 1:
        return g
    op2 = ops[1]
    if op2 == 'x':
        raise ParseError(f'{base}{ops}: x cannot follow {op1}')
    if op2 == 'y':
        if op1 == 'x':                      # the pair xy: y doubles the dot
            return _special(base, base)
        if op1 == 'j' and base in 'sz':     # y flips the anchored hush
            a, r = MARKS['anchor'], MARKS['reverse']
            return g.replace(a['below'], r['below'])
        raise ParseError(f'{base}{ops}: the special cannot stack on a marked form')
    raise ParseError(f'{base}{ops}: {op2} cannot be secondary')


def _special(g, base):
    sp = MARKS['special']
    has_below = any(v.get('below') and v['below'] in g
                    for v in MARKS.values() if isinstance(v, dict))
    if base not in DESC and not has_below:
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


def render(text):
    out = []
    for tok in tokenize(text):
        if tok[0] == 'raw':
            out.append(tok[1])
        else:
            _, form, tones = tok
            out.append(glyph(form) + tones)
    return ''.join(out)


if __name__ == '__main__':
    print(render(' '.join(sys.argv[1:])))
