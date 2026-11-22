#!/bin/sh
# The build chain, in order; run from anywhere. Fails on the first error.
# The engine reads vendor/ (scripts/sync_alphabet.py takes it from the
# alphabet checkout). The typing from before the split and its ports' data
# generators sleep in legacy/ and are not built.
set -e
cd "$(dirname "$0")/.."
python3 scripts/compile_profile.py
python3 tests/test_profile.py
