"""The load-bearing guardrails. If these fail, the minimal set is invalid."""
import os

from diaphone.loader import load
from diaphone.derive import derive

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _run():
    features, languages, all_ph = load(DATA)
    points, violations, near = derive(all_ph, features)
    return features, languages, all_ph, points, violations, near


def test_no_merged_contrasts():
    """No language may map two distinct phonemes to the same (point, modifiers)."""
    *_, violations, _ = _run()
    assert violations == [], violations


def test_mapping_is_injective_per_language():
    """Belt-and-braces: re-check injectivity directly from the phoneme records."""
    _, _, all_ph, *_ = _run()
    for code, phs in all_ph.items():
        keys = [(ph["base"], ph["mods"]) for ph in phs]
        assert len(keys) == len(set(keys)), f"{code} has a merged contrast"


def test_points_nonempty_and_typed():
    *_, points, _, _ = _run()[:6]
    assert len(points) > 0
    kinds = {p["kind"] for p in points.values()}
    assert kinds <= {"C", "V"}


def test_every_language_loads():
    _, languages, *_ = _run()
    assert len(languages) == 12
