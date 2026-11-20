# Split: the alphabet and the input

Status: P0 and P1 done, P2 done in part, on the branch `split` (2026-11-20).
See "P1 as built" and "P2 as built" below.

Diafon today is one system: the typed form is the point's identity. Stages,
lexicons, the spec, the font tools and every port are keyed by input forms
(`sj`, `tq`, `aj`), so no other way of typing can exist without rewriting
everything. This plan detaches the two completely:

- **diafon** (this repo): the alphabet. Points, glyphs, language analyses,
  stages, lexicons, fonts, reading text back. It knows no keyboard: no
  typed form, no operator and no key appears in its data, code, spec, fonts
  or docs.
- **diafon-input** (new repo): ways of typing the alphabet. An engine, input
  profiles, the platform input methods. It owns no sound decisions.

Two profiles at the split:

- `universal-v1`: today's typing, unchanged, all languages.
- `minimal-hu-v1`: Hungarian, English and Mandarin sounds on two operators,
  with an escape for everything else.

## Decisions

1. **The point ID is its canonical IPA value**, frozen at the split:
   - a consonant with several readings: the reading marked `primary` under
     `shares`;
   - a vowel: its area's `core`, or the split value for a split point
     (`areas`);
   - a back-lean point: its reading in the global map, never one from a
     language override (ʂ ʐ tʂ dʐ ʈ ɖ);
   - any other point: its one reading.
   Long points take `ː`, tones are `tone:<contour>`. The generator fails on
   two points with one ID. An ID is a name: it records the value at freeze
   time and is never renamed when a later review moves a primary. So
   `mapping.yaml` may hold lines such as Mandarin ʂ → ʃ; its header says the
   value is a point name.
2. **The text is the script.** The canonical stored form of Diafon text is
   NFC Unicode script. Lexicons, stage samples and hand tables store script
   text; stages, readers and vectors are keyed by point IDs. There is no
   ASCII transport form in the alphabet; the old transport form is
   `universal-v1` typing and lives in the input repo.
3. **A point is a letter and its marks.** `script.yaml` describes a point's
   glyph by its base letter and named marks (anchor, dot, reverse, flip,
   grave, acute), not by the operator that used to type them. The font tools
   read points from it.
4. **script → points is one reading.** No two points share a glyph today
   (226 compositions, all distinct), and the spec tests it. Length is the
   one identification: a doubled consonant letter is the long point, so two
   equal points in a row and the long point are the same text. The joiner
   stays an optional mark of the fused drawing, never of meaning. The reader
   matches a letter with its marks before a doubling (today a plain letter
   before its marked twin is misread).
5. **The alphabet ships a versioned spec, `alphabet-spec.json`.** Semver:
   major for a removed point, a changed glyph or an ID change; minor for an
   added point, language or stage.
6. **A profile is data, compiled to a table.** The engine segments by
   longest match over the profile's compiled key table plus a small set of
   declared rules (gemination, escape, token classes). The `universal-v1`
   grammar is no longer hard-coded.
7. **Profiles are immutable by ID.** A change to `minimal-hu-v1` is
   `minimal-hu-v2`. A profile declares the alphabet major it targets.
8. **The input repo vendors the alphabet spec**: `vendor/alphabet-spec.json`
   with version and sha in `vendor/ALPHABET`, updated by
   `scripts/sync_alphabet.py`. No submodule. The dependency runs one way:
   nothing in diafon refers to diafon-input.
9. **Platform ports of render and read live in the input repo**, because only
   the input methods use them. The alphabet repo keeps the Python reference
   and the JS used by the site, and its vectors bind every port.
10. **Repo names**: `diafon-org/diafon` stays the alphabet (keeps the domain,
    links and history); `diafon-org/diafon-input` is extracted with history.

## Target layout

