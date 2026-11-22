---
title: Font
hide:
  - navigation
---

# Font

Diafon text is ordinary Unicode, so any app can show it and store it. The
Diafon fonts draw it as designed.

## The fonts

Diafon Serif, Sans and Mono draw every Diafon letter, with the anchor joined
to its letter. They are built from Noto and free under the SIL Open Font
License. Download the `.ttf` files from the
[fonts folder](https://github.com/diafon-org/diafon/tree/main/fonts).

Other fonts show Diafon too, with the marks placed less precisely. The font
check further down shows how any installed font does.

## Try a font

<div class="tryfont" markdown="0">
  <div class="mt-bar fontbar">
    <label>font <select id="tf-font" autocomplete="off">
      <option value="Diafon" selected>Diafon Serif</option>
      <option value="Diafon Sans">Diafon Sans</option>
      <option value="Diafon Mono">Diafon Mono</option>
    </select></label>
    <label>size <input type="range" id="tf-size" min="14" max="72" value="30"></label>
  </div>
  <div class="tf-text" id="tf-text" contenteditable="true" spellcheck="false">Ḍạ Nórṭ Wind ạnd ḍạ Sạn wr̈ dispjútiṇ wic̦ wáz ḍạ stróṇr̈. Șok sép n̦ár, hossú alma. Niˇ ḳawˇ, c̦uṇˉkuoˊ. Boṃ veṃ blaṃ.</div>
  <p class="tryout-help">Edit the text, or paste your own from the converter below.</p>
</div>

## Convert a text

Paste a text in a language's usual spelling and read it in Diafon, or the
other way round. It works on long texts. A language's dictionary loads the
first time it is needed.

<div class="convert" markdown="0">
  <div class="mt-bar fontbar">
    <label>from <select id="cv-from" autocomplete="off"></select></label>
    <label>to <select id="cv-to" autocomplete="off"></select></label>
    <button type="button" id="cv-swap" title="swap the two">⇄</button>
    <span class="mt-summary" id="cv-note"></span>
  </div>
  <div class="cv-panes">
    <textarea id="cv-in" spellcheck="false" autocomplete="off" placeholder="paste or type a text"></textarea>
    <div class="cv-out ug" id="cv-out" data-empty="the converted text appears here"></div>
  </div>
  <div class="cv-actions"><button type="button" id="cv-copy">copy the result</button>
    <button type="button" id="cv-show">show it in the font above</button></div>
</div>

## The dictionaries

Most languages are converted by rule, letter by letter. English and
Mandarin cannot be: their spelling does not say the sound, so each has a
dictionary. Hungarian has rules and a dictionary for the words the rules
miss.

<div class="dicts" id="dicts" markdown="0"></div>

## The loanword registry

A word keeps the sound of the language it comes from. *Meeting* is English
wherever it is used, so Diafon writes it one way, <span class="ug">mítiṇ</span>,
in a Hungarian text as in an English one. The registry is the one list
every language consults for such words. It makes one written form out of
many national spellings, and keeps the original pronunciation in view.

<div class="loans" markdown="0">
  <div class="mt-bar fontbar">
    <label>find <input type="text" id="lw-find" placeholder="a word" autocomplete="off" spellcheck="false"></label>
    <button type="button" id="lw-load">load the registry</button>
    <span class="mt-summary" id="lw-note"></span>
  </div>
  <div class="lw-list" id="lw-list"></div>
</div>

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

Everything that reads or writes Diafon can work from one file,
[alphabet-spec.json](alphabet-spec.json): every letter with its marks and
glyphs, the languages, the spellings, and test cases to pass.

<script src="../assets/diafon-core.js"></script>
<script src="../assets/font.js"></script>
<script src="../assets/fontcheck.js"></script>
