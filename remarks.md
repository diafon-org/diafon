# Remarks

Decision rationale and history live here, never in the main docs; the docs
state only the current system.

- The unit is named "point" (over unit, sign, diaphone): short, composes well
  (point set, point inventory, a point's band).
- Russian's soft f and v ride the special (fxy vxy) with its s and z: only
  Russian has them, and the anchor sits badly on the f and v stems.
- Hungarian takes no cheap-slot exception (its a e write as ä ẹ): bare-letter
  typing comfort belongs to a future lazy-input layer, not the canonical
  mapping.
- Aspiration and breathiness are sequences with h everywhere (th, bh, tqh,
  tyh): no covered language contrasts an aspirate with the cluster, Mandarin
  has no h phoneme at all, Korean's coda-h clusters already coalesce to
  aspiration in speech, and Hindi, Thai and Vietnamese romanize exactly so.
  This also freed Georgian's bare letters: its aspirates are h-sequences like
  everyone's, its ejectives its special.
- The Hindi and Bengali aspirated retroflexes are sequences (tyh dyh ryh): a
  consonant wears one mark, the special never stacks, and every one-side
  glyph on those bases is spent.
- German pf is the sequence p+f (typed pf): German never contrasts the
  affricate with the cluster, and it was the last one-language point. py
  returns to the reserve.
- The low-usage review keeps mj and Russia's other soft-series members (one
  rule over the series; only s z f v ride the special, the first two forced,
  the second two for stem fit), keeps eq iq (witnessed points, no glyph
  cost), keeps ky gy (the back-lean family is per-language by design), and
  keeps kq and dc (the bare letters q and x doing their script jobs).
- The retroflex lateral is lx (ḷ, the Indological form): the reverse anchor
  fights the foot serif on l, and lx was free. The retroflex r stays r̖:
  Tamil holds three rhotics at once, and the dot and the soft anchor are
  spent on the tap and the modified r.
- No anchor ever sits on l, r or f (the stems are too thin). Their families
  ride the dots: the tap and flap share ṛ, the special r̤ carries the soft r
  and Czech ř, the vocalic r̈ carries ɚ ɝ and Tamil ɻ, and the soft and
  palatal laterals sit on l̤. The double dot below and above never contrast
  within one language.
- The mark doctrine: a single dot or anchor is a point of its own, drifting
  only slightly; a doubled dot or reversed anchor flags a variant the base
  form approximates; the double dot and the anti-anchor contrast freely, and
  neither ever stacks. Three-way contrasts prefer plain, anchor and dot (Polish s ś sz =
  s ș ṣ); Georgian's ejectives are the bare letters now that its aspirates
  are h-sequences, the cleanest reading of the exotic licence. No language puts four marked
  forms on one letter.
- Retroflex hush rides the flipped anchor (sjy zjy tqy dqy: y flips an
  anchored hush), so retroflex is the anti-anchor everywhere except the thin
  stems. Russian is the one exception, its hush staying on the plain anchors:
  its soft s̤ z̤ may not contrast the anti-anchors within one language.
  Polish returns from the dots to the flipped anchors; the dotted sibilants
  retire to reserve. Mandarin ch is tqyh.
- The bands vocabulary retires. Every written form is either a point (one
  reading, drifting at most a neighbouring column) or the special (double dot
  on consonants, grave on vowels: a language's own series over a stated
  default). The mark triangle carries both hierarchies at once: contrast
  strength and value width. "Exotic" said "no universal value", which stopped
  being true when every slot got a stated default.
- The lazy input layer gets its data home: a `lazy` section in the mapping,
  per-language candidate shortcuts shown on the language's master table. The
  law: a shortcut may only claim a sequence the language leaves unspent (an
  unused form, or one that cannot start a segment in strict mode), so strict
  typing always passes through unchanged; the generator enforces it. Mandarin
  cannot lazily flip p t k to Pinyin's aspirates, those keys being spent as
  the plain stops, so the aspirates stay h-sequences.
- The anchor's construction law (stroke mode): it starts at the letter's own
  outermost bottom point (right edge for the anchor, left for the reverse),
  bites up into the letter to absorb its serif, slants toward the letter's
  middle, always reaches the depth of the deepest descender, and ends in a
  serif foot; the above-anchors of the float rule mirror this to the
  ascender line. Baked per letter, so the joint is the letter's own.
- The site layer: scripts/pages.py is the page registry (file, label, tease)
  and the shared navigation block; scripts/gen_site.py builds the landing
  index.html (teaser tiles with live counts and specimens) and refreshes the
  nav markers on the static pages, while gen_master.py emits the nav into
  master.html directly. The description moved to description.html.
- Capitals are orthographic, not phonemic. An uppercase base letter
  capitalizes its point (Sjan = Șan); operators read the same in either
  case, so all-caps text works point by point (SJAN = ȘAN); the capital
  wears its marks on the same side as its small form (ġ Ġ, p̓ P̓), and a
  long consonant capitalizes only its first letter (Șș). No new forms, no
  mapping changes: case never carries phonemic weight.
