---
title: Learning
hide:
  - navigation
  - toc
  - footer          # the lessons have their own previous / next
---

# Learning

<link rel="stylesheet" href="assets/learn.css">

<div class="learn-bar" markdown="0">
  <label>language <select id="ln-lang" autocomplete="off"></select></label>
  <span class="learn-note" id="ln-note"></span>
</div>

<p class="learn-lede">Diafon one idea at a time, in the sounds of your
language. Each lesson adds one thing: first the letters that are sounds on
their own, then each operator in the order your language uses it most, then
length, the y forms, tones and capitals. Example words use only what the
lessons so far have taught. The last lesson is a card of every sound, to
print and keep by the keyboard.</p>

<div class="learn" markdown="0">
  <nav class="learn-steps" id="ln-steps" aria-label="lessons"></nav>
  <article class="lesson" id="ln-lesson"></article>
  <div class="learn-move">
    <button type="button" id="ln-prev">← previous</button>
    <button type="button" id="ln-next" class="primary">next →</button>
  </div>
</div>

<script src="play-data.js"></script>
<script src="engine.js"></script>
<script src="learn-data.js"></script>
<script src="assets/learn.js"></script>
