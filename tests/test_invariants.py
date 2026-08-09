"""The load-bearing guardrails. If these fail, the minimal set is invalid."""
import os

from diaphone.loader import load
from diaphone.derive import derive
from diaphone.merges import apply_merges
from diaphone.labeler import load_labels, validate

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _run():
    features, languages, all_ph = load(DATA)
    points, violations, near, suspicious, rhotic = derive(all_ph, features)
    return features, languages, all_ph, points, violations, near, suspicious, rhotic


def test_no_merged_contrasts():
    """No language may map two distinct phonemes to the same (point, modifiers)."""
    violations = _run()[4]
    assert violations == [], violations


def test_mapping_is_injective_per_language():
    """Belt-and-braces: re-check injectivity directly from the phoneme records."""
    _, _, all_ph, *_ = _run()
    for code, phs in all_ph.items():
        keys = [(ph["base"], ph["mods"]) for ph in phs]
        assert len(keys) == len(set(keys)), f"{code} has a merged contrast"


def test_points_nonempty_and_typed():
    points = _run()[3]
    assert len(points) > 0
    kinds = {p["kind"] for p in points.values()}
    assert kinds <= {"C", "V"}


def test_every_language_loads():
    _, languages, *_ = _run()
    assert len(languages) == 16   # 12 core targets + witnesses TR ET VI KO


def test_removed_allophones_absent():
    """ç (German ich-laut), ɸ (Japanese fu), ɐ (German -er) are allophones, not phonemes."""
    points = _run()[3]
    ipas = {p["canonical_ipa"] for p in points.values()}
    assert "ç" not in ipas, "German ç should fold into /x/"
    assert "ɸ" not in ipas, "Japanese ɸ should fold into /h/"
    assert "ɐ" not in ipas, "German -er/Vietnamese ă are not a distinct ɐ point"


def test_no_unreviewed_suspicious_cooccurrence():
    """Mirror of test_no_merged_contrasts: every co-occurring near-neighbour is a reviewed
    genuine contrast (in _CONFIRMED_CONTRAST). A fresh flag = a possible allophone to review."""
    suspicious = _run()[6]
    assert suspicious == [], suspicious


def test_no_unreviewed_rhotic_cooccurrence():
    """Cross-manner rhotic co-occurrences are all reviewed (only Spanish r~ɾ)."""
    rhotic = _run()[7]
    assert rhotic == [], rhotic


def test_general_inventory_ledger():
    """The Phase-2 merge ledger folds cleanly (apply_merges asserts safety) to 58 points."""
    points = _run()[3]
    general, folded = apply_merges(points)
    assert len(folded) == 12, [f[0] for f in folded]
    assert len(general) == len(points) - len(folded)
    assert len(general) == 56, len(general)   # 68 fine - 12 merges (glides /j/ /w/ are not points)
    # source points are gone; targets remain
    assert ("C", "dental", "plosive", "vl") not in general        # t̪ folded into t
    assert ("C", "alveolar", "approximant", "vd") not in general  # ɹ folded into ɻ
    assert ("V", "near-open", "front", False) not in general      # æ folded into a
    assert ("C", "alveolopalatal", "affricate", "vl") not in general  # tɕ folded into tʃ
    assert ("C", "alveolopalatal", "fricative", "vl") not in general  # ɕ folded into ʃ
    assert ("C", "retroflex", "approximant", "vd") in general     # ɻ kept (Dravidian witness)


def test_label_scheme_decided_parts():
    """Labels are unique, namespaces disjoint, and the operator scheme is self-segmenting: every
    base+operator label (sc, tq, kx, tj, …) decodes uniquely. The ONLY labels that decompose are
    the intended cluster-style overlaps — vowel pairs (iu=y) and the trill (rw = long tap). Both
    are monophthong/single-vs-sequence questions for the sequence layer, not decoding failures."""
    labels = load_labels(DATA)
    issues = validate(labels)
    assert issues["duplicates"] == {}, issues["duplicates"]
    assert issues["namespace"] == [], issues["namespace"]
    VOWELS = set("aeiou")
    unexpected = [(i, l) for i, l in issues["ambiguous"]
                  if not (l[0] in VOWELS and l[1] in VOWELS)]   # only the 3 vowel pairs may overlap
    assert unexpected == [], unexpected
