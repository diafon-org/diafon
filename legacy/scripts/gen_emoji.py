#!/usr/bin/env python3
"""Generate data/emoji.json: emoji as word choices, the way Mandarin
offers characters for a syllable. Type a word, and the emoji named by it are
offered; nothing is replaced unless one is picked.

  sources/emoji/annotations-<code>.json, derived-<code>.json
      CLDR emoji names and keywords per language (Unicode licence v3,
      https://github.com/unicode-org/cldr-json)
  sources/emoji/freq.txt
      the emoji by frequency of use, most used first (Unicode's emoji
      frequency page, https://home.unicode.org/emoji/emoji-frequency/)

Every keyword and name, and each word of a longer one (red heart: red, heart;
a word naming too many emoji is dropped there), is read into its input form
by the language's own reading (English: the lexicon; the others: their
spelling stage). Diafon forms read the same in every language, so the words
of all the languages share one table: kutja and dog both find the dog.
With conversion off the keyboard reads the word typed by the person's own
spellings into input form and matches it on the base letters alone
(Emoji.swift, plain), so the table needs no spelled keys.

The set is curated, not every emoji (2026-11-18): Unicode's 2019 frequency
ranking, its first TOP with gender variants merged into the neutral one (as
Unicode itself counts them), then ADD (the 2024-25 rankings' top emoji that
2019 could not rank, and hand picks), then every country's flag.

  {"rank": [emoji, most used first, then ADD, then the flags in CLDR order],
   "words": {input form: [indices into rank, most used first]}}

The keyboard offers a word's own emoji first, then from the third letter
those of the words it begins (Emoji.swift).

Usage: gen_emoji.py   (sources missing: the committed file is kept)
"""
import json
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import universal_v1 as engine
from universal_v1 import lexicon
from universal_v1 import stages

SRC = os.path.join(engine.alphabet_ref.PATH, 'data', 'lexicon', 'sources', 'emoji')     # CLDR, beside the alphabet's other sources
OUT = os.path.join(ROOT, 'data', 'emoji.json')       # beside the lexicons, not one of them
LANGS = ['en', 'hu', 'cs', 'pl', 'fi', 'tr', 'sw']
TOP = 400               # the most used, from freq.txt (gender variants merged)
# the 2024-25 rankings' top emoji newer than 2019's (Gboard 2025, Meltwater 2024,
# Brandwatch 2025, NYT), then hand picks
ADD = ['🥰', '🫰', '🗿', '🐌']
PER_KEY = 12            # emoji per word, most used first
CROWD = 30              # a word of longer names naming more emoji than this is too vague
WORD = re.compile(r"^[^\W\d_]+$")
TONE = re.compile('[\U0001F3FB-\U0001F3FF]')       # skin tones: left to the system's own picker


def bare(e):
    return e.replace('\ufe0f', '')


def is_emoji(e):
    """A pictograph, not one of the symbols CLDR also names (braces, arrows, math)."""
    if TONE.search(e):
        return False
    return '\ufe0f' in e or any(0x1F000 <= ord(c) <= 0x1FAFF or 0x2600 <= ord(c) <= 0x27BF for c in e)


def names(code):
    """-> {emoji without variation selectors: ([whole one-word names], [words of longer ones])}"""
    out = {}
    for f in (f'annotations-{code}.json', f'derived-{code}.json'):
        d = json.load(open(os.path.join(SRC, f), encoding='utf-8'))
        table = d.get('annotations', d.get('annotationsDerived', {}))
        table = table.get('annotations', table)
        for e, a in table.items():
            whole, parts = out.setdefault(bare(e), ([], []))
            for w in a.get('default', []) + a.get('tts', []):
                w = ud.normalize('NFC', w.strip().lower())
                if WORD.match(w):
                    if len(w) > 1 and w not in whole:
                        whole.append(w)
                    continue
                for p in re.split(r"[\s\-:,.()’'“”]+", w):
                    if len(p) > 2 and WORD.match(p) and p not in parts:
                        parts.append(p)
    return out


