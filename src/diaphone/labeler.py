"""Phase-2 labeller: attach a proposed character label to each general-inventory point and check
that the labels are uniquely decodable. Labels live in `data/labels.yaml` (a v0 proposal).

Decodability model: a token starts at a *lowercase* letter (a/e/i/o/u for a vowel, a consonant
letter otherwise) and extends through following *uppercase* operators/modifiers, which never start
a token. So vowel labels (base + uppercase operators) are self-segmenting. A consonant DIGRAPH
whose second char is lowercase (e.g. `sh`) is NOT: the stream `sh` also reads as `s`+`h`. The
validator flags exactly those — every base label that decomposes into a sequence of other labels.
"""
import os
import yaml

QUALITY_OPS = set("HXWVQ")   # vowel quality operators (uppercase; never start a token)


def load_labels(data_dir):
    with open(os.path.join(data_dir, "labels.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def attach(general, labels):
    """Return `general` with a `label` on each point (looked up by canonical_ipa; None if absent)."""
    cmap = {**labels.get("consonants", {}), **labels.get("vowels", {})}
    return {k: {**v, "label": cmap.get(v["canonical_ipa"])} for k, v in general.items()}


def _ambiguous(L, labelset):
    """True if L splits into >= 2 labels from labelset — i.e. not uniquely decodable."""
    n = len(L)
    seg = [False] * (n + 1)
    seg[n] = True                                   # seg[i]: L[i:] is a concatenation of labels
    for i in range(n - 1, -1, -1):
        for w in labelset:
            j = i + len(w)
            if j <= n and L.startswith(w, i) and seg[j]:
                seg[i] = True
                break
    return any(w != L and len(w) < n and L.startswith(w) and seg[len(w)] for w in labelset)


def validate(labels):
    """Return {duplicates, namespace, ambiguous, modifier_overlap} for a label scheme."""
    cons = labels.get("consonants", {})
    vow = labels.get("vowels", {})
    allmap = {**cons, **vow}
    labelset = set(allmap.values())
    VOW = set("aeiou")

    seen = {}
    for ipa, lab in allmap.items():
        seen.setdefault(lab, []).append(ipa)

    namespace = []
    for ipa, lab in vow.items():
        if lab[0] not in VOW:
            namespace.append((ipa, lab, "vowel label not vowel-initial"))
    for ipa, lab in cons.items():
        if lab[0] in VOW:
            namespace.append((ipa, lab, "consonant label starts with a vowel letter"))

    ambiguous = sorted(((ipa, lab) for ipa, lab in allmap.items()
                        if len(lab) >= 2 and _ambiguous(lab, labelset)),
                       key=lambda t: t[1])

    mods = labels.get("modifiers", {})
    overlap = {feat: ch for feat, ch in mods.items() if ch in QUALITY_OPS}

    return {
        "duplicates": {lab: ips for lab, ips in seen.items() if len(ips) > 1},
        "namespace": namespace,
        "ambiguous": ambiguous,
        "modifier_overlap": overlap,   # e.g. H = aspirated & 'lower' — OK, disambiguated by base type
    }
