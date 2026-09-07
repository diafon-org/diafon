#!/usr/bin/env python3
"""Generate fonts/hand/template.html, the printable handwriting capture sheets.

Print on A4 (100% scale, no fit-to-page), fill with a black 0.5-0.8mm pen,
then scan at 300dpi or photograph flat and straight-on with all four corner
markers visible. One image per page goes to fonts/hand/samples/page<N>.jpg;
fonts/tools/hand_trace.py turns them into per-glyph SVGs.

Each row is a writing strip with shared guides: ascender (dotted), x-height
(dashed), baseline (solid), descender (dotted). The label above each cell
names what to write; write naturally, aligned to the guides, and do not
touch the cell borders. Spoiled attempts are fine, just leave them: every
glyph has repeats and the best one is picked by hand later.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'fonts', 'hand', 'template.html')

LOWER = list('abcdefghijklmnopqrstuvwxyz')
MARKED = ['ș sj', 'ț tj', 'n̦ nj', 'ṭ tx', 't̤ txy', 't̖ ty',
          'á aw', 'à ay', 'ä ac', 'a̋ acw', 'ő ecw', 'ạ aj', 'g̓ gj']
GESTURES = ['◌̦ anchor', '◌̖ reverse', '◌́ acute', '◌̈ two dots']
DIGITS = list('0123456789')
UPPER = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
PUNCT = list('.,;:!?\'"()-')
LINES = ['the quick brown fox jumps over the lazy dog',
         'sphinx of black quartz judge my vow',
         'ța c̖u t̤in á sjoveri mạ']

# (page title, [(items, repeats, cells per strip)])
PAGES = [
    ('1 · lowercase', [(LOWER, 3, 9)]),
    ('2 · marks and digits', [(MARKED, 3, 8), (GESTURES, 4, 8), (DIGITS, 2, 10)]),
    ('3 · capitals, punctuation, free lines', [(UPPER, 2, 10), (PUNCT, 2, 11)]),
]

CSS = '''
@page{size:A4;margin:0}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,"Segoe UI",sans-serif;color:#333}
.page{width:210mm;height:296mm;position:relative;padding:14mm 12mm;page-break-after:always}
.fid{position:absolute;width:7mm;height:7mm;background:#000}
.fid.tl{top:5mm;left:5mm}.fid.tr{top:5mm;right:5mm}
.fid.bl{bottom:5mm;left:5mm}.fid.br{bottom:5mm;right:5mm}
h1{font-size:11pt;margin:0 0 2mm;font-weight:600}
p.help{font-size:8pt;color:#666;margin:0 0 4mm;line-height:1.45}
.strip{position:relative;display:flex;border:0.5mm solid #000;height:19mm;margin-top:6mm}
.cell{flex:1;position:relative;border-left:0.15mm solid #99c}
.cell:first-child{border-left:none}
.lab{position:absolute;top:-4.6mm;left:0;right:0;text-align:center;
  font-size:7.5pt;color:#777;font-family:Georgia,serif}
.lab code{font-family:Menlo,monospace;font-size:6.5pt;color:#a66}
.g{position:absolute;left:0;right:0;height:0;border-top-style:solid;border-top-color:#c8cede}
.g.asc{top:2mm;border-top-width:0.1mm;border-top-style:dotted}
.g.xh{top:6.5mm;border-top-width:0.15mm;border-top-style:dashed}
.g.base{top:13mm;border-top-width:0.25mm;border-top-color:#8892aa}
.g.desc{top:17.5mm;border-top-width:0.1mm;border-top-style:dotted}
.freeline{position:relative;border:0.5mm solid #000;height:19mm;margin-top:8mm}
.freeline .lab{text-align:left;padding-left:1mm}
.pageno{position:absolute;bottom:6mm;left:0;right:0;text-align:center;
  font-size:8pt;color:#999}
'''

HELP = ('Black 0.5&ndash;0.8&nbsp;mm pen. Write each item once per cell, naturally, '
        'small letters sitting on the <b>solid baseline</b> reaching the '
        '<b>dashed x-height</b>; ascenders toward the dotted top line, descenders '
        'toward the dotted bottom. Do not touch the cell borders; a spoiled cell '
        'is fine, leave it. For the marked letters write letter and mark in one '
        'natural gesture; the gray label shows the target and its typing.')


def strip_html(items):
    cells = ''
    for it in items:
        parts = it.split(' ', 1)
        lab = (f'<span class="lab">{parts[0]} <code>{parts[1]}</code></span>'
               if len(parts) == 2 and parts[1] else
               f'<span class="lab">{parts[0]}</span>')
        cells += f'<div class="cell">{lab}</div>'
    guides = ''.join(f'<div class="g {c}"></div>'
                     for c in ('asc', 'xh', 'base', 'desc'))
    return f'<div class="strip">{guides}{cells}</div>'


def main():
    body = ''
    for pi, (title, groups) in enumerate(PAGES, 1):
        strips = ''
        for items, repeats, per in groups:
            seq = [it for it in items for _ in range(repeats)]
            for i in range(0, len(seq), per):
                strips += strip_html(seq[i:i + per])
        if pi == 3:
            for line in LINES:
                strips += (f'<div class="freeline"><span class="lab">{line}'
                           '</span><div class="g xh"></div>'
                           '<div class="g base"></div></div>')
        head = (f'<h1>Diaphone handwriting capture · sheet {title}</h1>'
                + (f'<p class="help">{HELP}</p>' if pi == 1 else ''))
        body += (f'<div class="page">'
                 '<div class="fid tl"></div><div class="fid tr"></div>'
                 '<div class="fid bl"></div><div class="fid br"></div>'
                 f'{head}{strips}'
                 f'<div class="pageno">diaphone hand · page {pi} of {len(PAGES)}'
                 '</div></div>')
    html = (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<title>Diaphone handwriting capture</title>\n<style>{CSS}</style>\n'
            f'</head>\n<body>\n{body}\n</body>\n</html>\n')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w').write(html)
    n = sum(len(items) * reps for _, groups in PAGES for items, reps, _ in groups)
    print(f'{os.path.relpath(OUT, ROOT)}: {len(PAGES)} pages, {n} cells')


if __name__ == '__main__':
    main()
