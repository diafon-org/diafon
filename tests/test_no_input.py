#!/usr/bin/env python3
"""The alphabet knows no keyboard (split.md). Run: python3 tests/test_no_input.py  (or pytest tests/)

1. No script, test, font tool, data file or page of the alphabet names a
   typed form, an operator, the old transport form or the typing bridge.
2. The data is in points: every stage table is keyed by point names, the
   mapping's values are point names, every Diafon word a lexicon stores is
   script text.
3. Nothing that types is left in the alphabet: no engine, no playground, no
   lessons. The typing lives in input/, and no script, test or font tool of
   the alphabet reads that folder.

The alphabet is everything outside input/. The plan and the notes (split.md,
plan.md, remarks.md, publish.md) tell the story of the split and are not
scanned. The site carries one page on typing, docs/input, a link to
input/web: it is the typing's and is not scanned either.
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

GONE = ['scripts/universal_v1.py', 'scripts/engine.py', 'scripts/gen_spec.py', 'scripts/gen_play.py', 'scripts/gen_learn.py',
        'docs/engine.js', 'docs/play-data.js', 'docs/learn-data.js', 'docs/learn.md', 'docs/spec.json', 'docs/lexicon',
        'data/learn.yaml', 'data/layouts.yaml', 'data/emoji.json', 'input_methods/README.md',
        'scripts/sync_input_page.py', 'input/vendor']
TYPING = re.compile(r'universal_v1|\btransport\b|input form|legacy_(?:script|mapping)|\boperators?\b|diafon-input|play-data|engine\.js')
SELF = {'tests/test_no_input.py', 'tests/test_alphabet_spec.py'}      # they name the words they forbid
READS_INPUT = re.compile(r'''['"/]input['"/]''')                       # a path into the typing's folder


def files():
    for pattern in ('scripts/*.py', 'scripts/*.sh', 'tests/*.py', 'fonts/tools/*.py', 'data/*.yaml', 'data/*.md',
                    'data/*/*.yaml', 'data/*/*.md', 'docs/*.md', 'docs/.include/*.html', 'docs/assets/*.js',
                    'README.md', 'mkdocs.yml'):
        for p in sorted(glob.glob(os.path.join(ROOT, pattern))):
            yield os.path.relpath(p, ROOT)


def test_no_typing():
    for p in GONE:
        assert not os.path.exists(os.path.join(ROOT, p)), f'{p} is back'
    scanned = 0
    for p in set(files()) - SELF:
        if p == 'docs/assets/site-words.js':
            continue                                  # generated: the site's English words in Diafon
        for n, line in enumerate(open(os.path.join(ROOT, p), encoding='utf-8'), 1):
            m = TYPING.search(line)
            assert not m, f'{p}:{n}: {m.group(0)!r}: {line.strip()[:90]}'
            if p.endswith(('.py', '.sh')):
                assert not READS_INPUT.search(line), f'{p}:{n}: reads the typing: {line.strip()[:90]}'
        scanned += 1
    return scanned


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
    scanned = test_no_typing()
    words = test_data_in_points()
    print(f'the alphabet knows no keyboard: {scanned} files name no typed form, {words} lexicon words are script text')
