#!/usr/bin/env python3
"""The home page shows the whole alphabet. Run: python3 tests/test_site.py

Every point of data/script.yaml appears as a letter on the home page: in its
text, its charts or its tables (docs/index.md with its includes).
"""
import os
import re
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import script

MARK = '\u0300-\u036f'


def home():
    text = open(os.path.join(ROOT, 'docs', 'index.md'), encoding='utf-8').read()
    for name in re.findall(r'--8<-- "([^"]+)"', text):
        text += open(os.path.join(ROOT, 'docs', '.include', name), encoding='utf-8').read()
    return ud.normalize('NFC', text)


def test_complete():
    text = home()
    missing = []
    for name in script.POINTS:
        g = ud.normalize('NFC', script.glyph(name))
        if not re.search(f'(?<![\\w{MARK}]){re.escape(g)}(?![{MARK}])', text):      # the letter itself, not inside a longer one
            missing.append((name, g))
    assert not missing, f'not on the home page: {missing}'
    return len(script.POINTS)


if __name__ == '__main__':
    print(f'the home page shows the whole alphabet: {test_complete()} points')
