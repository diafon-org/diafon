#!/usr/bin/env python3
"""Subset the Diafon families -> docs/diafon.woff2 (serif), diafon-sans.woff2, diafon-mono.woff2.

Keeps basic Latin plus every codepoint any potential glyph of the system uses
(collected from fonts/glyphs.js, so regenerate that first), and reports the
codepoints the source font cannot yet serve — the drawing to-do list.
"""
import json
import os
import re

import yaml
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def needed_codepoints():
    src = open(os.path.join(ROOT, 'fonts', 'glyphs.js')).read()
    data = json.loads(re.search(r'const MATRIX = (.*);', src).group(1))
    cps = set(range(0x20, 0x7F))
    import unicodedata as ud
    for sec in data.values():
        for row in sec['rows']:
            for cell in row['cells']:
                if cell:
                    for form in ('NFC', 'NFD'):
                        cps.update(ord(c) for c in ud.normalize(form, cell['g']))
                        cps.update(ord(c) for c in ud.normalize(form, cell['g'].upper()))
    # every mark the script defines: the playground free-types any form
    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, str):
            cps.update(ord(c) for c in node)
    walk(yaml.safe_load(open(os.path.join(ROOT, 'data', 'script.yaml'))))
    return {c for c in cps if c >= 0x20}


WEB = {'serif': 'diafon.woff2', 'sans': 'diafon-sans.woff2', 'mono': 'diafon-mono.woff2'}


def main():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_font as BF
    cps = needed_codepoints()
    missing = set()
    for key, name in WEB.items():
        src = BF.family(key)['ttf']
        if not os.path.exists(src):
            print(f'{name}: no {os.path.relpath(src, ROOT)} yet, skipped')
            continue
        out = os.path.join(ROOT, 'docs', name)
        have = set(TTFont(src).getBestCmap())
        missing |= cps - have - set(range(0x20, 0x7F))
        unis = ','.join(f'U+{c:04X}' for c in sorted(cps & have))
        subset.main([src, f'--unicodes={unis}', '--layout-features=*',
                     '--flavor=woff2', f'--output-file={out}'])
        print(f'{out}: {os.path.getsize(out)} bytes, {len(cps & have)} codepoints kept')
        ver = os.path.getmtime(out).__int__()
        for page in ('assets/diafon.css',):      # the site's stylesheet declares the faces
            p = os.path.join(ROOT, 'docs', page)
            if not os.path.exists(p):
                continue
            html = open(p).read()
            html = re.sub(re.escape(name) + r'(\?v=\d+)?', f'{name}?v={ver}', html)
            open(p, 'w').write(html)
    missing = sorted(missing)
    print('cache-bust: pages reference the fresh woff2 files')
    if missing:
        print('codepoints the source font still needs drawn:',
              ' '.join(f'U+{c:04X}({chr(c)})' for c in missing))


if __name__ == '__main__':
    main()
