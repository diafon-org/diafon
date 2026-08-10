# diaphone — documentation

- **The guide** (everything): [viz/guide.html](viz/guide.html) — the full notation (operators,
  consonant grid, vowel chart, features) followed by a live decoder for English, Hungarian, and
  Mandarin. Pick a language, type notation, watch it become that language's spelling. Self-contained.
  (`viz/notation.html` and `viz/try.html` are the older split versions.)
- **The vowel triangle** (adopted redesign): [viz/vowel-triangle.html](viz/vowel-triangle.html) — the
  vowels as a triangle: cardinals on the edges, one operator off for the rest (`c`=toggle-rounding,
  `j`=lax, `q`=c+j, `x`=centralise→schwa), schwa at the centre, nasal as an overlay. **17 oral + 4
  nasal**, only `ɒ→ɔ` merged (œ/ʏ kept — French *jeûne/jeune*, German ü/ö). NOTE: this is the agreed
  next-gen vowel model; `labels.yaml`/orth/guide still run the old 18-vowel scheme until the code sync.
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
