# diaphone — native view (Latin + diacritics)

A reading layer that renders the notation as Latin letters with diacritics, using existing Unicode
codepoints (bespoke font later). It's chosen by *sound/legibility*, not a blind transliteration of the
labels. **Placement rule:** consonants wear their mark **below** or as a **superscript index**; vowels
wear it **above** — except the in-between dot, whose position deliberately encodes direction.

Status legend: ✓ decided · ◻ open.

## Consonants

| operator / point | mark | glyphs | |
|---|---|---|---|
| palatal `j` | comma-below | sj→ș · zj→z̦ · nj→ņ · lj→ļ · tj→ț · dj→ḑ | ✓ |
| affricate `c` | letter | tc→**c** · dc→**đ** | ✓ |
| hush `q` (affricate+palatal) | letter + comma-below | tq→**c̦** · dq→**đ̦** | ✓ (dʒ=đ̦; `j` is the informal alt) |
| aspirated `h` | **overdot** ˙ | ṗ ṫ k̇ · ċ (tsʰ) · ċ̦ (tʃʰ) | ✓ |
| pharyngealised (`qx`) | **dot-below** | ṭ ḍ ṣ ð̣ | ✓ |
| labialised (`c` on k/g) | superscript **ʷ** | kʷ gʷ | ✓ (stays superscript: kʰ=k̇ vs kʷ would collide) |
| long `w` | doubled letter (tight-set) | tt … | ✓ |
| dental `x` | — | θ / ð | ◻ (upper-index? under/over dot?) |
| velar `x` | — | x / ɣ | ◻ |
| pf `pc` | superscript **f**? | pᶠ | ◻ |

Gutturals/uvular keep their letters where they exist (ʔ ħ ʕ q).

## Vowels

| operator / point | mark | glyphs | |
|---|---|---|---|
| round `c` | diaeresis | ic→ü · ec→ö | ✓ |
| long `w` | acute; +round → double-acute | á é í ó ú · ő ű | ✓ |
| nasal `h` | tilde | ã õ ẽ … | ✓ |
| in-between `j` — front (steps down) | **dot below** | ij→ị · ej→ẹ · iq→ụ̈ · eq→ọ̈ | ✓ |
| in-between `j` — back (steps up) | **dot above** | oj→ȯ (ʊ) · aj→ȧ (ɔ) | ✓ |
| de-rounded back `uc`/`oc` | — | ɯ→**ı** (dotless-i) · ɤ→**ọ** (underdot) | ✓ |
| schwa `ax` | the letter | ə | ✓ |
| open back `ac` (ɑ) | — | à? | ◻ (part of the a-family) |
| rhotic `r` | superscript r | əʳ (ɝ) | ◻ |

Render note: for the round in-between (ʏ, œ), build the below-dot into the base and add the diaeresis on
top so the upper dots don't skid — `ụ̈` = U+1EE5 + U+0308, `ọ̈` = U+1ECD + U+0308.

## The dot theme
Dots run through both halves, always on distinct base letters so nothing clashes:
vowels — front in-between = dot-below (ị ẹ), back in-between = dot-above (ȯ ȧ);
consonants — aspirated = dot-above (ṗ ṫ k̇), pharyngealised = dot-below (ṭ ḍ ṣ).

## Still open
- **the a-family** — a, ɑ (ac), ɔ (aj/ȧ) — settle the three together
- **dental θ/ð and velar x/ɣ** — upper-index / dot idea
- **pf** — superscript f
- **rhotic** vowel mark
