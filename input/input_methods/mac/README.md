# Diafon for macOS

An input method for macOS 13 and later. Pick it in the input menu and type
the input form in any app; it converts as you type, by the streaming rule:
each segment is inserted the moment the keystroke stream can no longer change
it, and only the undecidable tail shows as underlined text in place. No
compose step and no network.

## Build and install (the Command Line Tools are enough, no Xcode)

    make check     # replay the vectors through the shared core (tests/test_apple.py)
    make install   # build, ad-hoc sign, copy to ~/Library/Input Methods

Then, once: **System Settings → Keyboard → Input Sources → Edit… → +** →
search **Diafon** (listed under English) → Add; or `make enable`, which
enables and selects it from the command line (and disables the old
Diaphone input source if that is still installed). Pick it from the input menu
in the menu bar and type `sy cy aq`: it streams out as `ș c̦ á`.

## What it does

- **Streaming conversion.** Letters, digits, space and punctuation go through
  the streaming rule (`Diafon.stream`): everything before the last letter is
  inserted as final text, the last letter stays underlined until a key settles
  it; in a language's spelling the whole word being typed stays underlined.
  Backspace edits the underlined tail first; Escape drops the tail in as
  typed; Return, Tab, arrows and any shortcut make the tail final and pass
  through.
- **Each output is a keyboard.** Diafon (the script) and one keyboard per
  language written by its letters (Diafon – Magyar, Diafon – Polski, …) are
  input modes of the one input method, so the system's own switching picks
  them: the input menu, the Globe key, ⌃Space. Diafon is on from the start;
  a language becomes a keyboard when it is ticked under Keyboards… in
  Diafon's menu or added in System Settings → Keyboard → Input Sources. The
  two are the same list: the system's. Diafon keeps none of its own
  (`Sources/Keyboards.swift` reads and changes the system's input sources).
  The controller writes what the selected keyboard says, checked each time a
  field is entered. There is no "off": for plain letters, switch to another
  keyboard.
- **The typing.** What the keys mean comes from the compiled profile
  (`../../spec/diafon-v1.json`): `y` and `q` mark the letter before them
  (`sy` ș, `cy` c̦, `oyq` ő), a doubled consonant is long (`ssy` șș), a
  doubled `y` or `q` is the plain letter (`cityy` city), and a digit after a
  letter is its tone (`ni3 kqaw3`), doubled the plain digit (`h22o`).
- **No dictionaries.** The input method carries no word list. A language
  is offered when its spelling is written by its letters alone; English,
  whose spelling is a dictionary, is not, and comes out in the script.
  Mandarin's pinyin is a table of syllables, not a dictionary, and is a
  keyboard (Diafon – Pinyin): `ni3 kqaw3` writes ni3 hao3. The characters
  are not carried. Hungarian is written by its letters: every /j/ is j, and a loan is
  spelled as it sounds.
- **The status menu**, under the input source in the menu bar: Convert
  selection to … and Convert selection…, then Keyboards… (the chooser: every
  language, filtered as you type by native name, English name or code; the
  box beside one makes it a keyboard, Return or a double click also switches
  to it; on the right the keyboards as they are now) and Setup…. Flat by
  necessity: the menu is shown by a system process that returns only
  top-level clicks, so a submenu cannot be picked from.
- **Setup…** opens a window: the keyboard in use (Diafon, or a language's
  spelling, the language in a popup, its sample beside it; a choice here
  switches the keyboard in the system too), the base layout, Try it (a typed
  line in both), the options (tones, joined long consonants) with a line on
  each, and How to. It is set in the Diafon fonts, which the app carries.
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

1. Pick Diafon in the input menu (or ⌃Space). The letters sit as Setup's
   base layout puts them: QWERTY by default, or QWERTZ, AZERTY, Dvorak,
   Colemak, whatever layout the Mac had selected before.
2. Type a letter, then `y` or `q` for its mark: `sy` → ș, `cy` → c̦,
   `aq` → á; the last sound stays underlined until the next key settles it.
3. Switch between Diafon and your language keyboards as between any
   keyboards. Diafon's menu has Keyboards… (which languages are keyboards);
   for plain letters, switch to another keyboard.
4. Text in any spelling: select it, then Diafon menu → Convert selection
   (or right-click → Services → Convert with Diafon); the … variants let
   you set the source and the target first.

## Layout of this project

    ../apple/Core/Diafon.swift         the alphabet and the typing: the site's JavaScript, run in JavaScriptCore
    ../apple/Core/diafon-glue.js       what the apps ask of it, as plain functions
    ../apple/Core/Prefs.swift          the settings (output, language, tones, join) and the renderer
    ../apple/Check/main.swift          stdin/stdout driver used by tests/test_apple.py
    Sources/DiafonInputController.swift  IMKInputController: keystrokes in, streaming rule, insertText / setMarkedText out; the status menu
    Sources/ConvertWindow.swift        the From / To window of Convert with Diafon…
    Sources/Hud.swift                  a small label shown for a moment (nothing selected to convert)
    Sources/Keyboards.swift            the keyboards: the system's input sources read, switched on and off, selected
    Sources/LanguageChooser.swift      the searchable language list (Keyboards…)
    tools/modes.py                     the Info.plist with one input mode per output
    Sources/SetupWindow.swift          the setup window
    Sources/MacPrefs.swift             the base layout under Diafon (overrideKeyboard), from ../apple/Core/Layouts.swift
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
- After `make install` or `make enable`, quit and reopen the apps that were
  running (or log out and in). Both register the input method again, and an
  app that was already running keeps its old list of input sources: when the
  cursor badge then lands on Diafon while keyboards are cycled, Apple's badge
  code looks Diafon up, gets nothing, and the app quits (Teams with exit code
  5 and no report, Notes with `CFRelease() called with NULL` in
  TextInputUIMacHelper). An app started after the install is not affected.
  Switching keyboards on and off (Keyboards…) registers nothing and is safe.
