# Diafon for iOS

A custom keyboard for iOS 16 and later, with the app that carries it. Like
the Android keyboard it shows the 26 letters on the base layout of your
choice, the digits for tones, a symbols page and a few functional keys. It
converts by the streaming rule and writes the result into whatever field has
focus. Above the keys, the pending segment appears in every spelling, and a
tap writes that one. Select text in any spelling and the strip offers to
convert it. A word typed in English or Hungarian offers the emoji it names
first on the strip (*heart* ❤️, *kutya* 🐶); a tap puts the emoji in the
word's place. That one small table (data/emoji.json, 86 KB) is the
only word list the keyboard carries: no dictionary, no prediction, no
network, no full access.

**State:** the keystroke logic is checked on a Mac. The app and the keyboard
build for iOS, and a UI test types on the keyboard in the simulator (iPhone
17, iOS 26.5) in both tail modes; every case passes. Not yet run on a device
or in other apps.

## How an iOS keyboard works

iOS has no input-method layer; third-party text input is a **keyboard
extension**, a `UIInputViewController` the system loads into the app being
typed in. It gets:

- **its view**, the panel under the text (our strip, keys and settings),
- **`textDocumentProxy`**, a handle into the field: `insertText`,
  `deleteBackward`, `setMarkedText` / `unmarkText` (provisional text, iOS
  13+), `documentContextBeforeInput`, `selectedText`, and the field's
  `returnKeyType` and `autocapitalizationType`,
- **`textDidChange` / `selectionDidChange`**, when the field or the cursor
  changed, by us or by the person,
- **no hardware key events**: with a hardware keyboard attached, iOS
  bypasses extensions. Diafon on an iPad keyboard is not possible.

Extensions run under a tight memory limit (tens of megabytes), and without
**full access** a keyboard has no network and no storage shared with its
app. Diafon needs neither, so it does not ask, and the system shows no
warning when it is turned on. As a result, its settings live in the
keyboard (the gear on the strip, or hold Dia), not in the app.

## The text path, and the device pass that settles it

`Shared/Session.swift` holds the streaming rule against a `TextSink`. It has
no UIKit dependency, so the whole keystroke logic is checked on a Mac. The
editor always shows the render of everything typed, and only the last
segment is provisional. There are two ways to keep that segment provisional,
because iOS apps honour marked text unevenly:

- **marked** (the default): the tail is marked text. `insertText` replaces
  it with the settled head, which is final; then the new tail is marked.
  Text is never made final with `unmarkText`, except for an orphaned tail:
  in the simulator, a setMarkedText, unmarkText, setMarkedText sequence
  garbled the field (`sjok sewp njawr` came out `okk epp ar`).
- **replace**: the tail is plain text the keyboard remembers. The next key
  deletes back only the graphemes that differ and types the rest.

The settings panel switches between them ("Underline the letter being
typed"). A changed field (`textDidChange`, `selectionDidChange`) keeps the
tail only if the text before the cursor still ends with it. Otherwise the
tail is left where it is, final (unmarked first, so the next key cannot
overwrite it).

**Simulator, the app's own field (SwiftUI TextField), 2026-10-02:** both
modes pass items 1 and 3 below and the capitals-and-tones case
(`Sjan1 Tqy` → `Șan1 C̖`). One `deleteBackward` takes `n̦` whole.

To check on a device, per app (Notes, Messages, Safari textarea and
contenteditable, Mail, WhatsApp, Telegram, a search field), in both modes:

1. `sjok sewp njawr` streams to `șok sép n̦ár`; nothing is doubled or dropped.
2. Fast typing (overlapping taps) loses no letter.
3. Backspace after `nj` + `a` leaves `n̦`; one more removes the whole `n̦`
   (one `deleteBackward` must take a letter with its combining mark).
4. Whether `documentContextBeforeInput` includes marked text. If it doesn't,
   marked mode settles a tail on every host callback, and that callback
   needs a different test.
5. Tapping elsewhere mid-segment leaves the tail where it was.
6. Return, the globe and dismissing the keyboard settle the tail.

Record the results here. The outcome decides the default mode, or a
per-app choice if the apps disagree.

## The keyboard, key by key

| Key | Does |
|---|---|
| letters, digits | `Session.type`: the head becomes final, the tail stays provisional; digits are tones |
| ⇧ | next letter capital; double tap locks; on at a sentence start where the field asks |
| ⌫ | edits the tail first, then one grapheme of the field; repeats when held |
| 123 / ABC | the symbols page and back |
| Dia / abc | a tap switches conversion off and back on; quick taps walk off → Universal → each language on the quick list (the Mac's Shift cycle); hold for the settings |
| 🌐 | the system's keyboard list; shown only where the system has no switcher of its own (`needsInputModeSwitchKey`) |
| return | settles the tail, then a newline; labelled by the field's return key type |

Characters are sent on touch down, as on Android. Touches between keys go
to the nearest key. Each key is an accessibility element (VoiceOver reads
it; the UI test taps it by its id, `key:s`, `key:space`, `key:delete`).

## Layout of this project

    project.yml                       the Xcode project as text (XcodeGen); Diafon.xcodeproj is generated
    Makefile                          check, data, project, sim, open
    Shared/Session.swift              the streaming rule against a TextSink; no UIKit
    Shared/KeyboardPrefs.swift        what iOS adds to the shared settings: layout, tail mode, the strip's spellings
    Shared/Layouts.swift              generated from data/layouts.yaml by scripts/gen_layouts.py
    Keyboard/KeyboardViewController.swift  UIInputViewController: proxy ↔ Session, keys, strip, convert selection
    Keyboard/KeyboardView.swift       the keys, drawn in one view; touch down emits; the globe button
    Keyboard/StripView.swift          the spellings of the pending segment, the mode, convert selection, the gear
    Keyboard/SettingsPanel.swift      Universal or a language, layout, tones, strict, tail mode
    Keyboard/Theme.swift              the palette (light and dark), operator tints, Diafon Serif
    App/DiafonApp.swift               the app: setup, try, convert, how-to
    App/Assets.xcassets               the icon (copied from docs/logo/png by `make icon`)
    check/SessionCheck.swift          the Mac check of Session, driven by tests/test_ios_session.py
    UITests/KeyboardTests.swift       the keyboard in a simulator: keys tapped by accessibility id, the field read back

The shared core is `../apple/Core` (SpecData, Engine, Stages, Reading,
Lexicon, Prefs), compiled into the macOS input method as well.

## Build

    make check                         # Command Line Tools only: spec vectors, Session, UIKit typecheck
    brew install xcodegen               # once
    make project TEAM=<your team id>    # Diafon.xcodeproj
    make sim                           # simulator build
    make uitest                        # type on the keyboard in a simulator, both tail modes
    make open                          # Xcode: pick a device, run the Diafon scheme

Running on your own device needs only a free Apple ID as the team, but the
build then has to be re-signed every 7 days. TestFlight and the App Store
need the Apple Developer Program.

Then on the device: Settings → General → Keyboard → Keyboards → Add New
Keyboard… → Diafon, and in a field pick it with the globe or the switcher.

## Not yet

- The device pass above, and the default tail mode it decides.
- The lexicon (English and Mandarin render in the script, as on Android).
  The JSON lexicons are too large to parse inside an extension's memory
  limit. A memory-mapped format generated next to the JSON is the route.
- Mandarin's character choices on the strip.
- A Shortcuts action (App Intent) and a share-sheet action for converting text.
- Key previews on press; haptics (these need full access, so probably never).
- Release: privacy label (Data Not Collected), screenshots, the listing at
  about one dollar (remarks.md, 2026-09-27).
