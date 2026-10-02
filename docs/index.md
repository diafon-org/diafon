---
title: The system
hide:
  - navigation
---

--8<-- "home-hero.html"

## One sound, one letter

Every language spells its sounds its own way: the same /ʃ/ is *sh* in
English, *s* in Hungarian, *š* in Czech and *ş* in Turkish. Diafon writes
each sound one way in every language, so a reader from anywhere can say a
word they have never seen.

--8<-- "home-sounds.html"

## The letters

The letters of the keyboard split into two groups that never overlap.
Twenty are **bases**: each stands for a sound on its own. Six are
**operators**: they never stand alone, they only change the base before
them.

--8<-- "home-keys.html"

The split is forced, not chosen. Each base carries a widespread sound no
other letter covers. The operators are the letters the Latin alphabet
wastes: c and q duplicate k or s, x spells k plus s, and j, w and y name
glides, the close vowels i and u in another role. Six is also the number
needed: every pair of operator meanings is kept apart by some language that
contrasts what fewer operators would merge.

## Typing a sound

A sound is typed as one base, then at most two operators, then `w` for
length, then tone digits where the language has tones. That is the whole
grammar of the input. An operator never starts a sound, so the input
converts to the script without ambiguity: no dead keys, no menus, no
keyboard to switch, and every typed line reads one way only.

An operator means the same thing on every letter of its class, and on
screen it becomes a small mark. Each example shows the glyph, what you type
and its most common reading.

--8<-- "home-ops.html"

- A second operator is read by the first, as the first is read by the
  base: `sj` is <span class="ug">ș</span>, `sjy` the retroflex
  <span class="ug">s̖</span>.
- Length is `w`, after the operators: `aw` <span class="ug">á</span>; a
  long consonant doubles its letter in the script, `sjw`
  <span class="ug">șș</span>.
- Aspiration and breathiness are not operators. They are sequences with h,
  as they sound: `th` /tʰ/, `bh` /bʱ/.
- Tones are plain trailing digits in input and script alike: `sjan1`
  <span class="ug">șan1</span>. A language's own spelling may render them
  natively, as Pinyin does with diacritics.

## The marks

The script is built from small letters and a small set of marks. Each mark
keeps one meaning on every letter; none is borrowed from any language's
alphabet.

### On consonants

A consonant wears its mark below, unless the letter has a descender: then
the mark floats above, on g and p (the **float rule**). No capital has a
descender, so a capital always wears its mark below:
<span class="ug">p̓ P̦</span>, <span class="ug">ġ G̣</span>.

--8<-- "marks.html"

The signature mark is the **anchor**: a comma-like stroke, elongated and
attached to its letter. The attached form is in wide use nowhere else, so
it can be Diafon's own, and in handwriting it is one continuous stroke off
the letter. It is the standard comma-below character, which the Diafon font
draws attached: <span class="ug">ț ș n̦</span>. It never sits on l, r or
f, whose stems are too thin; their modified forms use the dots instead
(<span class="ug">ḷ ṛ r̤ r̈ l̤</span>).

A single mark, anchor or dot, makes a point of its own, whose value drifts
only slightly between languages. A double dot or a reversed anchor flags a
variant the reader should notice, with the bare letter as the good-enough
approximation. Marks never stack.

Some sounds are whole letters: the operators take script jobs of their
own. c is /t͡s/ and x is /d͡z/; the anchor turns them into
<span class="ug">c̦</span> /t͡ʃ/ and <span class="ug">x̦</span> /d͡ʒ/, so the
anchor marks the whole hush family, <span class="ug">ș z̦ c̦ x̦</span>. q is
the uvular /q/, j and w are the glides /j/ and /w/, and the glottal stop is
the dot on h, <span class="ug">ḥ</span>.

### On vowels

A vowel wears at most one mark above and one below; two marks never stack
above. The double acute exists because flip and long together would
otherwise need two.

--8<-- "vowelmarks.html"

Lowering sits below and everything else above, so every combination in use
keeps to one mark per side: <span class="ug">ẹ́</span> /ɛː/,
<span class="ug">ẹ̀</span> /ɛ̃/, and the flipped and lowered
<span class="ug">ọ̈</span> /œ/, <span class="ug">ụ̈</span> /ʏ/.

## The points

Every point of the system: 29 consonants and 17 vowels, each with its
script glyph, its input and its reading. The colours are the operators of
the keyboard above. Every form in use, and each language's own reading of
it, is in the [master tables](master.md).

--8<-- "points.html"

## Points and the special

Diafon writes what a language distinguishes, not the fine detail of how a
sound is pronounced. Every written form is one of two things.

A **point** has one reading. Its value in a given language drifts at most
into a neighbouring column: an adjacent place for a consonant, one quality
step for a vowel. A t is dental in one language and alveolar in another;
both write t, and a reader from any other language lands close.

**The special** is a language's own series over a stated default: emphatic
in Arabic, soft in Russian, ejective in Georgian, nasal on vowels. It is
read per language, always in the neighbourhood of its base, never as an
arbitrary sound: one thing to learn per language, not a new letter each. On
a consonant it is typed `xy` and drawn as a double dot,
<span class="ug">t̤</span>; on a vowel it is typed `y` and drawn as a
grave, <span class="ug">à</span>.

A language may write a sound on a form it does not otherwise use in two
cases only. Sounds most outside speakers cannot produce anyway (implosives,
ejectives, emphatics) may share their base form, because an outsider's
approximation is exactly what is written. Elsewhere the drift must be
minor, so a reader from another language still says it close: one height
step, dental for alveolar, aspiration on a voiceless stop, rounding among
the open vowels. Neither case allows a difference a listener would notice:
no u for /y/, no voicing or manner swaps.

Dialect and speech impediments are never recorded. Very fine phonetic
detail stays outside the notation, as it does in every practical spelling.

## Capitals

Case is spelling, not sound. A sound is capitalized by typing its base
uppercase: `Sjip` <span class="ug">Șip</span>. Operators read the same in
either case, so all-caps text works sound by sound: `SJIP`
<span class="ug">ȘIP</span>. A long consonant capitalizes only its first
letter.

## Ordinary text, any app

A Diafon text is ordinary Unicode: base letters plus the system's own
combining marks, normalised the standard way. Where Unicode already has a
letter for the pair (<span class="ug">ș ṭ ä á</span>) that letter is used;
elsewhere the sequence stands (<span class="ug">t̤ k̦ a̋</span>), and Unicode
treats both as the same text. Any app, file or message carries it.

The Diafon fonts (Serif, Sans and Mono) draw the marks as designed. Without
them a reader's own font draws the marks, roughly in place; the font switch
on the [master tables](master.md) shows how any typeface does. The engine
converts every way: from the script, the input form or a language's
spelling to any of the others, and it can tell which one it was given.

## Names

One name per concept, used everywhere: documents, code, interfaces.

--8<-- "names.html"

A point is what linguistics calls a diaphoneme: one abstract unit uniting
corresponding sounds across languages, realised a little differently by
each. The name Diafon comes from it.
