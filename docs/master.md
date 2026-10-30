---
title: Reference
hide:
  - navigation
---

# Reference

<div class="mt-bar" markdown="0">
  <label>language <select id="mt-table" autocomplete="off"></select></label>
</div>

<p class="mt-lede">Every Diafon letter with its readings, and each
language's own table. Pick a language to see its table. An example and the
typing box are below the tables.</p>

--8<-- "master-tables.html"

## Try it

<div class="mt-sample" id="mt-sample" markdown="0"></div>

<div class="tryout" markdown="0">
  <textarea id="try-in" spellcheck="false" rows="3" placeholder="Type in Diafon, for example: sjip, tqokolawda" aria-label="Diafon typing"></textarea>
  <div class="tryout-out" id="try-out"></div>
</div>


<details class="fontcheck" markdown="0">
  <summary>Check a font</summary>
  <p class="tryout-help">Show every Diafon letter on this page in another font. A red outline
  means the font leaves the mark out; amber means another font steps in.</p>
  <div class="mt-bar fontbar">
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
</details>

<div class="mt-samples" id="mt-samples" markdown="1">

## Sample texts

Longer texts in the picked language, read from their usual spelling and
shown in Diafon. Texts in a language other than English come with an English
translation.

--8<-- "samples.html"

</div>

<script src="../play-data.js"></script>
<script src="../engine.js"></script>
<script src="../assets/master.js"></script>
