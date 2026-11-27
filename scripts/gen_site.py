#!/usr/bin/env python3
"""The site layer around MkDocs (mkdocs.yml builds docs/ into site/).

Writes the home page's figures into docs/.include (home-hero.html, and the two
charts: sounds-consonants.html, sounds-vowels.html), every glyph computed by the
script and the stages, never written by hand.
"""
import html
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import mapping
import script
import stages

INC = os.path.join(ROOT, 'docs', '.include')
esc = html.escape


def nfc(s):
    return ud.normalize('NFC', s)


def ug(s):
    return f'<span class="ug">{esc(nfc(s))}</span>'


def write(name, body):
    open(os.path.join(INC, name), 'w', encoding='utf-8').write(body.strip() + '\n')


# ---- the hero: what the system is for, and one sound in the spellings of a few languages
HERO = [('stage:cs', 'Czech', 'čokoláda', 'č'), ('stage:tr', 'Turkish', 'çikolata', 'ç'),
        ('stage:pl', 'Polish', 'czekolada', 'cz'), ('stage:sw', 'Swahili', 'chokoleti', 'ch'),
        ('stage:en', 'English', 'chocolate', 'ch')]
USES = [('One sound, one letter', 'A sound has the same letter in every language that has it.'),
        ('To and from usual spelling', 'A text converts between Diafon and the usual spelling of each supported '
         'language, Pinyin included.'),
        ('Ordinary text', 'Diafon is plain Unicode, Latin letters with standard marks. Any app, file or '
         'message can carry it.')]


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
    <p class="same-k">One sound, /t͡ʃ/, has four spellings here. Diafon always writes it c̦.</p>
    {''.join(rows)}
  </div>
  <div class="uses">{uses}</div>
  <div class="hero-go">
    <a class="md-button md-button--primary" href="reference/">Reference</a>
  </div>
