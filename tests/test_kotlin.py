#!/usr/bin/env python3
"""The Android engine port against the spec vectors. Run: python3 tests/test_kotlin.py

Compiles the pure-Kotlin part of input_methods/android (Engine, Stages,
SpecData) with the vector check into a jar, then replays docs/spec.json:
renders, rejected inputs, lenient renders, streaming traces and stage
renders must come back byte for byte. Needs kotlinc (brew install kotlin).
"""
import json
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'input_methods', 'android', 'app', 'src', 'main', 'java', 'io', 'diafon', 'ime')
CHECK = os.path.join(ROOT, 'input_methods', 'android', 'check', 'Check.kt')
FIELD, STEP = '\x1e', '\x1f'


def java_env():
    env = dict(os.environ)
    if not env.get('JAVA_HOME'):
        try:
            prefix = subprocess.check_output(['brew', '--prefix', 'openjdk'], text=True).strip()
            home = os.path.join(prefix, 'libexec', 'openjdk.jdk', 'Contents', 'Home')
            if os.path.isdir(home):
                env['JAVA_HOME'] = home
                env['PATH'] = os.path.join(home, 'bin') + os.pathsep + env['PATH']
        except Exception:
            pass
    return env


def build(env):
    out = tempfile.mkdtemp(prefix='diafon-kt-')
    jar = os.path.join(out, 'check.jar')
    files = [os.path.join(SRC, f) for f in ('SpecData.kt', 'Engine.kt', 'Stages.kt')] + [CHECK]
    res = subprocess.run(['kotlinc', *files, '-include-runtime', '-d', jar],
                         env=env, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    return jar


def test_kotlin_vectors():
    if not shutil.which('kotlinc'):
        print('SKIP: kotlinc not installed (brew install kotlin)')
        return
    env = java_env()
    jar = build(env)
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
        if spec['stages'][code].get('lexicon'):      # the Kotlin port has no lexicon layer yet: letters only
            continue
        for inp, want in pairs:
            reqs.append((f'stage:{code}', inp)); wants.append(want)
    stdin = ''.join(f'{m}\t{i}\n' for m, i in reqs)
    res = subprocess.run(['java', '-jar', jar], input=stdin, env=env, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    got = res.stdout.split('\n')[:-1]
    assert len(got) == len(wants), (len(got), len(wants))
    bad = [(r, g, w) for r, g, w in zip(reqs, got, wants) if g != w]
    assert not bad, bad[:10]
    print(f'kotlin port holds {len(wants)} vectors')


if __name__ == '__main__':
    test_kotlin_vectors()
