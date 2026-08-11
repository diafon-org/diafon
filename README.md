# diaphone

A minimal **diaphonemic point inventory** across 12 languages
(English, German, Spanish, French, Italian, Latin, Modern Greek, Russian,
Modern Standard Arabic, Hungarian, Mandarin, Japanese).

It finds the smallest set of cross-linguistic phonemic *points* such that **no
language's minimal pair is ever merged**, then proves the mapping is injective in
every language. Modifiers (length, nasal, palatalization, pharyngealization,
labialization, aspiration, rhoticity) ride on top of points instead of multiplying them.

## Quickstart
```bash
pip install -e ".[dev]"
diaphone          # derive, write out/, print summary
pytest            # verify the no-merged-contrast invariant
```

Output lands in `out/`: `points.json`, `mappings.json`, `report.md`.

## Model in one paragraph
A *point* is a base segment — `(place, manner, voice)` for consonants,
`(height, backness, round)` for vowels. Phonemes from different languages collapse to
one point iff their base tuples match; two phonemes in the same language may share a
point only if a modifier distinguishes them. The minimal set is the distinct base
tuples; the engine validates that no within-language contrast is lost.

See `CLAUDE.md` for architecture and `docs/native-view.md` for the native-view spec.

## Notation & rendering
Every point gets a plain-ASCII label (`data/labels.yaml`): consonant bases + operators
`c q x j w`, vowel bases `a e i o u` + operators `c j q x` on the triangular vowel model
(`docs/viz/notation.html` — the whole-system visualisation). One engine renders a notation string to any **target** —
universal (`ipa`, `native`) or a language's spelling — and the same phonemes spell themselves
differently per target:

```
diaphone render native "sjok sewp njawr"   # -> șok sép ņár
diaphone render ipa    "sjok sewp njawr"   # -> ʃok seːp ɲaːr
diaphone render hu     "sjok sewp njawr"   # -> sok szép nyár
diaphone render zh     "sjan1 kxaxn3 kau1" # -> shān hěn gāo   (tones by trailing digit)
```

Two invariants keep it honest, both enforced by `diaphone --strict` and the tests:
**injectivity** (no language collapses two phonemes to one `(point, modifiers)`) and
**notation decodability** (no label re-reads as a sequence of that language's labels).

## Status
**53 general points** (36 consonant · 17 vowel) folded from 68 fine-grained via 15 reviewed
merges · 490 phonemes · 7 modifiers · **0 merged contrasts, 0 notation collisions**.
16 languages: 12 core targets + 4 **witnesses** (Turkish, Estonian, Vietnamese, Korean) that
prove near-merge pairs stay distinct where a significant language contrasts them.
The native Latin-diacritics view is fully specified (`docs/native-view.md`); a bespoke font
and a macOS input method are the next build steps.
