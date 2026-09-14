# Diafon font

## Three families, one chain (fonts/build.sh)

`families.yaml` lists the families, each derived from a Noto face of the same
metrics: **Diafon Serif** (Noto Serif), **Diafon Sans** (Noto Sans) and
**Diafon Mono** (Noto Sans Mono); the sans faces take the logo's hooked tail
for the anchor (`stroke.hook` in `families.yaml`: it leaves the letter's
bottom outer corner flush and stem-wide, bends toward the middle and ends in a round cap
a little below p) instead of the serifed straight stroke. `fonts/build.sh [serif sans mono]` runs, per family:

    derive from Noto  ->  UFO sources  ->  fontmake  ->  FontBakery gate  ->  web subsets + proof
    tools/build_font.py   tools/make_ufo.py   fontmake     check-googlefonts    tools/subset_web.py
    build/<Family>-derived.ttf  sources/<Family>-Regular.ufo  <Family>-Regular.ttf  docs/diafon[-sans|-mono].woff2

- `tools/build_font.py <family>` derives an intermediate font from the family's Noto face:
  the charset (the system's glyphs, every mark it defines, Google Fonts' Latin
  Core set), the anchor family from `anchor.yaml`, the baked letter+mark
  glyphs, and the web letters pointed at the compositions they stand for.
- `tools/make_ufo.py <family>` extracts the editable sources, `sources/<Family>-Regular.ufo`:
  the reachable glyphs with their anchors and kerning, our own small
  `features.fea` (ccmp for the compositions, dotless i j, the f ligatures;
  fontmake writes kern, mark and mkmk from the UFO's data), font info to
  Google Fonts' rules, glyph categories and the meta table. Regenerated on
  every build; hand edits belong upstream, in the SVG overrides or the tools.
- `fontmake` compiles the UFO into the shipping `<Family>-Regular.ttf`
  (unhinted; `tools/finish_font.py` adds the dropout-control prep and gasp
  tables), then FontBakery's googlefonts profile must report no failures
  (`fonts/build/fontbakery-<family>.txt` holds the report) before the web
  subsets and the proof sheet are refreshed. The pages load the serif as
  `diafon.woff2`; the fonts page offers all three.

Tools: `pip3 install --user fontmake 'fontbakery[googlefonts]' ufo-extractor skia-pathops`
(they land in `~/Library/Python/3.9/bin`).

## SVG overrides

Any `fonts/svg/<glyphname>.svg` replaces that glyph's outline at build time.
`tools/font_svg.py export 0329 s t` writes editable SVGs with the em box and
guide lines; edit only the paths inside `<g id="glyph">`; deleting a file
returns the glyph to its procedural or Noto shape. Some marks exist twice, a
combining glyph and a positioned variant referenced by precomposed letters
(uni0307 and dotaccent, uni0308 and dieresis, acutecomb and acute, tildecomb
and tilde, uni0304 and uni02C9, uni030D and uni030E): edit both of a pair
identically or the two renderings drift apart. The anchors and dots are
procedural (`anchor.yaml`, `families.yaml`); an SVG override wins over them.

## The handwriting capture

`hand/` grows the original hand, serif and sans families from one set of
samples: `tools/hand_frame.py` draws the drawing frame, `tools/hand_read.py`
reads a drawn copy back into per-glyph SVGs under `hand/glyphs/`, and
`tools/hand_design.py` builds glyphs described in text (`hand/design.yaml`).
See `hand/README.md`.
