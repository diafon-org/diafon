#!/usr/bin/env python3
"""The site layer around MkDocs (mkdocs.yml builds docs/ into site/).

Writes the home page's figures into docs/.include/home-*.html, every glyph
and reading computed by the engine and the stages, never typed by hand; and
refreshes the navigation block on the one standalone app page, the font
review (the master tables are a MkDocs page, docs/master.md).
"""
import html
import json
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine
import pages
import stages

STATIC_PAGES = ['inspect.html']
INC = os.path.join(ROOT, 'docs', '.include')
esc = html.escape


def refresh_nav():
    for fn in STATIC_PAGES:
        path = os.path.join(ROOT, 'docs', fn)
        page = open(path).read()
        block = pages.nav_block(fn)
        if pages.MARK0 in page:
            page = re.sub(re.escape(pages.MARK0) + '.*?' + re.escape(pages.MARK1),
                          lambda m: block, page, count=1, flags=re.S)
        else:
            anchor = '<main class="wrap">'
            assert anchor in page, f'{fn}: no wrap to hang the nav on'
            page = page.replace(anchor, anchor + '\n\n' + block, 1)
        open(path, 'w').write(page)


def readings():
    """The most common reading of every form, as the try-out shows it."""
    src = open(os.path.join(ROOT, 'docs', 'play-data.js'), encoding='utf-8').read()
    return json.loads(re.search(r'const DIA = (.*);\n', src).group(1))['default']


def nfc(s):
    return ud.normalize('NFC', s)


def ug(s):
    return f'<span class="ug">{esc(nfc(s))}</span>'


def write(name, body):
    open(os.path.join(INC, name), 'w', encoding='utf-8').write(body.strip() + '\n')


# ---- the hero: one line of text in its three forms
HERO = ('stage:en', 'ship chip thin think')


def hero():
    src, text = HERO
    typed = stages.parse(text, src)
    assert stages.convert(typed, 'transport', src) == text, 'hero example must round-trip'
    mark = open(os.path.join(ROOT, 'docs', 'logo', 'mark-inline.svg'), encoding='utf-8').read().strip()
    mark = mark.replace('width="1em" height="1em"', 'class="hero-mark"')
    name = stages.load(src[6:])['name']
    return f'''
<div class="hero" markdown="0">
  <div class="hero-title">{mark}<div><h1>Diafon</h1>
    <p class="hero-tag">One keyboard, one script, every language.</p></div></div>
  <p class="hero-sub">Type the sounds of any language on the 26 letters you already have.
  Read them as one script, or as that language's own spelling.</p>
  <div class="flow">
    <div class="flow-step"><span class="flow-k">you type</span><code class="flow-v">{esc(typed)}</code></div>
    <div class="flow-arrow" aria-hidden="true">→</div>
    <div class="flow-step main"><span class="flow-k">everyone reads</span><span class="flow-v ug">{esc(nfc(engine.render(typed)))}</span></div>
    <div class="flow-arrow" aria-hidden="true">→</div>
    <div class="flow-step"><span class="flow-k">{esc(name)}</span><span class="flow-v">{esc(text)}</span></div>
  </div>
  <div class="hero-go">
    <a class="md-button md-button--primary" href="master.html">Open the master tables</a>
    <a class="md-button" href="typing.html">Learn to type it</a>
  </div>
</div>'''


# ---- one sound, one letter: the same two sounds in five spellings
SOUNDS = [('sj', 'ʃ'), ('tq', 't͡ʃ')]
WORDS = [   # source, the word per sound, the letters that spell the sound
    ('stage:en', [('ship', 'sh'), ('chip', 'ch')]),
    ('stage:hu', [('sok', 's'), ('csók', 'cs')]),
    ('stage:cs', [('šest', 'š'), ('čaj', 'č')]),
    ('stage:tr', [('şeker', 'ş'), ('çay', 'ç')]),
    ('stage:pl', [('szafa', 'sz'), ('czas', 'cz')]),
]


