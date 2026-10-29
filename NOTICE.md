# Third-party material

Diafon builds on the following. Each keeps its own licence; the files generated
from it carry the same terms.

## Fonts

| Material | Used for | Licence |
|---|---|---|
| [Noto Serif, Sans, Sans Mono](https://github.com/notofonts/latin-greek-cyrillic) (`fonts/Noto*.ttf`) | the base outlines of Diafon Serif, Sans and Mono | SIL Open Font License 1.1 |

## Lexicons

The sources are downloaded to `data/lexicon/sources/` and are not committed.
The generated tables (`data/lexicon/*.json` and their copies under `docs/` and
`extensions/`) are derived from them.

| Material | Used for | Licence |
|---|---|---|
| [CMU Pronouncing Dictionary](https://github.com/cmusphinx/cmudict) | English readings (`en.json`) | BSD 2-Clause, © Carnegie Mellon University |
| [FrequencyWords](https://github.com/hermitdave/FrequencyWords) | ranking spellings that sound alike (`en.json`) | CC BY-SA 4.0 |
| [LibreOffice hu_HU dictionary](https://github.com/LibreOffice/dictionaries/tree/master/hu_HU) | Hungarian stems (`hu.json`) | MPL 2.0 or LGPL 3.0+ |
| [Unihan database](https://www.unicode.org/charts/unihan.html) | Mandarin readings (`zh.json`) | Unicode License v3 |
| [CLDR annotations](https://cldr.unicode.org) | emoji names (`data/emoji.json`) | Unicode License v3 |

Because of FrequencyWords, `en.json` is shared under CC BY-SA 4.0.

## Sample texts

Aesop's *The North Wind and the Sun*, Shakespeare's Sonnet 18 and Petőfi's
*National Song* are in the public domain. The Universal Declaration of Human Rights may
be freely reproduced.
