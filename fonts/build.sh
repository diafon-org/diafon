#!/bin/sh
# The font chain for every family in fonts/families.yaml; fails on the first error.
#   derive from Noto  ->  UFO sources  ->  fontmake  ->  finish  ->  FontBakery gate  ->  web subsets + proof
# Tools: pip3 install --user fontmake 'fontbakery[googlefonts]' ufo-extractor skia-pathops
set -e
cd "$(dirname "$0")/.."
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
FAMILIES=${*:-$(python3 -c "import sys; sys.path.insert(0,'fonts/tools'); import build_font as b; print(' '.join(b.family_keys()))")}
for key in $FAMILIES; do
  PS=$(python3 -c "import sys; sys.path.insert(0,'fonts/tools'); import build_font as b; print(b.family('$key')['ps'])")
  python3 fonts/tools/build_font.py $key
  python3 fonts/tools/make_ufo.py $key
  fontmake -u fonts/sources/$PS-Regular.ufo -o ttf --output-path fonts/$PS-Regular.ttf \
    --overlaps-backend pathops --no-production-names --flatten-components 2>&1 | grep -vE "^INFO|^DEBUG|instructionCompiler" || true
  test -f fonts/$PS-Regular.ttf
  python3 fonts/tools/finish_font.py fonts/$PS-Regular.ttf
  fontbakery check-googlefonts fonts/$PS-Regular.ttf -l FAIL --no-progress 2>/dev/null > fonts/build/fontbakery-$key.txt || true
  grep -E "^ *FAIL [A-Za-z]|ERROR: [0-9]" fonts/build/fontbakery-$key.txt | sed 's/^ *//'
  grep -qE "FAIL: 0\b" fonts/build/fontbakery-$key.txt || { echo "$key: FontBakery failures above (fonts/build/fontbakery-$key.txt)"; exit 1; }
  grep -E "^ *(FAIL|WARN|PASS): [0-9]" fonts/build/fontbakery-$key.txt | tr -s ' \n' ' '; echo " <- $PS"
done
python3 fonts/tools/subset_web.py
python3 fonts/tools/proof.py
