# Publication plan

The system is complete as a description; this plan takes it live as a
standard with tools around it. Rationale lives in remarks.md; this file
holds the work, its order and its gates. The name is Diafon
(diafon.io), registration pending; the repo, font family, pages and input
methods carry it since 2026-09-11.

## Architecture

Two layers, and the transformation sits at whatever level a platform
offers.

- **Transport form**: the input form, plain ASCII, the canonical stored and
  transmitted text. Lossless by the engine's guarantees (totality, unique
  segmentation), survives every system: search, URLs, SMS, filenames.
- **Script form**: the presentation, composed by the engine or by a font.
- **Stages**: the script form rendered in a language's current orthography
  (data/stages/<code>.yaml). Render-only: a stage never changes what a key
  means, so text typed for one stage reads in all of them.

Every implementation consumes one machine-readable file, docs/spec.json
(scripts/gen_spec.py), and must reproduce its vectors. The Python engine is
the reference.

## The six questions, settled

1. **Plain ASCII representation.** The transport form is it. Two additions
   to write into the description: tone digits are part of the segment, and
   a span marker for mixed text, so a Diafon word inside an English
   sentence can be rendered and nothing else touched. Recommended marker:
   a leading and trailing `|` (`|sjok|`), rendered away; the engine treats
   marker-less text as all-Diafon, which is the mode inside the input
   methods and the playground.
2. **Transform to the font.** Three routes, all from data/script.yaml:
   - the engine (input methods, extension, playground) composes glyphs;
   - **the transport font**: a Diafon font variant whose liga rules compose
     `s j` into ș, `t q y` into c̖, `a w` into á, so typed transport text
     shows the script in any app that lets you pick a font; built by the
     existing baking machinery in fonts/tools/build_font.py from the form
     list in spec.json (longest-first ligature sets mirror the greedy
     tokenizer; the three-keystroke ceiling keeps ligatures at most four
     glyphs with w);
   - fonts embedded on the site and on Google Fonts (OFL).
