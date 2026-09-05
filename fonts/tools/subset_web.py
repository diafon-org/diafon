#!/usr/bin/env python3
"""Subset fonts/Diaphone-Regular.ttf -> docs/diaphone.woff2 for the pages.

Keeps basic Latin plus every codepoint any potential glyph of the system uses
(collected from docs/fonts-data.js, so regenerate that first), and reports the
codepoints the source font cannot yet serve — the drawing to-do list.
"""
import json
import os
import re

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def needed_codepoints():
    src = open(os.path.join(ROOT, 'docs', 'fonts-data.js')).read()
    data = json.loads(re.search(r'const MATRIX = (.*);', src).group(1))
    cps = set(range(0x20, 0x7F))
    for sec in data.values():
        for row in sec['rows']:
            for cell in row['cells']:
                if cell:
                    cps.update(ord(c) for c in cell['g'])
    return cps


def main():
    cps = needed_codepoints()
    src = os.path.join(ROOT, 'fonts', 'Diaphone-Regular.ttf')
    out = os.path.join(ROOT, 'docs', 'diaphone.woff2')
    have = set(TTFont(src).getBestCmap())
    missing = sorted(cps - have - set(range(0x20, 0x7F)))
    unis = ','.join(f'U+{c:04X}' for c in sorted(cps & have))
    subset.main([src, f'--unicodes={unis}', '--layout-features=*',
                 '--flavor=woff2', f'--output-file={out}'])
    print(f'{out}: {os.path.getsize(out)} bytes, {len(cps & have)} codepoints kept')
    if missing:
        print('codepoints the source font still needs drawn:',
              ' '.join(f'U+{c:04X}({chr(c)})' for c in missing))


if __name__ == '__main__':
    main()
