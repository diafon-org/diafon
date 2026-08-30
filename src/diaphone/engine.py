"""One render entry point: notation → any target.

Targets split into two kinds:
  - UNIVERSAL (language-independent, a pure label→glyph map): `uni` (our view; opt-in tone signs)
    and `ipa` (the why-not reference).
  - LANGUAGE  (one concept per language — input shortcuts + output conversion): `en`, `hu`, `zh`
    (orth + `_rules` in data/orth/<lang>.yaml, interpreted by decode.py).

`render(text, target)` dispatches to the right one so callers don't care which kind it is.
"""
from .loader import load
from .render import to_ipa
from .uni import to_uni
from .decode import decode

LANGUAGES = ("en", "hu", "zh")


def targets():
    return ["ipa", "uni", *LANGUAGES]


def render(text, target, data_dir="data", lazy=False, tones=False, off=()):
    """Render a notation string to `target` (a universal repr or a language's spelling).

    `tones` (uni only): tone digits become tone SIGNS on the vowel (opt-in; off by default).
    `off` (language targets only): the reader's adoption profile — the group names (or labels)
    whose native spelling is switched off, reverting to the universal glyph. All groups off = the
    uni view, so a language target and `uni` are the two ends of one continuous scale."""
    if target in ("ipa", "uni"):
        features, _languages, all_ph = load(data_dir)
        if target == "ipa":
            return to_ipa(text, all_ph, features, data_dir)
        return to_uni(text, all_ph, features, data_dir, tones=tones)
    if target in LANGUAGES:
        return decode(text, target, data_dir, lazy=lazy, off=off)
    raise ValueError(f"unknown target {target!r}; use one of: {', '.join(targets())}")


def export_data(data_dir="data"):
    """The conversion engine as pure data — for ports (the Mac input method, the web page).

    Everything a consumer needs to reproduce `render()`: the label→glyph maps for the universal
    targets plus the greedy token order (`keys`), and per language its orthography map, context
    rules (`rules` — the `_rules` lists from the orth files, so assembly is data too), lazy
    aliases, and the Mandarin tone table. A port proves itself by replaying a shared corpus
    against the CLI (tests/test_export.py does exactly that with a minimal consumer built from
    this data alone — including a generic rule interpreter, ~10 lines).
    """
    from .uni import uni_labels, TONE_SIGNS
    from .render import ipa_labels, _TONE_SUP
    from .decode import load_orth, load_rules, load_lazy, load_groups, _TONE_MARKS
    features, _languages, all_ph = load(data_dir)
    maps = {"uni": uni_labels(all_ph, features, data_dir),
            "ipa": ipa_labels(all_ph, features, data_dir)}
    keys = sorted(set().union(*(set(m) for m in maps.values())), key=len, reverse=True)
    return {
        "version": 2,
        "targets": targets(),
        "maps": maps,                                     # universal targets: label -> glyph
        "keys": keys,                                     # greedy (longest-first) token order
        "toneSup": dict(_TONE_SUP),                       # digit -> superscript — IPA target ONLY
        "toneSigns": dict(TONE_SIGNS),                    # digit -> combining tone sign (uni, opt-in;
                                                          #   0/5 neutral; Pinyin-priority placement)
        "orth": {lg: load_orth(lg, data_dir) for lg in LANGUAGES},   # language: label -> grapheme
        "rules": {lg: load_rules(lg, data_dir) for lg in LANGUAGES}, # language: ordered context rules
        "lazy": {lg: load_lazy(lg, data_dir) for lg in LANGUAGES},   # loose-input overlays
        "groups": {lg: load_groups(lg, data_dir) for lg in LANGUAGES},  # adoption groups
        "toneMarks": _TONE_MARKS,                         # zh: vowel -> tone-marked forms, tones 1-4
    }
