"""Universal `native` target: notation → the Latin+diacritics native view (see docs/native-view.md).

Like `render.ipa_labels`, this is a language-independent label→glyph map, built from a hand-assigned
per-point base glyph plus generative modifier diacritics. All cells are decided (see the doc). The
palatal *points* wear the comma-below family, PRECOMPOSED where Unicode has the letter (ș ț ņ ļ —
system fonts centre these perfectly; the combining U+0329 they replace rendered off-centre in real
apps) and combining U+0326 elsewhere (d̦ z̦ c̦ đ̦); the palatalised *modifier* (soft consonants) wears
the double vertical line below (U+0348 — p͈ s͈ …). The bespoke font will unify the two shapes. The
tap is ṛ (underdot — the retroflex approximant was merged into the plain r, freeing the dot; in a
language-specific view the same underdot may instead flag Mandarin's retroflex ⟨r⟩). A modifier label
that coincides with a point label (Russian tʲ=`tj`=c) keeps the point glyph — so the coronal soft
series (tʲ nʲ lʲ dʲ) reads as the palatal points ț ņ ļ d̦, and only the non-coronal soft consonants
(pʲ kʲ …, sʲ=`sjj` zʲ=`zjj`) wear the double line.

Vowels: `j` lowers (one dot below — ị ẹ ụ ọ), the diaeresis flips front↔back (ü ö · ï ë ä), and nasal
`y` is the tilde (ã ẽ õ). Pass `lang=` for a flavoured native view (HU ɑ→a); see `_LANG_OVERRIDE`.
"""
import unicodedata

from .decode import tokenize
from .notation import _label_maps, _mod_chars, full_label

# combining marks
_DA, _DB = "̇", "̣"        # one dot above / below
_DDA, _DDB = "̈", "̤"      # two dots above (diaeresis) / two dots below
_CB = "̦"                   # U+0326 combining comma below (palatal, where no precomposed letter exists)
_DVLB = "͈"                 # U+0348 combining double vertical line below (soft/palatalised)
_TILDE, _ACUTE = "̃", "́"

# point label -> native base glyph
_CONS = {
    "p": "p", "b": "b", "t": "t", "d": "d", "k": "k", "g": "g",
    "tj": "ț", "dj": "d" + _CB, "kq": "q", "hj": "ḥ",           # ț (precomposed) d̦ · q · ḥ = ʔ
    "m": "m", "n": "n", "nj": "ņ", "nx": "ṇ",                      # ņ (precomposed) · ṇ (velar ŋ, x-dot)
    "tc": "c", "dc": "đ", "pc": "p̈",                            # c đ p̈
    "tq": "c" + _CB, "dq": "đ" + _CB,                              # c̦ đ̦ (hush = affricate + palatal comma)
    "f": "f", "v": "v", "tx": "ṭ", "dx": "ḍ",                  # ṭ ḍ (dental)
    "s": "s", "z": "z", "sj": "ș", "zj": "z" + _CB,                # ș (precomposed) z̦ (ʃ ʒ)
    "kx": "ḳ", "gx": "g̣", "hc": "ħ", "hq": "ħ̣", "h": "h",  # ḳ g̣ · hc=ħ (pharyngeal, crossbar) · hq=ʕ (q=c+j: crossbar + underdot) · h
    "l": "l", "lj": "ļ", "r": "r", "rj": "ṛ",   # ļ (precomposed) · r (trill) · ṛ (tap, underdot)
}
_VOW = {
    "i": "i", "e": "e", "a": "a", "o": "o", "u": "u",
    "ic": "ü", "ec": "ö", "uc": "ï", "oc": "ë",        # diaeresis = flip front↔back: ü ö (u/o → front y/ø) · ï ë (i/e → back ɯ/ɤ)
    "ij": "ị", "ej": "ẹ", "uj": "ụ", "oj": "ọ",     # j = lower one step = dot below (front & back uniform)
    "iq": "ụ̈", "eq": "ọ̈",                            # ụ̈ ọ̈ (q = c+j: below-dot + diaeresis)
    "ac": "ä", "ax": "ə",                                        # ä = a flipped to the back = ɑ (same diaeresis logic) · ə
}


