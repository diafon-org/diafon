"""The alphabet's Python reference, for the generators that need a language
read or written (stages, lexicons, the mapping): the alphabet's scripts, one
folder up. Importing this module puts them on the path: then
`import script, stages, lexicon, mapping`.

The engine and the ports do not use it: they read the published
docs/alphabet-spec.json only.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.dirname(ROOT)

sys.path.insert(0, os.path.join(PATH, 'scripts'))
