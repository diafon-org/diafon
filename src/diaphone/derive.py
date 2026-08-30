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
    frozenset(("t",)),        # Tamil: dental த vs the alveolar t point (both canonically "t";
                              #   ட is that alveolar point + the retroflex modifier)
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


# A modifier that RELOCATES a segment: the feature it moves, and the value it moves to. These are
# the only modifiers that can make a point redundant — length, aspiration, nasality and rhoticity
# ride on top of a place/manner without relocating it, so they can never spell an existing point.
# (feature index, value moved to, places it may move FROM). The last field matters: palatalization
# is a SECONDARY articulation and does not relocate most segments — Russian /pʲ/ stays bilabial, and
# the data enters it that way. Only on the CORONALS does the secondary palatal swallow the primary
# place, which is why Hungarian ty and Russian ть are worth comparing and /pʲ/ and /c/ are not.
_CORONAL = ("dental", "alveolar", "postalveolar")
_MOD_RELOCATES = {
    "palatalized":    (1, "palatal", _CORONAL),      # base tuple index 1 = place
    "retroflex":      (1, "retroflex", _CORONAL),
    "pharyngealized": (1, "pharyngeal", _CORONAL),
}

# Points a modifier already reaches, REVIEWED and kept distinct anyway. Keyed
# (point_ipa, base_ipa, modifier). Empty until a decision is recorded here.
_CONFIRMED_MODIFIER_DISTINCT = set()


def find_modifier_redundant(points, all_ph, features, include_accepted=False):
    """Points that an existing MODIFIER already spells — the blind spot the other finders share.

    `_near_merges` compares a point to a point; `_suspicious_cooccurrence` compares a point to a
    same-language neighbour. Neither ever compares a point to a *point plus a modifier*, so a point
    can duplicate a combination the notation already writes and nothing notices.

    The test is exact, not a distance heuristic: for a relocating modifier (see `_MOD_RELOCATES`),
    take the attested base Q, move the feature the modifier moves, and ask whether the result IS a
    point P. If it is, and no language has both P and Q+modifier, then nothing holds them apart.
    Feature distance alone is useless here — it would pair /b/ with /p/+aspirated, which differ on
    an axis aspiration does not touch — and neither does a bare relocation rule, which would claim
    Russian /pʲ/ and /kʲ/ reach /c/. They do not; see `_MOD_RELOCATES`.

    This is the witness principle applied across the point/modifier boundary. The system is
    PHONEMIC: that /c/ and /tʲ/ are made differently is a phonetic fact it does not encode, and no
    basis for two points when no language contrasts them.

    Returns [(point_ipa, base_ipa, modifier, langs_of_point, langs_of_combination)].
    """
    bare, modded = {}, {}                       # base tuple -> langs ; (base, mod) -> langs
    for code, phs in all_ph.items():
        for ph in phs:
            if ph["mods"]:
                for m in ph["mods"]:
                    modded.setdefault((ph["base"], m), set()).add(code)
            else:
                bare.setdefault(ph["base"], set()).add(code)
    out = []
    for (q_base, m), qm_langs in modded.items():
        moved = _MOD_RELOCATES.get(m)
        if moved is None or q_base[0] != "C":
            continue
        idx, value, from_places = moved
        if q_base[idx] not in from_places:
            continue
        p_base = q_base[:idx] + (value,) + q_base[idx + 1:]
        if p_base == q_base or p_base not in bare:
            continue                            # the modifier reaches nothing we call a point
        if bare[p_base] & qm_langs:             # a language holds them apart — a real contrast
            continue
        key = (points[p_base]["canonical_ipa"], points[q_base]["canonical_ipa"], m)
        if not include_accepted and key in _CONFIRMED_MODIFIER_DISTINCT:
            continue
        out.append((*key, sorted(bare[p_base]), sorted(qm_langs)))
    out.sort()
    return out


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
