#!/usr/bin/env python3
"""Compile the profiles: profiles/<id>.yaml -> spec/<id>.json, the table the
engine and the ports read, with the profile's vectors:

  render   [typed, script]: every key sequence, small, capitalized and all
           caps, short and long, and sentences
  lenient  [typed, script] with ill-formed input passed through
  joined   [typed, script] with the long consonants joined
  invalid  typed text the strict reading rejects
  stream   {typed: [[buffer, committed, pending], ...]} key by key

Usage: compile_profile.py [id ...]   (default: every profile)
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from engine import alphabet, profile
from engine.engine import Engine, ParseError, make

PRESPLIT = os.path.join(ROOT, 'tests', 'goldens', 'spec.json')     # the spec as it was before the split


def trace(eng, text):
    out, buf = [], ''
    for ch in text:
        buf += ch
        committed, pending = eng.stream(buf)
        out.append([buf, committed, pending])
        buf = pending
    return out


MINIMAL = ['cyak a joq soq', 'zhong1guo2', 'anyy cityy boyy', 'the cityy', 'you my by quick', 'ssy ccy nny ttq',
           'syy tqq', 'h2o abc123 x9', 'Syok syeqp nyaqr, hossuq alma', 'Magyar, oyt, tuyz, uyq, oyq', 'SYOK Ssy SSY',
           'ni3hao3 ma5, lv4 Zhong1', 'say sayy, they theyy', 'aqq yy qq y q', 'tyuqk gyoyngy edy ketyteoy', 'ray ry rry',
           'tqink dqis sinq', 'dobozz, add; eddy.', 'aay aaq aa']


def universal():
    return Engine(profile.compile('universal-v1'))


def vectors(eng, pid):
    """The profile's vectors. universal-v1 keeps the inputs of the spec it
    had before the split, so that spec's answers are its conformance."""
    if pid != 'universal-v1':
        texts = [k for k in eng.inventory()] + [k[0].upper() + k[1:] for k in eng.inventory()] \
            + [k[0] * 2 + k[1:] for k in eng.inventory() if k[0] in eng.doubling] + MINIMAL
        return {'render': [[t, eng.render(t)] for t in texts],
                'joined': [[t, eng.render(t, join=True)] for t in texts if eng.render(t, join=True) != eng.render(t)],
                'stream': {t: trace(eng, t) for t in MINIMAL[:6]}}
    old = json.load(open(PRESPLIT, encoding='utf-8'))['vectors']
    render = []
    for f in eng.inventory():
        for x in (f, f[0].upper() + f[1:], f.upper()):
            render.append([x, eng.render(x)])
    v = {'render': render, 'lenient': [], 'joined': [], 'invalid': [], 'stream': {}}
    v['render'] += [[t, eng.render(t)] for t, _ in old['render'] if [t, eng.render(t)] not in render]
    v['lenient'] = [[t, eng.render(t, strict=False)] for t, _ in old['lenient']]
    v['joined'] = [[t, eng.render(t, join=True)] for t, _ in old['joined']]
    for t in old['invalid']:
        try:
            eng.render(t)
        except ParseError:
            v['invalid'].append(t)
    v['stream'] = {t: trace(eng, t) for t in old['stream']}
    return v


def build(pid):
    c = profile.compile(pid)
    eng = make(c)
    if pid != 'universal-v1':
        # what each key sequence, and each pinyin syllable, is in universal-v1 keys: the ports' way in
        uni = universal()
        for key, v in c['keys'].items():
            v['via'] = uni.typed([eng.letters(key)[0]])
        if c.get('pinyin'):
            c['pinyin']['via'] = {syl: uni.typed(alphabet.read(text)) for syl, text in c['pinyin']['syllables'].items()}
    c['vectors'] = vectors(eng, pid)
    return c


def main():
    ids = sys.argv[1:] or sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'profiles', '*.yaml')))
    for pid in ids:
        c = build(pid)
        with open(profile.path(pid), 'w', encoding='utf-8') as f:
            json.dump(c, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print(f'{profile.path(pid)}: {len(c["keys"])} keys, ' + ', '.join(f'{k} {len(x)}' for k, x in c['vectors'].items()))


if __name__ == '__main__':
    main()
