#!/usr/bin/env python3
"""The SVG round trip for the Diafon fonts: export glyphs as editable SVGs with
guides and rulers, edit them in Inkscape (or any vector editor), and the build
imports them back.

    python3 fonts/tools/font_svg.py export serif dieresis uni0324 t A   # glyph names, letters, U+XXXX
    python3 fonts/tools/font_svg.py export sans uni0324 --on t k        # ghost base letters under a mark
    python3 fonts/tools/font_svg.py check serif                         # what the build would import

fonts/svg/<family>/<glyph>.svg is the one way to override a glyph: it replaces
that glyph's outline in that family (fonts/families.yaml: serif, sans, mono)
when fonts/build.sh runs; delete the file and the glyph returns to its
procedural or Noto shape. Only a file named exactly for a glyph is imported: a
variant saved beside it (n_uni0326-try.svg) or a file starting with `_` is
kept but inert, so variants are swapped in by renaming. Capitals are filed by
codepoint (uni0041.svg for A: a and A cannot share a folder on a
case-insensitive disk). Marks seed the baked letter+mark compositions, so a
curated mark changes every composition; a composition (t_uni0326.svg) can be
curated as a whole too. fonts/tools/serif_tail.py writes the serif's anchor
compositions into this folder from a few numbers.

The canvas: one SVG unit is one font unit, the root's data-origin is the SVG
point of the font's (0, 0), y grows down in SVG and up in the font. Two
layers. `guides` is locked and ignored on import: the em box, ascender, cap
height, x-height, baseline, descender, origin and advance, rulers in font
units, a pale ghost of the exported shape and the base letters of --on.
`glyph` becomes the outline: paths, rects, circles, ellipses, polygons,
groups with transforms and <use> clones of the file's own elements, in any
nesting. Fills only, holes by either fill rule, overlaps merged. Strokes are
not rendered (Path > Stroke to Path first), nor text (Path > Object to Path).
data-advance on the root sets the advance width.
"""
import argparse
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import RecordingPen, replayRecording
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path.parser import parse_path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svg_read import (XLINK, INKSCAPE, SKIP, SVG_NS, XLINK_NS, INKSCAPE_NS, SODIPODI_NS,
                      local, parse_color, css_rules, style_of, parse_transform, shape_d,
                      nested_svg_transform)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SVG_ROOT = os.path.join(ROOT, 'fonts', 'svg')
LEFT, RIGHT = 500, 1500          # the canvas spans font x -LEFT .. RIGHT
RULER = 120                      # the rulers' strip
INK = '#111'
CUT = '#2a7de1'                  # the cut layer's colour
SPARE_CUT = (1200, 0)            # a spare cut square, 100 wide, set clear of the glyph at this
                                 #   font point: drag it onto the ink to use it


# ------------------------------------------------------------------- the font

def family(key):
    import build_font as BF
    return BF.family(key)


def font_for(key):
    """The derived font if built (the stage the overrides replace), else the
    shipping one."""
    fam = family(key)
    return fam['derived'] if os.path.exists(fam['derived']) else fam['ttf']


def metrics(font):
    from fontTools.pens.boundsPen import BoundsPen
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    os2 = font.get('OS/2')

    def box(ch):
        g = cmap.get(ord(ch))
        if g is None:
            return None
        pen = BoundsPen(gs)
        gs[g].draw(pen)
        return pen.bounds

    d, p, H, x = box('d'), box('p'), box('H'), box('x')
    return {'upm': font['head'].unitsPerEm,
            'asc': font['hhea'].ascent, 'desc': font['hhea'].descent,
            'xh': (os2 and os2.sxHeight) or (x and round(x[3])) or 0,
            'cap': (os2 and os2.sCapHeight) or (H and round(H[3])) or 0,
            'ascender': (d and round(d[3])) or font['hhea'].ascent,
            'descender': (p and round(p[1])) or font['hhea'].descent}


def glyph_name(font, arg):
    """A glyph name, a single character, or a codepoint (0324, U+0324, 0x324)."""
    cmap = font.getBestCmap()
    if arg in font.getGlyphOrder():
        return arg
    if re.fullmatch(r'(0x|U\+)?[0-9A-Fa-f]{4,6}', arg):
        return cmap.get(int(re.sub(r'^(0x|U\+)', '', arg), 16))
    if len(arg) == 1:
        return cmap.get(ord(arg))
    return None


