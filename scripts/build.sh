#!/bin/sh
# The build chain, in order; run from anywhere. Fails on the first error.
set -e
cd "$(dirname "$0")/.."
python3 scripts/gen_points.py
python3 scripts/gen_master.py
python3 scripts/gen_fonts.py
python3 scripts/gen_lexicon.py 2>/dev/null || echo "lexicon sources missing: data/lexicon/*.json kept as committed"
python3 scripts/gen_alphabet_spec.py
python3 scripts/gen_site.py
python3 scripts/gen_samples.py
python3 fonts/tools/subset_web.py
python3 tests/test_script.py
python3 tests/test_alphabet_spec.py
python3 tests/test_no_input.py
python3 tests/test_samples.py
python3 tests/test_font_long.py
python3 -m mkdocs build --strict      # docs/ (Markdown + the app pages) -> site/, what GitHub Pages serves
python3 scripts/gen_site_words.py     # the site's words in Diafon, for the script switch (reads site/)
