#!/usr/bin/env python3
"""Generate fonts/hand/frame.svg and frame.json: the digital drawing frame.

The frame has the structure of the fonts page: bases across, derivations
down, one cell per potential glyph (read from docs/fonts-data.js, so the two
never drift apart), followed by the extras a font needs anyway (the other
letters, capitals, digits, punctuation). Every cell carries the writing
guides (ascender, cap height, x-height, baseline, descender), a small pale
reference of the target in the Diafon font, its input form and codepoints.

Open the SVG in any vector editor (Inkscape, Illustrator, Affinity, an iPad
drawing app that exports SVG), draw each glyph in its cell in black, save,
and run fonts/tools/hand_read.py on the saved file: it finds the ink by
colour and position, so the frame's own layers may be flattened, moved or
re-scaled by the editor without harm (the four corner squares register it).

    python3 fonts/tools/hand_frame.py [--ghost]

--ghost adds a full-size pale copy of the target inside each cell to write
over; the default leaves the cell clear so the hand stays the writer's own.

frame.json is the manifest the reader uses: cell boxes, baselines, guides
and the reference metrics. Regenerate both together, never edit by hand.
"""
import json
import os
import re
import sys
import unicodedata

import uharfbuzz as hb
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = os.path.join(ROOT, 'fonts', 'DiafonSerif-Regular.ttf')
DATA = os.path.join(ROOT, 'docs', 'fonts-data.js')
OUT_SVG = os.path.join(ROOT, 'fonts', 'hand', 'frame.svg')
OUT_JSON = os.path.join(ROOT, 'fonts', 'hand', 'frame.json')

# geometry: frame units; the em is 100 units (S frame units per font unit)
S = 0.1
CELL_TOP, CELL_BOT = 1000, -520       # the drawing box, in font units
CELL_W = 140                          # frame units (1.4 em)
LABEL_H = 36                          # the label band above the drawing box
DRAW_H = (CELL_TOP - CELL_BOT) * S
CELL_H = LABEL_H + DRAW_H
HEAD_W = 190                          # the row-header column
PAD = 48
FID = 16                              # fiducial square
TITLE_H, HDR_H, ROW_GAP, SECTION_GAP = 40, 22, 14, 56
COLS = 15
MINI = 0.3                            # reference glyph scale in the label band

# the frame draws only in pale colours; the reader treats anything darker
# than mid-grey as ink, so these must stay light (fiducials excepted)
C = {'border': '#b9c0cc', 'guide': '#cfd5e0', 'guide2': '#dfe3ea',
     'label': '#a3aab8', 'code': '#b48a8a', 'ref': '#c5cbd8', 'ghost': '#e8ebf1',
     'title': '#a3aab8', 'fid': '#000000'}

