#!/usr/bin/env python3
"""The SVG round trip, as tests. Run: python3 -m pytest tests/test_font_svg.py

1. Export writes the canvas: origin, layers, rulers, one path per shape (a
   diaeresis two, an o one with its hole), capitals filed by codepoint, the
   ghost of --on; an existing override is not overwritten. The import gives
   the outlines back: bounds, contour count, advance and TrueType direction.
2. An editor's file imports: Inkscape layers and namedview, transforms on
   groups and clones, rects and circles, the even-odd hole kept a hole,
   hidden objects skipped, text and stroke-only paths skipped with a
   warning, the advance from data-advance.
3. A clone cycle is reported, not looped; a variant file beside a glyph
   file is inert.
4. The legacy canvas of the hand tools (viewBox at the ascent, no
   data-origin) imports at the right place, by codepoint file name.
5. check reports every file and writes the proof sheet.
"""
import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'fonts', 'tools'))
import font_svg as FS

FONT = os.path.join(ROOT, 'fonts', 'DiafonSerif-Regular.ttf')
NS = ('xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
      'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
      'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"')


class Tmp:
    def __enter__(self):
        self.d = tempfile.mkdtemp()
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d)


def write(d, name, text):
    with open(os.path.join(d, name), 'w', encoding='utf-8') as fh:
        fh.write(text)


def bounds(font, g):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[g].draw(pen)
    return pen.bounds


def contour_info(font, g):
    """[(bounds, signed area)] per contour, y up."""
    rec = RecordingPen()
    font.getGlyphSet()[g].draw(rec)
    out = []
    for _, pts in FS.contours(rec):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        out.append(((min(xs), min(ys), max(xs), max(ys)), FS.area(pts)))
    return out


def near(a, b, tol=2):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def test_export_and_roundtrip():
    with Tmp() as tmp:
        written = FS.export('serif', ['dieresis', 'o', 'A', 'uni0324', 'nosuchglyph'],
                            on=['t'], font_path=FONT, out_dir=tmp)
        assert sorted(os.path.basename(p) for p in written) == ['dieresis.svg', 'o.svg', 'uni0041.svg', 'uni0324.svg']
        text = open(os.path.join(tmp, 'dieresis.svg'), encoding='utf-8').read()
        root = ET.fromstring(text)
        orig = TTFont(FONT)
        assert root.get('data-origin') and root.get('data-advance') == str(orig['hmtx']['dieresis'][0])
        assert len(list(FS.glyph_layer(root))) == 2          # two dots, two paths
        assert len(list(FS.glyph_layer(ET.parse(os.path.join(tmp, 'o.svg')).getroot()))) == 1   # ring and hole, one path
        assert 'inkscape:groupmode="layer"' in text and 'sodipodi:guide' in text
        assert 'x-height' in text and 'cap height' in text and text.count('<text') > 40   # the rulers
        assert 'id="ghost"' in text and 'id="on-t"' in text
        assert FS.export('serif', ['o'], font_path=FONT, out_dir=tmp) == []                 # no overwrite without force
        assert FS.export('serif', ['o'], font_path=FONT, out_dir=tmp, force=True)

        font = TTFont(FONT)
        done = FS.import_overrides(font, 'serif', svg_dir=tmp, verbose=False)
        assert sorted(done) == ['A', 'dieresis', 'o', 'uni0324']
        for g in done:
            assert font['glyf'][g].numberOfContours == orig['glyf'][g].numberOfContours, g
            assert near(bounds(font, g), bounds(orig, g)), (g, bounds(font, g), bounds(orig, g))
            assert font['hmtx'][g] == orig['hmtx'][g], g
            outer = max(contour_info(font, g), key=lambda c: abs(c[1]))
            assert outer[1] < 0, g                     # TrueType: the outer contour clockwise


INKSCAPE_FILE = f'''<svg {NS} width="2260px" height="1560px" viewBox="0 0 2260 1560"
     data-origin="620 1200" data-advance="480">
  <sodipodi:namedview id="namedview1" showgrid="true"/>
  <defs id="defs1"><symbol id="local-square"><rect x="0" y="0" width="50" height="50"/></symbol></defs>
  <g inkscape:groupmode="layer" id="layer1" inkscape:label="guides" style="display:inline">
    <line x1="0" x2="2000" y1="1200" y2="1200" style="stroke:#88f"/>
    <path d="M0 0h100v100h-100z" style="fill:#000"/>
  </g>
  <g inkscape:groupmode="layer" id="layer2" inkscape:label="glyph" transform="translate(620,1200)">
    <rect id="body" x="0" y="-500" width="200" height="500" style="fill:#000000;stroke:none"/>
    <circle id="dot" cx="100" cy="-600" r="40" fill="black"/>
    <path id="ring" style="fill:#000;fill-rule:evenodd" d="M300,-100 h200 v-200 h-200 z M350,-150 h100 v-100 h-100 z"/>
    <rect id="hidden" x="900" y="-900" width="100" height="100" style="display:none"/>
    <path id="hair" d="M600,0 L700,-300" style="fill:none;stroke:#000;stroke-width:20"/>
    <text id="t" x="800" y="0" style="font-size:40px">abc</text>
    <use id="clone" xlink:href="#local-square" transform="matrix(2,0,0,2,700,-500)"/>
    <g id="grp" transform="rotate(90)"><rect x="0" y="-1000" width="10" height="10" style="fill:#000"/></g>
  </g>
</svg>
'''


