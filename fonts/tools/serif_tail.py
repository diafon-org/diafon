"""The serif anchor tail (fonts/svg/serif): the right stem runs on below the
baseline in one even arc from right under the arch, thinning a little, and
lands on a one-sided plate foot, inward for the anchor (U+0326) and outward
for the anti-anchor (U+0316); the letter's stem and foot give way to the
tail, and its other feet lose the half that faces the tail, cut to a slanted
spur. Letters without such a stem get the tail appended at their right side
(LETTERS). The numbers were read off a hand
drawn n; the tail is grown from each letter's own stem, so it fits any width.

    python3 fonts/tools/serif_tail.py            # every letter of ALL, both marks -> fonts/svg/serif/<glyph>.svg
    python3 fonts/tools/serif_tail.py nH         # some of them

Then fonts/build.sh serif. The written files are ordinary overrides: edit
them in Inkscape, or change a number here and regenerate. Each keeps the
letter whole, in black, and shows the change apart: what the tail adds in
TAIL_INK, and what is taken away from the letter in the cut layer, CUT_INK."""
import sys, re, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import font_svg as FS
ROOT = FS.ROOT
from fontTools.ttLib import TTFont
from fontTools.misc.transform import Transform
from fontTools.misc.bezierTools import splitCubicAtT, solveCubic, cubicPointAtT, quadraticPointAtT
from fontTools.pens.recordingPen import RecordingPen, replayRecording
import pathops

START_Y = 345          # the stem gives way to the tail this high up, right under the arch (vertical tangent there)
ANG = math.radians(25) # landing angle off vertical
K0, K1 = 0.45, 0.35    # handle lengths as fractions of the edge: one long even arc
LAND_IN = 192          # the inner edge lands this far left of the stem's inner edge
TIP_W = 0.85           # the tail's width at the foot, as a fraction of the stem's
SLAB = 94              # the foot's plate beyond the landed edge (inward: left; outward: right)
REACH = 25             # the bracket lands this far along the plate from the edge
BR = 45                # bracket height
DEPTH, SH = -330, 42   # plate bottom, height
TOP = DEPTH + SH
SPUR = (16, 50)        # every other stem's foot half facing the tail is cut to a spur: the
                       #   cut runs from this far beyond the stem at the baseline to this
                       #   far at the plate's top (a slant leaning outward going up)
WIDTH = ((-60, 84), (-230, 63))   # every tail's stroke, across it: this thick under the letter,
                                  #   tapering evenly to this at the foot (read off the hand drawn s k b)
TAIL_INK = '#c8324e'   # the tail's colour in the written SVGs (any fill is ink to the build)
CUT_INK = FS.CUT        # the cut's (the cut layer shows it half see-through)
d1 = (-math.sin(ANG), -math.cos(ANG))

def cubic(p0, p3):
    L = math.hypot(p3[0]-p0[0], p3[1]-p0[1])
    return (p0, (p0[0], p0[1]-K0*L), (p3[0]-d1[0]*K1*L, p3[1]-d1[1]*K1*L), p3)
def upper_part(c, y):
    a=(-c[0][1]+3*c[1][1]-3*c[2][1]+c[3][1]); b=(3*c[0][1]-6*c[1][1]+3*c[2][1]); cc=(-3*c[0][1]+3*c[1][1]); d=(c[0][1]-y)
    t=[t for t in solveCubic(a,b,cc,d) if 0<t<1][0]; return splitCubicAtT(*c, t)[0]
def tang(c):
    t=(c[3][0]-c[2][0], c[3][1]-c[2][1]); l=math.hypot(*t); return (t[0]/l, t[1]/l)
def bracket(end_x, j, t, br):
    """From (end_x, TOP) on the slab, leaving horizontal, up into the edge at j
    along its tangent t."""
    return ((float(end_x), float(TOP)), (end_x+(j[0]-end_x)*0.5, float(TOP)), (j[0]+t[0]*br*0.5, j[1]+t[1]*br*0.5), j)
def rev(c): return (c[3],c[2],c[1],c[0])

