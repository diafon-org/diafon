#!/usr/bin/env python3
"""Put the two drawn tails (fonts/hand/anchors/) on the letters that take
them, as fonts/svg/serif/<glyph>.svg overrides to fine-tune in Inkscape.

The anchor (U+0326, its foot reaching left) and the reverse (U+0316,
curling right) are the drawn shapes (fonts/hand/anchors/uni0316.svg and
uni0326.svg) at the middle weight, fonts/hand/anchors/middle/. Each is moved sideways only, its stem's top on the baseline
under the letter's right part (ATTACH): centred under the right stem, near
the end of the right foot, or at the underside's lowest point. Where the
letter's underside is curved, a connector fills between the tail's flat top
and the letter. Each file holds, in the glyph layer, the tail (TAIL_INK), the
connector (JOIN_INK) and the letter, untouched (black); the cut layer holds
the spare square for taking parts of the letter away.

    python3 fonts/tools/attach_tails.py              # every letter + mark the system uses
    python3 fonts/tools/attach_tails.py tT           # some letters (both marks where used)

It overwrites the files it writes: fine-tune after, not before, running it.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import font_svg as FS
import serif_tail as ST
import pathops
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

SHAPES = {0x0326: 'middle/anchor.svg', 0x0316: 'middle/reverse.svg'}   # mark -> its tail: the drawn
                                                  #   shapes at the middle weight (74 across the stroke)
USED = {0x0326: 'tskbnmdcxzTSKBNMDCXZ', 0x0316: 'tsndcxzTSNDCXZ'}
ATTACH = {}                                       # how each letter places the tail's top
ATTACH.update({L: 'stem' for L in 'nmhdNMHT'})    # centred under the right stem
ATTACH.update({L: 'foot' for L in 'kxzKXZBD'})    # near the right foot's end
ATTACH.update({L: 'low' for L in 'stcbSC'})       # at the underside's lowest point
FOOT_IN = 60                                      # 'foot': the top's centre this far in from the foot's end
# the joint (after t's, drawn by hand, tightened): the stem runs up to these
# heights (right, left edge), then flares out this far to meet the letter's
# underside, arriving along it, its handles HANDLE of the way long
JOINT_Y = (-12, -14)
FLARE = (35, 18)                                  # right, left
HANDLE = 0.3
PLACE = (-25, 55)                                 # 'low' letters: the stem's right edge, at this height, this far
TIP_Y = 6                                         #   left of the ink's far right at TIP_Y (where t's stem was drawn)
DONE = set('tskKbBnmNMdcxzTSDCXZ')                                # letters finished (or being finished) by hand: not rewritten
FLAGGED = {'s': 'joint drawn by hand, but not settled: waiting for a better idea'}
TAIL_INK, JOIN_INK = '#c8324e', '#e8912d'


def path_of(rec):
    p = pathops.Path(); rec.replay(p.getPen()); p.simplify(fix_winding=True); return p


def rect(x0, y0, x1, y1):
    r = pathops.Path(); p = r.getPen()
    p.moveTo((x0, y0)); p.lineTo((x1, y0)); p.lineTo((x1, y1)); p.lineTo((x0, y1)); p.closePath(); return r


def under(rec, step=2):
    """The region under a letter's underside: per column, from -1000 up to the
    lowest ink (and a unit into it)."""
    t = RecordingPen(); t.value = [(op, tuple((y, x) for x, y in pts)) for op, pts in rec.value]
    xs = [x for poly in ST.polys(rec) for x, _ in poly]
    p = pathops.Path(); pen = p.getPen()
    for x in range(int(min(xs)), int(max(xs)) + 1, step):
        ys = ST.crossings(t, x + step / 2)
        if ys:
            pen.moveTo((x, -1000)); pen.lineTo((x + step, -1000)); pen.lineTo((x + step, ys[0] + 1)); pen.lineTo((x, ys[0] + 1)); pen.closePath()
    p.simplify(fix_winding=True)
    return p


def underside(rec):
    """(y, direction) of the letter's underside at x: its lowest ink, or None."""
    t = RecordingPen(); t.value = [(op, tuple((y, x) for x, y in pts)) for op, pts in rec.value]
    def y_at(x):
        ys = ST.crossings(t, x)
        return ys[0] if ys else None
    def at(x):
        y = y_at(x)
        if y is None: return None
        a, b = y_at(x - 3), y_at(x + 3)
        if a is None or b is None or abs(a - b) > 20: return y, (1.0, 0.0)
        n = ((6) ** 2 + (b - a) ** 2) ** 0.5
        return y, (6 / n, (b - a) / n)
    return at


