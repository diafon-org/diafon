#!/usr/bin/env python3
"""The published vectors, as tests. Run: python3 tests/test_spec.py  (or pytest tests/)

1. The Python engine reproduces every render, lenient and invalid vector in
   docs/spec.json (regression guard on the reference).
2. Streaming: feeding any vector keystroke by keystroke commits a monotone
   prefix of the batch render and ends on exactly the batch render; the
   published traces match.
3. Stages: every stage validates; the stage vectors reproduce.
4. Parity: the playground's JS engine (docs/play.html + play-data.js), run in
   node, renders every render vector identically.
"""
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine
import stages

SPEC = json.load(open(os.path.join(ROOT, 'docs', 'spec.json')))
VEC = SPEC['vectors']

JS_HARNESS = r'''
function render(text){
  let out = '';
  for (const tok of tokenize(text)){
    if (tok.t !== 'form'){ out += tok.ch; continue; }
    const g = glyph(tok.form, tok.caps);
    if (g === null){ out += tok.form + tok.tones; continue; }
    out += (tok.caps ? (g[0].toUpperCase() + g.slice(1)).normalize('NFC') : g) + tok.tones;
  }
  return out;
}
const vec = JSON.parse(require('fs').readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(vec.map(([i]) => render(i))));
'''


def test_render_vectors():
    for inp, want in VEC['render']:
        assert engine.render(inp) == want, (inp, engine.render(inp), want)
    for inp, want in VEC['lenient']:
        assert engine.render(inp, strict=False) == want, (inp, want)
    for inp in VEC['invalid']:
        try:
            engine.render(inp)
        except engine.ParseError:
            continue
        raise AssertionError(f'{inp!r} should be invalid')


def _stream_all(text):
    committed, buf = '', ''
    for ch in text:
        buf += ch
        c, buf = engine.stream(buf)
        committed += c
        assert engine.render(text, strict=False).startswith(committed), (text, committed)
    c, rest = engine.stream(buf)
    return committed + c + engine.render(rest, strict=False)


def test_streaming():
    for inp, _ in VEC['render'] + VEC['lenient']:
        assert _stream_all(inp) == engine.render(inp, strict=False), inp
    for text, want in VEC['stream'].items():
        got, buf = [], ''
        for ch in text:
            buf += ch
            c, p = engine.stream(buf)
            got.append([buf, c, p])
            buf = p
        assert got == want, text
    forms = [i for i, _ in VEC['render'] if i.islower() and ' ' not in i]
    for a in forms:
        for b in forms:
            assert _stream_all(a + b) == engine.render(a + b), (a, b)


def test_stages():
    for code in stages.codes():
        assert stages.validate(code) == [], code
        st = stages.load(code)
        for inp, want in VEC['stages'][code]:
            assert stages.render(inp, st) == want, (code, inp, want)
    assert stages.render('sjok sewp njawr, hoswuw Aclmac', 'hu') == 'sok szép nyár, hosszú Alma'
    assert stages.render('sjok Kxy', 'hu') == 'sok K̤'      # unspelled forms fall back to the script


def test_js_parity():
    node = shutil.which('node')
    assert node, 'node is required for the JS parity test'
    html = open(os.path.join(ROOT, 'docs', 'play.html')).read()
    m = re.search(r"<script>\n'use strict';\n(.*?)// ---- UI ----", html, re.S)
    assert m, 'engine block not found in play.html'
    data = open(os.path.join(ROOT, 'docs', 'play-data.js')).read()
    prog = data + '\n' + m.group(1) + JS_HARNESS
    vec = VEC['render'] + VEC['lenient']
    res = subprocess.run([node, '-e', prog], input=json.dumps(vec), text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    got = json.loads(res.stdout)
    bad = [(i, g, w) for (i, w), g in zip(vec, got) if g != w]
    assert not bad, bad[:10]


if __name__ == '__main__':
    test_render_vectors()
    test_streaming()
    test_stages()
    test_js_parity()
    print('spec vectors hold: python, streaming, stages, js')
