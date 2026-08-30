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
    of injectivity: e.g. a hypothetical `ku` label would read /k/+/u/ — modifiers must use the
    operator letters, never vowel letters."""
    from diaphone.notation import find_collisions
    features, languages, all_ph = load(DATA)
    hits = find_collisions(all_ph, features, DATA)
    assert hits == {}, f"unreviewed notation collisions: {hits}"


def test_universal_stream_decodability():
    """The GLOBAL label set (what uni/ipa/the IM tokenise against) must be uniquely decodable —
    per-language decodability alone would let a cross-language ambiguity hide (the global set holds
    every phoneme letter, even for languages that lack the phoneme). The guarantee is ABSOLUTE:
    zero collisions, zero accepted exceptions — the accepted lists are empty and must stay so."""
    from diaphone.notation import find_universal_collisions, _ACCEPTED, _ACCEPTED_UNIVERSAL
    features, languages, all_ph = load(DATA)
    assert _ACCEPTED == {} and _ACCEPTED_UNIVERSAL == {}
    both = find_universal_collisions(all_ph, features, DATA, include_accepted=True)
    assert both == [], f"universal-stream collisions: {both}"


def test_no_label_carries_two_analyses():
    """FOURTH invariant — one label, one (point, modifiers). The two finders above ask whether a
    label re-reads as a *sequence*; neither can see one label string produced by two different
    analyses, because within a language it never is (that's derive's injectivity). The clash lives
    only in the unioned UNIVERSAL stream, and it is real: `sj` is the hush point /ʃ/ (17 languages)
    and would equally be palatalized /s/ (ET/RU/UK), one label and one glyph for two sounds. The
    doubling rule in `_mod_chars` is derived from the point set precisely so this stays empty."""
    from diaphone.notation import find_shared_labels
    features, languages, all_ph = load(DATA)
    shared = find_shared_labels(all_ph, features, DATA)
    assert shared == {}, f"labels with two analyses: {shared}"


def test_label_map_folds_by_tuple_not_canonical_ipa():
    """Canonical IPA is NOT a unique point id — distinct fine points share an IPA string, and the
    ledger may send them to different targets. Folding the label map by IPA let the last entry win,
    which mislabelled one point and left another with no label at all, silently skipping English
    /ɹ/ in every check. Live cases: `t`/`d` name both the dental and the alveolar point, and the
    two retroflex approximant sources both reach the R slot by different routes."""
    from diaphone.notation import _label_maps
    features, languages, all_ph = load(DATA)
    label_of_base, _mods = _label_maps(all_ph, features, DATA)
    assert label_of_base[("C", "dental", "plosive", "vl")] == "t"            # ES/TA t̪ -> folded
    assert label_of_base[("C", "alveolar", "plosive", "vl")] == "t"          # and its target
    assert label_of_base[("C", "alveolar", "approximant", "vd")] == "r"      # EN ɹ -> the R slot
    assert label_of_base[("C", "retroflex", "approximant", "vd")] == "r"     # ZH ⟨r⟩ -> the R slot (ɹ→ɻ→r)
    assert all(label_of_base.get(ph["base"]) for ph in all_ph["EN"]), "every EN phoneme is labelled"


def test_adoption_scale_ends_at_the_universal_view():
    """FIFTH invariant — the adoption scale is CONTINUOUS. A language target with every adoption
    group switched off must equal the `uni` target exactly, so a reader moves from their own
    spelling to the universal one along one scale with nothing else at the end. This is what makes
    the uni-glyph fallback (rather than the raw label) the right choice: any other fallback would
    put a third thing at the end of the ladder."""
    from diaphone.engine import render
    from diaphone.decode import load_groups
    for lang, text in (("hu", "sjok sewp njawr aclmac hoswuw ejdj kisj kutjac"),
                       ("en", "dxax kat sijts acn dxax mat sji sejlz fijsj"),
                       ("zh", "tqonx1kuo2 tqya2 kxaxn3 kxau3 sjiau3 nic3")):
        groups = list(load_groups(lang, DATA))
        assert groups, f"{lang} declares no adoption groups"
        assert render(text, lang, DATA, off=groups) == render(text, "uni", DATA), lang


def test_mapping_is_injective_per_language():
    """Belt-and-braces: re-check injectivity directly from the phoneme records."""
    _, _, all_ph, *_ = _run()
    for code, phs in all_ph.items():
        keys = [(ph["base"], ph["mods"]) for ph in phs]
        assert len(keys) == len(set(keys)), f"{code} has a merged contrast"


def test_a_series_never_drops_the_source_modifiers():
    """`long_series` / `nasal_series` / `secondary_series` must UNION the source phoneme's own
    modifiers, not replace them. Applying `aspirated` to a retroflex ʈ has to give
    {retroflex, aspirated}; taking only {aspirated} silently moves the phoneme onto the plain t
    point, where Hindi's ʈʰ collides with its dental t̪ʰ and the ledger's safety assert fires with
    no hint why. Latent for a long time — Hindi is the first language to apply a series to a
    phoneme that already carries a modifier."""
    from diaphone.loader import expand
    L = {"consonants": [{"ipa": "ʈ", "pl": "alveolar", "mn": "plosive", "vc": "vl",
                         "mod": ["retroflex"]}],
         "secondary_series": [{"type": "aspirated", "applies_to": ["ʈ"]}]}
    got = {ph["ipa"]: ph["mods"] for ph in expand("XX", L)}
    assert got["ʈ"] == frozenset({"retroflex"})
    assert got["ʈʰ"] == frozenset({"retroflex", "aspirated"}), got["ʈʰ"]


def test_modifier_order_is_place_then_rest_then_length():
    """A label spells what modifies what: place-like layers closest to the base, length last.
    Hindi's ʈʰ is `txxy` — a retroflex t, then aspirated — not `tyxx`."""
    from diaphone.notation import _mod_chars, _label_maps
    features, languages, all_ph = load(DATA)
    _lab, mod_map = _label_maps(all_ph, features, DATA)
    assert _mod_chars({"aspirated", "retroflex"}, "t", mod_map, DATA) == "xxy"
    assert _mod_chars({"long", "palatalized"}, "t", mod_map, DATA) == "jw"


