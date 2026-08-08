# Vowel notation — plain-Latin labels (proposal + review)

**Status:** proposal. Not frozen. Phase 2 (label assignment) stays gated until the point set is frozen — this document is input to that freeze, not a record of it.

**Supersedes:** nothing. **Blocks:** Phase 2.

---

## 0. Review (2026-07 · against the 16-language point set)

A full review of the proposal below, checked against `out/points.json`, `data/languages/*.yaml`, and the derivation code. Severities: **BLOCKER** = must resolve before freeze; **MAJOR** = wrong or stale claim that changes a decision; **MINOR** = correctness nit; **ENDORSE** = agreed, no change.

| # | Sev | Finding | Verdict / action |
|---|---|---|---|
| **B1** | BLOCKER | **The scheme is not self-segmenting.** The quality letters `h x w v q` (§2.1) are *also* the consonant bases `h x w v q`. So `ix` (ɨ) is indistinguishable from `/i/`+`/x/` — Russian *их* `/ix/`. Same for `uv` (ɯ) vs `u`+`v`, `aq` (ɑ) vs `a`+`q` (Arabic), `iw` (y) vs `i`+`w`, `ov` (ɤ) vs `o`+`v`. §2's "self-segmenting without delimiters" and §5.5's "uniquely decodable" do **not** hold. Rule 5.5 only guards the *first* letter, not where a vowel's quality string ends and a following consonant begins. | **Recase quality operators to the uppercase (rides-on-base) tier**, using the free uppercase letters `H X W V Q` (modifiers already use `G C N B K R L`). Base becomes the 5 lowercase cardinals `a e i o u` *only*; everything riding on them is uppercase → fully self-segmenting against lowercase consonants. `y`=`iW`, ɨ=`iX`, ɪ=`iH`, ɯ=`uV`, ɑ=`aQ`. Cost: longer labels; the "uppercase never creates a point" slogan softens to "lowercase = 5 cardinal anchors; uppercase = everything that rides, point-creating (`H X W V Q`) or not (`G C N B K R L`)." See §11. |
| **B2** | BLOCKER | **The register can't hold the low/central region without merges.** The central column stops at close-mid and the open row is binary front/back (§3), so there is no slot for a near-open or open-central vowel. But the derived set keeps `æ` and `ɐ`, and Vietnamese contrasts three central-ish vowels `ə / ɐ / a` in one inventory. Pruning `ɐ` (§9) with no slot forces a Vietnamese merge. | Resolve **with M1/M2** — the honest fix is mostly on the *data* side (see M2), but the register must still name whatever survives. Do not freeze until the low-vowel carving is settled end-to-end (data + register + a witness search for `æ`). |
| **M1** | MAJOR | **§7's diff is wrong.** It is not "one cell apart." Against the current 22-point derived set the diff is a **2-for-2 swap**: derive keeps `{æ, ɐ}`, the doc adds `{ʉ, ɵ}`. (The old "21 vs 22" compared *counts*, not *sets* — the set difference was already 5 cells at 12 languages.) By the doc's own rule ("more than one cell means one of the two is wrong"), this is a live signal — localized in M2. | Replace the §7 claim with the real diff. Treat each of the four cells on its own evidence (below). |
| **M2** | MAJOR | **`ɐ` is a derived-data artifact, not a real point.** German `ɐ` is entered as `orth: -er` — that is r-vocalization, an **allophone** of coda `/r/`, which the project's own rule forbids as a point. Its only other witness, Vietnamese `ă`, is better analysed as *short* `/a/` (a length pair with `/aː/`), not a distinct `ɐ` quality. Strip both and `ɐ` has **no valid phonemic witness**. | ✅ **DONE.** German `ɐ` (`-er` allophone) dropped; Vietnamese `ă` re-read as short `/a/` (`long_series: [a]`). `ɐ` removed → 22 → 21 vowels; B2's Vietnamese pressure dissolved; the suspicious-co-occurrence guard is now empty. |
| **M3** | MAJOR | **`æ` is a real point, and its prune is unjustified.** Unlike `ɐ`, `æ` has two solid phonemic witnesses — English TRAP and Estonian *ä* — both contrasting `/æ/` from `/e/` and from the open vowel. §9 deletes it ("near-open is backness, not height") without a witness search. | ✅ **SEARCHED → MERGE.** No significant language contrasts `/æ/` with a same-length front/central `/a/` (Danish, the one candidate, resolves to `/æ/`~back `/ɑ/` — already kept). So `æ`→`a` is a decided merge, deferred to the Phase-2 low-vowel carving (needs no recovery diacritic). `æ` still appears in the fine-grained set for now. |
| **M4** | MAJOR | **Witness/count facts are stale.** The doc says 12 languages, 21 derived points, and *five* unwitnessed cells (`ixw uv exw ohv aq`). Current state is **16 languages, 22 derived points, and only two** unwitnessed cells: `ʉ`(ixw) and `ɵ`(exw). `ɯ`(uv), `ʌ`(ohv) and `ɑ`(aq) are already witnessed by TR/KO, EN/KO and EN/FR/ET respectively. | Update §3 † marks, §7, and §8. Only Swedish is still owed (for `ʉ`,`ɵ`). |
| **m1** | MINOR | §7 says "Swedish, Turkish and Finnish settle all five," but `ohv`(ʌ) needs **Korean** (or English) — Finnish supplies only `aq`(ɑ). §8 correctly lists Korean for `ohv`; §7 contradicts it. | Fix §7 to match §8. |
| **m2** | MINOR | The consonant side has the **same latent ambiguity**: `sh`=ʃ vs `s`+`h`, `ng`=ŋ vs `n`+`g`, `sy`=ɕ vs `s`+`j`. Out of this doc's vowel scope, but the "self-segmenting" claim spans the whole label stream, so B1's fix alone does not make full transcriptions decodable. | Note it as a Phase-2 consonant-scheme item; the vowel fix (B1) is necessary but not sufficient for stream decodability. |
| **m3** | MINOR | Rule 5.3 (ATR vowels spelled higher+`G`) is only enforceable if the model knows which languages are ATR-harmony systems. That is per-language metadata not currently in the data. | Add an `atr_harmony: true` flag to the relevant language files before 5.3 can be tested. |
| **m4** | MINOR | §10's `test_label_namespaces_disjoint` (rule 5.5) will **pass while the scheme is still ambiguous** — it only checks first letters, so it gives false confidence against B1. | Add `test_concatenation_decodable` (round-trips a concatenated label stream) as the real guard. See §10 note. |
| **E1** | ENDORSE | §6 (stay at 22; record the ATR fork rather than resolve it) — agreed and well-argued, including the asymmetry (no ATR reanalysis one row down, because e/ɛ and o/ɔ contrast with no harmony in the system). §4 (G-as-modifier, not a height step) — correct. §10 test set — endorse, with m4's addition. | No change. |

