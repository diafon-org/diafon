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