def test_points_nonempty_and_typed():
    points = _run()[3]
    assert len(points) > 0
    kinds = {p["kind"] for p in points.values()}
    assert kinds <= {"C", "V"}


def test_every_language_loads():
    _, languages, *_ = _run()
    assert len(languages) == 28   # 12 core + 5 witnesses (TR ET VI KO TA) + 11 coverage (ID FI HE FA NL UK PL TH RO CS HI)


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


def test_no_point_a_modifier_already_spells():
    """FIFTH invariant — the point/modifier boundary holds. A point may not duplicate a combination
    the notation already writes: if a relocating modifier (palatalized, retroflex, pharyngealized)
    turns an attested base into an existing point and no language contrasts the two, they are ONE
    phoneme and must be entered as one. The other finders are all blind to this — they compare a
    point to a point, never a point to a point-plus-a-modifier — and it is why the palatal coronals
    /c ɟ ɲ ʎ/ are /t d n l/ + palatalized and Tamil's ஷ is the hush point, not a retroflex one.
    Reviewed exceptions would live in `_CONFIRMED_MODIFIER_DISTINCT`; there are none."""
    from diaphone.derive import find_modifier_redundant, _CONFIRMED_MODIFIER_DISTINCT
    features, languages, all_ph = load(DATA)
    points = derive(all_ph, features)[0]
    assert _CONFIRMED_MODIFIER_DISTINCT == set()
    both = find_modifier_redundant(points, all_ph, features, include_accepted=True)
    assert both == [], f"points an existing modifier already spells: {both}"


def test_no_unreviewed_rhotic_cooccurrence():
    """Cross-manner rhotic co-occurrences are all reviewed (only Spanish r~ɾ)."""
    rhotic = _run()[7]
    assert rhotic == [], rhotic