</div>'''


# ---- the points: consonants and vowels as one kind of table. A tile is
# glyph · /reading/, coloured by the mark it wears; a cell holding a pair puts
# voiceless (unrounded) left, voiced (rounded) right. Points are named as in
# data/script.yaml; the chart writes the affricates with a tie.
TIE = {'ts': 't͡s', 'dz': 'd͡z', 'tʃ': 't͡ʃ', 'dʒ': 'd͡ʒ'}
COMPOSED = {'c', 'ɟ', 'ɲ'}        # letters with a mark, shown where their sound sits, for orientation
CONSONANTS = (['labial', 'dental', 'alveolar', 'postalveolar', 'palatal', 'velar', 'glottal'], [   # lips to throat
    ('stop', {'labial': 'p b', 'alveolar': 't d', 'palatal': 'c ɟ', 'velar': 'k g', 'glottal': 'ʔ'}),
    ('affricate', {'alveolar': 'ts dz', 'postalveolar': 'tʃ dʒ'}),
    ('fricative', {'labial': 'f v', 'dental': 'θ ð', 'alveolar': 's z', 'postalveolar': 'ʃ ʒ',
                   'velar': 'x ɣ', 'glottal': 'h'}),
    ('nasal', {'labial': 'm', 'alveolar': 'n', 'palatal': 'ɲ', 'velar': 'ŋ'}),
    ('trill · tap', {'dental': (3, 'r | ɾ')}),                        # r ṛ side by side, centred under n
    ('approximant', {'labial': 'w', 'alveolar': 'l', 'palatal': 'j'}),     # the glides w j and the lateral l
])
# the mark a point wears -> the colour class of its edge
MARK_CLASS = {(): 'base', ('anchor',): 'j', ('dot',): 'x', ('twodots',): 'y', ('flip',): 'c', ('underdot',): 'j'}
MARK_GLOSS = [   # (class, on a consonant, on a vowel)
    ('base', 'no mark', 'no mark'),
    ('j', 'the anchor: hushed or soft', 'the dot below: more open'),
    ('x', 'the dot: a neighbouring sound', None),
    ('c', None, 'the double dot: moved front or back'),
    ('y', 'the double dot below: a sound made further back', None),
]


def kind(name):
    return MARK_CLASS[script.POINTS[name][1]]


def glyph(name):
    return nfc(script.glyph(name))


def sound(name):
    return TIE.get(name, name)


def vowel_areas():
    """-> {area point: (covers, {split point: (reading, [languages])})}, from the
    mapping: what each area covers, and which languages write each split."""
    m = yaml.safe_load(open(os.path.join(ROOT, 'data', 'mapping.yaml'), encoding='utf-8'))
    _, vows, over, _, _, _ = mapping.load()
    langs = mapping.load_languages()
    out = {}
    for area, a in m['areas'].items():
        area = str(area)
        pt = script.point(area)
        covers = [nfc(i) for i, pts in vows.items() if pts == (pt,)]
        splits = {}
        for sf, qs in (a.get('split') or {}).items():
            sp = script.point(str(sf))
            users = sorted(c for c, d in langs.items() for i, q in d['vowels'].items()
                           if q != 'X' and mapping.nfd(i) in over.get(c, {})
                           and mapping.within(over[c][mapping.nfd(i)][0], sp))
            splits[str(sf)] = (' '.join(qs), sorted(set(users)))
        out[area] = (covers, splits)
    return out


# a card's edge: an SVG outline, as the vowel chips draw theirs, so both are drawn the same way
EDGE = '<svg class="edge" aria-hidden="true"><rect width="100%" height="100%" rx="8"/></svg>'


# ---- the mouth, side view, lips on the left: the consonant columns run from
# the lips to the throat, and each header marks its place
MOUTH_ROOF = ('M14 30 Q8 31 6 37 Q6 41 10 42 L19 41 L19 34 Q22 29 27 26 Q36 18 50 15 Q66 13 78 17 '
              'Q87 21 89 28 Q90 33 87 35')                                   # upper lip, teeth, palate, velum, uvula
MOUTH_JAW = 'M10 50 Q6 51 6 55 Q8 61 14 62 L19 62 L19 55'                  # lower lip and teeth
MOUTH_TONGUE = 'M19 55 Q20 50 25 48 Q40 38 58 35 Q76 34 84 44 Q90 54 90 70 L90 84 L30 84 Q22 76 19 62 Z'
MOUTH_BACK = 'M94 22 Q99 30 98 50 L98 86'                                  # the back of the throat
PLACE = {'labial': (8, 46), 'dental': (19, 38), 'alveolar': (27, 26), 'postalveolar': (37, 20), 'palatal': (52, 15),
         'velar': (76, 17), 'glottal': (94, 78)}


def mouth(place):
    x, y = PLACE[place]
    return ('<svg class="mouth" viewBox="0 0 104 90" aria-hidden="true">'
            f'<path class="tongue" d="{MOUTH_TONGUE}"/><path d="{MOUTH_ROOF}"/><path d="{MOUTH_JAW}"/>'
            f'<path d="{MOUTH_BACK}"/><circle cx="{x}" cy="{y}" r="7"/></svg>')


# ---- the vowel triangle: front on the left (the lips' side), close at the
# top. Three rows, close, mid and open, each on a guide line and mirrored
# about the middle; a vowel only some languages write is dashed: the more
# open ones small, just under their letter on a thin tie, the front a beside a
VT_ROWS = {'close': 82, 'mid': 292, 'open': 506}
VT_POS = {   # area or split point -> (x, y) in the 840 x 600 figure
    'i': (120, 82), 'y': (214, 82), 'ɯ': (626, 82), 'u': (720, 82),
    'ɪ': (160, 166), 'ʊ': (680, 166),
    'e': (224, 292), 'ø': (318, 292), 'ɤ': (522, 292), 'o': (616, 292),
    'ɛ': (264, 376), 'ɔ': (576, 376),
    'æ': (373, 506), 'a': (467, 506),
}
VT_BIG = {'æ'}      # a split drawn as a full card: the front a is a's partner under the double dot


def chip(glyphs, sounds, kind, cls=''):
    """A chip: the letters and the sounds, edged in the colour of the mark. Both charts draw every card
    with this, so they look the same; a split (small) or a composition (dashed) adds a class.
    The outline sits half a stroke (0.6) inside the box."""
    small = 'split' in cls
    rect = ('<rect x="-26.4" y="-24.4" width="52.8" height="49.8" rx="9"/>' if small else
            '<rect x="-43.4" y="-35.4" width="86.8" height="72.8" rx="13"/>')
    y = (0, 17) if small else (2, 26)
    return (f'<g class="chip k-{kind}{" " + cls if cls else ""}">{rect}'
            f'<text class="nat" y="{y[0]}">{esc(glyphs)}</text>'
            f'<text class="ipa" y="{y[1]}">/{esc(sounds)}/</text></g>')


def chip_svg(names, cls=''):
    """One consonant cell as a chip of its own svg, the vowel chips' size."""
    kinds = {kind(n) for n in names}
    assert len(kinds) == 1, f'a cell mixes marks: {names}'
    g = chip(' '.join(glyph(n) for n in names), ' '.join(sound(n) for n in names), kinds.pop(), cls)
    return f'<svg class="chips card" viewBox="-44.6 -36.6 89.2 75.2" width="89" height="75" aria-hidden="true">{g}</svg>'


def vowel_triangle(areas):
    left = lambda y: 40 + (y - 30) * 260 / 540          # the slanted edges at a height
    out = ['<div class="scroll vt-frame"><div class="chart-cap">vowels</div>'          # framed and titled as the consonants
           '<figure class="vt" markdown="0"><svg class="chips" viewBox="0 0 840 600" role="img" '
           'aria-label="The vowels in the vowel triangle, front on the left, close at the top">',
           '<polygon class="edge" points="40,30 800,30 540,570 300,570"/>',
           '<text class="axis" x="40" y="22">front</text><text class="axis" x="800" y="22" text-anchor="end">back</text>']
    for label, y in VT_ROWS.items():
        x = left(y)
        out.append(f'<line class="guide" x1="{x:.0f}" y1="{y}" x2="{840 - x:.0f}" y2="{y}"/>'
                   f'<text class="axis" x="{x - 10:.0f}" y="{y + 4}" text-anchor="end">{label}</text>')
    chips = []
    for area, (covers, splits) in areas.items():
        if area not in VT_POS:
            continue
        k = kind(area)
        ax, ay = VT_POS[area]
        for sf, (reading, users) in splits.items():
            if not users:
                continue                                   # a split no language writes is left out
            sx, sy = VT_POS[sf]
            if sf not in VT_BIG:
                out.append(f'<line class="tie" x1="{ax}" y1="{ay}" x2="{sx}" y2="{sy}"/>')
            chips.append(f'<g transform="translate({sx},{sy})">'
                         + chip(glyph(sf), reading, kind(sf), 'cmp' if sf in VT_BIG else 'split') + '</g>')
        chips.append(f'<g transform="translate({ax},{ay})">'
                     + chip(glyph(area), ' '.join(covers), k) + '</g>')
    out += chips
    out.append('</svg></figure></div>')
    return ''.join(out)


def point_table(spec, caption):
    cols, rows = spec

    def cards(spec):
        groups = [g.split() for g in spec.split('|')]          # 'r | ɾ': a card each
        return ''.join(chip_svg(names, 'cmp' if set(names) <= COMPOSED else '') for names in groups)
    shy = lambda c: c.replace('postalveolar', 'post\u00adalveolar')          # breaks as post-alveolar, if at all
    head = (lambda c: f'<th title="{c}">{mouth(c)}<span>{shy(c)}</span></th>') if caption == 'consonants' else (lambda c: f'<th>{c}</th>')
    out = [f'<div class="scroll" markdown="0"><table class="grid pts"><caption>{caption}</caption>'
           '<thead><tr><th></th>' + ''.join(head(c) for c in cols) + '</tr></thead><tbody>']
    for name, cells in rows:
        tds, skip = [], 0
        for c in cols:
            if skip:
                skip -= 1
                continue
            if c not in cells:
                tds.append('<td></td>')
                continue
            span, spec = cells[c] if isinstance(cells[c], tuple) else (1, cells[c])
            skip = span - 1                                   # (3, 'r | ɾ'): across three columns, centred on the middle one
            cls = 'cell cluster' if '|' in spec else 'cell'
            tds.append(f'<td{f" colspan={span}" if span > 1 else ""}><div class="{cls}">{cards(spec)}</div></td>')
        label = name.replace('approximant', 'approx\u00adimant')        # can break on a phone
        out.append(f'<tr><th>{label}</th>' + ''.join(tds) + '</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)


def colours(vowels=False):
    """The edge colours: a swatch and the mark it stands for, one per line."""
    rows = [(k, v if vowels else c) for k, c, v in MARK_GLOSS if (v if vowels else c and k != 'y')]   # no double dot below on the consonant chart
    return '<ul class="ops">' + ''.join(f'<li><i class="sw k-{k}"></i>{t}</li>' for k, t in rows) + '</ul>'


def key(rows, cls=''):
    """A chart's key, under it: a sample on the left, what it means on the right."""
    return (f'<dl class="chartkey{" " + cls if cls else ""}" markdown="0">'
            + ''.join(f'<dt>{dt}</dt><dd>{dd}</dd>' for dt, dd in rows) + '</dl>')


def consonant_chart():
    return '<div class="chart" markdown="0">' + point_table(CONSONANTS, 'consonants') + key([
        (chip_svg(['p', 'b']), 'a card holds the letters and their sounds, the voiceless one first'),
        ('lips → throat', 'the columns follow where the sound is made, shown in each small profile'),
        ('edge colour', 'the mark on the letter' + colours()),
        (chip_svg(['c', 'ɟ'], 'cmp'), 'a dashed card holds marked letters, placed where their sound is made '
         f'({ug(" ".join(glyph(n) for n in sorted(COMPOSED, key=lambda n: script.POINTS[n])))})'),
    ]) + '</div>'


# ---- the letters a language adds: every consonant off the chart, by what it
# is in the languages that write it (data/mapping.yaml), so a letter with two
# roles shows in two rows
ADDED = [   # (what they are, the test on (letter, marks, the language's sound))
    ('soft sibilants', lambda l, m, ipa: m == ('dot',) and l in 'szcx'),
    ('soft consonants', lambda l, m, ipa: m == ('anchor',)),
    ('retroflex', lambda l, m, ipa: ipa[0] in 'ʈɖɳɭ'),
    ('emphatic', lambda l, m, ipa: 'ˤ' in ipa),
    ('made further back', lambda l, m, ipa: ipa[0] in 'qħʕ'),
]


def added_table():
    on_chart = {script.POINTS[n] for _, cells in CONSONANTS[1] for v in cells.values()
                for n in (v[1] if isinstance(v, tuple) else v).replace('|', ' ').split()}
    langs = mapping.load_languages()
    rows = {label: ({}, set()) for label, _ in ADDED}            # label -> ({composition: sounds}, languages)
    for code in langs:
        for pts, reads in mapping.language_points(code).items():
            comp = pts[0][0]
            if script.vocalic(comp) or comp in on_chart or not comp[1]:
                continue
            for ipa, _ in reads:
                label = next(lb for lb, test in ADDED if test(comp[0], comp[1], ipa))
                rows[label][0].setdefault(comp, set()).add(ipa.rstrip('ʰʱːʼ'))
                rows[label][1].add(langs[code]['name'].split(' (')[0].replace('Hindi-Urdu', 'Hindi').replace('Mandarin Chinese', 'Mandarin'))
    order = lambda c: ('pbfvmtdnszcxrlkgh'.index(c[0]), c[1])           # lips to throat, as the chart
    out = ['<div class="opswrap"><table class="ops marks added">',
           '<tr><th>Letters</th><th>What they are</th><th>Sounds</th><th>Where</th></tr>']
    for label, _ in ADDED:
        comps, where = rows[label]
        cs = sorted(comps, key=order)
        letters = ' '.join(nfc(script.glyph(script.NAME[c]) if c in script.NAME else script.write([script.Tok(c, False, False)])) for c in cs)
        sounds = ' '.join(dict.fromkeys(i for c in cs for i in sorted(comps[c])))        # in the letters' order
        out.append(f'<tr><td class="ex">{ug(letters)}</td><td>{label}</td><td>/{esc(sounds)}/</td>'
                   f'<td>{", ".join(sorted(where))}</td></tr>')
    nasal = sorted({langs[c]['name'].split(' (')[0].replace('Hindi-Urdu', 'Hindi') for c in langs
                    for pts in mapping.language_points(c) if any(comp == script.POINTS['ⁿ'] for comp, _ in pts)})
    out.append(f'<tr><td class="ex">{ug(nfc(script.glyph("ⁿ")))}</td><td>the nasal letter, which makes the vowel before it nasal</td>'
               f'<td>/◌̃/</td><td>{", ".join(nasal)}</td></tr>')
    out.append('</table></div>')
    return '\n'.join(out)


def vowel_chart():
    return '<div class="chart vt-chart" markdown="0">' + vowel_triangle(vowel_areas()) + key([
        ('front · back', 'front is on the left and back on the right, and the double dot moves a letter to the other side'),
        (f'<span class="chipkey area k-base">{EDGE}a</span>', 'a card holds a letter and every sound it covers'),
        (f'<span class="chipkey split cmp k-j">{EDGE}ẹ</span>', 'a dashed card is written only by languages with two vowels in that area '
         '(rule 2 on the Reference page)'),
        ('edge colour', 'the mark on the letter' + colours(vowels=True)),
    ], cls='vt-key') + '</div>'


def main():
    write('sounds-consonants.html', consonant_chart())
    write('sounds-added.html', added_table())
    write('sounds-vowels.html', vowel_chart())
    write('home-hero.html', hero())
    print('home figures in docs/.include: home-hero.html, sounds-consonants.html, sounds-vowels.html')


if __name__ == '__main__':
    main()
