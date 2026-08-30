# diaphone

A minimal **diaphonemic point inventory** across 12 languages
(English, German, Spanish, French, Italian, Latin, Modern Greek, Russian,
Modern Standard Arabic, Hungarian, Mandarin, Japanese).

It finds the smallest set of cross-linguistic phonemic *points* such that **no
language's minimal pair is ever merged**, then proves the mapping is injective in
every language. Modifiers (length, nasal, palatalization, pharyngealization,
aspiration, rhoticity, nonsyllabicity — the glides) ride on top of
points instead of multiplying them.

## Quickstart
```bash
pip install -e ".[dev]"
diaphone          # derive, write out/, print summary
pytest            # verify the no-merged-contrast invariant
```

Output lands in `out/`: `points.json`, `general_inventory.json`, `graph.json`, `mappings.json`, `report.md`.

## Model in one paragraph
A *point* is a base segment — `(place, manner, voice)` for consonants,
`(height, backness, round)` for vowels. Phonemes from different languages collapse to
one point iff their base tuples match; two phonemes in the same language may share a
point only if a modifier distinguishes them. The minimal set is the distinct base
tuples; the engine validates that no within-language contrast is lost.

See `CLAUDE.md` for architecture and `docs/uni-view.md` for the uni-view spec.

## Notation & rendering
Every point gets a plain-ASCII label (`data/labels.yaml`): consonant bases + the six operators
`c j q x w y`, vowel bases `a e i o u` + operators `c j q x` on the triangular vowel model
(`docs/index.html` — the whole-system page). One engine renders a notation string to any **target** —
universal (`uni` — our view — or `ipa`) or a language's spelling — and the same phonemes spell
themselves differently per target:

```
diaphone render uni    "sjok sewp njawr"   # -> șok sép n̦ár
diaphone render ipa    "sjok sewp njawr"   # -> ʃok seːp ɲaːr   (a curated approximation)
diaphone render hu     "sjok sewp njawr"   # -> sok szép nyár
diaphone render zh     "sjan1 kxaxn3 kau1" # -> shān hěn gāo   (tones by trailing digit)
```

Tone digits render per target: Pinyin diacritics (zh), superscripts (ipa — an IPA-only device),
plain digits (uni) — or, opt-in, **tone signs** on the vowel with `--tones` (`șān ḳǎu`), placed
by a Pinyin-matching priority rule.


Five invariants keep it honest, all enforced by `diaphone --strict` and the tests:
**injectivity** (no language collapses two phonemes to one `(point, modifiers)`),
**notation decodability** (no label re-reads as a sequence of that language's labels),
**universal-stream decodability** (the same, over the global label set every universal
target tokenises against), **one label, one analysis** (no label string is reachable from two
different `(point, modifiers)` pairs), and **the point/modifier boundary** (no point duplicates
what a modifier already spells) — with zero accepted exceptions.

## Status
**49 general points** (32 consonant · 17 vowel) folded from 62 fine-grained via 13 reviewed
merges · 875 phonemes (27 languages) · 8 modifiers · **0 merged contrasts, 0 notation collisions**.
27 languages: 12 core targets + 5 **witnesses** (Turkish, Estonian, Vietnamese, Korean, Tamil) that
prove near-merge pairs stay distinct where a significant language contrasts them, + 10 coverage
languages whose inventories are subsets of the existing points.
The uni Latin-diacritics view is fully specified (`docs/uni-view.md`) and set in the
**Diaphone font** (a Noto Serif derivative, SIL OFL — `scripts/build_font.py`); the macOS
input method streams conversion as you type (`mac/`).
