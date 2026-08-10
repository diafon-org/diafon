"""Universal output targets: render a notation string into a language-independent form.

`decode.py` turns notation into a *specific language's* spelling. This module renders the
*universal* view instead — currently IPA (the diaphonemic phonemes themselves), later a "nice"
diaphone glyph repr / latin22 profile. Everything keys off the general point set + `labels.yaml`, so
there is no per-language orthography involved.

notation label -> IPA is just the inverse of the labeller: each point label maps back to its general
point's canonical IPA, and each modifier char becomes an IPA diacritic. A trailing tone digit becomes
a superscript. Greedy longest-match tokenisation makes modifier-bearing labels (sjj=sʲ, kc=kʷ) win
over their bare-point prefixes (sj=ʃ, k=k).
"""
from .decode import tokenize
from .labeler import load_labels
from .notation import _label_maps, _mod_chars

# modifier feature -> IPA diacritic (combining marks for nasal/rhotic sit after the base char)
_MOD_IPA = {"long": "ː", "palatalized": "ʲ", "aspirated": "ʰ", "labialized": "ʷ",
            "nasal": "̃", "rhotic": "˞", "pharyngealized": "ˤ"}
_TONE_SUP = {"1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵"}


def ipa_labels(all_ph, features, data_dir="data"):
    """{notation_label: universal IPA} — every bare point plus every attested point+modifier label."""
    label_of_base, mod_map = _label_maps(all_ph, features, data_dir)
    by_ipa = {**load_labels(data_dir)["consonants"], **load_labels(data_dir)["vowels"]}
    base2ipa = {lab: ipa for ipa, lab in by_ipa.items()}     # general point label -> canonical IPA
    out = dict(base2ipa)
    for phs in all_ph.values():
        for ph in phs:
            pl = label_of_base.get(ph["base"])
            if pl is None:
                continue
            full = pl + _mod_chars(ph["mods"], pl, mod_map)
            out[full] = base2ipa[pl] + "".join(_MOD_IPA.get(m, "") for m in sorted(ph["mods"]))
    return out


def to_ipa(text, all_ph, features, data_dir="data"):
    """Render a notation string as universal IPA (space-separated words; trailing digit = tone)."""
    labs = ipa_labels(all_ph, features, data_dir)
    words = []
    for w in text.split():
        tone = ""
        if len(w) > 1 and w[-1] in _TONE_SUP:
            tone, w = _TONE_SUP[w[-1]], w[:-1]
        words.append("".join(labs.get(t, t) for t in tokenize(w, labs.keys())) + tone)
    return " ".join(words)
