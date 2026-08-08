# diaphone — documentation

Reference and design docs for the diaphonemic point inventory. Start with the explanations to
understand *what the sounds are*, then the notation docs for *how to write them*.

## Understand the points (plain language)

| Doc | What it is |
|---|---|
| [points-consonants.md](points-consonants.md) | All 49 consonant points — an example word and a plain description for each, grouped by manner. |
| [points-vowels.md](points-vowels.md) | All 21 vowel points — same treatment, grouped by height. |
| [viz/consonants.html](viz/consonants.html) | Interactive consonant grid (place × manner), tap a tile for its explanation. |
| [viz/vowels.html](viz/vowels.html) | Interactive vowel chart (the mouth-shaped quadrilateral). |
| [viz/all-points.html](viz/all-points.html) | Both together on one page, with the structure explainer. |

*The HTML files are self-contained (no external assets) — open them directly, or publish as an
Artifact to share a link.*

## Decide the notation (Phase 2, gated)

| Doc | What it is |
|---|---|
| [vowel-notation.md](vowel-notation.md) | The plain-Latin label proposal for vowels, **with a full review** (§0): blockers, the derived-set diff, and the fix. Input to the point-set freeze. |

## Open threads tracked in these docs

- **Allophones entered as phonemes — resolved.** `ç` (German *ich*), `ɸ` (Japanese *fu*), and
  `ɐ` (German `-er`; Vietnamese `ă` re-read as short `/a/`) were all removed. The
  suspicious-co-occurrence guard in `derive()` is now empty and a test keeps it so.
- **`æ` fusion — decided.** No language contrasts `/æ/` with a same-length front/central `/a/`
  (Danish resolves to `/æ/`~back `/ɑ/`), so `æ`→`a` is a merge; deferred to the Phase-2
  low-vowel carving.
- **The B1 notation fix** — quality letters collide with consonant letters; see vowel-notation.md §11.
