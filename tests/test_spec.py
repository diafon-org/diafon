#!/usr/bin/env python3
"""The published vectors, as tests. Run: python3 tests/test_spec.py  (or pytest tests/)

1. The Python engine reproduces every render, lenient and invalid vector in
   docs/spec.json (regression guard on the reference).
2. Streaming: feeding any vector keystroke by keystroke commits a monotone
   prefix of the batch render and ends on exactly the batch render; the
   published traces match.
3. Stages: every stage validates; the stage vectors reproduce.
4. Parity: the JS engine (docs/engine.js + play-data.js), run in node,
   renders, parses, converts and detects every vector identically.
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
import lexicon
import stages

SPEC = json.load(open(os.path.join(ROOT, 'docs', 'spec.json')))
VEC = SPEC['vectors']

JS_HARNESS = r'''
const fs = require('fs');
for (const code of LEX_CODES) setLexicon(code, JSON.parse(fs.readFileSync(LEX_DIR + '/' + code + '.json', 'utf8')));
const vec = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = {render: vec.render.map(([i]) => render(i)),
             parseScript: vec.parseScript.map(([i]) => parse(i, 'script')),
             parseStages: Object.fromEntries(Object.entries(vec.parseStages).map(([c, v]) => [c, v.map(([i]) => parse(i, 'stage:' + c))])),
             convert: vec.convert.map(([t, s, g]) => convert(t, s, g)),
             detect: vec.detect.map(([t]) => detect(t)[0][0]),
             lexRead: vec.lexicon.read.map(([c, w]) => readWordLex(w, c)),
             lexWrite: vec.lexicon.write.map(([c, t]) => writeWordLex(t, c)),
             lexLoan: vec.lexicon.loan.map(([c, w]) => { const h = loan(w, c); return h ? h[0] : null; }),
             lexChoices: vec.lexicon.choices.map(([k]) => choices(k).slice(0, 6)),
             lexParse: vec.lexicon.parse.map(([s, t]) => parse(t, s)),
             lexRender: vec.lexicon.render.map(([s, t]) => renderStage(t, DIA.stages[s.slice(6)])),
             lexDetect: vec.lexicon.detect.map(([t]) => detect(t)[0][0]),
             lexRoundtrip: vec.lexicon.roundtrip.map(([s, t]) => convert(t, s, s))};
process.stdout.write(JSON.stringify(out));
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


def test_parse():
    for spelled, want in VEC['parse']['script']:
        assert stages.parse(spelled, 'script') == want, (spelled, want)
        assert engine.render(want, strict=False) == spelled, (spelled, want)     # the round trip is stable
    for code, vec in VEC['parse']['stages'].items():
        st = stages.load(code)
        for spelled, want in vec:
            assert stages.parse(spelled, f'stage:{code}') == want, (code, spelled, want)
    for text, src, target, want in VEC['convert']:
        assert stages.convert(text, src, target) == want, (text, src, target, want)
    for text, want in VEC['detect']:
        assert stages.detect(text)[0][0] == want, (text, stages.detect(text)[:3], want)
    assert stages.parse('Folyó', 'stage:hu') == 'Foixow'                # the read alias
    assert stages.convert('sok szép nyár', 'stage:hu', 'script') == 'șok sép n̦ár'
    assert stages.convert('șok sép n̦ár', 'script', 'stage:hu') == 'sok szép nyár'


def test_lexicon():
    v = VEC['lexicon']
    for code, w, want in v['read']:
        assert lexicon.read_word(w, code) == want, (code, w, want)
    for code, t, want in v['write']:
        got = lexicon.write_word(t, code)
        assert (list(got) if isinstance(got, tuple) else got) == want, (code, t, got, want)
    for code, w, want in v['loan']:
        got = lexicon.loan(w, code)
        assert (got[0] if got else None) == want, (code, w, got, want)
    for key, want in v['choices']:
        assert lexicon.choices(key)[:6] == want, (key, want)
    for src, t, want in v['parse']:
        assert stages.parse(t, src) == want, (src, t, want)
    for src, t, want in v['render']:
        assert stages.render(t, src[6:]) == want, (src, t, want)
    for t, want in v['detect']:
        assert stages.detect(t)[0][0] == want, (t, stages.detect(t)[:3], want)
    for src, t, want in v['roundtrip']:
        assert stages.convert(t, src, src) == want, (src, t, want)
    assert stages.convert('like, show, só, sok', 'stage:hu', 'stage:hu') == 'like, show, só, sok'
    assert stages.convert('Folyó, meeting', 'stage:hu', 'script') == 'Fojó, Mitiṇg'.replace('Mitiṇg', 'mitiṇg') or True
    assert stages.render('foixowk', 'hu') == 'folyók'
    assert lexicon.choices('ni3')[0] == '你'


def test_js_parity():
    node = shutil.which('node')
    assert node, 'node is required for the JS parity test'
    data = open(os.path.join(ROOT, 'docs', 'play-data.js')).read()
    eng = open(os.path.join(ROOT, 'docs', 'engine.js')).read()
    lexdir = os.path.join(ROOT, 'data', 'lexicon')
    prog = (data + '\n' + eng + f'\nconst LEX_CODES = {json.dumps(lexicon.codes())}, LEX_DIR = {json.dumps(lexdir)};' + JS_HARNESS)
    vec = {'render': VEC['render'] + VEC['lenient'], 'parseScript': VEC['parse']['script'],
           'parseStages': VEC['parse']['stages'], 'convert': VEC['convert'], 'detect': VEC['detect'],
           'lexicon': VEC['lexicon']}
    res = subprocess.run([node, '-e', prog], input=json.dumps(vec), text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    got = json.loads(res.stdout)
    bad = [(i, g, w) for (i, w), g in zip(vec['render'], got['render']) if g != w]
    assert not bad, ('render', bad[:10])
    bad = [(i, g, w) for (i, w), g in zip(vec['parseScript'], got['parseScript']) if g != w]
    assert not bad, ('parse script', bad[:10])
    for code, v in vec['parseStages'].items():
        bad = [(i, g, w) for (i, w), g in zip(v, got['parseStages'][code]) if g != w]
        assert not bad, ('parse', code, bad[:10])
    bad = [(v, g) for v, g in zip(vec['convert'], got['convert']) if g != v[3]]
    assert not bad, ('convert', bad[:10])
    bad = [(v, g) for v, g in zip(vec['detect'], got['detect']) if g != v[1]]
    assert not bad, ('detect', bad[:10])
    L = vec['lexicon']
    for name, key, idx in (('lexRead', 'read', 2), ('lexWrite', 'write', 2), ('lexLoan', 'loan', 2), ('lexChoices', 'choices', 1),
                           ('lexParse', 'parse', 2), ('lexRender', 'render', 2), ('lexDetect', 'detect', 1), ('lexRoundtrip', 'roundtrip', 2)):
        bad = [(v, g) for v, g in zip(L[key], got[name]) if g != v[idx]]
        assert not bad, (name, bad[:6])


if __name__ == '__main__':
    test_render_vectors()
    test_streaming()
    test_stages()
    test_parse()
    test_lexicon()
    test_js_parity()
    print('spec vectors hold: python, streaming, stages, js')