**Net for the freeze gate:** the *idea* is sound and the uppercase/lowercase tiering is the right instinct — but two blockers stand. B1 is a clean recast (§11). B2/M1–M3 converge on a single satisfying result: the top-down and bottom-up methods disagree in exactly one *real* place (`æ`), and that disagreement is a **fusion decision owed a witness search** — while the other apparent disagreement (`ɐ`) is a **data bug the diff correctly surfaced**. Fixed the data and ran the `æ` search (both ✅ done — see M2/M3); recast the quality letters (B1), then freeze.

---

*The proposal follows, preserved, with inline anchors (`⚠[B1]`…) pointing at the findings above. Stale figures are struck through and corrected in place.*

## 1. Scope

Covers the vowel region of the point set and a proposed plain-Latin label scheme for it.

Out of scope: tone (suprasegmental), diphthongs (sequences of points, not points), stress, and allophonic detail that no language contrasts.

## 2. The alphabet partition

The label space is split so that strings are self-segmenting without delimiters:

> ⚠ **[B1]** This is the claim that fails — see §0. The split cleanly separates *base* from the 7 *modifiers*, but the *quality* letters `h x w v q` are borrowed from the consonant alphabet, so a vowel's quality string is ambiguous against a following consonant (`ix` = ɨ vs `/i/`+`/x/`). Fix in §11.

| Case | Role | Letters |
|---|---|---|
| lowercase | base — encodes quality only, creates points | `a e i o u` + `h x w v q` |
| uppercase | modifier — rides on any base, never creates points | `G C N B K R L` |

This is what accents were reaching for — a visible distinction between "part of the base" and "modifies the base" — without combining marks, NFD/NFC normalisation, font-stack risk, or leaving ASCII. It also stacks freely, which diacritics do not: a long nasal RTR vowel is three marks on one glyph in Akan or Igbo, but `iGNL` in this scheme.

Cost: case-insensitive matching is no longer safe on labels. Accepted.

### 2.1 Quality letters

| Letter | Effect | Notes |
|---|---|---|
| `h` | lower one step | |
| `x` | centralise | |
| `w` | round | on front and central bases |
| `v` | unround | on back bases only |
| `q` | retract | open row only; a plain binary there |

Front is the default for `i e a`; back is the default for `o u`. Mark exceptions, never defaults.

