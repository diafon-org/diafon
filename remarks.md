# Remarks

Decision rationale lives here, never in the main docs; the docs state only
the current system. A superseded decision is deleted, not kept.

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
  affricate with the cluster.
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
  Polish writes its sibilants on the flipped anchors; the dotted sibilants
  stay in reserve. Mandarin ch is tqyh.
- Every written form is either a point (one reading, drifting at most a
  neighbouring column) or the special (double dot on consonants, grave on
  vowels: a language's own series over a stated default). The mark triangle
  carries both hierarchies at once: contrast strength and value width. No
  form lacks a universal value: every slot has a stated default.
- The anchor's construction law (stroke mode): it starts at the letter's own
  outermost bottom point (right edge for the anchor, left for the reverse),
  bites up into the letter to absorb its serif, slants toward the letter's
  middle, always reaches the depth of the deepest descender, and ends in a
  serif foot; the above-anchor of the float rule is the vowels' long acute,
  a little longer, its foot standing at the letter's middle and rising
  outward (to the right for the anchor, the left for the reverse). Baked per
  letter, so the joint is the letter's own. The sans and mono faces take the
  logo's hook instead of the straight stroke: it leaves the letter's bottom
  outer corner flush and nearly vertical, as wide as the stem, bends one way
  toward the middle and ends in a round cap a little below p. On t the tail
  is first lengthened and the hook leaves its end, deeper and more bent; on
  t d z c the reverse anchor grows out of the letter's own underside a
  little back from the right tip, as the hook the other way round (down and
  to the right) in one bend; on s b the anchor does the same mirrored: from
  the left tip back along the underside, then down and to the left. On n m x (both anchors) the hook continues
  the letter's own stroke with no kink and at its width, one slight bend
  that tightens toward the foot and starts up in the stem, which gives way
  to it (families.yaml: leave along, bend, rise). The above-anchor of these
  faces (p̓ g̓) is the acute with the same little bend: from a flat foot over
  the letter's middle it rises right and bends over into a round tip
  (families.yaml: above_hook). The double dot below is the
  diaeresis's own pair of dots, set a little lower than the single dot and
  centred on the letter's lower part (anchor.yaml double_dot_below). The double
  acute on vowels has the gap between its strokes, where they start at their
  feet, at the letter's middle (on i the dotless body's; the tittle yields
  and the lift is the body's). The vowels' acute and grave are baked the
  same way, the foot at the middle (á à, and on the lowered ạ ẹ …; the
  precomposed codepoints draw these forms), and a mark's "middle" is that of
  the part of the letter it sits against: the upper part above (j: the
  stem), the lower part below (r: the stem, t: stem and tail).
- fonts/tools/hand_sheet.py prints the glyphs in use as a one-page drawing
  sheet (fonts/hand/sheet.html, sheet.pdf): each strip has the glyphs in a
  thin top row and blank space beneath to draw in.
- Capitals are orthographic, not phonemic. An uppercase base letter
  capitalizes its point (Sjan = Șan); operators read the same in either
  case, so all-caps text works point by point (SJAN = ȘAN); the capital
  wears its marks on the same side as its small form (ġ Ġ, p̓ P̓), and a
  long consonant capitalizes only its first letter (Șș). No new forms, no
  mapping changes: case never carries phonemic weight.
- The float rule reads the rendered letter, capitals included: no capital in
  the system has a descender, so a capital always wears its mark below
  (p̓ P̦, ġ G̣).
- No lazy input layer. Per-language shortcuts work against the linear
  learning curve and the universality of the input, the system's first
  cornerstone. If convenience layers return at all, they live inside a
  per-language IME as its own affair, never in the system.
- The float rule (below unless the rendered letter descends) is accepted as
  current law but may need sophistication later; open.
- Stages (data/stages) render the same point stream in a language's current
  orthography, as adoption on-ramps. Conceptually a font-level thing
  (OpenType locl: same codepoints, language-tagged alternate forms), but font
  delivery is not controllable in messengers and phone keyboards, so a stage
  is emitted at the IME level as a Unicode spelling of the same points, and
  is render-only: it never changes what a key means.
- The handwriting capture gets a digital route beside paper: a drawing
  frame in the fonts page's own structure (every potential glyph, plus the
  extras a font needs), edited in any vector editor and read back by colour
  and position rather than by document structure, since editors flatten
  layers, drop ids and rescale on save; the corner squares register the
  drawing. Everything in a cell is rasterised and traced into one filled
  outline (strokes and brush fills alike, overlaps merged), so the result
  is a glyph, never a stroke; the analysis counts pieces against the
  reference rendered through the same pipeline (a ș is one piece, a t̤
  three). Traced glyphs live in fonts/hand/glyphs, never fonts/svg, which
  overrides the Diafon serif at build time.
