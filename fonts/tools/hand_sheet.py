#!/usr/bin/env python3
"""Generate fonts/hand/sheet.html (and sheet.pdf where Chrome is present): a
printable sheet of the system's glyphs to draw under. Every glyph in use
(docs/fonts-data.js; --reserve adds the grammar's reserve) is set in a thin
top row of each strip, in one family (default the serif; --family sans|mono),
with its input form beneath in small type; the rest of the strip is blank
for drawing, with hairline cell borders and a faint baseline. Everything
fits one A4 page (--per-row N glyphs per strip, default 12).

    python3 fonts/tools/hand_sheet.py [--family serif|sans|mono] [--reserve] [--per-row 12]
"""
import base64
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_font as BF

OUT = os.path.join(ROOT, 'fonts', 'hand', 'sheet.html')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


def cells(reserve=False):
    src = open(os.path.join(ROOT, 'docs', 'fonts-data.js')).read()
    data = json.loads(re.search(r'const MATRIX = (.*);', src).group(1))
    out = []
    for sec in data.values():
        for row in sec['rows']:
            for c in row['cells']:
                if c and (c['langs'] or reserve):
                    out.append(c)
    return out


def main(argv):
    family, reserve, per_row = 'serif', False, 12
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == '--family':
            family = args.pop(0)
        elif a == '--reserve':
            reserve = True
        elif a == '--per-row':
            per_row = int(args.pop(0))
    fam = BF.family(family)
    font_b64 = base64.b64encode(open(fam['ttf'], 'rb').read()).decode()
    items = cells(reserve)
    rows = [items[i:i + per_row] for i in range(0, len(items), per_row)]
    # the page: A4 portrait, 10 mm margins; the strips share the height left
    page_h, margin, head = 297, 10, 9
    strip_h = (page_h - 2 * margin - head) / len(rows) - 1.2
    top_h = min(11, strip_h * 0.38)
    esc = lambda t: t.replace('&', '&amp;').replace('<', '&lt;')
    strips = []
    for row in rows:
        cs = ''.join(
            f'<div class="cell"><div class="top"><span class="g">{esc(c["g"])}</span>'
            f'<span class="f">{esc(c["f"])}</span></div><div class="draw"></div></div>'
            for c in row)
        cs += '<div class="cell empty"><div class="top"></div><div class="draw"></div></div>' * (per_row - len(row))
        strips.append(f'<div class="strip">{cs}</div>')
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Diafon · drawing sheet</title>
<style>
@page{{size:A4;margin:0}}
@font-face{{font-family:"Diafon Sheet";src:url(data:font/ttf;base64,{font_b64}) format("truetype")}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,Helvetica,Arial,sans-serif;color:#000}}
.page{{width:210mm;height:296mm;padding:{margin}mm;page-break-after:always}}
h1{{font-size:9pt;font-weight:600;margin:0 0 1.5mm;color:#333}}
h1 span{{font-weight:400;color:#888;margin-left:3mm}}
.strip{{display:flex;height:{strip_h:.2f}mm;margin-bottom:1.2mm;border:0.35mm solid #000}}
.cell{{flex:1;border-left:0.12mm solid #99a;display:flex;flex-direction:column}}
.cell:first-child{{border-left:0}}
.top{{height:{top_h:.2f}mm;border-bottom:0.12mm solid #99a;position:relative;text-align:center}}
.g{{font-family:"Diafon Sheet",serif;font-size:{top_h * 2.05:.1f}pt;line-height:{top_h * 0.78:.2f}mm;display:block;margin-top:{top_h * 0.08:.2f}mm}}
.f{{position:absolute;right:0.6mm;bottom:0.3mm;font-size:5pt;color:#888;font-family:Menlo,monospace}}
.draw{{flex:1;position:relative}}
.draw:before{{content:"";position:absolute;left:0;right:0;top:64%;border-top:0.12mm dashed #bbc}}
.empty .top{{background:#f3f3f5}}
@media screen{{body{{background:#ddd}}.page{{background:#fff;margin:6mm auto;box-shadow:0 0 6mm rgba(0,0,0,.2)}}}}
</style></head><body>
<div class="page">
<h1>Diafon · {esc(fam["family"])} · draw beneath each glyph <span>{len(items)} glyphs · print at 100%</span></h1>
{''.join(strips)}
</div></body></html>
'''
    open(OUT, 'w').write(html)
    print(f'{os.path.relpath(OUT, ROOT)}: {len(items)} glyphs in {len(rows)} strips of {per_row}')
    pdf = OUT[:-5] + '.pdf'
    if os.path.exists(CHROME):
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        f'--print-to-pdf={pdf}', 'file://' + OUT], capture_output=True)
        if os.path.exists(pdf):
            print(f'{os.path.relpath(pdf, ROOT)} written')
    else:
        print('  (no Chrome: print sheet.html from a browser at 100%)')


if __name__ == '__main__':
    main(sys.argv[1:])
