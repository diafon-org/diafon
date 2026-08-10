"""Notation-level decodability: does any phoneme's full label (point + modifiers) also read as a
*sequence* of the same language's phoneme labels?

The point-label validator in `labeler.py` only asks whether a base-point label splits into other
*base-point* labels — it never weighs a modifier-bearing label against a run of shorter phonemes.
That is exactly the gap where `ku`=/kʷ/ collides with /k/+/u/, or `ph`=/pʰ/ with /p/+/h/: a one-letter
modifier is ambiguous precisely when its letter is *also* a base segment that can legally follow. The
pure operators `w` (long) and `j` (palatal) are safe only because the glides /w/ /j/ were removed, so
no standalone phoneme wears those letters.

`find_collisions` builds each language's real per-phoneme label set (folding fine points into their
general targets, then appending modifier characters) and flags every label that a shorter sequence of
that language's own labels also spells. Reviewed, accepted ambiguities live in `_ACCEPTED` with a
verdict; `test_invariants` asserts nothing outside that set survives.
"""
from .merges import apply_merges
from .labeler import load_labels

# Accepted phoneme/sequence ambiguities, each with the reason it is harmless (the near-merge
# "significant witness" principle, applied to notation). Key: (lang, label). Anything NOT here that
# `find_collisions` reports is a real, undecided collision and fails the invariant.
_ACCEPTED = {
    # Aspiration `h` = /Cʰ/ vs /C/+/h/. The two-segment reading only spans a morpheme/word boundary
    # (Korean 국화, Vietnamese compounds); no language contrasts a *tautomorphemic* /Cʰ/ with /C.h/.
    # Aspiration is far too common (Mandarin, Korean, …) to burden with a combo, so we accept it.
    ("KO", "ph"): "aspirated /pʰ/ vs /p/+/h/ — only across a boundary; no tautomorphemic contrast",
    ("KO", "th"): "aspirated /tʰ/ vs /t/+/h/ — boundary only",
    ("KO", "kh"): "aspirated /kʰ/ vs /k/+/h/ — boundary only",
    ("KO", "tqh"): "aspirated affricate /tɕʰ/ vs /tʃ/+/h/ — boundary only, same aspiration family",
    ("VI", "th"): "aspirated /tʰ/ vs /t/+/h/ — boundary only",
    # Rhotic vowel /ɝ/ = `axr` (schwa + rhotic `r`) now re-reads as /ə/+/r/ because English's ⟨r⟩,
    # after the ɻ→r merge, is labelled `r`. Not a real contrast: English does not oppose /ɝ/ to
    # /ə/+/r/ — a tautomorphemic /ər/ IS r-coloured to ɝ; the split is boundary-only. Accepted.
    ("EN", "axr"): "rhotic /ɝ/ vs /ə/+/r/ — non-contrastive in English (ər = ɝ); boundary only",
}


def _mod_chars(mods, point_label, mod_map):
    """The modifier suffix for a phoneme, in a stable order, with the s/z palatalisation exception."""
    out = ""
    for m in sorted(mods):
        ch = mod_map.get(m, "?")
        if m == "palatalized" and point_label in ("s", "z"):
            ch = "jj"                      # sʲ=sjj, zʲ=zjj — because sj/zj are the hush ʃ/ʒ
        out += ch
    return out


def _label_maps(all_ph, features, data_dir="data"):
    """Return (label_of_base, mod_map): base *tuple* -> general point label, and modifier -> chars.

    A phoneme record carries `base` as the feature tuple (kind, place, manner, voice / height…), the
    same key `points` is indexed by — so we key labels by that tuple, folding each fine point into its
    general target before looking up its character label.
    """
    from .derive import derive
    points = derive(all_ph, features)[0]
    general, folded = apply_merges(points)
    fold = {src: tgt for src, tgt, _rec, _note in folded}     # fine canonical IPA -> general canonical
    labels = load_labels(data_dir)
    by_ipa = {**labels["consonants"], **labels["vowels"]}     # general canonical IPA -> label
    label_of_base = {}
    for base_tuple, rec in points.items():
        ipa = rec["canonical_ipa"]
        gen = fold.get(ipa, ipa)
        if gen in by_ipa:
            label_of_base[base_tuple] = by_ipa[gen]
    return label_of_base, labels.get("modifiers", {})


def phoneme_labels(phs, label_of_base, mod_map):
    """{full_label: [ipa, …]} for one language's phoneme records."""
    out = {}
    for ph in phs:
        pl = label_of_base.get(ph["base"])
        if pl is None:
            continue
        lab = pl + _mod_chars(ph["mods"], pl, mod_map)
        out.setdefault(lab, []).append(ph["ipa"])
    return out


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


def find_collisions(all_ph, features, data_dir="data", include_accepted=False):
    """Per language, the phoneme labels a shorter sequence of that language's labels also spells.

    Returns {lang: [(label, sorted_ipas), …]}. Accepted ambiguities in `_ACCEPTED` are excluded
    unless `include_accepted` is set.
    """
    label_of_base, mod_map = _label_maps(all_ph, features, data_dir)
    hits = {}
    for lang in sorted(all_ph):
        labmap = phoneme_labels(all_ph[lang], label_of_base, mod_map)
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
