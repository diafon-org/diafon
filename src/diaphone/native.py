"""Universal `native` target: notation → the Latin+diacritics native view (see docs/native-view.md).

Like `render.ipa_labels`, this is a language-independent label→glyph map, built from a hand-assigned
per-point base glyph plus generative modifier diacritics. A few cells are still IPA-fallbacks (marked
GAP below): palatalised-modifier, the tap ɾ, and the Mandarin retroflex ʐ — the design doc doesn't fix
these yet, so they render as their IPA symbol for now.
"""
import unicodedata

from .decode import tokenize
from .notation import _label_maps, _mod_chars

# combining marks
_DA, _DB = "̇", "̣"        # one dot above / below
_DDA, _DDB = "̈", "̤"      # two dots above (diaeresis) / two dots below
_TILDE, _ACUTE, _PALAT, _RHOT = "̃", "́", "ʲ", "˞"

# point label -> native base glyph
_CONS = {
    "p": "p", "b": "b", "t": "t", "d": "d", "k": "k", "g": "g",
    "tj": "ț", "dj": "d̦", "kq": "q", "hj": "ʔ",           # ț ḑ q ʔ
    "m": "m", "n": "n", "nj": "ņ", "nx": "ŋ",                    # ņ ŋ
    "tc": "c", "dc": "đ", "pc": "p̈",                            # c đ p̈
    "tq": "c̦", "dq": "đ̦",                                 # c̦ đ̦
    "f": "f", "v": "v", "tx": "ṭ", "dx": "ḍ",                  # ṭ ḍ (dental)
    "s": "s", "z": "z", "sj": "ș", "zj": "z̦",                   # ș z̦
    "kx": "ḳ", "gx": "g̣", "hq": "ħ", "hx": "ʕ", "h": "h",  # ḳ g̣ ħ ʕ
    "l": "l", "lj": "ļ", "rx": "ʐ", "r": "r", "rj": "ɾ",    # ļ · ʐ GAP · r · ɾ GAP
}
_VOW = {
    "i": "i", "e": "e", "a": "a", "o": "o", "u": "u",
    "ic": "ü", "ec": "ö", "uc": "ı", "oc": "ọ",        # ü ö ı ọ
    "ij": "ị", "ej": "ẹ", "oj": "ȯ", "aj": "ȧ",     # ị ẹ ȯ ȧ
    "iq": "ụ̈", "eq": "ọ̈",                            # ụ̈ ọ̈
    "ac": "â", "ax": "ə",                                        # â ə
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
            g = g + _PALAT                                                      # GAP: ʲ fallback
        elif m == "rhotic":
            g = "ɚ" if g == "ə" else g + _RHOT                        # ə→ɚ ; else ˞ fallback
    return unicodedata.normalize("NFC", g)   # precompose where possible (a+́ → á)


def native_labels(all_ph, features, data_dir="data"):
    """{notation_label: native glyph} — point base glyph + modifier diacritics."""
    label_of_base, mod_map = _label_maps(all_ph, features, data_dir)
    out = {}
    base_of = {**_CONS, **_VOW}
    for lab, g in base_of.items():
        out[lab] = g                                                           # bare points
    for phs in all_ph.values():
        for ph in phs:
            pl = label_of_base.get(ph["base"])
            if pl is None or pl not in base_of:
                continue
            full = pl + _mod_chars(ph["mods"], pl, mod_map)
            out[full] = _apply(base_of[pl], pl, ph["mods"], pl in _VOW)
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