- Glyphs can be described in text before any drawing: fonts/hand/design.yaml
  (points in font units, named heights, straight or smooth segments, a pen
  width, fills, dots, composition with flips) proofed to SVG over the
  Diafon reference and built through the frame's trace pipeline into the
  same glyph files. The point of a text form is iteration by numbers, the
  way the anchor is tuned in anchor.yaml; the smooth segment is a curve
  through the points (Catmull-Rom), so no control handles need writing.
- The Unicode representation (script.yaml `web`): the universal font is to be
  released separately and delivered through web font services, which cut a
  family into fixed subsets and never deliver a codepoint outside them; the
  anchors, the double dot below and the double acute sit in no subset, and a
  base plus mark split across two files loses its positioning. So every form
  in use is written as ONE precomposed letter inside latin and latin-ext
  (vietnamese deliberately excluded), and the font draws that letter as the
  Diafon composition: the marks stay the visual standard, the letter is the
  closest standard fallback, which messengers will show for good. Chosen per
  sign, closest look first: comma above → acute, and ģ for g (Latvian fonts
  float its cedilla above); anchor → cedilla where one exists, hooked ȥ ɱ for
  z m (a tail below), dot above for b x; reverse anchor → caron, ẍ for x, š ž
  for the flipped hush; dot below → ogonek on vowels; the special → macron
  below, hooked ƒ ʋ ʂ ƈ where none exists; diaeresis → caron on g r,
  circumflex on j; dot below with diaeresis → tilde; double acute → double
  grave; dot below with acute → circumflex, with grave → breve. The retroflex
  letters ʈ ɖ were declined for t d. A capital is the letter's case pair (Gj →
  Ģ), drawn with the mark below as the float rule says; ġ is listed so its
  capital is Ġ. The served ranges live in data/web_subsets.yaml with their
  date; tests/test_web.py holds every form in use, both cases, to them.
- Licensing (2026-09-11): the system is free to everyone, and no licence can
  make a company pay for the system itself. Copyright covers expression, not
  a system or method (Baker v. Selden; every copyright act excludes ideas,
  procedures and methods), so anyone may reimplement Diafon from the spec with
  their own glyphs and engine, as anyone could write Pitman shorthand. Copyleft
  does not protect them; it has no grip where they would take. The serif is a
  Noto derivative and stays OFL (derivatives inherit it, and OFL forbids
  selling the font), and a font file shipped beside proprietary software is
  mere aggregation under the GPL, so even the hand fonts ship free, as DejaVu
  does inside proprietary systems. Copyleft bites only on code: a vendor
  embedding the engine or an input method in a proprietary keyboard opens its
  code or buys a licence. Hence GPLv3 (AGPLv3 where the engine is served)
  with a commercial option for code, which needs the whole copyright, so
  contributors sign a CLA, not a DCO; the option can be relaxed to Apache
  later, never tightened once outside code is in. The lever that reaches
  every adopter is the name: "Diafon" and "supports Diafon" on a commercial
  product need a trademark licence, and a trademark policy can be tiered by
  company size, which no free licence can express (Rust, Mozilla, WordPress
  fund themselves this way). Non-commercial and source-available licences
  (PolyForm, BSL) were declined: not free software, kept out of Debian,
  F-Droid and Google Fonts, and a script lives or dies on adoption. Spec and
  data stay CC BY 4.0 so every implementation is welcome. The commercial
  licence text and the trademark policy go past a lawyer once, before any
  money is taken.
