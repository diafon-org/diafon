#!/usr/bin/env python3
"""The pre-split goldens (split.md, P0): what the system writes at the tag
v1-presplit, frozen as the oracle for the split. Run once at the tag; never
regenerated afterwards. `--check` recomputes every frozen row from its own
input with the code as it is (through the bridge, scripts/universal_v1.py).

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
import re
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import universal_v1 as engine
import gen_samples
from universal_v1 import lexicon
from universal_v1 import stages

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


def write(name, rows):
    text = ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows)
    data = text.encode('utf-8')
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


def generate():
    if os.path.exists(os.path.join(OUT, 'MANIFEST.json')) and '--force' not in sys.argv:
        sys.exit('tests/goldens exists: the goldens are frozen (split.md, P0)')
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(OUT, 'spec.json')
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
    with open(os.path.join(OUT, 'MANIFEST.json'), 'w', encoding='utf-8') as f:
        json.dump({'tag': 'v1-presplit', 'stages': CODES, 'files': MANIFEST}, f, indent=1, sort_keys=True)
        f.write('\n')


# ---- the check: the frozen inputs through the code as it is ----
#
# Every frozen row is recomputed from its own input (the typed text, or the
# spelling) and must come out the same. Two differences are the split's own
# decisions and are counted, not failed (split.md, decision 4 and the text
# as script):
#   doubled   two equal consonants in a row are the long one once the text
#             is script, so a word a lexicon reads comes back typed long
#   caps      a word typed with capital operators (SJ) is the same script
#             text as Sj, so a lexicon now finds it
#   alphabet  a spelling the alphabet changed on purpose since (CHANGED), in that stage's column only
#   letterq   a text typed with kq, the letter q the alphabet no longer has
#   inside    a prefix lexicon's stem that ended inside a typed form (hely in
#             heixtx) used to leave the operator over; a letter is not cut

# spellings the alphabet has changed since the split, on purpose: their rows no longer bind
CHANGED = {'pl', 'zh'}      # 2026-11-21: the hush on the anchor, the soft series on the dot (Polish; Mandarin's j q x)


def letter_q(t):
    """A typed text with the old form of the letter q (kq): q left the alphabet, /q/ is k̤, typed ky."""
    return 'kq' in t.lower()


def today(x):
    """A frozen row with the mark the alphabet has since changed (the reverse anchor, now the double
    dot below): U+0316 is U+0324, and above a letter U+0314 is U+0308."""
    if isinstance(x, str):
        # the glide of ü moved from j to w (j̈ and ẅ change places), before the mark that became U+0308
        swap = {'j\u0308': '\u1e85', 'J\u0308': '\u1e84', '\u1e85': 'j\u0308', '\u1e84': 'J\u0308',
                'w\u0308': 'j\u0308', 'W\u0308': 'J\u0308'}
        x = re.sub('[jJwW]\u0308|[\u1e84\u1e85]', lambda m: swap[m.group()], x)
        return x.replace('\u0316', '\u0324').replace('\u0314', '\u0308')
    if isinstance(x, list):
        return [today(v) for v in x]
    if isinstance(x, dict):
        return {k: today(v) for k, v in x.items()}
    return x


def frozen(name):
    path = os.path.join(OUT, name)
    data = (gzip.open(path, 'rb') if name.endswith('.gz') else open(path, 'rb')).read()
    want = json.load(open(os.path.join(OUT, 'MANIFEST.json'), encoding='utf-8'))['files'][name]['sha256']
    assert hashlib.sha256(data).hexdigest() == want, f'{name}: the frozen file itself has changed'
    return [json.loads(l) for l in data.decode('utf-8').splitlines()]


def doubled(t):
    toks = engine.points(t, strict=False)
    return any(a.point and b.point and a.comp == b.comp and not a.tones and not a.long and not b.long
               and a.comp[0] not in 'aeiou' for a, b in zip(toks, toks[1:]))


def caps_operators(t):
    return any(s['kind'] == 'form' and s['src'][1:len(s['form'])] != s['form'][1:]
               for s in engine.segments(t, strict=False))


def inside(t, code):
    """Whether the longest stem a prefix lexicon finds in a typed word ends
    inside one of its forms (hely in heixtx, cutting tx): the old writer
    then left the operator over; the script cannot be cut there."""
    L = lexicon.lex(code)
    if not L or L['match'] != 'prefix':
        return False
    key = t[0].lower() + t[1:]
    best = max((s for s in L['write'] if key.startswith(s)), key=len, default=None)
    ends, n = set(), 0
    for seg in engine.segments(t, strict=False):
        n += len(seg['src'])
        ends.add(n)
    return best is not None and len(best) not in ends


def same_script(a, b):
    return engine.render(a, strict=False) == engine.render(b, strict=False)


def check():
    show = int(os.environ.get('GOLDEN_SHOW', '5'))
    failed = 0
    names = json.load(open(os.path.join(OUT, 'MANIFEST.json'), encoding='utf-8'))['files']
    for name in names:
        if name == 'spec.json':
            continue
        rows = frozen(name)
        counts, bad = {'doubled': 0, 'caps': 0, 'inside': 0, 'alphabet': 0, 'letterq': 0}, []
        stage = stages.load(name[5:7]) if name.startswith('read/') else None
        for old in rows:
            old = today(json.loads(json.dumps(old)))        # the reverse anchor is the double dot below now
            if name.startswith('read/'):
                new = [old[0]] + list(stages.read_word(old[0], stage))
                if new != old:
                    if new[2] == old[2] and doubled(old[1]) and same_script(old[1], new[1]):
                        counts['doubled'] += 1
                    elif name[5:7] in CHANGED:
                        counts['alphabet'] += 1     # a spelling the alphabet reads differently now
                    else:
                        bad.append((old, new))
                continue
            if name == 'samples.jsonl':
                t = stages.parse(old[2], f'stage:{old[0]}')
                new = old[:3] + row(t)
                if new != old:
                    if doubled(old[3]) and same_script(old[3], new[3]) and new[4:] == old[4:]:
                        counts['doubled'] += 1
                    elif old[0] in CHANGED or (new[:6] == old[:6] and all(c in CHANGED for c in old[6] if old[6][c] != new[6][c])):
                        counts['alphabet'] += 1     # a text in a changed spelling, or its column of another text
                    else:
                        bad.append((old, new))
                continue
            new = json.loads(json.dumps(row(old[0])))
            if new != old:
                if letter_q(old[0]):
                    counts['letterq'] += 1
                elif caps_operators(old[0]) and new[:3] == old[:3]:
                    counts['caps'] += 1
                elif new[:3] == old[:3] and all(inside(old[0], c) for c in old[3] if old[3][c] != new[3][c]):
                    counts['inside'] += 1
                elif new[:3] == old[:3] and all(c in CHANGED for c in old[3] if old[3][c] != new[3][c]):
                    counts['alphabet'] += 1
                else:
                    bad.append((old, new))
        noted = ', '.join(f'{n} {k}' for k, n in counts.items() if n)
        print(f'{name}: {len(rows)} rows, {"same" if not bad else f"{len(bad)} DIFFER"}' + (f' ({noted})' if noted else ''))
        failed += len(bad)
        for o, n in bad[:show]:
            for k in range(min(len(o), len(n))):
                if o[k] != n[k]:
                    if isinstance(o[k], dict):
                        print('   ', o[0], {c: (o[k][c], n[k].get(c)) for c in o[k] if o[k][c] != n[k].get(c)})
                    else:
                        print('   ', o[0], (o[k], n[k]))
    sys.exit(f'goldens differ: {failed} rows' if failed else 0)


if __name__ == '__main__':
    check() if '--check' in sys.argv else generate()
