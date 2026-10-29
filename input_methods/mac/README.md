# Diafon for macOS

An input method for macOS 13 and later. Pick it in the input menu and type
the input form in any app; it converts as you type, by the streaming rule:
each segment is inserted the moment the keystroke stream can no longer change
it, and only the undecidable tail shows as underlined text in place. No
compose step, no candidate window, no dictionary, no network.

## Build and install (the Command Line Tools are enough, no Xcode)

    make check     # replay the spec vectors through the Swift engine (tests/test_swift.py)
    make install   # build, ad-hoc sign, copy to ~/Library/Input Methods

Then, once: **System Settings → Keyboard → Input Sources → Edit… → +** →
search **Diafon** (listed under English) → Add; or `make enable`, which
enables and selects it from the command line (and disables the old
Diaphone input source if that is still installed). Pick it from the input menu
in the menu bar and type `sjok sewp njawr`: it streams out as `șok sép ņár`.

## What it does

- **Streaming conversion.** Letters, digits, space and punctuation go through
  `Engine.stream`: everything before the last segment is inserted as final
  text, the last segment stays underlined until a key settles it. Backspace
  edits the underlined tail first; Escape drops the tail in as typed; Return,
  Tab, arrows and any shortcut make the tail final and pass through.
- **Two keys.** A bare Shift tap switches conversion off, and back on to
  the spelling you had; taps in quick succession (within 1.5 s) walk the
  cycle instead, passthrough (a plain keyboard) → Universal → each language
  on the quick list (settable). A small label near the caret names the
  mode for a moment. ⇧Space opens the language chooser, in every mode. A
  plain English word costs a tap, not a switch of input source.
- **Mandarin.** In the Mandarin spelling, letters build a syllable shown as
  pinyin; the tone digit (or a space, for the neutral tone) completes it and
  the candidate window lists its characters, most frequent first, the pinyin
  last. Return or space takes the selection, the next letter takes the first
  choice and starts the next syllable, Escape keeps the pinyin. The
  characters come from data/lexicon/zh.json (Unihan).
- **The candidate window.** While a segment is still underlined, Tab (or ↓)
  opens the system's candidate window, the one the CJK input methods use,
  with that segment in every spelling: the current output first, then
  Universal, each language, and as typed. Arrows pick one, Return takes
  it, Escape closes it; any other key, digits included (they are tones),
  closes it and typing goes on.
- **The output**: Universal (one letter per sound, the same in every
  language; the default) or one language's spelling.
- **The status menu**, under the input source in the menu bar: Passthrough
  (conversion off), Universal, then the quick list of language-specific
  spellings (by their own names and codes: magyar (hu), suomi (fi)…), the
  current choice ticked, and **Other language…** (⇧Space), the chooser
  with every language, filtered as you type by native name, English name or
  code, and on its right the quick list itself: the box beside a language
  puts it there, and Up, Down and Remove order and prune it; that order is
  the menu's and the Shift cycle's. No cap, but past three the chooser warns
  that every Shift tap then has further to go. The language in use is
  always listed, on the quick list or not. Then Setup. Flat by necessity: the menu is shown by a system
  process that returns only top-level clicks, so a submenu cannot be picked
  from.
- **Setup…** opens a window: Universal or Language spelling with the language
  in a popup and its sample beside it, a live pane that shows a typed line
  both ways, the toggles.
- **Convert selection.** Text in any app, any spelling: select it, then in
  the Diafon menu **Convert selection to …** converts it in place, from the
  source detected in the text (your own languages preferred when the text
  reads in several) to the mode in use; **Convert selection…** opens a
  window first: the source, detected and changeable, the target, a
  preview. The same two are text Services, **Convert with Diafon** and
  **Convert with Diafon…**, in the selection's right-click menu under
  Services and in the app menu's Services submenu, which work with any
  input source selected; no key combination, those are taken or shadowed
  app by app (assign one under System Settings → Keyboard → Keyboard
  Shortcuts → Services if you want one).

