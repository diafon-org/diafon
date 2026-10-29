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

## SVG overrides (fonts/tools/font_svg.py)

Any `fonts/svg/<family>/<glyphname>.svg` replaces that glyph's outline in that
family at build time (`serif`, `sans`, `mono`); deleting the file returns the
glyph to its procedural or Noto shape. The round trip:

    python3 fonts/tools/font_svg.py export serif dieresis uni0324 t A   # names, letters, codepoints
    python3 fonts/tools/font_svg.py export sans uni0324 --on t k        # ghost base letters, set by anchor
    # edit fonts/svg/serif/dieresis.svg in Inkscape (or any vector editor)
    python3 fonts/tools/font_svg.py check serif        # dry run: contours, warnings, fonts/build/svg-check-serif.svg
    fonts/build.sh serif

The export is a canvas at font scale: the em box, ascender, cap height,
x-height, baseline, descender, origin and advance as lines (and as Inkscape
guides, with a 10-unit grid), rulers in font units along the top and left, a
pale ghost of the exported shape, and the outline in the `glyph` layer as one
path per shape (a diaeresis is two, to move apart); the `guides` layer is
locked and ignored on import. Draw with fills only, in any nesting of groups,
transforms and clones; holes work by either fill rule and overlaps are
merged; strokes and text must become paths first (the check says so).
Whatever is drawn in the `cut` layer (above `glyph`, half see-through) is
taken away from the merged ink, so a letter can stay whole and visible while
an edit trims it; any fill colour is ink, so additions can be coloured apart.
`data-advance` on the root sets the advance width. Only a file named exactly
for a glyph is imported: a variant saved beside it (`n_uni0326-try.svg`) or a
file starting with `_` is kept but inert, so variants are swapped in by
renaming. Capitals are filed by
codepoint (`uni0041.svg` for A: a and A cannot share a folder on a
case-insensitive disk). A curated mark seeds every baked letter+mark
composition; a composition (`t_uni0324.svg`) can be curated as a whole too.
Some marks exist twice, a combining glyph and a positioned variant referenced
by precomposed letters (uni0307 and dotaccent, uni0308 and dieresis,
acutecomb and acute, tildecomb and tilde, uni0304 and uni02C9): edit both of
a pair identically or the two renderings drift apart.

**The serif's anchor compositions** (n̦ n̖ and the rest) are written into this
folder by `python3 fonts/tools/serif_tail.py`: the tail continues the right
stem of n m h d H M N J, or is drawn by hand (t s k b, read off Inkscape
edits) and borrowed by the letters with a like bottom, every stroke brought to
one weight; it lands on a one-sided plate, inward for the anchor and outward
for the anti-anchor. Edit a written file by hand like any override, or change
a number and regenerate. `hand/tails.pdf` (`tools/tail_sheet.py`) is a sheet
to draw the tails on by hand; `svg-archive-tails-scan/` keeps a set built from
a scanned sheet (and the study prototype), `svg-archive-tails-auto/` the
current set. The anchors and dots of the other families stay procedural
(`anchor.yaml`, `families.yaml`); an SVG override wins over them.

## The handwriting capture

`hand/` grows the original hand, serif and sans families from one set of
samples: `tools/hand_frame.py` draws the drawing frame, `tools/hand_read.py`
reads a drawn copy back into per-glyph SVGs under `hand/glyphs/`, and
`tools/hand_design.py` builds glyphs described in text (`hand/design.yaml`).
See `hand/README.md`.
