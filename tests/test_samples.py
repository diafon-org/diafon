#!/usr/bin/env python3
"""The converted texts are Diafon all the way through. Run: python3 tests/test_samples.py  (or pytest tests/)

1. Every sample text (scripts/gen_samples.py) and every Learn example word
   (docs/learn-data.js), shown in the script, uses only Diafon letters and
   marks: no letter of the source spelling is left over (Turkish ğ, Czech ě ů).
2. No spelling of the source language is left over either, though its
   letters are Diafon's own (Polish rz sz si+vowel, Finnish ng, Hungarian sz):
   a list per language.
3. The JS engine converts every sample text as the Python one does.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import universal_v1 as engine
import gen_samples
import lexicon
import stages

# the spellings that must not survive in the script, per language: the text is
# NFD and lower case, so a marked letter (n̦ = n + comma) never matches a plain one
LEFTOVER = {
    'pl': [r'rz', r'sz', r'cz', r'ch', r'dz', '(?<!n)[szcn]i(?![\u0300-\u036f])'],   # si ci zi ni are soft (not ï; powinni's long n aside)
    'cs': [r'ch', r'[dtn]i'],
    'fi': [r'ng', '(?<!n\u0323)n\u0323(?!n\u0323|k)'],    # ng is the long ṇṇ; a single ṇ only before k
    'hu': [r'sz', r'cs', r'zs', r'gy', r'ny', r'ty', r'ly'],
    'sw': [r'ch', r'sh', r'dh', r'th', r'gh', r'ny', r"ng'"],
    'tr': [],
    'en': [r"\w['’]\w", 'r\u0308[aeiou]'],            # an elision left over; r̈ before a vowel is ạr
    'zh': [],
}


def allowed_marks():
    """The combining marks the script uses: every mark in its table, and the tone signs."""
    marks = set()
    for glyph in engine.script_table(stages.used_forms()):
        marks.update(ch for ch in ud.normalize('NFD', glyph) if ud.combining(ch))
    return marks


MARKS = allowed_marks()
TONES = set(engine.TONE_OF)


def problems(code, text):
    """What in a script text is not Diafon: letters and marks, then leftover spellings."""
    out = []
    nfd = ud.normalize('NFD', text)
    for ch in nfd:
        if ud.combining(ch):
            if ch not in MARKS:
                out.append(f'mark U+{ord(ch):04X}')
        elif ch.isalpha() and not ('a' <= ch.lower() <= 'z' and ch.lower() != 'y') and ch not in TONES:
            out.append(f'letter {ch!r}')
    low = nfd.lower()
    for pat in LEFTOVER[code]:
        for m in re.finditer(pat, low):
            out.append(f'{pat}: ...{ud.normalize("NFC", low[max(0, m.start() - 6):m.end() + 6])}...')
    return out


def sample_texts():
    """(code, title, script) for each sample text, converted line by line as the page shows it."""
    return [(code, title, '\n'.join(stages.convert(l, 'stage:' + code, 'script') for l in text.split('\n')))
            for code, _, title, text in gen_samples.TEXTS]


def test_samples():
    bad = [(code, title, p) for code, title, script in sample_texts() for p in problems(code, script)]
    assert not bad, bad


def test_learn_words():
    src = open(os.path.join(ROOT, 'docs', 'learn-data.js'), encoding='utf-8').read()
    learn = json.loads(src[src.index('{'):src.rindex('}') + 1])
    bad = []
    for code, L in learn.items():
        for lesson in L['lessons']:
            for w in lesson['words'] + lesson['drill']:
                bad += [(code, w['w'], p) for p in problems(code, w['g'])] if code in LEFTOVER else []
    assert not bad, bad[:20]


JS = r'''
const fs = require('fs');
for (const code of LEX_CODES) setLexicon(code, JSON.parse(fs.readFileSync(LEX_DIR + '/' + code + '.json', 'utf8')));
const texts = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(texts.map(([c, t]) => t.split('\n').map(l => convert(l, 'stage:' + c, 'script')).join('\n'))));
'''


def test_js_parity():
    node = shutil.which('node')
    assert node, 'node is required for the JS parity test'
    data = open(os.path.join(ROOT, 'docs', 'play-data.js')).read()
    eng = open(os.path.join(ROOT, 'docs', 'engine.js')).read()
    lexdir = os.path.join(ROOT, 'data', 'lexicon')
    prog = data + '\n' + eng + f'\nconst LEX_CODES = {json.dumps(lexicon.codes())}, LEX_DIR = {json.dumps(lexdir)};' + JS
    texts = [(code, text) for code, _, _, text in gen_samples.TEXTS]
    res = subprocess.run([node, '-e', prog], input=json.dumps(texts), text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    got = json.loads(res.stdout)
    want = [script for _, _, script in sample_texts()]
    bad = [(t[0], g, w) for t, g, w in zip(texts, got, want) if g != w]
    assert not bad, bad[:3]


if __name__ == '__main__':
    test_samples()
    test_learn_words()
    test_js_parity()
    print('samples and Learn words are Diafon throughout; JS converts them alike')
