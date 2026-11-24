#!/usr/bin/env python3
"""The lexicon layer (data/lexicon/README.md): word-level reading and
writing above the letter stages. Loaded from data/lexicon/<code>.json; a
word of Diafon is stored there as script text.

  lex(code)                 the lexicon, or None
  read_word(word, code)     spelling -> script text, or None
  write_word(toks, code)    a word's points -> spelling; prefix lexicons (hu ly
                            stems) return (stem spelling, the rest of the points)
  choices(syllable, code)   the characters of a toned syllable (zh)
  recase(out, original)     the original's case laid on the script text
"""
import glob
import json
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import script

LEX = os.path.join(ROOT, 'data', 'lexicon')
_CACHE = {}

# a word of text: letters and combining marks (U+0300–036F, where every mark of
# the system lives), an apostrophe inside, tone digits after
_L = r"(?:[^\W\d_]|[̀-ͯ])"
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
    """The original's case on the script text: capitalized -> first point up;
    all in capitals (more than one letter) -> every point up."""
    if not out or not original:
        return out
    if len(original) > 1 and original.isupper():
        toks = script.read(out)
        for t in toks:
            if t.point:
                t.caps = True
        return script.write(toks, join=script.ZWJ in out)
    if original[0].isupper():
        return script.capital(out)
    return out


def split_tones(word):
    """A spelling and the tone digits after it."""
    digits = ''
    while word and word[-1].isdigit():
        digits, word = word[-1] + digits, word[:-1]
    return word, digits


TONE_MARK = {'1': '\u0304', '2': '\u0301', '3': '\u030c', '4': '\u0300'}     # pinyin's: ā á ǎ à
MARK_TONE = {m: d for d, m in TONE_MARK.items()}


def tone_marked(sp, tones):
    """A pinyin syllable with its tone as the mark over its vowel: a or e, the
    o of ou, otherwise the last vowel (hǎo, guó, liú, lǜ). A tone pinyin has no
    mark for, or a syllable with no vowel, keeps the number."""
    if not tones:
        return sp
    low = sp.lower()
    i = next((low.index(v) for v in 'ae' if v in low), -1)
    if i < 0 and 'ou' in low:
        i = low.index('ou')
    if i < 0:
        i = max(low.rfind(v) for v in 'iouü')
    if tones not in TONE_MARK or i < 0:
        return sp + tones
    return ud.normalize('NFC', sp[:i + 1] + TONE_MARK[tones] + sp[i + 1:])


def tone_stripped(word):
    """A spelling without pinyin's tone marks, and where they were: (bare word,
    {index of the marked letter: tone number}). ü keeps its dots."""
    out, marks = '', {}
    for ch in word:
        d = ud.normalize('NFD', ch)
        hit = [MARK_TONE[m] for m in d[1:] if m in MARK_TONE]
        if hit:
            marks[len(out)] = hit[0]
            ch = ud.normalize('NFC', ''.join(m for m in d if m not in MARK_TONE))
        out += ch
    return out, marks


def syllables(key, read):
    """A run of syllables written together -> [(start, syllable)], the longest
    first, stepping back where that leaves a rest no syllable reads. An
    apostrophe parts two; a syllable after another begins with no a, o or e
    (that is what the apostrophe is for: henan is he nan), unless nothing else reads."""
    top = max(map(len, read), default=0)

    def go(i, end, first, strict):
        if i == end:
            return []
        for n in range(min(top, end - i), 0, -1):
            s = key[i:i + n]
            if s in read and (first or not strict or s[0] not in 'aoe'):
                rest = go(i + n, end, False, strict)
                if rest is not None:
                    return [(i, s)] + rest
        return None
    out, i = [], 0
    for part in re.split(r"(['’])", key):
        if part and part not in "'’":
            hit = go(i, i + len(part), True, True) or go(i, i + len(part), True, False)
            if hit is None:
                return None
            out += hit
        i += len(part)
    return out


def read_word(word, code):
    """spelling (tone digits allowed after it) -> script text, the tone as
    its sign, or None. A syllable lexicon also reads a run of syllables
    written together (nihao, henan), and pinyin's tone marks (nǐhǎo, Xī'ān)."""
    L = lex(code)
    if not L:
        return None
    word = ud.normalize('NFC', word)
    if L.get('kind') == 'syllable':
        bare, marks = tone_stripped(word)
        if marks:                                                    # nǐhǎo: each syllable with its own tone
            w, digits = split_tones(bare)
            syls = syllables(w.lower(), L['read'])
            if syls is None:
                return None
            ends = [i for i, _ in syls[1:]] + [len(w)]
            t = ''.join(L['read'][s] + script.tone_signs(next((d for k, d in marks.items() if i <= k < e), ''))
                        for (i, s), e in zip(syls, ends))
            return recase(t, w) + script.tone_signs(digits)
    if L.get('kind') == 'syllable' and re.search(r'\d\D', word):     # ni3hao3: syllable by syllable
        parts = re.findall(r'\D+\d*', word)
        outs = [read_word(p, code) for p in parts]
        return None if None in outs else ''.join(outs)
    word, digits = split_tones(word)
    key = word.lower()
    t = L['read'].get(key)
    if t is None and re.search(r"['’]d$", key):            # poetry's elided -ed: dimm'd reads as dimmed
        t = L['read'].get(key[:-2] + 'ed')
    if t is None and L.get('kind') == 'syllable' and key:
        syls = syllables(key, L['read'])
        if syls is None:
            return None
        t = ''.join(L['read'][s] for _, s in syls)
    return recase(t, word) + script.tone_signs(digits) if t is not None else None


