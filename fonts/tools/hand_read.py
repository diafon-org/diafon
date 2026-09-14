#!/usr/bin/env python3
"""Read a drawn copy of the hand frame back: find the ink, cut it per cell,
trace it to font outlines, analyse it against the reference, and write

    fonts/hand/glyphs/<glyph name>.svg   one file per drawn cell, in the
                                         fonts/tools/font_svg.py format
                                         (em box, guides, g#glyph)
    fonts/hand/review.svg                the frame again, with every traced
                                         glyph in black over its pale
                                         reference and the analysis flags
    fonts/hand/analysis.json             the machine-readable report

    python3 fonts/tools/hand_read.py [drawn.svg] [--manifest frame.json]
        [--out fonts/hand/glyphs] [--review review.svg] [--report analysis.json]
        [--keep-stale]

Glyph files from cells no longer drawn are removed from --out on each run
(only files this tool wrote, recognised by their data-form attribute);
--keep-stale leaves them.

How the ink is found. The frame draws itself only in pale colours; any
shape whose fill or stroke is darker than mid-grey is ink (text is never
ink). Editors may flatten layers, drop ids, add transforms or change the
viewBox: every shape is taken with its full cumulative transform, and the
four black corner squares register the drawing back onto the frame. Ink
is assigned to the cell that contains the centre of its bounding box.

How a glyph is made. Everything drawn in a cell, strokes (round caps and
joins, the pen's width honoured) and filled shapes alike, is rasterised at
one pixel per font unit and traced with potrace into one clean outline:
overlaps merge, and the result is a filled glyph, never a stroke. The
horizontal origin is the reference letter's left side bearing before the
ink; the advance is that ink width plus the reference's side bearings.
The analysis compares the ink against the reference: connected pieces
(a t̤ has three, a ș one: the anchor attaches), baseline and top
alignment, width, and whether the ink stays inside the cell.
"""
import json
import math
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

import cv2
import numpy as np
import potrace
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path.parser import parse_path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_frame as HF

ROOT = HF.ROOT
DEFAULT_IN = os.path.join(ROOT, 'fonts', 'hand', 'drawn.svg')
OUT_DIR = os.path.join(ROOT, 'fonts', 'hand', 'glyphs')
REVIEW = os.path.join(ROOT, 'fonts', 'hand', 'review.svg')
REPORT = os.path.join(ROOT, 'fonts', 'hand', 'analysis.json')

SVG = '{http://www.w3.org/2000/svg}'
XLINK = '{http://www.w3.org/1999/xlink}'
INK_LUM = 0.45            # luminance below this is ink
R = 1.0                   # raster pixels per font unit
SKIP = {'text', 'tspan', 'image', 'defs', 'clipPath', 'mask', 'symbol', 'marker',
        'pattern', 'metadata', 'title', 'desc', 'style', 'namedview', 'linearGradient',
        'radialGradient', 'filter', 'foreignObject', 'script'}
NAMED = {'black': (0, 0, 0), 'white': (255, 255, 255), 'red': (255, 0, 0),
         'blue': (0, 0, 255), 'navy': (0, 0, 128), 'green': (0, 128, 0),
         'gray': (128, 128, 128), 'grey': (128, 128, 128), 'silver': (192, 192, 192),
         'maroon': (128, 0, 0), 'purple': (128, 0, 128), 'darkblue': (0, 0, 139),
         'darkgreen': (0, 100, 0), 'brown': (165, 42, 42), 'orange': (255, 165, 0),
         'yellow': (255, 255, 0), 'lightgray': (211, 211, 211), 'lightgrey': (211, 211, 211),
         'dimgray': (105, 105, 105), 'darkgray': (169, 169, 169), 'darkgrey': (169, 169, 169)}


# ----------------------------------------------------------------- SVG parsing

def local(tag):
    return tag.split('}', 1)[1] if '}' in tag else tag


