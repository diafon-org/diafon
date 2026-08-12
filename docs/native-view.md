# diaphone — native view (Latin + diacritics)

A reading layer that renders the notation as Latin letters with diacritics, using existing Unicode
codepoints (bespoke font later). It's chosen by *sound/legibility*, not a blind transliteration of the
labels. **Placement rule:** consonants wear their mark **below** or **above** as dots/accents (no
superscript index letters); vowels wear it **above** — except the in-between/exotic dots below.

Status legend: ✓ decided · ◻ open.

## Consonants

| operator / point | mark | glyphs | |
|---|---|---|---|
| palatal `j` | **single vertical line below** `U+0329` | sj→**s̩** · zj→**z̩** · nj→**n̩** · lj→**l̩** · tj→**t̩** · dj→**d̩** | ✓ (latin22's mark — renders cleaner than the combining comma, and pairs as one-line vs the two-line soft) |
| palatalised *modifier* (Russian) | **double vertical line below** `U+0348` | pʲ→**p͈** · kʲ→**k͈** … · sʲ→**s͈** · zʲ→**z͈** | ✓ (latin22's *soft/tense* mark; the two-line partner of the single-line palatal points; coronal soft tʲ nʲ lʲ dʲ = `tj nj lj dj` = the palatal points t̩ n̩ l̩ d̩) |
| trill / tap `r` | — / **dot-below** | r → **r** · ɾ `rj` → **ṛ** | ✓ (retroflex approximant merged into r; ṛ freed for the tap) |
| affricate `c` | letter | tc→**c** · dc→**đ** | ✓ |
| hush `q` (affricate+palatal) | letter + **vertical line below** | tq→**c̩** · dq→**đ̩** | ✓ (dʒ=đ̩; the palatal line rides the affricate) |
| dental / velar `x` (fricativise) | **one dot below** | tx→**ṭ** · dx→**ḍ** · kx→**ḳ** · gx→**g̣** | ✓ (θ/ð/x/ɣ = the homorganic fricative) |
| pharyngealised (`qx`) | **two dots below** | tˤ→**t̤** · dˤ→**d̤** · sˤ→**s̤** · ðˤ→**ẓ** | ✓ |
| aspirated `h` | **one dot above** | ṗ ṫ k̇ · ċ (tsʰ) · ċ̩ (tʃʰ, dot above + palatal line) | ✓ |
| labialised (`c` on k/g) | **two dots above** (diaeresis) | k̈ g̈ | ✓ — diaeresis = rounding, same as vowels ü ö |
| pf `pc` | diaeresis `p̈` (on p — no clash with k/g) | p̈ | ✓ |
| long `w` | doubled letter (tight-set) | tt … | ✓ |

**Gutturals** are off-grid, so they get their own mini-scheme on the `h` base: **crossbar = one step
deeper** (glottal → pharyngeal) and **underdot = the paired second sound** at that depth. So **h** = /h/,
**ḥ** = ʔ (glottal + underdot = the stop), **ħ** = ħ (pharyngeal, the crossbar), **ħ̣** = ʕ (pharyngeal +
underdot = the voiced one). The uvular stop keeps its letter **q**. **No superscripts anywhere.**

## Vowels

| operator / point | mark | glyphs | |
|---|---|---|---|
| `c` = flip front↔back (rounded pair) | **diaeresis** | u→**ü** (y) · o→**ö** (ø) | ✓ |
| `c` = flip front↔back (unrounded) | **diaeresis** | i→**ï** (ɯ) · e→**ë** (ɤ) · a→**ä** (ɑ) | ✓ (one rule: diaeresis crosses the front/back divide, keeping rounding; base letter stays above the dot-below `j` slot) |
| long `w` | acute; +round → double-acute | á é í ó ú · ő ű | ✓ |
| nasal `y` (dedicated operator) | tilde | ay→**ã** · ey→**ẽ** · oy→**õ** | ✓ (French, 3-way: brin ẽ · banc ã · bon õ; `y` = the one free letter, not `h` which is a base) |
| lower `j` (one step) | **one dot below**, uniform | ij→ị · ej→ẹ · uj→**ụ** (ʊ) · oj→**ọ** (ɔ) | ✓ (`j` lowers front *and* back the same way; `iq`=ụ̈ `eq`=ọ̈ add the diaeresis for `c`) |
| schwa `ax` | the letter | ə | ✓ |
| rhotic `q` on schwa — `axq` (ɝ) | hooked schwa | **ɚ** | ✓ (moved off `r`: `q` is inert on a central vowel, so no trill overlap) |

Two clean rules carry the vowels. **Diaeresis = flip front↔back** (keeping rounding): u/o→ü/ö are the
front-rounded y/ø, and i/e/a→**ï/ë/ä** are the back-unrounded ɯ/ɤ/ɑ — one mark, symmetric on both sides,
and it sits *above*, so it never touches the dot-below `j` slot. **`j` = lower one step, uniformly**
(ij=ɪ ej=ɛ uj=ʊ oj=ɔ) → **one dot below on every j-vowel** (ị ẹ ụ ọ); the base letter says front vs back.
So the low vowels read **a · ä (ɑ, `ac`) · ọ (ɔ, `oj`) · ə** — all distinct, and **Hungarian á/a renders
as á/ä**, a clean a-family pair (HU short a /ɒ/ folds into ɑ; base `a` is the common low vowel, 13
languages, only French contrasts a~ɑ). Round in-between (ʏ, œ): below-dot + diaeresis — `ụ̈` = U+1EE5 +
U+0308. Unattested lengths compose: `ojw`=ɔː → ọ́ (the long acute rides any vowel glyph).

## The mark system
The mark carries the feature; the base letter says which (like the operators — `x` is dental
on t, velar on k). Marks live on distinct letters (or vowel vs consonant), so nothing clashes:
- **diaeresis `¨` (two dots above)** — vowels: flip front↔back (ü ö · ï ë ä) · consonants: labialised k̈ g̈, pf p̈.
- **one dot above `˙`** — consonant aspirated (ṗ ṫ k̇).
- **tilde `˜` (above)** — nasal vowel (ã ẽ õ), the `y` operator.
- **one dot below** — consonant fricativise (ṭ ḍ ḳ g̣) · vowel lowered `j` (ị ẹ ụ ọ) · the tap **ṛ**.
  The tap's dot is the one glyph whose meaning is **language-specific**: universally ṛ = tap (ES/JA/TR), but a Mandarin-flavoured view may read it as the retroflex ⟨r⟩ — safe because no language has both a tap and a retroflex approximant, so ṛ stays unambiguous within any one language.
- **two dots below** — consonant pharyngealised (t̤ d̤ s̤).
- **single vertical line below `U+0329`** — the palatal points (t̩ n̩ l̩ s̩ z̩ d̩ · hush c̩ đ̩); latin22's mark, renders more reliably than the combining comma it replaced.
- **double vertical line below `U+0348`** — consonant palatalised / *soft* (p͈ k͈ · s͈ z͈): the two-line partner of the palatal single line. One codepoint, side by side, no stacking; doubles as the IPA tense/fortis sign (Korean t͈). So **one line = palatal · two lines = soft**.

Side effect: **k** runs the full set — k · k̇ (aspirated) · k̈ (labialised) · ḳ (velar fricative).

## Status
All cells decided. Next: bespoke glyphs/font (later), and wiring `native` as a target in the engine.
