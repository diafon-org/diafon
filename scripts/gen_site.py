#!/usr/bin/env python3
"""The site layer around MkDocs (mkdocs.yml builds docs/ into site/).

Writes the home page's figures into docs/.include (home-*.html and the point
tables, points.html), every glyph computed by the engine and the stages,
never typed by hand.
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
import stages

INC = os.path.join(ROOT, 'docs', '.include')
esc = html.escape


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
HERO = ('stage:en', 'she sells sea shells')


def hero():
    src, text = HERO
    typed = stages.parse(text, src)
    st = stages.load(src[6:])
    for word in text.split():     # every word read by the dictionary, none by fallback
        assert stages.read_word(word, st)[1] == 'lexicon', f'hero: {word} not in the lexicon'
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
    <a class="md-button" href="#typing-a-sound">Learn to type it</a>
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


# ---- the points: consonants and vowels as one kind of table. A tile is
# glyph · input · /reading/, coloured by the operator that makes it; a cell
# holding a pair puts voiceless (unrounded) left, voiced (rounded) right
IPA = {'p': 'p', 'b': 'b', 't': 't', 'd': 'd', 'tj': 'c', 'dj': 'ɟ', 'k': 'k', 'g': 'g', 'kq': 'q',
       'hx': 'ʔ', 'tc': 't͡s', 'dc': 'd͡z', 'tq': 't͡ʃ', 'dq': 'd͡ʒ', 'f': 'f', 'v': 'v', 'tx': 'θ',
       'dx': 'ð', 's': 's', 'z': 'z', 'sj': 'ʃ', 'zj': 'ʒ', 'kx': 'x', 'gx': 'ɣ', 'h': 'h', 'm': 'm',
       'n': 'n', 'nj': 'ɲ', 'nx': 'ŋ', 'r': 'r', 'rc': 'ɾ', 'l': 'l',
       'i': 'i', 'ic': 'y', 'uc': 'ɯ', 'u': 'u', 'ij': 'ɪ', 'iq': 'ʏ', 'uj': 'ʊ', 'e': 'e', 'ec': 'ø',
       'oc': 'ɤ', 'o': 'o', 'aj': 'ə', 'ej': 'ɛ', 'eq': 'œ', 'oj': 'ɔ', 'a': 'a', 'ac': 'ɒ'}
COMPOSED = {'tj', 'dj', 'nj'}     # compositions, shown for orientation
CONSONANTS = (['labial', 'dental', 'alveolar', 'palatal', 'hush', 'velar', 'uvular', 'glottal'], [
    ('stop', {'labial': 'p b', 'alveolar': 't d', 'palatal': 'tj dj', 'velar': 'k g',
              'uvular': 'kq', 'glottal': 'hx'}),
    ('affricate', {'alveolar': 'tc dc', 'hush': 'tq dq'}),
    ('fricative', {'labial': 'f v', 'dental': 'tx dx', 'alveolar': 's z', 'hush': 'sj zj',
                   'velar': 'kx gx', 'glottal': 'h'}),
    ('nasal', {'labial': 'm', 'alveolar': 'n', 'palatal': 'nj', 'velar': 'nx'}),
    ('trill · tap', {'alveolar': 'r rc'}),
    ('lateral', {'alveolar': 'l'}),
])
VOWELS = (['front', 'central', 'back'], [
    ('close', {'front': 'i ic', 'back': 'uc u'}),
    ('near-close', {'front': 'ij iq', 'back': 'uj'}),
    ('close-mid', {'front': 'e ec', 'back': 'oc o'}),
    ('mid', {'central': 'aj'}),
    ('open-mid', {'front': 'ej eq', 'back': 'oj'}),
    ('open', {'central': 'a ac'}),
])


def tile(form):
    kind = form[-1] if len(form) > 1 else 'base'
    return (f'<div class="pt k-{kind}{" cmp" if form in COMPOSED else ""}">'
            f'<span class="nat">{esc(nfc(engine.render(form)))}</span>'
            f'<span class="lab">{form}</span><span class="ipa">/{IPA[form]}/</span></div>')


def point_table(spec, caption):
    cols, rows = spec
    out = [f'<div class="scroll" markdown="0"><table class="grid pts"><caption>{caption}</caption>'
           '<thead><tr><th></th>' + ''.join(f'<th>{c}</th>' for c in cols) + '</tr></thead><tbody>']
    for name, cells in rows:
        out.append(f'<tr><th>{name}</th>' + ''.join(
            f'<td><div class="cell">{"".join(tile(f) for f in cells[c].split())}</div></td>'
            if c in cells else '<td></td>' for c in cols) + '</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)


def points():
    legend = (
        '<div class="klegend" markdown="0">'
        '<span>each tile: <b class="ug">glyph</b> · <code>input</code> · /reading/</span>'
        '<span>colour: the operator that makes it, as on the keyboard</span>'
        '<span>a pair in one cell: voiceless | voiced, unrounded | rounded</span>'
        f'<span>dashed: a composition shown for orientation ({ug(" ".join(engine.render(f) for f in ["tj", "dj", "nj"]))})</span>'
        '</div>')
    return (point_table(CONSONANTS, 'consonants') + point_table(VOWELS, 'vowels') + legend)


def main():
    read = readings()
    write('points.html', points())
    write('home-hero.html', hero())
    write('home-sounds.html', sound_grid())
    write('home-keys.html', keyboard())
    write('home-ops.html', operators(read))
    print('home figures in docs/.include: home-*.html, points.html')


if __name__ == '__main__':
    main()
