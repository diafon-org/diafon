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

- **Two choices, not seven (2026-09-14).** The Mac status menu listed
  Universal and every language's spelling as one flat row of radio items; Sz:
  too many options. The choice a person makes is binary, Universal or my
  language's spelling, and the language is a second, rarer choice. So every
  screen now offers Universal (the default) and Language spelling, the
  language in a submenu or popup, and remembers the language apart from the
  choice, so switching back and forth keeps it. The default language is the
  first system language that has a spelling. The macOS icon follows the
  system's grid (a rounded tile inset on the canvas) at the large sizes and
  the full tile at the menu-bar sizes, so the mark still reads at 16 px.
  Android keeps its flat list for now and follows in its own round.

- **One key for the mode; the CJK candidate window for the spellings
  (2026-09-14).** Sz asked for a good shortcut between passthrough, Universal
  and the language's spelling: the bare Shift tap now cycles the three in
  that order, with a label near the caret naming the mode, so a three-state
  cycle stays legible. And the Pinyin-style chooser: InputMethodKit's own
  candidate window (IMKCandidates) shows the underlined segment in every
  spelling, opened with Tab or the down arrow so the digits keep their tone
  meaning while typing; it takes arrows, digits, Return, Escape. It is the
  Android strip in the Mac's native form, and one more argument for the
  IME as the place where the spellings meet.

- **The h-sequence is a reading, not a segment (2026-09-25).** Sz: lighthouse
  is not tʰ, so th already has a problem. The engine agrees: th is two
  segments, t and h, and the text is the two letters; the aspirated reading
  is a convention of the languages that have aspirates (zh ko th vi ka: tʰ,
  bn hi: t̪ʰ), the way sh is a convention of English. It holds because none
  of those languages has a t + h cluster to contrast with it (Korean even
  merges the cluster into tʰ by rule), and English, which has the cluster,
  has no aspirate. A language with both would need the aspirate on a mark,
  not on h; none of the 32 does, and the table records the sequence as the
  licence it is. The same goes for θ: no language of the 32 contrasts θ (tx)
  with tʰ (th); Burmese does, and writes both apart in Diafon anyway.

- **The engine reads back (2026-09-26).** Two asks, a context-menu
  conversion of a selection between modes and a browser extension that
  turns pages between canonical spelling and Universal, needed one thing
  the engine lacked: reading a spelling back into forms. It is the same
  machine reversed, longest match over a table, and it holds without a
  dictionary because the stages are validated injective and the script is
  one to one over the forms in use (the grammar as a whole is not: kx and
  kc both dot the k, so the forms in use decide). What a language keeps for
  etymology and never writes (Hungarian ly, Czech y ý ů ě) enters as read
  aliases, read but never rendered, so the stage's one-way losses stay
  stated. Detection is coverage, the share of letters a source reads with
  its own spellings, the mode in use breaking ties; the Mac's plain
  service trusts it, the window shows it and lets it be overruled. Limits
  named: all-caps re-renders as capitalized, and compounds can fool a
  digraph (házszám). The browser extension is the first surface that is
  not an input method at all: it reads a page as written and shows it in
  the script, which is the argument for the script made on every page of
  the web.

