#!/usr/bin/env python3
"""The script layer's law, as tests. Run: python3 tests/test_script.py  (or pytest tests/)

1. One system: every glyph in use is a base letter plus the system's own
   combining marks and nothing else; the marks are those data/script.yaml
   defines, each with one meaning on every letter.
2. Normalized: every glyph is NFC, so a pair Unicode precomposes (ș ṭ ä á)
   appears as that letter, and a pair it does not (t̤ k̦ ȁ) stays a sequence;
   both are the same text to Unicode, and there is exactly one spelling.
3. Capitals follow the float rule: no capital in the system descends, so a
   capital wears its mark below (Gj -> G̦, Pj -> P̦), and the base letter
   of a capital is the base letter of its small form.
"""
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine
from gen_master import aggregate

SCRIPT = yaml.safe_load(open(os.path.join(ROOT, 'data', 'script.yaml')))
MARKS = {ch for m in SCRIPT['marks'].values() for v in m.values() for ch in v}
SEQS = {'aix', 'aux', 'ojix', 'oix', 'oicx', 'ecicx', 'ocux', 'eix', 'oux', 'ojicx', 'ejix', 'eqicx', 'ajux', 'tyh', 'dyh',
        'rch', 'pf', 'ph', 'th', 'kh', 'bh', 'dh', 'gh', 'tch', 'tqh', 'dqh', 'tqyh'}


def glyphs():
    for form in sorted(aggregate()):
        if form in SEQS:
            continue
        yield form, engine.glyph(form), engine.glyph(form[0].upper() + form[1:])


def test_one_system():
    for form, g, cap in glyphs():
        for x in (g, cap):
            for ch in ud.normalize('NFD', x):
                if ud.combining(ch):
                    assert ch in MARKS, (form, x, f'U+{ord(ch):04X} is not one of the system\'s marks')
                else:
                    assert ch.isascii() and ch.isalpha(), (form, x, ch)


def test_normalized():
    for form, g, cap in glyphs():
        assert g == ud.normalize('NFC', g), (form, g)
        assert cap == ud.normalize('NFC', cap), (form, cap)
    assert engine.glyph('sj') == 'ș' and len(engine.glyph('sj')) == 1        # precomposed by NFC
    assert engine.glyph('txy') == 't̤' and len(engine.glyph('txy')) == 2       # a sequence: none exists
    assert engine.glyph('kj') == 'k̦' and engine.glyph('aj') == 'ạ'


def test_capitals_float_below():
    assert engine.glyph('Gj') == 'G̦' and engine.glyph('Pj') == 'P̦' and engine.glyph('Gx') == 'G̣'
    assert engine.glyph('Txy') == 'T̤' and engine.glyph('Tjw') == 'Țț'
    for form, g, cap in glyphs():
        assert ud.normalize('NFD', cap)[0].lower() == ud.normalize('NFD', g)[0], (form, g, cap)
        assert cap != g, form


if __name__ == '__main__':
    test_one_system()
    test_normalized()
    test_capitals_float_below()
    print('the script layer holds: one set of marks, one normalized spelling, capitals below')
