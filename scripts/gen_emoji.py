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

Each one-word keyword or name is read into its input form by the language's
own reading (English: the lexicon; Hungarian: its spelling stage), so the key
is what a person types, in the universal input or the language's spelling.

  {"rank": [emoji, most used first],
   "choices": {code: {input form: [emoji, most used first]}}}

Usage: gen_emoji.py   (sources missing: the committed file is kept)
"""
import json
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine
import lexicon
import stages

SRC = os.path.join(ROOT, 'data', 'lexicon', 'sources', 'emoji')
OUT = os.path.join(ROOT, 'data', 'emoji.json')       # beside the lexicons, not one of them
LANGS = ['en', 'hu']
TOP = 600               # the most used emoji offered; the rest are rare enough to look up
PER_KEY = 8             # choices per word, most used first
WORD = re.compile(r"^[^\W\d_]+$")


def bare(e):
    return e.replace('️', '')


def names(code):
    """-> {emoji without variation selectors: [one-word names and keywords]}"""
    out = {}
    for f in (f'annotations-{code}.json', f'derived-{code}.json'):
        d = json.load(open(os.path.join(SRC, f), encoding='utf-8'))
        table = d.get('annotations', d.get('annotationsDerived', {}))
        table = table.get('annotations', table)
        for e, a in table.items():
            words = out.setdefault(bare(e), [])
            for w in a.get('default', []) + a.get('tts', []):
                w = ud.normalize('NFC', w.strip().lower())
                if WORD.match(w) and len(w) > 1 and w not in words:
                    words.append(w)
    return out


def reader(code):
    """A word -> its input form in this language, or None where it cannot be read."""
    if code == 'en':
        read = lexicon.lex('en')['read']
        return read.get
    def hu(w):
        try:
            return stages.parse(w, f'stage:{code}')
        except Exception:
            return None
    return hu


def main():
    if not os.path.exists(os.path.join(SRC, 'freq.txt')):
        print(f'{OUT}: sources missing, kept as committed')
        return
    rank = [e for e in open(os.path.join(SRC, 'freq.txt'), encoding='utf-8').read().split('\n') if e][:TOP]
    out = {'rank': rank, 'choices': {}}
    for code in LANGS:
        named, read = names(code), reader(code)
        choices, missed = {}, 0
        for e in rank:
            for w in named.get(bare(e), []):
                t = read(w)
                if not t:
                    missed += 1
                    continue
                key = re.sub(r'\d', '', t).lower()
                try:
                    if not all(s['kind'] == 'form' for s in engine.segments(key)):
                        continue
                except engine.ParseError:
                    continue
                lst = choices.setdefault(key, [])
                if e not in lst and len(lst) < PER_KEY:
                    lst.append(e)
        out['choices'][code] = dict(sorted(choices.items()))
        print(f'  {code}: {len(choices)} words, {missed} names unread')
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'{OUT}: {len(rank)} emoji · {os.path.getsize(OUT) // 1024} KB')


if __name__ == '__main__':
    main()
