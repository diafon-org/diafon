# Diaphone font

Restored from the previous implementation (git history) — the source of the
signature glyph: the true **attached, elongated anchor**.

Current state in the remake:
- `docs/diaphone.woff2` is the cleaned, subset build actually served by the
  pages: basic Latin + only the combining marks the system uses
  (U+0300 0301 0307 0308 030B 0313 0314 0316 0323 0324 0326) — regenerate with
  `fontTools.subset` from `Diaphone-Regular.ttf` (72 KB → 19 KB).
- `tools/build_font.py` is rebuilt for the remake: charset from
  `docs/fonts-data.js`; the anchor and reverse anchor end in a parametric
  **serif foot** (SERIF_W/SERIF_T), matching the font's own descender
  terminals; U+0314, U+0324 and the precomposed ḷ ṃ ṿ ẍ ẗ are generated
  procedurally — the drawing to-do is closed. SVG overrides still win where
  present (`tools/font_svg.py`; paths inside font_svg still assume the old
  layout).

The previous workflow notes follow, kept for the rebuild:

---

# Diaphone font — customisation workflow

`Diaphone-Regular.ttf` is built from `NotoSerif-Regular.ttf` (SIL OFL, see OFL.txt) by
`scripts/build_font.py`: subset to the engine's charset → procedural stroke-mark seeds →
**your SVG edits imported on top** (they always win). The loop:

```
1. edit any fonts/svg/<glyph>.svg          (only the path inside <g id="glyph">; guides are reference)
2. python scripts/build_font.py            (rebuilds the ttf with your shapes)
3. python scripts/gen_uni_page.py          (refreshes docs/index.html with the embedded font)
```

To (re)export a glyph for editing: `python scripts/font_svg.py export <glyph …>` — accepts a
codepoint (`0329`), a letter (`s`), or a glyph name (`dieresis`). Deleting an SVG returns that
glyph to its seed/Noto shape on the next build. The em is 1000 units; the dashed guides mark
baseline, x-height and descender.

## The mark kit (all currently exported)

Some marks exist twice: a *combining* glyph (used when a letter+mark pair has no precomposed
character — ș t̤ t̰ r̈ h̤) and a *positioned variant* (referenced by precomposed characters —
ü á ṗ). **Edit both files of a pair identically** or the two renderings drift apart.

| shape | combining file | variant file | appears in |
|---|---|---|---|
| stroke below (palatal) | uni0329.svg | — | ș z̦ ț d̦ n̦ l̦ c̦ đ̦ |
| double stroke below (soft) | uni0348.svg | — | s͈ z͈ k͈ … |
| stroke above / double (soft on p g) | uni030D.svg | uni030E.svg (its own file) | p̎ g̎ |
| dot below (derived point) | dotbelowcomb.svg | — (precomposed ṭ ḍ ḳ ṇ ṛ ị ẹ ụ ọ reference it directly) | ṭ ḍ ḳ ṇ ṛ · vowels |
| dot above | uni0307.svg | dotaccent.svg | ṗ ġ ẇ |
| two dots below | uni0324.svg | — | t̤ k̤ c̤ h̤ |
| two dots above | uni0308.svg | dieresis.svg | r̈ p̈ c̦̈ j̈ · ü ö ï ë ä |
| tilde below (emphatics) | uni0330.svg | — | t̰ d̰ s̰ z̰ |
| tilde above (nasal) | tildecomb.svg | tilde.svg | ã ẽ õ |
| acute (long V · tone 2) | acutecomb.svg | acute.svg | á é í ó ú … |
| double acute (long ü ö) | — | hungarumlaut.svg | ő ű |
| macron (tone 1) | uni0304.svg | uni02C9.svg | șān · ā ē … |
| caron (tone 3) | uni030C.svg | — | ǎ ǒ … |
| grave (tone 4) | gravecomb.svg | — | à è … |

The four stroke marks are procedural seeds (knobs `SINGLE_TOP/TIP`, `DOUBLE_TOP/TIP`,
`DOUBLE_SEP` at the top of build_font.py) — the exported SVGs match the current knob values;
an edited SVG overrides the knobs entirely.

Letters can be exported and edited the same way (`export s t đ ħ`).