EXTRAS = [
    ('capitals', list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')),
    ('digits', list('0123456789')),
    ('punctuation', list('.,;:!?\'"()[]/-–—·')),
]


def matrix():
    src = open(DATA, encoding='utf-8').read()
    return json.loads(re.search(r'const MATRIX = (.*);', src).group(1))


class Ref:
    """The reference font: shaping (harfbuzz, what browsers do) and outlines."""

    def __init__(self, path=FONT):
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt['head'].unitsPerEm
        self.asc, self.desc = self.tt['hhea'].ascent, self.tt['hhea'].descent
        self.xh = self.tt['OS/2'].sxHeight
        self.cap = self.tt['OS/2'].sCapHeight
        face = hb.Face(hb.Blob.from_file_path(path))
        self.hb = hb.Font(face)

    def shape(self, text):
        """[(glyph name, x, y)], total advance; font units."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf)
        x, out = 0, []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((self.order[info.codepoint], x + pos.x_offset, pos.y_offset))
            x += pos.x_advance
        return out, x

    def draw(self, text, pen):
        """Draw the shaped run into a pen (font units, y up)."""
        run, adv = self.shape(text)
        for name, dx, dy in run:
            self.gs[name].draw(TransformPen(pen, Transform(1, 0, 0, 1, dx, dy)))
        return adv

    def metrics(self, text):
        """advance and ink bbox (xmin, ymin, xmax, ymax) of the shaped run."""
        rec = DecomposingRecordingPen(self.gs)
        adv = self.draw(text, rec)
        pts = [p for op, args in rec.value for p in args if isinstance(p, tuple)]
        if not pts:
            return adv, None
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return adv, [min(xs), min(ys), max(xs), max(ys)]

    def svg_d(self, text, k, x0, ybase):
        """Path data of the run placed in frame space: scale k·S, origin at
        (x0, ybase), y flipped."""
        pen = SVGPathPen(self.gs, ntos=lambda v: ('%.2f' % v).rstrip('0').rstrip('.'))
        self.draw(text, TransformPen(pen, Transform(k * S, 0, 0, -k * S, x0, ybase)))
        return pen.getCommands()

    def glyph_name(self, text):
        """The font glyph a whole cell drawing stands for: the NFC first
        character's glyph, then _uniXXXX per following mark (the baked
        letter+mark names build_font.py uses)."""
        s = unicodedata.normalize('NFC', text)
        head = self.cmap.get(ord(s[0])) or 'uni%04X' % ord(s[0])
        return head + ''.join('_uni%04X' % ord(c) for c in s[1:])


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def cells_of(m, ref):
    """Every cell of the frame in reading order: (section, row header,
    list of (col, item)) where item = dict(form, text, cps, langs) or None."""
    out = []
    for key, title in (('cons', 'Consonants'), ('vows', 'Vowels')):
        sec = m[key]
        rows = []
        for row in sec['rows']:
            head = (row['ops'], row['label'])
            items = []
            for cell in row['cells']:
                items.append(None if not cell else {
                    'form': cell['f'], 'text': cell['g'], 'cps': cell['cps'],
                    'langs': cell['langs'], 'kind': 'matrix'})
            rows.append((head, items))
        out.append((title, sec['bases'], rows))
    seen = {unicodedata.normalize('NFD', c['g'])[0]
            for sec in m.values() for row in sec['rows'] for c in row['cells'] if c}
    others = [ch for ch in 'abcdefghijklmnopqrstuvwxyz' if ch not in seen]
    groups = ([('other letters', others)] if others else []) + EXTRAS
    rows = []
    for label, chars in groups:
        for i in range(0, len(chars), COLS):
            chunk = chars[i:i + COLS]
            head = ('', label if i == 0 else '')
            items = [{'form': ch, 'text': ch, 'cps': '%04X' % ord(ch), 'langs': None,
                      'kind': 'extra'} for ch in chunk]
            items += [None] * (COLS - len(items))
            rows.append((head, items))
    out.append(('Extras', [''] * COLS, rows))
    return out


def guides(ref, m):
    """The five writing guides in font units, read from the reference."""
    _, dbox = ref.metrics('d')
    depth = 0
    for sec in m.values():
        for row in sec['rows']:
            for cell in row['cells']:
                if cell:
                    _, box = ref.metrics(cell['g'])
                    if box:
                        depth = min(depth, box[1])
    return {'ascender': int(dbox[3]), 'cap': int(ref.cap), 'xheight': int(ref.xh),
            'baseline': 0, 'descender': int(depth)}


def cell_svg(ref, item, x, y, G, ghost, cid):
    """One cell: border, guides, label band, reference; returns (svg, manifest)."""
    ybase = y + LABEL_H + CELL_TOP * S
    parts = [f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H:.1f}" fill="none" '
             f'stroke="{C["border"]}" stroke-width="0.6"/>',
             f'<line x1="{x}" x2="{x + CELL_W}" y1="{y + LABEL_H}" y2="{y + LABEL_H}" '
             f'stroke="{C["border"]}" stroke-width="0.4"/>']
    for gname, dash, col in (('ascender', '2 2', 'guide'), ('cap', '1 3', 'guide2'),
                             ('xheight', '4 2', 'guide'), ('baseline', '', 'guide'),
                             ('descender', '2 2', 'guide')):
        gy = ybase - G[gname] * S
        w = 0.9 if gname == 'baseline' else 0.5
        parts.append(f'<line x1="{x}" x2="{x + CELL_W}" y1="{gy:.1f}" y2="{gy:.1f}" '
                     f'stroke="{C[col]}" stroke-width="{w}"'
                     + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')
    text = item['text']
    adv, box = ref.metrics(text)
    # the label band: form code left, mini reference centred, codepoints right
    parts.append(f'<text x="{x + 5}" y="{y + 12}" font-family="Menlo,Consolas,monospace" '
                 f'font-size="8.5" fill="{C["code"]}">{esc(item["form"])}</text>')
    parts.append(f'<text x="{x + CELL_W - 5}" y="{y + 12}" text-anchor="end" '
                 f'font-family="Menlo,Consolas,monospace" font-size="5.5" '
                 f'fill="{C["label"]}">{item["cps"]}</text>')
    if item['kind'] == 'matrix':
        n = item['langs']
        tag = ('reserve' if not n else f'{n} lang' + ('s' if n > 1 else ''))
        parts.append(f'<text x="{x + 5}" y="{y + LABEL_H - 5}" font-family="Menlo,Consolas,monospace" '
                     f'font-size="5.5" fill="{C["label"]}">{tag}</text>')
    mx = x + CELL_W * 0.62 - adv * MINI * S / 2
    parts.append(f'<path fill="{C["ref"]}" d="{ref.svg_d(text, MINI, mx, y + LABEL_H - 9)}"/>')
    if ghost:
        gx = x + (CELL_W - adv * S) / 2
        parts.append(f'<path fill="{C["ghost"]}" d="{ref.svg_d(text, 1, gx, ybase)}"/>')
    man = {'id': cid, 'kind': item['kind'], 'form': item['form'], 'text': text,
           'cps': item['cps'], 'langs': item['langs'], 'name': ref.glyph_name(text),
           'box': [x, round(y + LABEL_H, 2), x + CELL_W, round(y + CELL_H, 2)],
           'baseline': round(ybase, 2),
           'ref': {'advance': adv, 'bbox': box and [round(v, 1) for v in box]}}
    return f'<g id="{cid}">' + ''.join(parts) + '</g>', man


def build(ghost=False):
    ref = Ref()
    m = matrix()
    G = guides(ref, m)
    sections = cells_of(m, ref)
    W = PAD * 2 + HEAD_W + COLS * CELL_W
    body, manifest = [], []
    y = PAD + 8
    for title, bases, rows in sections:
        body.append(f'<text x="{PAD + HEAD_W}" y="{y + 26}" font-family="Georgia,serif" '
                    f'font-size="20" fill="{C["title"]}">{esc(title)}</text>')
        y += TITLE_H
        for i, b in enumerate(bases):
            if b:
                body.append(f'<text x="{PAD + HEAD_W + i * CELL_W + CELL_W / 2}" y="{y + 15}" '
                            f'text-anchor="middle" font-family="Georgia,serif" font-size="13" '
                            f'fill="{C["label"]}">{esc(b)}</text>')
        y += HDR_H
        for (ops, label), items in rows:
            head = (f'<tspan font-family="Menlo,Consolas,monospace" font-size="8" '
                    f'fill="{C["code"]}">+{esc(ops)}</tspan> ' if ops else '')
            body.append(f'<text x="{PAD}" y="{y + LABEL_H + 20}" font-family="Georgia,serif" '
                        f'font-size="10" fill="{C["label"]}">{head}{esc(label)}</text>')
            for i, item in enumerate(items):
                if not item:
                    continue
                cid = ('cell-' + item['form'] if item['kind'] == 'matrix'
                       else 'cell-x-%04X' % ord(item['text']))
                svg, man = cell_svg(ref, item, PAD + HEAD_W + i * CELL_W, y, G, ghost, cid)
                body.append(svg)
                manifest.append(man)
            y += CELL_H + ROW_GAP
        y += SECTION_GAP
    H = y + PAD
    fids = {'tl': (PAD / 2, PAD / 2), 'tr': (W - PAD / 2 - FID, PAD / 2),
            'bl': (PAD / 2, H - PAD / 2 - FID), 'br': (W - PAD / 2 - FID, H - PAD / 2 - FID)}
    fid_svg = ''.join(f'<rect id="fid-{k}" x="{x}" y="{y}" width="{FID}" height="{FID}" '
                      f'fill="{C["fid"]}"/>' for k, (x, y) in fids.items())
    note = ('Diafon hand frame: draw each glyph in its cell, in black; the pale frame is '
            'reference. Read back with fonts/tools/hand_read.py.')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
           f'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" '
           f'viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" data-diafon-frame="1">\n'
           f'<title>Diafon hand frame</title>\n<desc>{esc(note)}</desc>\n'
           f'<sodipodi:namedview id="namedview" inkscape:current-layer="ink" '
           f'inkscape:document-units="px"/>\n'
           f'<g id="frame" inkscape:groupmode="layer" inkscape:label="frame (reference, locked)" '
           f'sodipodi:insensitive="true">\n'
           f'<rect x="0" y="0" width="{W}" height="{H:.0f}" fill="#ffffff"/>\n'
           + fid_svg + '\n' + '\n'.join(body) +
           f'\n</g>\n<g id="ink" inkscape:groupmode="layer" inkscape:label="ink (draw here)">\n</g>\n</svg>\n')
    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    open(OUT_SVG, 'w', encoding='utf-8').write(svg)
    data = {'version': 1, 'font': os.path.relpath(FONT, ROOT), 'units_per_em': ref.upm,
            'scale': S, 'size': [W, round(H)], 'fiducial_size': FID,
            'fiducials': {k: [v[0], v[1]] for k, v in fids.items()},
            'guides': G, 'cell': {'top': CELL_TOP, 'bottom': CELL_BOT,
                                  'width': CELL_W, 'label_h': LABEL_H},
            'ghost': ghost, 'cells': manifest}
    json.dump(data, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    n_m = sum(c['kind'] == 'matrix' for c in manifest)
    print(f'{os.path.relpath(OUT_SVG, ROOT)}: {W}x{H:.0f}, {len(manifest)} cells '
          f'({n_m} matrix + {len(manifest) - n_m} extras)' + (', ghosted' if ghost else ''))
    print(f'{os.path.relpath(OUT_JSON, ROOT)}: guides {G}')


if __name__ == '__main__':
    build(ghost='--ghost' in sys.argv[1:])
