# diaphone — working notes for Claude Code

## What this is
Derives the **minimal set of cross-linguistic phonemic points** for 12 languages
(EN DE ES FR IT LA EL RU AR HU ZH JA) such that **no language's minimal pair is ever
merged** — and proves it. The eventual goal is a universal notation: one label char per
point, one systematic char per modifier.

## Architecture — three layers (Sz)
1. **Covering graph**: the minimal phonemic point set covering all languages, no minimal pair merged —
   `derive.py` + `merges.py`, exported explicitly as `out/graph.json` (`graph.py`).
2. **Unambiguous input**: base chars + operator chars spell every point/modifier, provably decodable
   per language and over the universal stream (`labels.yaml`, `labeler.py`, `notation.py`).
3. **Parameterised rendering**: one engine, few clean targets — universal `uni` (our view; opt-in
   tone signs) and `ipa` (the why-not reference), plus ONE concept per language (`hu`, `zh`, `en` =
   input shortcuts + output conversion together; no per-language flavour of the uni view). Assembly
   rules are data (`engine.py`, `render.py`, `uni.py`, `decode.py` + `data/orth/*.yaml`).

## The core idea (don't break this)
- A **point** is a *base segment*: `(place, manner, voice)` for a consonant,
  `(height, backness, round)` for a vowel. Nothing else defines a point.
- **Modifiers** — `long, nasal, palatalized, pharyngealized, aspirated,
  rhotic, retroflex, nonsyllabic, ejective, exotic` — are stripped off to get the base. They ride on top and **never create
  points** (the glides /j w ɥ ɰ/ are close-vowel points + `nonsyllabic`).
- Two phonemes in different languages **share a point** iff their base tuples are equal.
  Two phonemes in the **same** language may share a point only if a modifier separates
  them. This guarantees `phoneme → (point, modifiers)` is **injective per language**.
- **Minimal set = the distinct base tuples.** `derive()` builds it and validates the
  injectivity invariant; any residual collision means the feature grid is too coarse —
  the fix is a new feature or modifier (e.g. rhotic separates /ə/~/ɝ/, nonsyllabic /i/~/j/).

## Invariant (must always hold)
`merged contrasts == 0`. Enforced by `tests/test_invariants.py` and `diaphone --strict`.
If a data edit breaks it, either the data is wrong or a new modifier/feature is needed —
never "fix" it by deleting a phoneme.

**Second invariant — notation decodability** (`src/diaphone/notation.py`): no phoneme's full label
(point + modifier chars) may also read as a *sequence* of that language's phoneme labels — the
linear-notation cousin of injectivity, catching what `labeler.py` cannot. **The modifier-letter law:
a modifier letter never has a phoneme twin** — `w j y q c x` are never standalone phonemes, so a full
label cannot re-read as a sequence, while a phoneme letter after a base is always the sequence it
looks like (`Ch` = /C/+/h/; aspiration is `Cy`). The accepted-ambiguity list `notation._ACCEPTED` is
**empty and must stay so**; anything either finder reports fails `diaphone --strict` and the test.

**Third invariant — UNIVERSAL-stream decodability** (`notation.find_universal_collisions`): the
per-language check can't see cross-language ambiguity — the universal targets (uni, ipa, the
Mac IM) tokenise against the GLOBAL label set, where every phoneme letter exists even
for languages that lack the phoneme, so this is the stricter check. `notation._ACCEPTED_UNIVERSAL`
is also **empty**. **The guarantee is absolute**: the notation is provably unambiguous per language
AND over the universal stream, zero accepted exceptions. Enforced by `diaphone --strict` and the test.

**Fourth invariant — one label, ONE analysis** (`notation.find_shared_labels`): no label string may
be produced by two different `(point, modifiers)` pairs. The three checks above are all blind to
this — each language is injective by construction, so a clash exists only in the *unioned* universal
stream, where the global set collapses the two readings into one entry. It is real: without the
doubling rule `sj` would be both the hush point /ʃ/ (17 languages) and palatalized /s/ (ET RU UK) —
same label, same glyph, different sounds — IN RUSSIAN ITSELF, which has both. Restated for THE
EXOTIC LADDER: one label = one analysis PER LANGUAGE; cross-language overloading is deliberate
(the exotic registry). `--strict` fails on any within-language share (a "crime").