```
diafon/                          the alphabet
  data/
    points.yaml                  generated: ID, glyph, readings, family
    languages/*.yaml             unchanged: phoneme metadata
    mapping.yaml                 phoneme -> point IDs (was -> input form)
    script.yaml                  point -> letter and marks; tones
    stages/*.yaml                keyed by point ID; new: zh (pinyin)
    lexicon/                     words <-> script text
  scripts/
    script.py                    points <-> glyphs (from engine.py)
    stages.py lexicon.py         parse, convert, detect over points
    gen_master.py gen_points.py gen_spec.py gen_fonts.py gen_site.py ...
  fonts/
  docs/                          diafon.io: letters, reading, languages
  tests/                         spec, script, samples, fonts, no-input

diafon-input/                    the typing
  vendor/alphabet-spec.json, vendor/ALPHABET
  profiles/
    universal-v1.yaml
    minimal-hu-v1.yaml
  engine/                        Python reference: compile, segment, stream
  spec/<profile>.json            per-profile vectors
  layouts.yaml
  input_methods/{apple,mac,ios,android}/
  fonts/transport/               the liga font over universal-v1 typing
  docs/                          input.diafon.io: typing, per profile
  tests/
```

## What moves

| Today | Goes to | Change |
|---|---|---|
| data/languages, mapping.yaml | alphabet | mapping values become point IDs; a sequence (pʰ, aɪ) is a list of them |
| data/script.yaml | alphabet | keyed by point: letter and marks, no operators |
| data/stages, data/lexicon | alphabet | rekeyed; lexicons, samples and hand tables store script text |
| scripts/engine.py `glyph`, `render`, `inventory`, `script_table`, `read` | alphabet `script.py` | points in, not forms |
| scripts/engine.py `segments`, `tokenize`, `stream` | input `engine/` | profile-driven |
| scripts/stages.py, lexicon.py | alphabet | over points |
| scripts/gen_spec.py | split | `alphabet-spec.json` here; profile specs there |
| scripts/gen_fonts.py, fonts/tools/build_font.py | alphabet | read points.yaml, not the form inventory |
| data/learn.yaml, gen_learn.py | split | reading lessons here; typing drills there |
| scripts/gen_play.py | input | the playground types |
| data/layouts.yaml, gen_layouts, gen_android, gen_mac | input | |
| input_methods/ | input | Core reads compiled profiles + alphabet spec |
| tests/test_kotlin, test_swift, test_ios_session | input | |
| data/emoji.json, gen_emoji.py | input | a word chooser is an input feature |
| fonts/ | alphabet | the transport liga build moves to input |
| remarks.md | split | sound and glyph rationale here, key rationale there |
| plan.md workstreams 2, 4, 5, 6, 7, 9, 10, 12, 15, 18 | input | 1, 3, 11 (reading), 16, 17 stay; 13, 14 apply to both |

## The two contracts

**alphabet-spec.json**: `version`; `points` (ID, glyph NFC, caps glyph,
letter and marks, family, readings per language); `tones`; `stages` (read
and write tables keyed by ID); `lexicons` (references); vectors: points →
script, script → points, stage write, stage read, convert, detect. No field
holds a typed form.

**Profile** (input repo): what keys produce which points. Nothing about
sound. Compiles to `spec/<profile>.json`: the key table, the rules, and the
vectors (render, invalid, stream traces, token classes).

## Profile: universal-v1

Today's grammar, defined as data: 20 bases, operators `c j q w x y`,
segment = base, up to two operators, `w` at most once and last, tone digits.
Its compiled table is the old form list mapped to point IDs. Streaming
commit per segment, as now. The `transport` output setting is defined as
this profile's keys, whatever profile is typed with.

Acceptance: every vector of the pre-split spec reproduces byte for byte.

## Profile: minimal-hu-v1

One flavour of typing, nothing more: a key table, two operators and an
escape. No dictionary. Scope: the Hungarian, English and Mandarin sounds.
Targets the alphabet as it is; it adds no points and changes no glyph.

**Bases** (24): `a e i o u p b t d k g f v s z h m n l r` as their points;
`c` → ts, `x` → dz, `j` → j, `w` → w.

**Operators** (2):

