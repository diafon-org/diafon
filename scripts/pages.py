"""The site layer: the page registry and the shared navigation block.

The minimal build framework for the static pages. scripts/gen_site.py builds
docs/index.html (the landing tiles) and refreshes the navigation on every
static page; scripts/gen_master.py imports nav_block() when it renders
master.html. The block is self-contained (style + markup) between sitenav
markers, so a refresh is a single replace and pages need no other support.
"""

PAGES = [
    ('description.html', 'description',
     'What the system is: the cornerstones, bases and operators, the marks, '
     'and the two triangles.'),
    ('master.html', 'master tables',
     "Every input form in use, its glyph and readings; each language's own "
     'table, stamped with its review state.'),
    ('play.html', 'playground',
     'Type the input form, read the script form, live, per language.'),
    ('fonts.html', 'fonts',
     'Every glyph the system can draw, in the Diaphone font or any other, '
     'with the support gaps.'),
]

MARK0, MARK1 = '<!-- sitenav -->', '<!-- /sitenav -->'

NAV_CSS = '''<style>
nav.sitenav{display:flex;gap:1.1rem;align-items:baseline;flex-wrap:wrap;
  font:600 .72rem/1 var(--mono);letter-spacing:.05em;text-transform:uppercase;
  margin:0 0 1.7rem;padding-bottom:.85rem;border-bottom:1px solid var(--line)}
nav.sitenav a{color:var(--muted);text-decoration:none}
nav.sitenav a:hover{color:var(--accent)}
nav.sitenav a.brand{color:var(--ink);font-family:var(--serif);font-size:1rem;
  font-weight:600;text-transform:none;letter-spacing:0;margin-right:.4rem}
nav.sitenav .here{color:var(--accent)}
</style>'''


def nav_block(current):
    items = ''.join(
        f'<span class="here">{label}</span>' if fn == current
        else f'<a href="{fn}">{label}</a>'
        for fn, label, _ in PAGES)
    return (f'{MARK0}\n{NAV_CSS}\n<nav class="sitenav">'
            f'<a class="brand" href="index.html">Diaphone</a>{items}</nav>\n{MARK1}')
