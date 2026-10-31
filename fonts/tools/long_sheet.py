#!/usr/bin/env python3
"""The long consonants to draw: one sheet for the three families, read back as overrides.

    python3 fonts/tools/long_sheet.py make            # fonts/hand/long-sheet.svg (+ .json)
    # draw in Inkscape, on the "pairs" layer
    python3 fonts/tools/long_sheet.py read            # fonts/svg/<family>/<letter>.long.svg
    fonts/build.sh

The sheet holds the plain pairs (t.long ...) in system order, six to a
section; each section is three rows, Serif / Sans / Mono, the same letter in
the same column. Each pair is one path labelled '<family> <letter> <glyph>'
on the "pairs" layer, 1 unit = 1 font unit, starting as the rough pair
build_font.py makes (the second letter set into the first); behind it, on
the locked "guides" layer, the same rough pair in grey, the baseline,
x-height, cap height, ascender, descender, and the pair's origin and advance.
The marked pairs (s_uni0326.long) follow from the drawn plain one.

read writes an override for each pair whose drawing changed; a pair left as
it was stays rough and does not ship. A shape drawn without a label belongs
to the cell its middle falls in. Needs the derived fonts (fonts/build.sh).
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import font_svg as FS
from svg_read import INKSCAPE, SVG_NS, INKSCAPE_NS, SODIPODI_NS, local, parse_transform, register_namespaces

ROOT = FS.ROOT
SHEET = os.path.join(ROOT, 'fonts', 'hand', 'long-sheet')
FAMS = ('serif', 'sans', 'mono')
ORDER = 'ptkbdgfvszmnlrcxhq'      # the review sheets' order, then h q
PER_ROW, COL, ROWH, LEFT, ORIGIN = 6, 1600, 1350, 700, 150   # pairs a section, column, row pitch, label margin, origin in a cell
GUIDE_COLORS = {'baseline': '#7a9', 'x-height': '#cfcfcf', 'cap height': '#cfcfcf',
                'ascender': '#e0e0e0', 'descender': '#e0e0e0'}


def pairs(font):
    have = set(font.getGlyphOrder())
    return [c for c in ORDER if f'{c}.long' in have]


def make():
    from fontTools.ttLib import TTFont
    fonts = {k: TTFont(FS.font_for(k)) for k in FAMS}
    letters = pairs(fonts['serif'])
    sections = [letters[i:i + PER_ROW] for i in range(0, len(letters), PER_ROW)]
    guides, edit, layout = [], [], {}
    y = 1200
    W = LEFT + COL * PER_ROW
    for sec in sections:
        guides.append(f'<text x="30" y="{y - 1000}" font-size="56" font-family="Helvetica" fill="#888">'
                      f'{" ".join(sec)}</text>')
        for k in FAMS:
            font = fonts[k]
            M = FS.metrics(font)
            for label, h in (('baseline', 0), ('x-height', M['xh']), ('cap height', M['cap']),
                             ('ascender', M['ascender']), ('descender', M['descender'])):
                guides.append(f'<line x1="{LEFT - 40}" x2="{W}" y1="{y - h}" y2="{y - h}" '
                              f'stroke="{GUIDE_COLORS[label]}" stroke-width="{3 if h == 0 else 2}"/>')
            guides.append(f'<text x="30" y="{y - 20}" font-size="44" font-family="Helvetica" fill="#888">{k.title()}</text>')
            for i, c in enumerate(sec):
                g = f'{c}.long'
                ox = LEFT + i * COL + ORIGIN
                adv = font['hmtx'][g][0]
                d = FS.path_d([ops for ops, _ in FS.contours(FS.glyph_rec(font, g))], (1, 0, 0, -1, ox, y))
                lab = f'{k} {c} {g}'
                guides.append(f'<path d="{d}" fill="#d8d8d8"/>')
                guides.append(f'<line x1="{ox}" x2="{ox}" y1="{y - 1000}" y2="{y + 300}" stroke="#f0c090" stroke-width="1.5"/>'
                              f'<line x1="{ox + adv}" x2="{ox + adv}" y1="{y - 1000}" y2="{y + 300}" '
                              f'stroke="#f0c090" stroke-width="1.5" stroke-dasharray="8 6"/>')
                guides.append(f'<text x="{ox}" y="{y + 260}" font-size="36" font-family="Helvetica" fill="#aaa">{lab}</text>')
                edit.append(f'<path id="{k}-{c}" inkscape:label="{lab}" d="{d}" fill="#111"/>')
                layout[lab] = {'family': k, 'glyph': g, 'origin': [ox, y], 'd': d,
                               'cell': [ox - ORIGIN, y - 1050, ox - ORIGIN + COL, y + ROWH - 1050]}
            y += ROWH
        y += 250
    H = y - 800
    svg = f'''<svg xmlns="{SVG_NS}" xmlns:inkscape="{INKSCAPE_NS}" xmlns:sodipodi="{SODIPODI_NS}" viewBox="0 0 {W} {H}">
  <title>Diafon long consonants</title>
  <!-- Draw on the "pairs" layer: one path per pair, labelled '<family> <letter> <glyph>'; 1 unit = 1 font unit,
       the pair's origin on the solid orange line, its advance on the dashed one. "guides" is locked.
       Then: python3 fonts/tools/long_sheet.py read && fonts/build.sh -->
  <sodipodi:namedview id="namedview" inkscape:current-layer="pairs" showguides="true" inkscape:pagecheckerboard="0"/>
  <rect width="{W}" height="{H}" fill="#fff"/>
  <g id="guides" inkscape:groupmode="layer" inkscape:label="guides" sodipodi:insensitive="true">
    {chr(10).join('    ' + x for x in guides).strip()}
  </g>
  <g id="pairs" inkscape:groupmode="layer" inkscape:label="pairs">
    {chr(10).join('    ' + x for x in edit).strip()}
  </g>
</svg>
'''
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    open(SHEET + '.svg', 'w', encoding='utf-8').write(svg)
    json.dump(layout, open(SHEET + '.json', 'w'), indent=1)
    print(f'{os.path.relpath(SHEET, ROOT)}.svg: {len(letters)} pairs x {len(FAMS)} families')


def _ctm(parents, el):
    from fontTools.misc.transform import Transform
    t = Transform()
    for p in parents + [el]:
        t = t.transform(parse_transform(p.get('transform')))
    return t


def _middle(el, t):
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.svgLib.path.parser import parse_path
    pen = BoundsPen(None)
    try:
        parse_path(FS.shape_d(el) or '', TransformPen(pen, t))
    except Exception:
        return None
    if not pen.bounds:
        return None
    x0, y0, x1, y1 = pen.bounds
    return (x0 + x1) / 2, (y0 + y1) / 2


def read(path=SHEET + '.svg'):
    from fontTools.ttLib import TTFont
    register_namespaces()
    layout = json.load(open(SHEET + '.json'))
    root = ET.parse(path).getroot()
    layer = next((g for g in root.iter() if local(g.tag) == 'g'
                  and (g.get('id') == 'pairs' or g.get(INKSCAPE + 'label') == 'pairs')), None)
    if layer is None:
        raise SystemExit(f'{path}: no "pairs" layer')
    cells = {}                                        # label -> [(element, its parents' transform)]
    def walk(el, parents):
        for ch in el:
            if local(ch.tag) == 'g':
                walk(ch, parents + [ch])
            elif local(ch.tag) in ('path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline'):
                lab = ch.get(INKSCAPE + 'label')
                if lab not in layout:
                    mid = _middle(ch, _ctm(parents, ch))
                    lab = next((k for k, v in layout.items() if mid and v['cell'][0] <= mid[0] < v['cell'][2]
                                and v['cell'][1] <= mid[1] < v['cell'][3]), None)
                if lab is None:
                    print(f'  a shape outside every cell, skipped ({ch.get("id")})')
                    continue
                cells.setdefault(lab, []).append((ch, parents))
    walk(layer, [layer])
    fonts, written = {}, 0
    for lab, items in cells.items():
        v = layout[lab]
        if len(items) == 1 and items[0][0].get('d') == v['d'] and not items[0][0].get('transform') \
                and not any(p.get('transform') for p in items[0][1]):
            continue                                  # left as it was: stays rough
        k, g = v['family'], v['glyph']
        font = fonts.setdefault(k, TTFont(FS.font_for(k)))
        M = FS.metrics(font)
        cx, cy = FS.canvas(M)[:2]
        ox, oy = v['origin']
        body = []
        for el, parents in items:
            t = _ctm(parents, el)                     # the shape's own transforms, then the cell to the canvas
            t = t.__class__(1, 0, 0, 1, cx - ox, cy - oy).transform(t)
            el = ET.fromstring(ET.tostring(el))
            el.attrib.pop('transform', None)
            el.set('transform', 'matrix(%g %g %g %g %g %g)' % tuple(t))
            el.set('fill', FS.INK)
            body.append('    ' + ET.tostring(el, encoding='unicode'))
        svg = FS.glyph_svg(font, g, k, M)
        i = svg.index('<g id="glyph"'); j = svg.index('</g>', i)
        svg = svg[:svg.index('>', i) + 1] + '\n' + '\n'.join(body) + '\n  ' + svg[j:]
        out = os.path.join(FS.SVG_ROOT, k, FS.file_stem(font, g) + '.svg')
        open(out, 'w', encoding='utf-8').write(svg)
        written += 1
        print(f'  {os.path.relpath(out, ROOT)}')
    print(f'{written} drawn pairs written' + ('' if written else ' (nothing changed on the sheet)'))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'make':
        make()
    elif cmd == 'read':
        read(*sys.argv[2:3])
    else:
        print(__doc__)
