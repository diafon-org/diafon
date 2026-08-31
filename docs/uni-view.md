# diaphone — the uni view (Latin + diacritics)

The notation rendered as Latin letters with diacritics (existing Unicode; bespoke font later).
Chosen for sound and legibility, not a blind transliteration of the labels. No superscript
characters anywhere.

## The mark grammar

**Meaning = mark shape and count. Side = typography.** Each mark means one thing wherever it
appears; which side of the letter it sits on says nothing — the letterform decides:

- **below is the default**;
- the **two dots are always above** — one mark, one side, on every letter;
- the **place-like marks** (dot, comma, tail) go below by default, and above only when the below
  zone is taken — a descender letter **p g** (ṗ ġ p̓ g̓), or a glyph already wearing one;
- **nothing else sits above a tall letter**.

| mark | meaning | glyphs |
|---|---|---|
| **one dot** | the `c`/`x`/`y` mark | the x-points ḳ ġ (x ɣ) · THE EXOTIC SLOTS ṭ ḍ ṇ ṗ ṣ ẓ k̇ g̣ (`y` — defaults θ ð ŋ pf ħ ʕ; aspiration, ejectives and the fallen soft s z ride the same dot) · the tap ṛ (`rc`) · the schwa ạ (`ax`) · lowered vowels ị ẹ ụ ọ (`j`) |
| **two dots** | **always above** | vowel FLIP front↔back ü ö (y ø) · ï ë ä (ɯ ɤ ɑ) (`c`) · vocalic r̈ (`aq`) — and nothing else |
| **tilde** | nasal, nothing else | above a vowel: ã ẽ õ (`y`) |
| **comma** | the `j` mark, one per j — and never doubled | the hush points ș z̦ and their affricates c̦ x̦ · every soft consonant ț d̦ n̦ l̦ p̓ k̦ b̦ m̦ r̦ … — every comma is palatal. Where the comma's slot is a point (s z tc), that palatalization is the language's EXOTIC and takes the dot instead: сь = `sy` ṣ |
| **"\\" tail** | the SECOND-exotic `x` | retroflex ʈ ɖ ɳ ɭ ɻ = `tx dx nx lx rx` · the hush layer s̖ z̖ c̖ x̖ (PL sz ż cz dż; it replaces the j-comma rather than stacking) · Arabic tˤ dˤ (`tx dx` — the same slots, read per language) |

## Consonants

| what | mark | glyphs |
|---|---|---|
| palatal & soft (`j`) | one comma per j | the hush points ș z̦ · their affricates c̦ x̦ · the soft consonants ț d̦ n̦ l̦ k̦ b̦ m̦ … (s and t precompose to ș ț) · p̓ above |
| … where the slot is taken | the exotic dot | soft s z ts fall to the exotic slot: `sy zy tcy` = ṣ ẓ c̣ — one dot, never a doubled mark |
| retroflex modifier (`x`) | the "\\" tail | t̖ d̖ n̖ l̖ r̖ · s̖ z̖ c̖ x̖ (TA HI BN PL …) |
| velar fricatives (`x`) | one dot | ḳ · ġ above (x ɣ) |
| the exotic slots (`y`) | one dot | ṭ ḍ ṇ ṣ ẓ · ṗ k̇ above · g̣ — stated defaults θ ð ŋ ħ ʕ, pf; the Arabic emphatics read ṣ ẓ (and t̖ d̖ on the second slot) |
| tap (`rc`) | one dot | ṛ (trill stays r) — `c` draws the dot here as everywhere; `j` on r is left to the soft r̦ |
| aspirated (`y`) | the exotic dot | ṗ ṭ k̇ c̣ ċ̦ — a reading of the same slots; stacked above a tail: ṫ̖ (HI ʈʰ `txy`) |
| whole characters | no mark | c (ts `tc`) · x (dz `dc`) · q (`kq`) · ' (ʔ `hq`) — see below |
| long (`w`) | doubled letter | tt șș … |

**Letter-points.** A base carries more points than the mark grammar can build for it, so the extras
take a whole character instead: **c** /ts/ (`tc`), **x** /dz/ (`dc`), **q** /q/ (`kq`), **'** /ʕ/
(`hq`). See it on t, which ran out first — ṭ (the dot) and ț (the comma) exhaust its marks, so `tc`
became the letter c and `tq` the letter-plus-mark c̦. k is the same case one point earlier: ḳ takes
the dot for /x/, and /q/ takes the letter.

The first three are **operator letters** (`c` `x` `q`), never the modifier-only ones (`y` `w`)
— the same line the marks obey. And the pair c/x follows the system's own shape for voicing: every
voiced partner is a plain, visually unrelated letter (p/b, t/d, k/g, f/v, s/z), never a modified one.

**The view is therefore plain ASCII letters + combining marks, with one exception** — the apostrophe
for /ʔ/. Every other character is a letter (the last non-ASCII one, đ for /dz/ and /dʒ/, is gone),
which is what lets the view survive in an arbitrary font, a message box, or a plain-text field, with
or without the project font.

**Gutturals**: h carries h /h/ and **'** /ʔ/ (`hq`). **The pharyngeals are not h-forms**: ħ ʕ ride
the k/g exotic slots — **k̇** (`ky`) and **g̣** (`gy`) — symmetric with the velar fricatives ḳ ġ
(Arabic خ~ح = `kx`~`ky`, غ~ع = `gx`~`gy`), the exotic as the guttural one step beyond x.