def sound_grid():
    head = ''.join(f'<th>/{ipa}/ <span class="sg-arrow">→</span> {ug(engine.render(f))} '
                   f'<code>{f}</code></th>' for f, ipa in SOUNDS)
    rows = []
    for src, words in WORDS:
        st = stages.load(src[6:])
        cells = []
        for (word, letters), (form, _) in zip(words, SOUNDS):
            typed = stages.parse(word, src)
            g = nfc(engine.render(form))
            if g not in nfc(engine.render(typed)):
                continue    # the stage reads this sound otherwise: the row says nothing
            spelled = esc(word).replace(esc(letters), f'<mark>{esc(letters)}</mark>', 1)
            script = esc(nfc(engine.render(typed))).replace(g, f'<mark>{g}</mark>', 1)
            cells.append(f'<td><span class="sg-word">{spelled}</span>'
                         f'<span class="sg-to">→</span><span class="sg-script ug">{script}</span></td>')
        if len(cells) == len(SOUNDS):
            rows.append(f'<tr><th>{esc(st["name"].replace(" spelling", ""))}</th>{"".join(cells)}</tr>')
    return f'''
<div class="sg-wrap" markdown="0"><table class="sg">
<thead><tr><th></th>{head}</tr></thead>
<tbody>{"".join(rows)}</tbody>
</table></div>'''


# ---- the keyboard: twenty sounds, six modifiers
KEYS = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm']


def keyboard():
    rows = []
    for row in KEYS:
        keys = ''.join(
            f'<span class="key {"op op-" + k if k in "cjqxwy" else "vowel" if k in "aeiou" else "cons"}">{k}</span>'
            for k in row)
        rows.append(f'<div class="kb-row">{keys}</div>')
    return f'''
<div class="kb" markdown="0">
  {"".join(rows)}
</div>
<div class="kb-legend" markdown="0">
  <span><span class="key vowel">a</span> <b>5 vowels</b> are sounds</span>
  <span><span class="key cons">t</span> <b>15 consonants</b> are sounds</span>
  <span><span class="key op op-j">j</span> <b>6 operators</b> change the sound before them</span>
</div>'''


# ---- the operators: what each does, with its marks
OPS = [
    ('j', 'softens or hushes; lowers a vowel one step', ['sj', 'zj', 'tj', 'oj', 'aj']),
    ('x', 'shifts the manner: stop to fricative', ['tx', 'dx', 'nx', 'kx', 'hx']),
    ('c', 'makes an affricate; flips a vowel\'s rounding', ['tc', 'ic', 'uc', 'ac']),
    ('q', 'c and j in one: the hush affricates', ['tq', 'dq', 'eq', 'aq']),
    ('w', 'long', ['aw', 'iw', 'ew']),
    ('y', 'leans back: retroflex; on a vowel, nasal', ['ty', 'ny', 'sjy', 'ay']),
]


def operators(read):
    cards = []
    for op, gloss, forms in OPS:
        ex = ''.join(
            f'<span class="opx"><span class="opx-g ug">{esc(nfc(engine.render(f)))}</span>'
            f'<code>{f}</code><span class="opx-r">/{esc(read[f])}/</span></span>'
            for f in forms)
        cards.append(f'<div class="opcard"><div class="opcard-h"><span class="key op op-{op}">{op}</span>'
                     f'<span>{esc(gloss)}</span></div><div class="opcard-x">{ex}</div></div>')
    sp = ''.join(f'<span class="opx"><span class="opx-g ug">{esc(nfc(engine.render(f)))}</span>'
                 f'<code>{f}</code></span>' for f in ['txy', 'sxy', 'kxy', 'lxy'])
    cards.append(f'<div class="opcard special"><div class="opcard-h">'
                 f'<span class="key op op-x">x</span><span class="key op op-y">y</span>'
                 f'<span>the special: a language\'s own series, read per language '
                 f'(emphatic in Arabic, soft in Russian, ejective in Georgian)</span></div>'
                 f'<div class="opcard-x">{sp}</div></div>')
    return f'<div class="opgrid" markdown="0">{"".join(cards)}</div>'


def main():
    read = readings()
    write('home-hero.html', hero())
    write('home-sounds.html', sound_grid())
    write('home-keys.html', keyboard())
    write('home-ops.html', operators(read))
    refresh_nav()
    print(f'home figures in docs/.include/home-*.html; nav refreshed on {", ".join(STATIC_PAGES)}')


if __name__ == '__main__':
    main()
