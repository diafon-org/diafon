---
title: Diafon
hide:
  - navigation
  - toc
---

--8<-- "home-hero.html"

## One sound, one letter

Every language spells its sounds its own way: the same /ʃ/ is *sh* in
English, *s* in Hungarian, *š* in Czech and *ş* in Turkish. Diafon writes
each sound one way in every language, so a reader from anywhere can say a
word they have never seen.

--8<-- "home-sounds.html"

## 26 letters, two jobs

The letters of the keyboard split into two groups that never overlap.
Twenty stand for a sound on their own. Six never stand alone; they only
change the letter before them. These six are the letters the Latin alphabet
wastes: c and q duplicate k or s, x is k plus s, and j, w and y are glides.

--8<-- "home-keys.html"

A sound is one letter plus at most two operators, then `w` for length:
`sj` is the *sh* of *ship*, `tx` the *th* of *thin*, `nx` the *ng* of
*sing*. That is the whole grammar. No dead keys, no menus, no keyboard to
switch, and every typed line reads back one way only.

## Each operator, one meaning

An operator means the same thing on every letter, and on screen it becomes
a small mark. The signature mark is the **anchor**, a comma-like stroke
attached to the letter: <span class="ug">ș ț z̦</span>. A dot is the
shifted sound: <span class="ug">ṭ ḍ ṇ</span>. Vowels take an acute for
length, a diaeresis for the rounding flip, a dot below for one step lower
and a grave for nasal. Each example below shows the glyph, what you type,
and its most common reading.

--8<-- "home-ops.html"

## Ordinary text, any app

The script is ordinary Unicode: Latin letters with combining marks, so any
app, file or message carries it. The Diafon fonts draw the marks as
designed; without them, a reader's own font draws them, roughly in place.
The engine converts every way: from the script, the input form or a
language's spelling to any of the others, and it can tell which one it was
given.

## Phonemic, not phonetic

Diafon writes what a language distinguishes, not the fine detail of how a
sound is pronounced. A t is dental in one language and alveolar in
another; both write t, and the difference never goes beyond a neighbouring
sound, so a reader from any other language lands close. Where a language
has a series of its own (emphatic in Arabic, soft in Russian, ejective in
Georgian), that series takes the **special**: one thing to learn per
language, not a new letter each.

## Where to go next

<div class="grid cards" markdown>

-   **[Master tables](master.html)**

    Every form, its glyph and readings, every language's own table. Try
    any text and check any font on the same page.

-   **[Typing](typing.md)**

    The bases, the operators, what each one means, the two-operator limit,
    tones and capitals.

-   **[The script](script.md)**

    The marks, the mark triangle, why marks float above g and p, the
    names.

-   **[The points](points.md)**

    Every consonant and vowel point in one table and one triangle.

-   **[Status](status.md)**

    Which languages are mapped and reviewed, which have a spelling and a
    dictionary, which tools exist.

-   **[For implementers](implement.md)**

    The grammar, streaming, reading back, and the one spec file every
    port reproduces.

</div>

A point is what linguistics calls a diaphoneme: one abstract unit uniting
corresponding sounds across languages, realised a little differently by
each. The name Diafon comes from it.
