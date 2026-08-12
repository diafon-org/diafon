"""Derive the minimal point set and validate the no-merged-contrast invariant."""
import itertools
import collections

from .model import strip_mods


def derive(all_ph, features):
    """Return (points, violations, near_merges, suspicious).

    points: base_tuple -> {base, kind, canonical_ipa, languages{code:ipa}, modifiers_seen}
    violations: within-language (point, mods) collisions — must be empty
    near_merges: (dist, ipa_a, ipa_b, langs_a, langs_b) — non-co-occurring ≤1-step pairs,
        candidates to fuse across languages
    suspicious: (n_rare, ipa_a, ipa_b, shared_langs) — co-occurring ≤1-step pairs propped up
        by ≤2 languages, candidate allophones-entered-as-phonemes (advisory)
    rhotic: (ipa_a, ipa_b, shared_langs) — cross-manner rhotic pairs that co-occur, minus the
        reviewed r~ɾ contrast; the near-merge finder is blind to these (advisory)
    """
    points = {}
    for code, phs in all_ph.items():
        for ph in phs:
            b = ph["base"]
            rec = points.setdefault(b, {
                "base": b, "kind": ph["kind"],
                "canonical_ipa": strip_mods(ph["ipa"]), "_cm": len(ph["mods"]),
                "languages": {}, "modifiers_seen": set(), "members": set(),
            })
            if len(ph["mods"]) < rec["_cm"]:            # prefer fewest-modifier form
                rec["canonical_ipa"] = strip_mods(ph["ipa"])
                rec["_cm"] = len(ph["mods"])
            rec["languages"].setdefault(code, strip_mods(ph["ipa"]))
            rec["modifiers_seen"] |= set(ph["mods"])
            rec["members"].add((code, frozenset(ph["mods"])))   # exact per-language claims, for merge safety
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
    suspicious = _suspicious_cooccurrence(points, all_ph, features)
    rhotic = _rhotic_cooccurrence(points, all_ph)
    return points, violations, near, suspicious, rhotic


def _dist(a, b, features):
    """Feature-step distance between two base tuples; 99 if not comparable."""
    if a[0] != b[0]:
        return 99
    if a[0] == "C":
        if a[2] != b[2]:                    # different manner -> not adjacent
            return 99
        PLACE = features["consonant"]["place"]
        return abs(PLACE.index(a[1]) - PLACE.index(b[1])) + (a[3] != b[3])
    HEIGHT = features["vowel"]["height"]
    BACK = features["vowel"]["backness"]
    return (abs(HEIGHT.index(a[1]) - HEIGHT.index(b[1]))
            + abs(BACK.index(a[2]) - BACK.index(b[2])) + (a[3] != b[3]))


def _cooccurring(all_ph):
    co = set()
    for phs in all_ph.values():
        bases = {ph["base"] for ph in phs}
        for x, y in itertools.combinations(sorted(bases, key=str), 2):
            co.add(frozenset((x, y)))
    return co


def _near_merges(points, all_ph, features):
    """≤1-step pairs that NEVER co-occur — candidates to fuse across languages."""
    co = _cooccurring(all_ph)
    near = []
    for x, y in itertools.combinations(points, 2):
        d = _dist(x, y, features)
        if d <= 1 and frozenset((x, y)) not in co:
            near.append((d, points[x]["canonical_ipa"], points[y]["canonical_ipa"],
                         sorted(points[x]["languages"]), sorted(points[y]["languages"])))
    near.sort()
    return near


