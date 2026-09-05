#!/usr/bin/env python3
"""Render fonts/proof.png — the annotated anchor proof sheet.

Big shaped specimens (harfbuzz-positioned, what browsers do) over guide lines:
baseline, x-height, and the anchor's attach/tip lines from fonts/anchor.yaml.
The parameter dump is printed on the sheet, so instructions can be given as
numbers against named knobs.
"""
import os

import freetype
import uharfbuzz as hb
import yaml
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = os.path.join(ROOT, 'fonts', 'Diaphone-Regular.ttf')
OUT = os.path.join(ROOT, 'fonts', 'proof.png')
SIZE = 330
TEXT = 'ș s̖ ț t̖ m̦ p̓ p̔ g̓'

def main():
    P = yaml.safe_load(open(os.path.join(ROOT, 'fonts', 'anchor.yaml')))
    blob = hb.Blob.from_file_path(FONT)
    face = hb.Face(blob)
    font = hb.Font(face)
    scale = SIZE / face.upem
    buf = hb.Buffer(); buf.add_str(TEXT); buf.guess_segment_properties()
    hb.shape(font, buf)
    ft = freetype.Face(FONT); ft.set_char_size(SIZE * 64)

    W, H = 2100, 760
    img = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(img)
    base_y = H * 0.58

    # guides: baseline, x-height, attach, tip
    xh = 480  # Noto Serif x-height in em units (close enough for guides)
    guides = [(0, 'baseline', (160, 160, 160)),
              (xh, 'x-height', (160, 160, 160)),
              (P['attach'], f"attach {P['attach']}", (70, 140, 200)),
              (P['tip'], f"tip {P['tip']}", (200, 90, 90))]
    for em_y, label, color in guides:
        y = base_y - em_y * scale
        d.line([(20, y), (W - 20, y)], fill=color, width=1)
        d.text((W - 240, y - 16), label, fill=color)

    x = 60.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        ft.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
        bm = ft.glyph.bitmap
        gx = int(x + pos.x_offset * scale + ft.glyph.bitmap_left)
        gy = int(base_y - pos.y_offset * scale - ft.glyph.bitmap_top)
        if bm.width:
            tile = Image.frombytes('L', (bm.width, bm.rows), bytes(bm.buffer))
            img.paste((20, 20, 20), (gx, gy), tile)
        x += pos.x_advance * scale

    d.text((30, 20), 'fonts/anchor.yaml — ' + ' · '.join(
        f'{k}: {v}' for k, v in P.items()), fill=(60, 60, 60))
    d.text((30, 44), TEXT + '   (edit the yaml, rebuild, re-proof)', fill=(120, 120, 120))
    img.save(OUT)
    print(f'{OUT} written')


if __name__ == '__main__':
    main()