- **The lexicon: the fourth layer (2026-09-26).** Sz asked for English (its
  own spelling, and as loans), Hungarian ly, and a pinyin chooser by tone,
  in one structure. They are one thing: knowledge the letters cannot carry,
  kept per word. So the system now has four layers: the points, the marks
  (the script), the letter stages, and the lexicon. A lexicon reads
  (spelling to transport) and writes (transport to spelling), by word or by
  stem, and may offer choices (a toned syllable's characters). The sources
  are open dictionaries, never hand lists where a dictionary exists:
  CMUdict, Magyar Ispell, Unihan, a subtitle frequency list to rank
  homophones. Two decisions worth recording. Loans belong to the source
  language, not the host: one English lexicon serves every host, and the
  host says only how the sounds fold into its own (θ → t, æ → e), a small
  table a native speaker can review, drafted for Hungarian. And the loan
  decision stays lexical, never phonotactic alone: the host's own
  dictionary decides what is native (tag, team), the loan lexicon what is
  foreign, the longest stem wins, and only a foreign letter shape (ee, sh,
  w) tips a word the host's dictionary also lists. The round trip of a
  loan is lossy by design: hausz, lájk, míting are how Hungarian ends up
  writing them anyway.

- **The extension is a switch (2026-09-27).** Sz: the icon should turn the
  conversion on and off; and the reverse mode, a Universal page shown in a
  language's spelling, is a very rare feature, maybe useless; keep the
  language by hand only where auto does not work. So the extension has one
  setting and no menu: a click on the icon toggles Universal for every
  page (the badge says on), the language comes from the page, its lang
  attribute or its text, and the reverse mode is gone. The popup survives
  only as the picker on a page whose language neither says, set per tab by
  the background when the page reports none, with the switch inside since
  the click opens it there; the language picked is kept for that host. The
  test drives the switch from the extension's own service worker (found
  among Chrome's built-in extensions' workers by its manifest name) and
  holds on and off both. The state is the icon itself, not a badge: round,
  inset to 70% of the canvas as toolbar icons are, light grey while off,
  the two-tone mark on ink while on (logo.py draws both, the extension's
  icons/ folder holds them). Sz: no settings is fine only if auto is
  reliable. The engine's detect scores a stage by the letters it reads
  without its aliases, so Czech text with y or ě never reached the 0.98
  bar, and plain ASCII ties every Latin stage. The extension reads a page
  its own way: English first, by its function words (its letters say
  nothing without the lexicon); then the stages that read the text in
  full with aliases; among several, those that read it without them
  (Hungarian reads nyár by its own letters, Czech by y = i); then the
  browser's languages; else nobody, and the picker. The tab's tooltip
  names the language found and where it came from. Left open in the
  engine: the Turkish stage does not read the capital dotted İ (the caps
  come from toUpperCase), and detect's alias rule is worth revisiting.
  Firefox takes a background script where Chrome takes a worker and
  neither tolerates the other's key, so build.sh writes an extensions/
  firefox copy with manifest.firefox.json.

- **A stem looked up short (2026-09-27).** Sz, reading a page: traumái came
  out as tromái, jamaicai as dzsöméköi. Two holes in the loan rule. The
  native stem is matched as a prefix of the word, and a Hungarian suffix
  lengthens the stem's final a or e (trauma, traumái), so trauma was never
  found, while English had traum with a short suffix. The lexicon now
  names the lengthened vowels (`lengthen`, á → a, é → e) and every stem,
  native or loan, is looked up short as well, in the three ports. And ai
  and oa were on the foreign-shape list, though ai is the commonest
  adjective ending after a (hazai, jamaicai); both are off it, ay and ey
  with them as the y rule already had them. Then akinek read as akin + ek,
  English being one letter longer than the stem aki the dictionary holds
  (the inflected forms are not in it): the longest stem cannot be trusted
  against a suffix, so a suffixed word with no foreign shape is now never
  a loan; a loan is a whole word (like, team) or carries its shape
  (meetingen). Left as they were, for a
  native review: tea reads as the loan ti, because ea is the shape that
  makes team a loan and the two cannot be told apart by shape; and
  igazságtalanságok reads zs across the morpheme boundary, the stated
  limit of longest match, which only a dictionary split would lift.

- **Spoken: the spellings a host keeps (2026-09-27).** Sz, still reading:
  jamaicai came out by the letters (jämäicäi, c as ts) once it was no
  loan, and franchise-ba by the letters too, the dictionary listing the
  word and ch being no shape on the list. Two answers. ch joins the
  foreign shapes: franchise, chat, Michael go to English; but Bach, pech,
  cech would too, and Jamaica is nobody's: not the English sounds, not
  the Hungarian letters, but the name as a Hungarian says it. So the
  Hungarian lexicon has a `spoken` section, a hand list for native
  review: spelling -> how it is said, in Hungarian letters, read by the
  letters alone (bah is an English word too), matched as a stem with the
  lengthening, and consulted before everything else, in the three ports.
  The reader's order for a host with letters is now: its own entries,
  then the loan check, then the letters. The vectors carry the sentence.

