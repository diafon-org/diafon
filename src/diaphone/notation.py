"""Notation-level decodability: does any phoneme's full label (point + modifiers) also read as a
*sequence* of the same language's phoneme labels?

The point-label validator in `labeler.py` only asks whether a base-point label splits into other
*base-point* labels — it never weighs a modifier-bearing label against a run of shorter phonemes.
That gap is where a modifier letter would be ambiguous if it were *also* a base segment that can
legally follow. THE LAW: **a modifier letter must never have a phoneme twin.** Every modifier letter
satisfies it — `w`, `j` (no glide phonemes), `y` (not a base), `q`, `c` (never bare) — so no full
label can re-read as a sequence.

`find_collisions` builds each language's real per-phoneme label set (folding fine points into their
general targets, then appending modifier characters) and flags every label that a shorter sequence of
that language's own labels also spells. `_ACCEPTED` holds reviewed, accepted ambiguities; it is EMPTY
and `test_invariants` asserts it stays so.

THE GUARANTEE (absolute): the notation is uniquely decodable (1) per language — a label stream
tokenised against one language's label set has exactly one reading — (2) over the UNIVERSAL
stream — the global label set the uni/ipa targets and the input method tokenise against
(`find_universal_collisions`) — and (3) per label: no string is reachable from two different
(point, modifiers) analyses (`find_shared_labels`). Zero exceptions: greedy tokenisation is provably
unambiguous everywhere. In particular `Ch` is the sequence /C/+/h/ (aspiration is `Cy`: `py ty ky` =
/pʰ tʰ kʰ/), and the Arabic emphatics wear the doubled letter (/tˤ/ = `tyy`, the rarer phenomenon
takes the longer spelling). Anything any finder reports is a real, undecided collision and fails
--strict.

(3) is the one the other two structurally cannot see, and it was not empty: THE DOUBLING RULE
(`doubles`) is derived from labels.yaml rather than enumerated precisely because the enumerated
version drifted — see its docstring.
"""
from .merges import apply_merges
from .labeler import load_labels

# Accepted per-language phoneme/sequence ambiguities, keyed (lang, label). EMPTY by design — the
# modifier-letter law (no phoneme twin) leaves nothing to accept — and it must stay empty: anything
# `find_collisions` reports is a real, undecided collision and fails the invariant.
_ACCEPTED = {}

# The UNIVERSAL-stream counterpart of _ACCEPTED. The per-language check proves each language's label
# stream decodable; the universal targets (uni, ipa, the Mac IM) tokenise against
# the GLOBAL label set — the union of every attested label — where every phoneme letter exists even
# for languages that lack the phoneme, so this is the stricter check. Also EMPTY by design; anything
# `find_universal_collisions` reports is a fresh, undecided collision and fails the invariant.
_ACCEPTED_UNIVERSAL = {}


_POINT_LABELS = {}                 # data_dir -> frozenset of every point label (the doubling input)


def point_labels(data_dir="data"):
    """Every POINT label, read off labels.yaml — the input to the doubling rule below."""
    if data_dir not in _POINT_LABELS:
        labels = load_labels(data_dir)
        _POINT_LABELS[data_dir] = frozenset({**labels["consonants"], **labels["vowels"]}.values())
    return _POINT_LABELS[data_dir]


def doubles(point_label, ch, data_dir="data"):
    """THE DOUBLING RULE for LABELS: **a modifier letter doubles exactly when base+letter is already
    a POINT LABEL**, because then the short form is taken.

    FOUR labels double, and only four. Palatalized: `sj`=/ʃ/ so /sʲ/=`sjj`, and `zj`=/ʒ/ so
    /zʲ/=`zjj`. Retroflex: `tx`=/θ/ and `nx`=/ŋ/ so Tamil ʈ ɳ are `txx nxx`. Everything else stays
    single because nothing occupies the short form — `tj dj nj lj` are the soft coronals outright
    (the palatal points merged into them), `rj` is the soft r (the tap sits on `rc`), and
    `pj kj gj fj vj mj bj lx rx` were always free. Hardcoded lists drift from the data; reading the
    rule off labels.yaml cannot.

    This guards LABEL collisions only. The uni view has its own, separate guard for GLYPH collisions
    (`uni._doubles_glyph`) — the two constraints are not the same, and merging them cost length for
    nothing: Ukrainian ць /tsʲ/ is `tcj`, whose label collides with no point, even though its glyph
    would collide with `tq`=/tʃ/ and therefore doubles its mark.
    """
    if len(ch) != 1:                       # multi-char letters (yy) can never collide
        return False
    return point_label + ch in point_labels(data_dir)


