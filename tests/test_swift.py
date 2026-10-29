#!/usr/bin/env python3
"""The macOS engine port against the spec vectors. Run: python3 tests/test_swift.py

Compiles the pure-Swift core in input_methods/apple/Core (Engine, Stages,
SpecData; shared by the macOS and iOS input methods) with the vector check,
then replays docs/spec.json: renders, rejected
inputs, lenient renders, streaming traces, stage renders, parses,
conversions and detections must come back byte for byte. Needs the Xcode Command Line Tools (swiftc).
"""
import json
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'input_methods', 'apple', 'Core')
FIELD, STEP = '\x1e', '\x1f'


def build():
    out = tempfile.mkdtemp(prefix='diafon-swift-')
    exe = os.path.join(out, 'check')
    files = [os.path.join(SRC, f) for f in ('SpecData.swift', 'Engine.swift', 'Stages.swift', 'Reading.swift', 'Lexicon.swift', 'CheckMain.swift')]
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
    for inp, want in vec['parse']['script']:
        reqs.append(('parse:script', inp)); wants.append(want)
    for code, pairs in vec['parse']['stages'].items():
        for inp, want in pairs:
            reqs.append((f'parse:stage:{code}', inp)); wants.append(want)
    for text, src, target, want in vec['convert']:
        reqs.append((f'convert:{src}|{target}', text)); wants.append(want)
    for text, want in vec['detect']:
        reqs.append(('detect', text)); wants.append(want)
    lv = vec['lexicon']
    for code, w, want in lv['read']:
        reqs.append((f'lexread:{code}', w)); wants.append(want if want is not None else '!NONE')
    for code, t, want in lv['write']:
        reqs.append((f'lexwrite:{code}', t)); wants.append('!NONE' if want is None else (FIELD.join(want) if isinstance(want, list) else want))
    for code, w, want in lv['loan']:
        reqs.append((f'loan:{code}', w)); wants.append(want if want is not None else '!NONE')
    for key, want in lv['choices']:
        reqs.append(('choices', key)); wants.append(FIELD.join(want))
    for src, t, want in lv['parse']:
        reqs.append((f'parse:{src}', t)); wants.append(want)
    for src, t, want in lv['render']:
        reqs.append((src, t)); wants.append(want)
    for t, want in lv['detect']:
        reqs.append(('detect', t)); wants.append(want)
    for src, t, want in lv['roundtrip']:
        reqs.append((f'convert:{src}|{src}', t)); wants.append(want)
    stdin = ''.join(f'{m}\t{i}\n' for m, i in reqs)
    env = dict(os.environ, DIAFON_LEXICON_DIR=os.path.join(ROOT, 'data', 'lexicon'))
    res = subprocess.run([exe], input=stdin, capture_output=True, text=True, env=env)
    assert res.returncode == 0, res.stderr
    got = res.stdout.split('\n')[:-1]
    assert len(got) == len(wants), (len(got), len(wants))
    bad = [(r, g, w) for r, g, w in zip(reqs, got, wants) if g != w]
    assert not bad, bad[:10]
    print(f'swift port holds {len(wants)} vectors')


if __name__ == '__main__':
    test_swift_vectors()
