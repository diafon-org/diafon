#!/usr/bin/env python3
"""Generate fonts/hand/families.html (and families.pdf where Chrome is
present): A4 pages to draw the serif tails on by hand, a few letters for each
joint type (FAMILIES: the letters stand for their family), two families to a
page. Each letter's bottom (from TOP down) stands in a box with its guides,
the anchor (U+0326) in the left column, the reverse (U+0316) in the right;
the baseline and the floor run on past the box into OVERFLOW on the tail's
side (left of an anchor, right of a reverse), and the page around the boxes is
free to draw on. Black for ink, blue for what to take away; the corner squares
register a scan, and fonts/hand/families.json records where every letter
sits, in millimetres.

    python3 fonts/tools/family_sheet.py [family ...]      # default: all of FAMILIES
"""
import json
import os
import subprocess
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'fonts', 'hand', 'families.html')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
FAMILIES = {                                    # family: the letters that stand for it (its others)
    'stems': 'nT',                              #   upright stem on a foot serif (m N M P)
    'legs': 'xX',                               #   diagonal leg on a foot serif (k K)
    'bars': 'zZ',                               #   flat bar, its beak at the right end
    'bowls': 'dD',                              #   bowl meeting a stem (b B)
    'curves': 'cS',                             #   open curve (C s G t)
}
ANCHOR = set('tskbnmdcxzTSKBNMDCXZPG')          # the letters that take U+0326
REVERSE = set('tsnmdcxzTSNMDCXZPG')             #   and U+0316
PAGE_W, PAGE_H, MARGIN, SQUARE = 210, 297, 8, 5
TOP, BOTTOM = 250, -370                         # the box in font units: the letter's bottom, the tail's room
ROOM, NEAR = 260, 90                            # in the box: room on the tail's side and on the other
OVERFLOW = 22                                   # mm the guides run on past the box on the tail's side
EM = 62                                         # mm to the em
PER_PAGE = 2                                    # families to a page
REFERENCES = [('Athelas', '/System/Library/Fonts/Supplemental/Athelas.ttc'),     # a first page: Q from these,
              ('PT Serif', '/System/Library/Fonts/Supplemental/PTSerif.ttc')]    #   scaled to our cap height, as a guide


def reference_page(k):
    """The Qs of REFERENCES (those installed), on the sheet's guides, at its scale."""
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.ttLib import TTCollection
    parts, y = [], MARGIN + SQUARE + 30
    for name, path in REFERENCES:
        if not os.path.exists(path):
            continue
        f = TTCollection(path).fonts[0] if path.endswith('.ttc') else TTFont(path)
        gs, cm = f.getGlyphSet(), f.getBestCmap()
        b = BoundsPen(gs); gs[cm[ord('H')]].draw(b)
        s = 714 / b.bounds[3] * k                                                   # its cap height to ours
        q = BoundsPen(gs); gs[cm[ord('Q')]].draw(q)
        oy = y + 714 * k
        ox = (PAGE_W - (q.bounds[2] - q.bounds[0]) * s) / 2 - q.bounds[0] * s
        pen = SVGPathPen(gs)
        gs[cm[ord('Q')]].draw(TransformPen(pen, (s, 0, 0, -s, ox, oy)))
        line = lambda fy, color, sw=0.15, dash='': (
            f'<line x1="{MARGIN + SQUARE + 4}" x2="{PAGE_W - MARGIN - SQUARE - 4}" y1="{oy - fy * k:.2f}" '
            f'y2="{oy - fy * k:.2f}" stroke="{color}" stroke-width="{sw}"{dash}/>')
        parts += [line(fy, '#efefef', 0.12) for fy in range(-50, BOTTOM, -50)]
        parts += [line(-240, '#d4d4d4', 0.15, ' stroke-dasharray="1 0.8"'),
                  line(-288, '#a8c897', 0.15, ' stroke-dasharray="0.4 0.6"'),
                  line(-330, '#a8c897', 0.15, ' stroke-dasharray="0.4 0.6"'), line(0, '#a8a8a8', 0.25),
                  f'<path d="{pen.getCommands()}" fill="#bbb"/>',
                  f'<text x="{MARGIN + SQUARE + 4}" y="{y - 3:.2f}" font-size="3.6" fill="#444">{name} Q '
                  f'<tspan fill="#999" font-size="2.8">· its tail to {q.bounds[1] * s / k:.0f} (ours: -330)</tspan></text>']
        y = oy - BOTTOM * k + 22
    if not parts:
        return []
    parts += [f'<rect x="{x}" y="{y}" width="{SQUARE}" height="{SQUARE}"/>'
              for x in (MARGIN, PAGE_W - MARGIN - SQUARE) for y in (MARGIN, PAGE_H - MARGIN - SQUARE)]
    return [f'<svg class="page" xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" height="{PAGE_H}mm" '
            f'viewBox="0 0 {PAGE_W} {PAGE_H}" font-family="Helvetica, Arial, sans-serif">' + ''.join(parts) + '</svg>']


