#!/usr/bin/env python3
"""The SVG round-trip for the Diaphone font: export glyphs to editable SVGs, edit them in any
vector editor, and `build_font.py` imports the edits into the final font.

Export:  python scripts/font_svg.py export 0329 0348 030D 030E   # or letters: export s t j
         -> fonts/svg/uni0329.svg …  (em-box + baseline / x-height / descender guides included)

Editing rules (any editor — Inkscape, Illustrator, Figma):
  - Edit ONLY the path(s) inside the <g id="glyph"> group; everything in <g id="guides"> is
    reference and ignored on import.
  - The canvas is the em square (units per em read from the font — the comment in each SVG
    states it; y grows down in SVG, the importer flips it back). The "baseline" guide is y=0
    in font space; draw below it for under-marks.
  - Keep it plain paths (Object → Path). Cubic curves are fine — they are converted to
    TrueType quadratics on import.

Import happens automatically in build_font.py: any fonts/svg/<glyphname>.svg present replaces
that glyph's outline in the built font.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG_DIR = os.path.join(ROOT, "fonts", "svg")
FONT = os.path.join(ROOT, "fonts", "Diaphone-Regular.ttf")


def _metrics(font):
    """(upm, asc, desc, x_height) read from the font — no hardcoded base-font numbers."""
    upm = font["head"].unitsPerEm
    asc, desc = font["hhea"].ascent, font["hhea"].descent
    xh = getattr(font.get("OS/2"), "sxHeight", 0) or int(upm * 0.48)
    return upm, asc, desc, xh


def _glyph_name(font, arg):
    cmap = font.getBestCmap()
    if re.fullmatch(r"(0x|U\+)?[0-9A-Fa-f]{2,6}", arg):
        cp = int(arg.replace("U+", "").replace("0x", ""), 16)
    elif len(arg) == 1:
        cp = ord(arg)
    else:
        return arg                                   # already a glyph name
    return cmap.get(cp)


def export(args):
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.misc.transform import Transform
    from fontTools.pens.transformPen import TransformPen

    font = TTFont(FONT)
    glyphset = font.getGlyphSet()          # handles composite glyphs (decomposed on draw)
    upm, asc, desc, xh = _metrics(font)
    os.makedirs(SVG_DIR, exist_ok=True)
    for arg in args or ["0329", "0348", "030D", "030E"]:
        gname = _glyph_name(font, arg)
        if not gname or gname not in glyphset:
            print(f"  ?? {arg}: no such glyph")
            continue
        pen = SVGPathPen(glyphset)
        # font space (y up) -> SVG space (y down), origin at top-left of the em drawing box
        glyphset[gname].draw(TransformPen(pen, Transform(1, 0, 0, -1, 0, asc)))
        d = pen.getCommands()
        H = asc - desc
        guides = "\n".join(
            f'    <line x1="{-upm // 2}" x2="{upm + upm // 2}" y1="{asc - y}" y2="{asc - y}" stroke="#8bf" '
            f'stroke-width="{max(2, upm // 500)}" stroke-dasharray="{upm // 85} {upm // 85}"/><!-- {label} (font y={y}) -->'
            for y, label in ((0, "baseline"), (xh, "x-height"), (desc, "descender"))
        )
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-upm // 2} 0 {2 * upm} {H}" width="512">
  <!-- Diaphone glyph "{gname}" — edit ONLY inside g#glyph; g#guides is ignored on import.
       Font baseline is the dashed line at SVG y={asc}; the em is {upm} units. -->
  <g id="guides" opacity="0.5">
{guides}
  </g>
  <g id="glyph">
    <path fill="#111" d="{d}"/>
  </g>
</svg>
'''
        out = os.path.join(SVG_DIR, f"{gname}.svg")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"  exported {os.path.relpath(out, ROOT)}")


def import_overrides(font, verbose=True):
    """Replace glyph outlines from fonts/svg/<glyphname>.svg (called by build_font.py).
    Reads every <path d="…"> outside g#guides, flips y back to font space, converts cubics
    to quadratics. Returns the list of glyph names replaced."""
    from fontTools.svgLib.path.parser import parse_path
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.misc.transform import Transform

    if not os.path.isdir(SVG_DIR):
        return []
    glyf = font["glyf"]
    upm, asc, _, _ = _metrics(font)
    done = []
    for fn in sorted(os.listdir(SVG_DIR)):
        if not fn.endswith(".svg"):
            continue
        gname = fn[:-4]
        if gname not in glyf:
            continue
        text = open(os.path.join(SVG_DIR, fn), encoding="utf-8").read()
        body = re.sub(r'<g id="guides".*?</g>', "", text, flags=re.S)   # drop the reference layer
        ds = re.findall(r'<path[^>]*\bd="([^"]+)"', body)
        if not ds:
            continue
        tt = TTGlyphPen(None)
        pen = TransformPen(Cu2QuPen(tt, upm), Transform(1, 0, 0, -1, 0, asc))  # SVG -> font space
        for d in ds:
            parse_path(d, pen)
        glyf[gname] = tt.glyph()
        done.append(gname)
        if verbose:
            print(f"  svg override: {gname} ({fn}, {len(ds)} path(s))")
    return done


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "export":
        export(sys.argv[2:])
    else:
        print(__doc__)
