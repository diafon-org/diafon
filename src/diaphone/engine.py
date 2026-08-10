"""One render entry point: notation → any target.

Targets split into two kinds:
  - UNIVERSAL (language-independent, a pure label→glyph map): `ipa`, `native`.
  - LANGUAGE  (a spelling + assembly rules): `en`, `hu`, `zh` (orth in data/orth/<lang>.yaml,
    rules in decode.py).

`render(text, target)` dispatches to the right one so callers don't care which kind it is.
"""
from .loader import load
from .render import to_ipa
from .native import to_native
from .decode import decode

UNIVERSAL = {"ipa": to_ipa, "native": to_native}
LANGUAGES = ("en", "hu", "zh")


def targets():
    return ["ipa", "native", *LANGUAGES]


def render(text, target, data_dir="data", lazy=False):
    """Render a notation string to `target` (a universal repr or a language's spelling)."""
    if target in UNIVERSAL:
        features, _languages, all_ph = load(data_dir)
        return UNIVERSAL[target](text, all_ph, features, data_dir)
    if target in LANGUAGES:
        return decode(text, target, data_dir, lazy=lazy)
    raise ValueError(f"unknown target {target!r}; use one of: {', '.join(targets())}")