## How to (also in Setup…)

1. Pick Diafon in the input menu (or ⌃Space). Your keyboard stays as it is.
2. Type sounds as letters, a consonant or vowel plus a mark: `sj` → ș,
   `tq` → c̦, `aw` → á; a segment stays underlined until the next key
   settles it.
3. A bare Shift tap switches conversion off and back on; quick taps in a
   row walk the cycle: passthrough → Universal → each language on your
   quick list. ⇧Space opens the language chooser.
4. Tab (or ↓) on an underlined segment opens the candidate window with
   every spelling.
5. Text in any spelling: select it, then Diafon menu → Convert selection
   (or right-click → Services → Convert with Diafon); the … variants let
   you set the source and the target first.

## Layout of this project

    ../apple/Core/SpecData.swift       generated from docs/spec.json by scripts/gen_mac.py: script rules, marks, stages
    ../apple/Core/Engine.swift         the engine, rule for rule from scripts/engine.py: segments, glyph, render, stream
    ../apple/Core/Stages.swift         spelling stages, from scripts/stages.py
    ../apple/Core/Reading.swift        reading back, from scripts/engine.py and stages.py: inventory, tables, parse, convert, detect
    ../apple/Core/Lexicon.swift        the lexicon layer: English, Hungarian loans, Mandarin syllables
    ../apple/Core/Prefs.swift          the settings (output, language, tones, strict, enabled, shift toggle) and the renderer
    ../apple/Core/CheckMain.swift      stdin/stdout driver used by tests/test_swift.py
    Sources/DiafonInputController.swift  IMKInputController: keystrokes in, streaming rule, insertText / setMarkedText out; the status menu
    Sources/ConvertWindow.swift        the From / To window of Convert with Diafon…
    Sources/Hud.swift                  the mode label shown for a moment after a switch
    Sources/LanguageChooser.swift      the searchable language list (Other language…)
    Sources/SetupWindow.swift          the setup window
    Sources/Services.swift             the text service
    Sources/main.swift                 IMKServer bootstrap, services registration
    Info.plist                         the input source, the services, the app icon (docs/logo/Diafon.icns) and
                                       the input-menu icon (docs/logo/DiafonMenu.tiff, a template the system tints)
                                       and the cursor badge shown on a switch (TISIconLabels → docs/logo/DiafonBadge.pdf,
                                       vector, from docs/logo/icon-badge.svg)
    tools/enable.swift                 enable + select the input source (make enable)

The files in ../apple/Core are pure Swift with no AppKit dependency; that is
deliberate: they compile on their own, so the engine is verified against the
spec vectors before the app is built (`make app` runs the check first), and
the iOS keyboard (../ios) compiles the same files.

## Known limits

- Ad-hoc signed: fine on this machine; distribution needs a Developer ID.
- A second entry in Input Sources (an old Diaphone, or Diafon twice) is a
  stale LaunchServices registration of a bundle built elsewhere. List them
  with `lsregister -dump | grep -E '^path:.*Dia[a-z]*IM'` and drop the
  extras with `lsregister -u <path>` (`lsregister` lives in
  /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/).
  `make install` already unregisters its own build copy.
- Microsoft Teams sometimes quits (exit code 5, no crash report) while input
  sources are being cycled in a chat box. In every case seen so far, Teams
  had just connected to Apple's Pinyin (SCIM), and Diafon was not shown to
  be involved. That is not yet confirmed: Diafon writes nothing to the system
  log. To tell, cycle without Pinyin enabled, or with Diafon off. To read the
  evidence, use `/usr/bin/log` (in zsh a bare `log` is a builtin). runningboardd's
  `termination reported by launchd` gives the exit, and distnoted's
  `inputmethodkit.abnormaldeath ... pid:` lines show which input method the
  app connected to just before.
