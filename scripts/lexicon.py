#!/usr/bin/env python3
"""The lexicon layer (data/lexicon/README.md): word-level reading and
writing above the letter stages. Loaded from data/lexicon/<code>.json.

  lex(code)                 the lexicon, or None
  read_word(word, code)     spelling -> transport, or None
  write_word(t, code)       transport -> spelling; prefix lexicons (hu ly
                            stems) return (stem spelling, rest of transport)
  fold(t, code)             a loan's transport folded into the host's sounds
  choices(t_tone, code)     the characters of a toned syllable (zh)
  recase(out, original)     the original's case laid on the output
"""
import glob
import json
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine

LEX = os.path.join(ROOT, 'data', 'lexicon')
_CACHE = {}

WORD_T = re.compile(r'[A-Za-z]+\d*')                       # a word of transport text, tone digits after
# a word of text: letters and combining marks (U+0300–036F, where every mark of
# the system lives), an apostrophe inside, tone digits after; the same
# definition in docs/engine.js and Lexicon.swift
_L = r"(?:[^\W\d_]|[\u0300-\u036f])"
WORD = re.compile(_L + r"+(?:['’]" + _L + r"+)*\d*", re.U)


def codes():
    return sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(LEX, '*.json')))


def lex(code):
    if code not in _CACHE:
        p = os.path.join(LEX, f'{code}.json')
        _CACHE[code] = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
        if _CACHE[code] is not None:
            _CACHE[code].setdefault('read', {})
            _CACHE[code].setdefault('write', {})
            _CACHE[code].setdefault('loans', [])
            _CACHE[code].setdefault('fold', {})
            _CACHE[code].setdefault('choices', {})
            _CACHE[code].setdefault('loanwrite', {})
            _CACHE[code].setdefault('match', 'word')
            _CACHE[code].setdefault('lengthen', {})
            _CACHE[code]['common'] = set(_CACHE[code].get('common', []))
            _CACHE[code]['native'] = set(_CACHE[code].get('native', []))
    return _CACHE[code]


def recase(out, original):
    """The original's case on the output: capitalized -> first letter up;
    all caps (more than one letter) -> first letter up, the transport law."""
    if not out or not original:
        return out
    if original[0].isupper():
        return ud.normalize('NFC', out[0].upper() + out[1:])
    return out


def read_word(word, code):
    """spelling (tone digits allowed after it) -> transport, or None. A
    syllable lexicon also reads a run of syllables written together
    (nihao), greedily, longest syllable first."""
    L = lex(code)
    if not L:
        return None
    word = ud.normalize('NFC', word)
    if L.get('kind') == 'syllable' and re.search(r'\d\D', word):     # ni3hao3: syllable by syllable
        parts = re.findall(r'\D+\d*', word)
        outs = [read_word(p, code) for p in parts]
        return None if None in outs else ''.join(outs)
    digits = ''
    while word and word[-1].isdigit():
        digits, word = word[-1] + digits, word[:-1]
    key = word.lower()
    t = L['read'].get(key)
    if t is None and L.get('kind') == 'syllable' and key:
        out, i, keys = [], 0, sorted(L['read'], key=len, reverse=True)
        while i < len(key):
            hit = next((k for k in keys if key.startswith(k, i)), None)
            if hit is None:
                return None
            out.append(L['read'][hit])
            i += len(hit)
        t = ''.join(out)
    return recase(t, word) + digits if t is not None else None


def write_word(t, code):
    """transport -> spelling. Exact lexicons: the word, or None. Prefix
    lexicons: (stem spelling, remaining transport) for the longest stem
    the transport starts with, or None."""
    L = lex(code)
    if not L:
        return None
    digits = ''
    while t and t[-1].isdigit():                    # the tone rides along
        digits, t = t[-1] + digits, t[:-1]
    if not t:
        return None
    key = t[0].lower() + t[1:]
    if L['match'] == 'prefix':
        best = None
        for stem in L['write']:
            if key.startswith(stem) and (best is None or len(stem) > len(best)):
                best = stem
        if best is None:
            return None
        return recase(L['write'][best], t), t[len(best):] + digits
    sp = L['write'].get(key)
    return recase(sp, t) + digits if sp is not None else None


def spoken_stem(key, L):
    """The length of the longest of the host's own entries (`read`) that the
    lowercased word is, or starts with (a prefix lexicon, the stem looked up
    short too); 0 for none."""
    if not L['read'] or L.get('kind') == 'syllable':
        return 0
    if L['match'] != 'prefix':
        return len(key) if key in L['read'] else 0
    for i in range(min(len(key), 24), 2, -1):
        pre = key[:i]
        if pre in L['read'] or (pre[-1] in L['lengthen'] and pre[:-1] + L['lengthen'][pre[-1]] in L['read']):
            return i
    return 0


