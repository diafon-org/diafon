#!/bin/sh
# The build chain, in order; run from anywhere. Fails on the first error.
set -e
cd "$(dirname "$0")/.."
python3 scripts/gen_master.py
python3 scripts/gen_play.py
python3 scripts/gen_fonts.py
python3 scripts/gen_spec.py
python3 scripts/gen_android.py
python3 scripts/gen_site.py
python3 fonts/tools/subset_web.py
python3 tests/test_engine.py
python3 tests/test_spec.py
python3 tests/test_kotlin.py
