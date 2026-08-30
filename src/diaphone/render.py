"""Universal output targets: render a notation string into a language-independent form.

`decode.py` turns notation into a *specific language's* spelling. This module renders the
*universal* view instead — IPA, the why-not reference. Everything keys off the general point set +
`labels.yaml`, so there is no per-language orthography involved.

**The IPA target is an APPROXIMATION, and deliberately so.** Our unit is a phonemic point plus
modifiers; IPA's unit is a phonetic segment, and the two do not line up one-to-one — a point covers
every realisation its languages give it (the R slot is trill, tap, approximant and uvular at once).
So this module is a curated table, not a translation: one IPA rendering per label, chosen to be what
a reader of IPA expects. Every point has one, and where IPA has a LETTER for a point+modifier
combination we print the letter rather than composing a diacritic (`nj` is ɲ, not nʲ; `txx` is ʈ) —
see `_SEGMENT_IPA`. Nothing about the point set follows from these choices; they are rendering only.

Mechanically it is the inverse of the labeller: each point label maps back to its general point's
canonical IPA, and each modifier char becomes an IPA diacritic or is absorbed into a letter. A
trailing tone digit becomes a superscript. Greedy longest-match tokenisation makes modifier-bearing
labels (sjj=sʲ) win over their bare-point prefixes (sj=ʃ).
"""
import unicodedata

from .decode import tokenize, tokenize_cased
from .labeler import load_labels
from .notation import _label_maps, _mod_chars, full_label

# modifier feature -> IPA diacritic (combining marks for nasal/rhotic sit after the base char)
_MOD_IPA = {"long": "ː", "palatalized": "ʲ", "aspirated": "ʰ",
            "nasal": "̃", "rhotic": "˞", "pharyngealized": "ˤ", "retroflex": "̢",
            "nonsyllabic": "̯"}
# glides get their proper IPA symbols (not the compositional /i̯/): reduced close vowels
_GLIDE_IPA = {"ix": "j", "ux": "w", "icx": "ɥ", "ucx": "ɰ"}
# (point label, modifier) -> the IPA LETTER for that combination. Where IPA writes a segment with a
# symbol of its own we print it instead of point+diacritic: the palatal coronals (our `tj dj nj lj`
# are one point each, IPA's c ɟ ɲ ʎ) and the retroflex series (Tamil). This is the approximation the
# module docstring describes — it changes nothing in the analysis, only what the reference target
# shows. Remaining modifiers still compose onto the letter, so `tjw` is cː.
_SEGMENT_IPA = {
    ("t", "palatalized"): "c", ("d", "palatalized"): "ɟ",
    ("n", "palatalized"): "ɲ", ("l", "palatalized"): "ʎ",
    ("t", "retroflex"): "ʈ", ("d", "retroflex"): "ɖ", ("n", "retroflex"): "ɳ",
    ("l", "retroflex"): "ɭ", ("r", "retroflex"): "ɻ",
    ("sj", "retroflex"): "ʂ", ("zj", "retroflex"): "ʐ",
    ("tq", "retroflex"): "tʂ", ("dq", "retroflex"): "dʐ",
}


def _compose_ipa(point_label, mods, base_ipa):
    """point + modifiers -> IPA: a letter from _SEGMENT_IPA if one covers a modifier, else the
    point's symbol; every remaining modifier appends its diacritic."""
    rest = set(mods)
    core = base_ipa
    for m in sorted(rest):
        letter = _SEGMENT_IPA.get((point_label, m))
        if letter:
            core, rest = letter, rest - {m}
            break
    # same order as the label: place-like first, length last (`sjjw` = sʲː, not sːʲ)
    from .notation import _mod_order
    return core + "".join(_MOD_IPA.get(m, "") for m in sorted(rest, key=_mod_order))
_TONE_SUP = {"1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵"}


def ipa_labels(all_ph, features, data_dir="data"):
    """{notation_label: universal IPA} — every bare point plus every attested point+modifier label."""
    label_of_base, mod_map = _label_maps(all_ph, features, data_dir)
    by_ipa = {**load_labels(data_dir)["consonants"], **load_labels(data_dir)["vowels"]}
    base2ipa = {lab: ipa for ipa, lab in by_ipa.items()}     # general point label -> canonical IPA
    out = dict(base2ipa)
    seen_mods = set()                       # (point label, modifiers) actually attested
    for phs in all_ph.values():
        for ph in phs:
            pl = label_of_base.get(ph["base"])
            if pl is None:
                continue
            if ph["mods"]:
                seen_mods.add((pl, frozenset(ph["mods"])))
            full = full_label(pl, ph["mods"], mod_map, data_dir)
            # setdefault: a modifier label that coincides with a point label (tʲ=`tj`, nʲ=`nj`)
            # keeps the POINT's IPA — same rule as uni_labels, and order-independent
            out.setdefault(full, _GLIDE_IPA.get(full) or
                           _compose_ipa(pl, ph["mods"], base2ipa[pl]))
    for pl in ("sj", "zj", "tq", "dq"):          # the systematic retroflex layer (see uni.py)
        seen_mods.add((pl, frozenset({"retroflex"})))
        out.setdefault(full_label(pl, {"retroflex"}, mod_map, data_dir),
                       _compose_ipa(pl, {"retroflex"}, base2ipa[pl]))

    # Systematic long forms so an unattested length composes instead of leaking a `w`: for every
    # point (`ojw`=ɔː) and for every attested point+modifier (`tjw`=cː). Same for the four glides,
    # so an unattested one (ucx=ɰ) still renders.
    for pl, mods in [(p, frozenset()) for p in base2ipa] + sorted(seen_mods):
        out.setdefault(full_label(pl, mods | {"long"}, mod_map, data_dir),
                       _compose_ipa(pl, mods | {"long"}, base2ipa[pl]))
    for lab, g in _GLIDE_IPA.items():
        out.setdefault(lab, g)
    return {lab: unicodedata.normalize("NFC", ipa) for lab, ipa in out.items()}  # precompose (a+̃ → ã)


def to_ipa(text, all_ph, features, data_dir="data"):
    """Render a notation string as universal IPA (space-separated words; trailing digit = tone)."""
    labs = ipa_labels(all_ph, features, data_dir)

    def seg_out(seg):
        toks, _caps = tokenize_cased(seg, labs.keys())   # case-insensitive input; IPA has no capitals
        return "".join(labs.get(t, t) for t in toks)
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
