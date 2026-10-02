#!/usr/bin/env python3
"""Refresh the navigation block on every app page (master.html gets its nav
from gen_master.py directly). The written pages are Markdown under docs/,
built by MkDocs (mkdocs.yml); the app pages are copied through as they are.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import pages

STATIC_PAGES = ['play.html', 'fonts.html', 'inspect.html']


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


if __name__ == '__main__':
    refresh_nav()
