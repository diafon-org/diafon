#!/usr/bin/env python3
"""SVG reading shared by the font tools: tag names, styles, colours, transforms
and the basic shapes as path data. hand_read.py reads the drawn frame with
these, font_svg.py the glyph overrides."""
import math
import re
import xml.etree.ElementTree as ET

from fontTools.misc.transform import Transform

SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'
INKSCAPE_NS = 'http://www.inkscape.org/namespaces/inkscape'
SODIPODI_NS = 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'
SVG = '{%s}' % SVG_NS
XLINK = '{%s}' % XLINK_NS
INKSCAPE = '{%s}' % INKSCAPE_NS
SODIPODI = '{%s}' % SODIPODI_NS
INK_LUM = 0.45            # luminance below this is ink
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
PROPS = ('fill', 'stroke', 'stroke-width', 'opacity', 'display', 'visibility',
         'fill-rule', 'fill-opacity', 'stroke-opacity')


def register_namespaces():
    """So ElementTree writes svg/inkscape/sodipodi/xlink prefixes, not ns0."""
    ET.register_namespace('', SVG_NS)
    ET.register_namespace('xlink', XLINK_NS)
    ET.register_namespace('inkscape', INKSCAPE_NS)
    ET.register_namespace('sodipodi', SODIPODI_NS)


def local(tag):
    return tag.split('}', 1)[1] if '}' in tag else tag


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