# Co-occurring near-neighbours already reviewed and confirmed as GENUINE contrasts —
# a rare sound one step from a same-language neighbour, but really distinct. Anything that
# trips the filter and is NOT here is a fresh allophone-entered-as-phoneme suspect.
_CONFIRMED_CONTRAST = {
    frozenset(("q", "k")),    # Arabic: uvular vs velar stop (qalb / kalb)
    frozenset(("c", "k")),    # Hungarian: palatal ty vs k
    frozenset(("ɟ", "g")),    # Hungarian: palatal gy vs g
    frozenset(("tʂ", "tɕ")),  # Mandarin: retroflex zh vs alveolo-palatal j
    frozenset(("ħ", "h")),    # Arabic: pharyngeal vs glottal
    frozenset(("ʕ", "ʁ")),    # Arabic: pharyngeal ʿayn vs uvular ghayn
    frozenset(("ɨ", "i")),    # Vietnamese: central vs front close
    frozenset(("ɪ", "i")),    # English/German: lax vs tense KIT / FLEECE
    frozenset(("ʊ", "u")),    # English/German: lax vs tense FOOT / GOOSE
    frozenset(("ʏ", "y")),    # German: lax vs tense rounded close-front
    frozenset(("ʏ", "ø")),    # German: rounded front lax-close vs tense-mid
    frozenset(("œ", "ø")),    # French/German: open-mid vs close-mid rounded front
    frozenset(("æ", "ɛ")),    # English: TRAP vs DRESS
    frozenset(("ɪ", "e")),    # German: lax ɪ vs close-mid e
    frozenset(("ʊ", "o")),    # German: lax ʊ vs close-mid o
    frozenset(("ʂ", "ɕ")),    # Mandarin: retroflex sh vs alveolo-palatal x
}


def _suspicious_cooccurrence(points, all_ph, features, max_rare=2):
    """Co-occurring pairs one PLACE / HEIGHT / BACKNESS step apart (not a bare voice/round
    flip) whose rarer member leans on ≤max_rare languages — a rare sound sitting right next
    to a same-language neighbour. Usually a genuine contrast, occasionally an allophone
    entered as a phoneme (this is how ç~x and ɐ~a surface). Advisory; the reviewed genuine
    contrasts in _CONFIRMED_CONTRAST are filtered out, so what remains wants a look."""
    co = _cooccurring(all_ph)
    out = []
    for x, y in itertools.combinations(points, 2):
        if frozenset((x, y)) not in co or _dist(x, y, features) != 1:
            continue
        structural = (x[1] != y[1]) if x[0] == "C" else (x[1] != y[1] or x[2] != y[2])
        if not structural:
            continue
        ia, ib = points[x]["canonical_ipa"], points[y]["canonical_ipa"]
        if frozenset((ia, ib)) in _CONFIRMED_CONTRAST:
            continue
        na, nb = len(points[x]["languages"]), len(points[y]["languages"])
        if min(na, nb) > max_rare:
            continue
        shared = sorted(set(points[x]["languages"]) & set(points[y]["languages"]))
        out.append((min(na, nb), ia, ib, shared))
    out.sort()
    return out


# Rhotics that co-occur as a reviewed genuine contrast.
_RHOTIC_CONTRAST = {
    frozenset(("r", "ɾ")),   # Spanish alveolar trill vs tap (perro / pero)
}


def _is_rhotic(base):
    """An r-sound: any trill/tap, or an alveolar/retroflex central approximant."""
    return base[0] == "C" and (
        base[2] in ("trill", "tap")
        or (base[2] == "approximant" and base[1] in ("alveolar", "retroflex")))


def _rhotic_cooccurrence(points, all_ph):
    """The near-merge finder only compares SAME-manner points, so it never sees the rhotic
    family (trill / tap / approximant / retroflex). List rhotic pairs that co-occur in some
    language (= a real contrast) minus the reviewed _RHOTIC_CONTRAST — a fresh one is a
    cross-manner rhotic distinction that wants a witness check. Advisory."""
    rho = [k for k in points if _is_rhotic(k)]
    co = _cooccurring(all_ph)
    out = []
    for x, y in itertools.combinations(rho, 2):
        if frozenset((x, y)) not in co:
            continue
        ia, ib = points[x]["canonical_ipa"], points[y]["canonical_ipa"]
        if frozenset((ia, ib)) in _RHOTIC_CONTRAST:
            continue
        shared = sorted(set(points[x]["languages"]) & set(points[y]["languages"]))
        out.append((ia, ib, shared))
    out.sort()
    return out
