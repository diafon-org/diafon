#!/usr/bin/env python3
"""The browser core is the reference. Run: python3 tests/test_core_js.py  (or pytest tests/)

docs/assets/diafon-core.js is the script, the stages and the lexicon layer
in JavaScript, driven by docs/alphabet-spec.json and data/lexicon/*.json.
Node runs it here (the test is skipped when there is no node).

1. Every vector of the spec reproduces through it: write, joined, read,
   stage_write, stage_read, convert, detect, lexicon (read, write, loan,
   choices, parse, roundtrip, detect).
2. Without any lexicon the script and the letter stages still work (the
   large lexicons are optional), and the file loads as a plain <script>.
3. It agrees with the Python reference on more than the vectors: for every
   stage, words of the sample texts (docs/.include/samples.html) and of the
   lexicons, converted stage -> script -> stage and stage -> stage, and
   script words written in the stage; whole sample texts, and detect on them.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import lexicon
import stages

CORE = os.path.join(ROOT, 'docs', 'assets', 'diafon-core.js')
SPEC = os.path.join(ROOT, 'docs', 'alphabet-spec.json')
GROUPS = ('write', 'joined', 'read', 'stage_write', 'stage_read', 'convert', 'detect', 'lexicon')
PER_STAGE = 300          # words per stage in the cross-check, at least

DRIVER = r"""
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const [corePath, specPath, lexDir, extraPath] = process.argv.slice(2);
const DiafonCore = require(corePath);
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const extra = JSON.parse(fs.readFileSync(extraPath, 'utf8'));
const V = spec.vectors;
const counts = {}, failures = [];
const same = (a, b) => {
  if (a === b) return true;
  if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  const ka = Object.keys(a), kb = Object.keys(b);
  return ka.length === kb.length && ka.every((k) => Object.prototype.hasOwnProperty.call(b, k) && same(a[k], b[k]));
};
const check = (group, what, got, want) => {
  const c = counts[group] || (counts[group] = [0, 0]);
  c[1]++;
  let g;
  try { g = got(); } catch (e) { g = 'ERROR ' + (e && e.stack || e); }
  if (same(g, want)) c[0]++;
  else if (failures.length < 40) failures.push({ group, what, got: g, want });
};

// 2a. no lexicon: the script and the letter stages
const bare = DiafonCore.create(spec);
for (const [pts, text] of V.write) {
  check('bare', ['write', text], () => bare.write(pts), text);
  check('bare', ['read', text], () => bare.plains(bare.read(text)), pts);
}
for (const [pts, text] of V.joined) check('bare', ['joined', text], () => bare.write(pts, { join: true }), text);
for (const [text, pts] of V.read) check('bare', ['read', text], () => bare.plains(bare.read(text)), pts);
for (const code of Object.keys(V.stage_write)) {
  if (spec.lexicons[code]) continue;
  for (const [pts, sp] of V.stage_write[code]) check('bare', ['stage_write', code, sp], () => bare.render(pts, code), sp);
  for (const [sp, pts] of V.stage_read[code] || []) check('bare', ['stage_read', code, sp], () => bare.plains(bare.parse(sp, 'stage:' + code)), pts);
}
check('bare', 'a lexical stage without its lexicon falls to the letters', () => typeof bare.convert('The quick fox', 'stage:en', 'script'), 'string');
check('bare', 'a host without its lexicon reads by its letters', () => bare.convert('sok szép nyár', 'stage:hu', 'script'), 'șok sép n̦ár');

// 2b. a plain <script>: no module, the global is defined
const ctx = {};
vm.runInNewContext(fs.readFileSync(corePath, 'utf8'), ctx);
check('bare', 'window.DiafonCore', () => typeof (ctx.DiafonCore && ctx.DiafonCore.create), 'function');
check('bare', 'window.DiafonCore reads', () => ctx.DiafonCore.create(spec).write(['ʃ']), bare.write(['ʃ']));

