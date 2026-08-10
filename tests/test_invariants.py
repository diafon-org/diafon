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


def test_notation_has_no_unreviewed_collisions():
    """No phoneme's full label may be re-read as a sequence of that language's phonemes, unless the
    ambiguity is a reviewed, accepted one (see notation._ACCEPTED). This is the notation-level cousin
    of injectivity: `ku`=/kʷ/ vs /k/+/u/ was a real collision, now resolved (labialised = `cw`)."""
    from diaphone.notation import find_collisions
    features, languages, all_ph = load(DATA)
    hits = find_collisions(all_ph, features, DATA)
    assert hits == {}, f"unreviewed notation collisions: {hits}"


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
    assert len(folded) == 13, [f[0] for f in folded]
    assert len(general) == len(points) - len(folded)
    assert len(general) == 55, len(general)   # 68 fine - 13 merges; ʌ folded into schwa
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


def test_decode_recovers_hungarian_exactly():
    """Hungarian orthography is near-phonemic, so notation -> spelling must round-trip exactly."""
    from diaphone.decode import decode
    cases = {"sjok sewp njawr": "sok szép nyár",
             "kecsecnecm sewpejn": "köszönöm szépen",
             "ejdj nacdj kutjac": "egy nagy kutya",
             "acswonj": "asszony",      # long /sː/ = sw (one s + long) -> geminated digraph ssz, not szsz
             "hoswuw": "hosszú"}        # w after a consonant geminates it; w after a vowel is part of uw=ú
    for notation, spelling in cases.items():
        assert decode(notation, "hu", DATA) == spelling, (notation, decode(notation, "hu", DATA))


def test_decode_mandarin_tones():
    """A trailing digit on a Mandarin syllable places the Pinyin tone mark (a>e>ou>last vowel)."""
    from diaphone.decode import decode
    assert decode("sjan1 kxyn3 kau1", "zh", DATA) == "shān hěn gāo"
    assert decode("nic3", "zh", DATA) == "nǚ" and decode("he2", "zh", DATA, lazy=True) == "hé"
    assert decode("de5", "zh", DATA) == "de"          # neutral tone: no diacritic


def test_decode_mandarin_finals_and_palatals():
    """Multi-vowel finals and the j/q/x <-> zh/ch/sh split driven by the following vowel."""
    from diaphone.decode import decode
    d = lambda s: decode(s, "zh", DATA)
    assert d("tou1") == "dōu" and d("kxau3") == "hǎo" and d("kuo2") == "guó"   # ou stays ou; au->ao; uo
    # merged retroflex/alveolo-palatal series: front i/ü -> j/q/x (+ ü->u); else zh/ch/sh
    assert d("tqi1") == "jī" and d("sji1") == "xī" and d("tqic1") == "jū" and d("sjic1") == "xū"
    # apical/buzzed vowel `ix` keeps the retroflex spelling: zhī, shì, sì
    assert d("tqix1") == "zhī" and d("sjix4") == "shì" and d("six4") == "sì"


def test_decode_mandarin_lazy_pinyin():
    """Lazy Mandarin = type Pinyin: initials/finals spell literally, incl. p/t/k = aspirated."""
    from diaphone.decode import decode
    z = lambda s: decode(s, "zh", DATA, lazy=True)
    assert z("ni3 hao3") == "nǐ hǎo" and z("xiao3") == "xiǎo" and z("shi4") == "shì"
    assert z("zhong1 guo2") == "zhōng guó" and z("ren2") == "rén" and z("cai4") == "cài"
    assert z("bao3") == "bǎo" and z("dao4") == "dào"                 # lenis stops pass through
    # canonical examples still decode in lazy mode (p/t/k are NOT overridden -> stay lenis notation)
    assert z("sjan1 kxyn3 kau1") == "shān hěn gāo"
    assert decode("pa4", "zh", DATA) == "bà"                          # canonical: bare p = lenis


def test_decode_lazy_mode_aliases():
    """Lazy mode adds free language-specific shortcuts as real labels; canonical omits them."""
    from diaphone.decode import load_orth, decode
    canon = load_orth("hu", DATA)
    lazy = load_orth("hu", DATA, lazy=True)
    assert "a" not in canon and "e" not in canon        # canonical label set excludes the shortcuts
    assert lazy["a"] == "a" and lazy["e"] == "e"          # lazy adds bare a=/ɒ/, e=/ɛ/
    assert decode("alma kert", "hu", DATA, lazy=True) == "alma kert"
    assert decode("acswonj", "hu", DATA) == "asszony"     # canonical path unaffected
