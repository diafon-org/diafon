#!/usr/bin/env python3
"""The long consonants in the shipping fonts. Run: python3 tests/test_font_long.py

1. Every family maps ZWJ and ZWNJ to a glyph with no ink and no advance.
2. HarfBuzz: every long consonant the engine writes joined (t ZWJ t) shapes
   to its <letter>.long when the family ships that pair (drawn), and to the
   two letters with an empty ZWJ between them when it does not; the plain
   double (tt) and the ZWNJ-split pair never fuse.
3. CoreText (macOS, with swiftc): the same for the joined, plain and split
   pair of every long consonant.
"""
import os
import shutil
import subprocess
import sys
import tempfile

import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
sys.path.insert(0, os.path.join(ROOT, 'fonts', 'tools'))
import build_font as BF
import engine

LONG = [f for f in engine.inventory() if f.endswith('w') and f[0] in engine.C_BASES]
HIDDEN = ('uni200D', 'uni200C', 'space')     # a shaper may hide a joiner as an empty space


def letters(names):
    """Glyph names with the joiners left out and the stock ff ligature as two
    f: HarfBuzz ligates f ZWJ f (ZWJ asks for a ligature), CoreText does not."""
    return [p for n in names if n not in HIDDEN for p in (['f', 'f'] if n == 'f_f' else [n])]


def shape(font, text):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    names = [font.get_glyph_name(i.codepoint) for i in buf.glyph_infos]
    return names, [p.x_advance for p in buf.glyph_positions]


def families():
    for key in BF.family_keys():
        path = BF.family(key)['ttf']
        if os.path.exists(path):
            yield key, path


def test_joiners():
    for key, path in families():
        f = TTFont(path)
        cmap, gs = f.getBestCmap(), f.getGlyphSet()
        for cp in (0x200D, 0x200C):
            assert cp in cmap, (key, f'U+{cp:04X} unmapped')
            g = cmap[cp]
            assert f['hmtx'][g][0] == 0, (key, g, 'has an advance')
            assert f['glyf'][g].numberOfContours == 0, (key, g, 'has ink')


def test_harfbuzz():
    for key, path in families():
        names = set(TTFont(path).getGlyphOrder())
        font = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        fused = set()
        for form in LONG:
            joined, plain = engine.render(form, join=True), engine.render(form)
            got, adv = shape(font, joined)
            if len(got) == 1:
                assert got[0].endswith('.long'), (key, form, got)
                fused.add(got[0])
            else:
                assert not any(n.endswith('.long') for n in got), (key, form, got)
                zw = [a for n, a in zip(got, adv) if n in HIDDEN]
                assert zw == [0], (key, form, got, adv)          # the ZWJ is there and takes no room
            for text in (plain, plain[:len(plain) // 2] + '‌' + plain[len(plain) // 2:]):
                got, _ = shape(font, text)
                assert not any(n.endswith('.long') for n in got), (key, form, text, got)
        ship = {n for n in names if n.endswith('.long')}
        assert fused == ship, (key, ship - fused)                 # every pair the font ships is reached
        print(f'  {key}: {len(fused)} long glyphs reached')


CORETEXT = r'''
import CoreText
import Foundation
let url = URL(fileURLWithPath: CommandLine.arguments[1]) as CFURL
let desc = (CTFontManagerCreateFontDescriptorsFromURL(url) as! [CTFontDescriptor])[0]
let font = CTFontCreateWithFontDescriptor(desc, 40, nil)
while let s = readLine() {
  let a = NSAttributedString(string: s, attributes: [kCTFontAttributeName as NSAttributedString.Key: font])
  var names: [String] = []
  for run in CTLineGetGlyphRuns(CTLineCreateWithAttributedString(a)) as! [CTRun] {
    let n = CTRunGetGlyphCount(run)
    var g = [CGGlyph](repeating: 0, count: n)
    CTRunGetGlyphs(run, CFRange(location: 0, length: n), &g)
    for x in g { names.append((CTFontCopyNameForGlyph(font, x) as String?) ?? "\(x)") }
  }
  print(names.joined(separator: " "))
}
'''


def test_coretext():
    if sys.platform != 'darwin' or not shutil.which('swiftc'):
        print('  SKIP: CoreText needs macOS and swiftc')
        return
    out = tempfile.mkdtemp(prefix='diafon-ct-')
    src, exe = os.path.join(out, 'ct.swift'), os.path.join(out, 'ct')
    open(src, 'w').write(CORETEXT)
    res = subprocess.run(['xcrun', 'swiftc', '-O', src, '-o', exe], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    for key, path in families():
        hbfont = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        texts = []
        for form in LONG:
            plain = engine.render(form)
            texts += [engine.render(form, join=True), plain,
                      plain[:len(plain) // 2] + '‌' + plain[len(plain) // 2:]]
        res = subprocess.run([exe, path], input='\n'.join(texts) + '\n', capture_output=True, text=True)
        assert res.returncode == 0, res.stderr
        for text, line in zip(texts, res.stdout.split('\n')):
            got, want = letters(line.split()), letters(shape(hbfont, text)[0])
            assert got == want, (key, text, got, want)                        # as HarfBuzz shapes it
    print('  CoreText shapes every pair as HarfBuzz does')


if __name__ == '__main__':
    test_joiners()
    test_harfbuzz()
    test_coretext()
    print('long consonants hold in the fonts')
