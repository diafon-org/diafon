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
        dp.add_argument("--lazy", action="store_true",
                        help="allow language-specific shortcuts (e.g. HU bare a=/ɒ/, e=/ɛ/)")
        da = dp.parse_args(argv[1:])
        print(decode(da.text, da.lang, da.data, lazy=da.lazy))
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
    write_outputs(all_ph, points, violations, near, suspicious, rhotic,
                  general, folded, labels, label_issues, features, languages, args.out)

    C = sum(1 for p in points.values() if p["kind"] == "C")
    V = len(points) - C
    Cg = sum(1 for p in general.values() if p["kind"] == "C")
    Vg = len(general) - Cg
    mods = sorted({m for phs in all_ph.values() for ph in phs for m in ph["mods"]})
    print(f"languages        : {len(languages)}")
    print(f"phoneme records  : {sum(len(v) for v in all_ph.values())}")
    print(f"FINE-GRAINED     : {len(points)}  (C {C} / V {V})")
    print(f"GENERAL INVENTORY: {len(general)}  (C {Cg} / V {Vg})  after {len(folded)} Phase-2 merges")
    print(f"modifiers used   : {len(mods)}  {mods}")
    print(f"merged contrasts : {len(violations)}")
    print(f"near-merge cands : {len(near)}")
    print(f"suspicious co-occ: {len(suspicious)}")
    print(f"rhotic co-occ    : {len(rhotic)}")
    labelled = sum(1 for p in general.values() if p.get("label"))
    print(f"labels (v0)      : {labelled}/{len(general)} labelled · "
          f"{len(label_issues['ambiguous'])} not decodable · "
          f"{len(label_issues['duplicates'])} dup · {len(label_issues['namespace'])} namespace")
    print(f"written to       : {os.path.abspath(args.out)}/")
    for v in violations:
        print("  VIOLATION", v)
    for n, a, b, shared in suspicious:
        print(f"  SUSPECT {a}~{b} (rarer in {n} lang; shares {','.join(shared)}) — allophone?")
    for a, b, shared in rhotic:
        print(f"  RHOTIC {a}~{b} co-occurs in {','.join(shared)} — cross-manner contrast?")

    from .notation import find_collisions
    collisions = find_collisions(all_ph, features, args.data)
    print(f"notation collide : {sum(len(v) for v in collisions.values())} unreviewed")
    for lang, hits in collisions.items():
        for lab, ipas in hits:
            print(f"  COLLISION [{lang}] {lab} = /{','.join(ipas)}/ also reads as a sequence")

    if args.strict and (violations or collisions):
        sys.exit(1)


if __name__ == "__main__":
    main()
