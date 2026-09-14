#!/usr/bin/env python3
"""Finish the fontmake output for shipping: the unhinted font gets the
'prep' program that turns on smart dropout control and a 'gasp' table
(what gftools fix-nonhinting does), so it rasterises cleanly at small sizes
on Windows. In place: python3 fonts/tools/finish_font.py [font.ttf]
"""
import os
import sys

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables.ttProgram import Program

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = os.path.join(ROOT, 'fonts', 'DiafonSerif-Regular.ttf')


def main(path=FONT):
    font = TTFont(path)
    if 'prep' not in font or not getattr(font['prep'], 'program', None):
        prep = newTable('prep')
        prep.program = Program()
        prep.program.fromAssembly(['PUSHW[ ]', '511', 'SCANCTRL[ ]', 'PUSHB[ ]', '4', 'SCANTYPE[ ]'])
        font['prep'] = prep
    if 'gasp' not in font:
        gasp = newTable('gasp')
        gasp.version = 1
        gasp.gaspRange = {0xFFFF: 15}          # grayscale + gridfit + symmetric, all sizes
        font['gasp'] = gasp
    font['head'].flags |= 1 << 3                # ppem rounded to integers
    font.save(path)
    print(f'{os.path.relpath(path, ROOT)}: prep/gasp in place, {font["maxp"].numGlyphs} glyphs')


if __name__ == '__main__':
    main(*sys.argv[1:2])
