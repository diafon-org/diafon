# diaphone — working notes for Claude Code

## What this is
Derives the **minimal set of cross-linguistic phonemic points** for 12 languages
(EN DE ES FR IT LA EL RU AR HU ZH JA) such that **no language's minimal pair is ever
merged** — and proves it. The eventual goal is a universal notation: one label char per
point, one systematic char per modifier.

## The core idea (don't break this)
- A **point** is a *base segment*: `(place, manner, voice)` for a consonant,
  `(height, backness, round)` for a vowel. Nothing else defines a point.
- **Modifiers** — `long, nasal, palatalized, pharyngealized, labialized, aspirated,
  rhotic` — are stripped off to get the base. They ride on top and **never create points**.
- Two phonemes in different languages **share a point** iff their base tuples are equal.
  Two phonemes in the **same** language may share a point only if a modifier separates
  them. This guarantees `phoneme → (point, modifiers)` is **injective per language**.
- **Minimal set = the distinct base tuples.** `derive()` builds it and validates the
  injectivity invariant; any residual collision means the feature grid is too coarse
  (fix by adding a feature or a modifier, as we did for `ə/ɝ` → rhotic, `j/ɥ` → labialized).

## Invariant (must always hold)
`merged contrasts == 0`. Enforced by `tests/test_invariants.py` and `diaphone --strict`.
If a data edit breaks it, either the data is wrong or a new modifier/feature is needed —
never "fix" it by deleting a phoneme.

**Second invariant — notation decodability** (`src/diaphone/notation.py`): no phoneme's full label
(point + modifier chars) may also read as a *sequence* of that language's phoneme labels. This is the
linear-notation cousin of injectivity, and it catches what `labeler.py` cannot: a one-letter modifier
is ambiguous exactly when its letter is *also* a base segment that can follow (`ku`=/kʷ/ vs /k/+/u/;
`ph`=/pʰ/ vs /p/+/h/). The safe modifiers `w`/`j` have no phoneme twin (glides removed). Reviewed,
accepted ambiguities live in `notation._ACCEPTED` (aspiration `Ch`, boundary-only; rhotic `yr`,
vacuous — English has no trill); anything else fails `diaphone --strict` and the test. Latin `ku` was
the one real collision → resolved by making labialised a fixed combo `cw` (`kcw`=kʷ).

## Layout
```
data/features.yaml          feature scales + modifier list (drives distance metric)
data/languages/<code>.yaml  one file per language — THIS is where you edit inventories
src/diaphone/model.py       base tuples, modifier→diacritic map, strip_mods
src/diaphone/loader.py      load + expand modifier series (long/nasal/secondary)
src/diaphone/derive.py      minimal points, injectivity, near-merge + suspicious + rhotic finders
src/diaphone/merges.py      Phase-2 merge ledger: fold fine-grained points → general inventory
src/diaphone/notation.py    notation-decodability check: phoneme label vs same-language sequence
src/diaphone/decode.py      notation → a language's spelling (greedy tokenise + per-lang rules)
src/diaphone/report.py      JSON + Markdown output
src/diaphone/cli.py         `diaphone` entry point
out/                        generated (gitignored): points.json, general_inventory.json,
                            mappings.json, report.md
```

## Run / test
```
pip install -e ".[dev]"
diaphone                 # regenerates out/ and prints a summary
diaphone --strict        # non-zero exit if any contrast is merged (use in CI)
diaphone decode zh "sjan1 kxyn3 kau1"   # -> shān hěn gāo   (trailing digit 1-4 = Pinyin tone)
diaphone decode hu "alma kert" --lazy   # -> alma kert      (--lazy: per-language shortcuts)
pytest                   # runs the invariant guardrails
```

## Decoding (`decode.py`)
Notation → a language's spelling. Canonical labels live in `data/orth/<lang>.yaml`; two extras layer on:
- **Mandarin tones** — a trailing digit `1-4` on a zh syllable places the Pinyin tone mark (`5`/none =
  neutral); placement is the standard a > e > ou > last-vowel rule.
- **Lazy mode** (`decode(..., lazy=True)` / `--lazy`) — opt-in, language-specific shortcuts in
  `decode.LAZY_ALIASES`: HU bare `a`=/ɒ/, `e`=/ɛ/ (no cardinal /a/,/e/ in Hungarian); ZH `e`=/ɤ/,
  `h`=/x/, `r`=/ʐ/ (Pinyin-style — those letters are otherwise free). Canonical files stay pure.

## Data conventions
- `data/languages/*.yaml` short keys: `pl mn vc` (consonant place/manner/voice),
  `hi bk rd` (vowel height/backness/round), `orth` native spelling, `st` status
  (`phonemic|marginal|loan`), `note` free text.
