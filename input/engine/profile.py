"""Input profiles: what keys produce which points. A profile is data
(profiles/<id>.yaml); compiled, it is a table (spec/<id>.json) that the
engine and the ports read. A profile owns no sound decision: every target
is a point of the alphabet, by name, or a composition by letter and marks.

A profile is immutable by id: a change to universal-v1 is universal-v2. It
names the alphabet major it targets.

  load(id)       the profile as written
  compile(id)    the compiled table: {'id', 'alphabet', 'segment', 'case',
                 'commit', 'keys': {key: {'to': [letter, mark...], 'point':
                 name or None, 'long': may be long}}}
"""
import json
import os

import yaml

from . import alphabet

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(pid):
    p = yaml.safe_load(open(os.path.join(ROOT, 'profiles', f'{pid}.yaml'), encoding='utf-8'))
    assert p['id'] == pid, f'{pid}.yaml names itself {p["id"]}'
    return p


def compile(pid):
    p = load(pid)
    assert p['alphabet'] == alphabet.MAJOR, f'{pid} targets alphabet {p["alphabet"]}, the spec is {alphabet.VERSION}'
    seg = p['segment']
    table = seg['kind'] == 'key-table'
    ops = set(seg['operators'])
    bases = set(seg['bases']) if not table else {str(k)[0] for k in p['keys']}
    keys, seen = {}, {}
    for key, value in p['keys'].items():
        key = str(key)
        to, may_long = (value, True) if isinstance(value, str) else (value['to'], value.get('long', True))
        comp, long = alphabet.target(to)
        assert table or not long, f'{pid}: {key}: length is typed with the length key'
        assert key[0] in bases and all(ch in ops for ch in key[1:]), f'{pid}: {key} is not a base and operators'
        assert (comp, long) not in seen, f'{pid}: {key} and {seen[comp, long]} both type {to}'
        seen[comp, long] = key
        keys[key] = {'to': [comp[0], *comp[1]], 'point': alphabet.NAME.get(comp), 'long': bool(long if table else may_long)}
    out = {'id': pid, 'name': p.get('name', pid), 'alphabet': {'major': p['alphabet'], 'built_with': alphabet.VERSION},
           'case': p['case'], 'commit': p['commit'], 'keys': keys}
    if table:
        vowels = alphabet.VOWELS
        out['segment'] = {'kind': 'key-table', 'bases': ''.join(sorted(bases)), 'operators': ''.join(sorted(ops)),
                          'double': seg['double'], 'escape': seg['escape'],
                          'doubling': ''.join(sorted(b for b in bases if b not in vowels))}
        out['tones'] = p.get('tones') == 'digits'
    else:
        out['segment'] = {'kind': seg['kind'], 'bases': ''.join(sorted(bases)), 'operators': ''.join(sorted(ops)),
                          'max_operators': seg['max_operators'], 'length': seg['length'], 'tones': seg['tones']}
    return out


def path(pid):
    return os.path.join(ROOT, 'spec', f'{pid}.json')


def compiled(pid):
    """The compiled profile from spec/, as the ports read it."""
    return json.load(open(path(pid), encoding='utf-8'))