def word_key(toks):
    """A word's points -> (its lexicon key: the script text, the first point
    small, no tone; the tone numbers the word ends in; whether it began with
    a capital, or 'all' for a word all in capitals: its key is all small)."""
    if not toks:
        return '', '', False
    first, last = toks[0], toks[-1]
    up = lambda t: t.caps if t.raw is None else t.raw.isupper()
    shout = len(toks) > 1 and all(up(t) for t in toks)
    head = script.Tok(first.comp, first.long, False, raw=first.raw and first.raw.lower())
    body = [script.Tok(t.comp, t.long, t.caps and not shout, raw=t.raw and (t.raw.lower() if shout else t.raw)) for t in toks[1:]]
    return script.write([head] + body), (last.tones if last.raw is None else ''), 'all' if shout else up(first)


def _cased(sp, caps):
    if caps == 'all' and sp:
        return ud.normalize('NFC', sp.upper())
    return ud.normalize('NFC', sp[0].upper() + sp[1:]) if caps and sp else sp


def write_word(toks, code):
    """A word's points -> spelling. Exact lexicons: the word, or None. Prefix
    lexicons: (stem spelling, the remaining points) for the longest stem the
    word starts with, or None."""
    L = lex(code)
    if not L:
        return None
    key, tones, caps = word_key(toks)
    if not key:
        return None
    if L['match'] == 'prefix':
        best = None
        for stem in L['write']:
            if key.startswith(stem) and (best is None or len(stem) > len(best)) \
                    and not (len(key) > len(stem) and ud.category(key[len(stem)]) == 'Mn'):   # never inside a letter
                best = stem
        if best is None:
            return None
        rest = script.read(key[len(best):])
        if caps == 'all':                                 # the key was all small: the rest takes its capitals back
            rest = [script.Tok(t.comp, t.long, True) if t.point else script.Tok(raw=t.raw.upper()) for t in rest]
        if rest:
            rest[-1].tones = tones
            return _cased(L['write'][best], caps), rest
        return _cased(L['write'][best], caps), [script.Tok(raw=d) for d in tones]
    sp = L['write'].get(key)
    if sp is not None and L.get('tones') == 'marks':
        return tone_marked(_cased(sp, caps), tones)
    return _cased(sp, caps) + tones if sp is not None else None


def apostrophe(before, sp, code):
    """The apostrophe pinyin puts before a syllable that begins with a, o or e
    right after another (Xī'ān), or nothing."""
    L = lex(code)
    if L and L.get('tones') == 'marks' and before and before[-1].isalpha() and sp \
            and ud.normalize('NFD', sp)[0].lower() in 'aoe':
        return "'"
    return ''


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
    own way (Hungarian `spoken`: pech -> peh): (script text, the rest of the
    spelling), or None. The stem is looked up short too (`lengthen`)."""
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
    """A host's word that is a loan: (script text in its own sounds, origin code), or
    None, from the one loan dictionary (loans.json), the same text in every host.
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
            rest = script.write(stages.read_letters(rest, stages.table(stages.load(code))))
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


def write_loan(toks, code, letters_spelling):
    """A host's word written back as the loan it is: the points of a loan
    word -> how the host writes it (origin.yaml `spell`, `borrowed`), else its
    own spelling, unless the letters' spelling is a word of the host (só stays
    só). None otherwise, and for a word under three letters: a loan is looked up
    from three, as it is read (e, az)."""
    L, D = lex(code), loans()
    if not L or not L['loans'] or not D or len(letters_spelling) < 3:
        return None
    if letters_spelling.lower() in L['native']:
        return None
    key, tones, caps = word_key(toks)
    if not key:
        return None
    sp = D['hosts'].get(code, {}).get('write', {}).get(key) or D['write'].get(key)
    return _cased(sp, caps) + tones if sp is not None else None


def choices(syllable, code='zh'):
    """The characters of a syllable in script text, its tone sign after it."""
    L = lex(code)
    toks = script.read(syllable)
    for t in toks:
        t.caps = False
    return (L['choices'].get(script.write(toks)) if L else None) or []
