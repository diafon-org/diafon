"""One render entry point: notation → any target.

Targets split into two kinds:
  - UNIVERSAL (language-independent, a pure label→glyph map): `ipa`, `native`. `native-<lang>` is a
    language-*flavoured* native view (still the native glyphs, with that language's minor overrides —
    e.g. `native-hu` renders ɑ as plain `a`, giving Hungarian á/a; see native._LANG_OVERRIDE).
  - LANGUAGE  (a spelling + assembly rules): `en`, `hu`, `zh` (orth in data/orth/<lang>.yaml,
    rules in decode.py).

`render(text, target)` dispatches to the right one so callers don't care which kind it is.
"""
from .loader import load
from .render import to_ipa
from .native import to_native, NATIVE_LANGS
from .decode import decode

LANGUAGES = ("en", "hu", "zh")


def targets():
    return ["ipa", "native", *(f"native-{lg}" for lg in NATIVE_LANGS), *LANGUAGES]


def render(text, target, data_dir="data", lazy=False):
    """Render a notation string to `target` (a universal repr or a language's spelling)."""
    native_lang = target[len("native-"):] if target.startswith("native-") else None
    if target in ("ipa", "native") or native_lang in NATIVE_LANGS:
        features, _languages, all_ph = load(data_dir)
        if target == "ipa":
            return to_ipa(text, all_ph, features, data_dir)
        return to_native(text, all_ph, features, data_dir, lang=native_lang)
    if target in LANGUAGES:
        return decode(text, target, data_dir, lazy=lazy)
    raise ValueError(f"unknown target {target!r}; use one of: {', '.join(targets())}")


def export_data(data_dir="data"):
    """The conversion engine as pure data — for ports (the Mac input method, the web page).

    Everything a consumer needs to reproduce `render()`: the label→glyph maps for every universal
    target plus the greedy token order (`keys`), and per language its orthography map, lazy aliases,
    and the two Mandarin tables. The per-language assembly *rules* stay code — they are small,
    documented in decode.py, and a port proves itself by replaying a shared corpus against the CLI
    (tests/test_export.py does exactly that with a minimal consumer built from this data alone).
    """
    from .native import native_labels, _TONE_SUP
    from .render import ipa_labels
    from .decode import load_orth, LAZY_ALIASES, _ZH_RETRO, _TONE_MARKS
    features, _languages, all_ph = load(data_dir)
    maps = {"native": native_labels(all_ph, features, data_dir),
            "ipa": ipa_labels(all_ph, features, data_dir)}
    for lg in NATIVE_LANGS:
        maps[f"native-{lg}"] = native_labels(all_ph, features, data_dir, lang=lg)
    keys = sorted(set().union(*(set(m) for m in maps.values())), key=len, reverse=True)
    return {
        "version": 1,
        "targets": targets(),
        "maps": maps,                                     # universal targets: label -> glyph
        "keys": keys,                                     # greedy (longest-first) token order
        "toneSup": dict(_TONE_SUP),                       # universal: trailing digit -> superscript
        "orth": {lg: load_orth(lg, data_dir) for lg in LANGUAGES},   # language: label -> grapheme
        "lazy": LAZY_ALIASES,                             # loose-input overlays per language
        "zhRetro": _ZH_RETRO,                             # zh: hush initial -> (plain, before-front) spelling
        "toneMarks": _TONE_MARKS,                         # zh: vowel -> tone-marked forms, tones 1-4
    }