- Donations are the income until any company pays, and they are embedded, not
  a page apart: one support line in the footer of every page, the fonts page
  and the playground, the about screen of each input method, the repo's
  FUNDING.yml, the font's vendor URL in its name table, the bot's help. Every
  surface carries the same stable address, the site's /support, which
  redirects to the providers (GitHub Sponsors, Open Collective or Liberapay
  for recurring, Ko-fi for one-off), so a provider can change without
  touching an artifact. Never a paywall, nag or feature gate: the ask is one
  line, once per surface, and the free thing stays whole.
- The fonts are derivatives, and three of them: since the text is standard
  Unicode, a Diafon font adds only the visual standard, the anchors and
  double dots drawn under standard letters, so drawing 48 letters on top of
  an open superfamily is the proportionate way to have Serif, Sans and Mono
  now; original families from the hand project can replace them one by one.
  Noto is the base (Serif, Sans, Sans Mono share metrics and are OFL); the
  sans faces take the anchor without its serif foot. The chain is the
  industry one Google Fonts expects: fonts/families.yaml drives build_font
  (derive) → make_ufo (editable UFO sources with our own small feature file;
  Noto's decompiled features were unusable) → fontmake → a FontBakery gate
  that refuses failures → the web subsets. Whether Google lists a derivative
  is their curation call and does not affect delivery.
- The trademark is claimed, not filed (2026-09-12): a ™ notice and a
  TRADEMARK.md on every surface, the filing deferred until a commercial
  adopter or an imitation appears. Filing costs money and names an owner
  before either question is settled, and a claim already does the soft
  work: it tells adopters the name is not free to take, it dates first
  public use (the v1 tag and an archive snapshot), and it is the record a
  later filing rests on. ® would be false until registration and is never
  used. The limit is stated openly: the EU is first-to-file, so the claim
  deters there but does not bind; US rights do accrue from use. The fonts'
  names get the one hard protection available now, the OFL Reserved Font
  Name.
- Five more spelling stages beside Hungarian: Finnish, Turkish, Czech,
  Polish, Swahili, the orthographies that can be written per form without
  context. Spanish, Italian and Romanian (c/qu, c/ch, g/ge), German, and
  Estonian (unmarked palatalization) cannot, and Indonesian merges e and ə
  in one letter, which the validator rightly refuses; those wait for a
  stage format with context. Each stage carries a sample sentence in its
  own language, and the samples appear only in their own stage: the
  Hungarian sentence is not the system's specimen.
- One spelling, no chat spelling. The composed-marks rendering (base letter
  plus combining marks) was offered for a while as a chat output, since
  messengers never receive the Diafon font and their system fonts draw
  combining marks. It made every word exist twice, in stored messages, in
  copies, in every screen that had to explain the two. It is withdrawn from
  every output list; the universal letters go everywhere, and in a chat they
  show as the standard letters they are. Showing the Diafon font on the web
  is enough to convey the intent. The composed rendering stays only as an
  internal tool (stages.MARKS, the fonts page's shape comparison).
- Second pass on the web letters, toward the Diafon shapes: marks that sit
  below the letter in Diafon get letters with a mark below where Latin
  Extended has one. The retroflex t d n take the circumflex below (ṱ ḓ ṋ)
  instead of the caron; the anchored b takes the line below (ḇ) instead of
  the dot above. The affricates c̖ x̖ keep č ẍ, having nothing below.
- The web letters are withdrawn; the text is the composition. For a week the
  canonical spelling of each form was a precomposed Latin Extended letter
  chosen to sit inside the subsets a web font service delivers (ķ for k̦, ṱ
  for t̖, ȥ for z̦, ƒ for f̤). It bought delivery through one company's CSS
  service at the price of the system's promise: each borrowed letter carries
  a language's reading, and the system became one more dialect of the
  thicket it means to replace. The text is now the base letter plus the
  system's own combining marks, NFC-normalised, which is how the IPA and
  every new orthography of the last century are written: where Unicode has
  a letter for the pair it appears (ș ṭ ä á), elsewhere the sequence stands
  (t̤ k̦ ȁ), and Unicode calls both the same text. The fonts are served by
  the site (and can ride any CDN from the project's releases); a Google
  Fonts listing stays possible for download, their CSS embed does not. Kept
  from the detour: data/web_subsets.yaml as the measured reason, and the
  closest-shape study as guidance for drawing the shared precomposed letters.

