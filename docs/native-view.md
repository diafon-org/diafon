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
| pharyngealised (`qx`) | **dot below** | ṭ ḍ ṣ · ðˤ→ẓ | ✓ (ðˤ uses ẓ, the Arabic-Latin form, since ð is already ṿ) |
| dental `x` | underdot on f/v | tx→**f̣** · dx→**ṿ** | ✓ (f/v = nearest fricatives; underdot marks dental) |
| velar `x` | underdot on k/g | kx→**ḳ** · gx→**g̣** | ✓ (k/g fricativised) |
| long `w` | doubled letter (tight-set) | tt … | ✓ |

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
Dot count/position carries the feature; the base letter tells you which one (like your operators:
`x` is dental on t, velar on k). Always on distinct letters, so nothing clashes:
- **`¨` two dots above = rounding** — vowels ü ö, consonants k̈ g̈ (labialised), p̈ (pf).
- **`˙` one dot above = aspirated / raised** — consonant aspirated (ṗ ṫ k̇), vowel back-in-between (ȯ ȧ).
- **`.` one dot below** — base-dependent: emphatic on t/d/s (ṭ ḍ ṣ), velar-fricative on k/g (ḳ g̣),
  dental on f/v (f̣ ṿ), vowel front-in-between on i/e (ị ẹ).

Nice side effect: **k** now runs the full set — k · k̇ (aspirated) · k̈ (labialised) · ḳ (velar fricative).

## Still open
- **the a-family** — a, ɑ (ac), ɔ (aj/ȧ) — settle the three together
- **rhotic** vowel mark (no superscript)
