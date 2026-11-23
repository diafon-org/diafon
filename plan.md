# Plan

Diafon is complete as a description; this plan takes it live as a standard
with tools around it. The work, its order and its gates live here; the
publishing sequence in publish.md; decision rationale in remarks.md.

## Architecture

Two parts in one repository (split.md); the typing reads the alphabet,
never the other way.

- **The alphabet** (everything outside `input/`): the points, each a letter
  with named marks; the languages and the mapping; the stages, which render
  the script in a language's current orthography (data/stages/<code>.yaml);
  the dictionaries; the fonts; the site. The text is the script itself,
  ordinary Unicode. It publishes one machine-readable file,
  docs/alphabet-spec.json (scripts/gen_alphabet_spec.py), whose vectors an
  implementation must reproduce. The Python scripts are the reference;
  docs/assets/diafon-core.js is the same in JavaScript.
- **The typing** (`input/`): one profile, diafon-v1, every letter on a plain
  keyboard with two keys, y and q. Compiled (input/spec/diafon-v1.json) it
  carries its key table and its vectors. In Python (input/engine) and
  JavaScript (input/web/diafon-keys.js).

The rows below from before the split (2026-11-21) name the files and the
typing of that time: spec.json is now the alphabet's spec and the profile's,
and what was built on the old typing sleeps in input/legacy.

## Order (2026-11-02)

macOS and iOS first, the desktop and the mobile tool, until both are
right; then Android, Windows and Linux. The browser extension is removed.

## Gates

- G1 Name: diafon.io registered; the mark claimed with ™ on every surface,
  not filed (publish.md, stage A).
- G2 Licences in the repo: spec and data CC BY 4.0; code GPLv3, AGPLv3
  where the engine is served, with a commercial option; fonts OFL with
  Reserved Font Name Diafon; trademark policy; contributor CLA (not a DCO,
  so dual licensing stays possible).
- G3 Spec frozen at version 1: spec.json carries a version field, the
  vectors are the conformance suite, the description states the span
  marker and the settings schema.
- G4 Build in CI: scripts/build.sh on every push, docs/ published as the
  site, tests green.
- G5 One stage reviewed, one desktop input method shipped,
  the transport font released.
- G6 One /support line on every surface.

## Workstreams

| # | Deliverable | Test | State |
|---|---|---|---|
| 1 | docs/spec.json, versioned | tests/test_spec.py: vectors reproduce, invalid inputs rejected, streaming monotone and complete over every form pair | vectors done, version field open |
| 2 | Streaming commit rule in the engine | streaming traces in the spec | done |
| 3 | Stages: hu fi tr cs pl sw (the orthographies writable per form without context); a stage format with context for es it ro de et id | scripts/stages.py validates each stage; stage vectors | six drafted, native review open; context format open |
| 4 | Transport font: a liga variant that composes typed transport text into the script in any app with a font menu; ligature sets from the form list in spec.json, longest first, mirroring the greedy tokenizer | uharfbuzz shaping: every render vector shapes to the engine's glyph sequence | open |
| 5 | Span marker and settings schema in the description | vectors for mixed text | open |
| 6 | macOS input method, Input Method Kit, on spec.json | tests/test_swift.py replays all vectors | built on the old typing, asleep; rewrite on diafon-v1 and the letters open |
| 7 | m17n table for IBus and fcitx5, generated from spec.json, no native code | ibus-engine replays vectors via a driver | open |
| 8 | Browser extension (Chrome, Firefox, Safari) on docs/engine.js: any page read in Universal, on and off from the icon; then input into editable fields | tests/test_extension.py (content script cases in node; headless Chrome over a sample page) | removed (2026-11-09) |
| 9 | Android input method, input_methods/android | tests/test_kotlin.py replays all vectors on the JVM; Gradle build; device pass of the README's keystroke table | built on the old typing, asleep; rewrite open |
| 10 | Windows Text Services Framework service, Rust | the Rust port replays vectors | open |
| 11 | Learning page (docs/learn.md, scripts/gen_learn.py): per language, the concepts one at a time: the plain letters, each operator in the order the language uses it most, length, the y forms, sequences, tones, capitals; each lesson with the language's own sounds, example words that use only what is already taught, and a typing drill; a printable card of every sound. Then an IPA to Diafon converter for dictionary and Wiktionary use, and a names page | every example word re-reads to its own spelling and uses only the lessons so far (generator); converter round-trips mapping.yaml for every language | lessons on the Input page for diafon-v1, 32 languages (example words for cs en fi hu pl tr zh, native review open); the converter is on the Font page; names page open |
| 12 | Telegram inline bot; Slack and Discord commands | vectors through the bot's engine | open |
| 13 | Licences, trademark policy, contributor CLA | checklist | licences done (LICENSE, LICENSE-docs, fonts/OFL.txt, NOTICE.md); trademark policy and CLA open |
| 14 | /support line on every surface | checklist | open |
| 17 | The lexicon layer: English both ways (CMUdict), Hungarian ly stems and loans in their own sounds (Magyar Ispell), Mandarin pinyin syllables and the character chooser (Unihan); one format, one loader, in Python, JS and Swift; the Mac input method's Mandarin mode | lexicon vectors in the spec; the three ports hold them; the extension reads loans on a Hungarian page | done (draft folding, native review open); Kotlin open |
| 16 | Reading back: parse, convert, detect in the engine, every source to every target, in every port | parse, convert and detect vectors in the spec; Python, JS and Swift hold them | done for Python, JS, Swift; Kotlin open |
| 18 | iOS keyboard extension, input_methods/ios, on the shared Swift core (apple/Core) | tests/test_ios_session.py: Session over every stream trace in both tail modes, a seeded fuzz in every output, a UIKit typecheck; device pass of the README's text-path list | built on the old typing, asleep; rewrite and device pass open |
| 15 | Spike: Keyman (one package for Windows, macOS, Linux, Android, iOS and web) or RIME as a single schema; adopted only if it auto-commits per the streaming rule | replays vectors | open |

Order: 1 3 5 13 14 (the launch), then 4 11 8, then 7 15 10 12.

## Design to write into the description

- Tone digits are part of the segment.
- The span marker for mixed text: a Diafon word inside another language's
  sentence is rendered and nothing else touched. Recommended `|sjok|`,
  rendered away; marker-less text is all-Diafon, the mode inside the input
  methods and the playground.
- The settings schema, one for every platform, stored as JSON: `output`
  (script · transport · stage:<code>), `tones` (digits · none), `strict`
  (flag ill-formed input; default pass through), `enabled` with its toggle
  key (default a bare Shift tap). Same labels, order and defaults
  everywhere, so one help page serves all.

## Open decisions

- The span marker: `|...|`, backticks, or a leading `\`.
- The named owner and the public git identity (publish.md, stage A).
- The donation providers behind /support.
- The legal structure behind payments and donations (remarks, 2026-09-27):
  Syrus Ltd holds the assets and sells (the stores, the paid sync); a
  fiscal host takes donations under the Diafon name; a Diafon foundation
  only when donations outgrow the host's fee, a grant requires one, or an
  adopter needs the standard held by a neutral body, and then the spec,
  the data and the trademark move to it. The accountant confirms the
  Hungarian specifics before the first store listing; the Diafon assets
  stay separated in the Ltd's books meanwhile.
- Review of data/stages/hu.yaml; ly is the one stated loss.
