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
        out.append({
            "canonical_ipa": p["canonical_ipa"], "kind": p["kind"], "features": feats,
            "languages": p["languages"], "modifiers_seen": sorted(p["modifiers_seen"]),
        })
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


def render_report(all_ph, points, violations, near, suspicious, features, languages):
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
    return "\n".join(L)


def write_outputs(all_ph, points, violations, near, suspicious, features, languages, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "points.json"), "w", encoding="utf-8") as f:
        json.dump(points_to_json(points), f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "mappings.json"), "w", encoding="utf-8") as f:
        json.dump(mappings_to_json(all_ph), f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(render_report(all_ph, points, violations, near, suspicious, features, languages))
