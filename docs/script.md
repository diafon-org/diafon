# The script

<p class="specimen"><span class="ug">ș z̦ c̦ x̦ · ṭ ḍ ṇ ḳ ġ ḥ · t̤ s̤ · s̖ z̖ · á ä a̋ à ạ</span></p>

The script form is built on small letters carrying a small set of marks.
Each mark keeps one meaning on every letter; nothing is borrowed from any
language's alphabet.

## The consonant marks

A consonant wears its mark below, governed by the **float rule**: every mark
floats above when its letter has a descender. No capital in the system has a
descender, so a capital always wears its mark below
(<span class="ug">p̓ P̦</span>, <span class="ug">ġ G̣</span>).

--8<-- "marks.html"

The signature mark is the **anchor**: a comma-like stroke that is both
elongated and attached to its base letter. This is deliberate: the attached
form is not in wide use anywhere, so it can become Diafon's visual
signature, and the attachment gives handwriting an easy, distinctive
gesture, one continuous stroke flowing off the letter. It never sits on l, r
or f, whose stems are too thin for it; their modified forms ride the dot
family instead (<span class="ug">ḷ ṛ r̤ r̈ l̤</span>). It is written with the
standard comma-below character, which the Diafon font draws as the true
attached form: <span class="ug">ț ș n̦</span>, and by the float rule g wears
its anchor on top.

Not every sound composes from marks; the operator letters themselves take
script-form jobs. c is /t͡s/ and x is /d͡z/; the anchor turns them into the
hush affricates <span class="ug">c̦</span> /t͡ʃ/ and <span class="ug">x̦</span>
/d͡ʒ/, so the anchor marks the whole hush family:
<span class="ug">ș z̦ c̦ x̦</span>. q is the uvular /q/. The glottal stop is
the shift on h, <span class="ug">ḥ</span>. The glides take j /j/ and w /w/.
Length needs no mark at all: a long consonant doubles its letter.

## The vowel marks

A vowel wears at most one mark above and one below; two marks never stack
above. The double acute exists precisely because flip + long would otherwise
have to.

--8<-- "vowelmarks.html"

Lowering sits below, everything else above, so every attested combination
keeps to one mark per side: <span class="ug">ẹ́</span> /ɛː/,
<span class="ug">ẹ̀</span> /ɛ̃/, and the flip-and-lowered pair
<span class="ug">ọ̈</span> /œ/, <span class="ug">ụ̈</span> /ʏ/.

## The mark triangle

y is deliberately the nasty letter. A single mark, dot or anchor, is a point
of its own whose value drifts only slightly. A doubled dot or a reversed
anchor flags a variant the reader should notice, with the base form as the
good-enough approximation; the double dot and the anti-anchor contrast
freely, and neither ever stacks. On an anchored hush, y performs the flip
itself: retroflex is always the anti-anchor.

--8<-- "triangle.html"

The mark triangle is the vowel triangle turned. The base sits at the apex;
the anchor and the dot grow out of it as two branches, and each branch ends
in its flagged form, the anti-anchor and the double dot. Contrast strength
falls with proximity: strongest between the branches, then between the base
and a branch, weakest between the two forms of one branch, and that last one
is avoided as a contrast. Value width follows the same tree: the base and
the single marks are points, one reading each; at the branch ends the
reverse anchor stays a point, retroflex everywhere, while the double dot is
the special, read per language.

## The text is the marks

A Diafon text is a base letter plus the system's own combining marks,
normalised the standard way: where Unicode already has a letter for the pair
(<span class="ug">ș ṭ ä á</span>) it appears as that letter, elsewhere the
sequence stands (<span class="ug">t̤ k̦ a̋</span>), and Unicode treats both as
the same text. Fonts draw the marks; a reader without the Diafon font sees
them drawn by their own font, roughly where they belong. The fonts are
served by the site itself, because web font services that cut a family into
fixed Unicode subsets deliver only some of the marks.

## Names

One name per concept, used everywhere: documents, code, interfaces.

--8<-- "names.html"
