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
    row per final, each syllable with its Diafon form and the keys that type it; from the alphabet's own table of
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

    # a family of initials starts a block of columns, a family of finals a block of rows
    col = lambda i: ' class="g"' if i in ('b', 'd', 'g', 'j', 'zh', 'z') else ''
    cell = lambda d: f'<span class="ug">{html.escape(d)}</span><code>{keys(d)}</code>'    # the Diafon form over its keys
    head = '<tr><th></th><th>–</th>' + ''.join(f'<th{col(i)}>{i}{cell(first[i])}</th>' for i in INITIALS) + '</tr>'
    rows = []
    for f, alone in FINALS:
        d = read[alone] if alone else read[SAMPLE[f]][len(first['d']):]
        cells = [f'<th>{f}{cell(d)}</th>']
        for i in [''] + INITIALS:
            py = syllable(i, f, alone)
            cells.append(f'<td{col(i)}>{py}{cell(read[py])}</td>' if py else f'<td{col(i)}></td>')
        rows.append(f'<tr{" class=g" if f in ("i", "u", "ü") else ""}>' + ''.join(cells) + '</tr>')
    rest = ', '.join(f'{py} `{keys(read[py])}`' for py in sorted(left))
    table = f'<table class="py-chart"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table>'
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
    """The languages of a key's letter (a long letter by its own name). A letter that is no point of
    its own (the nasal that is a syllable, m̈ n̈) belongs to the languages whose spelling writes it."""
    if v['point']:
        return use.get(v['point'] + (alphabet.LONG if v['long'] else ''), [])
    g = v['writes']['glyph']
    return [] if v['long'] else sorted(st['name'] for st in alphabet.SPEC['stages'].values() if any(g in k for k in st.get('pairs', {})))


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
    """The letters of at most FEW languages, laid out as the grids above (a row per code, the
    consonants before the vowels, in the alphabet's order), each tile with its languages under the keys."""
    order = 'pbtdkgfvszcxhmnlrjwaeiou'
    rows = []
    for code in CODES:
        tiles = []
        for key, v in sorted(c['keys'].items(), key=lambda kv: order.index(kv[0][0])):
            if key[1:] == code and 0 < len(langs(v, use)) <= FEW:
                names = ''.join(f'<span>{html.escape(n)}</span>' for n in sorted(langs(v, use)))
                tiles.append(tile(key, v).replace('</div>', f'<span class="pt-langs">{names}</span></div>'))
        if tiles:
            label = f'<code>{code}</code>' if code else 'alone'
            rows.append(f'<div class="keys-row"><span class="keys-op">{label}</span>'
                        f'<div class="keys-grid">{"".join(tiles)}</div></div>')
    return '<div class="keys-rows keys-few" markdown="0">' + ''.join(rows) + '</div>'


PAGE = '''---
title: Input
hide:
  - navigation
---

# Input

<link rel="stylesheet" href="input.css">

Diafon is typed on a plain keyboard. Twenty-four keys are its letters. The
other two, `y` and `q`, are not Diafon letters. Typed after a letter, they
put a mark on it.

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

- On r and w, `y` is the double dot above: `ry` is <span class="ug">r̈</span>, `wy` is <span class="ug">ẅ</span>. The anchor on r, <span class="ug">r̦</span> (Czech ř, the Russian soft r), is `ryq`.
- On m and n the double dot above is `qy`: `mqy` is <span class="ug">m̈</span>, `nqy` is <span class="ug">n̈</span>, the nasal that is a syllable before its own letter. `mqymaduqy` is <span class="ug">m̈madụ</span>, and `mm` is still the long m.
- One more `q` makes a dotted vowel long: `oqyq` is <span class="ug">ọ́</span>.
- A nasal vowel is the vowel and `mq`: `bomq` is <span class="ug">boṃ</span>.
- A doubled consonant is the long one, and the key after it marks both: `ssy` is <span class="ug">șș</span>.
- A digit after a letter is its tone: `ni3 kqaw3` is <span class="ug">niˇ ḳawˇ</span>.
- For a plain y, q or digit after a letter, type it twice: `cityy` is city, `h22o` is h2o.

## Every letter and its keys

These are the letters most languages share, each with the keys that type
it. The first row has the letters typed alone. Every row after it has the
letters that take the same keys after them, the simplest first. The letters
of only a few languages are in a table of their own, in the same order.

### Consonants

@CONSONANTS@

### Vowels

@VOWELS@

### Letters of a few languages

Each of these is used by at most three of the languages Diafon covers. They are named under its keys.

@FEW@

## Learn it in your language

The lessons teach the typing one step at a time, with the sounds of one
language. The example words use only what earlier lessons have taught.

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

## Keyboards

This is the only typing Diafon has. The Mac and iPhone keyboards use it. The
Android keyboard still has an older typing with five mark keys, and is
being rebuilt on this one.

<script src="input-data.js"></script>
<script src="diafon-keys.js"></script>
<script src="lessons-data.js"></script>
<script src="input.js"></script>
'''