def _mod_chars(mods, point_label, mod_map, data_dir="data"):
    """The modifier suffix for a phoneme, in a stable order, per `doubles` above.

    Order: the segment's own qualities first, **length last** — `w` holds the finished segment, so a
    long soft t is `tjw`, not `twj` (and the uni glyph doubles the finished ț → țț to match). No
    attested phoneme carries two modifiers, so this only ever orders systematic compositions.
    """
    out = ""
    for m in sorted(mods, key=lambda m: (m == "long", m)):
        ch = mod_map.get(m, "?")
        if doubles(point_label, ch, data_dir):
            ch += ch
        out += ch
    return out


# Irregular full labels — reviewed exceptions where plain composition is clunky (cf. the doubling rule).
# The rhotic vowel /ɝ/ (the only one, English NURSE) elides the schwa's x: ax+q -> `aq`. The base stays
# truthfully the schwa point (mid central), so IPA renders /ə˞/ and uni r̈; only the label is short.
_IRREGULAR = {("ax", frozenset({"rhotic"})): "aq"}


def full_label(point_label, mods, mod_map, data_dir="data"):
    """The complete label for (point, modifiers): composed, unless a reviewed irregular applies."""
    irr = _IRREGULAR.get((point_label, frozenset(mods)))
    if irr is not None:
        return irr
    return point_label + _mod_chars(mods, point_label, mod_map, data_dir)


def _label_maps(all_ph, features, data_dir="data"):
    """Return (label_of_base, mod_map): base *tuple* -> general point label, and modifier -> chars.

    A phoneme record carries `base` as the feature tuple (kind, place, manner, voice / height…), the
    same key `points` is indexed by — so we key labels by that tuple, folding each fine point into its
    general target before looking up its character label.

    The fold is resolved over base TUPLES, chain-resolved (ɹ→ɻ→r), exactly as graph.py does it:
    **canonical IPA is not a unique point id.** Two distinct fine points share the string "ʐ" —
    Russian ж (retroflex FRICATIVE) and Mandarin ⟨r⟩ (retroflex APPROXIMANT, zh.yaml) — and the
    ledger sends them to different targets (ʒ and r). Keying the fold by IPA let the last ledger
    entry win, which labelled Russian ж as the trill `r` and left the alveolar approximant with no
    label at all (silently skipping English /ɹ/ in every check below).
    """
    from .derive import derive
    from .merges import LEDGER
    points = derive(all_ph, features)[0]
    apply_merges(points)                  # for its per-language safety assert; the fold below is ours
    fold = {src: tgt for src, tgt, _rec, _note in LEDGER
            if src in points and tgt in points}        # base tuple -> base tuple (inactive pairs skipped)
    labels = load_labels(data_dir)
    by_ipa = {**labels["consonants"], **labels["vowels"]}     # general canonical IPA -> label
    label_of_base = {}
    for base_tuple in points:
        tgt, seen = base_tuple, set()
        while tgt in fold and tgt not in seen:                # chain-resolve: ɹ→ɻ→r
            seen.add(tgt)
            tgt = fold[tgt]
        ipa = points[tgt]["canonical_ipa"]
        if ipa in by_ipa:
            label_of_base[base_tuple] = by_ipa[ipa]
    return label_of_base, labels.get("modifiers", {})


def phoneme_labels(phs, label_of_base, mod_map, data_dir="data"):
    """{full_label: [ipa, …]} for one language's phoneme records."""
    out = {}
    for ph in phs:
        pl = label_of_base.get(ph["base"])
        if pl is None:
            continue
        lab = full_label(pl, ph["mods"], mod_map, data_dir)
        out.setdefault(lab, []).append(ph["ipa"])
    return out


