#!/usr/bin/env python3
"""Vendor the alphabet: copy the alphabet's spec and the lexicons it refers
to from a checkout of diafon-org/diafon into vendor/, and record what was
taken in vendor/ALPHABET (version, commit, sha256 of the spec).

Usage: sync_alphabet.py [path to the diafon checkout]   (default: $DIAFON_ALPHABET, then ../diafon)

The dependency runs one way: this repository reads the alphabet, the
alphabet knows nothing of it. The engine and the ports read only vendor/.
The generators that need a language read or written (the old spec, the
lessons, the emoji table) also run the alphabet's Python reference from the
same checkout, at the commit recorded here.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, 'vendor')


def checkout():
    return os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                           os.environ.get('DIAFON_ALPHABET') or os.path.join(ROOT, '..', 'diafon'))


def main():
    src = checkout()
    spec_path = os.path.join(src, 'docs', 'alphabet-spec.json')
    spec = json.load(open(spec_path, encoding='utf-8'))
    os.makedirs(os.path.join(VENDOR, 'lexicon'), exist_ok=True)
    shutil.copyfile(spec_path, os.path.join(VENDOR, 'alphabet-spec.json'))
    for code, L in spec['lexicons'].items():
        raw = open(os.path.join(src, L['file']), 'rb').read()
        assert hashlib.sha256(raw).hexdigest() == L['sha256'], f'{code}: the lexicon is not the one the spec names'
        open(os.path.join(VENDOR, 'lexicon', f'{code}.json'), 'wb').write(raw)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=src, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=src, text=True).strip())
    with open(os.path.join(VENDOR, 'ALPHABET'), 'w', encoding='utf-8') as f:
        f.write(f'version: {spec["version"]}\n'
                f'commit: {commit}{" (with uncommitted changes)" if dirty else ""}\n'
                f'sha256: {hashlib.sha256(open(spec_path, "rb").read()).hexdigest()}\n')
    print(open(os.path.join(VENDOR, 'ALPHABET')).read().strip())
    print(f'{len(spec["lexicons"])} lexicons, {len(spec["points"])} points')


if __name__ == '__main__':
    main()
