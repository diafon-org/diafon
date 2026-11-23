#!/usr/bin/env python3
"""The typing in JavaScript (web/diafon-keys.js). Run: python3 tests/test_keys_js.py

Node replays every vector of every compiled profile through it: render,
joined, and the streaming traces, key by key.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DRIVER = r'''
const fs = require('fs');
const K = require(process.argv[1]);
let n = 0, bad = [];
for (const path of process.argv.slice(2)) {
  const p = JSON.parse(fs.readFileSync(path, 'utf8')), k = K.create(p), v = p.vectors;
  const eq = (got, want, what) => { n++; if (JSON.stringify(got) !== JSON.stringify(want)) bad.push([p.id, what, got, want]); };
  for (const [t, want] of v.render) eq(k.render(t), want, 'render ' + t);
  for (const [t, want] of v.joined) eq(k.render(t, {join: true}), want, 'joined ' + t);
  for (const [t, steps] of Object.entries(v.stream)) {
    let buf = '';
    const got = [];
    for (const ch of Array.from(t)) { buf += ch; const [c, pend] = k.stream(buf); got.push([buf, c, pend]); buf = pend; }
    eq(got, steps, 'stream ' + t);
  }
}
if (bad.length) { console.error(JSON.stringify(bad.slice(0, 5), null, 1)); process.exit(1); }
console.log(n);
'''


def test_vectors():
    if not shutil.which('node'):
        print('  SKIP: node is not installed')
        return None
    specs = sorted(glob.glob(os.path.join(ROOT, 'spec', '*.json')))
    res = subprocess.run(['node', '-e', DRIVER, os.path.join(ROOT, 'web', 'diafon-keys.js'), *specs], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    return int(res.stdout)


if __name__ == '__main__':
    n = test_vectors()
    if n is not None:
        print(f'the typing in JavaScript holds {n} vectors')
