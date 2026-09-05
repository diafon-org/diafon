# Language data

Two layers, strictly separated:

- `languages/<code>.yaml` — **metadata only**: what each language contrasts,
  per the standard descriptive literature. No system analysis in here.
- `mapping.yaml` — **the mapping**: phoneme → input form, the explicit,
  reviewable layer between the metadata and everything generated. Global map
  plus per-language `overrides`, reviewed within-language `merges`, and the
  per-language `review` state: non-reviewed → reviewed → native-reviewed.
  Every language ultimately needs a native or expert reviewer.

`scripts/gen_master.py` validates the mapping (full coverage; no
within-language form collision outside `merges`) and renders
`docs/master.html` — the universal table plus every language's own table,
each stamped with its review state.

## Schema

```yaml
code: hu              # ISO 639-1
name: Hungarian
speakers: {native: 13, total: 13}   # millions, rough 2025 estimates
geminates: true       # only where consonant length is contrastive
tones:                # only where the language is tonal:
  1: high             # input digit -> standard contour, from the vocabulary below
consonants:           # the phonemes the language contrasts, as IPA
  p: M                # value = coarse frequency, see below
vowels:
  ɒ: L
```

## Frequency sizes

Per-phoneme T-shirt sizing of how often the phoneme occurs in running text:

- **L** — among the language's most frequent phonemes
- **M** — ordinary
- **S** — notably infrequent
- **X** — marginal: loanword-only, interjection-only, or recessive /
  dialect-restricted (Spanish ʎ, French ɑ, Korean ø y)

## Standard tone vocabulary

Every tonal language maps its input digits onto one canonical contour set —
never onto ad-hoc accent characters:

| Contour | Chao letters | Shape |
|---|---|---|
| `high` | ˥ | level, high register |
| `mid` | ˧ | level, mid register |
| `low` | ˨ / ˨˩ | level or falling, low register |
| `rising` | ˧˥ | rises |
| `falling` | ˥˩ | falls |
| `dipping` | ˨˩˦ | falls then rises |
| `glottal-` prefix | ◌ˀ | the contour with glottalization (Vietnamese ngã, nặng) |

A language with more tones than this vocabulary extends the table here, not
its own file.

## Sources and confidence

- **Inventories** follow the standard descriptive literature: the *Journal of
  the IPA*'s "Illustrations of the IPA" series, standard reference
  phonologies and grammars per language, with PHOIBLE and the per-language
  phonology overviews (Wikipedia's tertiary summaries of the above) as
  cross-checks. Each file was reviewed language by language against these.
- **Frequency sizes** are coarse editorial estimates informed by
  per-language phoneme frequency studies where available and typological
  judgment otherwise.
- **Speaker numbers** are rough 2025 estimates of the Ethnologue /
  encyclopedic ballpark, in millions. Statistics sum **native** counts —
  totals double-count multilingual people.

Phonemes are listed as the language's own contrastive units under the
mainstream analysis (allophones excluded); long vowels are listed as
segments, contrastive consonant length is the `geminates` flag; glides j/w
appear under consonants as is conventional. Where mainstream analyses
disagree (e.g. English diphthongs, Polish nasal vowels), the file follows
the majority description, and the Diaphone mapping layer — not this data —
is where system-specific analysis happens.