/ʔ/ is the one point the mark grammar cannot draw: `q` composes both marks where it can
(`iq` = ụ̈), but on h it cannot — the c-dot and the j-comma both live below, two below marks never
stack, and nothing sits above a
tall letter. So `hq` takes a whole character — and **which sound gets it is decided by precedent,
because a whole character has no shape the grammar could derive.** It goes to the glottal stop: `'`
is the glottal stop in Hawaiian, Samoan, Tongan and Māori (the ʻokina), across Mayan, in Tagalog and
Guaraní, and hamza in ASCII Arabic. U+0027 is the only candidate every font and keyboard has: 40/40 scanned fonts, against
27/40 for ʼ (U+02BC) and 18/40 for ʿ (U+02BF). Two prices, both taken knowingly: it is punctuation
rather than a letter, so a word-break splits it off and some editors autocorrect it to ’; and it has
no capital form.

**The r base is regular.** `rc` is the tap (ṛ — `c` draws the dot, as everywhere) and `rj` is the
soft r (r̦ — `j` draws the comma, as everywhere), so every mark on r is one slot, read per language, with no
exception and nothing doubled: r · ṛ · r̦ · r̖ · r̈. The soft r is an ordinary member of the soft
series (k̦ b̦ m̦ r̦). What an operator *means* is base-dependent everywhere — `c` is affricate on
t/d and the second rhotic on r — but the mark it *draws* never varies.

**Every exotic slot has a stated DEFAULT reading** — declared data (`labels.yaml exotic_defaults`
for the `exotic` modifier, the primary composition for the rest), which is what the universal
targets print and which never moves when a language is added; the exotic registry lists each
language's override and is the per-language authority.

**The mark always follows the operator — everywhere, no exceptions.** `c`/`x` draw the dot and `j`
draws the comma on every base. What an operator *means* is base-dependent — `c` is affricate on t/d
and the tap on r — but `j` is palatal everywhere and every comma in the view is palatal. /ʔ/ is a
whole character because the mark grammar cannot build it on the tall h (both q-marks live below,
and two below marks never stack).

**No point wears a modifier-only mark.** The modifier-only letters are `y` (the exotic dot —
aspiration, ejectives, the emphatics; nasal on a vowel) and `w` (long) — neither ever forms a
point, so their marks belong to the modifiers alone, and the "\\" tail is
retroflex, full stop. `j` `x` `c` `q` are different — they are operator *and* modifier letters by
design (base+letter is that point if it exists, else it reads as the modifier), so their marks are
shared: k̦ is /kʲ/ and ț is Hungarian *ty* and Russian *ть* alike, all legitimately wearing the
j-comma.

**The palatal coronals are one sound each.** /c ɟ ɲ ʎ/ and /tʲ dʲ nʲ lʲ/ are the same points — no
language contrasts them, and the difference is phonetic, which this system does not encode. So
ț d̦ n̦ l̦ carry Hungarian *ty gy ny*, Spanish *ñ*, Italian *gl* and the Russian soft coronals with
**one** comma. Soft s and z take the exotic dot instead (`sy zy` = ṣ ẓ), because there the single
comma already spells a point — ș z̦ are /ʃ ʒ/, which Russian contrasts with /sʲ zʲ/
(*сесть*~*шесть*). The same ṣ ẓ are Arabic's emphatic ṣād and ẓāʾ: one slot, read per language,
never two sounds within one language (the exotic registry).

## Vowels

| what | mark | glyphs |
|---|---|---|
| flip front↔back (`c`) | two dots | ü ö (y ø) · ï ë ä (ɯ ɤ ɑ) |
| lower one step (`j`) | one dot (down) | ị ẹ ụ ọ (ɪ ɛ ʊ ɔ) · +flip: ụ̈ ọ̈ (ʏ œ) |
| long (`w`) | acute · on a FLIPPED vowel the double acute (one mark, never dots+acute) | á é í ó ú ạ́ · ű ő i̋ e̋ a̋ · ụ̋ ọ̋ |
| nasal (`y`) | tilde | ã ẽ õ (French 3-way) |
| schwa (`ax`) / rhotic (`aq`) | ạ (a + the x-dot) · r̈ | the r glyph family: r trill · ṛ tap · r̦ soft · r̖ retroflex · r̈ vocalic — one mark per slot, read per language |
| glides (`x` on close vowels) | letters + the flip mark | j w (ix ux) · j̈ (ɥ `icx`, French) · ẅ (ɰ `ucx`) — a systematic slot, attested nowhere |
| tone signs (opt-in `--tones`) | ◌̄ ◌́ ◌̌ ◌̀ on the vowel | șān ḳǎu kuó (Pinyin-priority placement; 0/5 neutral; plain digits by default) |

Two rules carry the vowels: **two dots flip front↔back keeping rounding** (both directions, one
mark), and **`j` lowers one step uniformly** (the base letter says front vs back). The low vowels
read a · ä (ɑ) · ọ (ɔ) · ạ (ə) — all distinct; Hungarian á/a renders á/ä in uni (real á/a lives in the
`hu` target). Everything composes: `ojw` = ɔː → ọ́; unattested glides/lengths still render.

**Capitals**: input is case-insensitive; an initial capital renders as the capitalised glyph
(Sjok → Șok, SJOK → ȘOK). IPA ignores case.

## Status
All cells decided; `uni` is a live engine target with the opt-in tone signs. The bespoke
**Diaphone font** exists as a derivative of Noto Serif (SIL OFL; `scripts/build_font.py` →
`fonts/Diaphone-Regular.ttf`, subset to the engine's exact character set, mark positioning
kept) — the base for glyph work: mark tuning via the SVG round-trip (`scripts/font_svg.py`),
then bespoke letterforms.
