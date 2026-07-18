"""Feature model: base-segment tuples and the modifier layer.

A POINT is a base segment tuple. MODIFIERS are stripped off to obtain it and never
create points. Keep this module tiny and dependency-light; it's the shared vocabulary.
"""
import yaml

# modifier name -> IPA diacritic used when synthesising a surface form
MOD_DIA = {
    "long": "ː",
    "nasal": "\u0303",       # combining tilde
    "palatalized": "ʲ",
    "pharyngealized": "ˤ",
    "labialized": "ʷ",
    "aspirated": "ʰ",
    "rhotic": "\u02de",      # rhotic hook
}


def load_features(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def cbase(p):
    """Consonant base tuple: (kind, place, manner, voice)."""
    return ("C", p["pl"], p["mn"], p["vc"])


def vbase(p):
    """Vowel base tuple: (kind, height, backness, round)."""
    return ("V", p["hi"], p["bk"], bool(p["rd"]))


def strip_mods(ipa):
    """Remove modifier diacritics to recover the base surface form."""
    for d in MOD_DIA.values():
        ipa = ipa.replace(d, "")
    return ipa
