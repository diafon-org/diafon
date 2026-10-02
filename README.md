# Diafon

**One keyboard, one script, every language.**

Diafon is a phonemic writing system with a matching input system. You type
the sounds of any language on the plain 26-letter keyboard you already
have, and read them as one script, or as that language's own spelling.

| you type | everyone reads | English spelling |
|---|---|---|
| `sjijp tqijp txijn txijnxk` | șịp c̦ịp ṭịn ṭịṇk | ship chip thin think |

The same sound is written the same way in every language: English *sh*,
Hungarian *s*, Czech *š* and Turkish *ş* are all `sj`, read ș.

## How it works

- Twenty letters are sounds: the vowels `a e i o u` and the consonants
  `b d f g h k l m n p r s t v z`.
- Six letters never stand alone; they change the sound before them:
  `c j q x w y`. They are the letters the Latin alphabet wastes.
- A sound is one letter plus at most two operators, then `w` for length.
  Every typed line reads one way only.
- On screen each operator becomes a small mark. The signature mark is the
  **anchor**, a comma-like stroke attached to the letter: ș ț z̦.
- The text is ordinary Unicode (Latin letters with combining marks), so any
  app, file or message carries it.

The documentation site explains the rest: the home page gives the
overview, and the **master tables** page lists every form, its glyph and
its readings, each language's own table with its review state, a try-out
box, and a font switch that shows which typefaces draw the marks.

## What is in this repository

| Path | What it holds |
|---|---|
| `data/` | The source of truth: each language's phonemes (`languages/`), the phoneme to input form mapping (`mapping.yaml`), how forms draw (`script.yaml`), spelling stages (`stages/`) and lexicons (`lexicon/`). See `data/README.md`. |
| `scripts/` | The reference engine (`engine.py`, `stages.py`, `lexicon.py`) and the generators for everything derived from the data. |
| `docs/` | The documentation site (MkDocs Material), the JavaScript engine and the generated `spec.json`. |
| `fonts/` | Diafon Serif, Sans and Mono, derived from Noto, with their build chain. See `fonts/README.md`. |
| `input_methods/` | The macOS and Android input methods. See `input_methods/README.md`. |
| `extensions/` | The browser extension. |
| `tests/` | The engine, spec, script, font and port tests. |

Every implementation reads one file, `docs/spec.json`, and must reproduce
its vectors; the Python engine is the reference.

## Building

The data drives everything. After changing anything in `data/`:

```sh
pip install mkdocs-material pyyaml
scripts/build.sh          # every generator, the tests, and the site into site/
```

To work on the documentation alone:

```sh
python3 scripts/gen_master.py   # the master tables, after a mapping change
python3 scripts/gen_site.py     # the home page figures
python3 -m mkdocs serve         # http://127.0.0.1:8000
```

The site is published to GitHub Pages by `.github/workflows/docs.yml` on
every push to `main`.

## Status

32 languages carry a phoneme inventory and a mapping; English and Mandarin
are reviewed against the literature, Hungarian by a native speaker. Six
languages have a draft spelling stage. The status page of the site holds
the full table, generated from the data.

**Native reviewers wanted.** A language's mapping is final only when a
native or expert reviewer has checked it. Each language's table on the
master tables page shows what there is to check.

## Licence

The fonts are under the SIL Open Font License (`fonts/OFL.txt`).