- Modifier series expand automatically: `long_series: [...]`, `nasal_series: [...]`,
  `secondary_series: [{type, applies_to:[...]}]`, or inline `mod: [rhotic]` on a phoneme.
- **Allophones are NOT phonemes** — record them in `note`, never as their own entry.
  Points come from contrastive units only.
- Mandarin: lenis series entered as voiceless-unaspirated; the fortis series is generated
  via `secondary_series: aspirated`. Mandarin therefore uses no voiced stop points.
- Korean: three-way plain/aspirated/**tense(fortis)** obstruents. The tense series reuses
  the `long` modifier (fortis ≈ length — no language contrasts them; Seoul Korean has no
  vowel length or geminates, so `long` is free). Aspiration stays its own modifier because
  Korean contrasts fortis vs aspirated (`t͈`~`tʰ`). So: fortis ≈ long, but fortis ≠ aspirated.

## Witness languages (Phase-1 decision-gate evidence)
The 12 core languages are the notation's target; **TR ET VI KO** were added purely as
*witnesses* — significant languages that phonemically contrast a near-merge pair, forcing
the point to stay distinct. Turkish locks `u`~`ɯ` (*kul*/*kıl*); Estonian + Vietnamese lock
`o`~`ɤ` (õ; ô/ơ). See the near-merge verdict table below for the full witness search.

## Current state
68 fine-grained points → **55 general** (37 C · 18 V) after 13 merges, 0 merged contrasts, 491
phoneme records, 16 languages (12 core + 4 witnesses). **Every point is a base or base + ONE
operator** — no 2-operator points, no bi-vowels. Removed (not points): `ç` (German ich-laut → `x`),
`ɸ` (Japanese *fu* → `h`), `ɐ` (German `-er`), **Mandarin j/q/x `[tɕ tɕʰ ɕ]`** (allophones of the
retroflex series), the **glides `/j/ /w/ /ɥ/`**, and **`ʌ`** (folded into schwa: English STRUT =
stressed `/ə/`, Korean ㅓ ≈ schwa). Vietnamese `ă` re-read as short `/a/`.

## Notation (Phase 2 — locked, round-tripped)
`data/labels.yaml` gives one label per general point; `labeler.py` validates it, `out/labels.json`
regenerates it. **Every point is a base or base + ONE operator** — no tier, no case, no diacritics.
- **Bases** `p b t d k g m n f v s z l h`, the trill `r` (the common rhotic; tap `ɾ`=`rj`), and 6
  vowel letters `a e i o u y` (`y`=schwa). Glides `/j/ /w/ /ɥ/` removed (non-syllabic `/i/ /u/ /y/`).
- **Consonant operators** (never a bare label): `c`=affricate (`tc`=t͡s) · `q`=hush **affricate**
  (`tq`=t͡ʃ) · `x`=dental/velar (`tx`=θ, `kx`=x) · `j`=palatal (`sj`=ʃ, `tj`=c/tʲ, `nj`=ɲ) · `w`=long
  (`tw`=tː, geminate/long trill `rw`). So `q`=`c+j` (hush = affricate+palatal). Off-grid combos:
  gutturals `ʔ`=`hj` `ħ`=`hq` `ʕ`=`hx`; emphatics `qx` (`tˤ`=`tqx`).
- **Vowels**: 6 bases `a e i o u y`(=ə, which also carries English STRUT ʌ / Korean ㅓ). Operators
  mirror the consonants — `c` and `j` primitive, `q`=`c+j`: `c`=round `j`=lower `q`=round+lower,
  `x`=back. Every vowel is base+1op — ü/ʏ = `ic`/`iq`, ö/œ = `ec`/`eq`, ɪ = `ij`. No pairs.
- **Modifiers ride on top, one letter each**: long `w`, aspirated `h` (nasal `h` on vowels), rhotic
  `r`; palatalised `j` (`pj tj`…) but **`jj` on s/z** (`sʲ`=`sjj`, since `sj`/`zj`=ʃ/ʒ); pharyngealised
  `qx` and labialised `cw` (`kcw`=kʷ) are the two fixed combos — labialised is NOT bare `u`, which
  would collide with the vowel /u/ (Latin quī/cui); see the notation-decodability invariant above.
- Validated: all **491** phonemes get a distinct label per language, **0 collisions**, and (now that
  the vowel pairs are gone) **no label decomposes** — every one is base or base + operators.

