#!/usr/bin/env python3
"""Generate the Input page: web/index.md (the page) and web/input-data.js
(the compiled profile, without its vectors, for the page's scripts).

The page is written here and published by the alphabet's site, which copies
web/ as it is. Its scripts are web/diafon-keys.js (the typing), web/input.js
(the try-out and the lessons) and web/lessons-data.js (scripts/gen_lessons.py).
"""
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from engine import alphabet, profile

PROFILE = 'diafon-v1'
WEB = os.path.join(ROOT, 'web')
CLASS = {'anchor': 'j', 'dot': 'x', 'twodots': 'y', 'flip': 'c', 'underdot': 'j'}
EDGE = '<svg class="edge" aria-hidden="true"><rect width="100%" height="100%" rx="8"/></svg>'


def tile(key, v):
    marks = v['to'][1:]
    k = CLASS[marks[0]] if marks else 'base'
    g = v['writes']['long' if v['long'] else 'glyph']
    return (f'<div class="pt k-{k}">{EDGE}<span class="nat">{html.escape(g)}</span>'
            f'<span class="lab">{html.escape(key)}</span></div>')


FEW = 3     # a letter of at most this many languages is listed apart, with its languages


def usage():
    """-> {point id: [language names]}: the languages that write a sound with the point."""
    use = {}
    for lang in alphabet.SPEC['languages'].values():
        for sound in lang['sounds'].values():
            if sound['frequency'] != 'X':
                for p in sound['points']:
                    names = use.setdefault(p, [])
                    if lang['name'] not in names:
                        names.append(lang['name'])
    return use


def langs(v, use):
    """The languages of a key's letter (a long letter by its own name); none for a key that is no point."""
    return use.get(v['point'] + (alphabet.LONG if v['long'] else ''), []) if v['point'] else []


CODES = ['', 'y', 'q', 'yq', 'qy', 'qyq']      # the keys after a letter, the simplest first


def grid(c, letters, use):
    """The letters by what is typed after them: one row per code, the simplest first."""
    rows = []
    for code in CODES:
        tiles = [tile(key, v) for key, v in c['keys'].items()
                 if key[0] in letters and key[1:] == code and len(langs(v, use)) > FEW]
        if tiles:
            label = f'<code>{code}</code>' if code else 'alone'
            rows.append(f'<div class="keys-row"><span class="keys-op">{label}</span>'
                        f'<div class="keys-grid">{"".join(tiles)}</div></div>')
    return '<div class="keys-rows" markdown="0">' + ''.join(rows) + '</div>'


def few(c, use):
    rows = ['| Letter | Keys | Languages |', '|---|---|---|']
    for key, v in sorted(c['keys'].items(), key=lambda kv: CODES.index(kv[0][1:]) if kv[0][1:] in CODES else len(CODES)):
        if 0 < len(langs(v, use)) <= FEW:
            g = v['writes']['long' if v['long'] else 'glyph']
            rows.append(f'| <span class="ug">{html.escape(g)}</span> | `{key}` | {", ".join(sorted(langs(v, use)))} |')
    return '\n'.join(rows)


PAGE = '''---
title: Input
hide:
  - navigation
---

# Input

<link rel="stylesheet" href="input.css">

Diafon is typed on a plain keyboard. Twenty-four keys are its letters. The
other two, `y` and `q`, are not letters of Diafon: typed after a letter,
they put its mark on.

<div class="keys-try" markdown="0">
  <textarea id="keys-in" spellcheck="false" autocomplete="off" autocapitalize="off"
    placeholder="type here: cyak a joq soq, ni3 kqaw3, bomq"></textarea>
  <div class="keys-out ug" id="keys-out" data-empty="what you type appears here in Diafon"></div>
</div>

## The two keys

| After | `y` | `q` | `yq` | `qy` |
|---|---|---|---|---|
| a consonant | the anchor: `sy` <span class="ug">ș</span> | the dot: `tq` <span class="ug">ṭ</span> | the double dot below: `tyq` <span class="ug">t̤</span> | |
| a vowel | the double dot: `uy` <span class="ug">ü</span> | long: `aq` <span class="ug">á</span> | both: `oyq` <span class="ug">ő</span> | the dot below: `eqy` <span class="ug">ẹ</span> |

- On r and w the `y` is the double dot above: `ry` is <span class="ug">r̈</span>, `wy` is <span class="ug">ẅ</span>. The anchor on r, <span class="ug">r̦</span> (Czech ř, the Russian soft r), is `ryq`.
- On a, `ay` is the schwa <span class="ug">ạ</span> and `aqy` the front <span class="ug">ä</span>.
- A dotted vowel is made long with one more `q`: `oqyq` is <span class="ug">ọ́</span>.
- A nasal vowel is the vowel and `mq`: `bomq` is <span class="ug">boṃ</span>.
- A doubled consonant is the long one, and the key after it marks both: `ssy` is <span class="ug">șș</span>.
- A digit after a letter is its tone: `ni3 kqaw3` is <span class="ug">niˇ ḳawˇ</span>.
- For a plain y, q or digit after a letter, type it twice: `cityy` is city, `h22o` is h2o.

## Every letter and its keys

The letters most languages share, with the keys that type each: first the
letters typed alone, then a row for each thing typed after a letter, the
simplest first. The letters of only a few languages follow in their own
table, in the same order.

### Consonants

@CONSONANTS@

### Vowels

@VOWELS@

### Letters of a few languages

Each of these is used by one to three of the languages Diafon covers.

@FEW@

## Learn it in your language

The lessons teach the typing one idea at a time, in the sounds of one
language. Example words use only what the lessons so far have taught.

<div class="learn-bar" markdown="0">
  <label>language <select id="ln-lang" autocomplete="off"></select></label>
  <span class="learn-note" id="ln-note"></span>
</div>

<div class="learn" markdown="0">
  <nav class="learn-steps" id="ln-steps" aria-label="lessons"></nav>
  <article class="lesson" id="ln-lesson"></article>
  <div class="learn-move">
    <button type="button" id="ln-prev">← previous</button>
    <button type="button" id="ln-next" class="primary">next →</button>
  </div>
</div>

## Other ways of typing

This is the only typing Diafon has now. An older one, with five mark keys,
is no longer offered. The keyboards for the Mac, the iPhone and Android
still use it and are being rebuilt on this one.

<script src="input-data.js"></script>
<script src="diafon-keys.js"></script>
<script src="lessons-data.js"></script>
<script src="input.js"></script>
'''


def main():
    c = profile.compiled(PROFILE)
    data = {k: v for k, v in c.items() if k != 'vectors'}
    with open(os.path.join(WEB, 'input-data.js'), 'w', encoding='utf-8') as f:
        f.write('// generated by scripts/gen_page.py from spec/%s.json; do not edit\n' % PROFILE)
        f.write('const DIAFON_PROFILE = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    use = usage()
    page = (PAGE.replace('@CONSONANTS@', grid(c, 'pbtdkgfvszcxhmnlrjw', use)).replace('@VOWELS@', grid(c, 'aeiou', use))
            .replace('@FEW@', few(c, use)))
    with open(os.path.join(WEB, 'index.md'), 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'web/index.md, web/input-data.js: {len(c["keys"])} keys')


if __name__ == '__main__':
    main()
