#!/usr/bin/env python3
"""The macOS engine port against the spec vectors. Run: python3 tests/test_swift.py

Compiles the pure-Swift part of input_methods/mac (Engine, Stages, SpecData)
with the vector check, then replays docs/spec.json: renders, rejected
inputs, lenient renders, streaming traces and stage renders must come back
byte for byte. Needs the Xcode Command Line Tools (swiftc).
"""
import json
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'input_methods', 'mac', 'Sources')
FIELD, STEP = '\x1e', '\x1f'


def build():
    out = tempfile.mkdtemp(prefix='diafon-swift-')
    exe = os.path.join(out, 'check')
    files = [os.path.join(SRC, f) for f in ('SpecData.swift', 'Engine.swift', 'Stages.swift', 'CheckMain.swift')]
    res = subprocess.run(['xcrun', 'swiftc', '-O', *files, '-o', exe], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    return exe


def test_swift_vectors():
    if not shutil.which('swiftc'):
        print('SKIP: swiftc not installed')
        return
    exe = build()
    spec = json.load(open(os.path.join(ROOT, 'docs', 'spec.json')))
    vec = spec['vectors']
    reqs, wants = [], []
    for inp, want in vec['render']:
        reqs.append(('render', inp)); wants.append(want)
    for inp in vec['invalid']:
        reqs.append(('render', inp)); wants.append('!ERR')
    for inp, want in vec['lenient']:
        reqs.append(('lenient', inp)); wants.append(want)
    for text, tr in vec['stream'].items():
        reqs.append(('stream', text)); wants.append(STEP.join(FIELD.join(step) for step in tr))
    for code, pairs in vec['stages'].items():
        for inp, want in pairs:
            reqs.append((f'stage:{code}', inp)); wants.append(want)
    stdin = ''.join(f'{m}\t{i}\n' for m, i in reqs)
    res = subprocess.run([exe], input=stdin, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    got = res.stdout.split('\n')[:-1]
    assert len(got) == len(wants), (len(got), len(wants))
    bad = [(r, g, w) for r, g, w in zip(reqs, got, wants) if g != w]
    assert not bad, bad[:10]
    print(f'swift port holds {len(wants)} vectors')


if __name__ == '__main__':
    test_swift_vectors()
