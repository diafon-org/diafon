# Going public

The sequence from the private repo to the launch posts. The work itself
and its gates are in plan.md, the rationale in remarks.md. The academic
track (native reviewers from phonology departments, a paper at
a writing-systems venue, the dataset as a citable DOI) comes after the
launch and lives on what the launch recruits; nothing here waits for it.

## Stage A: before the first push (identity, licences, the claim)

The repo has no remote. Everything in this stage is invisible after the
push and hard to change after it, so it is done first.

1. **Owner.** One named legal person (Sz or the company) is the copyright
   holder of record, the trademark claimant, the donation recipient and
   the store publisher. The git identity for public commits is chosen
   with it; the existing pseudonymous history is either kept as is or
   rewritten once now, never after.
2. **History audit.** `git log --all --stat` read once for anything not
   meant to be public (the _prevver reference tree, keys, personal paths in
   scripts, screenshots with private content). Rewrite or squash now if
   anything turns up.
3. **Licence files.** `LICENSE` (GPLv3) at the root; `LICENSES/` holding
   CC-BY-4.0 (spec, data, docs prose), OFL-1.1 (fonts, already
   fonts/OFL.txt) and AGPLv3 (any served engine: the bot); a short
   `LICENSING.md` mapping directories to licences, stating the commercial
   option exists on request, and pointing to the CLA. SPDX headers on the
   source files so the mapping is machine-checkable. The CLA is the
   Apache ICLA adapted to name the owner; signing is a line in the PR
   template until there is volume.
4. **The trademark claim.** The mark is used, not registered, so the
   notice is ™, never ®. `TRADEMARK.md` at the root: Diafon™ is a
   trademark of <owner>; the name and logo identify the system; anyone
   may say a product "implements the Diafon specification" or "supports
   Diafon" and may use the name to describe, teach or discuss the system;
   nobody may use it as or in a product name, domain, app store listing
   or font family name, or imply endorsement, without written permission;
   the tiered commercial policy of G2 is promised, not yet published. The
   notice line (`Diafon™ · <owner>`) goes on every surface at once: site
   footer via scripts/gen_site.py (today's footer says working draft),
   README, the fonts' name table (nameID 7 trademark and nameID 11 vendor
   URL in fonts/tools/build_font.py, plus Reserved Font Name Diafon in the
   OFL header, which is the one hard protection the fonts get), the
   Android and macOS about screens, spec.json's `name` block. First public
   use is dated by the v1 tag and an Internet Archive snapshot taken on
   launch day; that record is what a later filing rests on. Honest limit:
   the EU is first-to-file, so the claim deters and documents there but
   does not bind; in the US, use in commerce does create rights. The
   filing (EU word mark, US intent-to-use) is budgeted, not scheduled.
5. **Donations.** Pick the providers behind /support (GitHub Sponsors
   needs the named owner and a bank; Liberapay and Ko-fi need less).
   `.github/FUNDING.yml`, and the one support line beside the ™ line on
   every surface (G6).

Gate: a fresh clone shows licence, trademark and support on README, site
footer, fonts and IME about screens, and nothing else in history.

## Stage B: the public repo and the site

1. GitHub organisation `diafon`, repo `diafon`, Discussions on, Issues
   with two templates (language review, implementation bug).
2. `README.md` rewritten as the front door: one paragraph, one typed
   example and its rendering, links to description, playground, fonts,
   spec, input methods; status table per workstream; the licence, ™ and
   support lines; the call for native reviewers.
3. CI: scripts/build.sh on every push in GitHub Actions, publishing docs/
   to Pages with `CNAME diafon.io`; HTTPS on; a green badge in README (G4).
4. spec.json gains `version: "1.0"` and the description states the span
   marker and the settings schema (G3). Tag `v1.0.0`; release assets: the
   three fonts, the web subsets, spec.json, the Android APK (release-signed
   with a key kept out of the repo).
5. Privacy-respecting page counts (GoatCounter or Cloudflare analytics, no
   cookies), so the launch waves can be measured.

Gate: G3 and G4 hold; https://diafon.io serves the current build.

## Stage C: the surfaces a visitor tries in the first minute

Every launch post sends people to one of these; they are finished before
any post.

1. **Playground first impression.** Opens prefilled (`sjok sewp njawr` in
   the Hungarian stage, a Mandarin and an English line beside it), and the
   full state (text, output mode, stage) lives in the URL hash, so a post
   can link a typed example that renders on arrival.
2. **Names page** (workstream 11, pulled forward): your name in Diafon,
   the rendering as a shareable image. This is the one artifact people
   post back.