def file_stem(font, gname):
    """The file name for a glyph: the name, unless it carries a capital, then
    the codepoint (uni0041 for A, uni0041_uni0324 for A_uni0324)."""
    if gname == gname.lower():
        return gname
    rev = {g: cp for cp, g in font.getBestCmap().items()}
    head, _, tail = gname.partition('_')
    if head in rev:
        return f'uni{rev[head]:04X}' + (f'_{tail}' if tail else '')
    return gname


def stem_glyph(font, stem):
    """The glyph a file stands for: its stem, or the codepoint form of it."""
    order = set(font.getGlyphOrder())
    if stem in order:
        return stem
    m = re.fullmatch(r'uni([0-9A-Fa-f]{4,6})(?:_(.+))?', stem)
    if m:
        g = font.getBestCmap().get(int(m.group(1), 16))
        if g:
            cand = g + (f'_{m.group(2)}' if m.group(2) else '')
            if cand in order:
                return cand
    return None


def ufo_anchors(key):
    """{glyph: [(name, x, y)]} from the family's UFO sources, if built."""
    fam = family(key)
    if not os.path.isdir(fam['ufo']):
        return {}
    import ufoLib2
    ufo = ufoLib2.Font.open(fam['ufo'])
    return {g.name: [(a.name, a.x, a.y) for a in g.anchors] for g in ufo}


def attach(anchors, gname, other):
    """Where `other` stands next to `gname` so their anchors meet: an offset
    in font units, or None when they share no anchor."""
    a, b = anchors.get(gname, []), anchors.get(other, [])
    for an, ax, ay in a:
        for bn, bx, by in b:
            if an.startswith('_') and an[1:] == bn:       # gname is the mark
                return (ax - bx, ay - by)
            if bn.startswith('_') and bn[1:] == an:       # other is the mark
                return (ax - bx, ay - by)
    return None


# ------------------------------------------------------------------- geometry

def contours(rec):
    """A RecordingPen value split per contour: [(ops, points)], the points
    every on- and off-curve point (enough for containment and direction)."""
    out, ops, pts = [], [], []
    for op, args in rec.value:
        ops.append((op, args))
        pts += [p for p in args if isinstance(p, tuple)]
        if op in ('closePath', 'endPath'):
            out.append((ops, pts))
            ops, pts = [], []
    if ops:
        out.append((ops, pts))
    return out


def area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts))) / 2


def inside(pt, pts):
    x, y = pt
    hit = False
    for i in range(len(pts)):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def components(rec):
    """Contours grouped into shapes, each an outer contour with its holes:
    [[(ops, pts), ...]] — so a diaeresis exports as two paths to move apart."""
    cs = [c for c in contours(rec) if len(c[1]) >= 2]
    depth = [sum(1 for j, o in enumerate(cs) if j != i and inside(c[1][0], o[1]))
             for i, c in enumerate(cs)]
    groups = {i: [c] for i, c in enumerate(cs) if depth[i] % 2 == 0}
    for i, c in enumerate(cs):
        if depth[i] % 2:
            owners = [j for j in groups if inside(c[1][0], cs[j][1])]
            j = min(owners, key=lambda j: abs(area(cs[j][1]))) if owners else None
            (groups[j] if j is not None else groups.setdefault(i, [])).append(c)
    return [groups[i] for i in sorted(groups)]


def path_d(ops_list, t=None):
    pen = SVGPathPen(None)
    dst = TransformPen(pen, t) if t else pen
    for ops in ops_list:
        for op, args in ops:
            getattr(dst, op)(*args)
    return pen.getCommands()


def glyph_rec(font, gname):
    """The glyph's outline, components decomposed."""
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    gs = font.getGlyphSet()
    rec = DecomposingRecordingPen(gs)
    gs[gname].draw(rec)
    return rec


# --------------------------------------------------------------------- export