def main(argv):
    names = argv or list(FAMILIES)
    font = TTFont(os.path.join(ROOT, 'fonts', 'build', 'DiafonSerif-derived.ttf'))
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    adv = lambda L: font['hmtx'][cmap[ord(L)]][0]
    k = EM / 1000
    box_h = (TOP - BOTTOM) * k
    pages = [names[i:i + PER_PAGE] for i in range(0, len(names), PER_PAGE)]
    rows_on_page = PER_PAGE * 2
    top0, bottom0 = MARGIN + SQUARE + 8, PAGE_H - MARGIN - SQUARE - 4
    pitch = (bottom0 - top0) / rows_on_page                                         # rows spread down the page
    svgs, cells = [], []
    for n, fams in enumerate(pages, 1):
        parts = [f'<rect x="{x}" y="{y}" width="{SQUARE}" height="{SQUARE}"/>'
                 for x in (MARGIN, PAGE_W - MARGIN - SQUARE) for y in (MARGIN, PAGE_H - MARGIN - SQUARE)]
        parts.append(f'<text x="{PAGE_W / 2}" y="{MARGIN + 4}" text-anchor="middle" font-size="2.8" fill="#999">'
                     f'black: tail · blue: take away · print at 100%</text>')
        r = 0
        for fam in fams:
            for i, L in enumerate(FAMILIES[fam]):
                y = top0 + r * pitch + (pitch - box_h) / 2 + 2
                if i == 0:
                    parts.append(f'<text x="{MARGIN + SQUARE + 4}" y="{y - 5:.2f}" font-size="3.6" fill="#444">{fam}</text>')
                oy = y + TOP * k                                                    # the baseline, mm
                for col, mark in enumerate((0x0326, 0x0316)):
                    if L not in (ANCHOR if mark == 0x0326 else REVERSE):
                        continue
                    a = adv(L)
                    left, right = (ROOM, NEAR) if mark == 0x0326 else (NEAR, ROOM)
                    w = (left + a + right) * k
                    bx = (PAGE_W / 2 - 6 - w) if col == 0 else (PAGE_W / 2 + 6)   # the columns meet in the middle,
                    ox = bx + left * k                                              #   the overflow outward
                    cid = f'b{len(cells)}'
                    pen = SVGPathPen(gs)
                    gs[cmap[ord(L)]].draw(TransformPen(pen, (k, 0, 0, -k, ox, oy)))
                    hline = lambda fy, color, sw=0.15, dash='', x0=bx, x1=bx + w: (
                        f'<line x1="{x0:.2f}" x2="{x1:.2f}" y1="{oy - fy * k:.2f}" y2="{oy - fy * k:.2f}" '
                        f'stroke="{color}" stroke-width="{sw}"{dash}/>')
                    vline = lambda fx, dash='': (
                        f'<line x1="{ox + fx * k:.2f}" x2="{ox + fx * k:.2f}" y1="{y:.2f}" y2="{y + box_h:.2f}" '
                        f'stroke="#f0b070" stroke-width="0.15"{dash}/>')
                    ov = (bx - OVERFLOW, bx) if col == 0 else (bx + w, bx + w + OVERFLOW)
                    parts += [f'<clipPath id="{cid}"><rect x="{bx:.2f}" y="{y:.2f}" width="{w:.2f}" height="{box_h:.2f}"/></clipPath>',
                              f'<g clip-path="url(#{cid})">']
                    parts += [hline(fy, '#efefef', 0.12) for fy in range(-50, BOTTOM, -50)]
                    parts += [hline(-240, '#d4d4d4', 0.15, ' stroke-dasharray="1 0.8"'),
                              hline(-288, '#a8c897', 0.15, ' stroke-dasharray="0.4 0.6"'),
                              hline(-330, '#a8c897', 0.15, ' stroke-dasharray="0.4 0.6"'),
                              hline(0, '#a8a8a8', 0.25), vline(0), vline(a, ' stroke-dasharray="1 0.8"'),
                              f'<path d="{pen.getCommands()}" fill="#e2e2e2" stroke="#b8b8b8" stroke-width="0.12"/></g>',
                              f'<rect x="{bx:.2f}" y="{y:.2f}" width="{w:.2f}" height="{box_h:.2f}" fill="none" stroke="#99a" stroke-width="0.2"/>',
                              hline(0, '#c8c8c8', 0.2, ' stroke-dasharray="0.6 0.8"', *ov),
                              hline(-330, '#c4dcb8', 0.15, ' stroke-dasharray="0.4 0.6"', *ov),
                              f'<text x="{bx + 1:.2f}" y="{y - 1.2:.2f}" font-size="2.6" fill="#888">'
                              f'{L} {"anchor" if mark == 0x0326 else "reverse"}</text>']
                    cells.append({'page': n, 'family': fam, 'glyph': f'{cmap[ord(L)]}_uni{mark:04X}', 'letter': L,
                                  'mark': f'U+{mark:04X}', 'origin_mm': [round(ox, 3), round(oy, 3)], 'mm_per_unit': k,
                                  'advance': a, 'box_mm': [round(bx, 3), round(y, 3), round(w, 3), round(box_h, 3)]})
                r += 1
        svgs.append(f'<svg class="page" xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" height="{PAGE_H}mm" '
                    f'viewBox="0 0 {PAGE_W} {PAGE_H}" font-family="Helvetica, Arial, sans-serif">' + ''.join(parts) + '</svg>')
    svgs = reference_page(k) + svgs
    html = ('<!doctype html><html><head><meta charset="utf-8"><title>Diafon tails by family</title><style>'
            '@page{size:A4;margin:0}body{margin:0}.page{display:block;page-break-after:always}'
            '@media screen{body{background:#ddd}.page{background:#fff;margin:6mm auto;box-shadow:0 0 6mm rgba(0,0,0,.2)}}'
            '</style></head><body>' + ''.join(svgs) + '</body></html>')
    open(OUT, 'w').write(html)
    json.dump({'page_mm': [PAGE_W, PAGE_H], 'squares_mm': {'size': SQUARE, 'margin': MARGIN}, 'cells': cells},
              open(OUT[:-5] + '.json', 'w'), indent=1)
    print(f'{os.path.relpath(OUT, ROOT)}: {len(cells)} boxes on {len(svgs)} pages, {EM} mm to the em')
    pdf = OUT[:-5] + '.pdf'
    if os.path.exists(CHROME):
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        f'--print-to-pdf={pdf}', 'file://' + OUT], capture_output=True)
        if os.path.exists(pdf):
            print(f'{os.path.relpath(pdf, ROOT)} written')
    else:
        print('  (no Chrome: print families.html from a browser at 100%)')


if __name__ == '__main__':
    main(sys.argv[1:])
