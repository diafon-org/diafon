"""Serialise derived points/mappings to JSON and render a Markdown report."""
import os
import json

from .model import strip_mods


def points_to_json(points):
    out = []
    for p in points.values():
        feats = ({"place": p["base"][1], "manner": p["base"][2], "voice": p["base"][3]}
                 if p["kind"] == "C"
                 else {"height": p["base"][1], "backness": p["base"][2], "round": p["base"][3]})
        d = {
            "canonical_ipa": p["canonical_ipa"], "kind": p["kind"], "features": feats,
            "languages": p["languages"], "modifiers_seen": sorted(p["modifiers_seen"]),
        }
        if p.get("recovered"):
            d["recovered"] = p["recovered"]      # general-inventory targets that absorbed a merge
        if p.get("label"):
            d["label"] = p["label"]              # the character label
        out.append(d)
    out.sort(key=lambda x: (x["kind"], x["canonical_ipa"]))
    return out


def mappings_to_json(all_ph):
    out = {}
    for code, phs in all_ph.items():
        out[code] = [{
            "ipa": ph["ipa"], "base_ipa": strip_mods(ph["ipa"]),
            "modifiers": sorted(ph["mods"]), "orth": ph["orth"], "status": ph["st"],
        } for ph in phs]
    return out


def render_report(all_ph, points, violations, near, suspicious, rhotic, general, folded,
                  labels, label_issues, features, languages):
    PLACE = features["consonant"]["place"]
    MANNER = features["consonant"]["manner"]
    HEIGHT = features["vowel"]["height"]
    BACK = features["vowel"]["backness"]
    C = [p for p in points.values() if p["kind"] == "C"]
    V = [p for p in points.values() if p["kind"] == "V"]
    mods_used = sorted({m for phs in all_ph.values() for ph in phs for m in ph["mods"]})

    L = []
    L.append("# Diaphonemic point derivation — report\n")
    L.append(f"- Languages: **{len(languages)}** ({', '.join(languages)})")
    L.append(f"- Phoneme records (after expansion): **{sum(len(v) for v in all_ph.values())}**")
    L.append(f"- **Minimal points: {len(points)}** (consonant {len(C)} · vowel {len(V)})")
    L.append(f"- Modifiers used: **{len(mods_used)}** ({', '.join(mods_used)})")
    L.append(f"- Merged contrasts (must be 0): **{len(violations)}**\n")

    L.append("## Points per language\n")
    for code, lang in languages.items():
        bases = {ph["base"] for ph in all_ph[code]}
        L.append(f"- **{code}** {lang['name']}: {len(bases)} points, {len(all_ph[code])} phonemes")
    L.append("")

    if violations:
        L.append("## ⚠ Merged contrasts\n")
        for v in violations:
            L.append(f"- {v['lang']}: {v['phonemes']} collapse at {v['point']} mods={v['mods']}")
    else:
        L.append("## ✓ No merged contrasts\n"
                 "Every language's phonemes stay distinct as (point, modifier) tuples.\n")

    L.append("## Consonant points\n")
    for p in sorted(C, key=lambda p: (MANNER.index(p["base"][2]),
                                      PLACE.index(p["base"][1]), p["base"][3])):
        b = p["base"]
        mv = ("  +" + ",".join(sorted(p["modifiers_seen"]))) if p["modifiers_seen"] else ""
        L.append(f"- `{p['canonical_ipa']}` {b[2]} {b[1]} {b[3]} "
                 f"[{len(p['languages'])}: {','.join(sorted(p['languages']))}]{mv}")

    L.append("\n## Vowel points\n")
    for p in sorted(V, key=lambda p: (HEIGHT.index(p["base"][1]),
                                      BACK.index(p["base"][2]), p["base"][3])):
        b = p["base"]
        rd = "rounded" if b[3] else "unrounded"
        mv = ("  +" + ",".join(sorted(p["modifiers_seen"]))) if p["modifiers_seen"] else ""
        L.append(f"- `{p['canonical_ipa']}` {b[1]} {b[2]} {rd} "
                 f"[{len(p['languages'])}: {','.join(sorted(p['languages']))}]{mv}")

    L.append("\n## Near-merge candidates (same manner, ≤1 step apart, never co-occurring)\n")
    L.append("Optional fusions to decide before labelling — the rhotic trade-off, per pair:\n")
    for d, a, b, la, lb in near:
        L.append(f"- `{a}` ({','.join(la)}) ~ `{b}` ({','.join(lb)}) · dist {d}")

    L.append("\n## Suspicious co-occurrences (candidate allophones)\n")
    L.append("Rare points sitting one place/height step from a same-language neighbour — a real "
             "contrast is expected to recur across languages, so a rare one propped up by ≤2 "
             "languages may be an allophone entered as a phoneme. Reviewed genuine contrasts are "
             "filtered out; what remains wants a look:\n")
    if suspicious:
        for n, a, b, shared in suspicious:
            L.append(f"- `{a}` ~ `{b}` · shares [{','.join(shared)}] · rarer in {n} lang")
    else:
        L.append("_None — every co-occurring near-neighbour is a reviewed genuine contrast._")

    L.append("\n## Rhotic co-occurrences (cross-manner blind spot)\n")
    L.append("The near-merge finder only compares same-manner points, so the rhotic family "
             "(trill / tap / approximant / retroflex) is invisible to it. Rhotic pairs that "
             "co-occur in a language (a real contrast), minus the reviewed `r`~`ɾ`:\n")
    if rhotic:
        for a, b, shared in rhotic:
            L.append(f"- `{a}` ~ `{b}` · co-occur in [{','.join(shared)}]")
    else:
        L.append("_None beyond `r`~`ɾ` (Spanish trill/tap)._")

    L.append("\n## General inventory (merge ledger applied)\n")
    Cg = sum(1 for p in general.values() if p["kind"] == "C")
    L.append(f"Fine-grained **{len(points)}** → general **{len(general)}** "
             f"(C {Cg} · V {len(general) - Cg}) after {len(folded)} decided merges:\n")
    for a, b, rec, note in folded:
        r = f"recover **{rec}**" if rec else "no recovery (sub-phonemic everywhere)"
        L.append(f"- {note} — {r}")

    L.append("\n## Labels — the character scheme\n")
    amb, dup = label_issues["ambiguous"], label_issues["duplicates"]
    L.append(f"Base + operator labels, self-segmenting. "
             f"Decodability check: **{len(amb)}** base labels are NOT uniquely decodable "
             f"(they split into other labels), **{len(dup)}** duplicates, "
             f"**{len(label_issues['namespace'])}** namespace issues.\n")
    if amb:
        L.append("**Not decodable (consonant digraphs that collide with a letter sequence):**")
        L.append("  " + ", ".join(f"`{lab}`(={ipa})" for ipa, lab in amb))
        L.append("\nEvery such label must be reworked until it decodes uniquely.\n")
    if label_issues["modifier_overlap"]:
        ov = ", ".join(f"`{c}`={f}" for f, c in label_issues["modifier_overlap"].items())
        L.append(f"_Modifier/quality overlap (OK — disambiguated by base type): {ov}._\n")
    L.append("| point | label |   | point | label |")
    L.append("|---|---|---|---|---|")
    lab = [(p["canonical_ipa"], p.get("label") or "—") for p in
           sorted(general.values(), key=lambda p: (p["kind"], p["canonical_ipa"]))]
    half = (len(lab) + 1) // 2
    for i in range(half):
        a_ = f"`{lab[i][0]}` | `{lab[i][1]}`"
        b_ = f"`{lab[i+half][0]}` | `{lab[i+half][1]}`" if i + half < len(lab) else " | "
        L.append(f"| {a_} |   | {b_} |")
    return "\n".join(L)