| Key | After | Gives |
|---|---|---|
| `y` | s z c x t d n | ʃ ʒ tʃ dʒ c ɟ ɲ (ș z̦ c̦ x̦ ț d̦ n̦) |
| `y` | u o i e | y ø ɯ ɤ (ü ö ï ë) |
| `y` | a | ə (ạ), the one exception to "y on a vowel is the double dot" |
| `y` | r | ɝ (r̈) |
| `q` | t d n | θ ð ŋ (ṭ ḍ ṇ) |
| `q` | any vowel point | its long point: `aq` á, `oyq` ő, `uyq` ű |

**Rules**:

- Gemination: a doubled base is a long consonant, and an operator after it
  applies to both: `ssy` șș, `ccy` c̦c̦, `nny` n̦n̦.
- Escape: a doubled operator is the plain letter: `syy` → `sy`, `tqq` →
  `tq`. This is how everything outside the table is typed: `anyy cityy
  boyy` → any city boy.
- An operator with nothing to apply to is the plain letter, with no escape:
  `you`, `my`, `by`, `quick`.
- Mandarin: a token whose syllables each end in a digit 1–5 (5 neutral, `v`
  for ü) is read as pinyin through the alphabet's zh stage. Any other token
  with digits passes through.
- Commit per segment, as in universal-v1; a token that may still be pinyin
  (letters, then digits) stays composing until its boundary.

Examples: `cyak a joq soq` → c̦ak a jó só; `zhong1guo2` → the zh stage's
reading; `the cityy` → the city.

Acceptance: vectors in all four engines, the escape and the plain-operator
rule among them.

## Phases and gates

**P0, freeze.** Tag `v1-presplit`. Generate goldens: script and every stage
for each spec vector, sample and lexicon entry. The goldens are the oracle
for P1 and P2.

**P1, the alphabet inside this repo.** gen_points.py builds points.yaml from
mapping, script, areas and shares. Rekey stages, lexicons and the font
tools; split engine.py; emit alphabet-spec.json. The reader fix of decision
4. A temporary `universal_v1.py` keeps the build chain working; it is the
only file that knows a typed form, and P2 removes it.
Gate: goldens byte-identical through universal_v1 → points → script; the
one-reading test passes.

**P2, extract diafon-input.** `git filter-repo` for the moved paths;
profile compiler; universal-v1.yaml; ports read compiled profiles and the
vendored alphabet spec. Then delete the moved paths and `universal_v1.py`
here.
Gate: the pre-split vectors pass in Python, JS, Swift and Kotlin; macOS and
iOS input methods pass their device checklists; `tests/test_no_input.py`
passes in diafon: no form list, operator table or key in its data, spec,
scripts or font tools, and no reference to diafon-input.

**P3, minimal-hu-v1.** The zh pinyin stage in the alphabet (alphabet minor
release): the rules move from data/lexicon/zh.yaml, with tone 5 and `v`
added. Then the profile. A `profile` setting on every platform, defaulting
to universal-v1.
Gate: as under the profile above.

**P4, docs and sites.** diafon.io describes the alphabet only; input.diafon.io
describes typing per profile. READMEs rewritten (today's opens with the
operators); remarks.md and plan.md split.

## P1 as built

- **The script**: `data/script.yaml` names 79 short points as a letter and
  marks; `scripts/script.py` composes, writes and reads them; a text is a
  list of tokens. `data/points.yaml` (generated) lists the 97 points in use,
  long ones included, with their readings.
- **Open compositions**: the script allows 113 letter-and-mark compositions,
  the ones the old grammar could type. The 34 that no point names are
  script all the same: they read and write, the spec lists every
  composition with its glyphs (`compositions`, `id` null for these), and `universal-v1` goes on typing them. A profile names them by
  letter and marks until a language uses one and it gets a name.
- **Stages and lexicons**: `data/stages` by point name, lexicons in script
  text; `stages.py`, `lexicon.py` and `mapping.py` work in points.
  `data/mapping.yaml` values are point names, a sequence a list.
- **Fonts**: the glyph matrix and the long consonants come from the script.
  The glyph set is unchanged; no font was rebuilt.
- **The spec**: `docs/alphabet-spec.json`, version 1.0.0-pre.1 (1.0.0 when
  the split is done), with `tests/test_alphabet_spec.py`.
