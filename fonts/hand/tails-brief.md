# Brief: tails for Diafon Serif

## The task

Design a set of glyphs for a serif font: Latin letters, each with a tail
hanging below it, in two mirror forms. The attached scan shows the
designer's hand drawings of these tails, sketched over the base letters. Use
them as the reference; the design itself is open.

## The characters

Diafon is a phonetic spelling system written in Latin letters plus a few
marks. One mark, the **anchor**, is a tail below a consonant, drawn as part
of the letter (not a separate accent). It comes in two forms:

| Form | Unicode | Needed on |
|---|---|---|
| anchor | letter + U+0326 (combining comma below) | b c d k m n s t x z, and B C D K M N S T X Z |
| reverse | letter + U+0316 (combining grave accent below) | c d n s t x z, and C D N S T X Z |

That is 34 glyphs. Each is one precomposed shape, so the tail may be fully
merged into the letter, and the letter itself may change where the tail
joins it.

## The base font

**Noto Serif Regular**, freely available under the SIL Open Font License.
The letters are Noto Serif's, unchanged except where a tail joins them.
Metrics: 1000 units per em, x-height 536, cap height 714, ascender 760,
descender −240. A tail may go somewhat below the descender; the font's
lowest line is −293, and the current tails reach −330.

## What to deliver

One SVG per glyph, in font units:

- **Coordinates:** 1 SVG unit = 1 font unit. The letter's origin is
  x = 0, y = 0 at the baseline, and y points **down**, so the tail has
  positive y values and the x-height is at y = −536.
- **The whole glyph:** the letter with its tail, as filled paths only, with no
  strokes or text. Overlapping shapes are fine.
- **Advance width:** the advance width of Noto Serif's base letter, unless
  the design needs a different one; if so, say which.
- **File names:** the letter and the form, for example `t-anchor.svg`,
  `T-reverse.svg`.