def parse_transform(s):
    """An SVG transform attribute -> fontTools Transform (SVG order)."""
    t = Transform()
    for name, args in re.findall(r'(\w+)\s*\(([^)]*)\)', s or ''):
        v = [float(x) for x in re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', args)]
        if name == 'matrix' and len(v) == 6:
            n = Transform(*v)
        elif name == 'translate':
            n = Transform(1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == 'scale':
            n = Transform(v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == 'rotate':
            a = math.radians(v[0])
            n = Transform(math.cos(a), math.sin(a), -math.sin(a), math.cos(a), 0, 0)
            if len(v) == 3:
                n = Transform(1, 0, 0, 1, v[1], v[2]).transform(n).transform(
                    Transform(1, 0, 0, 1, -v[1], -v[2]))
        elif name == 'skewX':
            n = Transform(1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        elif name == 'skewY':
            n = Transform(1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        else:
            continue
        t = t.transform(n)
    return t


def parse_color(s):
    """CSS colour -> (r, g, b) or None for none/transparent; 'paint' for
    gradients and the like (counted as ink)."""
    if s is None:
        return None
    s = s.strip().lower()
    if s in ('none', 'transparent', ''):
        return None
    if s.startswith('url('):
        return 'paint'
    if s == 'currentcolor':
        return (0, 0, 0)
    m = re.fullmatch(r'#([0-9a-f]{3,4})', s)
    if m:
        h = m.group(1)
        return tuple(int(c * 2, 16) for c in h[:3])
    m = re.fullmatch(r'#([0-9a-f]{6})(?:[0-9a-f]{2})?', s)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.fullmatch(r'rgba?\(([^)]*)\)', s)
    if m:
        v = [x.strip() for x in m.group(1).replace('/', ',').split(',')]
        vals = []
        for x in v[:3]:
            vals.append(round(float(x[:-1]) * 2.55) if x.endswith('%') else float(x))
        return tuple(vals)
    return NAMED.get(s, (0, 0, 0))     # unknown names: assume dark


def dark(color):
    if color is None:
        return False
    if color == 'paint':
        return True
    r, g, b = color
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 < INK_LUM


def css_rules(root):
    """.class{...} rules from <style> blocks (Illustrator writes these)."""
    rules = {}
    for st in root.iter(SVG + 'style'):
        text = re.sub(r'/\*.*?\*/', '', st.text or '', flags=re.S)
        for sel, body in re.findall(r'([^{}]+)\{([^}]*)\}', text):
            decl = dict(kv.split(':', 1) for kv in
                        (p.strip() for p in body.split(';')) if ':' in kv)
            decl = {k.strip(): v.strip() for k, v in decl.items()}
            for s in sel.split(','):
                s = s.strip()
                if s.startswith('.'):
                    rules.setdefault(s[1:], {}).update(decl)
    return rules


PROPS = ('fill', 'stroke', 'stroke-width', 'opacity', 'display', 'visibility',
         'fill-rule', 'fill-opacity', 'stroke-opacity')


def style_of(el, inherited, rules):
    st = dict(inherited)
    for cls in (el.get('class') or '').split():
        st.update(rules.get(cls, {}))
    for p in PROPS:
        if el.get(p) is not None:
            st[p] = el.get(p)
    for kv in (el.get('style') or '').split(';'):
        if ':' in kv:
            k, v = kv.split(':', 1)
            st[k.strip()] = v.strip()
    return st


def shape_d(el):
    """Path data for a basic shape element, or None."""
    tag = local(el.tag)
    f = lambda k, d=0.0: float(el.get(k, d))
    if tag == 'path':
        return el.get('d')
    if tag == 'rect':
        x, y, w, h = f('x'), f('y'), f('width'), f('height')
        rx = f('rx', 0) or f('ry', 0)
        ry = f('ry', 0) or rx
        if w <= 0 or h <= 0:
            return None
        if not rx:
            return f'M{x} {y}H{x + w}V{y + h}H{x}Z'
        rx, ry = min(rx, w / 2), min(ry, h / 2)
        return (f'M{x + rx} {y}H{x + w - rx}A{rx} {ry} 0 0 1 {x + w} {y + ry}V{y + h - ry}'
                f'A{rx} {ry} 0 0 1 {x + w - rx} {y + h}H{x + rx}A{rx} {ry} 0 0 1 {x} {y + h - ry}'
                f'V{y + ry}A{rx} {ry} 0 0 1 {x + rx} {y}Z')
    if tag in ('circle', 'ellipse'):
        cx, cy = f('cx'), f('cy')
        rx = f('r') if tag == 'circle' else f('rx')
        ry = f('r') if tag == 'circle' else f('ry')
        if rx <= 0 or ry <= 0:
            return None
        return (f'M{cx - rx} {cy}A{rx} {ry} 0 1 0 {cx + rx} {cy}'
                f'A{rx} {ry} 0 1 0 {cx - rx} {cy}Z')
    if tag == 'line':
        return f'M{f("x1")} {f("y1")}L{f("x2")} {f("y2")}'
    if tag in ('polyline', 'polygon'):
        pts = re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', el.get('points', ''))
        if len(pts) < 4:
            return None
        d = 'M' + ' '.join(f'{pts[i]} {pts[i + 1]}' for i in range(0, len(pts) - 1, 2))
        return d + ('Z' if tag == 'polygon' else '')
    return None


def nested_svg_transform(el):
    """A nested <svg> with a viewBox maps its box onto x/y/width/height."""
    vb = el.get('viewBox')
    if not vb:
        return Transform()
    vx, vy, vw, vh = [float(v) for v in re.split(r'[\s,]+', vb.strip())]
    w = float(re.sub(r'[a-z%]+$', '', el.get('width', str(vw))) or vw)
    h = float(re.sub(r'[a-z%]+$', '', el.get('height', str(vh))) or vh)
    sx, sy = w / vw, h / vh
    s = min(sx, sy)      # preserveAspectRatio xMidYMid meet, the default
    x = float(el.get('x', 0)) + (w - vw * s) / 2
    y = float(el.get('y', 0)) + (h - vh * s) / 2
    return Transform(s, 0, 0, s, x - vx * s, y - vy * s)


class Shape:
    __slots__ = ('rec', 'bbox', 'stroke_w', 'filled', 'stroked', 'fill_rule', 'id', 'frame')

    def __init__(self, rec, stroke_w, filled, stroked, fill_rule, sid, frame):
        self.rec, self.stroke_w = rec, stroke_w
        self.filled, self.stroked, self.fill_rule = filled, stroked, fill_rule
        self.id, self.frame = sid, frame
        pts = [p for op, args in rec.value for p in args if isinstance(p, tuple)]
        if pts:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            pad = stroke_w / 2 if stroked else 0
            self.bbox = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
        else:
            self.bbox = None


def collect(root):
    """Every drawable shape in root user space: [Shape]. Ink and frame
    alike; the caller decides by colour, id and position."""
    rules = css_rules(root)
    shapes = []

    def walk(el, ctm, st, in_frame):
        tag = local(el.tag)
        if tag in SKIP:
            return
        st = style_of(el, st, rules)
        if st.get('display') == 'none' or st.get('visibility') == 'hidden':
            return
        eid = el.get('id') or ''
        in_frame = in_frame or eid == 'frame' or eid.startswith('frame-') or eid.startswith('fid-')
        t = ctm.transform(parse_transform(el.get('transform')))
        if tag == 'svg' and el is not root:
            t = t.transform(nested_svg_transform(el))
        if tag in ('g', 'svg', 'a', 'switch'):
            for ch in el:
                walk(ch, t, st, in_frame)
            return
        if tag == 'use':      # a referenced shape, drawn again where used
            href = (el.get(XLINK + 'href') or el.get('href') or '').lstrip('#')
            target = ids.get(href)
            if target is not None and local(target.tag) not in ('use',):
                t2 = t.transform(Transform(1, 0, 0, 1, float(el.get('x', 0)), float(el.get('y', 0))))
                walk(target, t2, st, in_frame)
            return
        d = shape_d(el)
        if not d:
            return
        rec = RecordingPen()
        try:
            parse_path(d, TransformPen(rec, t))
        except Exception as e:      # a malformed path: skip, but say so
            print(f'  ! unreadable path {eid or tag}: {e}')
            return
        fill = parse_color(st.get('fill', 'black'))
        stroke = parse_color(st.get('stroke', 'none'))
        if tag == 'line' or len({p for op, args in rec.value for p in args
                                 if isinstance(p, tuple)}) < 3:
            fill = None          # no area to fill: a line, a dot, a two-point path
        if float(st.get('opacity', 1) or 1) < 0.05:
            return
        if fill is not None and float(st.get('fill-opacity', 1) or 1) < 0.05:
            fill = None
        if stroke is not None and float(st.get('stroke-opacity', 1) or 1) < 0.05:
            stroke = None
        sw = float(re.sub(r'[a-z%]+$', '', str(st.get('stroke-width', 1))) or 1)
        sw *= math.sqrt(abs(t.xx * t.yy - t.xy * t.yx))
        filled = dark(fill)
        stroked = dark(stroke) and sw > 0
        pale = (fill is not None and not dark(fill)) or (stroke is not None and not dark(stroke))
        if not (filled or stroked) and not pale:
            return
        shapes.append(Shape(rec, sw if stroke is not None else 0, filled, stroked,
                            st.get('fill-rule', 'nonzero'), eid, in_frame or not (filled or stroked)))

    ids = {el.get('id'): el for el in root.iter() if el.get('id')}
    walk(root, Transform(), {}, False)
    return [s for s in shapes if s.bbox]


# ------------------------------------------------------------- registration

def register(shapes, man):
    """Transform from the drawing's user space onto the frame, from the
    four corner squares (by id, else by shape: dark squares of the right
    proportion nearest the corners). Identity if they cannot be found."""
    F = man['fiducial_size']
    want = {k: (v[0] + F / 2, v[1] + F / 2) for k, v in man['fiducials'].items()}
    found = {}
    for s in shapes:
        if s.id.startswith('fid-') and s.id[4:] in want:
            b = s.bbox
            found[s.id[4:]] = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    if len(found) < 2:
        # by shape: filled dark, nearly square, small; the extreme ones
        cands = []
        for s in shapes:
            b = s.bbox
            w, h = b[2] - b[0], b[3] - b[1]
            if s.filled and w > 0 and h > 0 and 0.8 < w / h < 1.25:
                cands.append(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, w))
        if cands:
            xs = [c[0] for c in cands]
            ys = [c[1] for c in cands]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            for key, tx, ty in (('tl', x0, y0), ('tr', x1, y0), ('bl', x0, y1), ('br', x1, y1)):
                c = min(cands, key=lambda c: (c[0] - tx) ** 2 + (c[1] - ty) ** 2)
                found[key] = (c[0], c[1])
    if len(found) < 2:
        print('  ! corner squares not found: assuming the drawing kept the frame coordinates')
        return Transform(), 'identity'
    # least squares similarity (scale, rotation, translation) from found -> want
    src = np.array([found[k] for k in found])
    dst = np.array([want[k] for k in found])
    sc, dc = src.mean(0), dst.mean(0)
    s0, d0 = src - sc, dst - dc
    a = (s0 * d0).sum()
    b = (s0[:, 0] * d0[:, 1] - s0[:, 1] * d0[:, 0]).sum()
    n = (s0 ** 2).sum()
    if n < 1e-9:
        return Transform(), 'identity'
    ca, sa = a / n, b / n
    t = Transform(ca, sa, -sa, ca, 0, 0)
    ox, oy = t.transformPoint(tuple(sc))
    t = Transform(ca, sa, -sa, ca, dc[0] - ox, dc[1] - oy)
    scale = math.hypot(ca, sa)
    err = max(math.dist(t.transformPoint(tuple(p)), tuple(q)) for p, q in zip(src, dst))
    how = f'{len(found)} corners, scale {scale:.4f}, rotation {math.degrees(math.atan2(sa, ca)):.2f}°, residual {err:.2f}'
    if abs(scale - 1) < 1e-4 and abs(sa) < 1e-6 and abs(t.dx) < 0.05 and abs(t.dy) < 0.05:
        return Transform(), f'{len(found)} corners in place'
    return t, how


# ------------------------------------------------------------- rasterising

def flatten(rec, tol=0.6):
    """RecordingPen value -> list of polylines (closed flag) in its own space."""
    polys, cur, closed = [], [], False

    def bez(p0, ctrl, p1):
        pts = [p0] + list(ctrl) + [p1]
        L = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        n = max(2, int(L / (tol * 4)) + 1)
        out = []
        for i in range(1, n + 1):
            t = i / n
            if len(ctrl) == 1:
                (x1, y1), = ctrl
                x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * x1 + t * t * p1[0]
                y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * y1 + t * t * p1[1]
            else:
                (x1, y1), (x2, y2) = ctrl
                x = ((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * x1
                     + 3 * (1 - t) * t * t * x2 + t ** 3 * p1[0])
                y = ((1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * y1
                     + 3 * (1 - t) * t * t * y2 + t ** 3 * p1[1])
            out.append((x, y))
        return out

    for op, args in rec.value:
        if op == 'moveTo':
            if cur:
                polys.append((cur, closed))
            cur, closed = [args[0]], False
        elif op == 'lineTo':
            cur.append(args[0])
        elif op == 'curveTo':
            if cur:
                cur.extend(bez(cur[-1], args[:-1], args[-1]))
        elif op == 'qCurveTo':
            if cur:
                pts = list(args)
                if pts[-1] is None:      # TrueType implied on-curve
                    pts[-1] = ((pts[0][0] + pts[-2][0]) / 2, (pts[0][1] + pts[-2][1]) / 2)
                p0 = cur[-1]
                # split multi-control qcurves into single quadratics
                ctrls, end = pts[:-1], pts[-1]
                for i, c in enumerate(ctrls):
                    if i < len(ctrls) - 1:
                        nxt = ctrls[i + 1]
                        mid = ((c[0] + nxt[0]) / 2, (c[1] + nxt[1]) / 2)
                        cur.extend(bez(p0, [c], mid))
                        p0 = mid
                    else:
                        cur.extend(bez(p0, [c], end))
        elif op in ('closePath', 'endPath'):
            closed = op == 'closePath'
            if cur:
                polys.append((cur, closed))
            cur = []
    if cur:
        polys.append((cur, closed))
    return polys


def rasterise(shapes, to_px, W, H):
    """Shapes -> boolean ink raster (H, W); to_px maps user space -> pixels."""
    img = np.zeros((H, W), dtype=np.uint8)
    for s in shapes:
        polys = [([to_px.transformPoint(p) for p in pts], closed) for pts, closed in flatten(s.rec)]
        if s.filled:
            acc = np.zeros((H, W), dtype=np.int32)
            for pts, _ in polys:
                if len(pts) < 3:
                    continue
                arr = np.array([pts], dtype=np.int32)
                if s.fill_rule == 'evenodd':
                    m = np.zeros((H, W), dtype=np.uint8)
                    cv2.fillPoly(m, arr, 1)
                    acc ^= m
                else:
                    area = 0.0
                    for i in range(len(pts)):
                        x0, y0 = pts[i]
                        x1, y1 = pts[(i + 1) % len(pts)]
                        area += x0 * y1 - x1 * y0
                    m = np.zeros((H, W), dtype=np.uint8)
                    cv2.fillPoly(m, arr, 1)
                    acc += m.astype(np.int32) * (1 if area >= 0 else -1)
            img |= (acc != 0).astype(np.uint8)
        if s.stroked:
            w = max(1, int(round(s.stroke_w * math.sqrt(abs(to_px.xx * to_px.yy - to_px.xy * to_px.yx)))))
            for pts, closed in polys:
                arr = np.array([pts], dtype=np.int32)
                if len(pts) == 1:
                    cv2.circle(img, tuple(arr[0][0]), max(1, w // 2), 1, -1)
                else:
                    cv2.polylines(img, arr, closed, 1, w, lineType=cv2.LINE_8)
                    if not closed:       # round caps
                        for p in (arr[0][0], arr[0][-1]):
                            cv2.circle(img, tuple(p), max(1, w // 2), 1, -1)
    return img.astype(bool)


def trace(mask, px_to_font, turd=12):
    """Boolean raster -> font-space path (RecordingPen value list); potrace."""
    # potracer treats True as white, so the ink goes in inverted
    path = potrace.Bitmap(~mask).trace(turdsize=turd, alphamax=1.0, opticurve=True,
                                       opttolerance=0.2)
    rec = RecordingPen()
    pen = TransformPen(rec, px_to_font)
    for curve in path:
        p = curve.start_point
        pen.moveTo((p.x, p.y))
        for seg in curve:
            e = seg.end_point
            if seg.is_corner:
                pen.lineTo((seg.c.x, seg.c.y))
                pen.lineTo((e.x, e.y))
            else:
                pen.curveTo((seg.c1.x, seg.c1.y), (seg.c2.x, seg.c2.y), (e.x, e.y))
        pen.closePath()
    return rec


def rec_bbox(rec):
    pts = [p for op, args in rec.value for p in args if isinstance(p, tuple)]
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]


def rec_d(rec, nd=1):
    """RecordingPen value -> SVG path data (no transform)."""
    fmt = lambda v: ('%.*f' % (nd, v)).rstrip('0').rstrip('.') if nd else '%d' % round(v)
    out = []
    for op, args in rec.value:
        if op == 'moveTo':
            out.append('M%s %s' % tuple(fmt(v) for v in args[0]))
        elif op == 'lineTo':
            out.append('L%s %s' % tuple(fmt(v) for v in args[0]))
        elif op == 'curveTo':
            out.append('C' + ' '.join(fmt(v) for p in args for v in p))
        elif op == 'qCurveTo':
            # TrueType: several off-curve points in a row imply on-curve
            # midpoints between them; a trailing None means the contour is all
            # off-curve and closes through the midpoint of first and last
            pts = list(args)
            if pts[-1] is None:
                pts[-1] = ((pts[0][0] + pts[-2][0]) / 2, (pts[0][1] + pts[-2][1]) / 2)
            ctrls, end = pts[:-1], pts[-1]
            for i, c in enumerate(ctrls):
                if i < len(ctrls) - 1:
                    nxt = ctrls[i + 1]
                    mid = ((c[0] + nxt[0]) / 2, (c[1] + nxt[1]) / 2)
                    out.append('Q%s %s %s %s' % (fmt(c[0]), fmt(c[1]), fmt(mid[0]), fmt(mid[1])))
                else:
                    out.append('Q%s %s %s %s' % (fmt(c[0]), fmt(c[1]), fmt(end[0]), fmt(end[1])))
        elif op == 'closePath':
            out.append('Z')
    return ''.join(out)


# ---------------------------------------------------------------- analysis

def components(mask, px_to_font, G):
    """Connected pieces of the raster with font-space bboxes and a zone:
    base (touches the letter body), above, below."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 6:
            continue
        x0, y1 = px_to_font.transformPoint((x, y))
        x1, y0 = px_to_font.transformPoint((x + w, y + h))
        zone = 'base'
        if y1 < G['baseline'] - 15:
            zone = 'below'
        elif y0 > G['xheight'] - 25:
            zone = 'above'
        out.append({'bbox': [round(v) for v in (x0, y0, x1, y1)], 'area': int(area), 'zone': zone})
    out.sort(key=lambda c: -c['area'])
    return out


def analyse(cell, comps, ink_box, ref_comps, ref_box, G, upm, inside):
    """Compare the drawing to the reference; return (flags, measures)."""
    flags, m = [], {}
    if not inside:
        flags.append('ink leaves the cell')
    zones = lambda cs: sorted(c['zone'] for c in cs)
    m['pieces'] = len(comps)
    m['pieces_expected'] = len(ref_comps)
    if len(comps) != len(ref_comps):
        flags.append(f'{len(comps)} pieces, reference has {len(ref_comps)} '
                     f'({"+".join(zones(comps)) or "none"} vs {"+".join(zones(ref_comps))})')
    elif zones(comps) != zones(ref_comps):
        flags.append(f'pieces sit {"+".join(zones(comps))}, reference {"+".join(zones(ref_comps))}')
    base = [c for c in comps if c['zone'] == 'base']
    rbase = [c for c in ref_comps if c['zone'] == 'base']
    if base and rbase:
        bb = [min(c['bbox'][0] for c in base), min(c['bbox'][1] for c in base),
              max(c['bbox'][2] for c in base), max(c['bbox'][3] for c in base)]
        rb = [min(c['bbox'][0] for c in rbase), min(c['bbox'][1] for c in rbase),
              max(c['bbox'][2] for c in rbase), max(c['bbox'][3] for c in rbase)]
        m['base_bottom'], m['base_top'] = bb[1], bb[3]
        m['ref_bottom'], m['ref_top'] = rb[1], rb[3]
        m['width_ratio'] = round((bb[2] - bb[0]) / max(1, rb[2] - rb[0]), 2)
        tol = upm * 0.04
        if abs(bb[1] - rb[1]) > tol:
            flags.append(f'bottom {bb[1]:+d} (reference {rb[1]:+d})')
        if abs(bb[3] - rb[3]) > tol * 1.5:
            flags.append(f'top {bb[3]:+d} (reference {rb[3]:+d})')
        if not 0.4 <= m['width_ratio'] <= 2.0:   # a hand is narrower than a serif face
            flags.append(f'width {m["width_ratio"]}x the reference')
    if ink_box:
        m['ink_bbox'] = [round(v) for v in ink_box]
    return flags, m


# ------------------------------------------------------------------ output

def file_stem(cell):
    """The glyph file's name: the glyph name, except that a name with a
    capital in it (A, B ...) is spelt by codepoint (uni0041), since a and A
    cannot share a folder on a case-insensitive disk; the glyph name itself
    stays on the file's root as data-glyph."""
    name = cell['name']
    if name == name.lower():
        return name
    s = unicodedata.normalize('NFC', cell['text'])
    return 'uni%04X' % ord(s[0]) + ''.join('_uni%04X' % ord(c) for c in s[1:])


def glyph_svg(name, rec, cell, advance, ref,
              note='traced from the drawn frame\n       by fonts/tools/hand_read.py'):
    """The fonts/tools/font_svg.py format: em box, guides, g#glyph."""
    upm, asc, desc, xh = ref.upm, ref.asc, ref.desc, ref.xh
    H = asc - desc
    d = rec_d(TransformedRec(rec, Transform(1, 0, 0, -1, 0, asc)))
    guides = '\n'.join(
        f'    <line x1="{-upm // 2}" x2="{upm + upm // 2}" y1="{asc - y}" y2="{asc - y}" stroke="#8bf" '
        f'stroke-width="{max(2, upm // 500)}" stroke-dasharray="{upm // 85} {upm // 85}"/><!-- {label} (font y={y}) -->'
        for y, label in ((0, 'baseline'), (xh, 'x-height'), (desc, 'descender')))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-upm // 2} 0 {2 * upm} {H}" width="512" data-glyph="{name}" data-form="{HF.esc(cell['form'])}" data-text="{HF.esc(cell['text'])}" data-advance="{advance}">
  <!-- Diafon hand glyph "{name}" for {HF.esc(cell['text'])} (input {HF.esc(cell['form'])}), {note}. Edit ONLY inside g#glyph; g#guides is ignored on import.
       Font baseline is the dashed line at SVG y={asc}; the em is {upm} units; advance {advance}. -->
  <g id="guides" opacity="0.5">
{guides}
  </g>
  <g id="glyph">
    <path fill="#111" d="{d}"/>
  </g>
</svg>
'''


class TransformedRec:
    """A RecordingPen value seen through a transform (for rec_d)."""

    def __init__(self, rec, t):
        out = RecordingPen()
        rec.replay(TransformPen(out, t))
        self.value = out.value


def review_svg(man, results, ref):
    """The frame again, with the traced glyphs and their flags drawn in."""
    frame = open(HF.OUT_SVG, encoding='utf-8').read()
    S = man['scale']
    ink = []
    for r in results:
        cell = r['cell']
        x0, y0, x1, y1 = cell['box']
        if r.get('rec'):
            gx = x0 + (x1 - x0 - r['advance'] * S) / 2
            t = Transform(S, 0, 0, -S, gx, cell['baseline'])
            # the pale reference under the traced glyph, at the same origin
            ink.append(f'<path fill="#d8dce6" d="{ref.svg_d(cell["text"], 1, gx, cell["baseline"])}"/>')
            ink.append(f'<path fill="#111" d="{rec_d(TransformedRec(r["rec"], t), 2)}"/>')
        for i, fl in enumerate(r.get('flags', [])):
            ink.append(f'<text x="{x0 + 4}" y="{y1 - 4 - 8 * (len(r["flags"]) - 1 - i)}" '
                       f'font-family="Menlo,Consolas,monospace" font-size="6" fill="#c04646">'
                       f'{HF.esc(fl)}</text>')
    body = '\n'.join(ink)
    out = frame.replace('<g id="ink" inkscape:groupmode="layer" inkscape:label="ink (draw here)">\n</g>',
                        f'<g id="review">\n{body}\n</g>')
    out = out.replace('<title>Diafon hand frame</title>', '<title>Diafon hand review</title>')
    return out


# -------------------------------------------------------------------- main

def main(argv):
    src, manifest, out_dir, keep_stale = DEFAULT_IN, HF.OUT_JSON, OUT_DIR, False
    review, report_path = REVIEW, REPORT
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == '--manifest':
            manifest = args.pop(0)
        elif a == '--out':
            out_dir = args.pop(0)
        elif a == '--review':
            review = args.pop(0)
        elif a == '--report':
            report_path = args.pop(0)
        elif a == '--keep-stale':
            keep_stale = True
        else:
            src = a
    if not os.path.exists(src):
        print(f'no drawing at {os.path.relpath(src, ROOT)}: save the drawn frame there '
              '(or pass its path)')
        return 1
    man = json.load(open(manifest, encoding='utf-8'))
    ref = HF.Ref(os.path.join(ROOT, man['font']))
    G, S, upm = man['guides'], man['scale'], man['units_per_em']
    root = ET.parse(src).getroot()
    shapes = collect(root)
    reg, how = register(shapes, man)
    print(f'{os.path.relpath(src, ROOT)}: {len(shapes)} shapes; registration: {how}')
    inks = [s for s in shapes if (s.filled or s.stroked) and not s.frame]
    # into frame space
    for s in inks:
        out = RecordingPen()
        s.rec.replay(TransformPen(out, reg))
        s.rec = out
        b = s.bbox
        pts = [reg.transformPoint(p) for p in ((b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3]))]
        s.bbox = (min(p[0] for p in pts), min(p[1] for p in pts),
                  max(p[0] for p in pts), max(p[1] for p in pts))
        s.stroke_w *= math.hypot(reg.xx, reg.xy)
    F = man['fiducial_size']
    fid_boxes = [(x - 2, y - 2, x + F + 2, y + F + 2) for x, y in man['fiducials'].values()]
    cells = man['cells']
    by_cell = {c['id']: [] for c in cells}
    strays = []
    for s in inks:
        cx, cy = (s.bbox[0] + s.bbox[2]) / 2, (s.bbox[1] + s.bbox[3]) / 2
        if any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in fid_boxes):
            continue
        for c in cells:
            b = c['box']
            if b[0] <= cx <= b[2] and b[1] <= cy <= b[3]:
                by_cell[c['id']].append(s)
                break
        else:
            strays.append(s)
    os.makedirs(out_dir, exist_ok=True)
    results, report = [], []
    W = int(round((man['cell']['width'] / S) * R))
    H = int(round((man['cell']['top'] - man['cell']['bottom']) * R))
    n_drawn = 0
    for c in cells:
        shapes_c = by_cell[c['id']]
        if not shapes_c:
            continue
        n_drawn += 1
        x0, y0, x1, y1 = c['box']
        # frame -> font units (origin: cell left edge, baseline), then -> pixels
        frame_to_font = Transform(1 / S, 0, 0, -1 / S, -x0 / S, c['baseline'] / S)
        font_to_px = Transform(R, 0, 0, -R, 0, man['cell']['top'] * R)
        to_px = font_to_px.transform(frame_to_font)
        px_to_font = font_to_px.inverse()
        mask = rasterise(shapes_c, to_px, W, H)
        inside = all(x0 <= s.bbox[0] and s.bbox[2] <= x1 and y0 <= s.bbox[1] and s.bbox[3] <= y1
                     for s in shapes_c)
        if not mask.any():
            report.append({'id': c['id'], 'form': c['form'], 'text': c['text'], 'name': c['name'],
                           'flags': ['ink too thin to trace'], 'pieces': 0})
            continue
        rec = trace(mask, px_to_font)
        ink_box = rec_bbox(rec)
        comps = components(mask, px_to_font, G)
        # the reference through the same pipeline, for like-for-like pieces
        rref = RecordingPen()
        adv_ref = ref.draw(c['text'], rref)
        rbox = rec_bbox(rref) or [0, 0, 0, 0]
        ref_px = Transform(R, 0, 0, -R, (W / R - adv_ref) / 2 * R, man['cell']['top'] * R)
        rmask = rasterise([Shape(rref, 0, True, False, 'nonzero', 'ref', False)], ref_px, W, H)
        ref_comps = components(rmask, ref_px.inverse(), G)
        flags, measures = analyse(c, comps, ink_box, ref_comps, rbox, G, upm, inside)
        # horizontal origin: the reference's left side bearing before the ink
        lsb = rbox[0] if c['ref']['bbox'] else 50
        rsb = (c['ref']['advance'] - c['ref']['bbox'][2]) if c['ref']['bbox'] else 50
        shift = lsb - ink_box[0]
        placed = RecordingPen()
        rec.replay(TransformPen(placed, Transform(1, 0, 0, 1, shift, 0)))
        advance = int(round(lsb + (ink_box[2] - ink_box[0]) + rsb))
        path = os.path.join(out_dir, file_stem(c) + '.svg')
        open(path, 'w', encoding='utf-8').write(glyph_svg(c['name'], placed, c, advance, ref))
        results.append({'cell': c, 'rec': placed, 'advance': advance, 'flags': flags})
        report.append({'id': c['id'], 'form': c['form'], 'text': c['text'], 'name': c['name'],
                       'file': os.path.relpath(path, ROOT), 'advance': advance,
                       'shapes': len(shapes_c), 'flags': flags, **measures,
                       'pieces_detail': comps})
    if not keep_stale:
        # drop glyph files of cells no longer drawn: only this tool's own
        # files (data-form on the root), so a wrong --out cannot eat fonts/svg
        drawn_files = {r.get('file') for r in report if r.get('file')}
        for fn in sorted(os.listdir(out_dir)):
            full = os.path.join(out_dir, fn)
            p = os.path.relpath(full, ROOT)
            if not fn.endswith('.svg') or p in drawn_files:
                continue
            head = open(full, encoding='utf-8', errors='replace').read(600)
            if 'data-form=' in head and 'hand_read.py' in head:
                os.remove(full)
                print(f'  removed stale {p}')
    open(review, 'w', encoding='utf-8').write(review_svg(man, results, ref))
    summary = {'source': os.path.relpath(src, ROOT), 'registration': how,
               'cells_total': len(cells), 'cells_drawn': n_drawn,
               'cells_missing': [c['form'] for c in cells if not by_cell[c['id']]],
               'strays': [{'bbox': [round(v, 1) for v in s.bbox], 'id': s.id} for s in strays],
               'glyphs': report}
    json.dump(summary, open(report_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    flagged = [r for r in report if r['flags']]
    print(f'{n_drawn}/{len(cells)} cells drawn -> {os.path.relpath(out_dir, ROOT)}/ '
          f'({len(report) - len(flagged)} clean, {len(flagged)} flagged); '
          f'{len(strays)} stray shapes outside every cell')
    for r in flagged:
        print(f'  {r["text"]:4s} {r["form"]:6s} {r["name"]:16s} ' + '; '.join(r['flags']))
    for s in strays[:10]:
        print(f'  stray {s.id or "(no id)"} at {tuple(round(v) for v in s.bbox)}')
    print(f'review: {os.path.relpath(review, ROOT)} · report: {os.path.relpath(report_path, ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