def neutral(e, known):
    """A gendered emoji -> its neutral one where CLDR has it (🤷‍♀️ → 🤷, 👩‍⚕️ → 🧑‍⚕️)."""
    n = re.sub('\u200d[\u2640\u2642]', '', e)
    if '\u200d' in n and n[0] in '👨👩':
        n = '🧑' + n[1:]
    return n if n in known else e


def is_flag(e):
    return any(0x1F1E6 <= ord(c) <= 0x1F1FF for c in e) or '\U000E0067' in e


def order():
    """The set, most used first: freq.txt's first TOP (gender merged), ADD, the flags."""
    known = []
    for f in ('annotations-en.json', 'derived-en.json'):
        d = json.load(open(os.path.join(SRC, f), encoding='utf-8'))
        table = d.get('annotations', d.get('annotationsDerived', {}))
        known += [bare(e) for e in table.get('annotations', table)]
    have = set(known)
    rank, seen = [], set()
    def put(e):
        if e not in seen and is_emoji(e):
            seen.add(e); rank.append(e)
    for e in open(os.path.join(SRC, 'freq.txt'), encoding='utf-8').read().split('\n'):
        if e and len(rank) < TOP:
            put(neutral(bare(e), have))
    for e in ADD:
        put(bare(e))
    for e in known:
        if is_flag(e):
            put(e)
    return rank


def reader(code):
    """A word -> its input form in this language, or None where it cannot be read."""
    if code == 'en':
        read = lexicon.lex('en')['read']
        return read.get
    def spelled(w):
        try:
            return stages.parse(w, f'stage:{code}')
        except Exception:
            return None
    return spelled


def key(t):
    """The input form as the keyboard looks it up, or None for an ill-formed one."""
    k = re.sub(r'\d', '', t).lower()
    try:
        return k if k and all(s['kind'] == 'form' for s in engine.segments(k)) else None
    except engine.ParseError:
        return None


def main():
    if not os.path.exists(os.path.join(SRC, 'freq.txt')):
        print(f'{OUT}: sources missing, kept as committed')
        return
    rank = order()
    at = {e: i for i, e in enumerate(rank)}
    # the emoji systems show with their variation selector keep it
    shown = {bare(e): e for e in open(os.path.join(SRC, 'freq.txt'), encoding='utf-8').read().split('\n') if e}
    words = {}
    for code in LANGS:
        if not os.path.exists(os.path.join(SRC, f'annotations-{code}.json')):
            print(f'  {code}: no CLDR annotations, skipped')
            continue
        named, read, cache = names(code), reader(code), {}
        def form(w):
            if w not in cache:
                t = read(w)
                cache[w] = key(t) if t else None
            return cache[w]
        crowd = {}
        for e in rank:
            for w in named.get(e, ([], []))[1]:
                crowd[w] = crowd.get(w, 0) + 1
        n = 0
        for e in rank:
            whole, parts = named.get(e, ([], []))
            for w in whole + [p for p in parts if crowd[p] <= CROWD]:
                k = form(w)
                if k:
                    lst = words.setdefault(k, set())
                    if at[e] not in lst:
                        lst.add(at[e]); n += 1
        print(f'  {code}: {n} word-emoji pairs')
    def look(e):            # a lone symbol drawn as text by default gets the emoji selector
        if e in shown:
            return shown[e]
        return e + '\ufe0f' if len(e) == 1 and 0x2600 <= ord(e) <= 0x27BF else e
    out = {'rank': [look(e) for e in rank],
           'words': {k: sorted(v)[:PER_KEY] for k, v in sorted(words.items())}}
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'{OUT}: {len(rank)} emoji, {len(words)} words · {os.path.getsize(OUT) // 1024} KB')


if __name__ == '__main__':
    main()
