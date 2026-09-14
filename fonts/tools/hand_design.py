#!/usr/bin/env python3
"""Describe glyphs in text, see them as SVG, then make the glyph files.

    python3 fonts/tools/hand_design.py            # fonts/hand/design.yaml -> design.svg
    python3 fonts/tools/hand_design.py --build    # ... and glyphs/<name>.svg for each
    python3 fonts/tools/hand_design.py --outline  # proof also shows the traced outline
    python3 fonts/tools/hand_design.py --clean    # proof without the point markers
    python3 fonts/tools/hand_design.py other.yaml # another description file

THE DESCRIPTION (fonts/hand/design.yaml). Font units, 1000 to the em, y up,
baseline 0; x is where the glyph sits (the left side bearing is yours).
Heights may be named: base xh cap asc desc (read from the Diafon font),
with arithmetic and no spaces: 600,asc-40. A point is x,y.

    pen: {width: 70, cap: round}          # the default pen (cap: round|flat)
    glyphs:
      t:                                  # a font glyph name (font_svg.py names)
        advance: 480                      # optional; else the ink's right edge
                                          #   plus the reference's side bearing
        pen: {width: 80}                  # per glyph
        strokes:                          # a stroke: points; space = straight
          - 600,asc-40 600,60 ~ 700,0 ~ 800,60     #   ~ = smooth curve through
          - w=60 480,xh 760,xh            # w=… cap=… tokens override the pen
        fills:                            # filled shapes, always closed; a hole
          - 500,0 900,0 900,100 500,100   #   is a fill drawn the other way round
        dots:                             # x,y radius
          - 620,-140 45
      o:
        strokes:
          - ~ 700,xh ~ 900,270 ~ 700,0 ~ 500,270 ~close    # a closed smooth loop
      uni0324: {dots: [620,-140 45, 780,-140 45]}
      t_uni0324:
        use: [t, uni0324]                 # compose from other glyphs; at: [dx, dy]
      t_uni0316:
        use: [t, {glyph: uni0326, flip: x, at: [-60, 0], scale: 1}]  # flip x|y|xy
                                          #   about the part's own centre

THE PROOF (design.svg) shows every glyph on the guides over its pale
reference in the Diafon font (when the name is one of its glyphs, or a
frame cell's), the description in black, and its points with coordinates.
THE BUILD traces each glyph through the same rasterise-and-trace pipeline as
the drawn frame (strokes with their width, fills, dots; overlaps merge) into
fonts/hand/glyphs/<name>.svg in the font_svg.py format. Files of glyphs no
longer described are removed (only this tool's own).
"""
import json
import math
import os
import re
import sys

import yaml
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_frame as HF
import hand_read as HR

ROOT = HF.ROOT
SPEC = os.path.join(ROOT, 'fonts', 'hand', 'design.yaml')
PROOF = os.path.join(ROOT, 'fonts', 'hand', 'design.svg')
OUT_DIR = HR.OUT_DIR
NOTE = 'described in fonts/hand/design.yaml,\n       built by fonts/tools/hand_design.py'

K = 0.25                      # proof scale: frame px per font unit (em = 250)
COLS = 4
CW = int(1.6 * 1000 * K)      # cell width
TOP, BOT = HF.CELL_TOP, HF.CELL_BOT
LABEL_H = 34
DH = (TOP - BOT) * K
PAD, GAP = 30, 16
INSET = int(250 * K)          # the design's x = 0 sits this far into the cell
C = dict(HF.C, ink='#111', point='#0e7c86', outline='#c04646', warn='#c04646')


class SpecError(Exception):
    pass


# ------------------------------------------------------------------ parsing

