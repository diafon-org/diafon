"""Command-line entry point: `diaphone` (or `python -m diaphone.cli`)."""
import os
import sys
import argparse

from .loader import load
from .derive import derive
from .report import write_outputs


def _default_data():
    # repo-root/data when run from a clone
    for base in (os.getcwd(), os.path.dirname(os.path.dirname(os.path.dirname(__file__)))):
        cand = os.path.join(base, "data")
        if os.path.isdir(cand):
            return cand
    return "data"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Derive the minimal diaphonemic point set.")
    ap.add_argument("--data", default=_default_data(), help="data directory")
    ap.add_argument("--out", default="out", help="output directory")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any contrast is merged")
    args = ap.parse_args(argv)

    features, languages, all_ph = load(args.data)
    points, violations, near = derive(all_ph, features)
    write_outputs(all_ph, points, violations, near, features, languages, args.out)

    C = sum(1 for p in points.values() if p["kind"] == "C")
    V = len(points) - C
    mods = sorted({m for phs in all_ph.values() for ph in phs for m in ph["mods"]})
    print(f"languages        : {len(languages)}")
    print(f"phoneme records  : {sum(len(v) for v in all_ph.values())}")
    print(f"MINIMAL POINTS   : {len(points)}  (C {C} / V {V})")
    print(f"modifiers used   : {len(mods)}  {mods}")
    print(f"merged contrasts : {len(violations)}")
    print(f"near-merge cands : {len(near)}")
    print(f"written to       : {os.path.abspath(args.out)}/")
    for v in violations:
        print("  VIOLATION", v)
    if args.strict and violations:
        sys.exit(1)


if __name__ == "__main__":
    main()
