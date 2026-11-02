---
title: Tools
hide:
  - navigation
search:
  exclude: true      # out of the nav and search until reviewed
---

# Tools

Diafon text is ordinary Unicode, so any app can show it and store it. These
tools type it and draw it. All of them are early: they
work, but none is in an app store yet, so each is built from the
[repository](https://github.com/diafon-org/diafon).

## Keyboards

Each keyboard types the Diafon input on the 26 letters and converts as you
type. A sound is written the moment the next key can no longer change it;
only the last sound stays underlined until then.

| Platform | What it does | State |
|---|---|---|
| macOS 13+ | An input method for every app. A Shift tap turns conversion off and on. Mandarin offers the characters of each syllable. Two text Services convert selected text. | Works. [Build and install](https://github.com/diafon-org/diafon/tree/main/input_methods/mac) |
| iOS 16+ | A keyboard with a strip above the keys that shows the sound being typed; no full access and no network. Typing an English or Hungarian word offers the emoji it names. | Tested in the simulator, not yet on a device. [Build](https://github.com/diafon-org/diafon/tree/main/input_methods/ios) |
| Android 8+ | A keyboard on QWERTY, QWERTZ, AZERTY, Dvorak or Colemak, with the digits for tones. The strip above the keys shows the sound being typed. Selected text converts from the text menu. | Builds; next after macOS and iOS. [Build](https://github.com/diafon-org/diafon/tree/main/input_methods/android) |
| Windows | A Text Services Framework service. | Planned, after Android |
| Linux | A table for IBus and fcitx5. | Planned, after Android |

On macOS, after `make install` in `input_methods/mac`, add Diafon under
System Settings → Keyboard → Input Sources, pick it from the input menu and
type `sj tq aw` to get <span class="ug">ș c̦ á</span>.

## Fonts

Diafon Serif, Sans and Mono draw every Diafon letter, with the anchor joined
to its letter. They are built from Noto and free under the SIL Open Font
License. Download the `.ttf` files from the
[fonts folder](https://github.com/diafon-org/diafon/tree/main/fonts).

Other fonts show Diafon too, with the marks placed less precisely. The font
check below shows how any installed font does.

## Check a font

<div class="fontcheck" markdown="0">
  <p class="tryout-help">Every Diafon letter in use, in the font you pick. A red outline
  means the font leaves the mark out; amber means another font steps in.</p>
  <div class="mt-bar fontbar">
    <label>font <select id="fc-font" autocomplete="off">
      <optgroup label="Diafon">
        <option value="Diafon" selected>Diafon Serif</option>
        <option value="Diafon Sans">Diafon Sans</option>
        <option value="Diafon Mono">Diafon Mono</option>
      </optgroup>
      <optgroup label="popular">
        <option>Arial</option>
        <option>Times New Roman</option>
        <option>Georgia</option>
        <option>Verdana</option>
        <option>Helvetica</option>
        <option>Calibri</option>
        <option>Segoe UI</option>
        <option>Roboto</option>
        <option>Noto Serif</option>
        <option>Noto Sans</option>
        <option>Charis SIL</option>
        <option>Gentium Plus</option>
      </optgroup>
      <optgroup label="browser defaults">
        <option value="serif">serif</option>
        <option value="sans-serif">sans-serif</option>
        <option value="monospace">monospace</option>
        <option value="system-ui">system-ui</option>
      </optgroup>
    </select></label>
    <input type="text" id="fc-custom" placeholder="or any installed font" autocomplete="off" spellcheck="false">
    <span class="mt-summary" id="fc-summary"></span>
  </div>
<div class="fc-grid" id="fc-grid"></div>
</div>

## Building your own

Everything that types or shows Diafon reads one file,
[spec.json](spec.json), and must pass its test cases. The
[input methods overview](https://github.com/diafon-org/diafon/tree/main/input_methods)
describes how conversion works on each platform.

<script src="../play-data.js"></script>
<script src="../engine.js"></script>
<script src="../assets/fontcheck.js"></script>
