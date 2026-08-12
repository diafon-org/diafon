# Plan: native macOS input for diaphone

Goal: type notation in **any Mac app** and get the chosen target — native view, a language's
spelling (HU, ZH, EN), or IPA — via a real input method, not a helper app. No jailbreak-style
hacks needed on macOS: **InputMethodKit (IMK)** is the sanctioned mechanism, the same one the
built-in Pinyin and Japanese IMEs use. (latin22 is inspiration for the UX only; no code reuse.)

## Shape of the thing

```
diaphone repo ──(export)──▶ engine.json ──(bundled)──▶ Diaphone.app (input method)
     │                                                   ├─ IMKInputController (Swift)
     └─ scripts/check_swift corpus ◀──(validates)────────┴─ Tokenizer.swift (~120 lines)
```

- **The conversion engine is data, not code.** The web page already proves it: greedy
  longest-match tokenisation over label→glyph maps, plus three small per-language rules
  (HU i-glide, ZH retroflex split + tone placement, gemination). A new CLI command
  `diaphone export-json` emits one `engine.json`: `nat`, `natHu`, `natZh`, `ipa`, `orth`,
  `lazy`, `zhRetro`, `tone`, `keys` — exactly the payload the page embeds today.
- **Swift side stays tiny.** `Tokenizer.swift` reimplements `decode.py`'s ~80 lines
  (tokenise, tone mark placement, the two glide rules, gemination) against `engine.json`.
  It is validated the same way the JS port is: a `check_swift` runner replays the shared
  corpus (the same words as `scripts/check_js.mjs`) against the Python CLI — the port is
  only trusted because the corpus says outputs are byte-identical.

## UX — seamless streaming, no manual commit

The requirement: conversion happens **before the text hits the target app**, with no separate
commit step and minimal keystroke caching. So this is NOT the classic IME loop (compose →
space/Enter commits a buffer). Instead an **incremental committer**: every glyph is inserted the
instant the keystroke stream can no longer change it; only the undecidable tail is held.

Proven by `scripts/stream_poc.py` — feeding the corpus char-by-char is **byte-identical to the
batch renderer (85/85)**, with these cache bounds:

- **native / IPA — at most 3 keystrokes held.** A key is held only while the growing string is
  still a prefix of a longer label (`s` may yet become `sj`/`sjj`/`sw`/`sy`; `sjj` is the longest).
  The held tail can render as 1–3 chars of marked text purely as feedback — commitment is automatic.
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
- **Target switching**: a status-bar menu on the input source (native · HU · ZH · EN · IPA),
  plus the two per-language toggles (loose input, loose view) — mirroring the tryout.
- Secure input fields: IMK bypasses input methods automatically — raw keystrokes pass through.

## Milestones

1. **Export** — `diaphone export-json` (+ a test asserting it round-trips the corpus). ~½ day.
2. **Skeleton** — Xcode project: `.app` bundle with `Info.plist` keys (`InputMethodConnectionName`,
   `TISInputSourceID`, icon), installs to `~/Library/Input Methods`, appears in
   System Settings → Keyboard → Input Sources. The "hello world" of IMK. ~1 day.
3. **Streamer.swift + check_swift** — port the *incremental committer* (`scripts/stream_poc.py`
   is the reference), then corpus-validate: char-by-char feed must equal the batch CLI. ~1–2 days.
4. **Wiring UX** — insertText per committed glyph, held-tail feedback, backspace/escape rules,
   the target menu, ZH syllable handling. ~2 days.
5. **Polish** — codesign (Developer ID), notarize, a `make install` for local dev. ~1–2 days.

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

- **EN dictionary respelling** — deferred. The reverse-CMUdict PoC (`scripts/en_respell_poc.py`)
  proves it viable (bundle-sized index, needs homophone frequency ranking), but v1 ships the
  letter-respelling; the dictionary mode slots in later as an EN loose-view.
- iOS: only full custom keyboards are allowed there; a different, bigger project.
- The bespoke font: independent thread; the input method works with Charis SIL or any font
  the receiving app uses.
