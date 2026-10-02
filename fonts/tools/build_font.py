#!/usr/bin/env python3
"""Derive fonts/build/<Family>-derived.ttf from its Noto face (SIL OFL 1.1).

    python3 fonts/tools/build_font.py [serif|sans|mono]     (fonts/families.yaml)

The first step of fonts/build.sh: make_ufo.py turns the result into the UFO
sources and fontmake compiles those into the shipping fonts/<Family>-Regular.ttf.

Subset Noto Serif to the system's character set (from fonts/glyphs.js —
regenerate that first), then apply the glyph surgery:

- the ANCHOR (U+0326) and the reverse anchor (U+0316): a rotated copy of the
  font's acute, elongated, attached to the letter — now ending in a SERIF
  FOOT, the same terminal the font's own descenders wear;
- the comma above (U+0313) and NEW its mirror (U+0314), upright acutes;
- NEW the double dot below (U+0324): two copies of the font's dot below;
- NEW precomposed ḷ ṃ ṿ, composed like their existing siblings.

The text is the composition (base letter + the system's combining marks,
NFC), so the font carries the marks with their attachment and the baked
letter+mark pairs behind ccmp; no letter is remapped to another codepoint.

Any fonts/svg/<family>/<glyph>.svg present replaces that glyph at build time
(fonts/tools/font_svg.py): the marks before the procedural glyphs they seed,
the compositions after. fonts/build.sh carries on to the shipping fonts.
"""
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAMILIES = os.path.join(ROOT, 'fonts', 'families.yaml')


def family(key='serif'):
    """The family record from fonts/families.yaml with derived paths:
    source, family, after, anchor (overrides), ps (PostScript family),
    derived (the intermediate), ufo, ttf (the shipping font)."""
    import yaml as _yaml
    fams = _yaml.safe_load(open(FAMILIES))
    if key not in fams:
        raise SystemExit(f'no family {key!r}; families: {", ".join(fams)}')
    f = dict(fams[key])
    f['key'] = key
    f['ps'] = f['family'].replace(' ', '')
    f['source'] = os.path.join(ROOT, 'fonts', f['source'])
    f['derived'] = os.path.join(ROOT, 'fonts', 'build', f"{f['ps']}-derived.ttf")
    f['ufo'] = os.path.join(ROOT, 'fonts', 'sources', f"{f['ps']}-Regular.ufo")
    f['ttf'] = os.path.join(ROOT, 'fonts', f"{f['ps']}-Regular.ttf")
    f.setdefault('anchor', {})
    return f


def family_keys():
    import yaml as _yaml
    return list(_yaml.safe_load(open(FAMILIES)))

REPO = 'https://github.com/blagasz/diaphone'
COPYRIGHT = ('Copyright 2026 The Diafon Project Authors (' + REPO + '), portions Copyright 2022 '
             'The Noto Project Authors (https://github.com/notofonts/latin-greek-cyrillic) '
             'with Reserved Font Name "Noto"')   # = the first line of fonts/OFL.txt
LICENSE_TEXT = ('This Font Software is licensed under the SIL Open Font License, Version 1.1. '
                'This license is available with a FAQ at: https://openfontlicense.org')

BASIC = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
         " .,;:!?()[]/-–—'\"·")

# anchor geometry lives in fonts/anchor.yaml — the precise-instruction file

NEW_PRECOMPOSED = {         # cp: (base, mark, above?)
    0x1E37: ('l', 'dotbelowcomb', False),   # ḷ
    0x1E43: ('m', 'dotbelowcomb', False),   # ṃ
    0x1E7F: ('v', 'dotbelowcomb', False),   # ṿ
}                                            # ẍ ẗ (the special above x t) left with the old float rule


def charset():
    src = open(os.path.join(ROOT, 'fonts', 'glyphs.js')).read()
    data = json.loads(re.search(r'const MATRIX = (.*);', src).group(1))
    chars = set(BASIC)
    for sec in data.values():
        for row in sec['rows']:
            for cell in row['cells']:
                if cell:
                    for form in ('NFC', 'NFD'):
                        chars.update(unicodedata.normalize(form, cell['g']))
                        chars.update(unicodedata.normalize(form, cell['g'].upper()))
    # Google Fonts' minimum: the GF Latin Core set (from the glyphsets package
    # when installed; the build fails loudly if the source lacks any of it),
    # the no-break space and the dotted circle marks attach to when orphaned
    try:
        import glyphsets
        chars.update(chr(c) for c in glyphsets.unicodes_per_glyphset('GF_Latin_Core'))
    except ImportError:
        print('  (glyphsets not installed: GF Latin Core not enforced)')
    chars.update('\u00A0\u25CC')
    # every mark the script defines stays in the font: the reserve composes
    # with them, and the anchor family is derived from the source marks
    import yaml as _yaml
    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, str):
            chars.update(node)
    walk(_yaml.safe_load(open(os.path.join(ROOT, 'data', 'script.yaml')))['marks'])
    return {c for c in chars if not unicodedata.category(c).startswith('C')}