def tail_path(xi, xo, foot='in', start=START_Y, full=False, foot_w=None):
    """The tail for a stem with inner edge xi and outer edge xo, as a
    pathops.Path: one even arc from START_Y, thinning to TIP_W of the stem,
    landing at ANG on a plate foot at DEPTH. `in` (the anchor): the plate
    runs inward, to the left, with a small bracket up into the inner edge,
    and the outer edge runs straight on through the plate to its bottom
    corner. `out` (the anti-anchor): the mirror, the plate outward with the
    bracket up into the outer edge, the inner edge running on through."""
    XI = xi - (LAND_IN if full else LAND_IN * (start-TOP) / (START_Y-TOP))   # the reach scales with the drop, unless full
    global d1
    ang = max(ANG, math.atan2(xi-XI, start-TOP) + math.radians(5))   # a short drop lands steeper: no S-bend
    d1 = (-math.sin(ang), -math.cos(ang))
    XO = XI + (foot_w if foot_w else TIP_W*(xo-xi))/math.cos(ang)
    inner_c = cubic((float(xi), float(start)), (float(XI), float(TOP)))
    outer_c = cubic((float(xo), float(start)), (float(XO), float(TOP)))
    run = SH * math.tan(ang)                 # the edge continued down through the plate leans this much
    p = pathops.Path(); pen = p.getPen()
    if foot == 'in':
        inner = upper_part(inner_c, TOP+BR)
        SL = XI-SLAB
        br = bracket(XI-REACH, inner[3], tang(inner), BR)
        pen.moveTo((xi, start)); pen.curveTo(*inner[1:]); pen.curveTo(*rev(br)[1:])
        pen.lineTo((SL, TOP)); pen.lineTo((SL, DEPTH)); pen.lineTo((XO-run, DEPTH))
        pen.curveTo(*rev(outer_c)[1:]); pen.lineTo((xo, start)); pen.closePath()
        return p, (SL, XO)
    outer = upper_part(outer_c, TOP+BR)
    SR = XO+SLAB
    br = bracket(XO+REACH, outer[3], tang(outer), BR)
    pen.moveTo((xi, start)); pen.curveTo(*inner_c[1:]); pen.lineTo((XI-run, DEPTH)); pen.lineTo((SR, DEPTH))
    pen.lineTo((SR, TOP)); pen.lineTo((XO+REACH, TOP)); pen.curveTo(*br[1:]); pen.curveTo(*rev(outer)[1:])
    pen.lineTo((xo, start)); pen.closePath()
    return p, (XI, SR)


def polys(rec):
    out=[]; poly=[]; cur=None
    for op,a in rec.value:
        if op=='moveTo': cur=a[0]; poly=[cur]
        elif op=='lineTo': poly.append(a[0]); cur=a[0]
        elif op=='curveTo':
            for k in range(1,17): poly.append(cubicPointAtT(cur,*a,k/16))
            cur=a[-1]
        elif op=='qCurveTo':
            pts=list(a); prev=cur
            if len(pts)==1: segs=[(prev,pts[0],pts[0])]
            else:
                segs=[]
                for i in range(len(pts)-2):
                    mid=((pts[i][0]+pts[i+1][0])/2,(pts[i][1]+pts[i+1][1])/2); segs.append((prev,pts[i],mid)); prev=mid
                segs.append((prev,pts[-2],pts[-1]))
            for s in segs:
                for k in range(1,9): poly.append(quadraticPointAtT(*s,k/8))
            cur=a[-1]
        elif op in ('closePath','endPath'): out.append(poly); poly=[]
    return out

def crossings(rec, y):
    xs=[]
    for poly in polys(rec):
        for i in range(len(poly)):
            (x0,y0),(x1,y1)=poly[i],poly[(i+1)%len(poly)]
            if (y0>y)!=(y1>y): xs.append(x0+(y-y0)*(x1-x0)/(y1-y0))
    return sorted(xs)

