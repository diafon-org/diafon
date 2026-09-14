#!/usr/bin/env python3
"""The glyph description tool, as tests. Run: python3 tests/test_hand_design.py  (or pytest tests/)

1. The starter description parses, proofs without errors, and every feature
   resolves: strokes, smooth loops, fills with a hole, dots, composition
   with offsets and flips.
2. Named heights and arithmetic resolve against the font's guides.
3. Errors are reported by glyph, not raised: an unknown glyph in use, a
   self-use, a bad point.
4. The build writes font_svg-format files with the expected contours (the
   ring two, t̤ three, a with its hole two) and zero advance for bare marks;
   files of glyphs no longer described are removed, other files untouched.
"""
import os
import shutil
import sys
import tempfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'fonts', 'tools'))
import hand_design as HD
import hand_frame as HF

REF = HF.Ref()
GUIDES = HF.guides(REF, HF.matrix())


def load(text, tmp):
    path = os.path.join(tmp, 'd.yaml')
    open(path, 'w', encoding='utf-8').write(text)
    return HD.Design(path, REF, GUIDES)


def test_starter_resolves():
    d = HD.Design(HD.SPEC, REF, GUIDES)
    for name in d.glyphs:
        els = d.elements(name)
        assert els, name
    kinds = {e['kind'] for e in d.elements('t_uni0324')}
    assert kinds == {'stroke', 'dot'}
    own = [e for e in d.elements('t_uni0324') if e['own']]
    assert not own                       # a pure composition owns no points
    svg, errors = HD.proof(d, REF, {}, GUIDES)
    assert not errors and svg.count('<rect') == len(d.glyphs) + 1


def test_heights_and_arithmetic():
    tmp = tempfile.mkdtemp()
    try:
        d = load('glyphs:\n  x:\n    strokes:\n      - 0,base 100,xh-36 200,asc 300,cap*2 400,desc\n', tmp)
        pts = d.elements('x')[0]['points']
        assert pts == [(0, 0), (100, 500), (200, 760), (300, 1428), (400, -330)], pts
    finally:
        shutil.rmtree(tmp)


def test_flip_and_offset():
    tmp = tempfile.mkdtemp()
    try:
        d = load('glyphs:\n  m:\n    strokes: ["0,0 100,200"]\n'
                 '  f:\n    use: [{glyph: m, flip: x, at: [50, 10]}]\n', tmp)
        pts = d.elements('f')[0]['points']
        # mirrored about the part's own centre (x 50), then moved by 50,10
        assert [tuple(round(v) for v in p) for p in pts] == [(150, 10), (50, 210)], pts
    finally:
        shutil.rmtree(tmp)


def test_errors_are_reported():
    tmp = tempfile.mkdtemp()
    try:
        d = load('glyphs:\n  a:\n    use: [nothere]\n  b:\n    use: [b]\n'
                 '  c:\n    strokes: ["10 20"]\n  ok:\n    dots: ["0,0 10"]\n', tmp)
        _, errors = HD.proof(d, REF, {}, GUIDES)
        assert len(errors) == 3, errors
        assert any('no such glyph' in e for e in errors)
        assert any('uses itself' in e for e in errors)
        assert any('expected a point' in e for e in errors)
    finally:
        shutil.rmtree(tmp)


def test_build():
    tmp = tempfile.mkdtemp()
    try:
        out = os.path.join(tmp, 'glyphs')
        os.makedirs(out)
        open(os.path.join(out, 'keep.svg'), 'w').write('<svg/>')      # not ours: stays
        d = HD.Design(HD.SPEC, REF, GUIDES)
        HD.build(d, REF, {}, out)
        names = sorted(os.listdir(out))
        assert 'uni0041.svg' in names and 'keep.svg' in names and 't_uni0324.svg' in names, names
        def contours(fn):
            s = open(os.path.join(out, fn), encoding='utf-8').read()
            d_ = s.split('<g id="glyph">')[1].split('d="')[1].split('"')[0]
            return d_.count('M'), s
        assert contours('o.svg')[0] == 2
        assert contours('a.svg')[0] == 2
        assert contours('t_uni0324.svg')[0] == 3
        assert contours('t.svg')[0] == 1
        n, s = contours('uni0326.svg')
        assert 'data-advance="0"' in s and 'hand_design.py' in s
        # a shrunken description removes its own stale files only
        spec2 = os.path.join(tmp, 'small.yaml')
        open(spec2, 'w').write('glyphs:\n  t:\n    strokes: ["300,700 300,0"]\n')
        HD.build(HD.Design(spec2, REF, GUIDES), REF, {}, out)
        assert sorted(os.listdir(out)) == ['keep.svg', 't.svg'], os.listdir(out)
    finally:
        shutil.rmtree(tmp)


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn()
            print(f'ok  {name}')