**Fifth invariant — the point/MODIFIER boundary** (`derive.find_modifier_redundant`): no point may
duplicate what a modifier already spells. If a *relocating* modifier (palatalized, retroflex,
pharyngealized — the only ones that move a segment's place) turns an attested base into an existing
point, and no language contrasts the two, they are ONE phoneme and must be entered as one. Every
other finder is blind to this: they compare a point to a point, never a point to a point-plus-a-
modifier, so a duplicate can survive simply because nothing looked. This is the witness principle
applied across the point/modifier boundary, and it is what makes the palatal coronals `tj dj nj lj`
(below) one point each. Reviewed exceptions would live in `derive._CONFIRMED_MODIFIER_DISTINCT`;
it is **empty**, and `--strict` fails on anything the finder reports.

## Layout
```
data/features.yaml          feature scales + modifier list (drives distance metric)
data/languages/<code>.yaml  one file per language — THIS is where you edit inventories
src/diaphone/model.py       base tuples, modifier→diacritic map, strip_mods
src/diaphone/loader.py      load + expand modifier series (long/nasal/secondary)
src/diaphone/derive.py      minimal points, injectivity, near-merge + suspicious + rhotic finders
src/diaphone/merges.py      merge ledger: fold fine-grained points → general inventory
src/diaphone/graph.py       the covering graph as a first-class artifact (out/graph.json):
                            nodes = general points; edges = derivation (base+operator, the structural
                            proof of "base + ONE op") · adjacency (feature distance 1) · fold (ledger,
                            chain-resolved — canonical IPA is NOT a unique point id, base tuples are)
src/diaphone/notation.py    THE EXOTIC LADDER (`modifier_letter`) + the decodability checks: per-language,
                            universal-stream, and one-label-one-analysis (`find_shared_labels`)
src/diaphone/decode.py      notation → a language's spelling (greedy tokenise + per-lang rules)
src/diaphone/render.py      notation → universal IPA target
src/diaphone/uni.py         notation → the uni Latin+diacritics view (docs/uni-view.md)
src/diaphone/engine.py      ONE render entry: render(text, target) — uni/ipa (universal) + languages
src/diaphone/report.py      JSON + Markdown output
src/diaphone/cli.py         `diaphone` entry point
out/                        generated (gitignored): points.json, general_inventory.json,
                            graph.json, mappings.json, report.md
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
python scripts/lang_delta.py --add path/to/xx.yaml   # DRY-RUN a candidate language: what does it
                         #    force? Verdict is COVERAGE (a subset — free), WITNESS (new point or
                         #    modifier), or BREAKS (a merged contrast / a ledger fold that no longer
                         #    holds). Runs the derivation twice in a temp mirror; data/ is untouched.
python scripts/lang_delta.py --drop RU   # the same in reverse — what would we lose without it?
                         #    NOTE: one language at a time, so a pair held by TWO languages (u~ɯ by
                         #    both TR and KO, o~ɤ by both ET and VI) shows as load-bearing for neither.
python scripts/build_font.py   # rebuild fonts/Diaphone-Regular.ttf (Noto Serif derivative, OFL)
python scripts/check_font_coverage.py --target uni   # which system fonts can't render what we emit
                         #    informational, NOT a gate — `--strict --target uni` currently FAILS
                         #    (Georgia lacks U+0329, the palatal stroke; Verdana lacks 15). The
                         #    uni view still degrades far better than IPA: 16 exposed codepoints
                         #    vs 31. Helvetica/Arial/Times render the uni view completely.
pytest                   # runs the invariant guardrails
```

## Universal render (`render.py`)
`decode.py` gives a *language's* spelling; `render.to_ipa` gives the *universal* IPA — each point label
maps back to its general point's canonical IPA, each modifier becomes an IPA diacritic (long /ː/,
palatalised /ʲ/, aspirated /ʰ/, nasal / ̃/, rhotic /˞/, pharyngealised /ˤ/), trailing
tone digit → superscript. `diaphone ipa "sjan1 kxaxn3 kau1"` → /ʃan¹ xən³ kau¹/.
**THE IPA TARGET NAMES SLOTS — it is not a projection**, and the slot logic that governs the point
set governs it too. A rendering that tracked each language's phonetics would BE a phonetic system,
which this is not. A slot may be realised differently in different languages — `sj` is [ʃ ʂ ɕ], `r`
is [r ɹ ʐ], the plain `d` is [d d̪ ɗ] because Vietnamese đ is an implosive with no plain /d/ to
contrast against — and that overlap is the design. **Slots may overlap ACROSS languages; never
WITHIN one**, which is provable, not hoped for: injectivity gives each phoneme a distinct
(point, modifiers), the doubling rule gives each of those a distinct label, and the invert test
gives each label a distinct glyph and IPA string. Asserted end-to-end per language for both
universal targets by `test_universal_targets_are_slots_not_projections`. So the target is a
*curated table*: one IPA rendering per label, chosen to be what a reader of IPA expects. Every point
has one, and **where IPA has a LETTER for a point+modifier combination we print the letter** rather
than composing a diacritic — `render._SEGMENT_IPA`: `tj dj nj lj` = c ɟ ɲ ʎ (not tʲ dʲ nʲ lʲ) and the
retroflex series `tx nx lx rx` = ʈ ɳ ɭ ɻ, with `sjx zjx` = ʂ ʐ. Remaining modifiers still compose
onto the letter (`tjw` = cː). None of this touches the analysis: it is rendering only, and the uni
view — where one glyph per label is the point of the exercise — is unaffected.
**Modifier order in a label: length LAST** (`notation._mod_chars`) — `w` holds the finished segment,
so a long soft t is `tjw` and its glyph doubles the finished ț → țț. No attested phoneme carries two
modifiers, so this only ever orders systematic compositions. **Superscripts are
an IPA device only** — our own notation and the uni view never use upper-index characters: `uni`
keeps the plain tone digit (`șan1`), or, with **tone signs** on, marks the vowel.
**Tone signs** (`render(..., tones=True)` / `--tones`; `uni.TONE_SIGNS`): an opt-in `uni`
rendering, OFF by default (the zh spelling target carries real Pinyin diacritics inherently).
Signs 1–4 = ◌̄ ◌́ ◌̌ ◌̀
(the Pinyin four); `0`/`5` = neutral (digit consumed). Placement is ONE language-blind PRIORITY
rule over the **last vowel group** of the segment its digit closes: mark the first `a`-based
token, else the first `e`-based, else the first `o`-based, else the **last** vowel token — which
reproduces Pinyin placement exactly (`sjan1 kxau3 kuo2 sjiau3 liu2` → `șān ḳǎu kuó șiǎu liú`);
a vowelless segment or unmapped digit keeps the plain
digit. Digits `1-9` are per-language tone indices, so more-toned languages extend the table, not
the mechanism. Licence note: the acute doubles as the long-vowel mark — opting in accepts that
reading within the user's text (the trade for Pinyin familiarity).
The uni Latin+diacritics counterpart is `uni.py` (see docs/uni-view.md).

