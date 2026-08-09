# diaphone — documentation

- **Try it** (interactive): [viz/try.html](viz/try.html) — pick a language, see its filtered label
  inventory, and type notation to decode it back to the language's spelling live (runs `decode.py`'s
  logic in-browser).
- **What the points are** and **how to write them**: [viz/notation.html](viz/notation.html) —
  a single self-contained page with the operator legend, consonant grid, vowel chart, and examples.
- **Authoritative sources**: point set → `out/points.json` (70 fine-grained) →
  `out/general_inventory.json` (**58 general**); notation → `data/labels.yaml` → `out/labels.json`.
  `CLAUDE.md` ("Notation") is the prose summary.

## The notation in one paragraph
Flat scheme, base + operators, no diacritics/case/modifier-tier. Operators: `c`=affricate (`tc`=t͡s)
· `q`=hush (`tq`=t͡ʃ, `sq`=ʃ) · `x`=dental/velar (`tx`=θ) · `j`=palatal (`tj`=tʲ) · `w`=long (`tw`=tː,
`rw`=trill). Off-grid rarities are fixed combos (gutturals `ʔ`=`hj` `ħ`=`hq` `ʕ`=`hx`; emphatics on
`qx`, `tˤ`=`tqx`). Vowels: cardinals `a e i o u` + `x`/`c`/`q` + rounding as a vowel pair (`iu`=y).
All 518 phonemes round-trip to distinct per-language labels, 0 collisions.

## Resolved threads
- **Allophones removed** (not points): `ç` (German), `ɸ` (Japanese), `ɐ` (German), and Mandarin
  `j/q/x` `[tɕ tɕʰ ɕ]` — complementary with the retroflex series, so allophonic.
- **No recovery signs.** Nothing in the 16 languages contrasts dental~alveolar, retroflex~postalveolar
  (Mandarin's are complementary), or uvular~velar — those merges carry no diacritic.
- **`æ`, `tʃ~tɕ`, `ʃ~ɕ` merged** — no significant contrast.