> ⚠ **[B1]** Under the §11 fix these become uppercase operators `H X W V Q` (order and semantics unchanged), leaving `a e i o u` as the only lowercase vowel letters.

## 3. Base register — 22 points

Five heights. Backness resolution narrows with aperture, so the central column reaches only as far as close-mid and the open row is binary in backness.

> ⚠ **[B2]** "central column reaches only to close-mid" + "open row binary" = no slot for `ɐ` (near-open central) or an open-central `a`. This is what forces the Vietnamese merge. See §0 B2/M2.

| Code | IPA | Height | Back | Rnd | Witness |
|---|---|---|---|---|---|
| `i` | i | close | front | – | near-universal |
| `iw` | y | close | front | ● | French *lune*, Turkish *gül* |
| `ix` | ɨ | close | central | – | Russian *мы*, Guaraní |
| `ixw` | ʉ | close | central | ● | Swedish *hus* † |
| `uv` | ɯ | close | back | – | Turkish *ısı*, Korean *으* ~~†~~ **witnessed (TR, JA, KO)** |
| `u` | u | close | back | ● | near-universal |
| `ih` | ɪ | near-close | front | – | English *kit*, German *Mitte* ‡ |
| `ihw` | ʏ | near-close | front | ● | German *Müller* ‡ |
| `uh` | ʊ | near-close | back | ● | English *foot*, German *Mutter* ‡ |
| `e` | e | close-mid | front | – | Spanish, Italian, Japanese |
| `ew` | ø | close-mid | front | ● | French *peu*, German *schön* |
| `ex` | ə | close-mid | central | – | English *comma*, Hindi |
| `exw` | ɵ | close-mid | central | ● | Swedish *full* † |
| `ov` | ɤ | close-mid | back | – | Mandarin *歌*, Estonian *õ* |
| `o` | o | close-mid | back | ● | near-universal |
| `eh` | ɛ | open-mid | front | – | Italian *è*, French *mettre* |
| `ehw` | œ | open-mid | front | ● | French *sœur* |
| `ohv` | ʌ | open-mid | back | – | Korean *어* ~~†~~ **witnessed (EN, KO)** |
| `oh` | ɔ | open-mid | back | ● | Italian *ò*, French *sort* |
| `a` | a | open | front | – | Spanish, Hungarian *á* |
| `aq` | ɑ | open | back | – | Finnish, English *palm* ~~†~~ **witnessed (EN, FR, ET)** |
| `aqw` | ɒ | open | back | ● | Hungarian *hat*, RP *lot* |

† no witness among the 16 current languages — now **only** `ixw`(ʉ) and `exw`(ɵ), both settled by Swedish. See §7/§8. *(was: five points, twelve languages — stale, [M4].)*
‡ dissolves if the fork in §6 is taken.

> ⚠ **[M2/M3]** The register also lacks `æ` and `ɐ`, which the bottom-up derivation keeps. `ɐ` should indeed go — but for a *data* reason (German `ɐ` = `-er` r-vocalization, allophonic; Vietnamese `ă` = short `/a/`), not because near-open is not a height. `æ` should **stay** pending a witness search (English TRAP + Estonian *ä* are phonemic). Add a row for `æ` (e.g. `aH`, near-open front) until that search returns empty.

## 4. Modifiers — 7

Written in this order, always, so each phoneme has exactly one spelling.

| Char | Feature | Witness | Example |
|---|---|---|---|
| `G` | retracted tongue root (−ATR) | Akan, Igbo, Dinka | `iG` |
| `C` | compressed rounding (default is protruded) | Swedish ʉ against y | `ixwC` |
| `N` | nasalised | French, Portuguese, Hindi | `ohN` |
| `B` | breathy voice | Gujarati, Mazatec | `aB` |
| `K` | creaky voice | Vietnamese, Mazatec | `aK` |
| `R` | rhotic | English ɝ, Mandarin er | `exR` |
| `L` | long; `LL` overlong | Estonian three-way | `exL` |

`G` is a modifier rather than a height step because ATR is orthogonal to height and spreads harmonically — modelling it as height would need ladder steps no language contrasts, and would produce spurious merges when a −ATR vowel lands on the same tuple as a genuinely lower vowel elsewhere. **[E1: endorsed.]**

## 5. Spelling rules