def test_general_inventory_ledger():
    """The merge ledger folds cleanly (apply_merges asserts safety)."""
    points = _run()[3]
    general, folded = apply_merges(points)
    assert len(folded) == 13, [f[0] for f in folded]
    assert len(general) == len(points) - len(folded)
    assert len(general) == 49, len(general)   # 62 fine - 13 merges (ʌ→ə, ɒ→ɔ, ɻ→r among them)
    assert ("V", "open", "back", True) not in general             # ɒ folded into ɔ
    # source points are gone; targets remain
    assert ("C", "dental", "plosive", "vl") not in general        # t̪ folded into t
    assert ("C", "alveolar", "approximant", "vd") not in general  # ɹ folded into ɻ (then ɻ→r)
    assert ("V", "near-open", "front", False) not in general      # æ folded into a
    assert ("C", "alveolopalatal", "affricate", "vl") not in general  # tɕ folded into tʃ
    assert ("C", "alveolopalatal", "fricative", "vl") not in general  # ɕ folded into ʃ
    assert ("C", "retroflex", "approximant", "vd") not in general  # ɻ folded into the plain trill r
    assert ("C", "alveolar", "trill", "vd") in general            # the generic R slot (absorbs ɻ/ɹ)


def test_covering_graph_structure():
    """The covering graph (out/graph.json) is well-formed: one node per general point, every
    multi-char label derives from an existing parent point (the structural proof of 'base + ONE
    operator'), the fold edges echo the 15-entry ledger, and adjacency pairs are unique."""
    from diaphone.graph import build_graph
    features, languages, all_ph = load(DATA)
    points = derive(all_ph, features)[0]
    general, folded = apply_merges(points)
    g = build_graph(points, general, load_labels(DATA), features)
    labels = [n["label"] for n in g["nodes"]]
    assert len(labels) == 49 and len(set(labels)) == 49
    # base + ONE operator, structurally: every non-base label has exactly one derivation edge in
    multi = {l for l in labels if len(l) > 1}
    tos = [e["to"] for e in g["edges"]["derivation"]]
    assert sorted(tos) == sorted(multi)
    assert all(e["from"] in set(labels) for e in g["edges"]["derivation"])
    assert len(g["edges"]["fold"]) == 13
    assert all(f["to"] in set(labels) for f in g["edges"]["fold"])
    pairs = [(e["a"], e["b"]) for e in g["edges"]["adjacency"]]
    assert len(pairs) == len(set(pairs)) and all(a != b for a, b in pairs)


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


def test_glides():
    """Glides = nonsyllabic close vowels (x = reduce): ix/ux/icx/ucx. Written explicitly, so
    syllabicity contrasts (RU мой~мои, HU haj~hazai, fiú~*fjú) are representable and protected."""
    from diaphone.engine import render
    assert render("ix ux icx ucx", "ipa", DATA) == "j w ɥ ɰ"     # proper IPA symbols
    assert render("ix ux icx ucx", "uni", DATA) == "j w j̈ ẅ"    # glides carry their vowel's flip mark
    assert render("hacix ixow fiuw ixacix", "hu", DATA) == "haj jó fiú jaj"
    assert render("haciac", "hu", DATA) == "haia"                # written hiatus stays vowel i
    assert render("ixejs uxejst", "en", DATA) == "yes west"
    from diaphone.decode import load_rules
    assert load_rules("hu", DATA) == []      # the i->j heuristics are gone — glides are written


