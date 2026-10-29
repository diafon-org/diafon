#!/usr/bin/env python3
"""Generate fonts/hand/tails.html (and tails.pdf where Chrome is present):
printable A4 pages of the letters that take a tail below, large and pale,
one row per letter the system anchors (fonts/glyphs.js; --reserve adds the
reserve's): the small letter with the anchor U+0326 and the reverse U+0316,
then the capital with both, sized so the widest row fills the line; to draw
the tails on by hand: black for ink,
blue for what to take away. Each cell has the guides a tail needs, none of
them blue: the baseline, x-height and cap height, the descender, the foot's
plate (top -288, bottom -330) and the letter's origin and advance. The four
black corner squares of each page register a scan; fonts/hand/tails.json
records where every cell sits, in millimetres, for reading the drawings
back.

    python3 fonts/tools/tail_sheet.py [--em mm] [--reserve] [letters]   # letters: only these rows
"""
import json
import os
import re
import subprocess
import sys
import unicodedata

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.path.join(ROOT, 'fonts', 'hand', 'tails.html')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
ORDER = 'tskbnmhdcvxz'              # the drawn ones first, then their kin; capitals after
MARKS = {0x0326: 'anchor', 0x0316: 'reverse'}
PAGE_W, PAGE_H, MARGIN, SQUARE = 210, 297, 8, 5
TOP, BOTTOM = 800, -370                          # a cell in font units, around the letter
ROOM, NEAR = 320, 70                             # the room on the tail's side (left of an anchor,
                                                 #   right of a reverse) and on the other
LABEL = 4.5                                      # mm above each cell for its name
GAP = 2.5


def pairs(reserve=False):
    """[(letter, mark)] with a tail below that the glyph matrix uses (or
    keeps in reserve), lowercase in ORDER, then the same as capitals."""
    src = open(os.path.join(ROOT, 'fonts', 'glyphs.js')).read()
    data = json.loads(re.search(r'const MATRIX = (.*);', src).group(1))
    found = set()
    for sec in data.values():
        for row in sec['rows']:
            for c in row['cells']:
                if c and (c['langs'] or reserve):
                    g = unicodedata.normalize('NFD', c['g'])
                    found.update((g[i - 1], ord(ch)) for i, ch in enumerate(g) if i and ord(ch) in MARKS)
    low = sorted(found, key=lambda p: (ORDER.index(p[0]) if p[0] in ORDER else 99, p[1] != 0x0326))
    return low + [(L.upper(), m) for L, m in low]


