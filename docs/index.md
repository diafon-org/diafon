# What Diafon is

<p class="specimen"><span class="ug">șip · c̦ip · ṭin · siṇ</span> <code>sjip tqip txin sinx</code></p>

One keyboard, one script, every language. Diafon is a universal phonemic
writing system with a matching input system: you type the sounds of any
language on the plain 26-letter keyboard you already have, and read them as
one script, or as that language's own spelling.

## The problem it solves

Every language spells its sounds its own way, and most need their own
letters and keyboards. Write an English name, a Mandarin word and a Polish
word in one message and you switch keyboards three times, and a reader
from a fourth language still cannot tell how any of them sounds. Diafon is
one way of writing sounds that serves every language, on the keyboard
everyone has.

## Three forms of one text

- The **input form** is what you type: only the 26 lowercase letters.
  `sjip` is the English word *ship*, `tqip` is *chip*, `txin` is *thin*.
- The **script form** is what you read: ordinary Latin letters carrying a
  few small marks, one glyph per sound: <span class="ug">șip c̦ip ṭin</span>.
- A **spelling stage** is the same text shown in a language's current
  orthography, where one exists.

The input converts to the script without ambiguity: no dead keys, no
menus, no guessing. The text itself is the script form, ordinary Unicode
letters and marks that any app, file or message carries; a reader without
the Diafon font sees the marks drawn by their own font, roughly in place.
The engine also reads back: give it text in the script, in the input form
or in a language's spelling, and it converts to any of the others, and can
tell which one it was given.

Notation, on every page: input forms in `type style`, script forms in the
Diafon serif, and IPA always between slashes, /ʃ/, so the three readings
of one letter shape are never confused.

## How 26 letters cover every language

The letters split into two groups that never overlap.

- Twenty letters stand for a sound on their own: the vowels **a e i o u**
  and the consonants **b d f g h k l m n p r s t v z**.
- Six letters never stand alone; they only change the letter before them:
  **c j q x w y**. These are exactly the letters the Latin alphabet wastes:
  duplicates like c and q, a cluster like x, glides like j, y and w.

A sound is one base letter plus up to two modifiers, plus w for length.
`sj` is *sh*, `tx` is the English *th*, `nx` is the *ng* in *sing*, `tq`
the *ch* in *church*, `iw` a long i. Each modifier has one fixed meaning per
letter class: j softens or hushes, x shifts to the neighbouring sound, c
makes an affricate on a consonant and flips rounding on a vowel, w
lengthens, y leans back, and the pair x+y is the **special**, a slot each
language fills with its own series. The full rules are on [Typing](typing.md).

## The marks you see

Each modifier becomes a small mark. The system's signature is the
**anchor**, a comma-like stroke attached to the letter:
<span class="ug">ș ț n̦</span>. A single dot is the shifted sound,
<span class="ug">ṭ ḍ ṇ</span>. A double dot is the per-language special.
The anchor leaning the other way is retroflex. Vowels take an acute for
long, a diaeresis for the rounding flip, a dot below for one step lower,
and a grave for their special, nasal by default. Marks sit below a
consonant and float above on letters with descenders, g and p, so nothing
collides. The whole set is on [The script](script.md).

## Phonemic, not phonetic

Diafon records what a language distinguishes, not how a sound is precisely
pronounced. A t is dental in one language and alveolar in another; both
write t. The guarantee is that the drift stays small, a neighbouring sound
at most, so a reader from any other language lands close. Where a language
has a series of its own, emphatic in Arabic, soft in Russian, ejective in
Georgian, that series takes the special: one thing to learn per language
rather than a new letter each.

## Where to go next

- [Typing](typing.md): bases, operators, what each operator means, the
  two-operator limit, tones.
- [The script](script.md): the marks, the mark triangle, the float rule,
  capitals.
- [Tables](tables.md): every consonant and vowel point in the Diafon font.
- [Status](status.md): which languages are covered and reviewed, which have
  spelling stages and dictionaries, which tools exist.
- [Playground](play.html): type and read, live.

A point is what linguistics calls a diaphoneme: one abstract unit uniting
corresponding phonemes across languages, realised differently by each. The
system's name honours the concept.
