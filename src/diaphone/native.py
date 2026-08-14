"""Universal `native` target: notation → the Latin+diacritics native view (see docs/native-view.md).

Like `render.ipa_labels`, this is a language-independent label→glyph map, built from a hand-assigned
per-point base glyph plus generative modifier diacritics. All cells are decided (see the doc). The
palatal *points* wear a single vertical line below, uniform on every letter (U+0329 — t̩ n̩ l̩ s̩ z̩ d̩,
hush c̩ đ̩); the palatalised *modifier* (soft consonants) wears the double vertical line (U+0348 —
p͈ s͈ …). One line = palatal, two lines = soft. Generic mark placement varies by font; the bespoke
font will fix that — the comma-precomposed alternative was tried and looked wrong in the docs. The
tap is ṛ (underdot — the retroflex approximant was merged into the plain r, freeing the dot; in a
language-specific view the same underdot may instead flag Mandarin's retroflex ⟨r⟩). A modifier label
that coincides with a point label (Russian tʲ=`tj`=c) keeps the point glyph — so the coronal soft
series (tʲ nʲ lʲ dʲ) reads as the palatal points t̩ n̩ l̩ d̩, and only the non-coronal soft consonants
(pʲ kʲ …, sʲ=`sjj` zʲ=`zjj`) wear the double line.

Vowels: `j` lowers (one dot below — ị ẹ ụ ọ), the diaeresis flips front↔back (ü ö · ï ë ä), and nasal
`y` is the tilde (ã ẽ õ). Pass `lang=` for a flavoured native view (HU ɑ→a); see `_LANG_OVERRIDE`.
"""
import unicodedata

from .decode import tokenize, tokenize_cased, _cap
from .notation import _label_maps, _mod_chars, full_label

# combining marks
_DA, _DB = "̇", "̣"        # one dot above / below
_DDA, _DDB = "̈", "̤"      # two dots above (diaeresis) / two dots below
_VLB = "̩"                  # U+0329 combining vertical line below — the palatal mark, uniform on every
                            #   letter (generic mark placement until the bespoke font; pairs with U+0348 soft)
_DVLB = "͈"                 # U+0348 combining double vertical line below (soft/palatalised)
_TILDE, _ACUTE = "̃", "́"

# point label -> native base glyph
_CONS = {
    "p": "p", "b": "b", "t": "t", "d": "d", "k": "k", "g": "g",
    "tj": "t" + _VLB, "dj": "d" + _VLB, "kq": "q", "hj": "ḥ",     # t̩ d̩ (palatal line) · q · ḥ = ʔ
    "m": "m", "n": "n", "nj": "n" + _VLB, "nx": "ṇ",              # n̩ (palatal) · ṇ (velar ŋ, x-dot)
    "tc": "c", "dc": "đ", "pc": "p̈",                            # c đ p̈
    "tq": "c" + _VLB, "dq": "đ" + _VLB,                            # c̩ đ̩ (hush = affricate + palatal line)
    "f": "f", "v": "v", "tx": "ṭ", "dx": "ḍ",                  # ṭ ḍ (dental)
    "s": "s", "z": "z", "sj": "s" + _VLB, "zj": "z" + _VLB,        # s̩ z̩ (ʃ ʒ)
    "kx": "ḳ", "gx": "g̣", "hc": "ħ", "hq": "ħ̣", "h": "h",  # ḳ g̣ · hc=ħ (pharyngeal, crossbar) · hq=ʕ (q=c+j: crossbar + underdot) · h
    "l": "l", "lj": "l" + _VLB, "r": "r", "rj": "ṛ",   # l̩ · r (trill) · ṛ (tap, underdot)
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

    def seg_out(seg):
        toks, caps = tokenize_cased(seg, labs.keys())
        return "".join(_cap(labs.get(t, t)) if c else labs.get(t, t) for t, c in zip(toks, caps))
    out = []
    for w in text.split():
        piece, seg = "", ""
        for ch in w:                    # a tone digit closes its segment anywhere in the word
            if ch in _TONE_SUP:
                piece += seg_out(seg) + _TONE_SUP[ch]
                seg = ""
            else:
                seg += ch
        out.append(piece + seg_out(seg))
    return " ".join(out)