- **The stems compete (2026-09-27).** Sz: streamingajánlójában read by
  the letters, felkerült as fẹlkőült (a stale copy: Felker is a CMUdict
  surname), and asked for the systemic view. Three rules changed, in the
  three ports. A loan stem is one of the source's common words (the
  frequency list rides in en.json as `common`): CMUdict's names and
  rarities (Felker, traum) no longer reach a Hungarian word. The foreign
  shape is judged on the stem, and a shaped stem may be followed by
  anything, read by the host's letters: a compound with a loan head
  (streaming + ajánlójában, meeting + jén). And the three stems compete
  by length, spoken, native and loan, the longest winning, spoken on
  ties: tea is spoken, team is the loan (a letter longer), teaház is tea.
  The reader's order for a host with letters is: the loan check, the
  spoken entries, the letters. Seven spoken entries seed the list: tea,
  and loans the dictionary lists in English spelling that no shape
  betrays (online, offline, startup, email, update, live). Measured, for
  the review: 1628 words of the Hungarian dictionary are also common
  English words with no foreign shape (had, has, sir, must, mind, film,
  hotel, video, internet, online…); the dictionary lists what Hungarian
  writes, not how it is said, so the ones read the English way need a
  spoken entry each, and no source decides it. Sz, on Cudjoe East read
  as Cudjoẹ Ist: the names could have an entry. So `names`, beside
  spoken, the proper names no dictionary reads, as a Hungarian says them
  (cudjoe: kadzsó, ocho: ocso), the same table kept apart for review.

- **The commons free, the closed ecosystems pay (2026-09-27).** Sz, on the
  reader's own entries: they need syncing across the extension and the
  input methods, which needs an account, which is the monetization. So
  three layers, in order. One: the entries live in the extension (the
  selection menu makes them, the options page keeps them, yaml in and
  out), following the browser profile for free; built. Two: the commons,
  the repo's names and spoken sections, fed by a "propose" that hands the
  yaml to a prefilled issue once the repo is public; built, the address
  left to set at publish. Three: an account (sign in with Apple or
  Google, one record per user, merged on change), the paid tier: the
  personal dictionary that follows a person across every keyboard and
  browser; later, when users ask. The principle, Sz's: a closed-source
  ecosystem that charges its developers should carry a paying service,
  so the iOS keyboard is about one dollar, and macOS may follow; the
  price low, covering the developer fees plus a small donation on top;
  the commons and the free surfaces stay whole, per the donation note
  above. Open: the legal structure behind the money. Sales through a
  store are the store's, taxed as business income wherever the seller
  is, with the store as merchant of record for VAT; donations are gifts
  in name only for a company and become income, and are tax-favoured
  only when the recipient is a registered nonprofit; a fiscal host (Open
  Collective's foundation, a Software Freedom Conservancy-style body)
  takes donations for an open project without an entity of its own, for
  a share. The one named owner of publish.md stage A is the same
  question; an accountant answers it for the country of residence, once,
  before the first store listing.

- **Names kept (2026-09-27).** Sz: an option not to convert names; and
  the icon's disc too tight around the mark. A reader can keep names as
  written (the icon's menu, the options page): a capitalised word inside
  a sentence stays in its spelling, the first word of a sentence reads,
  since nothing tells a name from a sentence start there; quotes and
  brackets before a word do not open a sentence. The disc, at any inset,
  was either too tight or too small at 16 px, so the toolbar icon is the
  app icon's rounded tile, full bleed (the toolbar pads it), the mark at
  78% of it, grey while off; the same tile everywhere. The menus are made
  on every start of the background worker, not only on install, since
  the worker restarts often and a reload is not always an install; the
  headless test proves the selection item exists by refusing a duplicate.

- **Detection follows the content (2026-09-27).** Sz: a page reloaded with
  the conversion on did not convert. The headless reload did, so the
  page differed: the language was detected once, at load, from the text
  present then, and a page filled by script had none yet; a later toggle
  re-ran detection over the text that had arrived meanwhile, which is
  why the toggle worked and the reload did not. Now, while a page has no
  language, the content that arrives is sampled and detection runs again;
  and the observer queues batches instead of dropping all but the last
  under its debounce. A headless case holds a script-filled page on
  switch-on and on reload.

- **The page as it changes, and the languages inside it (2026-09-27).**
  Sz: text loaded dynamically stays unconverted, and mixed-language text
  needs work. The observer watched added nodes only: a script that
  rewrites a text node in place (a framework's update) changed nothing
  it saw, and the old original would have come back on the next pass. It
  now watches characterData too, telling its own writes apart by the
  value it wrote last, and takes the page's rewrite as a new original.
  For mixed text, the part that is certain: an element's own lang
  attribute overrides the page's for its text, a quote or a name marked
  by the site; a language with no stage leaves it as written; the
  lexicon of a second language is fetched as needed. And every frame
  converts its own document. Not done, and the harder half: text in a
  second language that the site does not mark, which only per-block
  detection could find, at the risk of flipping a paragraph over its
  loans; and shadow roots, which the walker does not enter.
