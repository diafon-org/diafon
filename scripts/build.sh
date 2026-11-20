#!/bin/sh
# The build chain, in order; run from anywhere. Fails on the first error.
# Needs the alphabet checkout ($DIAFON_ALPHABET, or ../diafon) for the
# generators that read a language; the engine and the ports read vendor/.
set -e
cd "$(dirname "$0")/.."
python3 scripts/compile_profile.py
python3 scripts/universal_v1.py export docs/lexicon    # the lexicons in typed forms, for the site's engine and the ports
python3 scripts/gen_play.py
python3 scripts/gen_emoji.py
python3 scripts/gen_learn.py
python3 scripts/gen_spec.py
python3 scripts/gen_android.py
python3 scripts/gen_mac.py
python3 tests/test_profile.py
python3 tests/test_engine.py
python3 tests/test_spec.py
python3 tests/test_samples.py
python3 tests/test_kotlin.py
python3 tests/test_swift.py