def main(argv):
    em, reserve = None, '--reserve' in argv
    if '--em' in argv:
        i = argv.index('--em'); em = float(argv[i + 1]); del argv[i:i + 2]
    argv = [a for a in argv if a != '--reserve']
    letters = []                                  # one row per letter: small and capital, anchor and reverse
    for L, _ in pairs(reserve):
        if L.islower() and L not in letters and (not argv or L in argv[0]):
            letters.append(L)
    rows = [[(L, 0x0326), (L, 0x0316), (L.upper(), 0x0326), (L.upper(), 0x0316)] for L in letters]
    font = TTFont(os.path.join(ROOT, 'fonts', 'build', 'DiafonSerif-derived.ttf'))
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    x0, x1 = MARGIN + SQUARE + 2, PAGE_W - MARGIN - SQUARE - 2
    if em is None:                                # the widest row fills the line
        widest = max(sum(ROOM + font['hmtx'][cmap[ord(L)]][0] + NEAR for L, _ in row) for row in rows)
        em = int((x1 - x0 - GAP * 3) / widest * 1000 * 2) / 2
    k = em / 1000                                 # mm per font unit
    cell_h = (TOP - BOTTOM) * k
    y_first = MARGIN + SQUARE + 6
    pages, cells, y = [[]], [], y_first
    for n, row in enumerate(rows):
        if n and y + 2 * (LABEL + cell_h) + GAP > PAGE_H - MARGIN - SQUARE - 2:
            pages.append([]); y = y_first
        elif n:
            y += LABEL + cell_h + GAP
        x = x0
        for L, mark in row:
            g, label = cmap[ord(L)], MARKS[mark]
            adv = font['hmtx'][g][0]
            left = ROOM if mark == 0x0326 else NEAR
            w = (ROOM + adv + NEAR) * k
            ox, oy = x + left * k, y + LABEL + TOP * k    # the font origin on the page, mm
            comp = f'{g}_uni{mark:04X}'
            pages[-1].append((L, g, comp, label, mark, x, y, w, ox, oy, adv))
            cells.append({'page': len(pages), 'glyph': comp, 'letter': L, 'mark': f'U+{mark:04X}',
                          'origin_mm': [round(ox, 3), round(oy, 3)], 'mm_per_unit': k, 'advance': adv,
                          'box_mm': [round(x, 3), round(y + LABEL, 3), round(w, 3), round(cell_h, 3)]})
            x += w + GAP
    svgs = []
    for n, page in enumerate(pages, 1):
        parts = [f'<rect x="{MARGIN}" y="{MARGIN}" width="{SQUARE}" height="{SQUARE}"/>',
                 f'<rect x="{PAGE_W - MARGIN - SQUARE}" y="{MARGIN}" width="{SQUARE}" height="{SQUARE}"/>',
                 f'<rect x="{MARGIN}" y="{PAGE_H - MARGIN - SQUARE}" width="{SQUARE}" height="{SQUARE}"/>',
                 f'<rect x="{PAGE_W - MARGIN - SQUARE}" y="{PAGE_H - MARGIN - SQUARE}" width="{SQUARE}" height="{SQUARE}"/>',
                 f'<text x="{PAGE_W / 2}" y="{MARGIN + 4}" text-anchor="middle" font-size="3.4" fill="#666">'
                 f'Diafon Serif · black: the tail · blue: what to take away · page {n} of {len(pages)} · print at 100%</text>']
        for L, g, comp, label, mark, x, y, w, ox, oy, adv in page:
            line = lambda fy, color, dash='', sw=0.15: (
                f'<line x1="{x:.2f}" x2="{x + w:.2f}" y1="{oy - fy * k:.2f}" y2="{oy - fy * k:.2f}" '
                f'stroke="{color}" stroke-width="{sw}"{dash}/>')
            vline = lambda fx, dash='': (
                f'<line x1="{ox + fx * k:.2f}" x2="{ox + fx * k:.2f}" y1="{oy - TOP * k:.2f}" y2="{oy - BOTTOM * k:.2f}" '
                f'stroke="#f0b070" stroke-width="0.15"{dash}/>')
            d = ' stroke-dasharray="1 0.8"'
            pen = SVGPathPen(gs)
            gs[g].draw(TransformPen(pen, (k, 0, 0, -k, ox, oy)))
            parts += [f'<rect x="{x:.2f}" y="{y + LABEL:.2f}" width="{w:.2f}" height="{cell_h:.2f}" fill="none" stroke="#99a" stroke-width="0.2"/>',
                      f'<text x="{x + 1:.2f}" y="{y + LABEL - 1.2:.2f}" font-size="2.8" fill="#333">{L} {label}</text>',
                      line(536, '#d0d0d0', d), line(714, '#d0d0d0', d), line(-240, '#d0d0d0', d),
                      line(-288, '#9fc08a', ' stroke-dasharray="0.4 0.6"'), line(-330, '#9fc08a', ' stroke-dasharray="0.4 0.6"'),
                      line(0, '#a8a8a8', sw=0.25), vline(0), vline(adv, d),
                      f'<path d="{pen.getCommands()}" fill="#e2e2e2" stroke="#b8b8b8" stroke-width="0.12"/>']
        svgs.append(f'<svg class="page" xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" height="{PAGE_H}mm" '
                    f'viewBox="0 0 {PAGE_W} {PAGE_H}" font-family="Helvetica, Arial, sans-serif">' + ''.join(parts) + '</svg>')
    html = ('<!doctype html><html><head><meta charset="utf-8"><title>Diafon tails</title><style>'
            '@page{size:A4;margin:0}body{margin:0}.page{display:block;page-break-after:always}'
            '@media screen{body{background:#ddd}.page{background:#fff;margin:6mm auto;box-shadow:0 0 6mm rgba(0,0,0,.2)}}'
            '</style></head><body>' + ''.join(svgs) + '</body></html>')
    open(OUT, 'w').write(html)
    json.dump({'page_mm': [PAGE_W, PAGE_H], 'squares_mm': {'size': SQUARE, 'margin': MARGIN}, 'cells': cells},
              open(OUT[:-5] + '.json', 'w'), indent=1)
    print(f'{os.path.relpath(OUT, ROOT)}: {len(cells)} cells on {len(pages)} pages, {em:g} mm to the em')
    pdf = OUT[:-5] + '.pdf'
    if os.path.exists(CHROME):
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        f'--print-to-pdf={pdf}', 'file://' + OUT], capture_output=True)
        if os.path.exists(pdf):
            print(f'{os.path.relpath(pdf, ROOT)} written')
    else:
        print('  (no Chrome: print tails.html from a browser at 100%)')


if __name__ == '__main__':
    main(sys.argv[1:])
