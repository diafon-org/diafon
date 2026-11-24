#!/usr/bin/env python3
"""The Apple input methods' shared core (input_methods/apple/Core/Diafon.swift).
Run: python3 tests/test_apple.py

The core runs the site's JavaScript in JavaScriptCore. This builds it for
the Mac and replays, through Swift:
1. every vector of the typing (render, joined, the streaming traces);
2. the alphabet's convert vectors between the script and the spellings the
   apps offer (the ones written by their letters, no dictionary);
3. a few typed phrases written straight into a language's spelling;
4. the keys found for a Diafon text (what to press for it) type that text again.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
APPLE = os.path.join(ROOT, 'input_methods', 'apple')
FIELD, STEP, NL = '\x1e', '\x1f', '\x1d'
TYPED = [('out:stage:hu', 'syok seqp nyaqr, hossuq alma', 'sok szép nyár, hosszú alma'),      # typed, in a spelling
         ('out:stage:cs', 'dobriq den, pryqaqteleq', 'dobrí den, přátelé'),
         ('out:stage:ig', 'nqynoqy, keduqy ka iqy mere', 'nnọ, kedụ ka ị mere'),
         ('render', 'mqymaduqy nqyne mma', 'm̈madụ n̈ne mma'), ('convert:stage:ig|script', 'mmadụ nne', 'm̈madụ n̈ne'),
         ('convert:stage:sw|script', 'mmoja mtu', 'm̈mod̦a mtu'), ('keys', 'm̈madụ', 'mqymaduqy'),
         ('out:transport', 'sy tq', 'sy tq'), ('keys', 'Șok sép n̦ár, hossú alma', 'Syok seqp nyaqr, hossuq alma'),
         ('keys', 'city niˇ h2o', 'cityy ni3 h22o'),
         ('render', 'KUKKA Kukka HOSSYUQ', 'KUKKA Kukka HOȘȘÚ'), ('keys', 'KUKKA Kukka HOȘȘÚ', 'KUKKA Kukka HOSSyUq'),   # all in capitals
         ('out:stage:hu', 'ADD HOSSUQ Kedd', 'ADD HOSSZÚ Kedd'), ('convert:stage:hu|script', 'ADD hozzá, KEDD', 'ADD hozzá, KEDD')]


def build(out):
    subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'gen_apple.py')], check=True, capture_output=True)
    src = [os.path.join(APPLE, 'Core', 'Diafon.swift'), os.path.join(APPLE, 'Check', 'main.swift')]
    subprocess.run(['xcrun', 'swiftc', '-swift-version', '5', '-O', *src, '-o', out], check=True)


def test_vectors():
    if not shutil.which('xcrun'):
        print('  SKIP: no Swift compiler')
        return None
    profile = json.load(open(os.path.join(ROOT, 'spec', 'diafon-v1.json'), encoding='utf-8'))
    spec = json.load(open(os.path.join(REPO, 'docs', 'alphabet-spec.json'), encoding='utf-8'))
    lettered = {'script'} | {f'stage:{c}' for c, st in spec['stages'].items() if st['state'] != 'lexical' and c not in spec['lexicons']}
    v = profile['vectors']
    asks = [('render', t, want) for t, want in v['render']] + [('joined', t, want) for t, want in v['joined']]
    asks += [('stream', t, STEP.join(FIELD.join(step) for step in steps)) for t, steps in v['stream'].items()]
    asks += [(f'convert:{s}|{t}', text, want) for text, s, t, want in spec['vectors']['convert'] if s in lettered and t in lettered]
    asks += [('rekey', t, want) for t, want in v['render']]          # the keys found for a text type it again
    asks += TYPED
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, 'check')
        build(exe)
        env = dict(os.environ, DIAFON_RESOURCES=os.path.join(APPLE, 'Resources'))
        feed = ''.join(f'{mode}\t{text.replace(chr(10), NL)}\n' for mode, text, _ in asks)
        res = subprocess.run([exe], input=feed, capture_output=True, text=True, env=env)
    assert res.returncode == 0, res.stderr
    got = res.stdout.split('\n')[:-1]
    assert len(got) == len(asks), (len(got), len(asks))
    bad = [(m, t, g, w) for (m, t, w), g in zip(asks, got) if g.replace(NL, '\n') != w]
    assert not bad, bad[:6]
    return len(asks)


if __name__ == '__main__':
    n = test_vectors()
    if n is not None:
        print(f'the Apple core holds {n} vectors')
