#!/usr/bin/env python3
"""Compile the profiles: profiles/<id>.yaml -> spec/<id>.json, the table the
engine and the ports read, with the profile's vectors:

  render   [typed, script]: every key sequence, small and capitalized, a
           doubled consonant, and sentences
  joined   [typed, script] with the long consonants joined
  stream   {typed: [[buffer, committed, pending], ...]} key by key

and `languages`, the languages the profile writes in full.

Usage: compile_profile.py [id ...]   (default: every profile)
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from engine import alphabet, profile
from engine.engine import make


def trace(eng, text):
    out, buf = [], ''
    for ch in text:
        buf += ch
        committed, pending = eng.stream(buf)
        out.append([buf, committed, pending])
        buf = pending
    return out


# sentences: Hungarian, Mandarin, the escapes, the doubled letters, the digits, every mark
TEXTS = ['cyak a joq soq', 'ni3 kqaw3, syiy4 cqie4', 'anyy cityy boyy', 'the cityy', 'you my by quick', 'ssy ccy nny ttq',
         'syy tqq', 'h2o abc123 x9 2x', 'Syok syeqp nyaqr, hossuq alma', 'Magyar, oyt, tuyz, uyq, oyq', 'SYOK Ssy SSY',
         'cyunq1kuo2 zyeyn2 ry4 luy4 ma5', 'say sayy, they theyy', 'aqq yy qq y q', 'tyuqk gyoyngy edy ketyteoy', 'ray ry rry',
         'tqink dqis sinq kqan', 'dobozz, add; eddy.', 'aay aaq aa', 'syy1 sy1y', 'h22o abc1123 x99 ni33 ma3 a2233',
         'bomq vemq blamq, simq', 'tyqak kyqalb hyqubb gyqajn', 'eqy oqy oqyq aqy aqyq, pqyq', 'ryqeka wyit, bry-d', 'sqiemq somq']


def vectors(eng):
    inv = eng.inventory()
    texts = inv + [k[0].upper() + k[1:] for k in inv] + [k[0] * 2 + k[1:] for k in inv if k[0] in eng.doubling] + TEXTS
    return {'render': [[t, eng.render(t)] for t in texts],
            'joined': [[t, eng.render(t, join=True)] for t in texts if eng.render(t, join=True) != eng.render(t)],
            'stream': {t: trace(eng, t) for t in TEXTS[:6] + TEXTS[-5:]}}


def languages(c):
    """The languages a profile can write in full: every sound of the language (the marginal ones
    aside) is written with letters the profile types."""
    typable = {v['point'] for v in c['keys'].values() if v['point']}
    out = []
    for code, lang in alphabet.SPEC['languages'].items():
        need = {n for s in lang['sounds'].values() if s['frequency'] != 'X' for n in s['points']}
        if all(n.rstrip(alphabet.LONG) in typable for n in need):
            out.append(code)
    return sorted(out)


def build(pid):
    c = profile.compile(pid)
    # what each key writes, so a port needs no other table: small and capital, and the long forms
    for v in c['keys'].values():
        comp = (v['to'][0], tuple(v['to'][1:]))
        v['writes'] = {f: g for f, g in alphabet.COMPS[comp].items()
                       if f in ('glyph', 'capital', 'long', 'long_capital', 'joined', 'joined_capital')}
    c['tone_signs'] = dict(alphabet.TONES)
    c['languages'] = languages(c)
    c['vectors'] = vectors(make(c))
    return c


def main():
    ids = sys.argv[1:] or sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'profiles', '*.yaml')))
    for pid in ids:
        c = build(pid)
        with open(profile.path(pid), 'w', encoding='utf-8') as f:
            json.dump(c, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print(f'{profile.path(pid)}: {len(c["keys"])} keys, {len(c["languages"])} languages, '
              + ', '.join(f'{k} {len(x)}' for k, x in c['vectors'].items()))


if __name__ == '__main__':
    main()
