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


# ---- the hero: what the system is for, and one familiar word shown four ways
HERO = [('stage:cs', 'Czech', 'čokoláda', 'č'), ('stage:tr', 'Turkish', 'çikolata', 'ç'),
        ('stage:hu', 'Hungarian', 'csokoládé', 'cs'), ('stage:sw', 'Swahili', 'chokoleti', 'ch'),
        ('stage:en', 'English', 'chocolate', 'ch')]
USES = [('One alphabet for many languages', 'A phonemic Latin alphabet. Each letter stands for one sound and is read '
         'much the same way across languages, so a new word can be read close to how it is said.'),
        ('The 26 Latin letters as easy input', 'Everything is typed with the plain Latin letters, without dead keys. '
         'There are a few letter combinations to learn.'),
        ('Your language\'s own spelling too', 'Text can be converted to and from the usual spelling of the supported '
         'languages, Pinyin included.'),
        ('One keyboard layout for fast typing', 'The supported languages can all be typed '
         'on one layout, without switching between keyboards.')]


def hero():
    rows = []
    for src, lang, word, letters in HERO:
        out = nfc(stages.convert(word, src, 'script'))
        assert out.startswith('c\u0326'), f'hero: {word} -> {out}'
        rows.append(f'<div class="same-row"><span class="same-lang">{esc(lang)}</span>'
                    f'<span class="same-nat"><b>{esc(letters)}</b>{esc(word[len(letters):])}</span>'
                    f'<span class="same-arrow" aria-hidden="true">→</span>'
                    f'<span class="same-dia ug"><b>{esc(out[0:2])}</b>{esc(out[2:])}</span></div>')
    uses = ''.join(f'<div class="use"><h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for t, d in USES)
    mark = open(os.path.join(ROOT, 'docs', 'logo', 'mark-inline.svg'), encoding='utf-8').read().strip()
    mark = mark.replace('width="1em" height="1em"', 'class="hero-mark"')
    return f'''
<div class="hero" markdown="0">
  <div class="hero-title">{mark}<div><h1>Diafon</h1>
    <p class="hero-tag">One alphabet for the sounds of many languages.</p></div></div>
  <div class="same">
    <p class="same-k">One sound, /t͡ʃ/, spelled five ways. Diafon writes it c̦ in each of them.</p>
    {''.join(rows)}
  </div>
  <div class="uses">{uses}</div>
  <div class="hero-go">
    <a class="md-button md-button--primary" href="learn/">Start learning</a>
    <a class="md-button" href="master/">Reference</a>
    <a class="md-button" href="tools/">Keyboards and fonts</a>
  </div>
</div>'''


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
  <span><span class="key vowel">a</span> 5 vowels</span>
  <span><span class="key cons">t</span> 15 consonants</span>
  <span><span class="key op op-any">j</span> 6 operators, which change the sound before them</span>
</div>'''


# ---- the operators: what each does, with its marks
OP_ORDER = 'jxcqyw'          # the operators' fixed order, everywhere on the site
OPS = {                      # operator: (on a consonant: gloss, examples), (on a vowel: gloss, examples)
    'j': (('hushed or soft', ['sj', 'zj', 'tj', 'nj']), ('more open; on a, the schwa', ['ij', 'ej', 'oj', 'aj'])),
    'x': (('a fixed nearby sound', ['tx', 'dx', 'kx', 'nx', 'hx']), ('the glide: i to j, u to w', ['ix', 'ux'])),
    'c': (('adds a hiss', ['tc', 'dc']), ('lip rounding swapped', ['ic', 'ec', 'uc', 'ac'])),
    'q': (('c and j together', ['tq', 'dq']), ('c and j together', ['eq', 'iq', 'aq'])),
    'y': (("the language's own variant", ['ty', 'ny', 'sjy']), ('nasal', ['ay', 'ey', 'oy'])),
    'w': (('long: written double', ['sjw']), ('long', ['aw', 'iw', 'ew'])),
}


def operators(read):
    read = dict(read, aj='ə')     # ạ is the schwa area; English's /ʌ/ is only its commonest reading
    def side(use):
        if use is None:
            return '<div class="opside none">no vowel use</div>'
        gloss, forms = use
        ex = ''.join(
            f'<span class="opx"><span class="opx-g ug">{esc(nfc(engine.render(f)))}</span>'
            f'<code>{f}</code><span class="opx-r">/{esc(read[f])}/</span></span>'
            for f in forms if f in read)
        return f'<div class="opside"><span class="opside-g">{esc(gloss)}</span><div class="opcard-x">{ex}</div></div>'
    head = ('<div class="optab-h"><span></span><span>after a consonant</span><span>after a vowel</span></div>')
    rows = ''.join(f'<div class="optab-r"><span class="key op op-{o}">{o}</span>{side(OPS[o][0])}{side(OPS[o][1])}</div>'
                   for o in OP_ORDER)
    return f'<div class="optab" markdown="0">{head}{rows}</div>'


# ---- the points: consonants and vowels as one kind of table. A tile is
# glyph · input · /reading/, coloured by the operator that makes it; a cell
# holding a pair puts voiceless (unrounded) left, voiced (rounded) right
IPA = {'p': 'p', 'b': 'b', 't': 't', 'd': 'd', 'tj': 'c', 'dj': 'ɟ', 'k': 'k', 'g': 'g', 'kq': 'q',
       'hx': 'ʔ', 'tc': 't͡s', 'dc': 'd͡z', 'tq': 't͡ʃ', 'dq': 'd͡ʒ', 'f': 'f', 'v': 'v', 'tx': 'θ',
       'dx': 'ð', 's': 's', 'z': 'z', 'sj': 'ʃ', 'zj': 'ʒ', 'kx': 'x', 'gx': 'ɣ', 'h': 'h', 'm': 'm',
       'n': 'n', 'nj': 'ɲ', 'nx': 'ŋ', 'r': 'r', 'rc': 'ɾ', 'l': 'l'}       # vowels: from the areas
COMPOSED = {'tj', 'dj', 'nj'}     # compositions, shown for orientation
CONSONANTS = (['labial', 'dental', 'alveolar', 'postalveolar', 'palatal', 'velar', 'uvular', 'glottal'], [   # lips to throat
    ('stop', {'labial': 'p b', 'alveolar': 't d', 'palatal': 'tj dj', 'velar': 'k g',
              'uvular': 'kq', 'glottal': 'hx'}),
    ('affricate', {'alveolar': 'tc dc', 'postalveolar': 'tq dq'}),
    ('fricative', {'labial': 'f v', 'dental': 'tx dx', 'alveolar': 's z', 'postalveolar': 'sj zj',
                   'velar': 'kx gx', 'glottal': 'h'}),
    ('nasal', {'labial': 'm', 'alveolar': 'n', 'palatal': 'nj', 'velar': 'nx'}),
    ('trill · tap', {'alveolar': 'r rc'}),
    ('lateral', {'alveolar': 'l'}),
])
def vowel_areas():
    """-> {area form: (covers, {split form: (reading, [languages])})}, from the
    mapping: what each area covers, and which languages write each split."""
    import gen_master
    m = __import__('yaml').safe_load(open(os.path.join(ROOT, 'data', 'mapping.yaml')))
    _, vows, over, _, _, _ = gen_master.load_mapping()
    langs = gen_master.load_languages()
    out = {}
    for area, a in m['areas'].items():
        covers = [nfc(i) for i, f in vows.items() if f == area]
        splits = {}
        for sf, qs in (a.get('split') or {}).items():
            users = sorted(c for c, d in langs.items() for i, q in d['vowels'].items()
                           if q != 'X' and (over.get(c, {}).get(gen_master.nfd(i)) or '').startswith(sf))
            splits[sf] = (' '.join(qs), sorted(set(users)))
        out[area] = (covers, splits)
    return out


def tile(form):
    kind = form[-1] if len(form) > 1 else 'base'
    return (f'<div class="pt k-{kind}{" cmp" if form in COMPOSED else ""}">'
            f'<span class="nat">{esc(nfc(engine.render(form)))}</span>'
            f'<span class="lab">{form}</span><span class="ipa">/{IPA[form]}/</span></div>')


# ---- the mouth, side view, lips on the left: the consonant columns run from
# the lips to the throat, and each header marks its place
MOUTH_ROOF = ('M14 30 Q8 31 6 37 Q6 41 10 42 L19 41 L19 34 Q22 29 27 26 Q36 18 50 15 Q66 13 78 17 '
              'Q87 21 89 28 Q90 33 87 35')                                   # upper lip, teeth, palate, velum, uvula
MOUTH_JAW = 'M10 50 Q6 51 6 55 Q8 61 14 62 L19 62 L19 55'                  # lower lip and teeth
MOUTH_TONGUE = 'M19 55 Q20 50 25 48 Q40 38 58 35 Q76 34 84 44 Q90 54 90 70 L90 84 L30 84 Q22 76 19 62 Z'
MOUTH_BACK = 'M94 22 Q99 30 98 50 L98 86'                                  # the back of the throat
PLACE = {'labial': (8, 46), 'dental': (19, 38), 'alveolar': (27, 26), 'postalveolar': (37, 20), 'palatal': (52, 15),
         'velar': (76, 17), 'uvular': (88, 34), 'glottal': (94, 78)}


def mouth(place):
    x, y = PLACE[place]
    return ('<svg class="mouth" viewBox="0 0 104 90" aria-hidden="true">'
            f'<path class="tongue" d="{MOUTH_TONGUE}"/><path d="{MOUTH_ROOF}"/><path d="{MOUTH_JAW}"/>'
            f'<path d="{MOUTH_BACK}"/><circle cx="{x}" cy="{y}" r="7"/></svg>')


# ---- the vowel triangle: front on the left (the lips' side), close at the
# top; each area a chip where its reference vowel sits, its split a small
# dashed chip where the split vowel sits, a soft band between the two
VT_POS = {   # area or split form -> (x, y) in the 840 x 600 figure
    'i': (114, 76), 'ic': (208, 76), 'uc': (632, 76), 'u': (726, 76),
    'ij': (152, 158), 'iq': (244, 158), 'uj': (700, 158),
    'e': (218, 306), 'ec': (312, 306), 'aj': (420, 336), 'oc': (528, 306), 'o': (622, 306),
    'ej': (266, 392), 'eq': (346, 396), 'oj': (590, 392),
    'a': (382, 530), 'ac': (460, 530),
}


def vowel_triangle(areas):
    out = ['<figure class="vt" markdown="0"><svg viewBox="0 0 840 600" role="img" '
           'aria-label="The vowel areas in the vowel triangle, front on the left, close at the top, with their splits">',
           '<polygon class="edge" points="40,30 800,30 540,570 300,570"/>',
           '<text class="axis" x="40" y="22">front</text><text class="axis" x="800" y="22" text-anchor="end">back</text>'
           '<text class="axis" x="30" y="76" text-anchor="end">close</text><text class="axis" x="290" y="560" text-anchor="end">open</text>']
    import gen_master
    names = {c: re.sub(r'\s*\(.*\)$', '', d['name']) for c, d in gen_master.load_languages().items()}
    chips = []
    for area, (covers, splits) in areas.items():
        if area not in VT_POS:
            continue
        kind = area[-1] if len(area) > 1 else 'base'
        ax, ay = VT_POS[area]
        for sf, (reading, users) in splits.items():
            sx, sy = VT_POS[sf]
            if not users:
                continue                                   # a split no language writes is left out
            out.append(f'<line class="band k-{kind}" x1="{ax}" y1="{ay}" x2="{sx}" y2="{sy}"/>')
            lines = [names[u] for u in users]
            who = ''.join(f'<text class="who" y="{38 + 12 * n}">{esc(t)}</text>' for n, t in enumerate(lines))
            chips.append(f'<g class="chip split k-{sf[-1]}" transform="translate({sx},{sy})">'
                         f'<rect x="-27" y="-25" width="54" height="51" rx="9"/>'
                         f'<text class="nat" y="-4">{esc(nfc(engine.render(sf)))}</text>'
                         f'<text class="lab" y="9">{sf}</text><text class="ipa" y="20">/{reading}/</text>{who}</g>')
        chips.append(f'<g class="chip k-{kind}" transform="translate({ax},{ay})">'
                     f'<rect x="-44" y="-36" width="88" height="74" rx="13"/>'
                     f'<text class="nat" y="-6">{esc(nfc(engine.render(area)))}</text>'
                     f'<text class="lab" y="14">{area}</text><text class="ipa" y="30">/{" ".join(covers)}/</text></g>')
    out += chips
    out.append('</svg></figure>')
    return ''.join(out)


def point_table(spec, caption):
    cols, rows = spec

    def cell(forms):
        return ''.join(tile(f) for f in forms)
    head = (lambda c: f'<th title="{c}">{mouth(c)}<span>{c}</span></th>') if caption == 'consonants' else (lambda c: f'<th>{c}</th>')
    out = [f'<div class="scroll" markdown="0"><table class="grid pts"><caption>{caption}</caption>'
           '<thead><tr><th></th>' + ''.join(head(c) for c in cols) + '</tr></thead><tbody>']
    for name, cells in rows:
        out.append(f'<tr><th>{name}</th>' + ''.join(
            f'<td><div class="cell">{cell(cells[c].split())}</div></td>'
            if c in cells else '<td></td>' for c in cols) + '</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)


def points():
    legend = (
        '<div class="klegend" markdown="0">'
        '<span>each tile: <b class="ug">glyph</b> · <code>input</code> · /reading/</span>'
        '<span>colour: the operator that makes it, as on the keyboard</span>'
        '<span>a pair in one cell: voiceless | voiced, unrounded | rounded</span>'
        '<span>consonants: lips to throat, the place marked in each column\'s profile</span>'
        '<span>vowels: front left, close at the top; a chip covers an area, /all it covers/; '
        'the small dashed chip is its split, written only by the languages named under it</span>'
        f'<span>dashed: a composition shown for orientation ({ug(" ".join(engine.render(f) for f in ["tj", "dj", "nj"]))})</span>'
        '</div>')
    return (point_table(CONSONANTS, 'consonants') + vowel_triangle(vowel_areas()) + legend)


def main():
    read = readings()
    write('points.html', points())
    write('home-hero.html', hero())
    write('home-keys.html', keyboard())
    write('home-ops.html', operators(read))
    print('home figures in docs/.include: home-*.html, points.html')


if __name__ == '__main__':
    main()
