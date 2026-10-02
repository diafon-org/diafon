"""The serif anchor tail (fonts/svg/serif): the right stem runs on below the
baseline in one even arc from right under the arch, thinning a little, and
lands on a one-sided plate foot, inward for the anchor (U+0326) and outward
for the anti-anchor (U+0316); the letter's other feet lose the half that
faces the tail, cut to a slanted spur. Letters without such a stem get the
tail appended at their right side (LETTERS), untouched. The numbers were read off a hand
drawn n; the tail is grown from each letter's own stem, so it fits any width.

    python3 fonts/tools/serif_tail.py            # n m h d H M N t k b s, both marks -> fonts/svg/serif/<glyph>.svg
    python3 fonts/tools/serif_tail.py nH         # some of them

Then fonts/build.sh serif. The written files are ordinary overrides: edit
them in Inkscape, or change a number here and regenerate."""
import sys, re, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import font_svg as FS
ROOT = FS.ROOT
from fontTools.ttLib import TTFont
from fontTools.misc.transform import Transform
from fontTools.misc.bezierTools import splitCubicAtT, solveCubic, cubicPointAtT, quadraticPointAtT
from fontTools.pens.recordingPen import RecordingPen
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
SPUR = (16, 50)        # every other stem's foot half facing the tail is cut to a spur: the
                       #   cut runs from this far beyond the stem at the baseline to this
                       #   far at the plate's top (a slant leaning outward going up)
TOP = DEPTH + SH
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
                     # `foot_w`: the width at the foot (else TIP_W of the head's); `extra`:
                     # a filled shape joining tail and letter, points and ('c', c1, c2, p).
    't': {'head': (239, 302), 'start': -10, 'full': True, 'foot_w': 80,   # a thin tail curling down out of
          'extra': [(220, 60), (370, 60), ('c', (370, 20), (335, -10), (302, -10)), (239, -10)]},  # the hook's extended end
    'k': {'head': (458, 520), 'start': 60, 'full': True, 'foot_w': 80},   # a thin tail from under the leg's foot
    'b': {'head': (458, 556), 'start': 50, 'full': True},                # the bowl's right side, leaving it under
                                                                         #   the bowl so a notch opens (as on d)
    's': {'head': (195, 289), 'start': 20},                              # from the lower bowl's bottom
}


def vertical_stems(rec):
    """[(xi, xo)] of the vertical stems: crossing pairs at y=200 that repeat at y=300."""
    p200 = list(zip(crossings(rec, 200)[::2], crossings(rec, 200)[1::2]))
    p300 = list(zip(crossings(rec, 300)[::2], crossings(rec, 300)[1::2]))
    return [(a, b) for a, b in p200 if any(abs(a-c) < 8 and abs(b-d) < 8 for c, d in p300)]


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
    head = spec['head'] if 'head' in spec else stems[-1]
    start = spec.get('start', START_Y)
    rec = rec0
    xi, xo = head
    letter_p=pathops.Path(); rec.replay(letter_p.getPen()); letter_p.simplify(fix_winding=True, keep_starting_points=False)
    def rect(x0,y0,x1,y1):
        r=pathops.Path(); p=r.getPen(); p.moveTo((x0,y0)); p.lineTo((x1,y0)); p.lineTo((x1,y1)); p.lineTo((x0,y1)); p.closePath(); return r
    xs=crossings(rec, 200)
    body = letter_p
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
    tail, (SL,SR) = tail_path(xi, xo, foot, start, spec.get('full', False), spec.get('foot_w'))
    if 'extra' in spec:                              # a filled join to the letter
        ex=pathops.Path(); ep=ex.getPen(); pts=spec['extra']
        ep.moveTo(pts[0])
        for seg in pts[1:]:
            if seg[0] == 'c': ep.curveTo(seg[1], seg[2], seg[3])
            else: ep.lineTo(seg)
        ep.closePath()
        tail = pathops.op(tail, ex, pathops.PathOp.UNION)
    tail = pathops.op(tail, rect(xi, start-1, xo, start+16), pathops.PathOp.UNION)   # the head overlaps the stem above
    out = pathops.op(body, tail, pathops.PathOp.UNION)
    out.simplify()
    rr=RecordingPen(); out.draw(rr)
    if any(abs(FS.area(c[1])) < 800 for c in FS.contours(rr)):          # slivers left at a join
        keep = RecordingPen(); keep.value = [op for ops, pts in FS.contours(rr) if abs(FS.area(pts)) >= 800 for op in ops]
        rr = keep
    new_adv = adv
    if SR > adv + 10:                                 # the plate overshoots the advance
        new_adv = int(round(SR + 25))
    FS.export('serif', [comp], font_path=font.reader.file.name, force=True)
    path=os.path.join(FS.SVG_ROOT, 'serif', FS.file_stem(font, comp) + '.svg')
    ox,oy,W,H=FS.canvas(M); d=FS.path_d([o for o,_ in FS.contours(rr)], Transform(1,0,0,-1,ox,oy))
    text=open(path).read()
    text=re.sub(r'(<g id="glyph"[^>]*>)\n.*?(\n  </g>)', lambda m: m.group(1)+f'\n    <path id="shape1" fill="#111" d="{d}"/>'+m.group(2), text, flags=re.S)
    text=re.sub(r'data-advance="[^"]*"', f'data-advance="{new_adv}"', text)   # the base letter's, or wider
    open(path,'w').write(text)
    print(f'  {comp}: head {xi:.0f}..{xo:.0f} from y={start}, plate {SL:.0f}..{SR:.0f}'
          + (f', advance {adv} -> {new_adv}' if new_adv != adv else '') + f', contours {len(FS.contours(rr))}')
    return comp, rr


if __name__ == '__main__':
    font=TTFont(os.path.join(ROOT, 'fonts', 'build', 'DiafonSerif-derived.ttf'))
    for L in sys.argv[1] if len(sys.argv)>1 else 'nmhdHMNtkbs':
        make(font, L, 0x0326)          # the anchor: foot inward
        make(font, L, 0x0316)          # the anti-anchor: foot outward
