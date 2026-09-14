#!/usr/bin/env python3
"""The hand frame round trip, as tests. Run: python3 tests/test_hand_frame.py  (or pytest tests/)

A synthetic drawing is written into the frame (strokes, filled rings,
nested transforms, class styles, colour names, a stray, a pale doodle, a
hidden shape) and read back:

1. Only the drawn cells count; pale and hidden shapes are not ink; a shape
   between cells is a stray.
2. Pieces come out as drawn: t̤ three (base and two dots), i two, ș one
   (the anchor attaches), o one ring.
3. Glyph files land under the font glyph names in the font_svg format
   (capitals by codepoint: a and A cannot share a case-insensitive folder).
4. Registration: the same drawing with every id stripped, re-scaled and
   shifted under a new viewBox traces to byte-identical outlines.
"""
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'fonts', 'tools'))
import hand_frame as HF
import hand_read as HR

MAN = json.load(open(HF.OUT_JSON, encoding='utf-8'))
CELLS = {c['form']: c for c in MAN['cells']}
S = MAN['scale']


def P(form, fx, fy):
    """font units (x from the cell's left edge, y from its baseline) -> frame."""
    c = CELLS[form]
    return c['box'][0] + fx * S, c['baseline'] - fy * S


def stroke(form, pts, sw=70, close=False, color='#000'):
    d = 'M' + ' L'.join('%.1f %.1f' % P(form, *p) for p in pts) + ('Z' if close else '')
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw * S:.1f}" '
            'stroke-linecap="round" stroke-linejoin="round"/>')


def drawing():
    ink = []
    ink.append(stroke('t', [(600, 720), (600, 60), (700, 0), (800, 60)]))
    ink.append(stroke('t', [(480, 520), (760, 520)]))
    cx, cy = P('o', 700, 270)
    r1, r2 = 270 * S, 200 * S                       # a ring: outer + reversed inner
    ink.append(f'<path fill="#111" d="M{cx - r1} {cy}A{r1} {r1} 0 1 0 {cx + r1} {cy}'
               f'A{r1} {r1} 0 1 0 {cx - r1} {cy}Z M{cx - r2} {cy}A{r2} {r2} 0 1 1 {cx + r2} {cy}'
               f'A{r2} {r2} 0 1 1 {cx - r2} {cy}Z"/>')
    ink.append(stroke('i', [(700, 536), (700, 0)]))
    dx, dy = P('i', 700, 680)
    ink.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="{45 * S:.1f}" fill="black"/>')
    tx0, ty0 = P('txy', 0, 0)                       # t̤ inside a translated, flipped group
    ink.append(f'<g transform="translate({tx0:.1f} {ty0:.1f}) scale({S:.3f} {-S:.3f})">'
               '<path d="M600 720 L600 60 L700 0 L800 60" fill="none" stroke="#000" '
               'stroke-width="70" stroke-linecap="round"/>'
               '<path d="M480 520 L760 520" fill="none" stroke="#000" stroke-width="70" '
               'stroke-linecap="round"/>'
               '<circle cx="620" cy="-140" r="45"/><circle cx="780" cy="-140" r="45"/></g>')
    ink.append(stroke('sj', [(820, 460), (700, 540), (560, 480), (620, 300), (780, 220),
                             (760, 40), (600, 10), (560, 60), (640, -120), (660, -320)]))
    d = re.search(r'd="([^"]+)"', stroke('a', [(560, 536), (820, 536), (820, 0), (560, 0)],
                                         close=True)).group(1)
    ink.append(f'<path class="st0" d="{d}"/>')     # Illustrator-style class fill
    ink.append(stroke('A', [(500, 0), (700, 714), (900, 0)], color='navy'))
    ink.append(stroke('A', [(580, 250), (820, 250)], color='rgb(20,20,60)'))
    b = CELLS['p']['box']
    ink.append(f'<rect x="{b[0] + 10}" y="{b[3] + 3}" width="30" height="6" fill="#000"/>')  # stray
    ink.append(stroke('k', [(500, 0), (900, 500)], color='#d0d0d0'))                        # pale
    ink.append(stroke('m', [(500, 0), (900, 500)]).replace('<path', '<path display="none"'))
    frame = open(HF.OUT_SVG, encoding='utf-8').read()
    drawn = frame.replace('<title>', '<style>.st0{fill:#222;stroke:none}</style><title>', 1)
    marker = 'inkscape:label="ink (draw here)">\n</g>'
    assert marker in drawn
    return drawn.replace(marker, marker[:-4] + '\n'.join(ink) + '\n</g>')


