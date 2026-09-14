#!/usr/bin/env python3
"""Build docs/index.html, the landing page, and refresh the navigation block
on every static page (master.html gets its nav from gen_master.py directly).

The landing introduces each page as a tile: a live specimen, the tease from
scripts/pages.py, and the current counts read from the generated data files.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine
import pages

MARK_H1 = pages._mark('.95em', '-.12em', '.3em')   # the mark before the title
STATIC_PAGES = ['description.html', 'play.html', 'fonts.html', 'inspect.html']


def refresh_nav():
    for fn in STATIC_PAGES:
        path = os.path.join(ROOT, 'docs', fn)
        html = open(path).read()
        block = pages.nav_block(fn)
        if pages.MARK0 in html:
            html = re.sub(re.escape(pages.MARK0) + '.*?' + re.escape(pages.MARK1),
                          lambda m: block, html, count=1, flags=re.S)
        else:
            anchor = '<main class="wrap">'
            assert anchor in html, f'{fn}: no wrap to hang the nav on'
            html = html.replace(anchor, anchor + '\n\n' + block, 1)
        open(path, 'w').write(html)
    print(f'nav refreshed on {", ".join(STATIC_PAGES)}')


def stats():
    play = open(os.path.join(ROOT, 'docs', 'play-data.js')).read()
    dia = json.loads(re.search(r'const DIA = (.*);', play).group(1))
    fonts = open(os.path.join(ROOT, 'docs', 'fonts-data.js')).read()
    matrix = json.loads(re.search(r'const MATRIX = (.*);', fonts).group(1))
    cells = [c for sec in matrix.values() for row in sec['rows']
             for c in row['cells'] if c]
    used = sum(1 for c in cells if c.get('langs'))
    forms = {f for l in dia['langs'].values() for f in l['readings']}
    return len(forms), len(dia['langs']), len(cells), used


def landing():
    forms, langs, glyphs, used = stats()
    g = engine.glyph
    specimens = {
        'description.html':
            f'<span class="ug">t {g("tj")} {g("tx")} {g("ty")} {g("txy")}</span>',
        'master.html':
            f'<span class="ug">{g("sj")}</span> <span class="arrow">=</span> '
            '<span class="ug">/ʃ/</span>',
        'play.html':
            '<code>sjy</code><span class="arrow">→</span><span class="ug">'
            f'{g("sjy")}</span> <code>txy</code><span class="arrow">→</span>'
            f'<span class="ug">{g("txy")}</span> <code>aw</code>'
            f'<span class="arrow">→</span><span class="ug">{g("aw")}</span>',
        'fonts.html':
            f'<span class="ug">{g("sj")} {g("zj")} {g("tqy")} {g("dq")} '
            f'{g("sxy")} {g("acw")} {g("ecw")}</span>',
        'inspect.html':
            f'<span class="ug">{g("tj")}</span><span class="arrow">→</span>'
            '<code>advance 393 · anchor −330</code>',
    }
    notes = {
        'master.html': f'{forms} forms · {langs} languages',
        'fonts.html': f'{glyphs} glyphs · {used} in use',
    }
    tiles = ''
    for fn, label, tease in pages.PAGES:
        note = f'<span class="note">{notes[fn]}</span>' if fn in notes else ''
        tiles += f'''
  <a class="tile" href="{fn}">
    <div class="spec">{specimens[fn]}</div>
    <h2>{label}{note}</h2>
    <p>{tease}</p>
  </a>'''
    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diafon</title>
<style>
:root{{
  --paper:#f5f6f8; --card:#ffffff; --sunken:#eef0f4; --ink:#1a1d24; --muted:#5b6472; --line:#dde1e8;
  --accent:#0e7c86;
  --serif:"Diafon","Charis SIL","Gentium Plus","Noto Serif","Times New Roman",Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  --mono:"SF Mono","JetBrains Mono","Menlo","Consolas",monospace;
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
  --paper:#14161b; --card:#1b1e25; --sunken:#101216; --ink:#e9ecf1; --muted:#98a1b0; --line:#2a2e37;
  --accent:#3ec8cf;
}}}}
:root[data-theme="dark"]{{
  --paper:#14161b; --card:#1b1e25; --sunken:#101216; --ink:#e9ecf1; --muted:#98a1b0; --line:#2a2e37;
  --accent:#3ec8cf;
}}
@font-face{{font-family:"Diafon";src:url(diafon.woff2) format("woff2");font-display:swap}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.6;font-size:15px;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1020px;margin:0 auto;padding:clamp(1.6rem,5vw,3.5rem) clamp(1rem,4vw,2rem) 4rem}}
h1{{font-family:var(--serif);font-weight:600;font-size:clamp(2.2rem,6vw,3.2rem);letter-spacing:-.01em;margin:0 0 .3rem}}
.lede{{color:var(--muted);max-width:64ch;margin:.2rem 0 0;font-size:1.05rem}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;margin-top:2.2rem}}
.tile{{display:block;background:var(--card);border:1px solid var(--line);border-radius:16px;
  padding:1.2rem 1.3rem 1.1rem;text-decoration:none;color:var(--ink);
  transition:border-color .15s, transform .15s}}
.tile:hover{{border-color:var(--accent);transform:translateY(-2px)}}
.tile .spec{{font-size:1.9rem;line-height:1.25;min-height:3.2rem;display:flex;align-items:center;gap:.45rem;flex-wrap:wrap}}
.tile .spec .ug{{font-family:var(--serif)}}
.tile .spec .arrow{{color:var(--muted);font-size:1.05rem}}
.tile .spec code{{font:600 .8rem/1 var(--mono);color:var(--accent);background:var(--sunken);padding:.18em .4em;border-radius:.35em}}
.tile h2{{font:600 .78rem/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--accent);margin:.7rem 0 .35rem;display:flex;gap:.7rem;align-items:baseline;flex-wrap:wrap}}
.tile h2 .note{{color:var(--muted);font-weight:600;text-transform:none;letter-spacing:.02em}}
.tile p{{margin:0;color:var(--muted);font-size:.92rem}}
footer{{margin-top:3.5rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.85rem}}
</style>
</head>
<body>
<main class="wrap">

<header>
  <h1>{MARK_H1}Diafon</h1>
  <p class="lede">One keyboard, one script, every language: a universal
  phonemic writing and input system.</p>
</header>

<div class="tiles">{tiles}
</div>

<footer>
  Diafon · working draft · generated by <code style="font-family:var(--mono)">scripts/gen_site.py</code>
</footer>

</main>
</body>
</html>
'''
    out = os.path.join(ROOT, 'docs', 'index.html')
    open(out, 'w').write(html)
    print(f'{out}: landing with {len(pages.PAGES)} tiles '
          f'({forms} forms, {langs} languages, {glyphs} glyphs)')


if __name__ == '__main__':
    refresh_nav()
    landing()