LETTERS = {          # letters without a right stem to continue: the tail is appended,
                     # the letter untouched. `head`: the band it leaves from, `start`: the
                     # height; the reach scales with the drop unless `full` (nj's reach);
                     # `foot_w`: the width at the foot (else TIP_W of the head's); `drawn`:
                     # the tail as drawn by hand, per foot ('in' the anchor, 'out' the
                     # anti-anchor), points and ('c', c1, c2, p), instead of the formula,
                     # its top reaching into the letter; `join`: a filled shape tying tail
                     # and letter; `cut`: per foot, a shape taken away from letter and tail.
    't': {'head': (239, 302), 'start': -10, 'drawn': {   # out of the hook's underside, the outer edge rising to its tip
        'in': [(239, -10), ('c', (239, -134.5), (154.8, -200.4), (85.1, -263)),          # a long slant
               ('c', (68.4, -278), (56.6, -288), (22, -288)), (-47, -288), (-47, -330),  #   onto a plate inward
               (77.1, -330), ('c', (185.3, -233), (301.6, -152.6), (302, -11))],
        'out': [(239, -10), ('c', (239, -162), (116.8, -214.7), (99.2, -292.4)),         # a curl down and left,
                (137.8, -330), (244.9, -330), (244.9, -288), (175.9, -288),             #   its end cut on a slant,
                ('c', (170.9, -288), (177.3, -257.7), (190.9, -243)),                    #   onto a plate outward
                ('c', (248.6, -180.9), (301.7, -126.1), (302, -11))]},
          'join': [(239, -10), (302, -11), (329, 6)]},                   # the outer edge rising to the hook's tip
    's': {'head': (84, 184), 'start': 21, 'drawn': {   # out of the lower curve before its low point: a swan's
        'in': [(84, 21), ('c', (173.2, -105.3), (63.8, -200.4), (-5.9, -263)),          #   neck, out to the right
               ('c', (-22.6, -278), (-34.4, -288), (-69, -288)), (-138, -288), (-138, -330),   #   and back, t's foot
               (-1.9, -330), ('c', (106.3, -233), (243.6, -123.6), (184, -9)), (125, 34), (60, 55)],
        'out': [(85, 25), ('c', (211.6, -96.7), (52.8, -238.7), (0.2, -292.4)),
                (38.8, -330), (193.9, -330), (193.9, -288), (106.6, -288),             # a longer plate
                ('c', (101.6, -288), (127.4, -250.7), (141, -236)),
                ('c', (184.9, -179.4), (259.7, -104.1), (198, 7)), (126, 73), (59, 50)]}},
    'k': {'head': (370, 451), 'start': 107, 'drawn': {   # out of the leg's underside, a wedge to its foot
        'in': [(451.1, -22.6), (550, 5), (448, 104), ('c', (460.9, 79.2), (463.9, 47.4), (458.7, 12.3)),
               ('c', (456.2, 13.3), (453.8, 14.4), (451.5, 15.5)), ('c', (438.5, 21.8), (426.2, 31.5), (414.5, 44.5)),
               ('c', (403, 57.2), (390.5, 74.3), (376.8, 95.8)), (370.3, 107),
               ('c', (427.7, -17.6), (292.7, -196.7), (175.1, -264)),
               ('c', (158.4, -279), (146.6, -289), (112, -289)), (43, -289), (43, -331), (179.1, -331),
               ('c', (186.6, -324.3), (194.3, -317.5), (202, -310.6)), ('c', (322.1, -260.9), (420.4, -132.3), (451.1, -22.6))],
        'out': [(332, 169), ('c', (481.6, -75), (345.7, -220.9), (285.3, -281.2)),        # the leg itself running on
                ('c', (281.3, -285.3), (277.5, -289), (274.2, -292.4)), (312.8, -330), (467.9, -330), (467.9, -288),
                (380.6, -288), ('c', (375.6, -288), (401.4, -250.7), (415, -236)),
                ('c', (418.9, -231), (423, -225.9), (427.2, -220.6)), ('c', (466.4, -171.5), (515.6, -39.2), (485, 57.7)),
                ('c', (484.8, 77.9), (481.6, 118), (455.2, 115.3)), (440, 168), (419.8, 102.2)]},
          'cut': {'out': [(495, -38), ('c', (489.6, -149.9), (855, -74), (855, -74)), (666, 198),   # the leg's foot
                          ('c', (666, 198), (379.6, 262.2), (429, 192)), ('c', (478.4, 121.8), (498.2, 27.6), (495, -38))]}},
    'b': {'head': (136, 260), 'start': 21, 'drawn': {    # the stem's foot running on, its spur cut away
        'in': [(160, 21), ('c', (247.9, -103.4), (143, -197.6), (70.1, -263)),
               ('c', (53.4, -278), (41.6, -288), (7, -288)), (-62, -288), (-62, -330), (74.1, -330),
               ('c', (81.6, -323.3), (89.3, -316.5), (97, -309.6)), ('c', (200.4, -217.8), (315.5, -115.6), (260, -9)),
               (185, 152), (136, 55)],
        'out': [(129, 25), ('c', (196.5, -120.9), (115.7, -220.9), (55.3, -281.2)),
                ('c', (51.3, -285.3), (47.5, -289), (44.2, -292.4)), (82.8, -330), (237.9, -330), (237.9, -288),
                (150.6, -288), ('c', (145.6, -288), (171.4, -250.7), (185, -236)),
                ('c', (188.9, -231), (193, -225.9), (197.2, -220.6)), ('c', (241, -165.9), (266.4, -17.7), (210.1, 83.6)),
                (173, 129.2), ('c', (205, 15.1), (166.8, 66.9), (139.7, 103.6)),
                ('c', (130.3, 116.4), (122.2, 127.4), (118.9, 128.8)), (120, 79.8)]},
          'cut': {'in': [(0, -10), (182, -21), (100, 136), (0, 90)],
                  'out': [(6.4, -85.1), (148.9, -51.1), (106.4, 183), (6.4, 183)]}},
    # the rest borrow a drawn tail (`like`, with its cut) from the letter whose bottom
    # they share, set by the same feature, then nudged to where its top hides best
    'B': {'like': 'b'}, 'D': {'like': 'b'}, 'P': {'like': 'b'},   # a stem's foot running on
    'T': {'like': 'b'}, 'Y': {'like': 'b'},
    'K': {'like': 'k'}, 'X': {'like': 'k'}, 'Z': {'like': 'k'},   # out of a leg's (or bar's) foot
    'x': {'like': 'k'}, 'z': {'like': 'k'},
    'S': {'like': 's'}, 'C': {'like': 's'}, 'G': {'like': 's'},   # out of a round bottom
    'Q': {'like': 's'}, 'c': {'like': 's'},                      # (J: its descender is the stem formula's)
    'V': {'like': 't'}, 'v': {'like': 't'},                       # hanging from a point
}
ALL = 'nmhdHMNtkbsBDPTYKXZxzSCGQJcVv'


