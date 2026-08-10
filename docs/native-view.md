# diaphone — native view (Latin + diacritics)

A reading layer that renders the notation as Latin letters with diacritics, using existing Unicode
codepoints (bespoke font later). It's chosen by *sound/legibility*, not a blind transliteration of the
labels. **Placement rule:** consonants wear their mark **below** or **above** as dots/accents (no
superscript index letters); vowels wear it **above** — except the in-between dot, whose position
deliberately encodes direction.

Status legend: ✓ decided · ◻ open.

## Consonants

| operator / point | mark | glyphs | |
|---|---|---|---|
| palatal `j` | comma-below | sj→ș · zj→z̦ · nj→ņ · lj→ļ · tj→ț · dj→ḑ | ✓ |
| affricate `c` | letter | tc→**c** · dc→**đ** | ✓ |
| hush `q` (affricate+palatal) | letter + comma-below | tq→**c̦** · dq→**đ̦** | ✓ (dʒ=đ̦; `j` is the informal alt) |
| aspirated `h` | **one dot above** | ṗ ṫ k̇ · ċ (tsʰ) · ċ̦ (tʃʰ) | ✓ |
| labialised (`c` on k/g) | **two dots above** (diaeresis) | k̈ g̈ | ✓ — diaeresis = rounding, same as vowels ü ö |
| pf `pc` | diaeresis `p̈` (on p — no clash with k/g) | p̈ | ◻ p̈, or its own accent |
| pharyngealised (`qx`) | **dot below** | ṭ ḍ ṣ ð̣ | ✓ (ð̣ follows the dental glyph) |
| long `w` | doubled letter (tight-set) | tt … | ✓ |
| dental `x` | — | θ / ð | ◻ (upper-index? under/over dot?) |
| velar `x` | — | x / ɣ | ◻ |

**No superscripts.** Secondary articulations are dots: aspirated = one dot above, labialised = two dots
above (= rounding), pharyngealised = dot below. So kʰ=k̇ vs kʷ=k̈ vs kˤ (n/a) never collide.
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
| rhotic `r` | — | ɝ | ◻ (no superscript — a hook/mark) |

Render note: for the round in-between (ʏ, œ), build the below-dot into the base and add the diaeresis on
top so the upper dots don't skid — `ụ̈` = U+1EE5 + U+0308, `ọ̈` = U+1ECD + U+0308.

## The dot system
One coherent scheme across both halves — always on distinct base letters, so nothing clashes:
- **diaeresis `¨` = rounding** — vowels ü ö, consonants k̈ g̈ (labialised).
- **one dot above** — vowel back-in-between (ȯ ȧ) / consonant aspirated (ṗ ṫ k̇).
- **one dot below** — vowel front-in-between (ị ẹ) / consonant pharyngealised (ṭ ḍ ṣ).

## Still open
- **the a-family** — a, ɑ (ac), ɔ (aj/ȧ) — settle the three together
- **dental θ/ð and velar x/ɣ** — upper-index / dot idea (dots are now spent, so likely a stroke/letter)
- **pf** — `p̈` or its own accent
- **rhotic** vowel mark (no superscript)
