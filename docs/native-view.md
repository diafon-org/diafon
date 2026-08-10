# diaphone — native view (Latin + diacritics)

A reading layer that renders the notation as Latin letters with diacritics, using existing Unicode
codepoints (bespoke font later). It's chosen by *sound/legibility*, not a blind transliteration of the
labels. **Placement rule:** consonants wear their mark **below** or **above** as dots/accents (no
superscript index letters); vowels wear it **above** — except the in-between/exotic dots below.

Status legend: ✓ decided · ◻ open.

## Consonants

| operator / point | mark | glyphs | |
|---|---|---|---|
| palatal `j` | comma-below | sj→ș · zj→z̦ · nj→ņ · lj→ļ · tj→ț · dj→ḑ | ✓ |
| affricate `c` | letter | tc→**c** · dc→**đ** | ✓ |
| hush `q` (affricate+palatal) | letter + comma-below | tq→**c̦** · dq→**đ̦** | ✓ (dʒ=đ̦; `j` is the informal alt) |
| dental / velar `x` (fricativise) | **one dot below** | tx→**ṭ** · dx→**ḍ** · kx→**ḳ** · gx→**g̣** | ✓ (θ/ð/x/ɣ = the homorganic fricative) |
| pharyngealised (`qx`) | **two dots below** | tˤ→**t̤** · dˤ→**d̤** · sˤ→**s̤** · ðˤ→**ẓ** | ✓ |
| aspirated `h` | **one dot above** | ṗ ṫ k̇ · ċ (tsʰ) · ċ̦ (tʃʰ) | ✓ |
| labialised (`c` on k/g) | **two dots above** (diaeresis) | k̈ g̈ | ✓ — diaeresis = rounding, same as vowels ü ö |
| pf `pc` | diaeresis `p̈` (on p — no clash with k/g) | p̈ | ✓ |
| long `w` | doubled letter (tight-set) | tt … | ✓ |

**No superscripts.** Gutturals/uvular keep their letters where they exist (ʔ ħ ʕ q).

## Vowels

| operator / point | mark | glyphs | |
|---|---|---|---|
| round `c` | diaeresis | ic→ü · ec→ö | ✓ |
| long `w` | acute; +round → double-acute | á é í ó ú · ő ű | ✓ |
| nasal `h` | tilde | ã õ ẽ … | ✓ |
| in-between `j` — front (down) | one dot below | ij→ị · ej→ẹ · iq→ụ̈ · eq→ọ̈ | ✓ |
| in-between `j` — back (up) | one dot above | oj→ȯ (ʊ) · aj→**ȧ** (ɔ) | ✓ |
| de-rounded back `uc`/`oc` | — | ɯ→**ı** · ɤ→**ọ** | ✓ |
| schwa `ax` | the letter | ə | ✓ |
| open back `ac` (ɑ) | circumflex | **â** (French pâte = /ɑ/) | ✓ |
| rhotic `axr` (ɝ) | hooked schwa | **ɚ** | ✓ |

The a-family reads distinct now: **a · â (ɑ) · ȧ (ɔ)** — plain / circumflex / overdot.
Round in-between (ʏ, œ): build the below-dot into the base then add diaeresis — `ụ̈` = U+1EE5 + U+0308.

## The dot system
Dot count/position carries the feature; the base letter says which (like your operators — `x` is dental
on t, velar on k). Always on distinct letters, so nothing clashes:
- **two dots above `¨` = rounding** — vowels ü ö · consonants k̈ g̈ (labialised), p̈ (pf).
- **one dot above `˙`** — consonant aspirated (ṗ ṫ k̇) · vowel back-in-between (ȯ ȧ).
- **one dot below** — consonant fricativise (ṭ ḍ ḳ g̣) · vowel front-in-between (ị ẹ) / open-back exotics.
- **two dots below** — consonant pharyngealised (t̤ d̤ s̤).

Side effect: **k** runs the full set — k · k̇ (aspirated) · k̈ (labialised) · ḳ (velar fricative).

## Status
All cells decided. Next: bespoke glyphs/font (later), and wiring `native` as a target in the engine.
