# Plan

Diafon is complete as a description; this plan takes it live as a standard
with tools around it. The work, its order and its gates live here; the
publishing sequence in publish.md; decision rationale in remarks.md.

## Architecture

Two layers; the transformation sits at whatever level a platform offers.

- **Transport form**: what is typed, plain ASCII, the canonical stored and
  transmitted text. Lossless by the engine's guarantees (totality, unique
  segmentation); survives search, URLs, SMS, filenames.
- **Script form**: what is read, composed by the engine or by a font.
- **Stages**: the script form rendered in a language's current orthography
  (data/stages/<code>.yaml). Render-only: a stage never changes what a key
  means, so text typed for one stage reads in all of them.

Every implementation consumes one machine-readable file, docs/spec.json
(scripts/gen_spec.py), and must reproduce its vectors. The Python engine is
the reference.

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
- G5 One stage native-reviewed (hu), one desktop input method shipped,
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
| 6 | macOS input method, Input Method Kit, on spec.json | tests/test_swift.py replays all vectors | done |
| 7 | m17n table for IBus and fcitx5, generated from spec.json, no native code | ibus-engine replays vectors via a driver | open |
| 8 | Browser extension (Chrome, Firefox, Safari) on the playground's JS engine | the JS parity test | open |
| 9 | Android input method, input_methods/android | tests/test_kotlin.py replays all vectors on the JVM; Gradle build; device pass of the README's keystroke table | done |
| 10 | Windows Text Services Framework service, Rust | the Rust port replays vectors | open |
| 11 | Learn page (the 26-key idea, the marks, one drill per operator, a printable per-language card), IPA to Diafon converter for dictionary and Wiktionary use, names page | converter round-trips mapping.yaml for every language | open |
| 12 | Telegram inline bot; Slack and Discord commands | vectors through the bot's engine | open |
| 13 | Licences, trademark policy, contributor CLA | checklist | open |
| 14 | /support line on every surface | checklist | open |
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
- Native review of data/stages/hu.yaml; ly is the one stated loss.