def under(rec, step=2):
    """The region under a letter's underside, down to -1000: per column of
    `step` units, from the lowest ink up to it."""
    t = RecordingPen(); t.value = [(op, tuple((y, x) for x, y in pts)) for op, pts in rec.value]   # x and y swapped
    xs = [x for poly in polys(rec) for x, _ in poly]
    p = pathops.Path(); pen = p.getPen()
    for x in range(int(min(xs)), int(max(xs)) + 1, step):
        ys = crossings(t, x + step / 2)
        if ys:
            pen.moveTo((x, -1000)); pen.lineTo((x + step, -1000)); pen.lineTo((x + step, ys[0] + 1)); pen.lineTo((x, ys[0] + 1)); pen.closePath()
    p.simplify(fix_winding=True)
    return p


def feature(rec, kind):
    """Where a borrowed tail is set on a letter: the leftmost stem's left edge
    ('b'), the far right end of the ink on the baseline ('k'), or the lowest
    point of the underside, of the parts that keep to the baseline ('s', 't')."""
    if kind == 'b':
        st = vertical_stems(rec)
        return st[0][0] if st else min(crossings(rec, 100))
    if kind == 'k':
        return max(crossings(rec, 15))
    t = RecordingPen(); t.value = [(op, tuple((y, x) for x, y in pts)) for op, pts in rec.value]
    xs = [x for poly in polys(rec) for x, _ in poly]
    low = [(crossings(t, x)[0], x) for x in range(int(min(xs)), int(max(xs)), 2) if crossings(t, x)]
    low = [(y, x) for y, x in low if y >= -20]                       # not a descender (Q's tail)
    y0 = min(y for y, _ in low)
    xs0 = [x for y, x in low if y <= y0 + 2]
    return (min(xs0) + max(xs0)) / 2


