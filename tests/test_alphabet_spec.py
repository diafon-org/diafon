#!/usr/bin/env python3
"""The alphabet's contract, as tests. Run: python3 tests/test_alphabet_spec.py  (or pytest tests/)

1. docs/alphabet-spec.json is what scripts/gen_alphabet_spec.py writes now.
2. Names: every point's name is NFC, unique, and made of IPA letters and
   modifiers only (no ASCII colon for ː, no decomposed mark); a long point is
   its short one with ː.
3. One reading: over the points and the open compositions, short and long,
   small and capital, plain and joined, no two share a glyph, and every
   glyph reads back as what wrote it.
4. The vectors reproduce through the reference: points -> script, script ->
   points, each stage written and read, convert, detect, the lexicon.
5. Nothing in it is typing: no field of the spec names a form, an operator,
   a key or a transport form.
"""
import json
import os
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gen_alphabet_spec as G
import lexicon
import script
import stages

SPEC = json.load(open(G.OUT, encoding='utf-8'))
VEC = SPEC['vectors']


def test_current():
    fresh = json.loads(json.dumps(G.build(), ensure_ascii=False))
    assert fresh == SPEC, 'docs/alphabet-spec.json is stale: run scripts/gen_alphabet_spec.py'


def test_names():
    seen = set()
    for p in SPEC['points']:
        name = p['id']
        assert name == ud.normalize('NFC', name), name
        assert name not in seen, name
        seen.add(name)
        for ch in name:
            assert not ch.isascii() or ch.isalpha(), (name, ch)
            assert ud.category(ch)[0] in 'LM', (name, ch, ud.category(ch))
        assert p['long'] == name.endswith(SPEC['script']['long'])
        if p['long']:
            assert name[:-1] in seen, f'{name}: its short point is not listed before it'
        assert script.glyph(name) == p['glyph'] and script.glyph(name, caps=True) == p['capital']


def test_one_reading():
    glyphs = {}
    for comp in script.compositions():
        for long in (False, True):
            for caps in (False, True):
                for join in ((False, True) if long and comp[0] not in script.VOWELS else (False,)):
                    g = script.glyph(comp, long, caps, join)
                    assert glyphs.setdefault(g, (comp, long, caps)) == (comp, long, caps), g
                    t = script.read(g)
                    assert len(t) == 1 and (t[0].comp, t[0].long, t[0].caps) == (comp, long, caps), (g, t)
    listed = {(c['letter'], tuple(c['marks'])): c for c in SPEC['compositions']}
    assert set(listed) == set(script.compositions())
    for comp, c in listed.items():
        assert c['id'] == script.NAME.get(comp)
        for long, caps, join, field in ((0, 0, 0, 'glyph'), (0, 1, 0, 'capital'), (1, 0, 0, 'long'), (1, 1, 0, 'long_capital'),
                                        (1, 0, 1, 'joined'), (1, 1, 1, 'joined_capital')):
            if field in c:
                assert script.glyph(comp, bool(long), bool(caps), bool(join)) == c[field], (comp, field)


def toks(xs):
    return [G.token(x) for x in xs]


def test_vectors():
    for pts, text in VEC['write']:
        assert script.write(toks(pts)) == text, (pts, text)
        assert G.plains(script.read(text)) == pts, (text, pts)
    for pts, text in VEC['joined']:
        assert script.write(toks(pts), join=True) == text, (pts, text)
        assert G.plains(script.read(text)) == pts, (text, pts)
    for text, pts in VEC['read']:
        assert G.plains(script.read(text)) == pts, (text, pts)
    for code, vec in VEC['stage_write'].items():
        for pts, spelled in vec:
            assert stages.render(toks(pts), code) == spelled, (code, pts, spelled)
    for code, vec in VEC['stage_read'].items():
        for spelled, pts in vec:
            assert G.plains(stages.parse(spelled, f'stage:{code}')) == pts, (code, spelled, pts)
    for text, source, target, out in VEC['convert']:
        assert stages.convert(text, source, target) == out, (text, source, target)
    for text, source in VEC['detect'] + VEC['lexicon']['detect']:
        assert stages.detect(text)[0][0] == source, (text, source)
    L = VEC['lexicon']
    for code, word, s in L['read']:
        assert lexicon.read_word(word, code) == s, (code, word)
    for code, s, want in L['write']:
        hit = lexicon.write_word(script.read(s), code)
        assert ([hit[0], script.write(hit[1])] if isinstance(hit, tuple) else hit) == want, (code, s)
    for code, word, s in L['loan']:
        assert (lexicon.loan(word, code) or [None])[0] == s, (code, word)
    for key, chars in L['choices']:
        assert lexicon.choices(key)[:6] == chars, key
    for source, text, s in L['parse']:
        assert script.write(stages.parse(text, source)) == s, (source, text)
    for source, text, out in L['roundtrip']:
        assert stages.convert(text, source, source) == out, (source, text)


TYPING = {'form', 'forms', 'operator', 'operators', 'transport', 'input', 'key', 'keys', 'bases'}


def test_no_typing():
    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if path[:1] not in (['languages'], ['stages'], ['points']) or k in ('name', 'sounds', 'points'):
                    assert k not in TYPING, '/'.join(path + [k])
                walk(v, path + [k])
        elif isinstance(node, list):
            for v in node:
                walk(v, path)
        elif isinstance(node, str):
            assert node not in ('transport',), '/'.join(path)
    walk(SPEC, [])
    for st in SPEC['stages'].values():
        for name in list(st['points']) + list(st['caps']) + list(st['before_i']) + list(st['before_vowel']):
            assert name in {p['id'] for p in SPEC['points']} or name.rstrip(SPEC['script']['long']) in \
                {p['id'] for p in SPEC['points']}, name
        assert script.is_script(st['sample'].replace(' ', '').replace(',', '')) or not st['sample'], st['sample']


if __name__ == '__main__':
    test_current()
    test_names()
    test_one_reading()
    test_vectors()
    test_no_typing()
    n = sum(len(v) for v in VEC.values() if isinstance(v, list)) + sum(len(x) for v in VEC.values() if isinstance(v, dict) for x in v.values())
    print(f'the alphabet spec holds: version {SPEC["version"]}, {len(SPEC["points"])} points, {n} vectors')