// 1. every vector, the lexicons in
const core = DiafonCore.create(spec);
for (const code of Object.keys(spec.lexicons)) {
  core.addLexicon(code, JSON.parse(fs.readFileSync(path.join(lexDir, code + '.json'), 'utf8')));
}
for (const [pts, text] of V.write) {
  check('write', ['write', text], () => core.write(pts), text);
  check('write', ['read', text], () => core.plains(core.read(text)), pts);
}
for (const [pts, text] of V.joined) {
  check('joined', ['write', text], () => core.write(pts, { join: true }), text);
  check('joined', ['read', text], () => core.plains(core.read(text)), pts);
}
for (const [text, pts] of V.read) check('read', text, () => core.plains(core.read(text)), pts);
for (const code of Object.keys(V.stage_write)) {
  for (const [pts, sp] of V.stage_write[code]) check('stage_write', [code, sp], () => core.render(core.tokens(pts), code), sp);
}
for (const code of Object.keys(V.stage_read)) {
  for (const [sp, pts] of V.stage_read[code]) check('stage_read', [code, sp], () => core.plains(core.parse(sp, 'stage:' + code)), pts);
}
for (const [text, source, target, out] of V.convert) check('convert', [text, source, target], () => core.convert(text, source, target), out);
for (const [text, source] of V.detect) check('detect', text, () => core.detect(text)[0][0], source);
const L = V.lexicon;
for (const [code, word, s] of L.read) check('lexicon', ['read', code, word], () => core.lexRead(word, code), s);
for (const [code, s, want] of L.write) check('lexicon', ['write', code, s], () => core.lexWrite(s, code), want);
for (const [code, word, s] of L.loan) check('lexicon', ['loan', code, word], () => (core.loan(word, code) || [null])[0], s);
for (const [key, chars] of L.choices) check('lexicon', ['choices', key], () => core.choices(key).slice(0, 6), chars);
for (const [source, text, s] of L.parse) check('lexicon', ['parse', source, text], () => core.write(core.parse(text, source)), s);
for (const [source, text, out] of L.roundtrip) check('lexicon', ['roundtrip', source, text], () => core.convert(text, source, source), out);
for (const [text, source] of L.detect) check('lexicon', ['detect', text], () => core.detect(text)[0][0], source);
check('sources', 'sources', () => core.sources(), extra.sources);

