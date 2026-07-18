"""Derive the minimal point set and validate the no-merged-contrast invariant."""
import itertools
import collections

from .model import strip_mods


def derive(all_ph, features):
    """Return (points, violations, near_merges).

    points: base_tuple -> {base, kind, canonical_ipa, languages{code:ipa}, modifiers_seen}
    violations: within-language (point, mods) collisions — must be empty
    near_merges: (dist, ipa_a, ipa_b, langs_a, langs_b) — optional fusions to review
    """
    points = {}
    for code, phs in all_ph.items():
        for ph in phs:
            b = ph["base"]
            rec = points.setdefault(b, {
                "base": b, "kind": ph["kind"],
                "canonical_ipa": strip_mods(ph["ipa"]), "_cm": len(ph["mods"]),
                "languages": {}, "modifiers_seen": set(),
            })
            if len(ph["mods"]) < rec["_cm"]:            # prefer fewest-modifier form
                rec["canonical_ipa"] = strip_mods(ph["ipa"])
                rec["_cm"] = len(ph["mods"])
            rec["languages"].setdefault(code, strip_mods(ph["ipa"]))
            rec["modifiers_seen"] |= set(ph["mods"])
    for rec in points.values():
        rec.pop("_cm", None)

    # --- invariant: phoneme -> (point, mods) is injective within each language ---
    violations = []
    for code, phs in all_ph.items():
        seen = collections.defaultdict(set)
        for ph in phs:
            seen[(ph["base"], ph["mods"])].add(ph["ipa"])
        for (base, mods), ipas in seen.items():
            if len(ipas) > 1:
                violations.append({"lang": code, "point": base,
                                   "mods": sorted(mods), "phonemes": sorted(ipas)})

    near = _near_merges(points, all_ph, features)
    return points, violations, near


def _near_merges(points, all_ph, features):
    PLACE = features["consonant"]["place"]
    MANNER = features["consonant"]["manner"]
    HEIGHT = features["vowel"]["height"]
    BACK = features["vowel"]["backness"]

    def dist(a, b):
        if a[0] != b[0]:
            return 99
        if a[0] == "C":
            if a[2] != b[2]:                # different manner -> not a merge candidate
                return 99
            return abs(PLACE.index(a[1]) - PLACE.index(b[1])) + (a[3] != b[3])
        return (abs(HEIGHT.index(a[1]) - HEIGHT.index(b[1]))
                + abs(BACK.index(a[2]) - BACK.index(b[2])) + (a[3] != b[3]))

    cooccur = set()
    for phs in all_ph.values():
        bases = {ph["base"] for ph in phs}
        for x, y in itertools.combinations(sorted(bases, key=str), 2):
            cooccur.add(frozenset((x, y)))

    near = []
    for x, y in itertools.combinations(points, 2):
        if dist(x, y) <= 1 and frozenset((x, y)) not in cooccur:
            near.append((dist(x, y), points[x]["canonical_ipa"], points[y]["canonical_ipa"],
                         sorted(points[x]["languages"]), sorted(points[y]["languages"])))
    near.sort()
    return near