3. **Demo clips.** Two screen recordings of 15 to 25 seconds, no sound:
   the Android keyboard streaming `sjok sewp njawr` into a chat, and the
   playground switching one typed line between script form and three
   stages. Exported as MP4 and GIF; every post carries one.
4. **Specimen sheet.** One image: the same short passage in four
   languages in the Diafon serif, the mark triangle, the 26-key
   partition. The r/neography post is this image.
5. **Android install path.** GitHub release APK now; F-Droid submission
   (fdroiddata merge request, reproducible build) the week of launch,
   because it fits a pseudonymous owner and needs no fee; Google Play
   deferred until an owner is named and the 14-day closed test is worth
   running.
6. **Transport font** (workstream 4): the liga variant lets anyone see the
   script by picking a font in any app. Wanted for the typography wave,
   not blocking wave 1.
7. **macOS input method as a download.** The port is done; what is missing
   is a signed build with install steps on the site. Blocking for the
   Hacker News wave, whose readers try things on a laptop, not for wave 1.
8. **FAQ page** in docs/, answered once: why not IPA; why not Shavian,
   Unifon, SaypU and what happened to them; is this a conlang (no: it
   writes existing languages); why Latin letters; what about Unicode
   (existing codepoints, nothing to propose); who decides a language's
   table (the reviewer programme); is it free (yes, and what the ™ does
   and does not restrict).

Gate: G5 for wave 1 is playground, fonts, Android APK and the hu stage
native-reviewed (data/stages/hu.yaml is still draft: Sz reviews it first).

## Stage D: launch waves

Different posts for different rooms, one to two weeks apart, each with
its own angle and asset; never one cross-post. Reply to every comment on
the day of the post; the FAQ page absorbs the repeated ones.

| Wave | Where | Angle | Asset | Ask |
|---|---|---|---|---|
| 1 | r/neography, r/conscripts | the script: the anchor as signature mark, the mark triangle, the float rule | specimen sheet, link in the first comment | try the playground |
| 1 | r/conlangs | the design argument: the partition is forced, six operators are necessary and sufficient, the neighbouring-column law | text post from the description | critique the tables |
| 1 | r/hungarian, hup.hu, prog.hu (in Hungarian) | one keyboard, `sjok sewp njawr` reads as `sok szép nyár` | Android clip | native reviewers for hu.yaml |
| 2 | r/typography, typo.social, TypeDrawers | three faces from one construction law; the anchor drawn per letter; the hand project | anchor construction figure, the fonts page | honest type critique |
| 2 | Show HN, Lobsters, r/programming | the engineering: 26 keys, unique segmentation proven, a spec with 454 conformance vectors, streaming commit rule, one JSON that four engines replay | the spec, the macOS IM, the playground | implementers; Keyman, IBus, Windows ports |
| 3 | r/languagelearning, r/polyglot | one script for all your languages; the names page | names page image | learners, feedback on the learn page |
| 3 | per-language subreddits, one per reviewed language | the language's own table and stage | that table | one credited native reviewer each |
| 3 | Google Fonts issue, F-Droid, Keyman keyboard repository | listings | release assets | distribution, iOS via Keyman |

Show HN specifics: Tuesday to Thursday, 8 to 10 in the morning US
Eastern; title of the form "Show HN: Diafon – a phonemic script for every
language, typed on 26 keys"; the first comment is Sz's own, the origin
and the two cornerstones in five sentences, with the invitation to break
the segmentation guarantee in the playground. Not posted: r/linguistics
and r/asklinguistics remove constructed systems by rule.

## Stage E: after the launch

- Reviewer programme live: a review page listing every language, its
  state and its credited reviewer; the reviewer guide derived from
  data/README.md; a review issue template. Every reviewed language earns
  its wave 3 post.
- A monthly state-of-Diafon note in Discussions; a CHANGELOG per release;
  the spec's version bumped only by the conformance suite.
- Measured: page counts per wave, playground and names-page shares, APK
  and font downloads, stars, reviewers recruited, implementers who
  appear. The reviewers and implementers are the numbers that matter.
- The academic track opens here, with a live site and reviewed languages
  to point at: named asks to phonology departments (a reviewer per
  language), a Zenodo DOI for the dataset, a short paper for Written
  Language & Literacy or the grapholinguistics conference.
- Trademark filing triggered by the first commercial adopter or the first
  imitation; the commercial licence text and the tiered policy go past a
  lawyer at that moment, before any money is taken.