def even_width(tail):
    """The tail with its stroke brought to WIDTH: measured across the stroke
    every 10 units down, each edge moved sideways by half the difference; the
    move fades out toward the letter (above -40) and the foot (below -250)."""
    rec = rec_from(tail)
    (y0, w0), (y1, w1) = WIDTH
    target = lambda y: w0 + (y - y0) * (w1 - w0) / (y1 - y0)
    def span(y, near=None):
        xs = crossings(rec, y); sp = list(zip(xs[::2], xs[1::2]))
        if not sp: return None
        return max(sp, key=lambda s: s[1]-s[0]) if near is None else min(sp, key=lambda s: abs((s[0]+s[1])/2 - near))
    rows, c = [], None
    for y in range(-30, -261, -10):
        sp = span(y, c)
        if sp: c = (sp[0]+sp[1])/2; rows.append((y, sp))
    if len(rows) < 3:
        return tail
    def at(y):                                        # (centre, horizontal change) at y
        ys = [r[0] for r in rows]
        y = max(min(y, ys[0]), ys[-1])
        i = min(range(len(rows)), key=lambda k: abs(rows[k][0]-y))
        y_, (a, b) = rows[i]
        j = min(i+1, len(rows)-1); k = max(i-1, 0)
        ca, cb = (rows[k][1][0]+rows[k][1][1])/2, (rows[j][1][0]+rows[j][1][1])/2
        dy = rows[k][0]-rows[j][0] or 1
        sin = abs(dy) / math.hypot(dy, ca-cb)
        dh = (target(y_) - (b-a)*sin) / sin
        return (a+b)/2, max(-60, min(60, dh))
    def fade(y):
        if y > 10 or y < -285: return 0
        if y > -40: return (10 - y) / 50
        if y < -250: return (y + 285) / 35
        return 1
    out = RecordingPen(); cur = None
    for op, pts in rec.value:
        if op in ('curveTo', 'lineTo', 'qCurveTo'):
            if op == 'curveTo':
                mid = cubicPointAtT(cur, *pts, 0.5)
            else:
                mid = ((cur[0]+pts[-1][0])/2, (cur[1]+pts[-1][1])/2)
            side = 1 if mid[0] > at(mid[1])[0] else -1
            moved = tuple((x + side * at(y)[1] / 2 * fade(y), y) for x, y in pts)
            out.value.append((op, moved)); cur = pts[-1]
        else:
            if op == 'moveTo': cur = pts[0]
            out.value.append((op, tuple((x + (1 if x > at(y)[0] else -1) * at(y)[1] / 2 * fade(y), y) for x, y in pts) if op == 'moveTo' else pts))
    p = pathops.Path(); out.replay(p.getPen()); p.simplify(fix_winding=True)
    return p


def vertical_stems(rec):
    """[(xi, xo)] of the vertical stems: crossing pairs at y=200 that repeat at y=300."""
    p200 = list(zip(crossings(rec, 200)[::2], crossings(rec, 200)[1::2]))
    p300 = list(zip(crossings(rec, 300)[::2], crossings(rec, 300)[1::2]))
    return [(a, b) for a, b in p200 if any(abs(a-c) < 8 and abs(b-d) < 8 for c, d in p300)]


def shape(pts, dx=0):
    """A closed pathops.Path from points and ('c', c1, c2, p), moved dx."""
    mv = lambda q: (q[0]+dx, q[1])
    p=pathops.Path(); pen=p.getPen(); pen.moveTo(mv(pts[0]))
    for seg in pts[1:]:
        if seg[0] == 'c': pen.curveTo(mv(seg[1]), mv(seg[2]), mv(seg[3]))
        else: pen.lineTo(mv(seg))
    pen.closePath(); p.simplify(fix_winding=True)
    return p