def canvas(M):
    """(ox, oy, W, H): the origin and size of the canvas, the origin on the
    10-unit grid so Inkscape's grid reads in round font units."""
    ox = RULER + LEFT
    oy = -(-(M['asc'] + RULER) // 10) * 10
    H = -(-(oy - M['desc'] + 60) // 10) * 10
    return ox, oy, ox + RIGHT + 230, H


def guide_layer(M, adv, ghosts, ox, oy, W, H):
    """The reference layer: em box, the heights, origin and advance, rulers,
    ghosts. Everything here is ignored on import."""
    x0, x1 = ox - LEFT, ox + RIGHT
    L = []
    L.append(f'<rect x="{x0}" y="{oy - M["asc"]}" width="{x1 - x0}" height="{M["asc"] - M["desc"]}" '
             f'fill="none" stroke="#ccd" stroke-width="1.5"/><!-- the em box -->')
    heights = [('descender', M['descender']), ('baseline', 0), ('x-height', M['xh']),
               ('cap height', M['cap']), ('ascender', M['ascender'])]
    for label, y in heights:
        sy = oy - y
        strong = label == 'baseline'
        dash = '' if strong else ' stroke-dasharray="12 8"'
        L.append(f'<line x1="{x0}" x2="{x1}" y1="{sy}" y2="{sy}" stroke="{"#48f" if strong else "#8bf"}" '
                 f'stroke-width="{2 if strong else 1.5}"{dash}/>'
                 f'<text x="{x1 + 10}" y="{sy + 7}" fill="#789" font-family="sans-serif" '
                 f'font-size="20">{label} {y}</text>')
    L.append(f'<line x1="{ox}" x2="{ox}" y1="{oy - M["asc"]}" y2="{oy - M["desc"]}" stroke="#f80" '
             f'stroke-width="2"/><text x="{ox + 6}" y="{oy - M["asc"] + 22}" fill="#c60" '
             f'font-family="sans-serif" font-size="20">origin</text>')
    if adv:
        L.append(f'<line x1="{ox + adv}" x2="{ox + adv}" y1="{oy - M["asc"]}" y2="{oy - M["desc"]}" '
                 f'stroke="#f80" stroke-width="1.5" stroke-dasharray="12 8"/><text x="{ox + adv + 6}" '
                 f'y="{oy - M["asc"] + 22}" fill="#c60" font-family="sans-serif" font-size="20">advance {adv}</text>')
    # rulers in font units: x along the top, y (baseline 0) down the left
    ry = RULER - 40
    L.append(f'<line x1="{x0}" x2="{x1}" y1="{ry}" y2="{ry}" stroke="#889" stroke-width="1.5"/>')
    for fx in range(-LEFT, RIGHT + 1, 50):
        big = fx % 100 == 0
        L.append(f'<line x1="{ox + fx}" x2="{ox + fx}" y1="{ry}" y2="{ry - (16 if big else 8)}" stroke="#889" stroke-width="1.5"/>')
        if big:
            L.append(f'<text x="{ox + fx}" y="{ry - 22}" fill="#667" font-family="sans-serif" font-size="18" '
                     f'text-anchor="middle">{fx}</text>')
    rx = RULER - 40
    ytop, ybot = -(-M['asc'] // 50) * 50, (M['desc'] // 50) * 50
    L.append(f'<line x1="{rx}" x2="{rx}" y1="{oy - ytop}" y2="{oy - ybot}" stroke="#889" stroke-width="1.5"/>')
    for fy in range(ybot, ytop + 1, 50):
        big = fy % 100 == 0
        L.append(f'<line x1="{rx}" x2="{rx - (16 if big else 8)}" y1="{oy - fy}" y2="{oy - fy}" stroke="#889" stroke-width="1.5"/>')
        if big:
            L.append(f'<text x="{rx - 22}" y="{oy - fy + 6}" fill="#667" font-family="sans-serif" font-size="18" '
                     f'text-anchor="end">{fy}</text>')
    for gid, d, color in ghosts:
        L.append(f'<path id="{gid}" fill="{color}" opacity="0.14" d="{d}"/>')
    return '\n'.join('    ' + l for l in L)


def glyph_svg(font, gname, key, M, on=(), anchors=None):
    """The editable SVG of a glyph: guides, rulers, ghosts, the outline as one
    path per shape, and Inkscape's layers, guides and grid."""
    ox, oy, W, H = canvas(M)
    to_svg = Transform(1, 0, 0, -1, ox, oy)
    adv = font['hmtx'][gname][0]
    rec = glyph_rec(font, gname)
    ghosts = [('ghost', path_d([ops for group in components(rec) for ops, _ in group], to_svg), '#000')]
    for other in on:
        off = attach(anchors or {}, gname, other)
        if off is None and anchors:
            print(f'  {gname} and {other} share no anchor; {other} drawn at the origin')
        dx, dy = off or (0, 0)
        ghosts.append((f'on-{other}', path_d([ops for ops, _ in contours(glyph_rec(font, other))],
                                             to_svg.translate(dx, dy)), '#06c'))
    paths = '\n'.join(f'    <path id="shape{i + 1}" fill="{INK}" d="{path_d([ops for ops, _ in group], to_svg)}"/>'
                      for i, group in enumerate(components(rec)))
    ink_guides = '\n'.join(
        f'    <sodipodi:guide position="0,{H - (oy - y)}" orientation="0,1" inkscape:label="{label}" inkscape:locked="true"/>'
        for label, y in (('baseline', 0), ('x-height', M['xh']), ('cap height', M['cap']),
                         ('ascender', M['ascender']), ('descender', M['descender'])))
    ink_guides += f'\n    <sodipodi:guide position="{ox},0" orientation="1,0" inkscape:label="origin" inkscape:locked="true"/>'
    if adv:
        ink_guides += f'\n    <sodipodi:guide position="{ox + adv},0" orientation="1,0" inkscape:label="advance" inkscape:locked="true"/>'
    return f'''<svg xmlns="{SVG_NS}" xmlns:xlink="{XLINK_NS}" xmlns:inkscape="{INKSCAPE_NS}" xmlns:sodipodi="{SODIPODI_NS}"
     viewBox="0 0 {W} {H}" data-glyph="{gname}" data-family="{key}" data-origin="{ox} {oy}"
     data-upm="{M['upm']}" data-advance="{adv}">
  <title>Diafon {key} {gname}</title>
  <!-- Draw in the "glyph" layer; whatever is in the "cut" layer is cut out of it
       (shown half see-through; a spare square waits there, clear of the glyph);
       "guides" is locked and ignored on import.
       Font (0, 0) is at SVG ({ox}, {oy}); one unit is one font unit, {M['upm']} to the em,
       y up in the font. Fills only: holes by either fill rule, overlaps merged;
       strokes and text must become paths first. data-advance sets the advance
       width. Clones (<use>) of the symbols in <defs> resolve to their masters
       (_parts.svg, the other glyph files) at build time. -->
  <sodipodi:namedview id="namedview" inkscape:document-units="px" inkscape:current-layer="glyph"
     showguides="true" showgrid="false" inkscape:pagecheckerboard="0">
    <inkscape:grid type="xygrid" id="grid" spacingx="10" spacingy="10" originx="{ox}" originy="{oy}" empspacing="10"/>
{ink_guides}
  </sodipodi:namedview>
  <g id="guides" inkscape:groupmode="layer" inkscape:label="guides" sodipodi:insensitive="true">
{guide_layer(M, adv, ghosts, ox, oy, W, H)}
  </g>
  <g id="glyph" inkscape:groupmode="layer" inkscape:label="glyph">
{paths}
  </g>
  <g id="cut" inkscape:groupmode="layer" inkscape:label="cut" style="opacity:0.5">
    <path id="spare-cut" inkscape:label="spare cut" fill="{CUT}" d="M{ox + SPARE_CUT[0]} {oy}h100v-100h-100z"/>
  </g>
</svg>
'''


def export(key, names, on=(), force=False, font_path=None, out_dir=None):
    """Write fonts/svg/<family>/<glyph>.svg for each name; returns the paths."""
    from fontTools.ttLib import TTFont
    font = TTFont(font_path or font_for(key))
    M = metrics(font)
    out_dir = out_dir or os.path.join(SVG_ROOT, key)
    os.makedirs(out_dir, exist_ok=True)
    on_names = []
    for o in on:
        g = glyph_name(font, o)
        if g is None:
            print(f'  ?? --on {o}: no such glyph')
        else:
            on_names.append(g)
    anchors = ufo_anchors(key) if on_names and font_path is None else {}
    if on_names and not anchors:
        print('  (no UFO sources: the base letters are drawn at the origin, run fonts/build.sh for anchors)')
    written = []
    for arg in names:
        gname = glyph_name(font, arg)
        if gname is None:
            print(f'  ?? {arg}: no such glyph')
            continue
        path = os.path.join(out_dir, file_stem(font, gname) + '.svg')
        if os.path.exists(path) and not force:
            print(f'  {os.path.relpath(path, ROOT)} exists: an override already, --force to replace it')
            continue
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(glyph_svg(font, gname, key, M, on_names, anchors))
        written.append(path)
        print(f'  exported {os.path.relpath(path, ROOT)}')
    return written


def stems(svg_dir):
    """The override files of a folder, by stem: no variants (a `-` in the
    name after the glyph) and nothing starting with `_`."""
    return sorted(f[:-4] for f in os.listdir(svg_dir) if f.endswith('.svg') and not f.startswith('_'))


def glyph_layer(root, name='glyph'):
    for el in root:
        if local(el.tag) == 'g' and (el.get('id') == name or el.get(INKSCAPE + 'label') == name):
            return el
    return None


def is_guides(el):
    return el.get('id') == 'guides' or el.get(INKSCAPE + 'label') == 'guides'


def origin_of(root, default):
    o = root.get('data-origin')
    if o:
        x, y = o.split()
        return float(x), float(y)
    return default


def read_glyph(path, default_origin):
    """The glyph and cut layers of an SVG in font space: ([(RecordingPen,
    fill_rule, cut)], warnings, advance or None), cut true for the shapes of
    the cut layer, which are taken away from the merged ink. Clones resolve
    within the file; a file with no data-origin is the hand tools' canvas
    (viewBox at the ascent)."""
    root = ET.parse(path).getroot()
    ids = {el.get('id'): el for el in root.iter() if el.get('id')}
    origin = origin_of(root, default_origin)
    rules = css_rules(root)
    warnings, pieces = [], []
    layer = glyph_layer(root)

    def walk(el, ctm, st, doc, stack, cut=False):
        """doc: (ids, origin) of the document el belongs to — a master's
        clones resolve in the master's own space."""
        tag = local(el.tag)
        if tag == 'text':
            warnings.append(f'text#{el.get("id", "")} ignored (Path > Object to Path)')
            return
        if tag in SKIP or is_guides(el):
            return
        st = style_of(el, st, rules)
        if st.get('display') == 'none' or st.get('visibility') == 'hidden':
            return
        t = ctm.transform(parse_transform(el.get('transform')))
        if tag == 'svg' and el is not root:
            t = t.transform(nested_svg_transform(el))
        if tag in ('g', 'svg', 'a', 'switch'):
            for ch in el:
                walk(ch, t, st, doc, stack, cut)
            return
        if tag == 'use':
            href = (el.get(XLINK + 'href') or el.get('href') or '').lstrip('#')
            t = t.transform(Transform(1, 0, 0, 1, float(el.get('x', 0)), float(el.get('y', 0))))
            if href in stack:
                warnings.append(f'#{href} refers back to itself ({" > ".join(stack)})')
                return
            target, mdoc = doc[0].get(href), doc
            if target is None:
                warnings.append(f'clone of unknown #{href} skipped')
                return
            if local(target.tag) in ('symbol', 'svg'):
                for ch in target:
                    walk(ch, t, st, mdoc, stack + (href,), cut)
            else:
                walk(target, t, st, mdoc, stack + (href,), cut)
            return
        d = shape_d(el)
        if not d:
            return
        fill = parse_color(st.get('fill', 'black'))
        if fill is None or float(st.get('fill-opacity', 1) or 1) == 0:
            what = 'stroke-only' if parse_color(st.get('stroke', 'none')) else 'unfilled'
            warnings.append(f'{what} {tag}#{el.get("id", "")} skipped'
                            + (' (Path > Stroke to Path)' if what == 'stroke-only' else ''))
            return
        rec = RecordingPen()
        try:
            parse_path(d, TransformPen(rec, t))
        except Exception as e:
            warnings.append(f'unreadable {tag}#{el.get("id", "")}: {e}')
            return
        pieces.append((rec, st.get('fill-rule', 'nonzero'), cut))

    if layer is None:
        warnings.append('no "glyph" layer')
    else:
        to_font = Transform(1, 0, 0, -1, -origin[0], origin[1])
        walk(layer, to_font, {}, (ids, origin), ())
        cut_layer = glyph_layer(root, 'cut')
        if cut_layer is not None:
            walk(cut_layer, to_font, {}, (ids, origin), (), cut=True)
    adv = root.get('data-advance')
    return pieces, warnings, (int(round(float(adv))) if adv not in (None, '') else None)


def without_stubs(ops, reach=1.5):
    """The recording without segments that end, controls and all, within
    reach of where they start: the stubs two outlines touching along a curve
    leave where the merge splits them, a unit long and turning sharply once
    rounded."""
    out, here = [], None
    for op, pts in ops:
        if op in ('lineTo', 'curveTo', 'qCurveTo') and here is not None and \
                all(math.dist(p, here) < reach for p in pts):
            continue
        out.append((op, pts))
        if pts:
            here = pts[-1]
    return out


def outline(pieces, upm):
    """A TrueType glyph from the pieces: overlaps merged, the cut pieces taken
    away, either fill rule honoured, outer contours clockwise as TrueType
    wants, cubics to quadratics."""
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.cu2quPen import Cu2QuPen
    tt = TTGlyphPen(None)
    dst = Cu2QuPen(tt, max_err=upm / 1000)
    try:
        import pathops
    except ImportError:
        pathops = None
    if pathops and pieces:
        builder = pathops.OpBuilder(fix_winding=True, keep_starting_points=False)
        for rec, rule, cut in sorted(pieces, key=lambda p: p[2]):    # the ink, then the cuts
            p = pathops.Path()
            rec.replay(p.getPen())
            if rule == 'evenodd':
                p.fillType = pathops.FillType.EVEN_ODD
            p.simplify(fix_winding=True, keep_starting_points=False)
            probe = RecordingPen()
            p.draw(probe)
            cs = contours(probe)
            if cs and area(max(cs, key=lambda c: abs(area(c[1])))[1]) > 0:
                p.reverse()             # the builder keeps holes only under a clockwise outer
            builder.add(p, pathops.PathOp.DIFFERENCE if cut else pathops.PathOp.UNION)
        merged = builder.resolve()
        rec = RecordingPen()
        merged.draw(rec)
        cs = contours(rec)
        if any(abs(area(pts)) < 1 for _, pts in cs):    # crumbs of no area a join can leave
            merged = pathops.Path()
            for ops, pts in cs:
                if abs(area(pts)) >= 1:
                    replayRecording(ops, merged.getPen())
            cs = [c for c in cs if abs(area(c[1])) >= 1]
        if cs and area(max(cs, key=lambda c: abs(area(c[1])))[1]) > 0:
            merged.reverse()
        rec = RecordingPen()
        merged.draw(rec)
        replayRecording(without_stubs(rec.value), dst)
    else:
        for rec, _, cut in pieces:
            if not cut:
                rec.replay(dst)
    glyph = tt.glyph()
    rec = RecordingPen()
    glyph.draw(rec, None)
    cs = contours(rec)
    if any(abs(area(pts)) < 1 for _, pts in cs):        # crumbs that flatten to nothing as quadratics
        tt = TTGlyphPen(None)
        for ops, pts in cs:
            if abs(area(pts)) >= 1:
                replayRecording(ops, tt)
        glyph = tt.glyph()
    return glyph


def import_overrides(font, key='serif', svg_dir=None, skip=(), final=True, verbose=True):
    """Replace glyph outlines from fonts/svg/<family>/<glyph>.svg; called by
    build_font.py before the procedural glyphs (the marks that seed them,
    final=False) and after (the compositions). Files of glyphs the font does
    not have yet are left for the later pass, and reported by the final one.
    Returns the glyph names replaced."""
    svg_dir = svg_dir or os.path.join(SVG_ROOT, key)
    if not os.path.isdir(svg_dir):
        return []
    glyf, hmtx = font['glyf'], font['hmtx']
    upm = font['head'].unitsPerEm
    done = []
    for stem in stems(svg_dir):
        gname = stem_glyph(font, stem)
        if gname is None:           # a variant (n_uni0326-try.svg) or a stray file: inert
            if verbose and final:
                print(f'  svg override {stem}.svg: no glyph of that name, skipped')
            continue
        if gname in skip or gname not in glyf:
            continue
        try:
            pieces, warnings, adv = read_glyph(os.path.join(svg_dir, stem + '.svg'), (0, font['hhea'].ascent))
        except ET.ParseError as e:
            print(f'  ! {stem}.svg is not well-formed XML, skipped: {e}')
            continue
        glyph = outline(pieces, upm)
        glyf[gname] = glyph
        glyph.recalcBounds(glyf)
        old_adv = hmtx[gname][0] if gname in hmtx.metrics else 0
        hmtx[gname] = (adv if adv is not None else old_adv, getattr(glyph, 'xMin', 0))
        done.append(gname)
        if verbose:
            n = glyph.numberOfContours
            print(f'  svg override: {gname} ({stem}.svg, {n} contour{"s" if n != 1 else ""})')
            for w in warnings:
                print(f'    ! {w}')
    return done


def check(key, font_path=None, svg_dir=None, out=None):
    """Dry run: what the build would import, with its warnings, and a proof
    sheet fonts/build/svg-check-<family>.svg (the import in black over the
    font's current shape). Returns [(stem, glyph or None, contours, warnings)]."""
    from fontTools.ttLib import TTFont
    font = TTFont(font_path or font_for(key))
    M = metrics(font)
    upm = M['upm']
    svg_dir = svg_dir or os.path.join(SVG_ROOT, key)
    if not os.path.isdir(svg_dir):
        print(f'  no {os.path.relpath(svg_dir, ROOT)}')
        return []
    report, cells = [], []
    for stem in stems(svg_dir):
        try:
            ET.parse(os.path.join(svg_dir, stem + '.svg'))
        except ET.ParseError:
            report.append((stem, None, 0, ['not well-formed XML (the build skips it)']))
            continue
        gname = stem_glyph(font, stem)
        if gname is None:
            report.append((stem, None, 0, ['no glyph of that name (the build skips it)']))
            print(f'  {stem}.svg: no glyph of that name')
            continue
        pieces, warnings, adv = read_glyph(os.path.join(svg_dir, stem + '.svg'), (0, M['asc']))
        glyph = outline(pieces, upm)
        n = glyph.numberOfContours
        report.append((stem, gname, n, warnings))
        print(f'  {stem}.svg -> {gname}: {n} contour{"s" if n != 1 else ""}'
              + (f', advance {adv}' if adv is not None else ''))
        for w in warnings:
            print(f'    ! {w}')
        rec = RecordingPen()
        glyph.draw(rec, font['glyf'])
        cells.append((gname, rec, glyph_rec(font, gname), adv if adv is not None else font['hmtx'][gname][0]))
    out = out or os.path.join(ROOT, 'fonts', 'build', f'svg-check-{key}.svg')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cw, ch = 1400, M['asc'] - M['desc'] + 80
    rows = []
    for i, (gname, rec, ref, adv) in enumerate(cells):
        t = Transform(1, 0, 0, -1, 400 + (i % 2) * cw, 40 + M['asc'] + (i // 2) * ch)
        rows.append(f'<g><text x="{t.dx - 380}" y="{t.dy - M["asc"] + 24}" font-family="sans-serif" font-size="28">{gname}</text>'
                    + ''.join(f'<line x1="{t.dx - 400}" x2="{t.dx + 1000}" y1="{t.dy - y}" y2="{t.dy - y}" stroke="#9bd" stroke-width="1"/>'
                              for y in (0, M['xh'], M['cap'], M['descender']))
                    + f'<line x1="{t.dx}" x2="{t.dx}" y1="{t.dy - M["asc"]}" y2="{t.dy - M["desc"]}" stroke="#f80"/>'
                    + f'<line x1="{t.dx + adv}" x2="{t.dx + adv}" y1="{t.dy - M["asc"]}" y2="{t.dy - M["desc"]}" stroke="#f80" stroke-dasharray="8 6"/>'
                    + f'<path fill="#000" opacity="0.15" d="{path_d([o for o, _ in contours(ref)], t)}"/>'
                    + f'<path fill="#000" d="{path_d([o for o, _ in contours(rec)], t)}"/></g>')
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(f'<svg xmlns="{SVG_NS}" viewBox="0 0 {2 * cw} {max(1, (len(cells) + 1) // 2) * ch}">\n'
                 + '\n'.join(rows) + '\n</svg>\n')
    print(f'  proof: {os.path.relpath(out, ROOT)}')
    return report


# ------------------------------------------------------------------------ CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split('\n\n', 1)[1])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('export', help='write editable SVGs of glyphs')
    p.add_argument('family')
    p.add_argument('glyphs', nargs='+', help='glyph names, letters or codepoints (0324, U+0324)')
    p.add_argument('--on', nargs='*', default=[], metavar='GLYPH', help='ghost letters attached by anchor')
    p.add_argument('--force', action='store_true', help='replace an existing override')
    p.add_argument('--font', help='export from this font instead of the built one')
    p = sub.add_parser('check', help='dry-run the import and write a proof sheet')
    p.add_argument('family')
    p.add_argument('--font')
    a = ap.parse_args(argv)
    if a.cmd == 'export':
        export(a.family, a.glyphs, on=a.on, force=a.force, font_path=a.font)
    elif a.cmd == 'check':
        check(a.family, font_path=a.font)
    return 0


if __name__ == '__main__':
    sys.exit(main())