1. Quality letters appear in the order `h → x/q → w/v`. So `ihxw`, never `iwxh`.
2. Modifiers appear in the order `G → C → N → B/K → R → L`.
3. **A vowel in an ATR harmony system is always spelled as the higher member plus `G`.** Akan ɪ is `iG`, never `ih`. Without this rule, adding ATR creates a *split* — one sound with two legal codes — which the existing no-merge invariant cannot see. *(⚠ [m3]: needs an `atr_harmony` flag per language to be enforceable.)*
4. Length by repetition of the modifier, not the base: `i` · `iL` · `iLL`.
5. No consonant label may begin with a vowel letter, and no vowel label may begin with a consonant letter. This keeps the two namespaces disjoint and the concatenation uniquely decodable. Currently holds — the consonant digraphs (`ny`, `sh`, `rr`, `rh`, `gh`) all start on consonants — but it is unenforced.

> ⚠ **[B1/m2]** Rule 5.5 guarantees only that a label's *first* letter reveals its namespace. It does **not** make concatenation decodable: it says nothing about where a vowel's quality run ends (`ix|...` vs `i|x...`), nor about consonant digraph ambiguity (`s|h` vs `sh`). "Uniquely decodable" is therefore not yet true. §11 fixes the vowel half; the consonant half is [m2].

## 6. Open decision: the fork at 19

The near-close row rests entirely on the Germanic tense–lax contrast. A long literature analyses that contrast as [±ATR] — the same feature Akan harmony uses. Accept that reading and the row dissolves:

| IPA | At 22 | At 19 |
|---|---|---|
| ɪ | `ih` | `iG` |
| ʏ | `ihw` | `iwG` |
| ʊ | `uh` | `uG` |

No merges result: no language contrasts a lax vowel with a −ATR one, and the four-way i/ɪ/e/ɛ that German needs still spells distinctly as `i` `iG` `e` `eh`.

Gain: three points, one unified feature. Cost: `G` means two things and the label stops being theory-neutral.

**Recommendation:** stay at 22. Record the fork in the data rather than resolving it. 19 buys little and commits a lot. **[E1: endorsed — including the asymmetry note below, which is correct.]**

Note the asymmetry — the *same* move is not available one row down. Italian, French and Portuguese contrast e/ɛ and o/ɔ with no harmony anywhere in the system, so calling that ATR would be unmotivated. Height above near-close is genuine.

## 7. Open items

> ⚠ **[M1]** Corrected diff. The two methods do **not** land one cell apart. Real difference against the 22-point derived set:
> - **derive() keeps, doc prunes:** `æ`, `ɐ` — treat separately: `ɐ` is a data bug (**[M2]**, prune agreed), `æ` is a real point (**[M3]**, owed a witness search).
> - **doc adds, derive lacks:** `ʉ`, `ɵ` — legitimate top-down cells, unwitnessed until Swedish (**[M4]**).
> The count coincidence (22 = 22) hides a 4-cell structural disagreement. The diff *is* the high-value check the doc promised — it worked, and it points at the data (`ɐ`) and at one unmade decision (`æ`).

- **~~Five~~ Two points have no witness in the current ~~twelve~~ 16:** `ixw` `exw`. ~~`uv` `ohv` `aq`~~ are now witnessed (TR/KO, EN/KO, EN/FR/ET). Swedish settles both remaining. **[M4]**
- **Danish may force a sixth height.** It is analysed with as many as five distinct front unrounded heights of its own, which the ladder does not have under either endpoint. Add it last, and read a failure as evidence about the ladder rather than about Danish.
- **Diff against the derived set.** Done — see the [M1] box above. Two methods, 22 each, differing in 4 cells; the difference localises cleanly to one data bug (`ɐ`) and one open fusion (`æ`).
- **The `q` irregularity.** `a` is front-default while `o u` are back-default, so open-back needs an explicit `q`. Tolerable now that the open row is binary, but an alternative is a dedicated base letter for open-back. *(Note: under [B1] this becomes uppercase `Q`, but the front/back-default asymmetry is unchanged.)*
- **`ex` carries both ə and ɘ.** No language contrasts them; recorded as a deliberate collapse rather than an accident.

## 8. Roster to add

Chosen because each forces a feature the current ~~twelve~~ core set leaves untested — not for size or prestige. Add one at a time, re-running the invariants between each. **(TR, ET, VI, KO are already in — marked ✓.)**

| Language | What it forces |
|---|---|
| Turkish ✓ | Closes the rounding × backness harmony square; cleanest witness for `uv` |
| Swedish | `ixw`, `exw`, and the only real argument for `C` — **the last two unwitnessed points [M4]** |
| Korean ✓ | `ohv`, plus a second witness for `uv` |
| Vietnamese ✓ | `K`; also tone interacting with vowel quality. *(⚠ re-examine `ă` as `a`+`L` — [M2].)* |
| Estonian ✓ | Three-way length — proves `L` must repeat rather than toggle |
| Akan | The entire `G` modifier and rule 5.3 |
| Portuguese | Nasality on a wider base set than French; tests `N` stacking |
| Gujarati | `B` as a vowel feature rather than a consonant one |
| Khmer | ~30 monophthongs — the volume test for the grid |
| Danish | The height stress test; see §7 |

