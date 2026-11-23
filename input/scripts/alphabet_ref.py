"""The alphabet's Python reference, for the generators that need a language
read or written (stages, lexicons, the mapping): a checkout of
diafon-org/diafon, at $DIAFON_ALPHABET or beside this repository, at the
commit vendor/ALPHABET records. Importing this module puts its scripts on
the path: then `import script, stages, lexicon, mapping`.

The engine and the ports do not use it: they read vendor/ only.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.abspath(os.environ.get('DIAFON_ALPHABET') or os.path.join(ROOT, '..', 'diafon'))

if not os.path.exists(os.path.join(PATH, 'scripts', 'script.py')):
    sys.exit(f'the alphabet checkout is not at {PATH}: set DIAFON_ALPHABET (scripts/sync_alphabet.py)')
sys.path.insert(0, os.path.join(PATH, 'scripts'))


def check():
    """Warn when the checkout is not the commit that was vendored."""
    want = dict(l.split(': ', 1) for l in open(os.path.join(ROOT, 'vendor', 'ALPHABET')).read().splitlines())['commit'].split()[0]
    have = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=PATH, text=True).strip()
    if have != want:
        print(f'note: the alphabet checkout is at {have[:7]}, vendor/ holds {want[:7]}: run scripts/sync_alphabet.py',
              file=sys.stderr)
    return have == want