class Design:
    def __init__(self, path, ref, guides):
        self.file = path
        self.ref = ref
        self.names = {'base': 0, 'xh': guides['xheight'], 'cap': guides['cap'],
                      'asc': guides['ascender'], 'desc': guides['descender']}
        doc = yaml.safe_load(open(path, encoding='utf-8')) or {}
        self.pen = dict({'width': 70, 'cap': 'round'}, **(doc.get('pen') or {}))
        self.glyphs = doc.get('glyphs') or {}
        if not isinstance(self.glyphs, dict):
            raise SpecError('glyphs: must be a mapping of glyph name -> description')
        self._cache = {}

    def num(self, s, where):
        """A coordinate: a number or an expression over the named heights."""
        if isinstance(s, (int, float)):
            return float(s)
        expr = s.strip()
        for name, val in self.names.items():
            expr = re.sub(r'\b%s\b' % name, str(val), expr)
        if not re.fullmatch(r'[\d\s+\-*/().]+', expr):
            raise SpecError(f'{where}: bad coordinate {s!r}')
        try:
            return float(eval(expr, {'__builtins__': {}}, {}))
        except Exception:
            raise SpecError(f'{where}: bad coordinate {s!r}')

    def point(self, tok, where):
        if ',' not in tok:
            raise SpecError(f'{where}: expected a point x,y, got {tok!r}')
        x, y = tok.split(',', 1)
        return (self.num(x, where), self.num(y, where))

    def path(self, text, where, closed=False):
        """A stroke/fill string -> (RecordingPen, points, width, cap)."""
        toks = str(text).split()
        width, cap = None, None
        pts, smooth = [], []       # smooth[i]: the segment INTO point i is a curve
        pending = False
        close, close_smooth = closed, False
        for t in toks:
            if t.startswith('w='):
                width = self.num(t[2:], where)
            elif t.startswith('cap='):
                cap = t[4:]
            elif t == '~':
                pending = True
            elif t in ('close', '~close'):
                close, close_smooth = True, t == '~close' or pending
                pending = False
            else:
                pts.append(self.point(t, where))
                smooth.append(pending)
                pending = False
        if not pts:
            raise SpecError(f'{where}: no points')
        if pending and not close:        # a trailing ~ on an open stroke
            close, close_smooth = False, False
        if close and len(pts) < 3 and not closed:
            raise SpecError(f'{where}: a closed stroke needs three points')
        if closed and len(pts) < 3:
            raise SpecError(f'{where}: a fill needs three points')
        rec = RecordingPen()
        n = len(pts)
        rec.moveTo(pts[0])

        def nb(i):        # neighbour with wrapping for closed paths, clamping otherwise
            if close:
                return pts[i % n]
            return pts[max(0, min(n - 1, i))]

        def curve(i0, i1):      # cubic through pts[i0] -> pts[i1], Catmull-Rom tangents
            p0, p1 = nb(i0), nb(i1)
            pm, pn = nb(i0 - 1), nb(i1 + 1)
            c1 = (p0[0] + (p1[0] - pm[0]) / 6, p0[1] + (p1[1] - pm[1]) / 6)
            c2 = (p1[0] - (pn[0] - p0[0]) / 6, p1[1] - (pn[1] - p0[1]) / 6)
            rec.curveTo(c1, c2, p1)

        for i in range(1, n):
            if smooth[i]:
                curve(i - 1, i)
            else:
                rec.lineTo(pts[i])
        if close:
            if close_smooth or (closed and smooth and all(smooth[1:]) and smooth[0]):
                curve(n - 1, n)
            rec.closePath()
        else:
            rec.endPath()
        return rec, pts, width, cap

    def elements(self, name, chain=()):
        """Resolve a glyph to drawing elements in font units:
        {'kind': stroke|fill|dot, 'rec', 'width', 'cap', 'points', 'own'}."""
        if name in self._cache:
            return self._cache[name]
        if name in chain:
            raise SpecError(f'{name}: uses itself ({" -> ".join(chain + (name,))})')
        spec = self.glyphs.get(name)
        if spec is None:
            raise SpecError(f'{" -> ".join(chain + (name,))}: no such glyph in the description')
        if not isinstance(spec, dict):
            raise SpecError(f'{name}: must be a mapping (strokes/fills/dots/use)')
        pen = dict(self.pen, **(spec.get('pen') or {}))
        els = []
        for i, s in enumerate(spec.get('strokes') or []):
            rec, pts, w, cap = self.path(s, f'{name} stroke {i + 1}')
            els.append({'kind': 'stroke', 'rec': rec, 'points': pts, 'own': True,
                        'width': w if w is not None else float(pen['width']),
                        'cap': cap or pen['cap']})
        fills = spec.get('fills') or []
        if fills:
            allrec, allpts = RecordingPen(), []
            for i, s in enumerate(fills):
                rec, pts, _, _ = self.path(s, f'{name} fill {i + 1}', closed=True)
                rec.replay(allrec)
                allpts += pts
            els.append({'kind': 'fill', 'rec': allrec, 'points': allpts, 'own': True})
        for i, d in enumerate(spec.get('dots') or []):
            where = f'{name} dot {i + 1}'
            if isinstance(d, (list, tuple)):
                parts = [str(v) for v in d]
            else:
                parts = str(d).split()
            if len(parts) == 2:
                (x, y), r = self.point(parts[0], where), self.num(parts[1], where)
            elif len(parts) == 3:
                x, y, r = (self.num(v, where) for v in parts)
            else:
                raise SpecError(f'{where}: expected x,y radius')
            els.append({'kind': 'dot', 'rec': circle(x, y, r), 'points': [(x, y)],
                        'own': True, 'r': r})
        for u in spec.get('use') or []:
            if isinstance(u, str):
                u = {'glyph': u}
            if not isinstance(u, dict) or 'glyph' not in u:
                raise SpecError(f'{name}: use entries are names or {{glyph: …}}')
            parts = self.elements(u['glyph'], chain + (name,))
            t = Transform()
            sc = float(u.get('scale', 1))
            flip = str(u.get('flip', '') or '')
            if flip or sc != 1:
                box = bbox(parts)
                cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                sx = -sc if 'x' in flip else sc
                sy = -sc if 'y' in flip else sc
                t = Transform(sx, 0, 0, sy, cx - sx * cx, cy - sy * cy)
            if 'at' in u:
                at = u['at']
                where = f'{name} use {u["glyph"]}'
                if isinstance(at, (list, tuple)) and len(at) == 2:
                    dx, dy = self.num(at[0], where), self.num(at[1], where)
                else:
                    dx, dy = self.point(str(at).replace(' ', ''), where)
                t = Transform(1, 0, 0, 1, dx, dy).transform(t)
            for e in parts:
                rec = RecordingPen()
                e['rec'].replay(TransformPen(rec, t))
                ne = dict(e, rec=rec, own=False,
                          points=[t.transformPoint(p) for p in e['points']])
                if 'width' in ne:
                    ne['width'] = e['width'] * sc
                els.append(ne)
        if not els:
            raise SpecError(f'{name}: nothing to draw (strokes, fills, dots or use)')
        self._cache[name] = els
        return els


