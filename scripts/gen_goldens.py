#!/usr/bin/env python3
"""The pre-split goldens (split.md, P0): what the system writes at the tag
v1-presplit, frozen as the oracle for the split. Run once at the tag; never
regenerated afterwards, and not part of scripts/build.sh. `--check` recomputes
every row with the code as it is and compares it with the frozen files.

-> tests/goldens/
  spec.json            docs/spec.json as it was: every vector must reproduce
  spec.jsonl           every transport text in the spec's vectors
  samples.jsonl        every sample text (scripts/gen_samples.py), read from its spelling
  lexicon/<code>.jsonl.gz   every transport text a lexicon holds
  read/<code>.jsonl.gz      every spelling a lexicon reads, read through its stage
  MANIFEST.json        rows and sha256 of each file (of the unpacked text)

A row of spec.jsonl and lexicon/*: [transport, script, script joined,
{stage: spelling}], every stage. A row of samples.jsonl: [code, title, text,
transport, script, script joined, {stage: spelling}]. A row of read/*:
[spelling, transport, how].
"""
import gzip
import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import universal_v1 as engine
import gen_samples
import lexicon
import stages

OUT = os.path.join(ROOT, 'tests', 'goldens')
CODES = stages.codes()


def row(t):
    return [t, engine.render(t, strict=False), engine.render(t, strict=False, join=True),
            {c: stages.render(t, c, strict=False) for c in CODES}]


def spec_texts(spec):
    """Every transport text among the vectors, in order, once."""
    v, seen = spec['vectors'], {}
    def add(t):
        if isinstance(t, str):
            seen.setdefault(t, None)
    for t, _ in v['render']: add(t)
    for t, _ in v['lenient']: add(t)
    for t, _ in v['joined']: add(t)
    for t in v['invalid']: add(t)
    for t in v['stream']: add(t)
    for pairs in v['stages'].values():
        for t, _ in pairs: add(t)
    for pairs in v['parse'].values():
        for _, t in pairs: add(t)
    for text, source, target, out in v['convert']:
        if source == 'transport': add(text)
        if target == 'transport': add(out)
    for text, source in v['detect']:
        if source == 'transport': add(text)
    for kind, rows in v['lexicon'].items():
        for r in rows:
            for x in r[1:]:
                if isinstance(x, str) and x.isascii() and kind in ('read', 'write', 'loan'):
                    add(x)
    return list(seen)


def lexicon_texts(code):
    """Every transport text one lexicon holds: read values, write keys, the
    hand tables, a host's loans, the chooser's keys."""
    L, seen = lexicon.lex(code), {}
    def add(t):
        seen.setdefault(t[0] if isinstance(t, list) else t, None)
    read = L.get('read', {})
    for val in read.values():
        if isinstance(val, dict):                    # loans: per origin
            for t in val.values(): add(t)
        else:
            add(val)
    for t in L.get('write', {}): add(t)
    for t in L.get('hand', {}).values(): add(t)
    for host in L.get('hosts', {}).values():
        for t in host.get('read', {}).values(): add(t)
        for t in host.get('write', {}): add(t)
    for t in L.get('choices', {}): add(t)
    return list(seen)


def lexicon_spellings(code):
    """Every spelling one lexicon reads, for a code that is a stage."""
    L, seen = lexicon.lex(code), {}
    for w in L.get('read', {}): seen.setdefault(w, None)
    for w in sorted(L.get('native', [])): seen.setdefault(w, None)    # a set once loaded: sorted, so the rows keep their order
    for w in L.get('common', []): seen.setdefault(w, None)
    return list(seen)


MANIFEST = {}
CHECK = None            # the frozen manifest, under --check
FAILED = []


def write(name, rows):
    text = ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows)
    data = text.encode('utf-8')
    if CHECK is not None:
        want = CHECK['files'][name]
        ok = want['sha256'] == hashlib.sha256(data).hexdigest()
        print(f"{name}: {len(rows)} rows, {'same' if ok else 'DIFFERS'}")
        FAILED.extend([] if ok else [name])
        return
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if name.endswith('.gz'):
        with open(path, 'wb') as f, gzip.GzipFile(fileobj=f, mode='wb', mtime=0, filename='') as g:
            g.write(data)
    else:
        with open(path, 'wb') as f:
            f.write(data)
    MANIFEST[name] = {'rows': len(rows), 'sha256': hashlib.sha256(data).hexdigest()}
    print(f'{name}: {len(rows)} rows, {os.path.getsize(path)} bytes')


def main():
    global CHECK
    if '--check' in sys.argv:
        CHECK = json.load(open(os.path.join(OUT, 'MANIFEST.json'), encoding='utf-8'))
    elif os.path.exists(os.path.join(OUT, 'MANIFEST.json')) and '--force' not in sys.argv:
        sys.exit('tests/goldens exists: the goldens are frozen (split.md, P0)')
    src = os.path.join(OUT, 'spec.json')
    if CHECK is None:
        os.makedirs(OUT, exist_ok=True)
        shutil.copyfile(os.path.join(ROOT, 'docs', 'spec.json'), src)
        MANIFEST['spec.json'] = {'sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest()}
    write('spec.jsonl', [row(t) for t in spec_texts(json.load(open(src, encoding='utf-8')))])
    rows = []
    for code, _, title, text in gen_samples.TEXTS:
        t = stages.parse(text, f'stage:{code}')
        rows.append([code, title, text] + row(t))
    write('samples.jsonl', rows)
    for code in lexicon.codes():
        write(f'lexicon/{code}.jsonl.gz', [row(t) for t in lexicon_texts(code)])
        if code in CODES:
            stage = stages.load(code)
            words = lexicon_spellings(code)
            if words:
                write(f'read/{code}.jsonl.gz', [[w] + list(stages.read_word(w, stage)) for w in words])
    if CHECK is not None:
        sys.exit(f'goldens differ: {FAILED}' if FAILED else 0)
    with open(os.path.join(OUT, 'MANIFEST.json'), 'w', encoding='utf-8') as f:
        json.dump({'tag': 'v1-presplit', 'stages': CODES, 'files': MANIFEST}, f, indent=1, sort_keys=True)
        f.write('\n')


if __name__ == '__main__':
    main()
