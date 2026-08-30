# The macOS input method

Goal: type notation in **any Mac app** and get the chosen target — the uni view, a language's
spelling (HU, ZH, EN), or IPA — via a real input method, not a helper app. No jailbreak-style
hacks needed on macOS: **InputMethodKit (IMK)** is the sanctioned mechanism, the same one the
built-in Pinyin and Japanese IMEs use. (latin22 is inspiration for the UX only; no code reuse.)

## Shape of the thing

```
diaphone repo ──(export)──▶ engine.json ──(bundled)──▶ Diaphone.app (input method)
     │                                                   ├─ IMKInputController (Swift)
     └─ scripts/check_swift corpus ◀──(validates)────────┴─ Tokenizer.swift (~120 lines)
```

- **The conversion engine is data, not code.** Greedy longest-match tokenisation over
  label→glyph maps; the per-language assembly rules are data too (`_rules` in the orth files,
  exported as `rules`). `diaphone export-json` emits one `engine.json` (version 2): `maps`
  (uni, ipa), `keys`, `toneSup` (IPA target only — uni keeps plain tone digits), `toneSigns`
  (the opt-in uni tone signs), `orth`, `rules` (the per-language context rules — every port
  interprets them generically), `lazy`, `toneMarks`.
- **Swift side stays tiny.** `mac/Sources/{Decoder,Streamer}.swift` reimplement decode.py
  (tokenise, tone mark placement, gemination) against `engine.json`. Validation = corpus
  replay: `scripts/check_swift.py` (and `scripts/check_js.mjs` for the page engine) replay
  the shared corpus against the Python CLI — a port is only trusted because the corpus says
  outputs are byte-identical.

## UX — seamless streaming, no manual commit

The requirement: conversion happens **before the text hits the target app**, with no separate
commit step and minimal keystroke caching. So this is NOT the classic IME loop (compose →
space/Enter commits a buffer). Instead an **incremental committer**: every glyph is inserted the
instant the keystroke stream can no longer change it; only the undecidable tail is held.

Proven by `scripts/stream_poc.py` — feeding the corpus char-by-char is **byte-identical to the
batch renderer (85/85)**, with these cache bounds:

- **uni / IPA — at most 3 keystrokes held.** A key is held only while the growing string is
  still a prefix of a longer label (`s` may yet become `sj`/`sjj`/`sw`/`sy`; `sjj` is the longest).
  Exception: with tone signs on (uni, opt-in) the open syllable is held until its tone digit
  or a boundary lands — the sign marks an earlier vowel, the same hold the ZH spelling needs.
- **The held tail is visible as underlined raw input, in place.** This is IMK *marked text*
  (`setMarkedText`): the raw tail shows inline at the caret with the standard composition
  underline, and each resolution replaces it via `insertText` — typing `sjok` reads
  s̲ → s̲j̲ → șo̲ → șok̲ → șok. A ZH syllable stays underlined until its tone digit lands
  (t̲q̲o̲n̲x̲1̲ → zhōng). Commitment stays automatic; the underline is pure feedback.
- **HU / EN — one token extra**, for the two next-token rules (HU `i`→j before a vowel; `w`
  doubles the *previous* grapheme, so a consonant can't commit until the next key rules `w` out).
- **ZH — one syllable held** (≤ ~7 keys, e.g. `tqonx1`). Pinyin is the tricky one, irreducibly:
  the tone digit arrives at syllable end but marks an *earlier* vowel (`kxau3` → hǎo), and the
  merged hush series spells j/q/x vs zh/ch/sh by the *following* vowel — so the syllable commits
  as a unit when its digit (or a boundary) lands.

Interaction details:
- **Backspace** while a tail is held edits the raw tail; after commit it deletes committed glyphs
  (no re-conversion of committed text — matching the "converted before it hits the target" model).
- **Escape** flushes the held tail as raw notation (the get-out for typing literal text);
  punctuation and unknown characters flush-and-pass-through.
- **Target switching**: a status-bar menu on the input source (HU · ZH · EN · uni · IPA),
  plus the toggles (loose input; tone signs for uni) — mirroring the tryout.
- Secure input fields: IMK bypasses input methods automatically — raw keystrokes pass through.

## Mode model

Default = **pass-through** (a plain keyboard). The menu selects a conversion mode — HU · ZH ·
EN (respell) · uni · IPA — and a bare Shift tap toggles between it and pass-through. Per-mode
switches: loose input (hu/zh/en typing shortcuts) and tone signs (uni).

## State & remaining work

Working today: the export (`tests/test_export.py` proves a minimal consumer built from
`engine.json` alone reproduces `render()` — every target, strict and loose), the `.app`
skeleton (plain `swiftc` + `mac/Makefile`, no Xcode; `make install` copies to
`~/Library/Input Methods`), and the Swift engine + incremental committer (`make check`
replays the corpus batch AND char-by-char: byte-identical to the Python CLI).

Remaining:
1. **Wiring UX** — insertText per committed glyph, held-tail feedback, backspace/escape rules,
   the target menu, ZH syllable handling. ~2 days.
2. **Polish** — codesign (Developer ID), notarize. ~1–2 days.

## Risks / open questions

- IMK documentation is thin; the working examples are open-source IMEs (e.g. Squirrel/rime,
  macSKK) — read for API shape, take no code.
- Rapid-fire insertText (a glyph every keystroke or two) needs testing across apps
  (Terminal vs TextEdit vs browsers); the corpus keeps *conversion* correct, but the
  insertion cadence needs hand-testing in ~5 apps.
- The PoC's HU/EN committer is conservative (holds up to a word); the Swift version should
  tighten it to one-token-plus-tail (~5 keys). ZH's syllable hold is irreducible.
- Distribution: unsigned input methods are painful to enable; a Developer ID cert is
  effectively required for anyone-else use. Local dev works unsigned with right-click → Open.

## Non-goals (for now)

- **Any dictionary-based mode** — the system is dictionary-free by design; EN is a pure
  pronunciation respelling.
- iOS: only full custom keyboards are allowed there; a different, bigger project.
- The bespoke font: independent thread; the input method works with any font
  the receiving app uses.
