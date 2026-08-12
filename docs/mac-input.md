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

## UX

- **Composition**: keystrokes accumulate as marked (underlined) text, converted live —
  type `sjok`, see `s̩ok` forming; **space/Enter commits**, Esc reverts to raw notation.
- **Target switching**: a status-bar menu on the input source (native · HU · ZH · EN · IPA),
  plus the two per-language toggles (loose input, loose view) — mirroring the tryout.
- **Digits** pass through as Mandarin tones in ZH mode; punctuation commits and passes through.
- Per-app quirks (password fields, secure input) fall back to raw pass-through automatically —
  IMK handles this.

## Milestones

1. **Export** — `diaphone export-json` (+ a test asserting it round-trips the corpus). ~½ day.
2. **Skeleton** — Xcode project: `.app` bundle with `Info.plist` keys (`InputMethodConnectionName`,
   `TISInputSourceID`, icon), installs to `~/Library/Input Methods`, appears in
   System Settings → Keyboard → Input Sources. The "hello world" of IMK. ~1 day.
3. **Tokenizer.swift + check_swift** — port, then corpus-validate against the CLI. ~1 day.
4. **Composition UX** — marked text, commit/revert, the target menu, tone digits. ~2 days.
5. **Polish** — codesign (Developer ID), notarize, a `make install` for local dev; optional
   candidate window later (shows native + spelling simultaneously, pick with ⇥). ~1–2 days.

## Risks / open questions

- IMK documentation is thin; the working examples are open-source IMEs (e.g. Squirrel/rime,
  macSKK) — read for API shape, take no code.
- Marked-text behaviour differs subtly across apps (Terminal vs TextEdit vs browsers); the
  corpus keeps *conversion* correct, but composition UX needs hand-testing in ~5 apps.
- English real spelling (see `scripts/en_respell_poc.py`): the reverse-CMUdict index (~115k
  pronunciations) is fine to bundle in the app (a few MB); homophone choice needs a frequency
  list. Ship EN letter-respelling first, add dictionary respelling as a later mode.
- Distribution: unsigned input methods are painful to enable; a Developer ID cert is
  effectively required for anyone-else use. Local dev works unsigned with right-click → Open.

## Non-goals (for now)

- iOS: only full custom keyboards are allowed there; a different, bigger project.
- The bespoke font: independent thread; the input method works with Charis SIL or any font
  the receiving app uses.
