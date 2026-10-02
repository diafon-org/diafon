# The handwriting capture

Three styles grow from one set of samples: the faithful hand, and a serif
and a sans regularised from the same skeletons and proportions. The samples
arrive by any of three routes; all end in per-glyph SVGs for review.

## The drawing sheet (draw on paper under the glyphs)

`python3 fonts/tools/hand_sheet.py` writes `sheet.html` and `sheet.pdf`: every
glyph in use in a thin top row per strip, its input form beside it, and
blank space beneath to draw in; one A4 page, print at 100%. `--family sans`
or `mono` sets the reference face, `--reserve` adds the grammar's reserve,
`--per-row N` the glyphs per strip.

## The digital frame (draw in a vector editor)

`frame.svg` has the structure of the fonts page: bases across, derivations
down, one cell per potential glyph, then the extras a font needs (the other
letters, capitals, digits, punctuation). Each cell shows the writing guides
(ascender, cap height, x-height, baseline, descender), the input form, the
codepoints and a small pale reference in the Diafon font.

1. Open `frame.svg` in any vector editor: Inkscape, Illustrator, Affinity,
   or an iPad app that opens and exports SVG. In Inkscape the `ink` layer is
   already current and the frame layer is locked.
2. Draw each glyph inside its cell, in black (any dark colour), with a
   stroked pen or filled brush shapes; the pen's width is honoured. Marks go
   where the reference puts them; letter and mark need not touch unless the
   reference's do (the anchors attach).
3. Save as SVG (plain or the editor's flavour) to `drawn.svg` here, and run

       python3 fonts/tools/hand_read.py            # or: hand_read.py path/to/file.svg

   It finds the ink by colour and position, so flattened layers, dropped
   ids, moved or re-scaled artwork and a changed viewBox do no harm (the
   four black corner squares register the drawing), traces every drawn
   cell into one filled outline and writes:

   - `glyphs/<glyph name>.svg`: one per drawn cell, in the format
     `fonts/tools/font_svg.py` imports (em box, guides, `g#glyph`), named
     as the font names the glyph (`t_uni0324` for t̤, `uni021B` for ț;
     capitals by codepoint, `uni0041` for A, since a and A cannot share a
     folder on a case-insensitive disk; `data-glyph` on the file's root
     carries the glyph name);
   - `review.svg`: the frame again with every traced glyph in black over
     its pale reference and the analysis flags under it;
   - `analysis.json`: per cell the pieces found against the reference,
     baseline and top alignment, width ratio, advance, ink box.

Regenerate the frame with `python3 fonts/tools/hand_frame.py` (add
`--ghost` for a full-size pale copy of the target inside each cell to write
over); `frame.json` is its manifest and must stay beside it.

## The description (write glyphs as text)

`design.yaml` describes glyphs in words and numbers: font units, y up,
baseline 0, heights by name (`xh`, `asc`, `cap`, `desc`, `base`) with
arithmetic; a stroke is a list of points, space for straight and `~` for a
smooth curve through, drawn with the pen's width and cap; fills are closed
shapes (a hole is a fill the other way round); dots are `x,y radius`; `use`
composes glyphs from others with offsets, flips and scale (a letter and its
mark, the reverse anchor from the anchor). The file's header states the
whole format; the entries in it are examples of every feature.

    python3 fonts/tools/hand_design.py             # -> design.svg, the proof
    python3 fonts/tools/hand_design.py --outline   # with the traced outline overlaid
    python3 fonts/tools/hand_design.py --build     # -> glyphs/<name>.svg as well

The proof shows every glyph on the guides over its pale Diafon reference,
with its points and coordinates and the resulting ink box and advance, so
the numbers can be tuned in the text and re-viewed. The build traces each
glyph through the same pipeline as the drawn frame into the same folder
and format; bare marks get zero advance.

## Paper (print, write, scan)

1. Open `template.html` in a browser, print at 100% on A4 (no fit-to-page).
2. Fill the three sheets with a black 0.5-0.8 mm pen, per the sheet notes.
3. Scan at 300 dpi (best) or photograph flat, straight-on, all four corner
   squares visible; good even light, no shadows.
4. Drop the images here as `samples/page1.jpg`, `samples/page2.jpg`,
   `samples/page3.jpg` (png works too).
5. `fonts/tools/hand_trace.py` (built when samples exist) dewarps by the
   corner squares, cuts the cells, and traces each glyph to
   `svg/<name>.svg` for review before any font is built.

The traced glyphs never go to `fonts/svg/<family>/`, which overrides the
Diafon fonts at build time (though their format is the same, and copying one
there is a way to put a drawn shape into the Diafon serif); the hand fonts
are assembled from `glyphs/` by their own builder, still to come.
