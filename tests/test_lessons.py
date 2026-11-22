#!/usr/bin/env python3
"""The lessons of the Input page. Run: python3 tests/test_lessons.py

Every letter, word and drill item of web/lessons-data.js types to the
letters it shows, through the reference engine; every language of the
alphabet has lessons, and its first lesson is the plain letters.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from engine import alphabet, profile
from engine.engine import make


def test_lessons():
    s = open(os.path.join(ROOT, 'web', 'lessons-data.js'), encoding='utf-8').read()
    data = json.loads(s[s.index('{'):s.rindex('}') + 1])
    eng = make(profile.compiled('diafon-v1'))
    assert sorted(data) == sorted(alphabet.SPEC['languages']), 'a language has no lessons'
    n = 0
    for code, L in data.items():
        assert L['lessons'] and L['lessons'][0]['key'] == 'letters', code
        for l in L['lessons']:
            assert l['forms'], (code, l['key'])
            for typed, want in [(f['f'], f['g']) for f in l['forms']] + [(w['t'], w['g']) for w in l['words'] + l['drill']]:
                assert eng.render(typed) == want, (code, typed, eng.render(typed), want)
                n += 1
    return len(data), n


if __name__ == '__main__':
    langs, n = test_lessons()
    print(f'the lessons hold: {langs} languages, {n} letters and words type as shown')