def test_decode_recovers_hungarian_exactly():
    """Hungarian orthography is near-phonemic, so notation -> spelling must round-trip exactly."""
    from diaphone.decode import decode
    cases = {"sjok sewp njawr": "sok szép nyár",
             "hacix ixow": "haj jó",
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
    """One engine renders universal targets (uni/ipa) and languages uniformly."""
    from diaphone.engine import render
    assert render("sjan1", "ipa", DATA) == "ʃan¹"              # superscript tone = IPA only
    assert render("sjan1", "uni", DATA) == "șan1"          # uni keeps the plain digit (no upper-index outside IPA)
    assert render("njawr", "uni", DATA) == "n̦ár"           # nj→ņ, aw→á (long)
    assert render("tyy dyy syy zyy", "uni", DATA) == "t̰ d̰ s̰ z̰"   # emphatics = tilde below (the dark colour)
    assert render("py ty ky", "uni", DATA) == "p̈ ẗ k̈"     # aspirated = two dots, ALWAYS above
    assert render("tcy tqy", "uni", DATA) == "c̈ c̦̈"         # the two dots never move; c̦ keeps its comma below
    assert render("py ty ky", "ipa", DATA) == "pʰ tʰ kʰ"       # aspiration = `y`, which has no phoneme twin
    assert render("aphijl", "ipa", DATA) == "aphɪl"            # ph = the sequence /p/+/h/ (uphill-type words)
    assert render("tx dx kx gx nx", "uni", DATA) == "ṭ ḍ ḳ ġ ṇ"  # x-family = one dot (above on the descender g)
    assert render("pc", "uni", DATA) == "ṗ"                 # pf: the dot above the descender p
    assert render("h hx hj hq", "uni", DATA) == "h ḥ h̦ '"  # every mark follows its operator (x→dot, j→comma); /ʔ/ has no buildable glyph (see uni.py) and takes the apostrophe
    assert render("ax axw aq", "uni", DATA) == "ạ ạ́ r̈"    # schwa = ạ (a + the x-dot); long and rhotic compose
    assert render("TW Tw SJOKK", "uni", DATA) == "TT Tt ȘOKK"   # ALL-CAPS uppercases whole glyphs
    assert render("ey ay oy", "uni", DATA) == "ẽ ã õ"      # nasal = dedicated `y` operator (not h), tilde on cardinals
    assert render("ay", "ipa", DATA) == "ã"
    assert render("aq", "ipa", DATA) == "ə˞" and render("aq", "uni", DATA) == "r̈"  # rhotic ɝ = `aq`; uni = vocalic r̈
    assert render("r rc rj rx aq", "uni", DATA) == "r ṛ r̦ r̖ r̈"   # r-family: trill · tap · soft · retroflex · vocalic — five sounds, five marks, no exception
    assert render("txx nxx lx rx", "uni", DATA) == "t̖ n̖ l̖ r̖"   # retroflex = the "\\" tail (Tamil)
    assert render("rx txx nxx lx", "ipa", DATA) == "ɻ ʈ ɳ ɭ"   # IPA has letters for these: we print them
    assert render("varxi vali valxi", "uni", DATA) == "var̖i vali val̖i"   # Tamil vaḻi~vali~vaḷi
    assert render("aq", "en", DATA) == "er"
    assert render("acswonj", "hu", DATA) == "asszony"          # language target still works (HU a = ac)
    assert render("sjj zjj rj", "uni", DATA) == "s͈ z͈ r̦"   # two commas only where one would spell a point
    #   (ș z̦ = ʃ ʒ); on r the tap sits on `rc`, so the soft r is plain `rj` — one j, one comma
    assert render("pj kj bj", "uni", DATA) == "p̓ k̦ b̦"     # one j = ONE stroke (above on the descender p)
    assert render("tj dj nj lj", "uni", DATA) == "ț d̦ n̦ l̦"  # ONE point each: HU ty = RU ть, ES ñ = RU нь
    assert render("sjw", "uni", DATA) == "șș"               # geminate doubles the WHOLE glyph
    assert render("dj zj tq dq", "uni", DATA) == "d̦ z̦ c̦ x̦"  # uniform j-stroke across the family
    assert render("tc dc", "uni", DATA) == "c x"            # the affricate letter-pair: c /ts/ · x /dz/
    assert render("ic icw uc ucw oc ocw ac acw", "uni", DATA) == "ü ű ï i̋ ë e̋ ä a̋"   # flip + long = the double acute
    assert render("Sjok Sewp Njawr", "uni", DATA) == "Șok Sép N̦ár"   # capitals carry through per token
    assert render("SJOK", "uni", DATA) == "ȘOK"             # all-caps works token-wise
    # a caseless glyph passes the capital to the next one — the ʻokina rule (ʻOahu), since ' has no capital
    assert render("Hqalif hqalif HQALIF", "uni", DATA) == "'Alif 'alif 'ALIF"
    assert render("Sjok", "ipa", DATA) == "ʃok"                # IPA has no capitals — case-insensitive input
    assert render("Acswonj", "hu", DATA) == "Asszony"
    assert render("r rc", "uni", DATA) == "r ṛ"             # trill r / tap ṛ (retroflex merged into r)
    assert render("uc oc ac", "uni", DATA) == "ï ë ä"       # diaeresis flips front↔back (ɯ ɤ ɑ from i e a)
    assert render("ic ec", "uni", DATA) == "ü ö"            # the rounded side of the same rule (y ø from u o)
    assert render("aw ac", "uni", DATA) == "á ä"            # uni keeps ä for ɑ — strictly universal
    assert render("aclmac", "hu", DATA) == "alma"              # HU á/a lives in the hu language target
    assert render("ojw", "uni", DATA) == "ọ́" and render("ojw", "ipa", DATA) == "ɔː"  # oj=ɔ (lowered o); length composes
    import pytest
    with pytest.raises(ValueError):
        render("x", "klingon", DATA)


def test_tone_signs():
    """Tone signs on `uni` (opt-in, off by default): within the LAST vowel group the digit marks
    the first a-based token, else e-based, else o-based, else the LAST vowel (= Pinyin placement);
    0/5 = neutral (digit consumed); vowelless/unmapped digits stay plain."""
    from diaphone.engine import render
    T = lambda t: render(t, "uni", DATA, tones=True)
    assert T("sjan1 kxau3 kuo2 de5") == "șān ḳǎu kuó de"
    assert T("de0") == "de" and render("de0", "uni", DATA) == "de0"          # 0 neutral / plain
    assert T("sjiau3 liu2 tou1") == "șiǎu liú tōu"          # a > o > last (Pinyin placement)
    assert T("nic3") == "nǚ"                                  # sign composes onto ü (ǚ)
    assert render("sjan1", "uni", DATA) == "șan1"            # off by default
    assert T("v2") == "v2"                                     # vowelless segment keeps the digit


def test_notation_to_ipa_universal():
    """Notation renders to language-independent IPA: point labels + modifier diacritics + tone."""
    from diaphone.render import to_ipa
    features, languages, all_ph = load(DATA)
    f = lambda s: to_ipa(s, all_ph, features, DATA)
    assert f("sjan") == "ʃan" and f("tx") == "θ" and f("nj") == "ɲ" and f("kx") == "x"
    # the ipa target is a curated approximation: where IPA writes a point+modifier with a LETTER we
    # print the letter (nj = ɲ, not nʲ), and remaining modifiers compose onto it — length LAST
    assert f("tj dj lj") == "c ɟ ʎ" and f("tjw") == "cː" and f("sjjw") == "sʲː"
    assert f("pya") == "pʰa" and f("tw") == "tː" and f("sjj") == "sʲ" and f("tyy") == "tˤ"
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
    """EN loose INPUT vowels: ee er ay ow aw oy oo uh — orthographic digraphs, respelled."""
    from diaphone.decode import decode
    assert decode("show boy law moon see day", "en", DATA, lazy=True) == "show boy law moon see day"
    assert decode("gud berd", "en", DATA, lazy=True) == "good berd"        # respell stays readable
    assert decode("dxax kat", "en", DATA) == "thu kat"                     # strict respell


def test_decode_lazy_mode_aliases():
    """Lazy mode adds free language-specific shortcuts as real labels; canonical omits them."""
    from diaphone.decode import load_orth, decode
    canon = load_orth("hu", DATA)
    lazy = load_orth("hu", DATA, lazy=True)
    assert "a" not in canon and "e" not in canon        # canonical label set excludes the shortcuts
    assert lazy["a"] == "a" and lazy["e"] == "e"          # lazy adds bare a=/ɒ/, e=/ɛ/
    assert decode("alma kert", "hu", DATA, lazy=True) == "alma kert"
    assert decode("acswonj", "hu", DATA) == "asszony"     # canonical path unaffected
