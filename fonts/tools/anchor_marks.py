#!/usr/bin/env python3
"""Seed the two anchor marks as editable canvases, fonts/hand/anchors/:
uni0326.svg (the anchor) and uni0316.svg (the reverse), both the same piece
of the capital X: its lower-left leg (the / diagonal with its foot serif),
its straight stem carried on along its own edges up to TOP, moved down by
DROP: the serif (42 high, as the sheet's foot band) stands on the floor at
-330 and the stem ends on the baseline; to be drawn on by hand.
The files are not overrides (nothing in fonts/svg/), so the build ignores
them; rerunning this overwrites them.

    python3 fonts/tools/anchor_marks.py           # -> fonts/hand/anchors/uni0326.svg, uni0316.svg
    python3 fonts/tools/anchor_marks.py sans      # -> fonts/hand/anchors/sans/  (mono: .../mono/)

The sans and mono X are plain strokes: their leg is the / from the bottom left,
its edges straight to the crossing, cut flat at the floor.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import font_svg as FS
import pathops
import serif_tail as ST
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

OUT = os.path.join(FS.ROOT, 'fonts', 'hand', 'anchors')
LEG = (-100, -100, 313, 250)      # the box that holds X's lower-left leg (the strokes part below y=290)
EDGES = ((150, 144.6, 211.4), (250, 214.4, 279.1))   # the stem's edges: y, left x, right x (straight lines)
FAMILIES = {                      # family: (font, its box, its leg's edges as above, the folder)
    'serif': ('DiafonSerif-derived.ttf', LEG, EDGES, ''),
    'sans': ('DiafonSans-derived.ttf', (-100, -100, 300, 250),       # (4,0)-(241,372) and (99,0)-(291,310)
             ((150, 4 + 237 * 150 / 372, 99 + 192 * 150 / 310), (250, 4 + 237 * 250 / 372, 99 + 192 * 250 / 310)), 'sans'),
    'mono': ('DiafonMono-derived.ttf', (-100, -100, 300, 250),       # (35,0)-(258,369) and (131,0)-(301,296)
             ((150, 35 + 223 * 150 / 369, 131 + 170 * 150 / 296), (250, 35 + 223 * 250 / 369, 131 + 170 * 250 / 296)), 'mono'),
}
TOP = 330                         # the stem carried on up to here (in X)
DROP = -330                       # moved down this far: serif on -330, stem's end on the baseline


def leg(font, LEG=LEG, EDGES=EDGES):
    X = pathops.Path(); FS.glyph_rec(font, font.getBestCmap()[ord('X')]).replay(X.getPen())
    X.simplify(fix_winding=True)
    box = pathops.Path(); p = box.getPen()
    x0, y0, x1, y1 = LEG
    p.moveTo((x0, y0)); p.lineTo((x1, y0)); p.lineTo((x1, y1)); p.lineTo((x0, y1)); p.closePath()
    piece = pathops.op(X, box, pathops.PathOp.INTERSECTION)
    (ya, la, ra), (yb, lb, rb) = EDGES
    at = lambda e0, e1, y: e0 + (e1 - e0) * (y - ya) / (yb - ya)
    stem = pathops.Path(); p = stem.getPen()
    p.moveTo((at(la, lb, y1 - 10), y1 - 10)); p.lineTo((at(ra, rb, y1 - 10), y1 - 10))
    p.lineTo((at(ra, rb, TOP), TOP)); p.lineTo((at(la, lb, TOP), TOP)); p.closePath()
    piece = pathops.op(piece, stem, pathops.PathOp.UNION)
    out = RecordingPen()
    piece.draw(TransformPen(out, (1, 0, 0, 1, 0, DROP)))
    return out


def sheet_lines(font, ox, oy):
    """The guides of the drawing sheet (fonts/tools/tail_sheet.py), in its
    colours: baseline, x-height, cap height and descender in grey, the foot
    band (-288, -330) in dotted green, X's origin and advance in orange, and
    the whole X, pale, where it stands."""
    adv = font['hmtx'][font.getBestCmap()[ord('X')]][0]
    x0, x1 = ox - 500, ox + 1500
    row = lambda y, c, w, dash='', label='': (
        f'<line x1="{x0}" x2="{x1}" y1="{oy - y}" y2="{oy - y}" stroke="{c}" stroke-width="{w}"{dash}/>'
        f'<text x="{x1 + 10}" y="{oy - y + 7}" fill="#777" font-family="sans-serif" font-size="20">{label} {y}</text>')
    col = lambda x, dash='': (f'<line x1="{ox + x}" x2="{ox + x}" y1="{oy - 800}" y2="{oy + 370}" '
                              f'stroke="#f0b070" stroke-width="3"{dash}/>')
    d = ' stroke-dasharray="30 24"'; dot = ' stroke-dasharray="10 16"'
    pen = SVGPathPen(font.getGlyphSet())
    font.getGlyphSet()[font.getBestCmap()[ord('X')]].draw(TransformPen(pen, (1, 0, 0, -1, ox, oy)))
    return '\n'.join('    ' + l for l in [
        f'<path id="X-reference" d="{pen.getCommands()}" fill="#e2e2e2" stroke="#b8b8b8" stroke-width="3"/>',
        row(714, '#d0d0d0', 3, d, 'cap height'), row(536, '#d0d0d0', 3, d, 'x-height'),
        row(-240, '#d0d0d0', 3, d, 'descender'), row(-288, '#9fc08a', 4, dot, 'foot top'),
        row(-330, '#9fc08a', 4, dot, 'floor'), row(0, '#a8a8a8', 5, '', 'baseline'),
        col(0), col(adv, d)])


def write(font, gname, rec, out=OUT):
    path = os.path.join(out, gname + '.svg')
    FS.export('serif', [gname], font_path=font.reader.file.name, force=True, out_dir=out)
    ox, oy, W, H = FS.canvas(FS.metrics(font))
    d = FS.path_d([o for o, _ in FS.contours(ST.tidy(rec))], Transform(1, 0, 0, -1, ox, oy))
    text = open(path).read()
    text = re.sub(r'(<g id="glyph"[^>]*>)\n.*?(\n  </g>)',
                  lambda m: m.group(1) + f'\n    <path id="tail" fill="#111" d="{d}"/>' + m.group(2), text, flags=re.S)
    text = re.sub(r'\n\s*<path id="ghost"[^>]*/>', '', text)     # not the font's old mark
    text = re.sub(r'\n\s*<line [^>]*stroke="#(8bf|48f|f80)"[^>]*/>(<text[^>]*>[^<]*</text>)?', '', text)   # the canvas's heights:
    text = text.replace('  </g>\n  <g id="glyph"', sheet_lines(font, ox, oy) + '\n  </g>\n  <g id="glyph"', 1)    #   the sheet's instead
    H_ = H
    for y in (-288, -330):                            # and Inkscape guides on the foot band
        text = text.replace('  </sodipodi:namedview>', f'    <sodipodi:guide position="0,{H_ - (oy - y)}" orientation="0,1" '
                            f'inkscape:label="{"foot top" if y == -288 else "floor"}" inkscape:locked="true"/>\n  </sodipodi:namedview>', 1)
    text = re.sub(r'data-advance="[^"]*"', 'data-advance="0"', text)
    open(path, 'w').write(text)


def main(argv):
    fam = argv[0] if argv else 'serif'
    src, box, edges, sub = FAMILIES[fam]
    out = os.path.join(OUT, sub)
    os.makedirs(out, exist_ok=True)
    font = TTFont(os.path.join(FS.ROOT, 'fonts', 'build', src))
    piece = leg(font, box, edges)
    for g in ('uni0326', 'uni0316'):
        write(font, g, piece, out)
        print(f'  {os.path.relpath(os.path.join(out, g + ".svg"), FS.ROOT)}')


if __name__ == '__main__':
    main(sys.argv[1:])
