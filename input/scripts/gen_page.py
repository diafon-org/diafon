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


# --- Mandarin: pinyin by its parts ---

INITIALS = ['b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'zh', 'ch', 'sh', 'r', 'z', 'c', 's']
# a final and how pinyin spells it as a syllable of its own (none: it has no such syllable)
FINALS = [('a', 'a'), ('o', 'o'), ('e', 'e'), ('ai', 'ai'), ('ei', 'ei'), ('ao', 'ao'), ('ou', 'ou'), ('an', 'an'), ('en', 'en'),
          ('ang', 'ang'), ('eng', None), ('ong', None), ('er', 'er'),
          ('i', 'yi'), ('ia', 'ya'), ('ie', 'ye'), ('iao', 'yao'), ('iu', 'you'), ('ian', 'yan'), ('in', 'yin'),
          ('iang', 'yang'), ('ing', 'ying'), ('iong', 'yong'),
          ('u', 'wu'), ('ua', 'wa'), ('uo', 'wo'), ('uai', 'wai'), ('ui', 'wei'), ('uan', 'wan'), ('un', 'wen'),
          ('uang', 'wang'), ('ueng', 'weng'),
          ('ü', 'yu'), ('üe', 'yue'), ('üan', 'yuan'), ('ün', 'yun')]
SAMPLE = {'eng': 'deng', 'ong': 'dong'}       # a syllable that shows a final with no syllable of its own, after d


def pinyin():
    """-> (the chart, the number of syllables): the usual table of pinyin, a column per initial and a
    row per final, each syllable with the keys that type it; from the alphabet's own table of
    syllables (data/lexicon/zh.json)."""
    sys.path.insert(0, os.path.join(ROOT, 'scripts'))
    import gen_lessons
    read = gen_lessons.lexicon.lex('zh')['read']
    keys = lambda d: html.escape(gen_lessons.typed(gen_lessons.script.read(d)))
    first = {i: os.path.commonprefix([d for py, d in read.items() if split(py)[0] == i]) for i in INITIALS}
    left = set(read)

    def syllable(i, f, alone):
        """How pinyin spells an initial with a final: ü is u after j q x, a final alone has its own spelling."""
        for py in ([alone] if not i else [i + f.replace('ü', 'u')] if i in 'jqx' and f[0] != 'u' else [] if i in 'jqx' else [i + f]):
            if py in left and (i or py == alone):
                left.discard(py)
                return py
        return None

    head = '<tr><th></th><th>–</th>' + ''.join(f'<th>{i}<code>{keys(first[i])}</code></th>' for i in INITIALS) + '</tr>'
    rows = []
    for f, alone in FINALS:
        d = read[alone] if alone else read[SAMPLE[f]][len(first['d']):]
        cells = [f'<th>{f}<code>{keys(d)}</code></th>']
        for i in [''] + INITIALS:
            py = syllable(i, f, alone)
            cells.append(f'<td>{py}<code>{keys(read[py])}</code></td>' if py else '<td></td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    rest = ', '.join(f'{py} `{keys(read[py])}`' for py in sorted(left))
    table = f'<div class="py-scroll" markdown="0"><table class="py-chart"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'
    return table, len(read), rest


def split(py):
    return next(((i, py[len(i):]) for i in sorted(INITIALS, key=len, reverse=True) if py.startswith(i)), ('', py))


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
- On m and n the double dot above is `qy`: `mqy` is <span class="ug">m̈</span>, `nqy` is <span class="ug">n̈</span>, the nasal that is a syllable before its own letter: `mqymaduqy` is <span class="ug">m̈madụ</span>. `mm` stays the long m.
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


PINYIN = '''---
title: Pinyin
hide:
  - navigation
---

# Pinyin

<link rel="stylesheet" href="../input.css">

Mandarin is typed in Diafon's letters, with a digit after each syllable for
its tone. The Diafon – Pinyin keyboard writes pinyin from the same keys:
`ni3 kqaw3` is <span class="ug">niˇ ḳawˇ</span> in Diafon and nǐ hǎo in pinyin.
The [Input page](../) has the keys of every letter and the lessons.

## The syllables

The @PY_COUNT@ syllables of pinyin, a column for each initial and a row for
each final, with the keys under each. A syllable is typed as its initial's
keys and its final's keys: hǎo is h `kq`, ao `aw` and the third tone `3`.

@PY_CHART@

- After z, c, s, zh, ch, sh and r the i is <span class="ug">ï</span>, `iy`: shi is `syiy`.
- After j, q, x and y pinyin writes ü as u. It is still <span class="ug">ü</span>, `uy`: xu is `squy`.
- After b, p, m and f pinyin writes uo as o: bo is `puo`.
@PY_REST@

## The tones

| Tone | Key | Diafon | Pinyin |
|---|---|---|---|
| first, high | `1` | <span class="ug">maˉ</span> | mā |
| second, rising | `2` | <span class="ug">maˊ</span> | má |
| third, low | `3` | <span class="ug">maˇ</span> | mǎ |
| fourth, falling | `4` | <span class="ug">maˋ</span> | mà |
| neutral | none | <span class="ug">ma</span> | ma |
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
    chart, count, rest = pinyin()
    with open(os.path.join(WEB, 'pinyin.md'), 'w', encoding='utf-8') as f:
        f.write(PINYIN.replace('@PY_CHART@', chart).replace('@PY_COUNT@', str(count))
                .replace('@PY_REST@', f'- Outside the table: {rest}.' if rest else ''))
    print(f'web/pinyin.md: {count} syllables' + (f', outside the table: {rest}' if rest else ''))
    print(f'web/index.md, web/input-data.js: {len(c["keys"])} keys')


if __name__ == '__main__':
    main()