def rec_from(p):
    r = RecordingPen(); p.draw(r); return r


def tidy(rec):
    """The recording with its points rounded to a tenth of a unit and the
    segments of about a unit or less dropped (the crumbs a boolean leaves at a join)."""
    out, cur, start = RecordingPen(), None, None
    for op, pts in rec.value:
        pts = tuple((round(x, 1), round(y, 1)) for x, y in pts)
        if op == 'moveTo':
            cur = start = pts[0]
        elif op in ('lineTo', 'curveTo', 'qCurveTo'):
            if all(math.dist(cur, q) < 1.5 for q in pts):
                continue
            cur = pts[-1]
        elif op == 'closePath' and out.value and out.value[-1][0] != 'moveTo' and math.dist(cur, start) < 1.5:
            last = out.value.pop()                       # the last point is the start again: end on the start
            if last[0] != 'lineTo':
                out.value.append((last[0], last[1][:-1] + (start,)))
        out.value.append((op, pts))
    return out


def make(font, letter, mark=0x0326):
    """Write the override for <letter> + mark. The tail continues the letter's
    rightmost vertical stem, bending left; LETTERS names the head for letters
    without one."""
    foot = 'in' if mark == 0x0326 else 'out'
    cmap=font.getBestCmap(); M=FS.metrics(font)
    gname=cmap[ord(letter)]; comp=f'{gname}_uni{mark:04X}'
    rec0=FS.glyph_rec(font, gname); adv=font['hmtx'][gname][0]
    spec=LETTERS.get(letter, {})
    stems=vertical_stems(rec0)
    if 'like' in spec:                               # a borrowed tail: no stem of its own
        spec = dict(spec, head=(0, 0), start=0)
    head = spec['head'] if 'head' in spec else stems[-1]
    start = spec.get('start', START_Y)
    rec = rec0
    xi, xo = head
    letter_p=pathops.Path(); rec.replay(letter_p.getPen()); letter_p.simplify(fix_winding=True, keep_starting_points=False)
    def rect(x0,y0,x1,y1):
        r=pathops.Path(); p=r.getPen(); p.moveTo((x0,y0)); p.lineTo((x1,y0)); p.lineTo((x1,y1)); p.lineTo((x0,y1)); p.closePath(); return r
    xs=crossings(rec, 200)
    body = letter_p                                  # what the letter keeps; the rest is cut
    if 'head' not in spec:
        pts=[pt for _,ps in FS.contours(rec) for pt in ps]
        fspan = [(a,b) for a,b in zip(crossings(rec,20)[::2], crossings(rec,20)[1::2]) if a-2 <= xo <= b+2]
        right_ink = fspan[0][1] if fspan else xo       # the foot serif's (or hook's) far end
        low = min([pt[1] for pt in pts if pt[1] < 150] + [0]) - 1                     # the foot may dip under the baseline (t's hook, a bowl)
        body = pathops.op(body, rect(xi-0.5, -1, xo+0.5, start), pathops.PathOp.DIFFERENCE)     # the stem
        fh = min(150, start)                              # the foot region, never above the tail's start
        body = pathops.op(body, rect(xi-0.5, low, right_ink+2, fh), pathops.PathOp.DIFFERENCE)  # its foot (serif or hook)
        s20=[(a,b) for a,b in zip(crossings(rec,20)[::2], crossings(rec,20)[1::2]) if a-2 <= xi <= b+2]
        s41=[(a,b) for a,b in zip(crossings(rec,41)[::2], crossings(rec,41)[1::2]) if a-2 <= xi <= b+2]
        if s20 and s41 and xi-s20[0][0] >= 40 and abs(s20[0][0]-s41[0][0]) < 6:      # a serif half on the inner side
            body = pathops.op(body, rect(s20[0][0]-1, low, xi, 150), pathops.PathOp.DIFFERENCE)   # left of the stem: the stem stays
        elif not [x for x in xs if x < xi-1]:            # nothing else on the inner side (t): the hook goes whole
            left_ink = min([pt[0] for pt in pts if pt[1] < 150] + [xi])
            body = pathops.op(body, rect(left_ink-2, low, xi, 150), pathops.PathOp.DIFFERENCE)
    # every other stem's foot half that faces the tail is cut back to a slanted spur (SPUR)
    def span_at(y, x):
        for a, b in zip(crossings(rec, y)[::2], crossings(rec, y)[1::2]):
            if a-2 <= x <= b+2: return (a, b)
        return None
    for a, b in (zip(xs[::2], xs[1::2]) if 'head' not in spec else ()):
        if b >= xi - 1: continue                       # the tail stem itself (and anything right of it)
        s20, s41, s60 = span_at(20, b), span_at(41, b), span_at(60, b)
        if not (s20 and s41 and s60): continue
        if s20[1]-b >= 40 and abs(s41[1]-s20[1]) < 6 and s60[1] < s20[1]-15:   # a flat slab with a bracket
            x0, x1 = b+SPUR[0], b+SPUR[1]
            top = SH+18; xt = x0 + (x1-x0)*(top+1)/SH
            cut=pathops.Path(); cp=cut.getPen()
            cp.moveTo((x0 - (x1-x0)/SH, -1)); cp.lineTo((xt, top)); cp.lineTo((s20[1]+2, top)); cp.lineTo((s20[1]+2, -1)); cp.closePath()
            body = pathops.op(body, cut, pathops.PathOp.DIFFERENCE)
    dx = 0
    if 'like' in spec:                               # set by the shared feature, nudged so its top hides
        src = LETTERS[spec['like']]
        srec = FS.glyph_rec(font, cmap[ord(spec['like'])])
        base = feature(rec0, spec['like']) - feature(srec, spec['like'])
        keep = pathops.op(pathops.op(letter_p, under(rec0), pathops.PathOp.UNION), rect(-1000, -1000, 2000, 0), pathops.PathOp.UNION)
        area = lambda q: sum(abs(FS.area(ps)) for _, ps in FS.contours(rec_from(q)))
        def showing(d):                              # its top showing, a clash with a descender, the distance
            t = shape(src['drawn'][foot], d)
            top = pathops.op(pathops.op(t, rect(-1000, 0, 2000, 1000), pathops.PathOp.INTERSECTION), letter_p, pathops.PathOp.DIFFERENCE)
            clash = pathops.op(pathops.op(t, rect(-1000, -1000, 2000, -20), pathops.PathOp.INTERSECTION), letter_p, pathops.PathOp.INTERSECTION)
            return area(top) + 5 * area(clash) + 3 * abs(d - base)
        dx = min(range(int(base) - 80, int(base) + 81, 5), key=showing)
        tail = pathops.op(shape(src['drawn'][foot], dx), rect(dx + src['head'][0], -12, dx + src['head'][1], 40), pathops.PathOp.UNION)
        tail = pathops.op(tail, keep, pathops.PathOp.INTERSECTION)   # up to the letter, never above it
        spec = dict(spec, cut={f: c for f, c in src.get('cut', {}).items()})
        xi, xo = dx + src['head'][0], dx + src['head'][1]
        xs_ = [x for _, ps in FS.contours(rec_from(tail)) for x, y in ps if y < -250]
        SL, SR = min(xs_), max(xs_)
    elif 'drawn' in spec:                            # by hand
        tail = shape(spec['drawn'][foot])
        if 'join' in spec:
            tail = pathops.op(tail, shape(spec['join']), pathops.PathOp.UNION)
        xs_ = [x for _, ps in FS.contours(rec_from(tail)) for x, y in ps if y < -250]
        SL, SR = min(xs_), max(xs_)
    else:
        tail, (SL,SR) = tail_path(xi, xo, foot, start, spec.get('full', False), spec.get('foot_w'))
        tail = pathops.op(tail, rect(xi, start-1, xo, start+16), pathops.PathOp.UNION)   # the head overlaps the stem above
    tail = even_width(even_width(tail))              # twice: one pass gets most of the way
    def rec_of(p):
        p.simplify()
        r=RecordingPen(); p.draw(r)
        if any(abs(FS.area(c[1])) < 800 for c in FS.contours(r)):           # slivers left at a join
            keep = RecordingPen(); keep.value = [op for ops, pts in FS.contours(r) if abs(FS.area(pts)) >= 800 for op in ops]
            r = keep
        return tidy(r)
    drawn_cut = shape(spec['cut'][foot], dx) if foot in spec.get('cut', {}) else pathops.Path()
    merged = lambda: pathops.op(pathops.op(body, tail, pathops.PathOp.UNION), drawn_cut, pathops.PathOp.DIFFERENCE)
    whole = rec_from(merged())                       # crumbs a cut or a join leaves: a sliver goes
    sign = 1 if FS.area(max(FS.contours(whole), key=lambda c: abs(FS.area(c[1])))[1]) > 0 else -1    # to the cut,
    counters = [abs(FS.area(ps)) for _, ps in FS.contours(rec_from(letter_p))]                     # a pinhole is filled
    for ops, ps in FS.contours(whole):
        a_ = FS.area(ps)
        if abs(a_) < 800 and not any(abs(abs(a_) - c) < 5 for c in counters):
            crumb = pathops.Path(); replayRecording(ops, crumb.getPen()); crumb.simplify(fix_winding=True)
            if a_ * sign > 0: drawn_cut = pathops.op(drawn_cut, crumb, pathops.PathOp.UNION)
            else: tail = pathops.op(tail, crumb, pathops.PathOp.UNION)
    rr = rec_of(merged())
    # written as three shapes the build puts together again: the tail whole in
    # TAIL_INK, under the letter as it is, never cut, in ink (they overlap, so
    # they merge); and in the cut layer what is taken away from the letter (and
    # not refilled by the tail)
    parts = [('tail', TAIL_INK, rec_of(tail)), ('letter', '#111', rec_of(letter_p))]
    cut = pathops.op(pathops.op(letter_p, body, pathops.PathOp.DIFFERENCE), tail, pathops.PathOp.DIFFERENCE)
    cut = pathops.op(cut, drawn_cut, pathops.PathOp.UNION)
    cut.simplify(); cut_r = RecordingPen(); cut.draw(cut_r); cut = cut_r          # every piece: a small cut is a cut
    new_adv = adv
    if SR > adv + 10:                                 # the plate overshoots the advance
        new_adv = int(round(SR + 25))
    FS.export('serif', [comp], font_path=font.reader.file.name, force=True)
    path=os.path.join(FS.SVG_ROOT, 'serif', FS.file_stem(font, comp) + '.svg')
    ox,oy,W,H=FS.canvas(M); to_svg=Transform(1,0,0,-1,ox,oy)
    shapes='\n'.join(f'    <path id="{pid}" fill="{ink}" d="{FS.path_d([o for o,_ in FS.contours(r)], to_svg)}"/>' for pid, ink, r in parts)
    text=open(path).read()
    text=re.sub(r'(<g id="glyph"[^>]*>)\n.*?(\n  </g>)', lambda m: m.group(1)+'\n'+shapes+m.group(2), text, flags=re.S)
    if cut.value:
        cuts=f'    <path id="cut1" fill="{CUT_INK}" d="{FS.path_d([o for o,_ in FS.contours(cut)], to_svg)}"/>'
        text=re.sub(r'(<g id="cut"[^>]*>)', lambda m: m.group(1)+'\n'+cuts, text)   # before the spare
    text=re.sub(r'data-advance="[^"]*"', f'data-advance="{new_adv}"', text)   # the base letter's, or wider
    open(path,'w').write(text)
    print(f'  {comp}: head {xi:.0f}..{xo:.0f} from y={start}, plate {SL:.0f}..{SR:.0f}'
          + (f', advance {adv} -> {new_adv}' if new_adv != adv else '') + f', contours {len(FS.contours(rr))}')
    return comp, rr


if __name__ == '__main__':
    font=TTFont(os.path.join(ROOT, 'fonts', 'build', 'DiafonSerif-derived.ttf'))
    for L in sys.argv[1] if len(sys.argv)>1 else ALL:
        make(font, L, 0x0326)          # the anchor: foot inward
        make(font, L, 0x0316)          # the anti-anchor: foot outward