def _apply(base, label, mods, is_vowel):
    g = base
    for m in sorted(mods):
        if m == "long":
            if is_vowel:
                g = {"ü": "ű", "ö": "ő"}.get(g, g + _ACUTE)  # ü→ű, ö→ő, else +acute
            else:
                g = g + g          # geminate: double the WHOLE glyph (s̩→s̩s̩ — g[0] would drop the mark;
                                   #   first-letter doubling is an orthography rule, decode.py only)
        elif m == "nasal":
            g = g + _TILDE
        elif m == "aspirated":
            g = g + _DA                                                         # one dot above
        elif m == "labialized":
            g = g + _DDA                                                        # diaeresis
        elif m == "pharyngealized":
            g = g + _DDB                                                    # two dots below (emphatics t̤ d̤ s̤ z̤)
        elif m == "palatalized":
            g = g + _DVLB           # U+0348 double vertical line below — the soft/tense mark, two-line partner of the single-line palatal points
        elif m == "rhotic":
            g = "ṙ"                     # the r-coloured vowel = a vocalic r: dot ABOVE (r-family: r trill · ṛ tap · ṙ rhotic)
    return unicodedata.normalize("NFC", g)   # precompose where possible (a+́ → á)


# Language-flavoured native overrides. A native glyph may mean something else in one language iff no
# language contrasts the two, so it stays injective within that language (see docs/native-view.md).
# HU has no base /a/ (only /ɒ/→ɑ and /aː/), so a Hungarian view can render ɑ (`ac`) as plain `a` — giving
# the natural á/a — where the universal view must keep ä (French contrasts a~ɑ: patte/pâte).
_LANG_OVERRIDE = {
    "hu": {"ac": "a"},        # HU has no base /a/, so ɑ → plain a (á/a)
    "zh": {"r": "ṛ"},         # Mandarin ⟨r⟩ is the retroflex approximant (merged into r); show it with the
                              #   underdot (the standard retroflex mark) — safe, Mandarin has no tap
}
NATIVE_LANGS = tuple(_LANG_OVERRIDE)   # languages that have a flavoured native view


def native_labels(all_ph, features, data_dir="data", lang=None):
    """{notation_label: native glyph} — point base glyph + modifier diacritics.

    `lang` selects a flavoured native view: its base-glyph overrides (see `_LANG_OVERRIDE`) apply before
    modifiers compose, so the whole family follows (HU `ac`→a, `acw`→á, `ach`→ã)."""
    label_of_base, mod_map = _label_maps(all_ph, features, data_dir)
    base_of = {**_CONS, **_VOW, **_LANG_OVERRIDE.get(lang, {})}
    out = {lab: unicodedata.normalize("NFC", g) for lab, g in base_of.items()}  # bare points first — always win
    for phs in all_ph.values():
        for ph in phs:
            pl = label_of_base.get(ph["base"])
            if pl is None or pl not in base_of:
                continue
            full = full_label(pl, ph["mods"], mod_map)
            # a modifier label that coincides with a point label (tʲ=`tj`=c) keeps the point glyph
            out.setdefault(full, _apply(base_of[pl], pl, ph["mods"], pl in _VOW))
    # Systematic long forms for every point, so an unattested length (e.g. `ojw`=ʊː) still composes
    # its diacritic instead of leaking a literal `w`. `w` is never a base, so no label collides.
    for pl, base in base_of.items():
        full = pl + _mod_chars({"long"}, pl, mod_map)
        out.setdefault(full, _apply(base, pl, {"long"}, pl in _VOW))
    return out


_TONE_SUP = {"1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵"}


def to_native(text, all_ph, features, data_dir="data", lang=None):
    labs = native_labels(all_ph, features, data_dir, lang=lang)
    words = []
    for w in text.split():
        tone = ""
        if len(w) > 1 and w[-1] in _TONE_SUP:
            tone, w = _TONE_SUP[w[-1]], w[:-1]
        words.append("".join(labs.get(t, t) for t in tokenize(w, labs.keys())) + tone)
    return " ".join(words)