def flattened(drawn):
    W, H = MAN['size']
    flat = re.sub(r' id="[^"]*"', '', drawn)
    flat = flat.replace(f'viewBox="0 0 {W} {H}" width="{W}" height="{H}"',
                        f'viewBox="0 0 {W * 0.5 + 100} {H * 0.5 + 50}" '
                        f'width="{W * 0.5 + 100}" height="{H * 0.5 + 50}"')
    flat = flat.replace('<g inkscape:groupmode="layer" inkscape:label="frame (reference, locked)" '
                        'sodipodi:insensitive="true">', '<g transform="matrix(0.5 0 0 0.5 100 50)">', 1)
    flat = flat.replace('<g inkscape:groupmode="layer" inkscape:label="ink (draw here)">',
                        '<g transform="translate(100 50) scale(0.5)">', 1)
    assert flat != drawn
    return flat


def run(svg_text, tmp, tag):
    src = os.path.join(tmp, f'{tag}.svg')
    open(src, 'w', encoding='utf-8').write(svg_text)
    out = os.path.join(tmp, tag)
    rep = os.path.join(tmp, f'{tag}.json')
    rc = HR.main([src, '--out', out, '--review', os.path.join(tmp, f'{tag}-review.svg'),
                  '--report', rep])
    assert rc == 0
    return out, json.load(open(rep, encoding='utf-8'))


def _setup():
    tmp = tempfile.mkdtemp(prefix='diafon-hand-')
    drawn = drawing()
    out, rep = run(drawn, tmp, 'drawn')
    return tmp, drawn, out, rep


def test_ink_selection():
    tmp, _, _, rep = _setup()
    try:
        drawn = {g['form'] for g in rep['glyphs']}
        assert drawn == {'t', 'o', 'i', 'txy', 'sj', 'a', 'A'}, drawn
        assert len(rep['strays']) == 1, rep['strays']
        assert rep['registration'].endswith('in place')
    finally:
        shutil.rmtree(tmp)


def test_pieces():
    tmp, _, _, rep = _setup()
    try:
        by = {g['form']: g for g in rep['glyphs']}
        assert by['txy']['pieces'] == 3 and by['txy']['pieces_expected'] == 3
        assert sorted(c['zone'] for c in by['txy']['pieces_detail']) == ['base', 'below', 'below']
        assert by['i']['pieces'] == 2
        assert by['sj']['pieces'] == 1 and by['sj']['pieces_expected'] == 1
        assert by['o']['pieces'] == 1
        assert not by['sj']['flags'] and not by['o']['flags'], (by['sj'], by['o'])
    finally:
        shutil.rmtree(tmp)


def test_glyph_files():
    tmp, _, out, rep = _setup()
    try:
        names = sorted(os.listdir(out))
        assert names == ['a.svg', 'i.svg', 'o.svg', 's_uni0326.svg', 't.svg', 't_uni0324.svg',
                         'uni0041.svg'], names          # A by codepoint: a and A share a disk
        cap = open(os.path.join(out, 'uni0041.svg'), encoding='utf-8').read()
        assert 'data-glyph="A"' in cap
        svg = open(os.path.join(out, 't_uni0324.svg'), encoding='utf-8').read()
        assert 'viewBox="-500 0 2000 1362"' in svg and '<g id="glyph">' in svg
        assert 'data-form="txy"' in svg and int(re.search(r'data-advance="(\d+)"', svg).group(1)) > 300
        d = re.search(r'<g id="glyph">\s*<path fill="#111" d="([^"]+)"', svg).group(1)
        assert d.count('M') == 3, d.count('M')      # three closed contours
    finally:
        shutil.rmtree(tmp)


def test_registration_is_exact():
    tmp, drawn, out, rep = _setup()
    try:
        out2, rep2 = run(flattened(drawn), tmp, 'flat')
        assert rep2['registration'].startswith('4 corners, scale 2.0000'), rep2['registration']
        for fn in os.listdir(out):
            a = open(os.path.join(out, fn), encoding='utf-8').read()
            b = open(os.path.join(out2, fn), encoding='utf-8').read()
            assert a == b, fn
        assert {g['form'] for g in rep2['glyphs']} == {g['form'] for g in rep['glyphs']}
    finally:
        shutil.rmtree(tmp)


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn()
            print(f'ok  {name}')
