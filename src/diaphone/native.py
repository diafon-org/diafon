"""Universal `native` target: notation → the Latin+diacritics native view (see docs/native-view.md).

Like `render.ipa_labels`, this is a language-independent label→glyph map, built from a hand-assigned
per-point base glyph plus generative modifier diacritics. All cells are decided (see the doc). The
palatal marking is a clean one-line/two-line family (latin22's scheme, which renders better than the
combining comma): the palatal *points* wear a single vertical line below (U+0329 — t̩ n̩ l̩ s̩ …), and the
palatalised *modifier* (soft consonants) wears the double vertical line below (U+0348 — p͈ s͈ …). The
tap is ṛ (underdot — the retroflex approximant was merged into the plain r, freeing the dot; in a
language-specific view the same underdot may instead flag Mandarin's retroflex ⟨r⟩). A modifier label
that coincides with a point label (Russian tʲ=`tj`=c) keeps the point glyph — so the coronal soft
series (tʲ nʲ lʲ dʲ) reads as the palatal points t̩ n̩ l̩ d̩, and only the non-coronal soft consonants
(pʲ kʲ …, sʲ=`sjj` zʲ=`zjj`) wear the double line.
"""
import unicodedata

from .decode import tokenize
from .notation import _label_maps, _mod_chars

# combining marks
_DA, _DB = "̇", "̣"        # one dot above / below
_DDA, _DDB = "̈", "̤"      # two dots above (diaeresis) / two dots below
_VLB = "̩"                  # U+0329 combining vertical line below (single — the palatal points; latin22's mark, renders cleaner than the comma)
_DVLB = "͈"                 # U+0348 combining double vertical line below (soft/palatalised — the two-line partner of _VLB)
_TILDE, _ACUTE, _RHOT = "̃", "́", "˞"

# point label -> native base glyph
_CONS = {
    "p": "p", "b": "b", "t": "t", "d": "d", "k": "k", "g": "g",
    "tj": "t" + _VLB, "dj": "d" + _VLB, "kq": "q", "hj": "ʔ",       # t̩ d̩ (palatal, vertical line) · q ʔ
    "m": "m", "n": "n", "nj": "n" + _VLB, "nx": "ṇ",               # n̩ (palatal) · ṇ (velar ŋ = x-operator dot-below)
    "tc": "c", "dc": "đ", "pc": "p̈",                            # c đ p̈
    "tq": "c" + _VLB, "dq": "đ" + _VLB,                            # c̩ đ̩ (hush = affricate + palatal line)
    "f": "f", "v": "v", "tx": "ṭ", "dx": "ḍ",                  # ṭ ḍ (dental)
    "s": "s", "z": "z", "sj": "s" + _VLB, "zj": "z" + _VLB,        # s̩ z̩ (ʃ ʒ, palatal line)
    "kx": "ḳ", "gx": "g̣", "hq": "ħ", "hx": "ʕ", "h": "h",  # ḳ g̣ ħ ʕ
    "l": "l", "lj": "l" + _VLB, "r": "r", "rj": "ṛ",   # l̩ · r (trill) · ṛ (tap, underdot — freed by the ɻ→r merge)
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
                g = g[0] + g                                                    # geminate: double
        elif m == "nasal":
            g = g + _TILDE
        elif m == "aspirated":
            g = g + _DA                                                         # one dot above
        elif m == "labialized":
            g = g + _DDA                                                        # diaeresis
        elif m == "pharyngealized":
            g = "ẓ" if label == "dx" else g + _DDB                         # ðˤ→ẓ ; else two dots below
        elif m == "palatalized":
            g = g + _DVLB           # U+0348 double vertical line below — the soft/tense mark, two-line partner of the single-line palatal points
        elif m == "rhotic":
            g = "ɚ" if g == "ə" else g + _RHOT                        # ə→ɚ ; else ˞ fallback
    return unicodedata.normalize("NFC", g)   # precompose where possible (a+́ → á)


def native_labels(all_ph, features, data_dir="data"):
    """{notation_label: native glyph} — point base glyph + modifier diacritics."""
    label_of_base, mod_map = _label_maps(all_ph, features, data_dir)
    base_of = {**_CONS, **_VOW}
    out = {lab: unicodedata.normalize("NFC", g) for lab, g in base_of.items()}  # bare points first — always win
    for phs in all_ph.values():
        for ph in phs:
            pl = label_of_base.get(ph["base"])
            if pl is None or pl not in base_of:
                continue
            full = pl + _mod_chars(ph["mods"], pl, mod_map)
            # a modifier label that coincides with a point label (tʲ=`tj`=c) keeps the point glyph
            out.setdefault(full, _apply(base_of[pl], pl, ph["mods"], pl in _VOW))
    # Systematic long forms for every point, so an unattested length (e.g. `ojw`=ʊː) still composes
    # its diacritic instead of leaking a literal `w`. `w` is never a base, so no label collides.
    for pl, base in base_of.items():
        full = pl + _mod_chars({"long"}, pl, mod_map)
        out.setdefault(full, _apply(base, pl, {"long"}, pl in _VOW))
    return out


_TONE_SUP = {"1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵"}


def to_native(text, all_ph, features, data_dir="data"):
    labs = native_labels(all_ph, features, data_dir)
    words = []
    for w in text.split():
        tone = ""
        if len(w) > 1 and w[-1] in _TONE_SUP:
            tone, w = _TONE_SUP[w[-1]], w[:-1]
        words.append("".join(labs.get(t, t) for t in tokenize(w, labs.keys())) + tone)
    return " ".join(words)