## Decoding (`decode.py`)
Notation → a language's spelling. Canonical labels live in `data/orth/<lang>.yaml`; extras layer on.
**Assembly rules are data, not code**: each orth file may carry an ordered `_rules` list (first match
wins; fields `t` token · `g` grapheme · `next`/`prev` token lists · `next_vowel`/`first` booleans),
interpreted generically by `decode._rule_grapheme` — so a new language target is pure YAML end to end
(the export carries them as `rules`, and tests/test_export.py's minimal consumer proves they suffice).
Only two things stay code: the notation-level `w`-gemination and the tone-digit machinery. `_ZH_RETRO`
exists only as the compact export form (`zhRetro`) the Swift/JS ports consume; new ports read `rules`.
- **Mandarin tones** — a trailing digit `1-4` on a zh syllable places the Pinyin tone mark (`5`/none =
  neutral); placement is the standard a > e > ou > last-vowel rule.
- **Mandarin finals/palatals** — vowel labels concatenate into finals; the -u offglide spells "o" only
  after `a` (au→ao; ou/uo keep u). Pinyin j/q/x and zh/ch/sh are ONE point series (complementary
  allophones), so the *following vowel* picks the spelling: front `i`/`ic`(ü) → j/q/x (+ ü→u), else zh/ch/sh. The
  apical/buzzed vowel (zhī, shì, sì) is written `uc` — Pinyin also spells it "i", but it is not front
  `/i/`, so it keeps the retroflex spelling. So `tqi1`=jī but `tquc1`=zhī; `sji1`=xī but `sjuc4`=shì.
**A language target is ONE concept**: that language's input shortcuts (lazy, `decode.LAZY_ALIASES`
— HU bare a/e · ZH type-Pinyin · **EN the familiar digraphs `sh ch zh ng th dh` + bare `j y w`**,
all free letters in English) plus its output conversion (the spelling). There is NO dictionary
anywhere — EN's target is a faithful pronunciation respelling only. Strict is the canonical
default; lazy never changes the point set.

- **Lazy mode** (`decode(..., lazy=True)` / `--lazy`) — the *input* half of loose; opt-in shortcuts in `decode.LAZY_ALIASES`
  (grapheme map, overriding canonical): HU bare `a`=/ɒ/, `e`=/ɛ/. ZH ≈ **"type Pinyin"** — the
  sibilant/affricate initials + `o` spell literally (`xiao`=xiǎo, `shi`=shì, `zhong`=zhōng, `cai`=cài),
  so the sh/x apical/front split is carried by the user's own Pinyin spelling. The one set NOT added is
  the aspirated stops `p/t/k` (they clash with the notation, where p/t/k are the *lenis* series) — so
  canonical still decodes in lazy mode; use `py/ty/ky` for aspirated stops. Canonical files stay pure.

## The SLOT PRINCIPLE (Sz) — the rule the rest are instances of
**A point is a SLOT, not a sound.** Where a language does not *contrast* X with Y, it may enter its
X on Y's slot and realise it however it likes; the realisation goes in `note`. Having every language
represented the *same* way is very much secondary — pursuing that turns the system phonetic, which
is not the aim. **Relatively wide swings in one character's phonetic value are acceptable; an
overlap inside one language never is.** The slots already swing: `sj` = [ʃ ʂ ɕ], `r` = [r ɹ ʐ],
plain `d` = [d d̪ ɗ] (Vietnamese đ). It governs the IPA target identically — see "Universal render".

Every hard call so far is an instance: Korean fortis on `long`, Czech ř on `rj`, Hindi's breathy
series on `aspirated`, Mandarin sh / Russian ш / Tamil ஷ on the unmarked hush point, Polish ś on the
hush point with sz taking the retroflex layer.

**The method for any new sound:**
1. Does the language CONTRAST it with the slot you would reuse? If not — reuse, and stop.
2. If it does: is there a free base+operator LABEL?
3. And a free GLYPH on that base — a mark not in use and not modifier-only (the tail and the tilde
   belong to `retroflex` and `pharyngealized` and can never carry a point)?
4. Both free → a real new point. Otherwise → reuse a slot THAT language leaves empty.

**The slot budget** (`t` and `d` have no free operator at all — anything new on the coronal stops
must reuse, which is why dental folds into alveolar and retroflex is a layer):
```
p  q x        b  c q x      k  c          g  c q        m n f v s z l h r   one or more each
t  —          d  —          ^ k's only free glyph is the doubled comma
```
Worked examples: **labial-velars** k͡p ɡ͡b reuse `kx` ḳ / `gx` ġ — Yoruba and Igbo have no velar
fricatives, and on `k` the only free glyph is the doubled comma, which says nothing about place, so
reuse is forced rather than merely allowed. **Implosives** are usually not contrastive at all
(Swahili, Vietnamese: plain b/d with an implosive realisation); where they are (Hausa, Sindhi), ɓ can
be a real point `bc` ḅ but ɗ has no free label, so it reuses `dx` ḍ — the glyphs still pair.

## Adding a language
**THE CLAIM IS PHONEMIC, NOT PHONETIC.** The system aims at universality in the *phonemic* sense:
what a language CONTRASTS. Phonetic analysis is the instrument, not the target — it is how we find
the right balance (which distinctions a language actually uses, and which are realisation), and it
is never the thing being encoded. That is why /c/ and /tʲ/ are one point, why `sj` covers ʃ, ʂ and ɕ
in different languages, and why Russian ш, Mandarin sh and Tamil ஷ are all the unmarked hush point
even though all three are [ʂ]. A phonetic difference earns structure only when some language uses it
to keep two words apart. Corollary, learned the hard way: a candidate drafted under the WRONG
analysis produces a confident, wrong verdict — the first Polish draft entered ś as an alveolo-palatal
POINT and "broke" the ledger; entered as the coronals + palatalized, the way Russian's soft series
already is, Polish is free. Ask which analysis THIS system's rules imply before drafting.

The procedure:
1. Draft `data/languages/<code>.yaml`. Allophones go in `note`, never as entries — points come from
   contrastive units only. Use the modifier series (`long_series`, `secondary_series`, `mod:`) rather
   than spelling out derived forms.
2. `python3 scripts/lang_delta.py --add <file>` — a dry-run in a temp mirror; `data/` is untouched.
   **COVERAGE** = a subset (free) · **WITNESS** = it forces a point, a modifier or a lock ·
   **BREAKS** = a merged contrast or a ledger fold that no longer holds, i.e. a decision to make.
