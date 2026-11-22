#!/usr/bin/env python3
"""Copy the Input page into the site: docs/input/, as the typing's own
repository built it, with the commit it was taken from (docs/input/SOURCE).

The page is not the alphabet's: nothing here reads it, generates it or
tests its content, and the alphabet's data, scripts and other pages stay
free of typing (tests/test_no_input.py). The site only carries it.

Usage: sync_input_page.py [path to the checkout]   (default: $DIAFON_TYPING, then ../diafon-input)
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'input')
FILES = ['index.md', 'input.css', 'input.js', 'input-data.js', 'diafon-keys.js', 'lessons-data.js']


def main():
    src = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DIAFON_TYPING') or os.path.join(ROOT, '..', 'diafon-input'))
    web = os.path.join(src, 'web')
    assert os.path.isdir(web), f'no web/ in {src}'
    os.makedirs(OUT, exist_ok=True)
    for name in FILES:
        shutil.copyfile(os.path.join(web, name), os.path.join(OUT, name))
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=src, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain', 'web'], cwd=src, text=True).strip()
    with open(os.path.join(OUT, 'SOURCE'), 'w', encoding='utf-8') as f:
        f.write(f'commit: {commit}{" (with uncommitted changes)" if dirty else ""}\nfiles: {" ".join(FILES)}\n')
    print(f'docs/input: {len(FILES)} files from {commit[:7]}')


if __name__ == '__main__':
    main()
