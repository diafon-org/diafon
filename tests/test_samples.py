#!/usr/bin/env python3
"""The converted texts are Diafon all the way through. Run: python3 tests/test_samples.py  (or pytest tests/)

1. Every sample text (scripts/gen_samples.py), shown in the script, uses only
   Diafon letters and marks: no letter of the source spelling is left over
   (Turkish ğ, Czech ě ů).
2. No spelling of the source language is left over either, though its
   letters are Diafon's own (Polish rz sz si+vowel, Finnish ng, Hungarian sz):
   a list per language.
"""
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gen_samples
import script
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
    'en': [r"\w['’]\w", 'r\u0308[aeiou]'],            # an elision left over; r̈ before a vowel is ër
    'zh': [],
}


MARKS = {ch for m in script.MARKS.values() for ch in m.values()}
TONES = set(script.TONE_OF)


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


if __name__ == '__main__':
    test_samples()
    print(f'the sample texts are Diafon throughout: {len(gen_samples.TEXTS)} texts')
