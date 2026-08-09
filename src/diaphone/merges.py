"""Phase-2 merge ledger: the decided fusions of fine-grained points into the general inventory.

Each entry folds a `source` base tuple into a `target`; `recover` names the feature/diacritic
that restores the source's realisation (None = sub-phonemic everywhere, no recovery mark needed).
Every merge is witness-decided (see CLAUDE.md "Decision gate") and invariant-safe: no language
co-occurs a source with its target, so folding never collapses a within-language contrast —
`apply_merges` asserts this.

The three consonant place features (dental, retroflex, uvular) all recover with the **underdot**
(one diacritic, "the marked exotic congener of this base letter"); each base letter has at most
one such congener, so the underdot is unambiguous per letter. Vowel `centralized` is a separate
vowel diacritic. Actual character assignment is the rest of Phase 2.
"""

# (source_base, target_base, recover, note)
LEDGER = [
    (("C", "dental", "plosive", "vl"),       ("C", "alveolar", "plosive", "vl"),       None, "t̪→t; only exotic Venda contrasts them, none of the 16"),
    (("C", "dental", "plosive", "vd"),       ("C", "alveolar", "plosive", "vd"),       None, "d̪→d; same"),
    (("C", "retroflex", "fricative", "vl"),  ("C", "postalveolar", "fricative", "vl"), None, "ʂ→ʃ; Mandarin sh/x are COMPLEMENTARY (allophones), not a contrast — no sign needed"),
    (("C", "retroflex", "fricative", "vd"),  ("C", "postalveolar", "fricative", "vd"), None, "ʐ→ʒ; Russian ж retroflex ≈ postalveolar, no contrast"),
    (("C", "retroflex", "affricate", "vl"),  ("C", "postalveolar", "affricate", "vl"), None, "tʂ→tʃ; Mandarin zh/j complementary, no contrast"),
    (("C", "alveolopalatal", "fricative", "vl"),  ("C", "postalveolar", "fricative", "vl"),  None, "ɕ→ʃ; postalveolar~alveolo-palatal never contrast"),
    (("C", "alveolopalatal", "affricate", "vl"),  ("C", "postalveolar", "affricate", "vl"),  None, "tɕ→tʃ; the 'ch' point"),
    (("C", "alveolopalatal", "affricate", "vd"),  ("C", "postalveolar", "affricate", "vd"),  None, "dʑ→dʒ; voiced 'ch'"),
    (("C", "uvular", "fricative", "vd"),     ("C", "velar", "fricative", "vd"),        None, "ʁ→ɣ; only exotic Tsakhur/Kabardian contrast them"),
    (("C", "alveolar", "approximant", "vd"), ("C", "retroflex", "approximant", "vd"), None,         "English ɹ ≈ Mandarin ɻ; no language contrasts them"),
    (("V", "near-open", "front", False),     ("V", "open", "central", False),        None,          "æ→a; no witness (Danish resolves to æ~back ɑ)"),
    (("V", "close", "central", False),       ("V", "close", "back", False),          "centralized", "ɨ→ɯ; no significant witness (major langs have one or the other)"),
]


def apply_merges(points):
    """Fold ledger sources into their targets. Returns (general, folded).

    general: dict like `points` (base_tuple -> record) with sources removed; each target that
        absorbed a source carries `recovered`: [{ipa, recover, langs}]. Language maps are unioned.
    folded: [(source_ipa, target_ipa, recover, note)] for entries actually applied (a source or
        target absent from `points` — e.g. inactive f~ɸ — is skipped).
    """
    general = {}
    for k, v in points.items():
        general[k] = {**v, "languages": dict(v["languages"]),
                      "modifiers_seen": set(v.get("modifiers_seen", set())),
                      "recovered": list(v.get("recovered", []))}
    # Safety is per (target, recovery-mark), not raw co-occurrence: a source may share a language
    # with its target as long as their marks differ (so they stay distinct within that language).
    # E.g. Mandarin ʂ→ʃ (underdot) and ɕ→ʃ (plain) both land on ʃ but never collapse — sh keeps
    # the underdot, x does not. Two members with the SAME mark in one language WOULD collapse.
    claimed = {}                       # target_key -> {(lang, mark)}
    def _claims(k):
        if k not in claimed:
            claimed[k] = {(lg, None) for lg in general[k]["languages"]}  # the target's own members
        return claimed[k]
    folded = []
    for src, tgt, rec, note in LEDGER:
        if src not in general or tgt not in general:
            continue
        cl = _claims(tgt)              # capture target's claims BEFORE folding this source in
        s = general.pop(src)
        t = general[tgt]
        for code in s["languages"]:
            key = (code, rec)
            assert key not in cl, \
                f"unsafe merge: {s['canonical_ipa']}→{t['canonical_ipa']} collides in {code} " \
                f"(both would be {t['canonical_ipa']} + {rec})"
            cl.add(key)
        for code, ipa in s["languages"].items():
            t["languages"].setdefault(code, ipa)
        t["modifiers_seen"] |= s["modifiers_seen"]
        t["recovered"].append({"ipa": s["canonical_ipa"], "recover": rec,
                               "langs": sorted(s["languages"])})
        folded.append((s["canonical_ipa"], t["canonical_ipa"], rec, note))
    return general, folded
