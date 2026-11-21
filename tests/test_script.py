#!/usr/bin/env python3
"""The script layer's law, as tests. Run: python3 tests/test_script.py  (or pytest tests/)

1. One system: every glyph is a letter of the script plus the system's own
   combining marks and nothing else; the marks are those data/script.yaml
   defines, each with one meaning on every letter.
2. Normalized: every glyph is NFC, so a pair Unicode precomposes (ș ṭ ä á)
   appears as that letter, and a pair it does not (t̤ k̦ ȁ) stays a sequence;
   both are the same text to Unicode, and there is exactly one spelling.
3. Capitals follow the float rule: no capital in the system descends, so a
   capital wears its mark below (G̦, P̦), and the base letter of a capital is
   the base letter of its small form.
4. One reading: no two compositions share a glyph, a point's name is its
   own (NFC, one composition), and every pair of points written one after
   the other reads back as that pair; two equal consonants are the long one,
   and a consonant before its own long one reads as the long one first. A
   letter takes its marks before a doubling (dd̦ is d and d̦).
5. The points file is what the generator writes.
"""
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gen_points
import script

MARKS = {ch for m in script.MARKS.values() for ch in m.values()}
POINTS = gen_points.points()


def glyphs():
    for comp in script.compositions():
        for long in (False, True):
            yield comp, long, script.glyph(comp, long), script.glyph(comp, long, caps=True)


def test_one_system():
    for comp, long, g, cap in glyphs():
        for x in (g, cap):
            for ch in ud.normalize('NFD', x):
                if ud.combining(ch):
                    assert ch in MARKS, (comp, x, f'U+{ord(ch):04X} is not one of the system\'s marks')
                else:
                    assert ch.isascii() and ch.isalpha(), (comp, x, ch)


def test_normalized():
    for comp, long, g, cap in glyphs():
        assert g == ud.normalize('NFC', g), (comp, g)
        assert cap == ud.normalize('NFC', cap), (comp, cap)
    assert script.glyph('ʃ') == 'ș' and len(script.glyph('ʃ')) == 1         # precomposed by NFC
    assert script.glyph('ʈ') == 't̤' and len(script.glyph('ʈ')) == 2          # a sequence: none exists
    assert script.glyph('kʲ') == 'k̦' and script.glyph('ə') == 'ạ'
    assert script.glyph('yː') == 'ű' and script.glyph('aː') == 'á' and script.glyph('ʃː') == 'șș'


def test_capitals_float_below():
    assert script.glyph('gʲ') == 'g̓' and script.glyph('gʲ', caps=True) == 'G̦'
    assert script.glyph('pʲ', caps=True) == 'P̦' and script.glyph('ɣ', caps=True) == 'G̣'
    assert script.glyph('ʕ', caps=True) == 'G̤' and script.glyph('cː', caps=True) == 'Țț'
    for comp, long, g, cap in glyphs():
        assert ud.normalize('NFD', cap)[0].lower() == ud.normalize('NFD', g)[0], (comp, g, cap)
        assert cap != g, comp


def test_one_reading():
    table = script.table()                      # building it asserts that no two compositions share a glyph
    for g, (comp, long, caps) in table.items():
        toks = script.read(g)
        assert len(toks) == 1 and (toks[0].comp, toks[0].long, toks[0].caps) == (comp, long, caps), (g, toks)
    for name, comp in script.POINTS.items():
        assert script.valid(comp), (name, comp)
        assert script.NAME[comp] == name
    key = lambda t: (t.comp, t.long)
    toks = [script.Tok(script.POINTS[n.rstrip(script.LONG)], n.endswith(script.LONG)) for n in POINTS]
    for a in toks:
        for b in toks:
            back = script.read(script.write([a, b]))
            if a.comp == b.comp and a.comp[0] not in script.VOWELS:
                # the same consonant twice is the long one; with a long one beside it, the long one first
                want = {(False, False): [(a.comp, True)],
                        (False, True): [(a.comp, True), (a.comp, False)],
                        (True, False): [(a.comp, True), (a.comp, False)],
                        (True, True): [(a.comp, True), (a.comp, True)]}[a.long, b.long]
            else:
                want = [key(a), key(b)]
            assert [key(t) for t in back] == want, (a, b, script.write([a, b]), back)
    assert script.names('dd̦') == ['d', 'ɟ'] and script.names('kkk') == ['kː', 'k']
    assert script.names('t‍t') == ['tː'] and script.names('Șș') == ['ʃː']
    t = script.read('niˇ')[1]
    assert (t.name, t.tones) == ('i', '3') and script.write(script.read('maˊ ma')) == 'maˊ ma'


def test_points_file():
    path = os.path.join(ROOT, 'data', 'points.yaml')
    on_disk = yaml.safe_load(open(path, encoding='utf-8'))
    assert on_disk == POINTS, 'data/points.yaml is stale: run scripts/gen_points.py'
    for name, p in POINTS.items():
        assert name == ud.normalize('NFC', name)
        assert script.glyph(name) == p['glyph']


if __name__ == '__main__':
    test_one_system()
    test_normalized()
    test_capitals_float_below()
    test_one_reading()
    test_points_file()
    print(f'the script layer holds: one set of marks, one normalized spelling, capitals below, '
          f'one reading; {len(POINTS)} points')
