---
title: Reference
hide:
  - navigation
---

# Reference

<div class="mt-bar" markdown="0">
  <label>Diafon flavour <select id="mt-table" autocomplete="off"></select></label>
</div>

## Tables

<p class="mt-lede">Every Diafon letter with its readings, and each
language's own table. Pick a language to see its table. An example and the
typing box are below the tables.</p>

--8<-- "master-tables.html"

## Spelling rules

Diafon writes the contrasts a language makes, so one sound can take a
different letter in two languages. Three rules cover every such row in the
tables; the row names its rule.

<div class="rules" markdown="0">
<p id="rule-1"><b>1. Two hush series.</b> A language's hushing sounds take the anchor:
<span class="ug">ș z̦ c̦ x̦</span>. A language with two series writes the softer, more
forward one with the anchor and the harder, further-back one with the reverse anchor:
Polish /ɕ/ and /ʂ/ are <span class="ug">ș</span> and <span class="ug">s̖</span>, Russian
сь and ш are <span class="ug">ș</span> and <span class="ug">s̖</span>. With one series
the anchor stands for it, whatever its exact sound: Mandarin /ʂ/ is <span class="ug">ș</span>.</p>
<p id="rule-2"><b>2. A vowel area splits only where a language needs it.</b> Each plain
vowel covers an area. A language with two vowels in one area marks the more open one
with a dot below, <span class="ug">ẹ ọ ị</span>, and on a the front one,
<span class="ug">ä</span>; it keeps the mark in its long and nasal vowels. Where length
already tells two vowels apart there is no mark: English /iː/ and /ɪ/ are
<span class="ug">í</span> and <span class="ug">i</span>, Dutch /i/ and /ɪ/ are
<span class="ug">i</span> and <span class="ug">ị</span>.</p>
<p id="rule-3"><b>3. One phoneme, one letter.</b> Two sounds that are one phoneme in a
language share the letter of its main value: English /ʌ/ is its stressed schwa,
<span class="ug">ạ</span>; Mandarin /ə/ and /ɤ/ are one vowel, <span class="ug">ë</span>.</p>
</div>

## Try it

<div class="tryout" markdown="0">
  <textarea id="try-in" spellcheck="false" rows="3" placeholder="Type in Diafon, for example: sjip, tqokolawda, ni3kxaux3" aria-label="Diafon typing"></textarea>
  <div class="tryout-out" id="try-out"></div>
  <div class="tryout-row tryout-opts">
    <label><input type="checkbox" id="try-orig"> usual spelling</label>
    <label><input type="checkbox" id="try-tones" checked> tones above the syllable</label>
    <label><input type="checkbox" id="try-join"> joined long consonants</label>
  </div>
</div>


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
