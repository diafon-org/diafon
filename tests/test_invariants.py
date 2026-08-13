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
    """The Phase-2 merge ledger folds cleanly (apply_merges asserts safety)."""
    points = _run()[3]
    general, folded = apply_merges(points)
    assert len(folded) == 15, [f[0] for f in folded]
    assert len(general) == len(points) - len(folded)
    assert len(general) == 53, len(general)   # 68 fine - 15 merges (ʌ→ə, ɒ→ɔ, ɻ→r among them)
    assert ("V", "open", "back", True) not in general             # ɒ folded into ɔ
    # source points are gone; targets remain
    assert ("C", "dental", "plosive", "vl") not in general        # t̪ folded into t
    assert ("C", "alveolar", "approximant", "vd") not in general  # ɹ folded into ɻ (then ɻ→r)
    assert ("V", "near-open", "front", False) not in general      # æ folded into a
    assert ("C", "alveolopalatal", "affricate", "vl") not in general  # tɕ folded into tʃ
    assert ("C", "alveolopalatal", "fricative", "vl") not in general  # ɕ folded into ʃ
    assert ("C", "retroflex", "approximant", "vd") not in general  # ɻ folded into the plain trill r
    assert ("C", "alveolar", "trill", "vd") in general            # the generic R slot (absorbs ɻ/ɹ)


def test_label_scheme_decided_parts():
    """Labels are unique, namespaces disjoint, and the operator scheme is self-segmenting: every
    base+operator label (tc, tq, kx, tj, …) decodes uniquely; nothing should decompose ambiguously."""
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
             "ejdj nacdj kutjac": "egy nagy kutya",   # HU short a = /ɒ/ -> ɑ = `ac` (HU á/a = a/ac)
             "acswonj": "asszony",     # long /sː/ = sw -> geminated digraph ssz, not szsz
             "hoswuw": "hosszú"}        # w after a consonant geminates it; w after a vowel is part of uw=ú
    for notation, spelling in cases.items():
        assert decode(notation, "hu", DATA) == spelling, (notation, decode(notation, "hu", DATA))


def test_decode_mandarin_tones():
    """A trailing digit on a Mandarin syllable places the Pinyin tone mark (a>e>ou>last vowel)."""
    from diaphone.decode import decode
    assert decode("sjan1 kxaxn3 kau1", "zh", DATA) == "shān hěn gāo"
    assert decode("nic3", "zh", DATA) == "nǚ" and decode("he2", "zh", DATA, lazy=True) == "hé"
    assert decode("de5", "zh", DATA) == "de"          # neutral tone: no diacritic


def test_engine_render_targets():
    """One engine renders universal targets (ipa/native) and languages uniformly."""
    from diaphone.engine import render
    assert render("sjan1", "ipa", DATA) == "ʃan¹"
    assert render("sjan1", "native", DATA) == "șan¹"          # native view (palatal = precomposed comma family)
    assert render("njawr", "native", DATA) == "ņár"           # nj→ņ, aw→á (long)
    assert render("ty", "native", DATA) == "t̤"                # pharyngealised = `y` on a consonant (two dots below)
    assert render("nx", "native", DATA) == "ṇ"                # velar nasal ŋ = x-operator dot-below (like ṭ ḳ)
    assert render("h hj hc hq", "native", DATA) == "h ḥ ħ ħ̣"  # guttural 2×2 (c/j/q): c=pharyngeal, j=marked, q=c+j
    assert render("ey ay oy", "native", DATA) == "ẽ ã õ"      # nasal = dedicated `y` operator (not h), tilde on cardinals
    assert render("ay", "ipa", DATA) == "ã"
    assert render("aq", "ipa", DATA) == "ə˞" and render("aq", "native", DATA) == "ṙ"  # rhotic ɝ = `aq`; native = vocalic r, dot above
    assert render("r rj aq", "native", DATA) == "r ṛ ṙ"        # the r-family: trill · tap (dot below) · rhotic vowel (dot above)
    assert render("aq", "en", DATA) == "er"
    assert render("acswonj", "hu", DATA) == "asszony"          # language target still works (HU a = ac)
    assert render("sjj zjj", "native", DATA) == "s͈ z͈"        # palatalised s/z = U+0348 double vertical line below
    assert render("pj kj", "native", DATA) == "p͈ k͈"          # soft (palatalised) consonants: U+0348
    assert render("tj nj", "native", DATA) == "ț ņ"            # coronal soft = palatal points (precomposed)
    assert render("sjw", "native", DATA) == "șș"               # geminate doubles the WHOLE glyph
    assert render("r rj", "native", DATA) == "r ṛ"             # trill r / tap ṛ (retroflex merged into r)
    assert render("uc oc ac", "native", DATA) == "ï ë ä"       # diaeresis flips front↔back (ɯ ɤ ɑ from i e a)
    assert render("ic ec", "native", DATA) == "ü ö"            # the rounded side of the same rule (y ø from u o)
    assert render("aw ac", "native", DATA) == "á ä"            # universal native keeps ä for ɑ
    assert render("aw ac", "native-hu", DATA) == "á a"         # HU-flavoured native: ɑ→a (HU has no base /a/) → á/a
    assert render("aclmac", "native-hu", DATA) == "alma"       # so Hungarian words read naturally
    assert render("ojw", "native", DATA) == "ọ́" and render("ojw", "ipa", DATA) == "ɔː"  # oj=ɔ (lowered o); length composes
    import pytest
    with pytest.raises(ValueError):
        render("x", "klingon", DATA)


