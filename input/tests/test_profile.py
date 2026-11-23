#!/usr/bin/env python3
"""The profiles, as tests. Run: python3 tests/test_profile.py  (or pytest tests/)

1. spec/<id>.json is what scripts/compile_profile.py writes now.
2. A profile is sound: every key is a letter and operators, every prefix of
   a key is a key, every target is a composition of the vendored alphabet,
   no two keys type the same letter, and each key types exactly its letter.
3. The profile's own vectors hold, and a few sentences by hand.
4. diafon-v1 types every named point of the alphabet, short and long, and
   so writes every language of the alphabet in full.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import compile_profile
from engine import alphabet, profile
from engine.engine import make

IDS = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'profiles', '*.yaml')))


def test_current():
    for pid in IDS:
        fresh = json.loads(json.dumps(compile_profile.build(pid), ensure_ascii=False))
        assert fresh == profile.compiled(pid), f'spec/{pid}.json is stale: run scripts/compile_profile.py'


def test_sound():
    for pid in IDS:
        c = profile.compiled(pid)
        eng = make(c)
        seen = {}
        for key, v in c['keys'].items():
            comp = (v['to'][0], tuple(v['to'][1:]))
            assert comp in alphabet.COMPS, (pid, key)
            assert v['point'] == alphabet.NAME.get(comp), (pid, key)
            assert all(key[:i] in c['keys'] for i in range(1, len(key))), (pid, key, 'a prefix is no key')
            assert seen.setdefault((comp, v['long']), key) == key, (pid, key, seen[comp, v['long']])
            toks = eng.points(key)
            assert len(toks) == 1 and toks[0].comp == comp and toks[0].long == v['long'], (pid, key)
            assert alphabet.read(eng.render(key))[0].comp == comp, (pid, key)          # the script reads back as that letter


def test_vectors():
    for pid in IDS:
        c = profile.compiled(pid)
        eng = make(c)
        v = c['vectors']
        for t, want in v['render']:
            assert eng.render(t) == want, (t, eng.render(t), want)
        for t, want in v['joined']:
            assert eng.render(t, join=True) == want, (t, want)
        for t, steps in v['stream'].items():
            assert compile_profile.trace(eng, t) == steps, t
    eng = make(profile.compiled('diafon-v1'))
    for typed, want in [('cyak a joq soq', 'c̦ak a jó só'), ('anyy cityy boyy', 'any city boy'), ('ssy', 'șș'), ('syy', 'sy'),
                        ('you myy byy quick', 'you my by quick'), ('my by', 'm̦ b̦'), ('cyunq1kuo2', 'c̦uṇˉkuoˊ'), ('ni3 kqaw3', 'niˇ ḳawˇ'), ('2x', '2x'),
                        ('bomq vemq', 'boṃ veṃ'), ('kyqalb', 'k̤alb'), ('oqyq', 'ọ́'), ('ay aqy', 'ạ ä'), ('ry wy ryq', 'r̈ ẅ r̦'),
                        ('h22o', 'h2o')]:
        assert eng.render(typed) == want, (typed, eng.render(typed), want)


def test_whole_alphabet():
    c = profile.compiled('diafon-v1')
    typed = {(v['point'], v['long']) for v in c['keys'].values()}
    vowels = alphabet.VOWELS
    for name in alphabet.POINTS:
        comp = alphabet.POINTS[name]
        assert (name, False) in typed, f'{name} is not typed'
        if comp[0] in vowels:
            assert (name, True) in typed, f'{name}, long, is not typed'
    assert sorted(c['languages']) == sorted(alphabet.SPEC['languages']), 'a language is not written in full'
    return len(alphabet.POINTS), len(c['languages'])


if __name__ == '__main__':
    test_current()
    test_sound()
    test_vectors()
    n, langs = test_whole_alphabet()
    print(f'the profiles hold: {", ".join(IDS)}; diafon-v1 types all {n} points and writes {langs} languages in full')
