#!/usr/bin/env python3
"""The lexicon layer (data/lexicon/README.md): word-level reading and
writing above the letter stages. Loaded from data/lexicon/<code>.json.

  lex(code)                 the lexicon, or None
  read_word(word, code)     spelling -> transport, or None
  write_word(t, code)       transport -> spelling; prefix lexicons (hu ly
                            stems) return (stem spelling, rest of transport)
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
            _CACHE[code].setdefault('loans', False)
            _CACHE[code].setdefault('choices', {})
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
    if t is None and re.search(r"['’]d$", key):            # poetry's elided -ed: dimm'd reads as dimmed
        t = L['read'].get(key[:-2] + 'ed')
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


def loans():
    """The one loan dictionary (loans.json), or None."""
    return lex('loans')


def loan(word, code):
    """A host's word that is a loan: (transport in its own sounds, origin code), or
    None, from the one loan dictionary (loans.json), the same form in every host.
    The longest stem the dictionaries read (Latin; English, its common words: not
    CMUdict's names) decides against the longest native stem (the host's
    dictionary), native on ties unless the stem has a foreign letter shape (the
    host's `foreign` pattern: ee, sh, w…), and against the host's own entries and
    the hand loans (origin.yaml, and the host's own spellings of them: míting),
    the longer wins. A suffixed word whose stem has no foreign shape is never a
    dictionary loan (akinek is aki + nek, not akin + ek); with the shape the rest
    may be anything, read by the host's letters (streaming + ajánlójában). A hand
    loan is a stem, its rest read by the letters (Jamaicában). A stem whose final
    vowel the suffix lengthened (`lengthen`: pizzát) is looked up short too."""
    L, D = lex(code), loans()
    if not L or not L['loans'] or not D:
        return None
    w = ud.normalize('NFC', word)
    key = w.lower()
    top = min(len(key), 24)

    def stems(i):
        pre = key[:i]
        yield pre
        if pre[-1] in L['lengthen']:
            yield pre[:-1] + L['lengthen'][pre[-1]]

    def with_rest(t, n):
        rest = w[n:]
        if rest:
            import stages                              # the rest by the host's letters
            rest = stages.read_letters(rest, stages.table(stages.load(code)))
        return recase(t, word) + rest

    own = D['hosts'].get(code, {}).get('read', {})
    native_len = next((i for i in range(top, 2, -1) if any(p in L['native'] for p in stems(i))), 0)
    spoken_len = spoken_stem(key, L)                   # the host's own entry, if any
    hand_len, hand = 0, None                           # a hand loan, the host's spelling of it first
    for i in range(top, 2, -1):
        p = next((p for p in stems(i) if p in own or p in D['hand']), None)
        if p is not None:
            hand_len, hand = i, own.get(p) or D['hand'][p]
            break
    loan_len, src, stem = 0, None, None
    for i in range(top, 2, -1):
        for lc, table in D['read'].items():
            if lc == code:
                continue
            stem = next((p for p in stems(i) if p in table), None)
            if stem is not None:
                loan_len, src = i, lc
                break
        if src:
            break
    if src is not None and loan_len > max(spoken_len, hand_len):
        foreign = bool(L.get('foreign')) and re.search(L['foreign'], key[:loan_len]) is not None
        if (foreign or loan_len == len(key)) and not (native_len > loan_len or (native_len == loan_len and not foreign)):
            return with_rest(D['read'][src][stem], loan_len), src
    if hand is not None and hand_len > spoken_len:
        return with_rest(hand[0], hand_len), hand[1]
    return None


def write_loan(t, code, letters_spelling):
    """A host's word written back as the loan it is: the transport of a loan
    word -> how the host writes it (origin.yaml `spell`, `borrowed`), else its
    own spelling, unless the letters' spelling is a word of the host (só stays
    só). None otherwise, and for a word under three letters: a loan is looked up
    from three, as it is read (e, az)."""
    L, D = lex(code), loans()
    if not L or not L['loans'] or not D or len(letters_spelling) < 3:
        return None
    if letters_spelling.lower() in L['native']:
        return None
    digits = ''
    while t and t[-1].isdigit():
        digits, t = t[-1] + digits, t[:-1]
    if not t:
        return None
    k = t[0].lower() + t[1:]
    sp = D['hosts'].get(code, {}).get('write', {}).get(k) or D['write'].get(k)
    return recase(sp, t) + digits if sp is not None else None


def choices(t_tone, code='zh'):
    L = lex(code)
    return (L['choices'].get(t_tone.lower()) if L else None) or []
