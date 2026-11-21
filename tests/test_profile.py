#!/usr/bin/env python3
"""The profiles, as tests. Run: python3 tests/test_profile.py  (or pytest tests/)

1. spec/<id>.json is what scripts/compile_profile.py writes now.
2. A profile is sound: every key is a base and operators, every target is a
   composition of the vendored alphabet, no two keys type one composition,
   and what is typed reads back as the keys that typed it.
3. The profile's own vectors hold.
4. universal-v1 is the typing Diafon had before the split: every typing
   vector of the spec as it was then (tests/goldens/spec.json: render,
   lenient, joined, invalid, the streaming traces) reproduces byte for byte
   (the reverse anchor read as the double dot below it has become),
   and every form that spec lists draws the glyph it lists.
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
from engine.engine import Engine, ParseError, make

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
            k = (comp, v['long']) if c['segment']['kind'] == 'key-table' else comp
            assert seen.setdefault(k, key) == key, (pid, key, seen[k])
        if c['segment']['kind'] == 'key-table':
            uni = Engine(profile.compiled('universal-v1'))
            for key, v in c['keys'].items():
                toks = eng.points(key)
                assert len(toks) == 1 and toks[0].comp == (v['to'][0], tuple(v['to'][1:])) and toks[0].long == v['long'], (pid, key)
                assert uni.render(v['via']) == eng.render(key), (pid, key, v['via'])      # the same point in universal-v1 keys
            continue
        inv = eng.inventory()
        for f in inv:
            for x in (f, f[0].upper() + f[1:]):
                toks = eng.points(x)
                assert len(toks) == 1 and eng.typed(toks) == x, (pid, x)
                assert eng.typed(alphabet.read(eng.render(x))) == x, (pid, x)
        glyphs = {}
        for f in inv:
            assert glyphs.setdefault(eng.glyph(f), f) == f, (pid, f, glyphs[eng.glyph(f)])


def trace(eng, t):
    return compile_profile.trace(eng, t)


def check(eng, v):
    for t, want in v['render']:
        assert eng.render(t) == want, (t, eng.render(t), want)
    for t, want in v.get('lenient', []):
        assert eng.render(t, strict=False) == want, (t, want)
    for t, want in v['joined']:
        assert eng.render(t, join=True) == want, (t, want)
    for t in v.get('invalid', []):
        try:
            eng.render(t)
        except ParseError:
            continue
        raise AssertionError(f'{t!r} should be invalid')
    for t, steps in v['stream'].items():
        assert trace(eng, t) == steps, t


def test_vectors():
    for pid in IDS:
        c = profile.compiled(pid)
        check(make(c), c['vectors'])
    eng = make(profile.compiled('minimal-hu-v1'))
    for typed, want in [('cyak a joq soq', 'c̦ak a jó só'), ('anyy cityy boyy', 'any city boy'), ('ssy', 'șș'),
                        ('syy', 'sy'), ('you my by quick', 'you my by quick'), ('cyunq1kuo2', 'c̦uṇˉkuoˊ'), ('ni3 kqaw3', 'niˇ ḳawˇ'), ('2x', '2x')]:
        assert eng.render(typed) == want, (typed, eng.render(typed), want)


def test_universal_v1_is_the_old_typing():
    old = compile_profile.presplit()      # with the mark as it is now, without the letter q
    eng = Engine(profile.compiled('universal-v1'))
    check(eng, old['vectors'])
    for f in old['forms']:
        assert eng.render(f['form']) == f['glyph'], f['form']
        assert eng.render(f['form'][0].upper() + f['form'][1:]) == f['capital'], f['form']
    return len(old['forms']), sum(len(old['vectors'][k]) for k in ('render', 'lenient', 'joined', 'invalid', 'stream'))


if __name__ == '__main__':
    test_current()
    test_sound()
    test_vectors()
    forms, n = test_universal_v1_is_the_old_typing()
    print(f'the profiles hold: {", ".join(IDS)}; universal-v1 reproduces the pre-split spec ({forms} forms, {n} typing vectors)')
