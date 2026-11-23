# Diafon

**One alphabet for the sounds of many languages.**

Diafon is a phonemic alphabet. Twenty-four Latin letters stand for sounds,
and a small mark on a letter changes its sound in a set way. A sound is
written the same way in each language that has it, so one script serves
many languages. The text is ordinary Unicode.

The repository has two parts.

- **The alphabet**, everything outside `input/`: the letters and marks, the
  languages, the spellings it converts to and from, the fonts, the site, and
  one machine-readable file of all of it, `docs/alphabet-spec.json`. It
  knows no keyboard, and a test holds it to that
  (`tests/test_no_input.py`).
- **The typing**, in `input/`: the keys that write the letters, and the
  keyboards for each platform. It reads the alphabet's published file and
  decides no sound. See `input/README.md`.

```
data/      the points, the languages, the mapping, the spellings, the dictionaries
scripts/   the reference in Python and the generators
fonts/     Diafon Serif, Sans and Mono, and their tools
docs/      the site (diafon.io); docs/input is the typing's page, linked from input/web
tests/     the alphabet's tests
input/     the typing
```

Documentation: **[diafon.io](https://diafon.io)**

## How Diafon is made

The maintainer designs Diafon, makes the decisions and reviews the
results. Most of the code, data, documentation and font tooling is written
with Claude (Anthropic) through Claude Code, and checked by the project's
tests. Commits are made under the project's name.

## Licence

Anyone may use, write, teach and implement Diafon. Code is MIT (`LICENSE`),
the fonts are SIL OFL 1.1 (`fonts/OFL.txt`), docs and data are CC BY 4.0
(`LICENSE-docs`), and the generated lexicons keep their sources' terms
(`NOTICE.md`).