def _outline(glyphset, name):
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    rec = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(rec)
    pts = [pt for op, args in rec.value for pt in args if isinstance(pt, tuple)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return rec, (min(xs) + max(xs)) / 2, min(ys), max(ys)


def _part_mid(pts, xh, above):
    """The middle of the part of a letter a mark sits against: its upper part
    for marks above (j: the stem, not the tail), its lower part for marks
    below (r: the stem, t: stem and tail); the whole letter as a fallback."""
    part = [p for p in pts if (p[1] >= xh * 0.6 if above else p[1] <= xh * 0.35)] or pts
    return (min(p[0] for p in part) + max(p[0] for p in part)) / 2


def _acute_axis(a_rec):
    """The acute's foot and head: the middles of its bottom and top terminals."""
    pts = [pt for op, args in a_rec.value for pt in args if isinstance(pt, tuple)]
    ymin, ymax = min(p[1] for p in pts), max(p[1] for p in pts)
    band = 0.15 * (ymax - ymin)
    low = [p[0] for p in pts if p[1] <= ymin + band]
    high = [p[0] for p in pts if p[1] >= ymax - band]
    return ((min(low) + max(low)) / 2, ymin, (min(high) + max(high)) / 2, ymax)


def _above_transform(S, a_rec, a_cx, a_ymin, mirror, mid, foot, dy=0):
    """The above-anchor: the vowels' long acute stretched by above_scale along
    its own stroke (longer, not heavier), mirrored for the reverse. With
    above_start set its foot stands at `foot` and it rises outward; otherwise
    it is centred on `mid` (the old form)."""
    import math
    from fontTools.misc.transform import Transform
    asc = S.get('above_scale', 1.0)
    fx, fy, hx, hy = _acute_axis(a_rec)
    ang = math.atan2(hy - fy, hx - fx)
    stretch = (Transform().translate(fx, fy).rotate(ang).scale(asc, 1)
               .rotate(-ang).translate(-fx, -fy))    # about the foot, along the axis
    pts = [stretch.transformPoint(pt) for op, args in a_rec.value
           for pt in args if isinstance(pt, tuple)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    s_cx, s_ymin = (min(xs) + max(xs)) / 2, min(ys)
    sx = -1 if mirror else 1
    x0, ax = (mid, s_cx) if S.get('above_start') is None else (foot, fx)
    place = Transform(sx, 0, 0, 1, x0 - sx * ax, dy + a_ymin - s_ymin)
    return place.transform(stretch)


def _above_foot(S, xmin, xmax, left):
    """Where the above-anchor's foot stands on a letter spanning xmin..xmax:
    above_start of the way across, from the left for the anchor and from the
    right for the reverse (0.5 = the letter's middle)."""
    frac = S.get('above_start') or 0.5
    return xmax - frac * (xmax - xmin) if left else xmin + frac * (xmax - xmin)


def _mark_anchor(font, name):
    """(x, y) of a mark glyph's GPOS attachment point, or None."""
    if 'GPOS' not in font:
        return None
    for lookup in font['GPOS'].table.LookupList.Lookup:
        if lookup.LookupType != 4:
            continue
        for sub in lookup.SubTable:
            cov = getattr(sub, 'MarkCoverage', None)
            if cov and name in cov.glyphs:
                a = sub.MarkArray.MarkRecord[cov.glyphs.index(name)].MarkAnchor
                return a.XCoordinate, a.YCoordinate
    return None


def _bake_glyph(font, name, glyph, bname):
    """Store a baked glyph: the base letter's advance, its own left bearing
    (a mark reaching left of the letter would otherwise shift the whole
    glyph downstream), registered in the glyph order."""
    glyf, hmtx = font['glyf'], font['hmtx']
    glyf[name] = glyph
    glyph.recalcBounds(glyf)
    hmtx[name] = (hmtx[bname][0], getattr(glyph, 'xMin', hmtx[bname][1]))
    _register(font, name)


def _register(font, name):
    order = font.getGlyphOrder()
    if name not in order:
        order.append(name)
    go = font['glyf'].glyphOrder
    if go is not order and name not in go:
        go.append(name)


def _clone_gpos_mark(font, model, new):
    """Give a new mark glyph the same GPOS attachment records as its model."""
    if 'GPOS' not in font:
        return
    n = 0
    for lookup in font['GPOS'].table.LookupList.Lookup:
        for sub in lookup.SubTable:
            for covname, arrname, recname in (
                    ('MarkCoverage', 'MarkArray', 'MarkRecord'),
                    ('Mark1Coverage', 'Mark1Array', 'MarkRecord'),
                    ('Coverage', None, None)):
                cov = getattr(sub, covname, None)
                if cov is None or model not in cov.glyphs or new in cov.glyphs:
                    continue
                if arrname is None:
                    cov.glyphs.append(new)
                    n += 1
                    continue
                idx = cov.glyphs.index(model)
                arr = getattr(sub, arrname)
                import copy
                rec = copy.deepcopy(arr.MarkRecord[idx])
                cov.glyphs.append(new)
                arr.MarkRecord.append(rec)
                arr.MarkCount = len(arr.MarkRecord)
                n += 1
    print(f'  GPOS: {new} inherits {n} attachment records from {model}')


ANCHOR_MARKS = {0x0326, 0x0316, 0x0313, 0x0314}


def _anchor_pairs():
    """(base letter, anchor mark cp) pairs the system's glyph matrix uses."""
    src = open(os.path.join(ROOT, 'fonts', 'glyphs.js')).read()
    data = json.loads(re.search(r'const MATRIX = (.*);', src).group(1))
    pairs = set()
    for sec in data.values():
        for row in sec['rows']:
            for cell in row['cells']:
                if not cell:
                    continue
                s = unicodedata.normalize('NFD', cell['g'])
                for i, ch in enumerate(s):
                    prev = s[i - 1] if i else ''
                    if ord(ch) in ANCHOR_MARKS and 'a' <= prev <= 'z':
                        pairs.add((prev, ord(ch)))
    # the full principled set: below marks on every anchorable letter, above
    # marks on the descenders and g (the float rule); l r f never anchor.
    # Capitals inherit their small form's side.
    for ch in 'bcdghjkmnpqstvxyz':
        marks = (0x0313, 0x0314) if ch in 'gjpqy' else (0x0326, 0x0316)
        pairs.update((ch, m) for m in marks)
        pairs.update((ch.upper(), m) for m in (0x0326, 0x0316))  # caps never float
    return sorted(pairs)


def _add_ccmp_ligatures(font, mapping):
    """base+mark -> baked glyph, appended to the ccmp feature."""
    if not mapping or 'GSUB' not in font:
        return
    from fontTools.otlLib.builder import buildLigatureSubstSubtable
    from fontTools.ttLib.tables import otTables as ot
    st = buildLigatureSubstSubtable(mapping)
    lookup = ot.Lookup()
    lookup.LookupType, lookup.LookupFlag = 4, 0
    lookup.SubTable, lookup.SubTableCount = [st], 1
    gsub = font['GSUB'].table
    gsub.LookupList.Lookup.append(lookup)
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)
    idx = gsub.LookupList.LookupCount - 1
    feats = [fr.Feature for fr in gsub.FeatureList.FeatureRecord
             if fr.FeatureTag == 'ccmp']
    if not feats:
        fr = ot.FeatureRecord()
        fr.FeatureTag = 'ccmp'
        fr.Feature = ot.Feature()
        fr.Feature.FeatureParams = None
        fr.Feature.LookupListIndex, fr.Feature.LookupCount = [], 0
        gsub.FeatureList.FeatureRecord.append(fr)
        gsub.FeatureList.FeatureCount = len(gsub.FeatureList.FeatureRecord)
        fidx = gsub.FeatureList.FeatureCount - 1
        for sr in gsub.ScriptList.ScriptRecord:
            for ls in ([sr.Script.DefaultLangSys]
                       + [r.LangSys for r in sr.Script.LangSysRecord]):
                if ls:
                    ls.FeatureIndex.append(fidx)
                    ls.FeatureCount = len(ls.FeatureIndex)
        feats = [fr.Feature]
    for f in feats:
        f.LookupListIndex.append(idx)
        f.LookupCount = len(f.LookupListIndex)


def _flatten(rec, n=8):
    """The closed polylines of a recorded outline, curves subdivided."""
    polys, cur = [], []
    for op, args in rec.value:
        if op == 'moveTo':
            cur = [args[0]]
        elif op == 'lineTo':
            cur.append(args[0])
        elif op in ('qCurveTo', 'curveTo'):
            pts = list(args)
            if pts[-1] is None:                  # all-off-curve contour
                pts[-1] = ((pts[0][0] + pts[-2][0]) / 2, (pts[0][1] + pts[-2][1]) / 2)
                cur = cur or [pts[-1]]
            p0 = cur[-1]
            if op == 'curveTo':
                a, b, p3 = pts
                for k in range(1, n + 1):
                    t, u = k / n, 1 - k / n
                    cur.append((u**3 * p0[0] + 3 * u * u * t * a[0] + 3 * u * t * t * b[0] + t**3 * p3[0],
                                u**3 * p0[1] + 3 * u * u * t * a[1] + 3 * u * t * t * b[1] + t**3 * p3[1]))
                continue
            ctrls, end = pts[:-1], pts[-1]
            for i, c in enumerate(ctrls):        # implied on-curve points between controls
                p2 = end if i == len(ctrls) - 1 else ((c[0] + ctrls[i + 1][0]) / 2, (c[1] + ctrls[i + 1][1]) / 2)
                for k in range(1, n + 1):
                    t, u = k / n, 1 - k / n
                    cur.append((u * u * p0[0] + 2 * u * t * c[0] + t * t * p2[0],
                                u * u * p0[1] + 2 * u * t * c[1] + t * t * p2[1]))
                p0 = p2
        elif op in ('closePath', 'endPath'):
            if cur:
                polys.append(cur)
            cur = []
    if cur:
        polys.append(cur)
    return polys


def _poly(out, pts):
    """A closed polygon, emitted clockwise (a TrueType outer contour)."""
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    if area > 0:
        pts = pts[::-1]
    out.moveTo(pts[0])
    for q in pts[1:]:
        out.lineTo(q)
    out.closePath()


def _hook(pen, rec, mx, left, S, depth, hw, tw, xh):
    """The hook (stroke.hook set): a curved tail like the logo's. It leaves
    the letter's bottom outer corner `leave` degrees off vertical, its outer
    edge flush with the corner and its head buried `bite` deep in the letter,
    and bends one way toward the letter's middle, to land lean_frac of the
    way there (at most `reach` across) with its foot at `depth`, in a round
    cap (or flat). The width eases from the head to the foot. The buried head
    follows the letter's own edge above the corner (stem, slanted leg or
    terminal cut), so nothing shows beside the join. Drawn on the right; the
    reverse anchor is the same construction mirrored.

    Per-letter keys (stroke.letters in families.yaml): `leave: along` makes
    the hook continue the letter's own edge with no kink (a stem: straight
    down; x's leg: along its slant), as wide as that stroke where its flat
    bottom edge gives the width, and `bend: [k0, k1]` sets the curve's
    handle lengths as fractions of the spine — a long k0 and a short k1 keep
    it nearly straight and tighten the bend toward the foot; `rise` starts
    the bend that high up in the stem, the stem below it giving way to the
    hook (the caller cuts it, see the returned quad); `extend` first
    lengthens the letter's terminal along its own direction and the hook
    leaves the extended end; `back_along` grows the anchor out of the
    letter's own underside that far back from the far tip along its outline
    (the reverse anchor: from the right tip, then down and to the right; the
    anchor: from the left tip, then down and to the left), in one bend."""
    import math
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.reverseContourPen import ReverseContourPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.misc.transform import Transform
    H = S['hook']
    ext, back = S.get('extend', 0), S.get('back_along')
    mirror = left != bool(back)      # the search frame: the anchor's own side, or,
    flip = Transform(-1, 0, 0, 1, 0, 0)   # growing back from the far tip, the other
    m = flip if mirror else Transform()
    polys = [[m.transformPoint(p) for p in poly] for poly in _flatten(rec)]
    mxw = -mx if mirror else mx                     # work on the right side
    a0 = math.radians(H.get('leave', 10))
    d0 = (-math.sin(a0), -math.cos(a0))             # down and inward
    n0 = (math.cos(a0), -math.sin(a0))              # the outer edge's normal
    cands = [(pi, i) for pi, poly in enumerate(polys) for i, p in enumerate(poly)
             if p[1] <= xh * 0.35] or [(pi, i) for pi, poly in enumerate(polys)
                                       for i in range(len(poly))]
    pi, i = max(cands, key=lambda c: polys[c[0]][c[1]][0] * n0[0] + polys[c[0]][c[1]][1] * n0[1])
    poly = polys[pi]
    ex, ey = poly[i]                                 # the corner
    up = max((poly[i - 1], poly[(i + 1) % len(poly)]), key=lambda p: p[1])  # the edge above it
    ux, uy = up[0] - ex, up[1] - ey
    if uy <= 1e-6:
        ux, uy = 0.0, 1.0                           # nothing above: straight up
    bl = min(S['bite'] / uy, 2 * S['bite'] / math.hypot(ux, uy))   # rise `bite`, or so
    u = (ux * bl, uy * bl)
    leave = S.get('leave', H.get('leave', 10))
    cut = None
    if leave == 'along':                             # continue the letter's own edge
        a0 = math.atan2(ux, uy)
        d0, n0 = (-math.sin(a0), -math.cos(a0)), (math.cos(a0), -math.sin(a0))
        other = poly[i - 1] if up == poly[(i + 1) % len(poly)] else poly[(i + 1) % len(poly)]
        bw = math.hypot(other[0] - ex, other[1] - ey) * math.cos(a0)   # the stroke's width,
        if 30 <= bw <= 200 and abs(other[1] - ey) < 8:   # from its flat bottom edge: match it
            tw, hw = tw * (bw / 2) / hw, bw / 2
        rise = S.get('rise', 0)
        if rise:    # the bend starts up in the stem: the head moves up its edge
            # and the stem below is cut away, the hook (same width, same
            # direction) taking its place — the caller subtracts `cut`
            ul_ = math.hypot(ux, uy)
            uu = (ux / ul_, uy / ul_)
            along_ = (other[0] - ex, other[1] - ey)   # across the stem's bottom
            al_ = math.hypot(*along_) or 1.0
            pad = (along_[0] / al_ * 3, along_[1] / al_ * 3)
            lo = -40
            cut = [(ex - pad[0] + uu[0] * lo, ey - pad[1] + uu[1] * lo),
                   (other[0] + pad[0] + uu[0] * lo, other[1] + pad[1] + uu[1] * lo),
                   (other[0] + pad[0] + uu[0] * rise, other[1] + pad[1] + uu[1] * rise),
                   (ex - pad[0] + uu[0] * rise, ey - pad[1] + uu[1] * rise)]
            if mirror:
                cut = [(-x_, y_) for x_, y_ in cut]
            ex, ey = ex + uu[0] * rise, ey + uu[1] * rise
    elif 'leave' in S:
        a0 = math.radians(leave)
        d0, n0 = (-math.sin(a0), -math.cos(a0)), (math.cos(a0), -math.sin(a0))
    k0, k1 = S.get('bend', (1 / 3, 1 / 3))          # handle lengths, as fractions of the spine
    out = TransformPen(Cu2QuPen(pen, 1.0), m)
    if mirror:                                       # keep the winding clockwise
        out = ReverseContourPen(out)
    corner, step = (ex, ey), (1 if poly[i - 1] == up else -1)   # back along the underside
    if ext and not back:                             # the terminal, lengthened:
        # a band as wide as the cut face sweeps on from it, curling up by `curl`
        fw = math.hypot(ux, uy) / 2
        t0 = (uy / (2 * fw), -ux / (2 * fw))         # along the terminal, outward
        if t0[0] < 0:
            t0 = (-t0[0], -t0[1])
        ph = math.radians(S.get('curl', 0))
        t1 = (t0[0] * math.cos(ph) - t0[1] * math.sin(ph), t0[0] * math.sin(ph) + t0[1] * math.cos(ph))
        nn0, nn1 = (-t0[1], t0[0]), (-t1[1], t1[0])   # the bands' upper normals
        m0 = ((ex + up[0]) / 2, (ey + up[1]) / 2)
        m1 = (m0[0] + (t0[0] + t1[0]) / 2 * ext, m0[1] + (t0[1] + t1[1]) / 2 * ext)
        q1 = (m0[0] + t0[0] * ext / 3, m0[1] + t0[1] * ext / 3)
        q2 = (m1[0] - t1[0] * ext / 3, m1[1] - t1[1] * ext / 3)
        off = lambda pt, n, w: (pt[0] + n[0] * w, pt[1] + n[1] * w)
        lo1, hi1 = off(m1, nn1, -fw), off(m1, nn1, fw)
        out.moveTo((ex, ey))                         # clockwise: up the face, out
        out.lineTo(up)                               # along the top, back along the bottom
        out.curveTo(off(q1, nn0, fw), off(q2, nn1, fw), hi1)
        out.lineTo(lo1)
        out.curveTo(off(q2, nn1, -fw), off(q1, nn0, -fw), (ex, ey))
        out.closePath()
        ex, ey = lo1
        ux, uy = hi1[0] - lo1[0], hi1[1] - lo1[1]     # the new end face
        bl = min(S['bite'] / max(uy, 1e-6), 2 * S['bite'] / math.hypot(ux, uy))
        u = (ux * bl, uy * bl)
    travel = min(S['lean_frac'] * (ex - mxw), H.get('reach', 1e9))
    if back:    # the anti anchor: grows out of the letter's own underside,
        # `back_along` back from the tip along its outline, as the hook mirrored
        path, acc, j, n_ = [corner], 0.0, i, 0
        while acc < back and n_ < len(poly):
            j, n_ = j + step, n_ + 1
            q = poly[j % len(poly)]
            if q[1] > path[-1][1] + 12:               # the outline climbs (a crotch,
                continue                              # a counter): bridge straight under it
            d_ = math.hypot(q[0] - path[-1][0], q[1] - path[-1][1])
            if acc + d_ > back:                      # trim the last step
                r = (back - acc) / d_
                q = (path[-1][0] + (q[0] - path[-1][0]) * r, path[-1][1] + (q[1] - path[-1][1]) * r)
                d_ = back - acc
            path.append(q)
            acc += d_
        E = path[-1]
        out = TransformPen(Cu2QuPen(pen, 1.0), flip if left else Transform())   # the hook, on
        if left:                                     # its own side (the output frame is
            out = ReverseContourPen(out)             # the search frame flipped)
        ex, ey = hw - E[0], E[1]                     # its head centred on E, buried straight up
        u = (0.0, float(S['bite']))
        mxw = ex - travel / S['lean_frac'] if S['lean_frac'] else ex
    hx, hy = ex - n0[0] * hw, ey - n0[1] * hw       # spine head: outer edge through the corner
    cap = H.get('cap', 'round') == 'round'
    fy = depth + (tw if cap else 0)
    dy = hy - fy
    dirn = lambda a: ((-math.sin(a), -math.cos(a)), (math.cos(a), -math.sin(a)))
    # the spine: cubic segments (p0, p1, p2, p3, normal at each end, width at each end)
    if True:    # one-way bend, landing `travel` inward
        a1 = max(a0, 2 * math.atan2(max(travel, 0), max(dy, 1)) - a0)
        d1, n1 = dirn(a1)
        L = dy / ((math.cos(a0) + math.cos(a1)) / 2)
        fx = hx - L * (math.sin(a0) + math.sin(a1)) / 2
        segs = [((hx, hy), (hx + d0[0] * L * k0, hy + d0[1] * L * k0),
                 (fx - d1[0] * L * k1, fy - d1[1] * L * k1), (fx, fy), n0, n1, hw, tw)]
    side = lambda pt, n, w, sg: (pt[0] + sg * n[0] * w, pt[1] + sg * n[1] * w)
    hl, hr = side((hx, hy), n0, hw, -1), side((hx, hy), n0, hw, 1)
    hl2 = hl                                          # where the head's inner edge
    if hl[1] < ey - 1e-6:                            # meets the corner's level (a hook
        s_ = (ey - hl[1]) / math.cos(a0)             # leaving outward would otherwise
        hl2 = (hl[0] + math.sin(a0) * s_, ey)        # hang below the letter's foot)
    tl, tr = (hl2[0] + u[0], hl2[1] + u[1]), (ex + u[0], ey + u[1])   # buried
    # head: a band up along the letter's edge, inside the ink there
    out.moveTo(tl)
    out.lineTo(tr)
    out.lineTo(hr)
    for p0, p1, p2, p3, nA, nB, wA, wB in segs:      # down the outer edge
        out.curveTo(side(p1, nA, wA + (wB - wA) / 3, 1), side(p2, nB, wA + (wB - wA) * 2 / 3, 1),
                    side(p3, nB, wB, 1))
    fl = side((fx, fy), n1, tw, -1)
    if cap:                                          # a semicircle, two quarters
        k = 0.5523 * tw
        fr = side((fx, fy), n1, tw, 1)
        b = (fx + d1[0] * tw, fy + d1[1] * tw)
        out.curveTo((fr[0] + d1[0] * k, fr[1] + d1[1] * k),
                    (b[0] + n1[0] * k, b[1] + n1[1] * k), b)
        out.curveTo((b[0] - n1[0] * k, b[1] - n1[1] * k),
                    (fl[0] + d1[0] * k, fl[1] + d1[1] * k), fl)
    else:
        out.lineTo(fl)
    for p0, p1, p2, p3, nA, nB, wA, wB in reversed(segs):   # back up the inner edge
        out.curveTo(side(p2, nB, wA + (wB - wA) * 2 / 3, -1), side(p1, nA, wA + (wB - wA) / 3, -1),
                    side(p0, nA, wA, -1))
    if hl2 != hl:
        out.lineTo(hl2)
    out.lineTo(tl)
    out.closePath()
    return cut


def _above_hook(pen, S, foot, mirror):
    """The above-anchor of the hook families (stroke.above_hook): the acute
    with a little bend like the anchor's. From its foot (a flat cut, floating
    `gap` above the letter, at the letter's upper-part middle) it rises to
    the right, `leave` degrees off vertical, and bends over to `swing` at the
    tip, `rise` up, in a round cap; the width eases foot_w -> tip_w.
    Mirrored about the foot for the reverse."""
    import math
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.reverseContourPen import ReverseContourPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.misc.transform import Transform
    A = S['above_hook']
    a0, a1 = math.radians(A.get('leave', 30)), math.radians(A.get('swing', 62))
    d0, d1 = (math.sin(a0), math.cos(a0)), (math.sin(a1), math.cos(a1))   # up and right
    n0, n1 = (math.cos(a0), -math.sin(a0)), (math.cos(a1), -math.sin(a1))  # the right side
    wf, wt = A.get('foot_w', 76) / 2, A.get('tip_w', 60) / 2
    rise = A.get('rise', 200) - wt
    L = rise / ((math.cos(a0) + math.cos(a1)) / 2)
    fx, fy = foot
    tx, ty = fx + L * (d0[0] + d1[0]) / 2, fy + rise
    k0, k1 = A.get('bend', (0.4, 0.4))
    c1 = (fx + d0[0] * L * k0, fy + d0[1] * L * k0)
    c2 = (tx - d1[0] * L * k1, ty - d1[1] * L * k1)
    side = lambda pt, n, w, sg: (pt[0] + sg * n[0] * w, pt[1] + sg * n[1] * w)
    w1, w2 = wf + (wt - wf) * k0, wf + (wt - wf) * (1 - k1)
    out = TransformPen(Cu2QuPen(pen, 1.0), Transform(-1, 0, 0, 1, 2 * fx, 0) if mirror else Transform())
    if mirror:
        out = ReverseContourPen(out)
    fl, fr = side(foot, n0, wf, -1), side(foot, n0, wf, 1)
    tl, tr = side((tx, ty), n1, wt, -1), side((tx, ty), n1, wt, 1)
    out.moveTo(fr)                                   # clockwise: the foot, up the left
    out.lineTo(fl)                                   # edge, over the cap, down the right
    out.curveTo(side(c1, n0, w1, -1), side(c2, n1, w2, -1), tl)
    k = 0.5523 * wt
    b = (tx + d1[0] * wt, ty + d1[1] * wt)
    out.curveTo((tl[0] + d1[0] * k, tl[1] + d1[1] * k), (b[0] - n1[0] * k, b[1] - n1[1] * k), b)
    out.curveTo((b[0] + n1[0] * k, b[1] + n1[1] * k), (tr[0] + d1[0] * k, tr[1] + d1[1] * k), tr)
    out.curveTo(side(c2, n1, w2, 1), side(c1, n0, w1, 1), fr)
    out.closePath()


def _joined(glyph, pinhole=90):
    """A letter with its anchor as one outline: overlaps merged, and any
    pinhole the join leaves (a tiny counter closed off between a bowl, its
    stem and the anchor's head) filled. Contours smaller than `pinhole`
    units both ways are pinholes; a letter has none that small."""
    from pathops import Path
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    path = Path()
    glyph.draw(path.getPen(), None)
    path.simplify(fix_winding=True, keep_starting_points=True)
    out = Path()
    for c in path.contours:
        x0, y0, x1, y1 = c.bounds
        if x1 - x0 < pinhole and y1 - y0 < pinhole:
            continue
        c.draw(out.getPen())
    pen = TTGlyphPen(None)
    out.draw(Cu2QuPen(pen, 1.0))
    return pen.glyph()


def _bake_strokes(font, gs, cmap, P, xh):
    """Per-letter anchors: from the letter's outer bottom point, slanted
    toward its middle, to descender depth, serifed at the tip; the head bites
    into the letter to absorb its serif. With stroke.hook set (sans, mono)
    the tail is the logo's curved hook instead (_hook). The above-anchors of
    the float rule are the vowels' long acute (_above_transform)."""
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.misc.transform import Transform
    S = P['stroke']
    head_w, tw = S['head_w'], S['tip_w'] / 2
    lean, bite = S['lean_frac'], S['bite']
    sw, st = P['serif']['w'] / 2, P['serif']['t']
    depth = (_outline(gs, cmap[ord(S['depth'])])[2] if isinstance(S['depth'], str)
             else S['depth'])   # a letter names its own descender depth
    a_rec, a_cx, a_ymin, _ = _outline(gs, cmap[0x0301])
    ascale = S.get('above_scale', 1.0)
    astart = S.get('above_start')
    glyf, hmtx = font['glyf'], font['hmtx']
    liga = {}
    for base, mark in _anchor_pairs():
        bname = cmap.get(ord(base))
        if bname is None:
            continue
        mname = cmap.get(mark) or f'uni{mark:04X}'
        rec, _, _, bymax = _outline(gs, bname)
        pts = [pt for op, args in rec.value for pt in args if isinstance(pt, tuple)]
        mx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
        above = mark in (0x0313, 0x0314)
        left = mark in (0x0316, 0x0314)
        pen = TTGlyphPen(None)
        rec.replay(pen)
        if above and S.get('hook') and S.get('above_hook'):
            # the hook families: the acute with a little bend, floating `gap`
            # above the letter, its foot at the upper-part middle
            part = [p for p in pts if p[1] >= xh * 0.6] or pts
            fx = _above_foot(S, min(p[0] for p in part), max(p[0] for p in part), left)
            _above_hook(pen, S, (fx, bymax + S['above_hook'].get('gap', 70)), left)
        elif above:   # the vowels' long acute, mirrored for the reverse, its
            # foot at above_start across the letter rising outward (or centred);
            # lifted over letters taller than the x-height (the capitals)
            dy = max(0, bymax - xh)
            foot = _above_foot(S, min(p[0] for p in pts), max(p[0] for p in pts), left)
            a_rec.replay(TransformPen(pen, _above_transform(
                S, a_rec, a_cx, a_ymin, left, mx, foot, dy)))
        elif S.get('hook'):
            SL, ov = dict(S), (S.get('letters') or {}).get(base) or {}
            SL.update({k: v for k, v in ov.items() if k != 'reverse'})
            if left:
                SL.update(ov.get('reverse') or {})
            d2 = depth if SL['depth'] == S['depth'] else (
                _outline(gs, cmap[ord(SL['depth'])])[2] if isinstance(SL['depth'], str) else SL['depth'])
            if SL.get('rise') and SL.get('leave') == 'along':
                from pathops import Path, op, PathOp
                from fontTools.pens.cu2quPen import Cu2QuPen
                letter, hookp, cutp = Path(), Path(), Path()
                rec.replay(letter.getPen())
                cut = _hook(hookp.getPen(), rec, mx, left, SL, d2, SL['head_w'] / 2, SL['tip_w'] / 2, xh)
                if cut:
                    cp = cutp.getPen()
                    cp.moveTo(cut[0])
                    for q in cut[1:]:
                        cp.lineTo(q)
                    cp.closePath()
                    letter = op(letter, cutp, PathOp.DIFFERENCE)
                res = op(letter, hookp, PathOp.UNION)
                res.simplify(fix_winding=True, keep_starting_points=True)
                pen = TTGlyphPen(None)
                res.draw(Cu2QuPen(pen, 1.0))
            else:
                _hook(pen, rec, mx, left, SL, d2, SL['head_w'] / 2, SL['tip_w'] / 2, xh)
        else:
            zone = [p for p in pts if p[1] <= xh * 0.35] or pts
            edge = (min if left else max)(p[0] for p in zone)
            tx = edge + lean * (mx - edge)
            h1, h2 = sorted((edge, edge + head_w if left else edge - head_w))
            # the head bites `bite` up into the letter's own ink where it
            # stands: under a round bottom (s c b d) the outline sits well
            # above the baseline there, and a head at a fixed height floats
            col = [p[1] for poly in _flatten(rec) for p in poly
                   if h1 - 2 <= p[0] <= h2 + 2 and p[1] <= xh * 0.6]
            top = (min(col) if col else 0) + bite
            ys = depth + st
            poly = [(h1, top), (h2, top), (tx + tw, ys), (tx + sw, ys),
                    (tx + sw, depth), (tx - sw, depth), (tx - sw, ys),
                    (tx - tw, ys)]
            pen.moveTo(poly[0])
            for p in poly[1:]:
                pen.lineTo(p)
            pen.closePath()
        name = f'{bname}_uni{mark:04X}'
        glyph = pen.glyph() if above else _joined(pen.glyph())
        _bake_glyph(font, name, glyph, bname)
        liga[(bname, mname)] = name
    # the double dot below (0324), centred on the letter's lower part; the
    # double acute (030B): the gap between its strokes, at their feet, at
    # double_acute.gap_at of the way across the letter's upper part; the
    # vowels' acute and grave (0301 0300), the foot at acute_grave.foot_at
    # likewise (bbox-centred when a knob is absent); the seed is the font's
    # final (svg-curated) mark
    gsl = font.getGlyphSet()
    da_at = (P.get('double_acute') or {}).get('gap_at')
    ag_at = (P.get('acute_grave') or {}).get('foot_at')
    VOWELS = 'aeiou' + 'AEIOU'
    DOTTED = 'ạẹịọụ' + 'ẠẸỊỌỤ'         # the lowered vowels take the same marks
    CONS = 'bcdfghjklmnpqrstvxz'
    for seed_name, mark, letters in (
            (cmap.get(0x0324, 'uni0324'), 0x0324,
             'bcdfhklmnrstvxz' + 'bcdfhklmnrstvxz'.upper() + 'GP'),
            (cmap.get(0x0308), 0x0308, CONS + CONS.upper()),   # r̈ p̈ j̈ … centred on
            #   the upper part (j: the stem, not the tail); i j lose their tittle
            ('hungarumlaut', 0x030B, VOWELS),
            (cmap.get(0x0301), 0x0301, VOWELS + DOTTED),
            (cmap.get(0x0300), 0x0300, VOWELS + DOTTED)):
        if seed_name not in gsl:
            continue
        s_rec, s_cx, _, _ = _outline(gsl, seed_name)
        above = mark in (0x030B, 0x0301, 0x0300, 0x0308)
        feet_at = da_at if mark == 0x030B else (ag_at if mark in (0x0301, 0x0300) else None)
        if above and feet_at is not None:
            # the gap between the two strokes where they start, at their feet
            # (the strokes lean right: their tops sit well right of their feet)
            polys = _flatten(s_rec)
            feet = []
            for poly in polys:
                ymin, ymax = min(p[1] for p in poly), max(p[1] for p in poly)
                low = [p[0] for p in poly if p[1] <= ymin + 0.15 * (ymax - ymin)]
                feet.append((min(low) + max(low)) / 2)
            s_gap = sum(feet) / len(feet)
        mname = cmap.get(mark) or f'uni{mark:04X}'
        for ch in letters:
            bname = cmap.get(ord(ch))
            if bname is None:
                continue
            rec, mx, _, bymax = _outline(gsl, bname)
            pts = [pt for op, args in rec.value for pt in args if isinstance(pt, tuple)]
            bxmin, bxmax = min(p[0] for p in pts), max(p[0] for p in pts)
            mx = _part_mid(pts, xh, above)   # the part the mark sits against
            pen = TTGlyphPen(None)
            dotted_i = unicodedata.normalize('NFD', ch)[0] in 'ij'
            if dotted_i and above:             # the tittle yields to the mark
                cur, kept = [], []
                for op, args in rec.value:
                    cur.append((op, args))
                    if op in ('closePath', 'endPath'):
                        cpts = [pt for o, a in cur for pt in a
                                if isinstance(pt, tuple)]
                        if not cpts or min(p[1] for p in cpts) < xh:
                            kept.extend(cur)
                        cur = []
                for op, args in kept:
                    getattr(pen, op)(*args)
                body = [pt for o, a in kept for pt in a if isinstance(pt, tuple)]
                bymax = max(p[1] for p in body)            # the body, not the tittle
                bxmin, bxmax = min(p[0] for p in body), max(p[0] for p in body)
                mx = _part_mid(body, xh, True)
            else:
                rec.replay(pen)
            dy = max(0, bymax - xh) if above else 0
            if above and feet_at is not None:
                part = [p for p in pts if p[1] >= xh * 0.6] or pts
                pxmin, pxmax = min(p[0] for p in part), max(p[0] for p in part)
                if dotted_i:
                    pxmin, pxmax = bxmin, bxmax
                dx = pxmin + feet_at * (pxmax - pxmin) - s_gap
            else:
                dx = mx - s_cx
            s_rec.replay(TransformPen(pen, Transform(1, 0, 0, 1, dx, dy)))
            name = f'{bname}_uni{mark:04X}'
            _bake_glyph(font, name, pen.glyph(), bname)
            liga[(bname, mname)] = name
            if ch in 'ij' and above:
                # the font's own ccmp turns i j dotless before our lookup runs
                for dn in (('dotlessi', 'uni0131') if ch == 'i' else ('uni0237', 'dotlessj')):
                    if dn in gsl:
                        liga[(dn, mname)] = name
                        break
            nfc = unicodedata.normalize('NFC', ch + chr(mark))
            if len(nfc) == 1 and ord(nfc) in cmap:      # the precomposed letter
                for table in font['cmap'].tables:        # (á ő Ù …) draws the baked form
                    if table.isUnicode():
                        table.cmap[ord(nfc)] = name
    _add_ccmp_ligatures(font, liga)
    for cp, base, mark in ((0x0219, 's', '0326'), (0x021B, 't', '0326'),
                           (0x0151, 'o', '030B'), (0x0171, 'u', '030B'),
                           (0x0218, 'S', '0326'), (0x021A, 'T', '0326'),
                           (0x0150, 'O', '030B'), (0x0170, 'U', '030B')):
        name = f'{cmap[ord(base)]}_uni{mark}'   # precomposed ș ț ő ű Ș Ț Ő Ű
        if name in glyf and cp in cmap:
            for table in font['cmap'].tables:
                if table.isUnicode():
                    table.cmap[cp] = name
    print(f'  baked: {len(liga)} pairs (anchors, double dots, double acutes'
          + (f' gap at {da_at} of the letter' if da_at is not None else '') + ') · '
          f'depth {depth:.0f}{" · hook" if S.get("hook") else ""} · above = acute x{ascale}'
          + (f' from {astart} of the letter' if astart is not None else ' centred'))


def _anchor_glyphs(font, skip_0324=False):
    """The anchor family: rotated acute strokes with a serif foot at the tip."""
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.misc.transform import Transform

    import yaml as _yaml
    P = _yaml.safe_load(open(os.path.join(ROOT, 'fonts', 'anchor.yaml')))
    for k, v in (font.diafon_family.get('anchor') or {}).items():   # per-family overrides
        if isinstance(v, dict) and isinstance(P.get(k), dict):
            P[k].update(v)
        else:
            P[k] = v
    glyf, cmap = font['glyf'], font.getBestCmap()
    upm = font['head'].unitsPerEm
    gs = font.getGlyphSet()
    _, _, _, xh = _outline(gs, cmap[ord('x')])
    top, tip = P['attach'], P['tip']
    sw, st = P['serif']['w'] / 2, P['serif']['t']

    seed = RecordingPen()
    if P['mode'] == 'comma':
        # the typeface's own comma, centred, raised to attach, stretched to tip
        comma, c_cx, c_ymin, c_ymax = _outline(gs, cmap[0x0326])
        sy = (top - tip) / (c_ymax - c_ymin)
        t = Transform(P['width'], 0, 0, sy, -P['width'] * c_cx, top - sy * c_ymax)
        rec = RecordingPen()
        comma.replay(TransformPen(rec, t))
        rec.replay(seed)
        if sw > 0:
            pts = [pt for op, args in rec.value for pt in args if isinstance(pt, tuple)]
            tx = min(pts, key=lambda p: p[1])[0]
            seed.moveTo((tx - sw, tip + st)); seed.lineTo((tx + sw, tip + st))
            seed.lineTo((tx + sw, tip)); seed.lineTo((tx - sw, tip)); seed.closePath()
    else:
        w1, w2 = P['wedge']['top_w'] / 2, P['wedge']['tip_w'] / 2
        lean = P['wedge']['lean']
        seed.moveTo((-w1, top))
        seed.lineTo((w1, top))
        seed.lineTo((lean + w2, tip + st))
        seed.lineTo((lean + sw, tip + st))
        seed.lineTo((lean + sw, tip))
        seed.lineTo((lean - sw, tip))
        seed.lineTo((lean - sw, tip + st))
        seed.lineTo((lean - w2, tip + st))
        seed.closePath()

    def stroke(target_cp, mirror=False, above=False):
        _, cx, _, _ = _outline(gs, cmap[target_cp]) if target_cp in cmap else (None, 0, 0, 0)
        pen = TTGlyphPen(None)
        sx = -1 if mirror else 1
        if above:   # the below anchor rotated 180°, attached at the letter-body top
            t = Transform(-sx, 0, 0, -1, cx, xh - P['above']['embed'] + top)
        else:
            t = Transform(sx, 0, 0, 1, cx, 0)
        seed.replay(TransformPen(pen, t))
        return pen.glyph()

    def put(cp, glyph, model_cp):
        """Map cp to a glyph, creating the slot if the font lacks it."""
        name = cmap.get(cp)
        if name is None:
            name = f'uni{cp:04X}'
            model = cmap[model_cp]
            font['hmtx'][name] = font['hmtx'][model]
            glyf[name] = glyph
            _register(font, name)
            for table in font['cmap'].tables:
                if table.isUnicode():
                    table.cmap[cp] = name
        else:
            glyf[name] = glyph
        return name

    put(0x0326, stroke(0x0326), 0x0326)                    # the anchor, serifed
    put(0x0316, stroke(0x0316, mirror=True), 0x0316)       # reverse anchor, serifed
    if P['mode'] == 'stroke':   # bare above marks: the vowels' long acute,
        # moved into the frame of the mark's own attachment point so it
        # lands where the acute would (the mark keeps 0313's GPOS records)
        a_rec, a_cx, a_ymin, _ = _outline(gs, cmap[0x0301])
        a_a = _mark_anchor(font, cmap[0x0301]) or (a_cx, a_ymin)
        m_a = _mark_anchor(font, cmap[0x0313]) or a_a
        shift = Transform(1, 0, 0, 1, m_a[0] - a_a[0], m_a[1] - a_a[1])
        def acute_mark(mirror=False):
            pen = TTGlyphPen(None)
            t = _above_transform(P['stroke'], a_rec, a_cx, a_ymin, mirror,
                                 a_a[0], a_a[0])   # on the acute's own anchor
            a_rec.replay(TransformPen(pen, shift.transform(t)))
            return pen.glyph()
        put(0x0313, acute_mark(), 0x0313)
        put(0x0314, acute_mark(True), 0x0313)
    else:
        put(0x0313, stroke(0x0313, above=True), 0x0313)        # comma above
        put(0x0314, stroke(0x0313, mirror=True, above=True), 0x0313)   # mirror above

    # U+0324: the diaeresis's own two dots, set below — their gap the
    # diaeresis's times double_dot_below.gap, their top `top` below the
    # baseline, centred on the dot below's attachment point
    if not skip_0324:
        D = P.get('double_dot_below') or {}
        dots, dd_cx, _, dd_ymax = _outline(gs, cmap[0x0308])
        ax, ay = _mark_anchor(font, cmap[0x0323]) or (_outline(gs, 'dotbelowcomb')[1], 0)
        polys = _flatten(dots)
        cxs = [(min(p[0] for p in poly) + max(p[0] for p in poly)) / 2 for poly in polys]
        pen = TTGlyphPen(None)
        cur, i = [], 0
        for op, args in dots.value:      # each contour: its own horizontal shift
            cur.append((op, args))
            if op in ('closePath', 'endPath'):
                off = (cxs[i] - dd_cx) * (D.get('gap', 1.0) - 1)
                t = Transform(1, 0, 0, 1, ax - dd_cx + off, ay + D.get('top', -59) - dd_ymax)
                tp = TransformPen(pen, t)
                for o, a in cur:
                    getattr(tp, o)(*a)
                cur, i = [], i + 1
        put(0x0324, pen.glyph(), 0x0323)
    _clone_gpos_mark(font, cmap[0x0313], 'uni0314')
    _clone_gpos_mark(font, cmap[0x0323], 'uni0324')
    print(f"  anchor family ({P['mode']}): attach {top} tip {tip} serif {2*sw:.0f}x{st:.0f}; 0314/0324 created")
    if P['mode'] == 'stroke':
        _bake_strokes(font, gs, cmap, P, xh)


def _font_svg():
    """fonts/tools/font_svg.py as a module, or None (the overrides are then skipped)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'font_svg.py')
    if not os.path.exists(path):
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location('font_svg', path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f'  (svg overrides skipped: {e})')
        return None
    return mod


def _precomposed(font):
    """Compose the missing precomposed letters as composites."""
    from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent
    glyf, cmap, hmtx = font['glyf'], font.getBestCmap(), font['hmtx']
    gs = font.getGlyphSet()
    for cp, (base, mark, above) in NEW_PRECOMPOSED.items():
        if cp in cmap:
            continue
        name = f'uni{cp:04X}'
        _, b_cx, _, b_ymax = _outline(gs, base)
        _, m_cx, _, _ = _outline(gs, mark)
        dx = b_cx - m_cx
        dy = 0
        if above:
            _, _, _, xh = _outline(gs, cmap[ord('x')])
            dy = max(0, b_ymax - xh)        # lift the mark over tall letters (ẗ)
        g = Glyph()
        g.numberOfContours = -1
        comp_b = GlyphComponent(); comp_b.glyphName = base
        comp_b.x, comp_b.y = 0, 0; comp_b.flags = 0x204
        comp_m = GlyphComponent(); comp_m.glyphName = mark
        comp_m.x, comp_m.y = int(dx), int(dy); comp_m.flags = 0x004
        g.components = [comp_b, comp_m]
        glyf[name] = g
        hmtx[name] = hmtx[base]
        _register(font, name)
        for table in font['cmap'].tables:
            if table.isUnicode():
                table.cmap[cp] = name
    print(f'  precomposed added: {" ".join(chr(c) for c in NEW_PRECOMPOSED)}')


def build(key='serif'):
    from fontTools.ttLib import TTFont
    from fontTools.subset import Subsetter, Options

    fam = family(key)
    chars = charset()
    font = TTFont(fam['source'])
    font.diafon_family = fam
    cmap = font.getBestCmap()
    needed = {ord(c) for c in chars}
    creatable = set(NEW_PRECOMPOSED) | {0x0314, 0x0324}
    missing = sorted(c for c in needed if c not in cmap and c not in creatable)
    if missing:
        print('MISSING from source font:', [f'U+{c:04X}' for c in missing])
        return 1

    opts = Options()
    opts.layout_features = ['*']
    opts.name_IDs = ['*']
    opts.notdef_outline = True
    opts.glyph_names = True
    ss = Subsetter(opts)
    ss.populate(unicodes=sorted((needed - creatable) | {0x0301}))
    ss.subset(font)

    # svg overrides FIRST, so every baked composition copies the curated marks;
    # again after the procedural glyphs, for the compositions curated as a whole
    font_svg = _font_svg()
    svg_done = font_svg.import_overrides(font, fam['key'], final=False) if font_svg else []
    _anchor_glyphs(font, skip_0324='uni0324' in svg_done)
    _precomposed(font)
    if font_svg:
        svg_done += font_svg.import_overrides(font, fam['key'], skip=set(svg_done))

    # the name table, to Google Fonts' rules: a single-style family carries no
    # typographic family name; the copyright is the first line of OFL.txt
    name = font['name']
    for nid in (16, 17):
        name.removeNames(nameID=nid)
    for nid, val in {1: fam['family'], 4: fam['family'] + ' Regular', 6: fam['ps'] + '-Regular',
                     0: COPYRIGHT, 13: LICENSE_TEXT, 14: 'https://openfontlicense.org',
                     3: 'Diafon Project;' + fam['ps'] + '-Regular'}.items():
        name.removeNames(nameID=nid)
        name.setName(val, nid, 3, 1, 0x409)
        name.setName(val, nid, 1, 0, 0)
    font['head'].flags |= 1 << 3          # hinted: round ppem to integers
    font['OS/2'].fsType = 0               # installable embedding

    os.makedirs(os.path.dirname(fam['derived']), exist_ok=True)
    font.save(fam['derived'])
    print(f'wrote {os.path.relpath(fam["derived"], ROOT)} ({fam["family"]}, after {fam["after"]}) · '
          f'{font["maxp"].numGlyphs} glyphs · GPOS {"kept" if "GPOS" in font else "MISSING"}')
    return 0


if __name__ == '__main__':
    sys.exit(build(*sys.argv[1:2]))
