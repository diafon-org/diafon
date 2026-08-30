"""The covering graph as a first-class artifact (out/graph.json).

One explicit node set carrying the three edge structures that otherwise live apart (the
feature-adjacency metric in `derive._dist`, the fine→general folds in `merges.LEDGER`, the
base+operator derivations inside `labels.yaml`'s strings) — so questions about the inventory,
above all "what does adding a language touch?", are answered by a graph diff.

Nodes: the general points (one per label), carrying features, canonical IPA and the languages that
use them. Edges, three kinds:
  - derivation: every multi-char label is parent-label + ONE operator (`sj` = s + j). Built by
    parsing the labels themselves, so this *structurally proves* the "base + ONE operator" claim —
    a label whose prefix is not itself a point label fails `build_graph`.
  - adjacency: general points one feature step apart (`derive._dist` == 1) — the same metric the
    near-merge and allophone finders walk.
  - fold: the merge ledger, fine point → general point with its recovery mark.
"""
from .derive import _dist
from .merges import LEDGER


def build_graph(points, general, labels, features):
    """Return the covering graph as a plain dict (JSON-ready).

    points: the fine-grained point dict (for the fold sources' identity); general: the post-merge
    point dict; labels: the labels.yaml dict; features: the feature scales (drives adjacency).

    Fold edges come from the base-tuple LEDGER, not apply_merges' IPA echo — canonical IPA strings
    are NOT unique point identifiers (dental t̪ and alveolar t both print 't'; the retroflex
    approximant's canonical is 'ʐ', same as the retroflex fricative's), and the ledger chains
    (ɹ → retroflex approximant → r), so each edge is resolved to its FINAL general node.
    """
    by_ipa = {**labels.get("consonants", {}), **labels.get("vowels", {})}   # canonical IPA -> label

    nodes = []
    label_of = {}                                    # base tuple -> label
    for base, rec in general.items():
        lab = by_ipa.get(rec["canonical_ipa"])
        assert lab, f"general point {rec['canonical_ipa']} has no label"
        label_of[base] = lab
        feats = ({"place": base[1], "manner": base[2], "voice": base[3]} if rec["kind"] == "C"
                 else {"height": base[1], "backness": base[2], "round": base[3]})
        nodes.append({"label": lab, "ipa": rec["canonical_ipa"], "kind": rec["kind"],
                      "features": feats, "languages": sorted(rec["languages"]),
                      "modifiers_seen": sorted(rec["modifiers_seen"])})
    nodes.sort(key=lambda n: (n["kind"], n["label"]))
    labelset = {n["label"] for n in nodes}

    # derivation: label = parent + ONE operator; the parse doubles as the structural proof
    derivation = []
    for lab in sorted(labelset):
        if len(lab) == 1:
            continue
        parent, op = lab[:-1], lab[-1]
        assert parent in labelset, f"label {lab!r}: parent {parent!r} is not a point label " \
                                   f"— violates 'base + ONE operator'"
        derivation.append({"from": parent, "to": lab, "op": op})

    # adjacency: one feature step apart, each unordered pair once (a < b by label)
    adjacency = []
    bases = sorted(general, key=lambda b: label_of[b])
    for i, x in enumerate(bases):
        for y in bases[i + 1:]:
            if _dist(x, y, features) == 1:
                adjacency.append({"a": label_of[x], "b": label_of[y]})

    # fold: the applied merge ledger (fine → general), chain-resolved to the final general node
    tgt_of = {src: tgt for src, tgt, _r, _n in LEDGER}
    fold = []
    for src, tgt, rec, note in LEDGER:
        if src not in points:                        # inactive entry (source never attested)
            continue
        final = tgt
        while final in tgt_of:                       # chase chains (ɹ → ɻ → r)
            final = tgt_of[final]
        assert final in general, f"fold target of {note!r} resolves outside the general inventory"
        sfeats = ({"place": src[1], "manner": src[2], "voice": src[3]} if src[0] == "C"
                  else {"height": src[1], "backness": src[2], "round": src[3]})
        fold.append({"fine_ipa": points[src]["canonical_ipa"], "fine_features": sfeats,
                     "to": label_of[final], "recover": rec, "note": note})

    return {"nodes": nodes,
            "edges": {"derivation": derivation, "adjacency": adjacency, "fold": fold}}
