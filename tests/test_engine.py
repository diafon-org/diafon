#!/usr/bin/env python3
"""The engine's guarantees, as tests. Run: python3 tests/test_engine.py  (or pytest tests/)

1. Totality: every form the mapping uses parses to itself.
2. Stream decodability: any two in-use forms concatenated tokenize back to
   exactly those two forms — no input ever re-reads as something else.
3. Glyph injectivity: no two single-segment forms share a script glyph.
   Documented exception: a long consonant doubles its letter, so its glyph
   equals the two-segment sequence of its base — deliberate.
"""
import os
import sys
import unicodedata as ud

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
import engine
from gen_master import aggregate

SEQS = {'aix', 'aux', 'ojix', 'eix', 'oux', 'ojicx', 'ejix', 'eqicx', 'ajux', 'tyh', 'dyh', 'rch', 'pf', 'ph', 'th', 'kh', 'bh', 'dh', 'gh', 'tch', 'tqh', 'dqh', 'tqyh'}


def in_use_forms():
    forms = set(aggregate())
    single = {f for f in forms if f not in SEQS}
    return single, forms


def test_totality():
    single, _ = in_use_forms()
    for f in sorted(single):
        toks = engine.tokenize(f)
        assert len(toks) == 1 and toks[0][1] == f, f
        g = engine.glyph(f)
        assert g, f


def test_sequences_are_two_segments():
    _, forms = in_use_forms()
    for f in sorted(forms & SEQS):
        toks = engine.tokenize(f)
        assert len(toks) == 2, (f, toks)


def test_stream_decodability():
    single, _ = in_use_forms()
    forms = sorted(single)
    for a in forms:
        for b in forms:
            toks = engine.tokenize(a + b)
            got = [t[1] for t in toks if t[0] == 'form']
            assert got == [a, b], (a, b, got)


def test_glyph_injectivity():
    single, _ = in_use_forms()
    seen = {}
    for f in sorted(single):
        g = ud.normalize('NFC', engine.glyph(f))
        if g in seen:
            # documented exception: long consonant = doubled letter
            pair = {f, seen[g]}
            assert any(x.endswith('w') for x in pair), (f, seen[g], g)
        seen[g] = f


if __name__ == '__main__':
    test_totality()
    test_sequences_are_two_segments()
    test_stream_decodability()
    test_glyph_injectivity()
    print('all engine guarantees hold')