## 9. Pruning record

The witness rule: **a point with no attested contrast in any language is as much a bug as a merged pair.** This is the existing no-merge invariant applied from the other side. **[E1: this framing is exactly right and is the backbone of `test_every_point_has_witness`.]**

| Count | Removed | Reason |
|---|---|---|
| 42 | — | full phonetic grid: 7 heights × 3 backnesses × rounding |
| 30 | near-open, mid rows | no language contrasts a third level between close-mid and open-mid; æ/ɑ is backness, not height |
| 27 | ä, ɶ, open central rounded | an open jaw compresses the F2 range |
| 23 | ɪ̈, ʊ̈, ɯ̽, ɞ | phonetically real, phonemically never contrastive |
| 22 | ɜ | RP *nurse* is stress-conditioned against schwa; exits cleanly as `exL`, with rhotic ɝ as `exR` |
| 19 | ɪ, ʏ, ʊ | **not taken** — see §6 |

> ⚠ **[M2/M3]** The `42 → 30` row conflates two different removals. Dropping **`ɐ`** (near-open central) is correct — but because its occupants are non-phonemic (German `-er`, Vietnamese short-`/a/`), *not* because "near-open is backness." Dropping **`æ`** is not yet earned: English TRAP and Estonian *ä* are phonemic `/æ/`, so `æ` is a *fusion candidate* (into open-front `a`) that needs the witness search — "does any language contrast `/æ/` with a front/central `/a/`?" — before it can leave. The line "æ/ɑ is backness, not height" is the assertion under test, not a settled reason.

That a pruned cell's occupants land somewhere sensible without special-casing is the signal that it was never a point.

## 10. Tests to add

```
test_every_point_has_witness      # §9 rule; symmetric to test_no_merged_contrasts
test_unique_code_per_phoneme      # catches splits, which the merge test cannot see
test_label_namespaces_disjoint    # rule 5.5
test_modifier_order_canonical     # rules 5.1, 5.2
test_concatenation_decodable      # ⚠ [m4] NEW — round-trips a concatenated label
                                  #   stream; the real guard against B1. namespaces_disjoint
                                  #   (first-letter only) passes even while the scheme is
                                  #   ambiguous, so it gives false confidence on its own.
```

`test_unique_code_per_phoneme` is worth adding regardless of whether ATR lands, since any future orthogonal feature can reintroduce the same split. **[E1: endorsed.]**

## 11. Review addendum — the B1 fix (recast quality to uppercase)

The one structural change the review asks for. Keep everything about the proposal — the tiering instinct, the stacking, the modifier order — but move the five **quality operators** out of lowercase (where they collide with consonants) into the uppercase rides-on-base tier, using the letters the modifiers don't: `H X W V Q`.

| Was (lowercase, ambiguous) | Becomes | Example |
|---|---|---|
| `h` lower | `H` | ɪ = `iH` |
| `x` centralise | `X` | ɨ = `iX` |
| `w` round | `W` | y = `iW` |
| `v` unround | `V` | ɯ = `uV` |
| `q` retract | `Q` | ɑ = `aQ` |

- **Lowercase vowel letters shrink to the 5 cardinals** `a e i o u`. Any lowercase run that isn't one of those is a consonant. Any uppercase is a vowel operator. → self-segmenting against lowercase consonants; B1's `ix`/*их* collision is gone (`iX` vs `i` `x`).
- **Ordering is unchanged**, just all-uppercase now: quality `H → X/Q → W/V` first (these define the point), then modifiers `G → C → N → B/K → R → L`. A long nasal −ATR ɪ is `iHGN L`→ `iHGNL`.
- **Point-creation is tracked in the model, not the case.** The slogan updates: *lowercase = 5 cardinal anchors; uppercase = everything that rides — some of it point-creating (`H X W V Q`), the rest pure modifiers (`G C N B K R L`).* This is a more honest statement of what the tiers are than "uppercase never creates a point."
- **Cost:** labels get longer and uppercase-heavier (`iHW` for ʏ vs `ihw`). That is the price of dropping the delimiter. Everything the proposal valued — no combining marks, ASCII, free stacking, one spelling per phoneme — is preserved.
- **Out of scope, flagged:** this fixes only the vowel half. Consonant digraphs (`sh`, `ng`, `sy`) carry the same disease at the stream level ([m2]); the Phase-2 consonant scheme owes the same treatment before full transcriptions are decodable.
