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
accepted ambiguities live in `notation._ACCEPTED` (only aspiration `Ch`, boundary-only — the rhotic
overlap is gone since rhotic moved off `r` to `q`; ɝ = the irregular short label `aq`, see notation._IRREGULAR); anything else fails `diaphone --strict` and the test. Latin `ku` was
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
src/diaphone/render.py      notation → universal IPA target
src/diaphone/native.py      notation → the native Latin+diacritics view (docs/native-view.md)
src/diaphone/engine.py      ONE render entry: render(text, target) — ipa/native (universal) + languages
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
diaphone decode zh "sjan1 kxaxn3 kau1"   # -> shān hěn gāo   (trailing digit 1-4 = Pinyin tone)
diaphone decode hu "alma kert" --lazy   # -> alma kert      (--lazy: per-language shortcuts)
diaphone export-json     # -> out/engine.json — the engine as pure data, for ports (Mac input method);
                         #    tests/test_export.py proves the export is sufficient for a port
pytest                   # runs the invariant guardrails
```

## Universal render (`render.py`)
`decode.py` gives a *language's* spelling; `render.to_ipa` gives the *universal* IPA — each point label
maps back to its general point's canonical IPA, each modifier becomes a diacritic (long ː, palatalised ʲ,
aspirated ʰ, labialised ʷ, nasal ̃, rhotic ˞, pharyngealised ˤ), trailing tone digit → superscript.
`diaphone ipa "sjan1 kxaxn3 kau1"` → `ʃan¹ xən³ kau¹`. The native Latin+diacritics counterpart is `native.py` (see docs/native-view.md).

## Decoding (`decode.py`)
Notation → a language's spelling. Canonical labels live in `data/orth/<lang>.yaml`; extras layer on:
- **Mandarin tones** — a trailing digit `1-4` on a zh syllable places the Pinyin tone mark (`5`/none =
  neutral); placement is the standard a > e > ou > last-vowel rule.
- **Mandarin finals/palatals** — vowel labels concatenate into finals; the -u offglide spells "o" only
  after `a` (au→ao; ou/uo keep u). Because we folded Pinyin j/q/x into zh/ch/sh (`_ZH_RETRO`), the
  *following vowel* picks the spelling: front `i`/`ic`(ü) → j/q/x (+ ü→u), else zh/ch/sh. The
  apical/buzzed vowel (zhī, shì, sì) is written `uc` — Pinyin also spells it "i", but it is not front
  `/i/`, so it keeps the retroflex spelling. So `tqi1`=jī but `tquc1`=zhī; `sji1`=xī but `sjuc4`=shì.
**Strict vs loose (per-language).** Every language has an optional **loose** ("not strict") mode — a
*local* toggle that turns on that language's simplifications, of two kinds: the **input** (lazy typing
shortcuts, `decode.LAZY_ALIASES`) and the **view** (native-glyph overrides, `native._LANG_OVERRIDE`, e.g.
HU ɑ→a so *alma* not *älmä*). Strict is the canonical default; loose is opt-in and never changes the point
set. The whole-system page surfaces it as one `loose (not strict)` toggle per language target.

- **Lazy mode** (`decode(..., lazy=True)` / `--lazy`) — the *input* half of loose; opt-in shortcuts in `decode.LAZY_ALIASES`
  (grapheme map, overriding canonical): HU bare `a`=/ɒ/, `e`=/ɛ/. ZH ≈ **"type Pinyin"** — the
  sibilant/affricate initials + `o` spell literally (`xiao`=xiǎo, `shi`=shì, `zhong`=zhōng, `cai`=cài),
  so the sh/x apical/front split is carried by the user's own Pinyin spelling. The one set NOT added is
  the aspirated stops `p/t/k` (they clash with the notation, where p/t/k are the *lenis* series) — so
  canonical still decodes in lazy mode; use `ph/th/kh` for aspirated stops. Canonical files stay pure.

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
68 fine-grained points → **53 general** (36 C · 17 V) after 15 merges, 0 merged contrasts, 490
phoneme records, 16 languages (12 core + 4 witnesses). **Every point is a base or base + ONE
operator** — no 2-operator points, no bi-vowels. Removed (not points): `ç` (German ich-laut → `x`),
`ɸ` (Japanese *fu* → `h`), `ɐ` (German `-er`), **Mandarin j/q/x `[tɕ tɕʰ ɕ]`** (allophones of the
retroflex series), the **glides `/j/ /w/ /ɥ/`**, and **`ʌ`** (folded into schwa: English STRUT =
stressed `/ə/`, Korean ㅓ ≈ schwa). Vietnamese `ă` re-read as short `/a/`.

## Notation (Phase 2 — locked, round-tripped)
`data/labels.yaml` gives one label per general point; `labeler.py` validates it, `out/labels.json`
regenerates it. **Every point is a base or base + ONE operator** — no tier, no case, no diacritics.
- **Bases** `p b t d k g m n f v s z l h`, the trill `r` (the common rhotic; tap `ɾ`=`rj`), and 5
  vowel letters `a e i o u` (`y` retired — schwa is now `ax`). Glides `/j/ /w/ /ɥ/` removed.
- **One mechanism — SEVEN operators `c j q x w h y`, all base-dependent.** Four (`c j q x`) can form new
  points; the rule per case: *base+letter is that point if it exists, otherwise the letter reads as the
  modifier* (`sj`=ʃ point vs `pj`=pʲ modifier; `tc`=t͡s point vs `kc`=kʷ modifier). `w h y` only ever ride
  as modifiers (`y` = emphatic on a consonant / nasal on a vowel).
- **Consonant operators** (never a bare label): `c`=affricate (`tc`=t͡s) · `q`=hush **affricate**
  (`tq`=t͡ʃ) · `x`=dental/velar (`tx`=θ, `kx`=x) · `j`=palatal (`sj`=ʃ, `tj`=c/tʲ, `nj`=ɲ) · `w`=long
  (`tw`=tː, geminate/long trill `rw`). So `q`=`c+j` (hush = affricate+palatal). **Gutturals** are a 2×2 on
  `h` via the same c/j/q pattern: `c`=pharyngeal (deeper), `j`=the marked second sound, `q`=c+j=both — so
  `h` · `hj`=ʔ (glottal stop) · `hc`=ħ · `hq`=ʕ (voiced pharyngeal), each base+ONE operator, mirroring the
  native `h · ḥ · ħ · ħ̣`. Emphatics ride on `y` on the consonant (`tˤ`=`ty`; base-dependent — `y` is nasal on a vowel).
- **Vowels** (17, triangular — see `docs/viz/notation.html`): 5 cardinal bases `a e i o u` on the
  triangle edges; operators `c`=toggle-rounding (front gains: `ic`=y `ec`=ø; back loses: `uc`=ɯ `oc`=ɤ;
  apex marks back: `ac`=ɑ), `j`=**lower one step, uniformly** — each in-between vowel is its higher
  neighbour lowered (`ij`=ɪ `ej`=ɛ `uj`=ʊ `oj`=ɔ); `a` is already lowest so `aj` is unused. So ɔ is
  o-based (the lowered o). `q`=`c+j` front-round lowered (`iq`=ʏ `eq`=œ — French œ / German ʏ keep it),
  `x`=centralise→schwa (`ax`=ə, which also carries English STRUT ʌ / Korean ㅓ). Every vowel is base+1op.
  **ɒ→ɑ merged** (`ac`): only HU had ɒ; its short a is open back, adjacent to ɑ — so **HU á/a = `a`/`ac`**,
  a clean c-pair, and the ear keeps ɔ (`oj`) for the languages that have it (DE EN FR IT VI). œ→ø and
  ʏ→y were tried and **reverted** — the injectivity check caught them collapsing French *jeûne/jeune*
  (no French vowel length to recover) and German ü/ö.
- **Modifiers ride on top, one letter each**: long `w`, aspirated `h` (consonants), **nasal `y`** (vowels —
  `y` is the one free letter after retiring the vowel base, so nasal gets a dedicated operator, not the /h/
  base: `ay`=ã; French is 3-way ẽ ã õ, œ̃ dropped as merging), rhotic **`q`** on the schwa (`aq`=ɝ — an irregular short label, ax+q with the x elided, cf. `sjj`;
  `q` is inert on a central vowel, so no trill overlap); palatalised `j` (`pj tj`…) but
  **`jj` on s/z** (`sʲ`=`sjj`, since `sj`/`zj`=ʃ/ʒ); pharyngealised
  `y` on the consonant (base-dependent: nasal on a vowel, `ay`=ã); labialised is `c` on k/g (`kc`=kʷ — those bases have no affricate, so the round `c` slot is
  free), NOT bare `u`, which would collide with the vowel /u/ (Latin quī/cui). See the notation invariant.
- Validated: all **490** phonemes get a distinct label per language, **0 collisions**, and (now that
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
    (tap) — Spanish *perro/pero*, significant. **MERGE** the retroflex approximant `ɻ`/`ʐ`
    (Mandarin/English ⟨r⟩) → the plain trill `r`, and `ɹ` → `ɻ` → `r` with it: no language in the
    16 has the retroflex approximant *and* a trill/tap, so EN/ZH ⟨r⟩ collapse into the generic **R
    slot** (realised approximant/trill/retroflex per language, contrasted nowhere), no recovery
    mark. This *reverses* the earlier "KEEP ɻ, Dravidian witness" verdict — retroflex is unmarked
    everywhere (the sibilants fold too), so singling out the approximant was the odd one out; rather
    than load a Tamil/Malayalam witness to defend a distinction the 16 never use, we drop it. Note
    `ʁ` is NOT a rhotic merge — Arabic contrasts `ʁ` (ghayn) ~ `r` (rā). (The retroflex *sibilants*
    `ʂ ʐ tʂ` also fold into the postalveolar with no mark — Mandarin's are complementary allophones.)
  - **RESOLVED as allophones (removed):** `ç`, `ɸ`, `ɐ` — see the allophone guard above.
  - **No open near-merges remain** — same-manner *and* the cross-manner rhotic family are both
    swept. Every pair is decided: KEEP (witnessed), MERGE-via-diacritic (exotic), MERGE-outright
    (no witness), or removed (allophone). Applying the merges is Phase 2 → general inventory ~61.
- **Phase 2 (done — merge ledger + notation):** `merges.py` folds the fine-grained **68** into the
  general inventory **53** (36 C · 17 V) via 15 merges; `apply_merges()` asserts safety per
  `(target, recovery-mark)` per language. **No recovery diacritics on consonants** — every
  consonant-place merge is `recover=None`: within the 16 languages nothing contrasts dental~alveolar,
  retroflex~postalveolar/alveolar (Mandarin's are complementary allophones), or uvular~velar, so the
  fold is lossless-in-practice and needs no sign. Retroflex is therefore **unmarked everywhere** — the
  sibilants `ʂ ʐ tʂ` fold into the postalveolar, and the approximant `ɻ` folds into the plain trill
  `r`. `labels.yaml` assigns the flat notation (see "Notation" above); all 490 phonemes round-trip to
  distinct per-language labels. **Superseded verdicts:** the old "retroflex trio via underdot",
  "tʃ/tɕ kept", and "KEEP ɻ (Dravidian witness)" plans below are obsolete — the retroflex sibilants
  *and* the approximant now fold with no mark, and `tʃ~tɕ` merged.
- **Native-view diacritics may carry language-specific minor meaning** (accepted deliberately, against
  the universal-phonemic-base principle but bounded): a native glyph's mark can mean one thing
  universally and another in a specific language's rendering *iff no language contrasts the two* — so it
  stays injective within every language. Case in point: the underdot `ṛ` = tap (ES/JA/TR) universally,
  but a Mandarin-flavoured view may read it as the retroflex ⟨r⟩. This is a *rendering-layer* licence
  only; the point inventory itself stays strictly universal. See `docs/native-view.md`.

## Open decisions
- LICENSE not chosen yet (Sz' decides — mirror weCan conventions if relevant).
- Greek is Modern; swap to Ancient if we want to pair it with Latin.
