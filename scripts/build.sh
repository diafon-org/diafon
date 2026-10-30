#!/bin/sh
# The build chain, in order; run from anywhere. Fails on the first error.
set -e
cd "$(dirname "$0")/.."
python3 scripts/gen_master.py
python3 scripts/gen_play.py
python3 scripts/gen_fonts.py
python3 scripts/gen_lexicon.py 2>/dev/null || echo "lexicon sources missing: data/lexicon/*.json kept as committed"
python3 scripts/gen_emoji.py
python3 scripts/gen_learn.py
python3 scripts/gen_spec.py
python3 scripts/gen_android.py
python3 scripts/gen_mac.py
python3 scripts/gen_site.py
python3 scripts/gen_samples.py
mkdir -p docs/lexicon extensions/browser/lexicon && cp data/lexicon/*.json docs/lexicon/ && cp data/lexicon/*.json extensions/browser/lexicon/
cp docs/engine.js extensions/browser/engine.js && cp docs/play-data.js extensions/browser/data.js   # the extension's copy
rm -rf extensions/firefox && cp -r extensions/browser extensions/firefox && mv extensions/firefox/manifest.firefox.json extensions/firefox/manifest.json   # Firefox: a background script, not a worker
python3 fonts/tools/subset_web.py
python3 tests/test_engine.py
python3 tests/test_spec.py
python3 tests/test_extension.py
python3 tests/test_kotlin.py
python3 tests/test_swift.py
python3 -m mkdocs build --strict      # docs/ (Markdown + the app pages) -> site/, what GitHub Pages serves
python3 scripts/gen_site_words.py     # the site's words in Diafon, for the script switch (reads site/)
