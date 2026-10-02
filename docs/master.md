---
title: Master tables
hide:
  - navigation
  - toc
---

# Master tables

<p class="mt-lede">Every input form in use, with its glyph and its readings; then
each language's own table, stamped with the review state of its mapping. Type
in the box to try any text, and switch the font to see how any typeface draws
the marks. Notation: <code>input forms</code> in type style, script forms in
the Diafon serif, IPA always between slashes, /ʃ/.</p>

<div class="mt-bar" markdown="0">
  <label>table <select id="mt-table" autocomplete="off"></select></label>
  <label>font <select id="mt-font" autocomplete="off">
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
  <input type="text" id="mt-custom" placeholder="or any installed font" autocomplete="off" spellcheck="false">
  <span class="mt-summary" id="mt-summary"></span>
</div>

<div class="tryout" markdown="0">
  <div class="tryout-row">
    <label>try it, from <select id="try-from" autocomplete="off"></select></label>
    <button id="try-sample" type="button">sample</button>
    <span id="try-status" class="tryout-status"></span>
  </div>
  <textarea id="try-in" spellcheck="false" rows="2">sji sejlz si sjejlz</textarea>
  <div class="tryout-out g" id="try-out"></div>
  <div class="tryout-out back g" id="try-back" hidden></div>
  <div class="chips" id="try-chips"></div>
  <div class="mt-wrap" id="try-words-wrap" hidden><table class="mt" id="try-words">
    <thead><tr><th>word</th><th>read by</th><th>input form</th><th>universal</th><th>written back</th></tr></thead>
    <tbody></tbody>
  </table></div>
  <details class="tryout-help">
    <summary>How to read the try-out</summary>
    <p>Each chip is one sound: its glyph, its <code>input form</code>, and its
    reading in the selected table's language (the universal table shows the
    most common reading). Click a chip to find its row. A faded chip is a form
    the language does not use; a red one is not a well-formed segment (an
    operator or a digit cannot start one, and a form carries at most two
    operators plus <code>w</code>). Tones are trailing digits. The rows of the
    forms you typed are marked in the table.</p>
    <p>With a language's spelling as the source, the text is read back word by
    word: by its letters, by the language's own lexicon, or by a loan lexicon
    folded into its sounds. The second line writes the text back in that
    spelling, and the word table marks in red every word the round trip
    changed. For Mandarin the chips carry the characters of each toned
    syllable, most frequent first.</p>
    <p>Font marks: a red outline means the font draws the glyph no differently
    from its bare letter (the mark is missing); amber means another font
    stepped in.</p>
  </details>
</div>

--8<-- "master-tables.html"

<script src="play-data.js"></script>
<script src="engine.js"></script>
<script src="assets/master.js"></script>
