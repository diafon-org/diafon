"""What does one language cost? — the structured way to add (or audit) a language.

Adding a language is only interesting for what it FORCES. This runs the whole derivation twice,
with and without one language, and reports the difference:

  * NEW POINTS      — the language contrasts something the 23 do not (it is a witness)
  * new modifiers   — it needs a mechanism that does not exist yet (the expensive kind)
  * MERGED CONTRASTS / unsafe folds — it breaks a decision already recorded in the ledger
  * everything else — it is a subset of the existing inventory (a coverage language, free)

Two modes:
    python3 scripts/lang_delta.py --add path/to/pl.yaml     # dry-run a candidate (nothing is written)
    python3 scripts/lang_delta.py --drop RU                 # audit: what would we lose without it?

The candidate is copied into a TEMPORARY data directory — `data/` is never touched.
"""
import argparse
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from diaphone.loader import load
from diaphone.derive import derive, find_modifier_redundant
from diaphone.merges import apply_merges
from diaphone.notation import find_collisions, find_universal_collisions, find_shared_labels

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def analyse(data_dir):
    """Everything one derivation run can tell us, or the exception that stopped it."""
    features, languages, all_ph = load(data_dir)
    points, violations, near, suspicious, rhotic = derive(all_ph, features)
    out = {
        "languages": set(languages),
        "phonemes": sum(len(v) for v in all_ph.values()),
        "points": {k: v["canonical_ipa"] for k, v in points.items()},
        "modifiers": {m for phs in all_ph.values() for ph in phs for m in ph["mods"]},
        "violations": violations,
        "near": near, "suspicious": suspicious, "rhotic": rhotic,
        "redundant": find_modifier_redundant(points, all_ph, features),
        "fold_error": None,
    }
    try:
        general, _ = apply_merges(points)
        out["general"] = {k: v["canonical_ipa"] for k, v in general.items()}
    except AssertionError as e:                   # a fold the ledger declared safe no longer is
        out["general"], out["fold_error"] = {}, str(e)
        return out
    for name, fn in (("collisions", find_collisions),
                     ("universal", find_universal_collisions),
                     ("shared", find_shared_labels)):
        try:
            out[name] = fn(all_ph, features, data_dir)
        except Exception as e:                    # labels.yaml has no entry for a brand-new point
            out[name] = f"n/a — {type(e).__name__}: {e}"
    return out


def _describe(base_tuple, ipa):
    kind = base_tuple[0]
    body = " ".join(str(x) for x in base_tuple[1:])
    return f"/{ipa}/ ({kind}: {body})"


def report(before, after, label):
    add = set(after["points"]) - set(before["points"])
    gone = set(before["points"]) - set(after["points"])
    newmods = after["modifiers"] - before["modifiers"]
    lost = before["languages"] - after["languages"] or after["languages"] - before["languages"]

    print(f"LANGUAGE DELTA — {label}   ({', '.join(sorted(lost))})")
    print(f"  phonemes           : {before['phonemes']} -> {after['phonemes']} "
          f"({after['phonemes'] - before['phonemes']:+d})")
    print(f"  fine points        : {len(before['points'])} -> {len(after['points'])} "
          f"({len(after['points']) - len(before['points']):+d})")
    print(f"  general inventory  : {len(before['general'])} -> {len(after['general'])} "
          f"({len(after['general']) - len(before['general']):+d})")
    print(f"  modifiers used     : {len(before['modifiers'])} -> {len(after['modifiers'])}")

    for title, keys in (("NEW POINTS", add), ("points no longer needed", gone)):
        if keys:
            print(f"  {title}: {len(keys)}")
            src = after if keys is add else before
            for k in sorted(keys):
                print(f"      {_describe(k, src['points'][k])}")
    if newmods:
        print(f"  NEW MODIFIERS      : {', '.join(sorted(newmods))}   <- a new mechanism, not just data")

    hard = False
    if after["violations"]:
        hard = True
        print(f"  MERGED CONTRASTS   : {len(after['violations'])}   <- FIRST INVARIANT")
        for v in after["violations"][:8]:
            print(f"      {v}")
    if after["fold_error"]:
        hard = True
        print("  UNSAFE FOLD        : the merge ledger no longer holds")
        print(f"      {after['fold_error']}")
    # A witness earns its place by CO-OCCURRING a pair, which keeps it off the mergeable list.
    # Losing the language does not remove a point — it removes the reason the point must stay.
    # Compare by the PAIR, not the whole row: every row's language lists change when a language
    # is added or removed, which would otherwise mark every pair as both locked and freed.
    pair = lambda rows: {frozenset((r[1], r[2])): r for r in rows}
    b_near, a_near = pair(before["near"]), pair(after["near"])
    locked = [b_near[k] for k in b_near.keys() - a_near.keys()]
    freed = [a_near[k] for k in a_near.keys() - b_near.keys()]
    if locked:
        print(f"  PAIRS IT LOCKS APART: {len(locked)}   <- it contrasts these, so they cannot merge")
        for n in sorted(locked, key=lambda r: (r[1], r[2])):
            print(f"      /{n[1]}/ ~ /{n[2]}/")
    if freed:
        print(f"  pairs that become mergeable without it: {len(freed)}")
        for n in sorted(freed, key=lambda r: (r[1], r[2])):
            print(f"      /{n[1]}/ ~ /{n[2]}/")
    for name, title in (("redundant", "modifier-reachable points"),
                        ("suspicious", "suspicious co-occurrences"),
                        ("rhotic", "rhotic co-occurrences")):
        b, a = len(before[name]), len(after[name])
        if a != b:
            hard = hard or a > b
            print(f"  {title}: {b} -> {a}")
            for row in after[name]:
                if row not in before[name]:
                    print(f"      + {row}")
    for name in ("collisions", "universal", "shared"):
        a = after.get(name)
        if isinstance(a, str):
            print(f"  {name}: {a}")
        elif a and a != before.get(name):
            hard = True
            print(f"  NOTATION {name}: {a}")

    if hard:
        verdict = "BREAKS something — a decision has to be made (new point, new modifier, or a ledger entry revisited)"
    elif add or newmods or locked:
        verdict = "WITNESS — it forces new structure"
    else:
        verdict = "COVERAGE — a subset of the existing points and modifiers; free to add"
    print(f"  VERDICT: {verdict}")
    return hard


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--add", metavar="YAML", help="dry-run a candidate language file (never copied into data/)")
    g.add_argument("--drop", metavar="CODE", help="audit an existing language: what would we lose without it?")
    a = ap.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        mirror = os.path.join(tmp, "data")
        shutil.copytree(DATA, mirror)
        if a.add:
            code = os.path.splitext(os.path.basename(a.add))[0]
            dest = os.path.join(mirror, "languages", code + ".yaml")
            if os.path.exists(dest):
                sys.exit(f"{code} is already in data/languages — use --drop {code.upper()} to audit it")
            shutil.copy(a.add, dest)
            before, after, label = analyse(DATA), analyse(mirror), f"+{code.upper()}"
        else:
            code = a.drop.lower()
            path = os.path.join(mirror, "languages", code + ".yaml")
            if not os.path.exists(path):
                sys.exit(f"no such language: {code}")
            os.remove(path)
            before, after, label = analyse(mirror), analyse(DATA), f"+{a.drop.upper()} (audit)"
        return 1 if report(before, after, label) else 0


if __name__ == "__main__":
    sys.exit(main())
