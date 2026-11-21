# Diafon

**One alphabet for the sounds of many languages.**

Diafon is a phonemic alphabet. Twenty-five Latin letters stand for sounds,
and a small mark on a letter changes its sound in a set way. A sound is
written the same way in each language that has it, so one script serves
many languages. The text is ordinary Unicode.

This repository is the alphabet: its letters and marks, the languages, the
spellings it converts to and from, the fonts, and one machine-readable file
of all of it, `docs/alphabet-spec.json`. It knows no keyboard: ways of
typing Diafon are separate projects that read that file.

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
