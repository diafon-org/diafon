---
title: Tools
hide:
  - navigation
---

# Tools

Diafon text is ordinary Unicode, so any app can show it and store it. These
tools type it, show web pages in it and draw it. All of them are early: they
work, but none is in an app store yet, so each is built from the
[repository](https://github.com/diafon-org/diafon).

## Keyboards

Each keyboard types the Diafon input on the 26 letters and converts as you
type. A sound is written the moment the next key can no longer change it;
only the last sound stays underlined until then.

| Platform | What it does | State |
|---|---|---|
| macOS 13+ | An input method for every app. A Shift tap turns conversion off and on. Mandarin offers the characters of each syllable. Two text Services convert selected text. | Works. [Build and install](https://github.com/diafon-org/diafon/tree/main/input_methods/mac) |
| Android 8+ | A keyboard on QWERTY, QWERTZ, AZERTY, Dvorak or Colemak, with the digits for tones. The strip above the keys shows the sound being typed. Selected text converts from the text menu. | Builds. [Build](https://github.com/diafon-org/diafon/tree/main/input_methods/android) |
| iOS 16+ | A keyboard with the same strip, no full access and no network. Typing an English or Hungarian word offers the emoji it names. | Tested in the simulator, not yet on a device. [Build](https://github.com/diafon-org/diafon/tree/main/input_methods/ios) |
| Windows | A Text Services Framework service. | Planned |
| Linux | A table for IBus and fcitx5. | Planned |

On macOS, after `make install` in `input_methods/mac`, add Diafon under
System Settings → Keyboard → Input Sources, pick it from the input menu and
type `sjok sewp njawr` to get <span class="ug">șok sép n̦ár</span>.

## Browser extension

For Chrome, Edge, Brave and Firefox. A click on its icon shows the page in
Diafon, and another click restores it. It finds the page's language by
itself and reads English, Hungarian and Mandarin with their dictionaries.
A word it misreads can be corrected from the right-click menu.

State: works for reading pages. Typing into fields is planned.

To install it in Chrome, open `chrome://extensions`, turn on Developer mode
and load the `extensions/browser` folder. For Firefox, run
`scripts/build.sh` once to make its copy, then open `about:debugging`,
choose This Firefox and load `extensions/firefox/manifest.json`.

## Fonts

Diafon Serif, Sans and Mono draw every Diafon letter, with the anchor joined
to its letter. They are built from Noto and free under the SIL Open Font
License. Download the `.ttf` files from the
[fonts folder](https://github.com/diafon-org/diafon/tree/main/fonts).

Other fonts show Diafon too, with the marks placed less precisely. The font
check on the [Reference](master.md) page shows how any installed font does.

## Building your own

Everything that types or shows Diafon reads one file,
[spec.json](spec.json), and must pass its test cases. The
[input methods overview](https://github.com/diafon-org/diafon/tree/main/input_methods)
describes how conversion works on each platform.
