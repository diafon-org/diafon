"""Load the database and expand every language into modifier-bearing phoneme records.

A phoneme record: {ipa, base, mods(frozenset), kind, lang, orth, st, note}.
"""
import os
import glob
import yaml

from .model import cbase, vbase, MOD_DIA, load_features

# canonical column order; files outside this list are appended alphabetically
ORDER = ["EN", "DE", "ES", "FR", "IT", "LA", "EL", "RU", "AR", "HU", "ZH", "JA",
         "TR", "ET", "VI", "KO"]  # witness languages added after the core 12


def _load_language_files(lang_dir):
    files = {}
    for path in sorted(glob.glob(os.path.join(lang_dir, "*.yaml"))):
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem.startswith("_"):
            continue
        with open(path, encoding="utf-8") as f:
            files[stem.upper()] = yaml.safe_load(f)
    ordered = {c: files[c] for c in ORDER if c in files}
    for c in sorted(files):
        ordered.setdefault(c, files[c])
    return ordered


def expand(code, L):
    """Return the full phoneme list for one language, including expanded series."""
    out = []

    def add(ipa, base, mods, kind, src):
        out.append({
            "ipa": ipa, "base": base, "mods": frozenset(mods), "kind": kind,
            "lang": code, "orth": src.get("orth"),
            "st": src.get("st", "phonemic"), "note": src.get("note"),
        })

    cons = {p["ipa"]: p for p in L.get("consonants", [])}
    vows = {p["ipa"]: p for p in L.get("vowels", [])}

    for p in L.get("consonants", []):
        mods = set(p.get("mod", []))
        if p.get("len"):
            mods.add("long")
        add(p["ipa"], cbase(p), mods, "C", p)
    for p in L.get("vowels", []):
        mods = set(p.get("mod", []))
        if p.get("len"):
            mods.add("long")
        add(p["ipa"], vbase(p), mods, "V", p)

    # same-quality long counterparts
    for ipa in L.get("long_series", []):
        p = vows.get(ipa) or cons.get(ipa)
        if not p:
            raise ValueError(f"{code}: long_series references unknown '{ipa}'")
        is_v = ipa in vows
        add(p["ipa"] + "ː", vbase(p) if is_v else cbase(p),
            {"long"}, "V" if is_v else "C", p)

    # nasalised vowels
    for ipa in L.get("nasal_series", []):
        p = vows[ipa]
        add(p["ipa"] + MOD_DIA["nasal"], vbase(p), {"nasal"}, "V", p)

    # secondary articulations (palatalized / pharyngealized / aspirated / labialized)
    for ser in L.get("secondary_series", []):
        typ = ser["type"]
        for ipa in ser["applies_to"]:
            p = cons[ipa]
            add(p["ipa"] + MOD_DIA[typ], cbase(p), {typ}, "C", p)

    return out


def load(data_dir):
    """Return (features, languages, all_phonemes)."""
    features = load_features(os.path.join(data_dir, "features.yaml"))
    languages = _load_language_files(os.path.join(data_dir, "languages"))
    all_ph = {code: expand(code, L) for code, L in languages.items()}
    return features, languages, all_ph
