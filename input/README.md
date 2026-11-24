# Diafon input

**Ways of typing the Diafon alphabet.**

The alphabet (everything above this folder) is the points, their glyphs,
the languages, the spellings, the fonts. It knows no keyboard. This folder
is the other half: input profiles (what keys produce which points), the
engine that reads them, and the input methods for each platform. It owns no
sound decision: every target of every key is a point of the alphabet.

Until 2026-11-23 this was a repository of its own, diafon-org/diafon-input;
its history came along.

## Layout

```
profiles/          the input profiles, as data: diafon-v1.yaml
spec/              the compiled profiles, with their vectors
engine/            the Python reference: alphabet.py (the script, from the
                   alphabet's spec), profile.py (compile), engine.py (segment,
                   letters, stream)
input_methods/     macOS and iOS on diafon-v1, with the core they share; Android asleep (see below)
legacy/            the typing from before the split and everything built on its
                   key strings; kept, not built
web/               the site's Input page: the typing in JavaScript, the
                   try-out and the lessons (docs/input links here)
scripts/           compile_profile.py, gen_lessons.py, gen_page.py, gen_apple.py,
                   gen_emoji.py, build.sh
tests/             the profiles, the JavaScript, the lessons, the Apple core,
                   the iOS keystroke logic
```

## The typing: diafon-v1

Every letter of the alphabet on a plain keyboard, with two operator keys:
`y` and `q`, the two letters the alphabet leaves out. It writes every
language of the alphabet in full.

| | `y` | `q` | `yq` | `qy` | `qyq` |
|---|---|---|---|---|---|
| consonant | anchor: `sy` ș | dot: `tq` ṭ | double dot below: `tyq` t̤ | | |
| vowel | double dot: `uy` ü | long: `aq` á | both: `oyq` ő | dot below: `eqy` ẹ | dot below, long: `oqyq` ọ́ |

- On r and w the `y` is the double dot above: `ry` r̈, `wy` ẅ. The soft r̦ is `ryq`.
- On m and n the double dot above is `qy`: `mqy` m̈, `nqy` n̈, the syllabic nasal before its own letter (`mqymaduqy` m̈madụ).
- A nasal vowel is the vowel and `mq`: `bomq` boṃ.
- A doubled consonant is the long one, and an operator after it applies to
  both: `ssy` șș.
- A doubled operator is the plain letter: `cityy` city, `tqq` tq. An
  operator with nothing to apply to is plain too: you, quick.
- A digit after a letter is its tone: `ni3 kqaw3` niˇ ḳawˇ. Doubled, it is
  the plain digit: `h22o` h2o.

The profile is data (`profiles/diafon-v1.yaml`); compiled
(`spec/diafon-v1.json`) it carries its key table, the languages it writes
and its vectors, which a port must reproduce.

## The input methods

The Mac input method and the iOS keyboard type `diafon-v1`. They port
nothing: they run the site's own JavaScript, `docs/assets/diafon-core.js`
(the alphabet) and `web/diafon-keys.js` (the typing), in JavaScriptCore, on
the alphabet's spec and the compiled profile
(`input_methods/apple/Core/Diafon.swift`). A change to the alphabet reaches
them with the next build, and `tests/test_apple.py` replays the vectors
through the Swift side.

## What is asleep

The typing Diafon had before the split, `universal-v1` (twenty base letters,
five operators), and the first two-operator table, `minimal-hu-v1`, are in
`legacy/` with their generators, tests and frozen data. The Android input
method still holds its text in `universal-v1` key strings and carries the
alphabet as it was when it was last generated; it is due the same rewrite.

## The alphabet

The dependency runs one way. The engine and the ports read the published
`docs/alphabet-spec.json` and nothing else of the alphabet; the apps bundle
its fonts and its mark from `fonts/` and `docs/logo/`. The generators of the
lessons also use the alphabet's Python reference (`scripts/alphabet_ref.py`).
Nothing of the alphabet reads this folder.

## Build and test

```
sh input/scripts/build.sh               # compile the profile, build the page, test
```

## How it is made

As Diafon is: the maintainer designs it, makes the decisions and reviews
the results; most of the code is written with Claude (Anthropic) through
Claude Code, and checked by the project's tests. Commits are made under the
project's name.

## Licence

As the rest of the repository: see the README one folder up.