def test_notation_to_ipa_universal():
    """Notation renders to language-independent IPA: point labels + modifier diacritics + tone."""
    from diaphone.render import to_ipa
    features, languages, all_ph = load(DATA)
    f = lambda s: to_ipa(s, all_ph, features, DATA)
    assert f("sjan") == "ʃan" and f("tx") == "θ" and f("nj") == "ɲ" and f("kx") == "x"
    assert f("pha") == "pʰa" and f("tw") == "tː" and f("sjj") == "sʲ" and f("ty") == "tˤ"
    assert f("kcw"[:2]) == "kʷ"                       # labialised k
    assert f("sjan1") == "ʃan¹"                        # trailing tone digit -> superscript


def test_decode_mandarin_finals_and_palatals():
    """Multi-vowel finals and the j/q/x <-> zh/ch/sh split driven by the following vowel."""
    from diaphone.decode import decode
    d = lambda s: decode(s, "zh", DATA)
    assert d("tou1") == "dōu" and d("kxau3") == "hǎo" and d("kuo2") == "guó"   # ou stays ou; au->ao; uo
    # merged retroflex/alveolo-palatal series: front i/ü -> j/q/x (+ ü->u); else zh/ch/sh
    assert d("tqi1") == "jī" and d("sji1") == "xī" and d("tqic1") == "jū" and d("sjic1") == "xū"
    # apical/buzzed vowel `uc` keeps the retroflex spelling: zhī, shì, sì
    assert d("tquc1") == "zhī" and d("sjuc4") == "shì" and d("suc4") == "sì"


def test_decode_mandarin_lazy_pinyin():
    """Lazy Mandarin = type Pinyin: initials/finals spell literally, incl. p/t/k = aspirated."""
    from diaphone.decode import decode
    z = lambda s: decode(s, "zh", DATA, lazy=True)
    assert z("ni3 hao3") == "nǐ hǎo" and z("xiao3") == "xiǎo" and z("shi4") == "shì"
    assert z("zhong1 guo2") == "zhōng guó" and z("ren2") == "rén" and z("cai4") == "cài"
    assert z("bao3") == "bǎo" and z("dao4") == "dào"                 # lenis stops pass through
    # canonical examples still decode in lazy mode (p/t/k are NOT overridden -> stay lenis notation)
    assert z("sjan1 kxaxn3 kau1") == "shān hěn gāo"
    assert decode("pa4", "zh", DATA) == "bà"                          # canonical: bare p = lenis


def test_en_simplified_input_aliases():
    """EN loose INPUT: familiar digraphs (sh ch zh ng th dh) + bare j/y/w — free letters in English."""
    from diaphone.decode import decode
    assert decode("shijp fijsh", "en", DATA, lazy=True) == "ship fish"
    assert decode("sjijp", "en", DATA, lazy=True) == "ship"                # canonical still decodes


def test_en_simplified_vowels():
    """EN loose INPUT vowels: ee er ay ow aw oy oo uh — orthographic digraphs, dict-canonicalised."""
    from diaphone.decode import decode
    assert decode("berd werld", "en", DATA, lazy=True, endict=True) == "bird world"
    assert decode("show boy law moon see day", "en", DATA, lazy=True, endict=True) == "show boy law moon see day"
    assert decode("dhuh kat sijts awn dhuh flawr", "en", DATA, lazy=True, endict=True) == "the cat sits on the floor"
    assert decode("gud berd", "en", DATA, lazy=True) == "good berd"        # respell fallback stays readable


def test_en_dictionary_view():
    """EN dictionary view (--dict): real words where known, respell otherwise; aliases canonicalise."""
    from diaphone.decode import decode
    assert decode("dxax kat sijts acn", "en", DATA, endict=True) == "the cat sits on"
    assert decode("dhax kat", "en", DATA, endict=True) == "the cat"        # typed with aliases -> same words
    assert decode("haxlo uaqld", "en", DATA, endict=True) == "hello world"
    assert decode("waqld yejlo", "en", DATA, lazy=True, endict=True) == "world yellow"
    assert decode("zorgblat dxax", "en", DATA, endict=True) == "zowrgblat the"  # unknown -> respell fallback
    assert decode("dxax kat", "en", DATA) == "thu kat"                     # strict unchanged


def test_decode_lazy_mode_aliases():
    """Lazy mode adds free language-specific shortcuts as real labels; canonical omits them."""
    from diaphone.decode import load_orth, decode
    canon = load_orth("hu", DATA)
    lazy = load_orth("hu", DATA, lazy=True)
    assert "a" not in canon and "e" not in canon        # canonical label set excludes the shortcuts
    assert lazy["a"] == "a" and lazy["e"] == "e"          # lazy adds bare a=/ɒ/, e=/ɛ/
    assert decode("alma kert", "hu", DATA, lazy=True) == "alma kert"
    assert decode("acswonj", "hu", DATA) == "asszony"     # canonical path unaffected
