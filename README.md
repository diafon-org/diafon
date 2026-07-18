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

See `CLAUDE.md` for architecture, conventions, and roadmap.

## Status
v0.1 — 72 points (51 consonant · 21 vowel), 7 modifiers, 0 merged contrasts.
Phase 2 (label + modifier characters) is intentionally not started yet.
