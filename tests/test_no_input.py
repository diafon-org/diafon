#!/usr/bin/env python3
"""The alphabet knows no keyboard (split.md). Run: python3 tests/test_no_input.py  (or pytest tests/)

1. No script, test, font tool or data file of the alphabet names a typed
   form, an operator table, the old transport form or the typing bridge.
2. The data is in points: every stage table is keyed by point names, the
   mapping's values are point names, every Diafon word a lexicon stores is
   script text.
3. Nothing refers to the input repository.

PENDING lists what still types and has not left yet: the bridge, and the
generators and tests behind the site's pages that show how a point is typed
(the playground, the lessons, the form columns of the master tables). They
are in diafon-input already; they go from here when the site is split
(split.md, P4). The list may only shrink: a file in it must still exist,
and nothing outside it may type. The site's prose (docs/, the READMEs,
plan.md, remarks.md) is not scanned until then.
"""
import glob
import json
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import script

PENDING = {
    'scripts/universal_v1.py',      # the bridge
    'scripts/gen_spec.py',          # the old spec, for the site's typing engine
    'scripts/gen_play.py',          # the playground
    'scripts/gen_learn.py',         # the lessons
    'scripts/gen_site_words.py',    # the script switch runs the typing engine
    'scripts/gen_master.py',        # the master tables' form column
    'scripts/gen_site.py',          # the charts' form labels
    'tests/test_engine.py',
    'tests/test_spec.py',
    'tests/test_samples.py',
    'data/learn.yaml',
    'data/README.md',
}
TYPING = re.compile(r'universal_v1|\btransport\b|input form|legacy_(?:script|mapping)|\boperators?\b|diafon-input')
SELF = {'tests/test_no_input.py', 'tests/test_alphabet_spec.py'}      # they name the words they forbid


def files():
    for pattern in ('scripts/*.py', 'scripts/*.sh', 'tests/*.py', 'fonts/tools/*.py', 'data/*.yaml', 'data/*.md',
                    'data/*/*.yaml', 'data/*/*.md'):
        for p in sorted(glob.glob(os.path.join(ROOT, pattern))):
            yield os.path.relpath(p, ROOT)


def test_no_typing():
    found = set(files())
    for p in PENDING:
        assert p in found, f'{p} is gone: take it off PENDING'
    for p in found - PENDING - SELF:
        for n, line in enumerate(open(os.path.join(ROOT, p), encoding='utf-8'), 1):
            if p == 'scripts/build.sh' and any(q.split('/')[-1] in line for q in PENDING):
                continue                              # the build still runs what is pending
            m = TYPING.search(line)
            assert not m, f'{p}:{n}: {m.group(0)!r}: {line.strip()[:90]}'


def test_data_in_points():
    names = set(script.POINTS) | {n + script.LONG for n in script.POINTS}
    for path in sorted(glob.glob(os.path.join(ROOT, 'data', 'stages', '*.yaml'))):
        d = yaml.safe_load(open(path, encoding='utf-8'))
        assert 'forms' not in d, path
        for table in ('points', 'caps', 'before_i', 'before_vowel'):
            for name in d.get(table) or {}:
                assert str(name) in names, (path, table, name)
        for sp, v in (d.get('read') or {}).items():
            assert script.is_script(v), (path, sp, v)
    m = yaml.safe_load(open(os.path.join(ROOT, 'data', 'mapping.yaml'), encoding='utf-8'))
    values = [v for sec in ('consonants', 'vowels') for v in m[sec].values()]
    values += [v for d in m['overrides'].values() for v in d.values()]
    for v in values:
        for name in (v if isinstance(v, list) else [v]):
            assert str(name) in names, name
    words = 0
    for path in sorted(glob.glob(os.path.join(ROOT, 'data', 'lexicon', '*.json'))):
        L = json.load(open(path, encoding='utf-8'))
        texts = list(L.get('write', {})) + list(L.get('choices', {}))
        read = L.get('read', {})
        if 'hand' in L:
            texts += [v[0] for v in L['hand'].values()] + [t for d in read.values() for t in d.values()]
            texts += [v[0] for h in L['hosts'].values() for v in h['read'].values()] + [t for h in L['hosts'].values() for t in h['write']]
        else:
            texts += list(read.values())
        for t in texts:
            assert script.is_script(t), (path, t)
        words += len(texts)
    return words


if __name__ == '__main__':
    test_no_typing()
    words = test_data_in_points()
    print(f'the alphabet knows no keyboard: {words} lexicon words are script text; {len(PENDING)} files still pending (the site, P4)')