// 3. against the reference, beyond the vectors
for (const [text, source, target, out] of extra.convert) check('cross', [text, source, target], () => core.convert(text, source, target), out);
for (const [text, ranked] of extra.detect) {
  check('cross_detect', text, () => core.detect(text).map(([s, c]) => [s, Math.round(c * 1e9) / 1e9]), ranked);
}
for (const [text, prefer, top] of extra.prefer) check('cross_detect', [text, prefer], () => core.detect(text, { prefer })[0][0], top);
process.stdout.write(JSON.stringify({ counts, failures }));
"""


def node():
    return shutil.which('node') or next((p for p in ('/opt/homebrew/bin/node', '/usr/local/bin/node') if os.path.exists(p)), None)


def samples():
    """The sample texts: [(language code, script text, original spelling)]."""
    page = open(os.path.join(ROOT, 'docs', '.include', 'samples.html'), encoding='utf-8').read()
    text = lambda s: html.unescape(re.sub(r'<[^>]+>', ' ', s.replace('<br>', '\n')))
    out = []
    for m in re.finditer(r'<article class="sample" data-lang="(\w+)".*?</article>', page, re.S):
        g = re.search(r'class="sample-text[^"]*">(.*?)</p>', m.group(0), re.S)
        o = re.search(r'class="sample-orig[^"]*">(.*?)</p>', m.group(0), re.S)
        out.append((m.group(1), text(g.group(1)) if g else '', text(o.group(1)) if o else ''))
    assert out, 'no sample texts in docs/.include/samples.html'
    return out


def uniq(xs):
    return list(dict.fromkeys(xs))


def spread(xs, n):
    """n of a list, evenly spread (the same ones each run)."""
    xs = list(xs)
    return xs if len(xs) <= n else [xs[i * len(xs) // n] for i in range(n)]


def words_of(text):
    return uniq(m.group(0) for m in lexicon.WORD.finditer(text))


def extras():
    """The inputs of the cross-check with what the reference makes of them."""
    S = samples()
    script_words = uniq(w for _, g, _ in S for w in words_of(g))
    orig = {}
    for code, _, o in S:
        orig.setdefault(code, []).extend(words_of(o))
    lex = {c: lexicon.lex(c) for c in lexicon.codes()}
    loans = lex['loans']
    en_keys = spread(sorted(lex['en']['read']), 220)
    hu_native = spread(sorted(lex['hu']['native']), 160)
    cap = lambda ws: [w[:1].upper() + w[1:] for w in ws]
    own = {
        'en': en_keys + cap(en_keys[::7]) + [w.upper() for w in en_keys[::11]] + ["dimm'd", "o'er", 'don’t'],
        'hu': hu_native + cap(hu_native[::5]) + list(lex['hu']['read']) + list(lex['hu']['write'].values())[::12]
              + list(loans['hand']) + cap(list(loans['hand'])) + list(loans['hosts'].get('hu', {}).get('read', {}))
              + list(loans['hosts'].get('hu', {}).get('write', {}).values())
              + spread(sorted(loans['read']['en']), 120) + list(loans['read']['la'])
              + [w + s for w in spread(sorted(loans['read']['en']), 40) for s in ('ban', 'ek', 'ját')],
        'zh': [k + d for k in spread(sorted(lex['zh']['read']), 110) for d in ('', '1', '4')]
              + [a + b for a, b in zip(sorted(lex['zh']['read'])[::9], sorted(lex['zh']['read'])[4::9])]
              + [a.capitalize() + '3' + b + '5' for a, b in zip(sorted(lex['zh']['read'])[::13], sorted(lex['zh']['read'])[6::13])],
    }
    foreign = spread(en_keys, 40) + spread(hu_native, 40)            # words of another spelling, read as they can be
    conv, per_stage = [], {}
    for code in stages.codes():
        src = f'stage:{code}'
        st = stages.load(code)
        ws = uniq(orig.get(code, []) + own.get(code, [])
                  + [stages.convert(w, 'script', src) for w in spread(script_words, 260)]     # words spelled in the stage
                  + foreign + spread(uniq(w for ws in orig.values() for w in ws), 80))
        ws = [w for w in ws if w]
        per_stage[code] = len(ws)
        assert len(ws) >= PER_STAGE, (code, len(ws))
        for w in ws:
            s = stages.convert(w, src, 'script')
            conv.append([w, src, 'script', s])
            conv.append([s, 'script', src, stages.convert(s, 'script', src)])
            conv.append([w, src, src, stages.convert(w, src, src)])
        for w in spread(script_words, 200):
            conv.append([w, 'script', src, stages.convert(w, 'script', src)])
        if st['sample']:
            conv.append([st['sample'], 'script', src, stages.convert(st['sample'], 'script', src)])
    texts = []
    for code, g, o in S:                                             # the whole texts, both ways, and across
        src = f'stage:{code}'
        if code not in stages.codes():
            continue
        conv.append([o, src, 'script', stages.convert(o, src, 'script')])
        conv.append([o, src, src, stages.convert(o, src, src)])
        conv.append([g, 'script', src, stages.convert(g, 'script', src)])
        conv.append([g, 'script', 'script', stages.convert(g, 'script', 'script')])
        for other in ('stage:hu', 'stage:pl', 'stage:en'):
            conv.append([o, src, other, stages.convert(o, src, other)])
        texts += [g, o] + [l for l in o.split('\n') if l.strip()][:2] + [' '.join(words_of(o)[:k]) for k in (1, 2, 5)]
    texts = uniq(t for t in texts if t.strip()) + ['', '123', 'x', 'ma1', 'Ni3hao3', 'a b', '日本語', 'ŝanĝo ĉiuĵaŭde']
    detect = [[t, [[s, round(c, 9)] for s, c in stages.detect(t)]] for t in texts]
    prefer = [[t, p, stages.detect(t, p)[0][0]] for t in ('alma', 'a', 'tea', 'dom', 'kala', 'on')
              for p in (['stage:fi'], ['stage:tr', 'stage:hu'], 'stage:pl')]
    return {'convert': conv, 'detect': detect, 'prefer': prefer, 'sources': stages.sources()}, per_stage


def run():
    exe = node()
    if not exe:
        return None
    extra, per_stage = extras()
    with tempfile.TemporaryDirectory() as tmp:
        driver, data = os.path.join(tmp, 'driver.js'), os.path.join(tmp, 'extra.json')
        open(driver, 'w', encoding='utf-8').write(DRIVER)
        json.dump(extra, open(data, 'w', encoding='utf-8'), ensure_ascii=False)
        r = subprocess.run([exe, driver, CORE, SPEC, lexicon.LEX, data], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, f'node failed:\n{r.stderr[-3000:]}'
    out = json.loads(r.stdout)
    return out, extra, per_stage


def test_core_js():
    res = run()
    if res is None:
        try:
            import pytest
            pytest.skip('no node')
        except ImportError:
            return None
    out, extra, per_stage = res
    counts = out['counts']
    assert not out['failures'], 'diafon-core.js differs from the reference:\n' + '\n'.join(
        json.dumps(f, ensure_ascii=False) for f in out['failures'][:12])
    vec = json.load(open(SPEC, encoding='utf-8'))['vectors']
    size = lambda v: len(v) if isinstance(v, list) else sum(len(x) for x in v.values())
    for g in GROUPS:                                     # every vector was replayed (write and joined: written and read back)
        want = size(vec[g]) * (2 if g in ('write', 'joined') else 1)
        assert counts[g] == [want, want], (g, counts[g], want)
    assert counts['cross'] == [len(extra['convert'])] * 2 and counts['bare'][0] == counts['bare'][1] > 0
    assert counts['cross_detect'] == [len(extra['detect']) + len(extra['prefer'])] * 2
    return {g: size(vec[g]) for g in GROUPS}, counts, per_stage


if __name__ == '__main__':
    res = test_core_js()
    if res is None:
        print('SKIP: the browser core is not checked: no node on this machine')
        sys.exit(0)
    sizes, counts, per_stage = res
    print(f'the browser core is the reference: {sum(sizes.values())} vectors ('
          + ', '.join(f'{g} {n}' for g, n in sizes.items()) + f'), {counts["bare"][0]} checks without a lexicon, '
          f'{counts["cross"][0]} conversions and {counts["cross_detect"][0]} detections equal to Python over '
          + ', '.join(f'{c} {n}' for c, n in per_stage.items()) + ' words')
