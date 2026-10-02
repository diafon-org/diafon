# Typing

<p class="specimen"><code>t</code> <span class="ug">t</span> · <code>tj</code> <span class="ug">ț</span> · <code>tx</code> <span class="ug">ṭ</span> · <code>ty</code> <span class="ug">ť</span> · <code>txy</code> <span class="ug">t̤</span></p>

Every sound is typed as one base letter followed by zero, one or two
operator letters, then w for length, then tone digits if the language has
tones. That is the whole grammar of the input.

## Bases and operators

The 26 Latin letters are split into two roles that never overlap:

- **Base** letters carry a sound on their own.
- **Operator** letters never stand alone; they modify the base before them.

This separation is what makes the input unambiguous: an operator can never
be read as the start of a new sound, and a base always starts one.

--8<-- "roles.html"

The partition is forced, not chosen. Twenty letters carry a widespread
phoneme that no other letter covers. The six operators are exactly the
redundant letters of the Latin alphabet: c and q duplicate k or s, x spells
the cluster k+s, and j, y, w name glides, compositions of the close vowels i
and u. Making any of them a base would waste a letter on a duplicate value;
making any base an operator would rob a common phoneme of its letter.

Six is also the necessary number. The system needs six mutually independent
operator meanings, each pair held apart by some language that contrasts what
a smaller set would merge: Ukrainian keeps the hush affricate distinct from
affricate-plus-palatal, Hindi needs the back-lean beside the plain letter.

## What each operator means

An operator's meaning depends on the letter class it follows, but each
meaning is fixed for the whole system:

--8<-- "operators.html"

The special covers vowels by the same mechanism as consonants: nasality is
not a separate concept, it is the vowel special's stated default. Aspiration
and breathiness are not specials at all: they are sequences with h, exactly
as they sound: `th` /tʰ/, `bh` /bʱ/.

Tones need no operator: plain trailing digits, in input and script alike
(`sjan1`, <span class="ug">șan1</span>); a language's own spelling stage may
render them natively, as Pinyin does with diacritics.

## The limit

A form carries at most two operators; length's w rides free on top, so no
sound costs more than three keystrokes plus its length. Any operator can
serve as the second, its reading set by the one before it, exactly as first
operators read by their base.

## Points and the special

Every written form is one of two things:

--8<-- "points.html"

There is no sharp line between "fixed" and "approximate" points. A p is the
same everywhere; a t may be dental here and alveolar there. The
neighbouring-column law is the whole guarantee: per-language values drift at
most into an adjacent place for a consonant, one quality step for a vowel.

A language may write a phoneme on a slot it does not contrast in exactly two
cases. Qualities most outside speakers cannot produce anyway (implosives,
ejectives, emphatics, the special's whole domain) may overload their base
form, because an outsider's approximation is exactly what is written.
Everywhere else the drift must be perceptually minor, keeping a
cross-language reader's pronunciation close: one height step, dental for
alveolar, aspiration on a voiceless stop, rounding in the open region.
Neither case covers a miss a listener would notice: no u for /y/, no voicing
or manner swaps.

Dialect and speech impediments are never recorded. The special's notation
may be borrowed for such cases, but no new notation is ever invented for
them. Very fine phonetic qualities stay outside the notation entirely, as
they do in every practical orthography.

## Case

Capitals are orthographic, not phonemic. A sound is capitalized by typing
its base letter uppercase (`Sjip` <span class="ug">Șip</span>); operators
read the same in either case, so all-caps text works sound by sound
(`SJIP` <span class="ug">ȘIP</span>). A long consonant capitalizes only its
first letter.