def labels_to_json(general, labels, label_issues):
    return {
        "points": {p["canonical_ipa"]: p["label"]
                   for p in sorted(general.values(), key=lambda p: (p["kind"], p["canonical_ipa"]))
                   if p.get("label")},
        "modifiers": labels.get("modifiers", {}),
        "recover": labels.get("recover", {}),
        "issues": {"ambiguous": label_issues["ambiguous"],
                   "duplicates": label_issues["duplicates"],
                   "namespace": label_issues["namespace"]},
    }


def write_outputs(all_ph, points, violations, near, suspicious, rhotic, general, folded,
                  labels, label_issues, features, languages, out_dir, graph=None):
    os.makedirs(out_dir, exist_ok=True)
    if graph is not None:
        with open(os.path.join(out_dir, "graph.json"), "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "points.json"), "w", encoding="utf-8") as f:
        json.dump(points_to_json(points), f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "general_inventory.json"), "w", encoding="utf-8") as f:
        json.dump(points_to_json(general), f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "labels.json"), "w", encoding="utf-8") as f:
        json.dump(labels_to_json(general, labels, label_issues), f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "mappings.json"), "w", encoding="utf-8") as f:
        json.dump(mappings_to_json(all_ph), f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(render_report(all_ph, points, violations, near, suspicious, rhotic,
                              general, folded, labels, label_issues, features, languages))
