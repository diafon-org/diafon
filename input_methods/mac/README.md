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
search **Diafon** (listed under English) → Add. Pick it from the input menu
in the menu bar and type `sjok sewp njawr`: it streams out as `șok sép ņár`.

## What it does

- **Streaming conversion.** Letters, digits, space and punctuation go through
  `Engine.stream`: everything before the last segment is inserted as final
  text, the last segment stays underlined until a key settles it. Backspace
  edits the underlined tail first; Escape drops the tail in as typed; Return,
  Tab, arrows and any shortcut make the tail final and pass through.
- **A bare Shift tap** flips conversion on and off (settable), so a plain
  English word costs one tap, not a switch of input source.
- **The output**: universal (one letter per sound, the same in every
  language) or a language's spelling.
- **The status menu**, under the input source in the menu bar: what is being
  typed and what comes out, the output switch, Setup.
- **Setup…** opens a window: the outputs with a sample in each, a live pane
  that shows a typed line in every spelling, the toggles.
- **Convert selection.** Text typed with any keyboard, in any app: select it,
  then **Services → Convert with Diafon** (⇧⌘D). Works without switching
  input sources at all.

## Layout of this project

    Sources/SpecData.swift             generated from docs/spec.json by scripts/gen_mac.py: script rules, web letters, stages
    Sources/Engine.swift               the engine, rule for rule from scripts/engine.py: segments, glyph, render, stream
    Sources/Stages.swift               spelling stages, from scripts/stages.py
    Sources/CheckMain.swift            stdin/stdout driver used by tests/test_swift.py
    Sources/Prefs.swift                the settings (output, tones, strict, enabled, shift toggle) and the renderer
    Sources/DiafonInputController.swift  IMKInputController: keystrokes in, streaming rule, insertText / setMarkedText out; the status menu
    Sources/SetupWindow.swift          the setup window
    Sources/Services.swift             the text service
    Sources/main.swift                 IMKServer bootstrap, services registration
    Info.plist                         the input source, the services, the icon (docs/logo/Diafon.icns)

The first three files are pure Swift with no AppKit dependency; that is
deliberate: they compile on their own, so the engine is verified against the
spec vectors before the app is built (`make app` runs the check first).

## Known limits

- Ad-hoc signed: fine on this machine; distribution needs a Developer ID.