3. **Language-native representations.** The stages, one file per language,
   validated (every form the language uses is spelled, spellings are
   letters of the stated alphabet, no two forms collide), each with a
   review state like the mapping. Losses are one-way and stated in the
   file. No shortcut ever claims a key: stages are output. Hungarian is the
   model (data/stages/hu.yaml, draft, for Sz's native review).
4. **Settings above the keyboard.** One settings schema shared by every
   input method and the extension, stored as JSON and documented in the
   spec: `output` (script · transport · stage:<code>), `stage`, `strict`
   (reject or pass through ill-formed input; default pass through),
   `tones` (digits · none), `toggle` (the key that flips conversion on and
   off, default a bare Shift tap as in the macOS version), `commit`
   (streaming, the only mode; the rule is stream() in the engine). Same
   labels, same order, same defaults on every platform, so one help page
   serves all.
5. **Input mechanisms.** Desktop first, then Android, no iOS keyboard.
   - macOS: Input Method Kit, already in input_methods/mac, to be reworked
     onto spec.json and the streaming rule (its old engine.json world is
     retired; nothing is reused without Sz's word).
   - Linux: IBus via an m17n `.mim` table generated from spec.json, one
     generator, no native code; fcitx5 reads the same table.
   - Windows: a Text Services Framework text service in Rust, the one
     native build; the engine port is verified against the vectors.
   - Android: an InputMethodService built on an open-source AOSP-derived
     keyboard (HeliBoard or FlorisBoard fork), adding the composing strip
     and the streaming rule; the engine port in Kotlin, verified against
     the vectors. The system keyboard layout stays; no dictionary, no
     prediction.
   - Web: a browser extension (Chrome, Firefox, Safari) transforming in
     editable fields with the JS engine; covers WhatsApp Web, mail, docs.
   - Messengers: a Telegram inline bot and Slack and Discord commands,
     server-side, for phones with no other route.
   - RIME (Weasel, Squirrel, ibus-rime, Trime) is evaluated in one spike
     as a possible single schema for four platforms; adopted only if its
     candidate model can be made to auto-commit per the streaming rule.
6. **Learners and adopters.** A learn page on the site: the 26-key idea,
   the marks, one drill per operator, the per-language table as a printable
   card. An IPA to Diafon converter (mapping.yaml applied to any IPA
   string) for dictionary and Wiktionary integration. A names page: your
   name in Diafon, shareable. Reviewer programme: one credited native
   reviewer per language, the review state public, a reviewer guide derived
   from data/README.md.

## Gates before going live

- G1 Name: Diafon registered (domain, EU and US word mark filed), repo,
  font family, page titles, woff2 and nav renamed in one commit.
- G2 Licences in the repo: spec and data CC BY 4.0, code Apache 2.0,
  fonts OFL with Reserved Font Name, trademark policy page, DCO for
  reviewers.
- G3 Spec frozen at version 1: spec.json carries a version field, the
  vectors are the conformance suite, the description doc states the span
  marker and the settings schema.
- G4 Build in CI: scripts/build.sh on every push, publishing docs/ as the
  site, tests green (engine guarantees, spec vectors, JS parity).
- G5 One language stage native-reviewed (hu), one input method shipped on
  a desktop OS against the streaming rule, the transport font released.

## Workstreams and their tests

| # | Deliverable | Test |
|---|---|---|
| 1 | docs/spec.json, versioned | tests/test_spec.py: vectors reproduce; invalid inputs rejected; streaming monotone and complete over every form pair |
| 2 | Streaming commit rule in the engine | test_streaming; the published traces |
| 3 | Stages: hu native, then en zh (the reviewed languages) | stages.validate per stage; stage vectors |
| 4 | Transport font (liga variant) | shaping test with uharfbuzz: every render vector shapes to the same glyph sequence as the engine's script form |
| 5 | Span marker and settings schema in the description | vectors for mixed text |
| 6 | macOS IM rebuilt on spec.json | its engine port replays all vectors byte-identically, batch and streamed |
| 7 | m17n table for IBus and fcitx5 | ibus-engine replays vectors via a driver |
| 8 | Browser extension | JS engine is the playground's; parity test already holds it |
| 9 | Android IME (input_methods/android) | tests/test_kotlin.py: the Kotlin port replays all vectors on the JVM; the Gradle build checks the service and views; a device pass of README's keystroke table |
| 10 | Windows TSF service | Rust port replays vectors |
| 11 | Learn page, IPA converter, names page | converter round-trips mapping.yaml for every language |
| 12 | Telegram inline bot | vectors through the bot's engine |
| 13 | Licences, trademark policy, reviewer DCO | none; a checklist |

Order: 1 2 3 5 9 (done or in progress here), then 4 6 7 8, then 11 13, then 10 12.

## Done in this pass

- engine.segments(strict) and render(strict): ill-formed input passes
  through leniently, the input-method reading; engine.stream(): the commit
  rule.
- scripts/gen_spec.py → docs/spec.json with 346 render vectors, lenient
  and invalid sets, streaming traces, stage vectors.
- scripts/stages.py and data/stages/hu.yaml (draft): the Hungarian
  spelling stage, validated against the Hungarian table; `sjok sewp njawr`
  renders `sok szép nyár`, `hoswuw` renders `hosszú`.
- tests/test_spec.py: Python and JS engines held to the vectors; streaming
  proven over every form pair; stages validated.
- scripts/build.sh: the build chain plus tests in one command, for CI.
- input_methods/README.md: the machine every input method implements and
  where it hooks in per platform. input_methods/android: the Android IME,
  complete source (service, keys, strip, settings, manifest, Gradle); its
  engine, stages and data (scripts/gen_android.py from spec.json) verified
  against all 454 vectors on the JVM (tests/test_kotlin.py); APK built with
  Gradle and passed a device pass on an API 35 emulator (screenshots in
  input_methods/android/screenshots, driver in tools/demo.sh).

## Decisions Sz takes

- The name: register diafon.io and file the mark, then the rename commit.
- The span marker: `|...|` recommended; alternatives are backticks or a
  leading `\`.
- Licences as listed under G2, or a different split.
- Reuse of the macOS input method's Swift streamer and controller from
  input_methods/mac: recommended to keep the IMK controller shell and port
  the engine fresh from spec.json.
- The Hungarian stage: native review of data/stages/hu.yaml, ly stated as
  the one loss.
