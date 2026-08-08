"""The load-bearing guardrails. If these fail, the minimal set is invalid."""
import os

from diaphone.loader import load
from diaphone.derive import derive

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _run():
    features, languages, all_ph = load(DATA)
    points, violations, near, suspicious = derive(all_ph, features)
    return features, languages, all_ph, points, violations, near, suspicious


def test_no_merged_contrasts():
    """No language may map two distinct phonemes to the same (point, modifiers)."""
    _, _, _, _, violations, _, _ = _run()
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