def circle(x, y, r):
    k = 0.5523 * r
    rec = RecordingPen()
    rec.moveTo((x + r, y))
    rec.curveTo((x + r, y + k), (x + k, y + r), (x, y + r))
    rec.curveTo((x - k, y + r), (x - r, y + k), (x - r, y))
    rec.curveTo((x - r, y - k), (x - k, y - r), (x, y - r))
    rec.curveTo((x + k, y - r), (x + r, y - k), (x + r, y))
    rec.closePath()
    return rec


def bbox(els):
    xs, ys = [], []
    for e in els:
        for op, args in e['rec'].value:
            for p in args:
                if isinstance(p, tuple):
                    pad = e.get('width', 0) / 2
                    xs += [p[0] - pad, p[0] + pad]
                    ys += [p[1] - pad, p[1] + pad]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else [0, 0, 0, 0]


# ------------------------------------------------------------------ tracing

def shapes_of(els):
    out = []
    for e in els:
        if e['kind'] == 'stroke':
            out.append(HR.Shape(e['rec'], e['width'], False, True, 'nonzero', '', False))
        else:
            out.append(HR.Shape(e['rec'], 0, True, False, 'nonzero', '', False))
    return out


def trace(els):
    """Elements -> traced outline (RecordingPen in font units)."""
    box = bbox(els)
    m = 40
    W = int(math.ceil(box[2] - box[0] + 2 * m))
    H = int(math.ceil(box[3] - box[1] + 2 * m))
    to_px = Transform(1, 0, 0, -1, m - box[0], box[3] + m)
    mask = HR.rasterise(shapes_of(els), to_px, W, H)
    if not mask.any():
        return None
    return HR.trace(mask, to_px.inverse())


# ------------------------------------------------------------------ proof

def ref_reference(ref, name, texts):
    """(text label, RecordingPen of the pale reference) for a glyph name."""
    rec = RecordingPen()
    if name in ref.gs:
        ref.gs[name].draw(rec)
        cp = {v: k for k, v in ref.cmap.items()}.get(name)
        return (chr(cp) if cp else texts.get(name, '')), rec
    if name in texts:
        ref.draw(texts[name], rec)
        return texts[name], rec
    return '', None


