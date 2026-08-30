"""Command-line entry point: `diaphone` (or `python -m diaphone.cli`)."""
import os
import sys
import argparse

from .loader import load
from .derive import derive
from .merges import apply_merges
from .labeler import load_labels, attach, validate
from .report import write_outputs
from .decode import decode


def _default_data():
    # repo-root/data when run from a clone
    for base in (os.getcwd(), os.path.dirname(os.path.dirname(os.path.dirname(__file__)))):
        cand = os.path.join(base, "data")
        if os.path.isdir(cand):
            return cand
    return "data"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "decode":
        dp = argparse.ArgumentParser(prog="diaphone decode",
                                     description="Notation -> a language's orthography.")
        dp.add_argument("lang", choices=["hu", "zh", "en"], help="target orthography")
        dp.add_argument("text", help="space-separated notation words, e.g. 'sqok sewp njawrw'")
        dp.add_argument("--data", default=_default_data())
        dp.add_argument("--off", default="",
                        help="adoption profile: comma-separated group names switched off")
        dp.add_argument("--lazy", action="store_true",
                        help="allow language-specific shortcuts (e.g. HU bare a=/ɒ/, EN sh/ch/th)")
        da = dp.parse_args(argv[1:])
        print(decode(da.text, da.lang, da.data, lazy=da.lazy,
                     off=[g for g in da.off.split(',') if g]))
        return
    if argv and argv[0] == "export-json":
        import json
        from .engine import export_data
        xp = argparse.ArgumentParser(prog="diaphone export-json",
                                     description="Export the conversion engine as pure data, for ports.")
        xp.add_argument("--data", default=_default_data())
        xp.add_argument("--out", default=os.path.join("out", "engine.json"))
        xa = xp.parse_args(argv[1:])
        data = export_data(xa.data)
        os.makedirs(os.path.dirname(os.path.abspath(xa.out)), exist_ok=True)
        with open(xa.out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        n_labels = len(data["keys"])
        print(f"wrote {xa.out}: {len(data['maps'])} universal maps · {n_labels} labels · "
              f"{len(data['orth'])} language orthographies")
        return
    if argv and argv[0] in ("ipa", "uni", "render"):
        from .engine import render, targets
        rp = argparse.ArgumentParser(prog="diaphone render",
                                     description="Notation -> a target (uni, ipa, or a language).")
        if argv[0] == "render":
            rp.add_argument("target", choices=targets())
            rest = argv[1:]
        else:
            rest = [argv[0], *argv[1:]]          # `diaphone ipa …` / `uni …` = render <that>
            rp.add_argument("target", choices=targets())
        rp.add_argument("text", help="space-separated notation words, e.g. 'sjan1 kxyn3 kau1'")
        rp.add_argument("--data", default=_default_data())
        rp.add_argument("--lazy", action="store_true")
        rp.add_argument("--tones", action="store_true",
                        help="uni target: render tone digits as tone signs on the vowel "
                             "(opt-in; plain digits by default)")
        ra = rp.parse_args(rest)
        print(render(ra.text, ra.target, ra.data, lazy=ra.lazy, tones=ra.tones))
        return

    ap = argparse.ArgumentParser(description="Derive the minimal diaphonemic point set.")
    ap.add_argument("--data", default=_default_data(), help="data directory")
    ap.add_argument("--out", default="out", help="output directory")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any contrast is merged")
    args = ap.parse_args(argv)

    features, languages, all_ph = load(args.data)
    points, violations, near, suspicious, rhotic = derive(all_ph, features)
    general, folded = apply_merges(points)
    labels = load_labels(args.data)
    general = attach(general, labels)
    label_issues = validate(labels)
    from .graph import build_graph
    graph = build_graph(points, general, labels, features)
    write_outputs(all_ph, points, violations, near, suspicious, rhotic,
                  general, folded, labels, label_issues, features, languages, args.out,
                  graph=graph)

    C = sum(1 for p in points.values() if p["kind"] == "C")
    V = len(points) - C
    Cg = sum(1 for p in general.values() if p["kind"] == "C")
    Vg = len(general) - Cg
    mods = sorted({m for phs in all_ph.values() for ph in phs for m in ph["mods"]})
    print(f"languages        : {len(languages)}")
    print(f"phoneme records  : {sum(len(v) for v in all_ph.values())}")
    print(f"FINE-GRAINED     : {len(points)}  (C {C} / V {V})")
    print(f"GENERAL INVENTORY: {len(general)}  (C {Cg} / V {Vg})  after {len(folded)} merges")
    print(f"modifiers used   : {len(mods)}  {mods}")
    print(f"merged contrasts : {len(violations)}")
    print(f"near-merge cands : {len(near)}")
    print(f"suspicious co-occ: {len(suspicious)}")
    print(f"rhotic co-occ    : {len(rhotic)}")
    e = graph["edges"]
    print(f"covering graph   : {len(graph['nodes'])} nodes · {len(e['derivation'])} derivation · "
          f"{len(e['adjacency'])} adjacency · {len(e['fold'])} fold edges")
    labelled = sum(1 for p in general.values() if p.get("label"))
    print(f"labels           : {labelled}/{len(general)} labelled · "
          f"{len(label_issues['ambiguous'])} not decodable · "
          f"{len(label_issues['duplicates'])} dup · {len(label_issues['namespace'])} namespace")
    print(f"written to       : {os.path.abspath(args.out)}/")
    for v in violations:
        print("  VIOLATION", v)
    for n, a, b, shared in suspicious:
        print(f"  SUSPECT {a}~{b} (rarer in {n} lang; shares {','.join(shared)}) — allophone?")
    for a, b, shared in rhotic:
        print(f"  RHOTIC {a}~{b} co-occurs in {','.join(shared)} — cross-manner contrast?")

    # FIFTH invariant — no point duplicates what a modifier already spells (the point/modifier
    # boundary). Empty: the palatal coronals are /t d n l/ + palatalized, Tamil's ஷ is the hush
    # point. A fresh hit is a real decision — merge it, or record it in _CONFIRMED_MODIFIER_DISTINCT.
    from .derive import find_modifier_redundant
    redundant = find_modifier_redundant(points, all_ph, features)
    print(f"modifier-reachable: {len(redundant)} unreviewed")
    for pt, base, mod, pl, ql in redundant:
        print(f"  REACHABLE /{pt}/ [{','.join(pl)}] == /{base}/+{mod} [{','.join(ql)}] "
              f"— no language contrasts them")

    from .notation import find_collisions, find_universal_collisions, find_shared_labels
    collisions = find_collisions(all_ph, features, args.data)
    print(f"notation collide : {sum(len(v) for v in collisions.values())} unreviewed")
    for lang, hits in collisions.items():
        for lab, ipas in hits:
            print(f"  COLLISION [{lang}] {lab} = /{','.join(ipas)}/ also reads as a sequence")

    uni_collisions = find_universal_collisions(all_ph, features, args.data)
    print(f"universal stream : {len(uni_collisions)} unreviewed")
    for lab in uni_collisions:
        print(f"  COLLISION [universal] {lab} also reads as a sequence of universal labels")

    # One label, two analyses — invisible to both finders above (each language is injective; the
    # clash only exists in the unioned universal stream). It is what forces the doubling rule.
    shared = find_shared_labels(all_ph, features, args.data)
    print(f"shared labels    : {len(shared)} unreviewed")
    for lab, analyses in shared.items():
        readings = " vs ".join(f"{pl}+{'+'.join(mods) or 'ø'} [{','.join(langs)}]"
                               for pl, mods, langs in analyses)
        print(f"  SHARED [universal] {lab} = {readings}")

    if args.strict and (violations or redundant or collisions or uni_collisions or shared):
        sys.exit(1)


if __name__ == "__main__":
    main()
