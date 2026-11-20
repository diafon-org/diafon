# Diafon input

**Ways of typing the Diafon alphabet.**

[Diafon](https://github.com/diafon-org/diafon) is a phonemic alphabet: its
points, their glyphs, the languages, the spellings, the fonts. It knows no
keyboard. This repository is the other half: input profiles (what keys
produce which points), the engine that reads them, and the input methods
for each platform. It owns no sound decision: every target of every key is
a point of the alphabet.

## Layout

```
vendor/            the alphabet, vendored: alphabet-spec.json, the lexicons,
                   and ALPHABET (version, commit, sha256 of what was taken)
profiles/          the input profiles, as data: universal-v1.yaml, minimal-hu-v1.yaml
spec/              the compiled profiles, with their vectors
engine/            the Python reference: alphabet.py (the script, from the
                   vendored spec), profile.py (compile), engine.py (segment,
                   points, stream)
input_methods/     macOS, iOS, Android, and the Swift core they share
data/              the keyboard layouts, the lessons' plan, the emoji table
docs/              the typing engine in JavaScript, the playground and the lessons
                   (files only: this repository publishes no site yet)
scripts/           the generators
tests/             the profiles, the engine, the ports, the pre-split goldens
```

## Profiles

A profile is data, compiled to a table. It is immutable by id: a change to
`universal-v1` is `universal-v2`. It names the alphabet major it targets.

- `universal-v1`: the typing Diafon had before the split, every language,
  plain ASCII. Twenty base letters, the operators `c j q x y`, `w` for
  length, digits for tones. Its conformance is the spec as it was before
  the split (`tests/goldens/spec.json`): every typing vector reproduces
  byte for byte.
- `minimal-hu-v1`: Hungarian, English and Mandarin sounds on two operators.
  Twenty-four letters are points as they stand; `y` marks the letter before
  it (`sy` ș, `cy` c̦, `ny` n̦, `uy` ü, `oy` ö), `q` is the dot after t d n
  (and `kq` ḳ) and length after a vowel (`aq` á, `oyq` ő). A doubled consonant is the
  long one (`ssy` șș). A doubled operator is the plain letter (`cityy`
  city), and so is one with nothing to apply to (you, my, quick). A digit
  after a point is its tone, so Mandarin is typed with the same keys
  (`ni3 kqaw3`). A segment commits when the next one starts.

## The alphabet

`scripts/sync_alphabet.py` copies the alphabet's spec and lexicons from a
checkout of diafon-org/diafon into `vendor/` and records the version. The
dependency runs one way. The engine and the ports read `vendor/` only. The
generators that need a language read or written (the old spec, the lessons,
the emoji table) also run the alphabet's Python reference from that
checkout (`$DIAFON_ALPHABET`, or `../diafon`).

## Build and test

```
python3 scripts/sync_alphabet.py        # after the alphabet changes
sh scripts/build.sh                     # compile, generate, test
python3 scripts/gen_goldens.py --check  # every pre-split row, about three minutes
```

The Mac input method and the iOS keyboard take the profile as a setting
(the keyboard menu on the Mac, the keyboard's settings on iOS). Inside, the
Swift core still holds a text in `universal-v1` forms: a key-table profile
is read into those forms (`input_methods/apple/Core/Profiles.swift`), and
`universal-v1` itself is still the grammar in code. Android has
`universal-v1` only.

## How it is made

As Diafon is: the maintainer designs it, makes the decisions and reviews
the results; most of the code is written with Claude (Anthropic) through
Claude Code, and checked by the project's tests. Commits are made under the
project's name.

## Licence

Code is MIT (`LICENSE`). The vendored lexicons and the generated tables
keep their sources' terms (`NOTICE.md`).
