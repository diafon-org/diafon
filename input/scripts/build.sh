#!/bin/sh
# The build chain, in order; run from anywhere. Fails on the first error.
# The engine reads the published ../docs/alphabet-spec.json; the site shows
# web/ as its Input page (docs/input links to it). The typing from before the
# split and its ports' data generators sleep in legacy/ and are not built.
set -e
cd "$(dirname "$0")/.."
python3 scripts/compile_profile.py
python3 tests/test_profile.py
python3 tests/test_keys_js.py
python3 scripts/gen_lessons.py     # reads the alphabet's scripts and word lists
python3 scripts/gen_page.py
python3 tests/test_lessons.py
