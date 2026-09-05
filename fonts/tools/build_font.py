#!/usr/bin/env python3
"""Build fonts/Diaphone-Regular.ttf from NotoSerif-Regular.ttf (SIL OFL 1.1).

Subset Noto Serif to the system's character set (from docs/fonts-data.js —
regenerate that first), then apply the glyph surgery:

- the ANCHOR (U+0326) and the reverse anchor (U+0316): a rotated copy of the
  font's acute, elongated, attached to the letter — now ending in a SERIF
  FOOT, the same terminal the font's own descenders wear;
- the comma above (U+0313) and NEW its mirror (U+0314), upright acutes;
- NEW the double dot below (U+0324): two copies of the font's dot below;
- NEW precomposed ḷ ṃ ṿ ẍ ẗ, composed like their existing siblings.

Any fonts/svg/<glyph>.svg present still replaces a seed at build time
(fonts/tools/font_svg.py). After building run fonts/tools/subset_web.py to
refresh docs/diaphone.woff2.
"""
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'fonts', 'NotoSerif-Regular.ttf')
OUT = os.path.join(ROOT, 'fonts', 'Diaphone-Regular.ttf')

BASIC = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
         " .,;:!?()[]/-–—'\"·")

# anchor geometry lives in fonts/anchor.yaml — the precise-instruction file

NEW_PRECOMPOSED = {         # cp: (base, mark, above?)
    0x1E37: ('l', 'dotbelowcomb', False),   # ḷ
    0x1E43: ('m', 'dotbelowcomb', False),   # ṃ
    0x1E7F: ('v', 'dotbelowcomb', False),   # ṿ
    0x1E8D: ('x', 'dieresis', True),        # ẍ
    0x1E97: ('t', 'dieresis', True),        # ẗ
}


def charset():
    src = open(os.path.join(ROOT, 'docs', 'fonts-data.js')).read()
    data = json.loads(re.search(r'const MATRIX = (.*);', src).group(1))
    chars = set(BASIC)
    for sec in data.values():
        for row in sec['rows']:
            for cell in row['cells']:
                if cell:
                    for form in ('NFC', 'NFD'):
                        chars.update(unicodedata.normalize(form, cell['g']))
                        chars.update(unicodedata.normalize(form, cell['g'].upper()))
    return {c for c in chars if not unicodedata.category(c).startswith('C')}


def _outline(glyphset, name):
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    rec = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(rec)
    pts = [pt for op, args in rec.value for pt in args if isinstance(pt, tuple)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return rec, (min(xs) + max(xs)) / 2, min(ys), max(ys)


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


def _anchor_glyphs(font):
    """The anchor family: rotated acute strokes with a serif foot at the tip."""
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.misc.transform import Transform

    import yaml as _yaml
    P = _yaml.safe_load(open(os.path.join(ROOT, 'fonts', 'anchor.yaml')))
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
    put(0x0313, stroke(0x0313, above=True), 0x0313)        # comma above
    put(0x0314, stroke(0x0313, mirror=True, above=True), 0x0313)   # NEW mirror above

    # NEW U+0324: two copies of the font's dot below
    dot, d_cx, _, _ = _outline(gs, 'dotbelowcomb')
    sep = 0.145 * upm
    pen = TTGlyphPen(None)
    for off in (-sep / 2, sep / 2):
        dot.replay(TransformPen(pen, Transform(1, 0, 0, 1, off, 0)))
    put(0x0324, pen.glyph(), 0x0323)
    _clone_gpos_mark(font, cmap[0x0313], 'uni0314')
    _clone_gpos_mark(font, cmap[0x0323], 'uni0324')
    print(f"  anchor family ({P['mode']}): attach {top} tip {tip} serif {2*sw:.0f}x{st:.0f}; 0314/0324 created")


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


def build():
    from fontTools.ttLib import TTFont
    from fontTools.subset import Subsetter, Options

    chars = charset()
    font = TTFont(SRC)
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

    _anchor_glyphs(font)
    _precomposed(font)

    svg_mod = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'font_svg.py')
    if os.path.exists(svg_mod):
        import importlib.util
        spec = importlib.util.spec_from_file_location('font_svg', svg_mod)
        font_svg = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(font_svg)
            font_svg.import_overrides(font)
        except Exception as e:
            print(f'  (svg overrides skipped: {e})')

    name = font['name']
    for nid, val in {1: 'Diaphone', 4: 'Diaphone Regular',
                     6: 'Diaphone-Regular', 16: 'Diaphone'}.items():
        name.setName(val, nid, 3, 1, 0x409)
        name.setName(val, nid, 1, 0, 0)
    cp0 = name.getDebugName(0) or ''
    name.setName(cp0 + ' Diaphone is a derivative work (SIL OFL 1.1); reserved font names removed.',
                 0, 3, 1, 0x409)
    name.setName('SIL Open Font License 1.1 — see fonts/OFL.txt', 13, 3, 1, 0x409)

    font.save(OUT)
    print(f'wrote {os.path.relpath(OUT, ROOT)} · {font["maxp"].numGlyphs} glyphs · '
          f'GPOS {"kept" if "GPOS" in font else "MISSING"}')
    return 0


if __name__ == '__main__':
    sys.exit(build())