- **The bridge**: `scripts/universal_v1.py` holds the typing grammar and
  the old form-based view of the stages, lexicons and mapping. What still
  thinks in forms reads through it, and all of it leaves in P2 or is
  rewritten in P4: gen_spec, gen_play, gen_learn, gen_emoji, gen_layouts,
  gen_android, gen_mac, gen_site_words, the form columns of gen_master and
  gen_site, docs/engine.js, the ports and their tests. `docs/lexicon/` is
  the lexicons exported in typed forms for the ports and the site's engine.
- **The gate**: `python3 scripts/gen_goldens.py --check` recomputes all
  370,000 frozen rows from their own inputs. All match except 226 that
  follow from decisions here, counted by kind:
  - 212 `doubled`: a word an English lexicon reads with two equal
    consonants in a row (bookcase, k k) comes back typed long (decision 4);
  - 9 `caps`: a word typed with capital operators (`SJ`) is the same text
    as `Sj`, so a lexical stage now finds it;
  - 5 `inside`: a Hungarian stem that ended inside a typed form (hely in
    `heixtx`) used to leave the operator over; a letter is not cut.
  The old spec, the lessons, the playground data, the emoji table and the
  port data regenerate byte for byte (but for the date stamp).

## P2 as built

- **The repository**: `diafon-input`, extracted with history beside this
  checkout (local only, no remote yet). It holds the input methods, the
  layouts, the lessons, the emoji table, the playground, the old spec and
  its tests, and the pre-split goldens.
- **Profiles**: `profiles/universal-v1.yaml` is the old grammar as data: 113
  key sequences, each naming a point or, for the 34 unnamed compositions,
  a letter and marks. It compiles to `spec/universal-v1.json`. The Python
  engine there is driven by that table and by `vendor/alphabet-spec.json`
  alone, and reproduces every typing vector of the pre-split spec byte for
  byte (117 forms, 497 vectors).
- **Vendoring**: `scripts/sync_alphabet.py` copies the spec and the
  lexicons and records version, commit and sha256 in `vendor/ALPHABET`.
- **A deviation, the generators**: the generators that read a language (the
  old spec, the lessons, the emoji table) run this repository's Python
  reference from a checkout beside theirs, at the vendored commit. The
  engine and the ports do not. The alternative is a second Python
  implementation of the stages and lexicons there.
- **Not done, the ports**: Swift, Kotlin and the site's JS still carry the
  universal-v1 grammar in code and read the old spec's tables. They pass
  the pre-split vectors, but they do not yet read compiled profiles. That
  rewrite is needed before `minimal-hu-v1` can run on a device, so it opens
  P3.
- **Not done, the last deletions**: the input-only paths are gone from
  here (input methods, layouts, emoji, their generators and tests, the
  goldens). The site still shows how a point is typed (playground, lessons,
  the master tables' form column), so the bridge and the generators behind
  those pages stay until the site is split: `tests/test_no_input.py` passes
  for everything else and lists those 12 files as pending. P4's work on
  this site therefore comes before the gate of P2 can close.
- Device checklists for macOS and iOS are not run.

## Arguments against

- Two repos double CI, releases and the sync step. A monorepo with two
  packages and an import boundary test gives the same separation for less
  coordination. The split is kept because the input methods ship on their
  own cadence and other profiles may come from other people.
- IPA IDs are awkward in Swift and Kotlin source and easy to corrupt
  (ː against `:`, decomposed marks). Mitigation: IDs are only ever read from
  the spec, never typed in code, and the spec test checks NFC and the
  allowed character set. Frozen v1 forms as IDs would avoid this and the
  rekeying, but they would keep input forms inside the alphabet, which is
  exactly what this plan removes.
- An IPA ID reads as a sound, and a language's phoneme may sit on a point
  named for another (Mandarin ʂ on ʃ).
- `minimal-hu-v1` has no free letter left. Any new point needs a new
  profile.
- English in `minimal-hu-v1` needs the escape wherever `y` or `q` follows a
  letter it applies to (any, city, boy, they).