def joint(tail_p, rec, letter_p):
    """The joint drawn on t, on this letter: the stem's edges run up to
    JOINT_Y and flare out FLARE, along the letter's underside; a flare that
    would land where there is no ink near the baseline is shortened, or left
    out. Returns the region from 60 below up into the letter."""
    edge = lambda y, side: (max if side else min)(ST.crossings(rec_from(tail_p), y))
    under_at = underside(rec)
    pts = {}
    for side, y0, reach in ((1, JOINT_Y[0], FLARE[0]), (0, JOINT_Y[1], FLARE[1])):
        x0 = edge(y0, side); x1 = edge(y0 - 40, side)
        up = ((x0 - x1) / 40, 1.0); n = (up[0] ** 2 + 1) ** 0.5; up = (up[0] / n, up[1] / n)
        target = None
        for r in range(reach, 0, -4):
            tx = x0 + r if side else x0 - r
            u = under_at(tx)
            if u is not None and u[0] <= 15:
                target = (tx, u[0], u[1] if side else (-u[1][0], -u[1][1])); break
        pts[side] = (x0, y0, up, target, x1)
    p = pathops.Path(); pen = p.getPen()
    xr0, yr0, upr, tr, _ = pts[1]; xl0, yl0, upl, tl, _ = pts[0]
    pen.moveTo((edge(-60, 1), -60)); pen.lineTo((xr0, yr0))
    if tr:
        k = HANDLE * ((tr[0] - xr0) ** 2 + (tr[1] - yr0) ** 2) ** 0.5
        pen.curveTo((xr0 + k * upr[0], yr0 + k * upr[1]), (tr[0] - k * tr[2][0], tr[1] - k * tr[2][1]), (tr[0], tr[1]))
        pen.lineTo((tr[0], tr[1] + 18))
    else:
        pen.lineTo((xr0 + 50 * upr[0], yr0 + 50 * upr[1]))
    if tl:
        pen.lineTo((tl[0], tl[1] + 18)); pen.lineTo((tl[0], tl[1]))
        k = HANDLE * ((tl[0] - xl0) ** 2 + (tl[1] - yl0) ** 2) ** 0.5
        pen.curveTo((tl[0] - k * tl[2][0], tl[1] - k * tl[2][1]), (xl0 + k * upl[0], yl0 + k * upl[1]), (xl0, yl0))
    else:
        pen.lineTo((xl0 + 50 * upl[0], yl0 + 50 * upl[1])); pen.lineTo((xl0, yl0))
    pen.lineTo((edge(-60, 0), -60)); pen.closePath()
    p.simplify(fix_winding=True)
    keep = pathops.op(pathops.op(rect(-2000, -2000, 3000, 0), letter_p, pathops.PathOp.UNION), under(rec), pathops.PathOp.UNION)
    p = pathops.op(p, keep, pathops.PathOp.INTERSECTION)   # above the baseline, only within the letter
    return p, bool(tr), bool(tl)


def rec_from(p):
    r = RecordingPen(); p.draw(r); return r


def attach_x(rec, letter):
    """Where the centre of the tail's top goes, on the baseline."""
    how = ATTACH[letter]
    if how == 'stem':
        a, b = ST.vertical_stems(rec)[-1]
        return (a + b) / 2
    if how == 'foot':
        return max(ST.crossings(rec, 2)) - FOOT_IN
    t = RecordingPen(); t.value = [(op, tuple((y, x) for x, y in pts)) for op, pts in rec.value]
    xs = [x for poly in ST.polys(rec) for x, _ in poly]
    low = [(ST.crossings(t, x)[0], x) for x in range(int(min(xs)), int(max(xs)), 2) if ST.crossings(t, x)]
    y0 = min(y for y, _ in low)
    near = [x for y, x in low if y <= y0 + 2]
    return (min(near) + max(near)) / 2