3. If it BREAKS, do not "fix" it by deleting a phoneme — either the analysis is wrong (see above) or
   the grid is too coarse and wants a new feature or modifier.
4. `diaphone --strict` and `pytest`, then the ports (`make -C mac check`, `node scripts/check_js.mjs`)
   and the page.
5. Record it in "Witness and coverage languages" with what it earns — and record the reservation too
   if the call was arguable. A decision with its objection written next to it does not get relitigated.

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
  Korean contrasts fortis vs aspirated (/t͈/~/tʰ/). So: fortis ≈ long, but fortis ≠ aspirated.

## Witness and coverage languages
The 12 core languages are the notation's target. **TR ET VI KO TA KA** are *witnesses* — significant
languages that phonemically contrast a near-merge pair, forcing the point to stay distinct
(Tamil forces the `retroflex` LAYER — ʈ~t̪ eṭṭu/ettu, ɳ~n maṇam/manam, ɭ~l~ɻ vaḷi/vali/vaḻi;
**Czech forces the one new manner value**, see below; Estonian + Vietnamese lock `o`~`ɤ` JOINTLY,
neither alone). Audited with `lang_delta --drop`, and one entry there is wrong in a way worth
keeping visible: **Turkish is credited with locking `u`~`ɯ` (kul/kıl), but the mechanical lock is
JAPANESE** — JA's /w/ is a nonsyllabic *rounded* close back vowel (the /u/ point) while う is /ɯ/,
so JA carries both points and the pair can never merge. Turkish's contrast is the witness-principle
justification; Japanese is what makes it unmergeable. **ID FI HE FA NL UK PL TH RO CS HI BN PT SW** are
*coverage* languages — their inventories are subsets of the existing points + modifiers (folds:
FI/FA æ→a, FA ɒ→ɑ, HE ʁ→ɣ, UK г entered as ɣ, PL ʑ→ʒ), added to grow the covering claim at zero
structural cost. **Polish** is the three-way sibilant test: s ~ sz [ʂ] ~ ś [ɕ] = `s` ~ `sjx` ~ `sj`,
the retroflex LAYER doing the work. **Thai** brings five tones (digits 1-5) and a three-way stop
series via the existing `aspirated`.

**Georgian — the ejective witness, absorbed by the exotic ladder.** The three-way stops are
voiced / aspirated / EJECTIVE; the aspirated series is the BARE voiceless point (exactly as
English p t k, which are [pʰ tʰ kʰ]) and the ejective is the language's exotic: tʼ = `ty`, kʼ =
`ky`, tsʼ = `tcy`, tʃʼ = `tqy`. No language pairs an ejective with θ / tʰ / pf on one base, so the
slots never clash — but `ky` and `tqy` became OVERLOADED (they printed kʰ / tʃʰ as sole tenants
until KA, an *invisible* default that went stale), which is what the STATED-DEFAULT rule fixed:
kʰ / tʃʰ stay the declared defaults, kʼ / tʃʼ are registry overrides. `ejective` joins the
modifiers as a data-honest name riding the exotic letter — zero new notation. The uvular ყ is ejective-only [qʼ] with no plain q, so it is the BARE `kq`
point (slot principle). KA counts as a WITNESS: it forces the modifier, though no glyph or letter.