def read_stem(word, code):
    """A word, or with `match: prefix` a stem, the host's lexicon reads its
    own way (Hungarian `spoken`: jamaica -> jamaika): (transport, the rest
    of the spelling), or None. The stem is looked up short too (`lengthen`)."""
    L = lex(code)
    if not L:
        return None
    w = ud.normalize('NFC', word)
    key = w.lower()
    i = spoken_stem(key, L)
    if not i:
        return None
    pre = key[:i]
    t = L['read'].get(pre)
    if t is None:
        t = L['read'][pre[:-1] + L['lengthen'][pre[-1]]]
    return recase(t, w), w[i:]


def loan(word, code):
    """A host's word that is a loan: (transport folded, source code), or
    None. The longest stem a loan lexicon reads (among its `common` words
    where it has them: not CMUdict's names) decides against the longest
    native stem (the host's dictionary), native on ties unless the stem has
    a foreign letter shape (the host's `foreign` pattern: ee, sh, w…). A
    suffixed word whose stem has no foreign shape is never a loan (akinek
    is aki + nek, not akin + ek); with the shape the rest may be anything,
    read by the host's letters (streaming + ajánlójában). A stem whose final
    vowel the suffix lengthened (`lengthen`: pizzát) is looked up short too."""
    L = lex(code)
    if not L or not L['loans']:
        return None
    w = ud.normalize('NFC', word)
    key = w.lower()

    def stems(i):
        pre = key[:i]
        yield pre
        if pre[-1] in L['lengthen']:
            yield pre[:-1] + L['lengthen'][pre[-1]]

    native_len = next((i for i in range(min(len(key), 24), 2, -1) if any(p in L['native'] for p in stems(i))), 0)
    spoken_len = spoken_stem(key, L)                   # the host's own entry, if any: it wins unless a loan stem is longer
    loan_len, src, stem = 0, None, None
    for i in range(min(len(key), 24), 2, -1):
        for lc in L['loans']:
            LL = lex(lc)
            if LL:
                stem = next((p for p in stems(i) if p in LL['read'] and (not LL['common'] or p in LL['common'])), None)
                if stem is not None:
                    loan_len, src = i, lc
                    break
        if src:
            break
    if src is None or spoken_len >= loan_len:
        return None
    foreign = bool(L.get('foreign')) and re.search(L['foreign'], key[:loan_len]) is not None
    if not foreign and loan_len < len(key):
        return None
    if native_len > loan_len or (native_len == loan_len and not foreign):
        return None
    t = recase(lex(src)['read'][stem], word)
    rest = w[loan_len:]
    if rest:
        import stages                                  # the rest by the host's letters
        rest = stages.read_letters(rest, stages.table(stages.load(code)))
    return fold(t, code) + rest, src


def write_loan(t, code, letters_spelling):
    """A host's word written back as the loan it is: the folded transport
    of a loan word -> its own spelling, unless the letters' spelling is a
    word of the host (só stays só). None otherwise."""
    L = lex(code)
    if not L or not L['loanwrite']:
        return None
    if letters_spelling.lower() in L['native']:
        return None
    digits = ''
    while t and t[-1].isdigit():
        digits, t = t[-1] + digits, t[:-1]
    sp = L['loanwrite'].get(t[0].lower() + t[1:]) if t else None
    return recase(sp, t) + digits if sp is not None else None


def fold(t, code):
    """A loan's transport rewritten in the host's sounds: the host's fold
    rules over the segment forms, longest rule first, left to right."""
    L = lex(code)
    rules = L['fold'] if L else {}
    if not rules:
        return t
    segs = engine.segments(t, strict=False)
    forms = [s['form'].lower() if s['kind'] == 'form' else None for s in segs]
    keys = sorted(rules, key=len, reverse=True)
    parsed = {k: [s['form'] for s in engine.segments(k)] for k in keys}
    out, i = [], 0
    while i < len(segs):
        hit = None
        for k in keys:
            pf = parsed[k]
            if forms[i:i + len(pf)] == pf:
                hit = k
                break
        if hit is None:
            out.append(segs[i]['src'])
            i += 1
            continue
        repl = rules[hit]
        first = segs[i]
        caps = first['kind'] == 'form' and first['form'][0].isupper()
        tones = ''.join(s.get('tones', '') for s in segs[i:i + len(parsed[hit])])
        out.append((repl[0].upper() + repl[1:] if caps else repl) + tones)
        i += len(parsed[hit])
    return ''.join(out)


def choices(t_tone, code='zh'):
    L = lex(code)
    return (L['choices'].get(t_tone.lower()) if L else None) or []