def tail_shape(mark):
    """The drawn tail (glyph layer only) and the span of its top on the baseline."""
    pieces, _, _ = FS.read_glyph(os.path.join(FS.ROOT, 'fonts', 'hand', 'anchors', SHAPES[mark]), (0, 1069))
    rec = RecordingPen()
    for r, _, cut in pieces:
        if not cut:
            r.replay(rec)
    xs = ST.crossings(rec, -1)
    return rec, (min(xs), max(xs))


def write(font, letter, mark, shape, span):
    cmap = font.getBestCmap(); M = FS.metrics(font)
    gname = cmap[ord(letter)]; comp = f'{gname}_uni{mark:04X}'
    rec = FS.glyph_rec(font, gname)
    dx = attach_x(rec, letter) - (span[0] + span[1]) / 2
    if ATTACH[letter] == 'low':                       # as on t: the right flare ends at the ink's far right
        right_now = max(ST.crossings(shape, PLACE[0]))
        dx = max(ST.crossings(rec, TIP_Y)) - PLACE[1] - right_now
    tail = RecordingPen(); shape.replay(TransformPen(tail, (1, 0, 0, 1, dx, 0)))
    letter_p = path_of(rec)
    tail_p = path_of(tail)
    j, has_r, has_l = joint(tail_p, rec, letter_p)
    tail_p = pathops.op(pathops.op(tail_p, rect(-2000, -2000, 3000, JOINT_Y[0] + 3), pathops.PathOp.INTERSECTION),
                        j, pathops.PathOp.UNION)
    tail_p.simplify(fix_winding=True)
    tail = rec_from(tail_p)
    jr = RecordingPen()
    FS.export('serif', [comp], font_path=font.reader.file.name, force=True)
    path = os.path.join(FS.SVG_ROOT, 'serif', FS.file_stem(font, comp) + '.svg')
    ox, oy, W, H = FS.canvas(M); to_svg = Transform(1, 0, 0, -1, ox, oy)
    d = lambda r: FS.path_d([o for o, _ in FS.contours(ST.tidy(r))], to_svg)
    shapes = [f'    <path id="tail" fill="{TAIL_INK}" d="{d(tail)}"/>']
    if jr.value:
        shapes.append(f'    <path id="join" fill="{JOIN_INK}" d="{d(jr)}"/>')
    shapes.append(f'    <path id="letter" fill="#111" d="{d(rec)}"/>')
    text = open(path).read()
    text = re.sub(r'(<g id="glyph"[^>]*>)\n.*?(\n  </g>)', lambda m: m.group(1) + '\n' + '\n'.join(shapes) + m.group(2), text, flags=re.S)
    open(path, 'w').write(text)
    pieces, warnings, _ = FS.read_glyph(path, (0, M['asc']))
    n = FS.outline(pieces, M['upm']).numberOfContours
    print(f'  {os.path.relpath(path, FS.ROOT)}: stem at x {span[0] + dx:.0f}..{span[1] + dx:.0f} ({ATTACH[letter]}), '
          f'flares {"right " if has_r else ""}{"left" if has_l else ""}, {n} contour{"s" if n != 1 else ""}'
          + (f' ! {warnings}' if warnings else ''))


def main(argv):
    for L, why in FLAGGED.items():
        print(f'  flagged: {L} ({why})')
    font = TTFont(os.path.join(FS.ROOT, 'fonts', 'build', 'DiafonSerif-derived.ttf'))
    only = argv[0] if argv else None
    for mark in (0x0326, 0x0316):
        shape, span = tail_shape(mark)
        for L in USED[mark]:
            if (only is None and L not in DONE) or (only is not None and L in only):
                write(font, L, mark, shape, span)


if __name__ == '__main__':
    main(sys.argv[1:])