def find_shared_labels(all_ph, features, data_dir="data"):
    """Labels reached from MORE THAN ONE (point, modifiers) analysis — the cross-language cousin of
    the two finders below, and the hole they cannot see.

    Both other finders ask whether a label re-reads as a *sequence*. Neither asks whether one label
    string is produced by two different analyses, because per language it never is (that is derive's
    injectivity invariant) — the ambiguity only appears in the UNIVERSAL stream, where the global set
    unions every language's labels and a shared string collapses to one entry. `sj` is exactly this:
    the hush point /ʃ/ (17 languages) and, without the doubling rule, palatalized /s/ (ET RU UK) —
    one label, two sounds, both rendering ș.

    Returns {label: [(point_label, sorted_mods, sorted_langs), …]} for labels with >1 analysis.
    Two languages spelling the SAME point+modifiers with the same label is the normal case and is
    not reported. Must be empty: anything here is a genuine universal-stream ambiguity.
    """
    label_of_base, mod_map = _label_maps(all_ph, features, data_dir)
    seen = {}                                   # label -> {(point_label, mods): {langs}}
    for lang in sorted(all_ph):
        for ph in all_ph[lang]:
            pl = label_of_base.get(ph["base"])
            if pl is None:
                continue
            key = (pl, tuple(sorted(ph["mods"])))
            seen.setdefault(full_label(pl, ph["mods"], mod_map, data_dir), {}) \
                .setdefault(key, set()).add(lang)
    return {lab: [(pl, list(mods), sorted(langs)) for (pl, mods), langs in sorted(by.items())]
            for lab, by in sorted(seen.items()) if len(by) > 1}


def _resegments(label, labelset):
    """True if `label` splits into >= 2 members of labelset (i.e. a shorter sequence spells it)."""
    n = len(label)
    seg = [False] * (n + 1)
    seg[n] = True
    for i in range(n - 1, -1, -1):
        for w in labelset:
            j = i + len(w)
            if j <= n and label.startswith(w, i) and seg[j]:
                seg[i] = True
                break
    return any(w != label and 0 < len(w) < n and label.startswith(w) and seg[len(w)]
               for w in labelset)


def universal_labels(all_ph, features, data_dir="data"):
    """The GLOBAL label set the universal targets tokenise against: the union of the uni and ipa
    maps' keys (identical to the export's greedy `keys` order). Bare points + every attested
    point+modifier label + the systematic long forms."""
    from .render import ipa_labels          # local: render imports from this module
    from .uni import uni_labels
    return set(ipa_labels(all_ph, features, data_dir)) | set(uni_labels(all_ph, features, data_dir))


def find_universal_collisions(all_ph, features, data_dir="data", include_accepted=False):
    """Labels that a shorter sequence of UNIVERSAL labels also spells — the stream-level cousin of
    `find_collisions`, run over the global set instead of one language's. Greedy longest-match makes
    tokenisation deterministic, but only an empty result here makes it *provably unambiguous*.
    Accepted entries (`_ACCEPTED_UNIVERSAL` — currently none) are excluded unless requested."""
    uni = universal_labels(all_ph, features, data_dir)
    hits = [lab for lab in sorted(uni) if len(lab) >= 2 and _resegments(lab, uni)]
    if not include_accepted:
        hits = [lab for lab in hits if lab not in _ACCEPTED_UNIVERSAL]
    return hits


def find_collisions(all_ph, features, data_dir="data", include_accepted=False):
    """Per language, the phoneme labels a shorter sequence of that language's labels also spells.

    Returns {lang: [(label, sorted_ipas), …]}. Accepted ambiguities in `_ACCEPTED` are excluded
    unless `include_accepted` is set.
    """
    label_of_base, mod_map = _label_maps(all_ph, features, data_dir)
    hits = {}
    for lang in sorted(all_ph):
        labmap = phoneme_labels(all_ph[lang], label_of_base, mod_map, data_dir)
        S = set(labmap)
        found = []
        for lab in sorted(S):
            if len(lab) >= 2 and _resegments(lab, S):
                if not include_accepted and (lang, lab) in _ACCEPTED:
                    continue
                found.append((lab, sorted(set(labmap[lab]))))
        if found:
            hits[lang] = found
    return hits