## Allophone guard (suspicious co-occurrences)
The near-merge finder only flags pairs that *don't* co-occur, so it is blind to allophones
entered as phonemes (which co-occur with their parent). `derive()` also returns
**suspicious co-occurrences**: rare points (≤2 languages) sitting one place/height step from a
same-language neighbour — the shape of an allophone. Reviewed genuine contrasts live in
`_CONFIRMED_CONTRAST` (derive.py) and are filtered out. This caught `ç`~`x`, `ɸ`~`h`, `a`~`ɐ`
(all now resolved); the list is **empty** and `tests/test_invariants.py` asserts it stays so.

## Roadmap
- **Phase 1 (done):** the database + derivation + invariant. ← we are here.
- **Decision gate (in progress):** every near-merge was adversarially witness-searched.
  **Principle (Sz):** a pair stays a distinct *point* only if a *significant* language
  contrasts it; pairs held apart only by a rare/exotic language get **merged in the
  general inventory and recovered by a diacritic later**. Verdicts:
  - **KEEP (significant witness) — added the language:** `u`~`ɯ` (Turkish), `o`~`ɤ`
    (Estonian, Vietnamese). **KEEP (advisory, by-construction):** `ɑ`~`ɒ` (RP; round is a
    defining feature).
  - **MERGE later via a place diacritic (exotic-only witness):** `t̪`~`t` / `d̪`~`d`
    (Venda), `ʁ`~`ɣ` (Tsakhur/Kabardian), `ʃ`~`ʂ` & `ʒ`~`ʐ` (Toda), `tʃ`~`tʂ` (Mapudungun) —
    the retroflex trio recovers via **underdot** (`ṣ ẓ`). Deferred to Phase 2; the fine-grained
    set still lists both. (`f`~`ɸ`, Ewe: currently inactive — `ɸ` was removed as a JA allophone;
    the merge applies only if Ewe is later added and reintroduces `ɸ`.)
  - **MERGE — no witness at all:** `æ`~`a` — adversarial search (incl. Danish, whose crowded
    low-front space resolves to `æ`~back `ɑ`, already kept) found nothing contrasting `/æ/`
    with a same-length front/central `/a/`. No recovery diacritic needed; collapses in the
    Phase-2 low-vowel carving. (`ç`~`ɕ` mooted — `ç` was removed as a German allophone.)
  - **MERGE — no significant witness:** `ɯ`~`ɨ` (close back vs central unrounded) — every major
    language has one or the other, never both, and the two symbols are used interchangeably;
    recover by a back-vs-central diacritic in Phase 2.
  - **Rhotics (cross-manner — invisible to the same-manner finder).** KEEP `r` (trill) ~ `ɾ`
    (tap) — Spanish *perro/pero*, significant. KEEP the retroflex central approximant `ɻ`/`ʐ`
    (Mandarin ⟨r⟩) — Dravidian Tamil/Malayalam contrast `ɻ`~`r`, significant. **MERGE** `ɹ`
    (English's only rhotic) → `ɻ`: no language contrasts the two central approximants
    (Eng-`ɹ` ≈ Mand-`ɻ`, Q4), no recovery diacritic. Note `ʁ` is NOT a rhotic merge — Arabic
    contrasts `ʁ` (ghayn) ~ `r` (rā). (The retroflex *sibilants* `ʂ ʐ tʂ` still merge via
    underdot — only Toda/Mapudungun, exotic, contrast them; the retroflex *approximant* is
    different, defended by Dravidian.)
  - **RESOLVED as allophones (removed):** `ç`, `ɸ`, `ɐ` — see the allophone guard above.
  - **No open near-merges remain** — same-manner *and* the cross-manner rhotic family are both
    swept. Every pair is decided: KEEP (witnessed), MERGE-via-diacritic (exotic), MERGE-outright
    (no witness), or removed (allophone). Applying the merges is Phase 2 → general inventory ~61.
- **Phase 2 (done — merge ledger + notation):** `merges.py` folds the fine-grained **70** into the
  general inventory **58** (39 C · 19 V) via 12 merges; `apply_merges()` asserts safety per
  `(target, recovery-mark)` per language. **No recovery diacritics** — every consonant-place merge
  is `recover=None`: within the 16 languages nothing contrasts dental~alveolar, retroflex~postalveolar
  (Mandarin's are complementary allophones), or uvular~velar, so the fold is lossless-in-practice and
  needs no sign. `labels.yaml` assigns the flat notation (see "Notation" above); all 518 phonemes
  round-trip to distinct per-language labels. **Superseded verdicts:** the old "retroflex trio via
  underdot" and "tʃ/tɕ kept" plans below are obsolete — the retroflex/alveolo-palatal sibilants now
  fold into the postalveolar with no mark, and `tʃ~tɕ` merged.

## Open decisions
- LICENSE not chosen yet (Sz' decides — mirror weCan conventions if relevant).
- Greek is Modern; swap to Ancient if we want to pair it with Latin.