PINYIN = '''---
title: Pinyin
hide:
  - navigation
  - toc
---

# Pinyin

<link rel="stylesheet" href="../input.css">

Mandarin is typed in Diafon's letters, with a digit after each syllable for
its tone. The Diafon – Pinyin keyboard writes pinyin from the same keys:
`ni3 kqaw3` is <span class="ug">niˇ ḳawˇ</span> in Diafon and nǐ hǎo in pinyin.
The [Input page](../) has the keys of every letter and the lessons.

The table has the @PY_COUNT@ syllables of pinyin, a column for each initial
and a row for each final. Under each is its Diafon form, then the keys that
type it. A syllable is typed as its initial's keys and its final's keys:
hǎo is h `kq`, ao `aw` and the third tone `3`.

<div class="py-card" markdown="0">
  <div class="py-bar">
    <span class="py-legend"><span>hao</span><span class="ug">ḳaw</span><code>kqaw</code><i>pinyin · Diafon · keys</i></span>
    <span class="py-tools">
      <button type="button" data-py="out" title="smaller" aria-label="smaller">−</button>
      <output class="py-zoom">100%</output>
      <button type="button" data-py="in" title="larger" aria-label="larger">+</button>
      <button type="button" data-py="fit">fit</button>
      <button type="button" data-py="full">full screen</button>
      <a class="py-get" href="../pinyin.pdf" download="diafon-pinyin.pdf">download PDF</a>
    </span>
  </div>
  <div class="py-scroll">@PY_CHART@</div>
</div>

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

<script src="../pinyin.js"></script>
'''

# the table as one sheet to download (web/pinyin.pdf): A3 upright, the site's fonts and colours
SHEET = '''<!doctype html><html><head><meta charset="utf-8"><title>Diafon · Pinyin</title><style>
@font-face{font-family:"Diafon";src:url("file://@DOCS@/diafon.woff2")}
@font-face{font-family:"Diafon Sans";src:url("file://@DOCS@/diafon-sans.woff2")}
@font-face{font-family:"Diafon Mono";src:url("file://@DOCS@/diafon-mono.woff2")}
@page{size:297mm 420mm;margin:9mm}
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;font:7.5pt/1.2 "Diafon Sans",sans-serif;color:#1a1d24}
header{display:flex;align-items:baseline;gap:5mm;margin:0 0 3mm}
h1{font:400 17pt/1 "Diafon",serif;margin:0}
header p{margin:0;color:#5b6472}
header .k{margin-left:auto;display:flex;align-items:baseline;gap:2mm}
.ug{font-family:"Diafon",serif;color:#0e7c86}
code{font-family:"Diafon Mono",monospace;color:#5b6472}
table{width:100%;table-layout:fixed;border-collapse:separate;border-spacing:0;border:.3mm solid #5b6472;border-radius:2.5mm;overflow:hidden}
th,td{height:10.25mm;padding:0;text-align:center;vertical-align:middle;white-space:nowrap;border-top:.15mm solid #dde1e8;font-weight:400}
td:empty{background:#f3f4f7}
th{font-weight:700;background:#eef0f4}
table .ug{display:block;font-size:10pt;line-height:1.25;font-weight:400}
table code{display:block;font-size:5.8pt;line-height:1.15}
thead th{border-top:0;border-bottom:.3mm solid #5b6472}
tbody th,thead th:first-child{border-right:.3mm solid #5b6472}
.g{border-left:.3mm solid #5b6472}
tr.g > *{border-top:.3mm solid #5b6472}
footer{display:flex;gap:8mm;margin-top:3mm;color:#5b6472}
footer p{margin:0}
footer b{color:#1a1d24;font-weight:600}
</style></head><body>
<header><h1>Pinyin in Diafon</h1><p>every syllable with its Diafon form and the keys that type it</p>
<span class="k"><span>hao</span><span class="ug" style="font-size:10pt">ḳaw</span><code>kqaw</code><span>pinyin · Diafon · keys</span></span></header>
@PY_CHART@
<footer><p><b>Tones</b> a digit after the syllable: 1 <span class="ug">maˉ</span> mā · 2 <span class="ug">maˊ</span> má · 3 <span class="ug">maˇ</span> mǎ · 4 <span class="ug">maˋ</span> mà · none <span class="ug">ma</span> ma</p>
<p style="margin-left:auto">diafon.io/input/pinyin</p></footer>
</body></html>
'''
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


def sheet(chart):
    """web/pinyin.pdf from the table, printed by Chrome; kept as it is where there is no Chrome."""
    import subprocess
    import tempfile
    out = os.path.join(WEB, 'pinyin.pdf')
    if not os.path.exists(CHROME):
        print('web/pinyin.pdf: not rebuilt (no Chrome to print it)')
        return
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, 'pinyin.html')
        with open(src, 'w', encoding='utf-8') as f:
            f.write(SHEET.replace('@DOCS@', os.path.join(os.path.dirname(ROOT), 'docs')).replace('@PY_CHART@', chart))
        subprocess.run([CHROME, '--headless', '--disable-gpu', '--no-pdf-header-footer', '--virtual-time-budget=3000',
                        f'--print-to-pdf={out}', 'file://' + src], capture_output=True, check=True)
    print('web/pinyin.pdf')


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
    sheet(chart)
    print(f'web/pinyin.md: {count} syllables' + (f', outside the table: {rest}' if rest else ''))
    print(f'web/index.md, web/input-data.js: {len(c["keys"])} keys')


if __name__ == '__main__':
    main()