**Swahili — the first Niger-Congo language, and the slot principle's cleanest win.** The famous
implosives are NOT contrastive ([ɓ ɗ ʄ ɠ] ~ [b d dʒ ɡ] in free variation), so they are the plain
voiced stops with the realisation in `note` — the Vietnamese đ call. Prenasalised mb nd nj ng
follow the majority analysis as CLUSTERS. The Arabic-loan θ ð land on the SAME exotic slots
English and Arabic use (`ty dy` — Swahili spells them th dh!), ɣ x on the velar points, ɟ (j,
usually [ʄ]) on the palatal stop `dj`, ŋ (ng') on `ny`. Zero new structure; 31 languages.

**Bengali and Portuguese — two more of the largest languages, free.** Bengali reuses everything
Hindi established (the four-way series on `aspirated`, the retroflex layer) with no retroflex nasal
and ʃ as the ordinary sibilant; Portuguese needs nothing new at all — ɲ ʎ are the palatalized
coronals, ʁ folds to ɣ, and [tʃ dʒ] before /i/ plus unstressed [ɐ] are allophones, in `note`.
**A near-miss worth keeping**: the first Bengali draft entered অ্যা as the NEAR-OPEN /æ/ and broke
the ledger's `æ→a` fold — which CLAUDE.md records as "merged, NO witness". Checking first: the
source gives no minimal pair, notes /æ/ "never occurs outside of the initial syllable", and writes
the nasal as "/æ̃~ɛ̃/". Bengali contrasts that vowel with both /e/ and /a/, and our e ~ ɛ ~ a covers
that three-way exactly, so it is the OPEN-MID FRONT point and the fold is never tested. Second time
a wrong-analysis draft produced a confident BREAKS (see Polish); ask what the rules imply first.

**Hindi-Urdu — the four-way stop series, at no cost.** p / pʰ / b / bʱ at five places. The fourth
is BREATHY VOICED (murmured), phonetically a different phonation from aspiration — but VOICING
already separates it from the aspirated series and **no language contrasts [bʰ] with [bʱ]**, so it
takes the `aspirated` slot on the voiced points: `p py b by`. Traditional grammars call the series
"voiced aspirates" for exactly that reason. The same reuse as Korean fortis on `long` and Czech ř on
`rj`. Retroflexion is the existing LAYER — ʈ ɖ ɳ = `tx dx nx`, ɽ = `rx` (the slot Tamil ழ uses;
flap vs approximant, contrasted nowhere) — and **Hindi is the first language with TWO modifiers on
one phoneme**: ʈʰ = `txy`, retroflex then aspirated. That surfaced two silent bugs, both fixed:
the loader's series builders REPLACED the source's own modifiers instead of unioning them (so ʈʰ
landed on the plain t point and collided with dental t̪ʰ), and `uni._below_taken` did not count the
retroflex tail, so the aspiration stacked a second mark underneath it.

**Czech ř — reviewed twice, and it costs NOTHING.** /r̝/ is a trill and a non-sibilant fricative
pronounced *simultaneously*, contrasting with r, with ʒ, and with both sequences: **řád** ~ **rád** ~
**žrát** ~ **ržát**. It is not a cluster. But phonemically Czech needs exactly ONE more rhotic than
plain r, and `rj` — the modified r — is free in Czech, which has no soft r. So ř takes it, and
`rj` reads as THE MODIFIED R: [rʲ] in RU/UK, [r̝] in CS, with nothing anywhere contrasting the two.
This is the same reuse as **Korean fortis on `long`** ("fortis ≈ length — no language contrasts
them, so `long` is free"): a modifier slot standing in for a different gesture where no contrast is
at stake. The first attempt gave ř its own manner value `fricative-trill` and the point `rq` (glyph
r͈) — phonetically exact, and rejected on review because it bought no contrast anywhere and the
phonetics is not what this system encodes. The IPA target prints rʲ for Czech ř, exactly as it
prints length for Korean fortis; the phonetics lives in the `note`.

See the near-merge verdicts below.

## Current state
58 fine-grained points → **45 general** (28 C · 17 V) after 13 merges, 0 merged contrasts, 1068
phoneme records, 32 languages (12 core + 6 witnesses + 14 coverage), 10 modifiers. **Every point is a base or base + ONE
operator** — no 2-operator points, no bi-vowels. NOT points (allophones or otherwise excluded):
`ç` (German ich-laut, an allophone of `x`), `ɸ` (Japanese *fu*, allophone of `h`), `ɐ` (German
`-er`), **Mandarin j/q/x `[tɕ tɕʰ ɕ]`** (allophones of the retroflex series), and **`ʌ`**
(= schwa: English STRUT = stressed `/ə/`, Korean ㅓ ≈ schwa).
**The palatal coronals are not points either**: `/c ɟ ɲ ʎ/` **are** `/t d n l/` + `palatalized`
(the fifth invariant). No language contrasts Hungarian *ty* with Russian *ть*, or Spanish *ñ* with
Russian *нь* — the difference (a palatal closure vs a coronal closure with a palatal raise) is
PHONETIC, and this system is phonemic. So HU ty = RU ть = `tj`, ES ñ = IT gn = RU нь = `nj`,
ES ll = IT gl = `lj`, and the soft coronals lose their doubled labels. Likewise Tamil ஷ is the hush
point `sj`, not a retroflex one — the ledger already folds `ʂ`→`ʃ` for RU ш and ZH sh. Vietnamese `ă` reads as short `/a/`.
**Glides are phonemes but not points**: /j w ɥ ɰ/ = close-vowel point + the `nonsyllabic`
modifier (labels `ix ux icx ucx`) — added only where contrastive (EN DE ES FR LA RU AR HU JA KO TR
ET VI TA; ES `ix` carries the yeísmo ⟨y⟩/⟨ll⟩; LA ⟨qu⟩/⟨ngu⟩ are k+w/g+w clusters, so quī=`kuxiw` ~
cui=`kuix` — no labialised modifier exists; IT/EL diphthong glides are allophonic, ZH medials
stay vowels). Syllabicity contrasts
(RU мой~мои, HU haj~hazai) are thereby protected by the invariant.

## Notation (locked, round-tripped)
`data/labels.yaml` gives one label per general point; `labeler.py` validates it, `out/labels.json`
regenerates it. **Every point is a base or base + ONE operator** — no tier, no case, no diacritics.
- **Bases** `p b t d k g m n f v s z l h`, the trill `r` (the common rhotic; tap `ɾ`=`rc`), and 5
  vowel letters `a e i o u`. `y` is not a base (it is the modifier letter; schwa is `ax`); the
  glides /j w ɥ ɰ/ are written `ix ux icx ucx` (close vowel + nonsyllabic `x`), never base letters —
  a base `j`/`w` would make every `Cj`/`Cw` label re-read as a sequence.
- **One mechanism — SIX operators `c j q x w y`, all base-dependent.** (`h` is NOT an operator: it is
  only the /h/ phoneme base — the modifier-letter law.) Four (`c j q x`) can form new points; the rule
  per case: *base+letter is that point if it exists, otherwise the letter reads as the modifier*
  (`sj`=/ʃ/ point vs `pj`=/pʲ/ modifier). `w y` only ever ride
  as modifiers (`y` = aspirated on a consonant / nasal on a vowel; doubled `yy` = emphatic).
- **Consonant operators** (never a bare label): `c`=affricate (`tc`=/t͡s/) · `q`=hush **affricate**
  (`tq`=/t͡ʃ/) · `x`=dental/velar (`tx`=/θ/, `kx`=/x/) · `j`=palatal — the hush points where
  base+`j` is one (`sj`=/ʃ/, `zj`=/ʒ/), the soft consonant everywhere else (`tj`=HU ty = RU ть) ·
  `w`=long (`tw`=/tː/, geminate/long trill `rw`). **`q` composes literally only on VOWELS** (`iq`=ʏ is
  `ic` rounded then lowered, and its glyph wears both marks). On a consonant it is the fourth
  operator, base-dependent like the rest — hush on t/d, uvular on k, the glottal stop on h.
  "Affricate+palatal" is why the LETTER was chosen for the hush series, not a rule: `tq`=/tʃ/ is a
  POINT, while `tc`+palatalized is `tcj`=/tsʲ/ — a different sound, and Ukrainian contrasts them
  (ч ~ ць). That the two share a recipe is exactly why their GLYPHS collide and `tcj` draws c͈.
  **The r base is REGULAR**: `rc`=/ɾ/ the tap (`c` → the dot ṛ, as `c`/`x` draw everywhere) and
  `rj`=/rʲ/ the soft r (`j` → the comma r̦, as `j` draws everywhere) — every mark on r is regular,
  **nothing doubled**. (The marks are SLOTS, not sounds: `rx` reads ɻ~ɽ, `rj` reads rʲ~r̝, and
  r̈ is the rhotic schwa `aq`, not an r point — never present this family as "five sounds".) The soft r is a
  plain member of the soft series (k̦ b̦ m̦ r̦). What `c` MEANS is base-dependent like every
  operator (affricate on t/d, the second rhotic on r); the MARK it draws never is.
  **Gutturals**: the WHOLE block sits on `h` — `h` · `hx`=/ħ/ (`x`=the fricative ONE STEP BACK,
  x's meaning everywhere: `tx`=θ, `kx`=x) · `hj`=/ʕ/ (`j`=the marked second guttural) ·
  `hq`=/ʔ/. Glyphs `h · ḥ · h̦ · '` — the bare letter h with below-marks, no stroked letter; the
  schwa is ạ. **/ʔ/ is the apostrophe `'`**: `q`=`c+j` composes BOTH marks where it can (`iq`=ụ̈),
  but on h the dot is already ḥ, two below marks never stack, and nothing sits above a tall letter —
  so `hq` has no glyph the grammar can build and takes a whole character, as `c`=/ts/, `x`=/dz/,
  `q`=/q/ take letters. **Which SOUND gets it is decided by precedent**, because a whole character
  has no shape the grammar could derive (this is what made the earlier `y` indefensible): it goes to
  the glottal stop — `'` in Hawaiian, Samoan, Tongan and Māori (the ʻokina), across Mayan, in Tagalog
  and Guaraní, and hamza in ASCII Arabic — which is also the commoner sound, /ʔ/ in five of the 23
  languages against one for /ʕ/. U+0027 is the only candidate every font and keyboard has: 40/40
  scanned fonts, against 27/40 for ʼ U+02BC and 18/40 for ʿ U+02BF. Knowingly accepted: it is
  punctuation, not a letter, so a word-break splits it and some editors autocorrect it to ’.
  **THE MARK ALWAYS FOLLOWS THE OPERATOR**, on every base without exception: `c`/`x` draw the dot,
  `j` draws the comma. So ḥ=/ħ/ (`hx`) and h̦=/ʕ/ (`hj`) — the one comma in the view on a sound that
  is not palatal, and it is there because `j` put it there. What an operator MEANS is base-dependent
  (affricate on t/d, the tap on r; `j` is palatal everywhere but h); what it DRAWS never is. ḥ is
  also how the world already writes Arabic ح (Muḥammad).
  Aspiration is single
  `y` (`py ty ky`=/pʰ tʰ kʰ/ — a reading of the exotic slot, so its glyph is the exotic DOT: ṭ below,
  ṗ k̇ above where the descender or a taken below-slot forces it). In a stack the dot rides above,
  which lets a doubly-modified segment wear one mark on each side: Hindi ʈʰ = `txy` = ṫ̖, retroflex
  below, aspiration above. The two dots belong to the VOWEL FLIP (ü ö ï ë ä) and the vocalic r̈
  alone. The Arabic emphatics ride the exotic slots (`sˤ`=`sy` ṣ · `tˤ`=`tx` t̖ — see THE EXOTIC LADDER).
- **Vowels** (17, triangular — see `docs/index.html`): 5 cardinal bases `a e i o u` on the
  triangle edges; operators `c`=toggle-rounding (front gains: `ic`=y `ec`=ø; back loses: `uc`=ɯ `oc`=ɤ;
  apex marks back: `ac`=ɑ), `j`=**lower one step, uniformly** — each in-between vowel is its higher
  neighbour lowered (`ij`=ɪ `ej`=ɛ `uj`=ʊ `oj`=ɔ); `a` is already lowest so `aj` is unused. So ɔ is
  o-based (the lowered o). `q`=`c+j` front-round lowered (`iq`=ʏ `eq`=œ — French œ / German ʏ keep it),
  `x`=REDUCE (`ax`=ə — the reduced vowel, which also carries English STRUT ʌ / Korean ㅓ; on the
  close vowels it rides as the nonsyllabic modifier instead → the glides `ix ux icx ucx` =
  /j w ɥ ɰ/, uni glyphs j w j̈ ẅ — the flip mark rides along). Every vowel is base+1op.
  **ɒ = ɑ** (`ac`): only HU has /ɒ/, open back, adjacent to /ɑ/ — so **HU á/a = `a`/`ac`**, a clean
  c-pair, and the ear keeps /ɔ/ (`oj`) for the languages that have it (DE EN FR IT VI). **œ~ø and ʏ~y
  are distinct points** — French *jeûne/jeune* (no vowel length to recover) and German ü/ö contrast
  them; the injectivity check enforces it.
- **Modifiers ride on top**: long `w`; **aspirated `y`** on a consonant (`py ty ky tcy tqy` =
  /pʰ tʰ kʰ tsʰ tʃʰ/ — `y` has no phoneme twin, so `Cy` never re-reads, and `Ch` is the sequence
  /C/+/h/); **nasal `y`** on a vowel (`ay`=/ã/; French is 3-way /ẽ ã õ/, œ̃ merges);
  **pharyngealised** on the exotic slots (`sy zy` ṣ ẓ; `tx dx` t̖ d̖ where θ ð hold the y-slots —
  AR-only); **nonsyllabic `x`** on the close vowels (the glides — see the vowel bullet);
  rhotic **`q`** on the schwa (`aq`=/ɝ/ — an irregular short label, ax+q with the x elided;
  `q` is inert on a central vowel, so no trill overlap); palatalised `j` (`pj kj bj`…), falling to
  the exotic `y` on s z tc per **THE EXOTIC LADDER** below. There is NO labialised modifier: Latin
  ⟨qu⟩/⟨ngu⟩ are k+w/g+w clusters via the glides (quī=`kuxiw` ~ cui=`kuix`, distinct sequences —
  bare `ku` would read /k/+/u/, which is exactly what cui is). See the notation invariant.
- **THE EXOTIC LADDER (Sz) — no letter ever doubles, no mark ever doubles.** Frequent, widespread
  phenomena have dedicated notation; a rare, language-specific quality rides an EXOTIC SLOT whose
  reading the language defines. `y` is the first exotic letter (glyph: ONE DOT — ṭ ḍ ṇ ṗ ṣ ẓ; side
  below, above on descenders or where a point owns the below form: ṗ k̇ ċ̦ g̣); `x` is the second
  (glyph: the ANTI-COMMA — t̖ d̖ n̖ …), used only where a language stacks TWO specials on one base.
  They are NOT a progression — where both appear they are different phenomena (AR θ=ty ~ tˤ=tx;
  HI t̪ʰ=ty ~ ʈ=tx ~ ʈʰ=txy). A slot may read differently per language but may NEVER carry two
  sounds within one language (`find_shared_labels` proves it; crimes fail --strict). The
  cross-language overloads are THE EXOTIC REGISTRY, printed by the CLI and on the page with each
  language's precise IPA — currently 10 slots, e.g. `ty` = θ (AR EL EN ES SW) ~ tʰ (BN HI KO TH VI ZH),
  `py` = pf (DE) ~ pʰ, `sy` = sʲ (ET RU UK) ~ sˤ (AR: ṣ, the scholarly mark exactly).
  Mechanics (`notation.modifier_letter`): a modifier spells its own letter; where its slot is
  occupied AND sharing would collide within a language, it falls down the ladder —
  palatalized j→y on s z tc (RU has both ʃ and sʲ), pharyngealized y→x on t d (AR has both θ and
  tˤ). Sharing is otherwise deliberate: aspiration stays `y` although ty is the θ point, because
  no language has both /tʰ/ and /θ/ — verified, with the fallbacks' forcedness, by
  `test_exotic_fallbacks_are_forced_and_shares_are_safe`.
  **Every exotic slot has a STATED DEFAULT reading (Sz)** — a slot shown in the consonant table
  already implies an IPA by its cell position, so the value is declared, never hedged: it claims
  default-ness, not universality, and it never moves when a language is added (an INVISIBLE
  default is what went stale — ky printed kʰ as if universal until Georgian brought kʼ). The
  `exotic` modifier's defaults are data (`labels.yaml exotic_defaults`: ty=θ dy=ð ny=ŋ py=pf —
  a missing entry fails loudly); every other shared label defaults to its PRIMARY composition,
  decided by the label grammar itself in `render.ipa_labels`: a modifier spelling its own letter
  beats one that arrived by ladder fallback (tx=ʈ over AR tˤ; sy=sˤ over the fallen soft sʲ),
  then exotic > aspirated/retroflex > pharyngealized > ejective (ky=kʰ over KA kʼ). Voiced
  aspirates print murmured (by=bʱ). The registry lists every per-language override and stays
  the per-language authority; the page states the default on the dotted tiles and in the
  registry table. θ ð ŋ pf are NOT points: they are t d n p + the `exotic`
  modifier in the data itself (features carry the SLOT, the phonetics lives in `note` — the ř/ś
  pattern), which is what freed single-x retroflex: ʈ ɖ ɳ = tx dx nx. **Modifiers (retroflex,
  aspiration, …) never enter the points table** — only the four exotic tiles appear, dotted, at
  the cells their defaults imply.
- Validated: all **1068** phoneme records get a distinct label per language, **0 collisions**, and
  **no label decomposes** — every one is base or base + operators.

## Why soft s z fall to the exotic slot, and why the tap is a point
Two questions that look alike and are not.

**The exotic fallback on s z.** The palatal slots `sj zj` are the hush points, held there by a
**WITNESS** — the strongest kind, a same-language phonemic contrast. Russian has ш and сь
(**сесть** /sʲestʲ/ 'sit down' ~ **шесть** /ʂestʲ/ 'six', a minimal pair) and ж and зь (**жевать**
'chew' ~ **зевать** 'yawn'); UK and ET repeat the s case. Re-reading /ʃ/ as /s/+palatalized would
merge a contrast in three languages — that breaks the FIRST invariant, not merely the fifth. So the
soft s z ARE the exotic s z of those languages: `sy zy`, ṣ ẓ — the same slots Arabic's ṣād and ẓāʾ
read as emphatics, with no language holding both readings. (The fifth's finder never compares
ʃ to sʲ: palatalization relocates a coronal to PALATAL, and there is no palatal fricative point —
German ç is an allophone of /x/ — while /ʃ/ is postalveolar, which no modifier reaches.)

**The tap `rc` and the soft r `rj` are two points-worth of different, not one — REVIEWED AND KEPT.**
Nothing in the 23 contrasts them (RU/UK have рь and no tap; ES/JA/TR/TA have the tap and no soft
series), so merging them passes every invariant and costs no points — it was tested. The soft r is
also genuinely marked: /rʲ/ is *"far more marked than other palatalized coronals"*, and Russian's is
"apical, palatalized, usually only a single vibration, presumably due to the palatalization", i.e.
phonetically a palatalized TAP. That is the case FOR merging, and it is not enough:
- **The palatal merge united two descriptions of one category; this would unite two categories.**
  /c/ and /nʲ/-style pairs are both "coronal with a palatal quality" — neither description becomes
  false. The Spanish tap has NO palatalization and Russian ряд has it; one description would.
- **The two languages contrast along DIFFERENT AXES, and the notation has to be able to say which.**
  Spanish opposes trill~tap, a MANNER contrast (*perro*~*pero*). Russian opposes hard~soft, a
  PALATALIZATION contrast (**рад** /rat/ 'glad' ~ **ряд** /rʲat/ 'row' — the pair is in the IPA's own
  Illustration of Russian, Yanushevskaya & Bunčić, JIPA 45(2), whose Trill row lists /r/ and /rʲ/ as
  separate phonemes). Merge the two marked members and both languages get the same two-way rhotic
  contrast, which is false about both.
- **Russian's soft series is one rule over fourteen consonants**
  (`palatalized applies_to [p b t d k g f v s z m n l r]`); рад/ряд is the same pair type as
  сад/сядь. Pulling `р` out would be the special case, and the palatalization it drops is exactly
  what makes рь pattern with the other thirteen (same soft-series vowel allophony, same morphology).
  (That soft р is *usually realised* as [ɾʲ] is a realisation, the same class of fact as Mandarin
  sh = [ɕ] before /i/ — realisations never set points, and this system is phonemic.)
- **The sound is real, not a Slavic spelling convenience**: /rʲ/ is phonemic in Russian, Ukrainian,
  Lithuanian, Bulgarian and Irish, and Marshallese contrasts three rhotics (/rʲ/ ~ /rˠ/ ~ /rʷ/).
  Its rarity is a fact about how hard it is to trill and palatalize at once, not about whether it
  exists.

Because they stay distinct, the tap takes `rc` and the soft r takes `rj` — `j` keeps its palatal
meaning on r, the comma-count matches the j-count, and nothing on r doubles in either the label or
the glyph. See "The r base is REGULAR" above.

## Allophone guard (suspicious co-occurrences)
The near-merge finder only flags pairs that *don't* co-occur, so it is blind to allophones
entered as phonemes (which co-occur with their parent). `derive()` also returns
**suspicious co-occurrences**: rare points (≤2 languages) sitting one place/height step from a
same-language neighbour — the shape of an allophone. Reviewed genuine contrasts live in
`_CONFIRMED_CONTRAST` (derive.py) and are filtered out. The list is **empty** and
`tests/test_invariants.py` asserts it stays so.

## Decision principles (near-merges)
- **The witness principle (Sz):** a pair stays a distinct *point* only if a *significant* language
  phonemically contrasts it; pairs held apart only by a rare/exotic language are merged in the
  general inventory (recoverable by a diacritic if that language is ever added). The merge record
  itself is `merges.LEDGER` — code is the ledger, this file only keeps the principles.
- **KEPT, with witness:** `u`~`ɯ` (Turkish *kul*/*kıl*), `o`~`ɤ` (Estonian õ; Vietnamese ô/ơ),
  `r`~`ɾ` trill~tap (Spanish *perro*/*pero*), `ɑ`~`ɒ` by construction (round is a defining feature).
- **MERGED, exotic-only witness (no mark within the covered languages):** dental~alveolar (Venda), `ʁ`~`ɣ`
  (Tsakhur/Kabardian). A conditional: `f`~`ɸ`
  merges only if a language with phonemic /ɸ/ (e.g. Ewe) is ever added.
- **MERGED, no witness:** `æ`~`a` (adversarial search incl. Danish found no same-length front/central
  contrast), `ɯ`~`ɨ` (every major language has one or the other, the symbols are interchangeable),
  `ʌ`~`ə` (English STRUT = stressed schwa, Korean ㅓ ≈ schwa).
- **The point/modifier boundary (the fifth invariant):** if a relocating modifier already spells a
  point and no language contrasts the two, they are ONE phoneme — the witness principle applied
  across the boundary rather than between two points. This is a *phonemic* system: the articulatory
  difference between /c/ and /tʲ/, or /ɲ/ and /nʲ/, is real and is exactly the kind of detail the
  system does not encode, the same call the ledger already makes for French R ≈ Greek γ. Hence the
  palatal coronals are `tj dj nj lj` and Tamil's ஷ is `sj`. What the principle does NOT reach:
  a manner difference (trill~tap), which no modifier moves — see "Why soft s z fall to the exotic slot".
- **Retroflex is a MODIFIER, never a point — literally, in the data.** There are no retroflex
  POINTS at all: a language that does not contrast retroflexion enters the plain point and realises
  it as it likes (Russian ш, Mandarin sh, Tamil ஷ are all the unmarked hush point `sj`, realised
  [ʂ]); a language that DOES contrast it takes the **retroflex layer** on top. **The single `j` is
  never retroflex** — it is the palatal, always — and the layer is drawn by FLIPPING the comma:
  ș → s̖ (U+0326 → U+0316). So Tamil's ʈ ɳ ɭ ɻ are `tx nx lx rx`, and a three-way sibilant
  language spells the series plain / palatal / palatal+retroflex: Polish s ~ ś `sj` ~ sz `sjx`.
  The only retroflex entry left in the ledger is the APPROXIMANT `ɻ`, which folds (with `ɹ`) into
  the generic **R slot** `r` — because it is a rhotic, not a retroflexed anything. `ʁ` is NOT a
  rhotic merge — Arabic contrasts `ʁ` (ghayn) ~ `r` (rā).
- **No recovery diacritics on consonants:** every consonant-place merge in the ledger is
  `recover=None` — within the 23 languages nothing contrasts dental~alveolar or uvular~velar,
  and retroflex contrasts ride the modifier, so the folds are lossless in practice. Only the
  vowel `centralized` (ɨ→ɯ) carries a recovery mark. `apply_merges()` asserts safety per
  `(target, modifiers, recovery-mark)` per language.
- **The uni view is strictly universal** — one glyph per label, no per-language flavours, both
  universal maps perfectly injective (the invert test enforces it). The single rendering licence
  is the opt-in tone signs: the acute doubles as the long-vowel mark, accepted by whoever opts in
  (see `docs/uni-view.md`). The point inventory itself is never touched by rendering choices.

## Open decisions
- LICENSE not chosen yet (Sz' decides — mirror weCan conventions if relevant).
- Greek is Modern; swap to Ancient if we want to pair it with Latin.
