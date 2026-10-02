# For implementers

Everything that renders, reads or types Diafon consumes one
machine-readable file, [spec.json](spec.json), and must reproduce its
vectors. The Python engine in `scripts/engine.py` is the reference; the
JavaScript, Swift and Kotlin ports hold the same vectors.

## The three forms

- **Input form**: the 26 letters and digits. Total and uniquely segmented:
  every string of letters reads as exactly one sequence of points, greedily
  left to right, and no two forms concatenated ever re-read as anything
  else. Any character outside the letters and digits is raw and passes
  through.
- **Script form**: the input rendered as base letters plus combining
  marks, NFC-normalised. This is the text.
- **Stages**: the script rendered in a language's current orthography
  (`data/stages/<code>.yaml`). A stage is render-only: it never changes
  what a key means, so text typed for one stage reads in all of them. A
  stage states its one-way losses.

## The grammar

A segment is one base letter followed by at most two operators (c j q x y),
then w at most once and last, then tone digits. An operator or a digit never
starts a segment: strictly, such input is an error; leniently, it passes
through as typed. Case is orthographic: an uppercase base capitalizes its
point, operators fold case, a long consonant capitalizes its first letter
only.

## Streaming

An input method commits as the user types. Everything before the last
segment is final; a last segment that is a form may still grow, so it stays
pending until a character arrives that cannot extend it. The spec's stream
vectors are the traces of this rule.

## Reading back

Reading inverts the rendering: longest match over a table of spellings,
tone digits attached to the form before them, anything unmatched raw. The
script table is the whole inventory; a stage's table is its spellings with
their read aliases, over the script table as fallback. `detect` ranks the
sources by coverage, the share of letters and marks a source reads with its
own spellings.

## The lexicon

Above the letter stages sits word-level knowledge where letters alone cannot
decide: a pronunciation dictionary for English, whose spelling is lexical
through and through; the pinyin syllables and the character chooser for
Mandarin; the stems that keep an etymological spelling in a language that
otherwise writes by the letters; and loans, a host reading a foreign word
through another lexicon and folding its sounds into its own. One format,
one loader, in every port. See `data/lexicon/README.md`.

## The data

- `data/languages/<code>.yaml`: what each language contrasts, per the
  standard descriptive literature. Metadata only.
- `data/mapping.yaml`: phoneme to input form, the explicit, reviewable
  layer between the metadata and everything generated: the global map,
  per-language overrides, reviewed merges, and each language's review
  state.
- `data/script.yaml`: how a form draws its glyph.
- `data/stages/`, `data/lexicon/`: the spellings above the script.

`scripts/build.sh` runs the whole chain: the master tables, the playground,
the fonts page, the lexicon, the spec, the input-method tables, this site,
and the tests.

## The fonts

Three families, Diafon Serif, Sans and Mono, each derived from the Noto
face of the same metrics, carry every mark and the attached anchor. The
serif is the reference face of the documentation. See `fonts/README.md`
for the build chain and how a glyph is overridden by an SVG.