def test_editor_file():
    with Tmp() as tmp:
        write(tmp, 'x.svg', INKSCAPE_FILE)
        pieces, warnings, adv = FS.read_glyph(os.path.join(tmp, 'x.svg'), (0, 1069))
        assert adv == 480 and len(pieces) == 5
        assert any('stroke-only' in w for w in warnings) and any('text' in w for w in warnings)
        font = TTFont(FONT)
        assert FS.import_overrides(font, 'serif', svg_dir=tmp, verbose=False) == ['x']
        assert font['hmtx']['x'][0] == 480
        info = contour_info(font, 'x')
        assert len(info) == 6, info
        assert near(bounds(font, 'x'), (0, -10, 1000, 640), 1)
        ring = [c for c in info if near(c[0], (300, 100, 500, 300), 1)]
        hole = [c for c in info if near(c[0], (350, 150, 450, 250), 1)]
        assert ring and hole and (ring[0][1] > 0) != (hole[0][1] > 0)   # the even-odd hole stays a hole
        assert any(near(c[0], (990, -10, 1000, 0), 1) for c in info)   # the rotated group
        assert any(near(c[0], (700, 400, 800, 500), 1) for c in info)  # the scaled local clone


def test_cut_layer():
    with Tmp() as tmp:
        write(tmp, 'x.svg', f'''<svg {NS} data-origin="0 1000">
  <g id="glyph" inkscape:groupmode="layer" inkscape:label="glyph"><rect x="0" y="0" width="400" height="1000"/><rect x="300" y="500" width="300" height="500" fill="#c8324e"/></g>
  <g id="layer2" inkscape:groupmode="layer" inkscape:label="cut" style="opacity:0.5"><rect x="100" y="400" width="100" height="100" fill="#2a7de1"/><rect x="500" y="900" width="200" height="200"/></g>
</svg>
''')
        pieces, warnings, _ = FS.read_glyph(os.path.join(tmp, 'x.svg'), (0, 1069))
        assert not warnings and [cut for _, _, cut in pieces] == [False, False, True, True]
        font = TTFont(FONT)
        assert FS.import_overrides(font, 'serif', svg_dir=tmp, verbose=False) == ['x']
        info = contour_info(font, 'x')
        assert len(info) == 2, info                                     # the coloured addition merged, a hole cut
        assert near(bounds(font, 'x'), (0, 0, 600, 1000), 1)
        assert any(near(c[0], (100, 500, 200, 600), 1) for c in info)   # the hole
        assert any(near(c[0], (0, 0, 600, 1000), 1) for c in info)      # the notch at the corner leaves the bounds


def test_cycle_and_variants():
    with Tmp() as tmp:
        write(tmp, 'c.svg', f'<svg {NS} data-origin="0 0"><defs><g id="a"><use href="#b"/></g><g id="b"><use href="#a"/></g></defs><g id="glyph"><use href="#a"/><rect x="0" y="-50" width="50" height="50"/></g></svg>')
        write(tmp, 'c-try.svg', f'<svg {NS} data-origin="0 0"><g id="glyph"><rect x="0" y="-500" width="500" height="500"/></g></svg>')
        write(tmp, '_c.svg', f'<svg {NS} data-origin="0 0"><g id="glyph"><rect x="0" y="-500" width="500" height="500"/></g></svg>')
        _, warnings, _ = FS.read_glyph(os.path.join(tmp, 'c.svg'), (0, 1069))
        assert any('refers back' in w for w in warnings)
        font = TTFont(FONT)
        assert FS.import_overrides(font, 'serif', svg_dir=tmp, verbose=False) == ['c']
        assert near(bounds(font, 'c'), (0, 0, 50, 50), 0)                # the small rect, not the variants


def test_legacy_canvas():
    with Tmp() as tmp:
        write(tmp, 'uni0323.svg', f'''<svg {NS} viewBox="-500 0 2000 1362" data-advance="0">
  <g id="guides"><line x1="-500" x2="1500" y1="1069" y2="1069"/></g>
  <g id="glyph"><path fill="#111" d="M0 1069h100v-100h-100z"/></g>
</svg>
''')
        font = TTFont(FONT)
        asc = font['hhea'].ascent
        assert FS.import_overrides(font, 'serif', svg_dir=tmp, verbose=False) == ['dotbelowcomb']
        assert near(bounds(font, 'dotbelowcomb'), (0, asc - 1069, 100, asc - 969), 0)
        assert font['hmtx']['dotbelowcomb'][0] == 0


def test_check():
    with Tmp() as tmp:
        FS.export('serif', ['o'], font_path=FONT, out_dir=tmp)
        write(tmp, 'zzz.svg', f'<svg {NS} data-origin="0 0"><g id="glyph"/></svg>')
        write(tmp, 'broken.svg', '<svg')
        out = os.path.join(tmp, 'check.svg')
        report = FS.check('serif', font_path=FONT, svg_dir=tmp, out=out)
        assert [(r[0], r[1], r[2]) for r in report] == [('broken', None, 0), ('o', 'o', 2), ('zzz', None, 0)]
        assert os.path.exists(out) and '<path' in open(out, encoding='utf-8').read()


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