def cell(design, name, x, y, ref, texts, guides, show_points, outline):
    ybase = y + LABEL_H + TOP * K
    t = Transform(K, 0, 0, -K, x + INSET, ybase)
    parts = [f'<rect x="{x}" y="{y}" width="{CW}" height="{LABEL_H + DH:.0f}" fill="none" '
             f'stroke="{C["border"]}" stroke-width="0.8"/>']
    for g, dash, col in (('ascender', '2 2', 'guide'), ('cap', '1 3', 'guide2'),
                         ('xheight', '4 2', 'guide'), ('baseline', '', 'guide'),
                         ('descender', '2 2', 'guide')):
        gy = ybase - guides[g] * K
        parts.append(f'<line x1="{x}" x2="{x + CW}" y1="{gy:.1f}" y2="{gy:.1f}" '
                     f'stroke="{C[col]}" stroke-width="{1.2 if g == "baseline" else 0.6}"'
                     + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')
    # the y axis: x = 0 of the design
    parts.append(f'<line x1="{x + INSET}" x2="{x + INSET}" y1="{y + LABEL_H}" y2="{y + LABEL_H + DH:.0f}" '
                 f'stroke="{C["guide"]}" stroke-width="0.6" stroke-dasharray="1 3"/>')
    text, rrec = ref_reference(ref, name, texts)
    parts.append(f'<text x="{x + 8}" y="{y + 22}" font-family="Menlo,Consolas,monospace" '
                 f'font-size="13" fill="{C["code"]}">{HF.esc(name)}</text>')
    if text:
        parts.append(f'<text x="{x + CW - 8}" y="{y + 24}" text-anchor="end" font-family="Georgia,serif" '
                     f'font-size="16" fill="{C["label"]}">{HF.esc(text)}</text>')
    try:
        els = design.elements(name)
    except SpecError as e:
        parts.append(f'<text x="{x + 8}" y="{ybase - 200 * K}" font-family="Menlo,Consolas,monospace" '
                     f'font-size="10" fill="{C["warn"]}">{HF.esc(str(e))}</text>')
        return ''.join(parts), str(e)
    if rrec is not None:
        parts.append(f'<path fill="{C["ref"]}" opacity="0.6" d="{HR.rec_d(HR.TransformedRec(rrec, t), 2)}"/>')
    if outline:
        tr = trace(els)
        if tr is not None:
            parts.append(f'<path fill="none" stroke="{C["outline"]}" stroke-width="1" '
                         f'd="{HR.rec_d(HR.TransformedRec(tr, t), 2)}"/>')
    ink = C['ink'] if not outline else '#11111166'
    for e in els:
        d = HR.rec_d(HR.TransformedRec(e['rec'], t), 2)
        if e['kind'] == 'stroke':
            cap = 'butt' if e['cap'] == 'flat' else 'round'
            parts.append(f'<path fill="none" stroke="{ink}" stroke-width="{e["width"] * K:.2f}" '
                         f'stroke-linecap="{cap}" stroke-linejoin="round" d="{d}"/>')
        else:
            parts.append(f'<path fill="{ink}" d="{d}"/>')
    if show_points:
        for e in els:
            if not e['own']:
                continue
            for px, py in e['points']:
                X, Y = t.transformPoint((px, py))
                parts.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="2.2" fill="{C["point"]}"/>')
                parts.append(f'<text x="{X + 4:.1f}" y="{Y - 3:.1f}" font-family="Menlo,Consolas,monospace" '
                             f'font-size="7" fill="{C["point"]}">{px:g},{py:g}</text>')
    box = bbox(els)
    parts.append(f'<text x="{x + 8}" y="{y + LABEL_H + DH - 8:.0f}" font-family="Menlo,Consolas,monospace" '
                 f'font-size="8" fill="{C["label"]}">ink {box[0]:.0f}..{box[2]:.0f} × {box[1]:.0f}..{box[3]:.0f}'
                 f' · advance {advance_of(design, name, els, ref, texts)}</text>')
    return ''.join(parts), None


def advance_of(design, name, els, ref, texts):
    spec = design.glyphs.get(name) or {}
    if isinstance(spec, dict) and spec.get('advance') is not None:
        return int(spec['advance'])
    box = bbox(els)
    text, rrec = ref_reference(ref, name, texts)
    rsb = 60
    if rrec is not None:
        pts = [p for op, args in rrec.value for p in args if isinstance(p, tuple)]
        adv = ref.hb.get_glyph_h_advance(ref.hb.get_glyph_from_name(name)) if name in ref.gs \
            else ref.metrics(text)[0]
        if adv == 0:
            return 0                 # a bare mark: zero advance, drawn around x = 0
        if pts:
            rsb = adv - max(p[0] for p in pts)
    return max(0, int(round(box[2] + rsb)))


def proof(design, ref, texts, guides, show_points=True, outline=False):
    names = list(design.glyphs)
    rows = math.ceil(len(names) / COLS) or 1
    W = PAD * 2 + COLS * CW + (COLS - 1) * GAP
    H = PAD * 2 + rows * (LABEL_H + DH) + (rows - 1) * GAP
    body, errors = [], []
    for i, name in enumerate(names):
        x = PAD + (i % COLS) * (CW + GAP)
        y = PAD + (i // COLS) * (LABEL_H + DH + GAP)
        svg, err = cell(design, name, x, y, ref, texts, guides, show_points, outline)
        body.append(svg)
        if err:
            errors.append(err)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" '
           f'width="{W}" height="{H:.0f}">\n<title>Diafon glyph designs</title>\n'
           f'<rect width="{W}" height="{H:.0f}" fill="#ffffff"/>\n' + '\n'.join(body) + '\n</svg>\n')
    return svg, errors


# ------------------------------------------------------------------ build

def build(design, ref, texts, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for name in design.glyphs:
        els = design.elements(name)
        tr = trace(els)
        if tr is None:
            print(f'  {name}: nothing traceable')
            continue
        text, _ = ref_reference(ref, name, texts)
        cellinfo = {'form': name, 'text': text or name}
        adv = advance_of(design, name, els, ref, texts)
        stem = name if name == name.lower() else 'uni%04X' % ord(text) if len(text) == 1 else name + '_'
        path = os.path.join(out_dir, stem + '.svg')
        open(path, 'w', encoding='utf-8').write(HR.glyph_svg(name, tr, cellinfo, adv, ref, NOTE))
        written.append(path)
        contours = sum(1 for op, _ in tr.value if op == 'moveTo')
        print(f'  {name:18s} -> {os.path.relpath(path, ROOT)}  {contours} contour(s), advance {adv}')
    for fn in sorted(os.listdir(out_dir)):
        full = os.path.join(out_dir, fn)
        if full in written or not fn.endswith('.svg'):
            continue
        head = open(full, encoding='utf-8', errors='replace').read(600)
        if 'hand_design.py' in head:
            os.remove(full)
            print(f'  removed {os.path.relpath(full, ROOT)} (no longer described)')
    return written


def main(argv):
    spec, do_build, outline, points = SPEC, False, False, True
    out_dir, proof_path = OUT_DIR, PROOF
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == '--build':
            do_build = True
        elif a == '--outline':
            outline = True
        elif a == '--clean':
            points = False
        elif a == '--out':
            out_dir = args.pop(0)
        elif a == '--proof':
            proof_path = args.pop(0)
        else:
            spec = a
    ref = HF.Ref()
    texts, guides = {}, None
    if os.path.exists(HF.OUT_JSON):
        man = json.load(open(HF.OUT_JSON, encoding='utf-8'))
        texts = {c['name']: c['text'] for c in man['cells']}
        guides = man['guides']
    if guides is None:
        guides = HF.guides(ref, HF.matrix())
    try:
        design = Design(spec, ref, guides)
    except (SpecError, yaml.YAMLError) as e:
        print(f'{os.path.relpath(spec, ROOT)}: {e}')
        return 1
    svg, errors = proof(design, ref, texts, guides, points, outline)
    open(proof_path, 'w', encoding='utf-8').write(svg)
    print(f'{os.path.relpath(proof_path, ROOT)}: {len(design.glyphs)} glyphs'
          + (f', {len(errors)} with errors' if errors else ''))
    for e in errors:
        print(f'  ! {e}')
    if do_build:
        if errors:
            print('not building: fix the errors first')
            return 1
        build(design, ref, texts, out_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
