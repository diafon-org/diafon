#!/usr/bin/env python3
"""Which of the characters we emit are missing from fonts people actually have?

The uni view is deliberately plain ASCII letters + combining marks, so that it renders without
the project font. That promise is only as good as the marks' coverage in ubiquitous fonts — and
the rarer combining marks (U+0348 double vertical below, U+030D/U+030E vertical above, U+0316
grave below) are missing from several system faces. This reports the exposure exactly: per font,
which codepoints are absent, and which notation labels those codepoints affect.

    python scripts/check_font_coverage.py                 # scan the system's common faces
    python scripts/check_font_coverage.py --strict        # exit 1 if any BASELINE font has a gap
    python scripts/check_font_coverage.py path/to/x.ttf   # add specific fonts

There is no automatic fix — a missing mark can only be solved by choosing a different mark, by
shipping the font, or by accepting the degradation. This tool exists to keep the cost visible and
to stop it growing silently when a glyph is changed.
"""
import argparse
import glob
import os
import sys
import unicodedata
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fontTools.ttLib import TTFont                    # noqa: E402

from diafon.loader import load                      # noqa: E402
from diafon.uni import uni_labels                   # noqa: E402
from diafon.render import ipa_labels                # noqa: E402

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

# Faces to scan by default: the ones a reader is most likely to be using. BASELINE names are the
# ones we hold ourselves to — a gap there is a real-world failure, not a curiosity.
BASELINE = {"Helvetica", "Times New Roman", "Arial", "Georgia", "Verdana"}
FONT_DIRS = ["/System/Library/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts",
             os.path.expanduser("~/Library/Fonts"), "/usr/share/fonts"]
WANTED = ["Helvetica.ttc", "Times New Roman.ttf", "Arial.ttf", "Georgia.ttf", "Verdana.ttf",
          "SFNS.ttf", "SFNSRounded.ttf", "DejaVuSans.ttf", "NotoSerif-Regular.ttf",
          "Menlo.ttc"]


def emitted_chars(data_dir=DATA):
    """{codepoint: {labels that emit it}} across both universal targets.

    NFC, because that is what the engine actually emits — `uni._apply` normalises before
    returning. Decomposing here would badly overstate the exposure: ü ṭ á ã are single
    precomposed codepoints that every Latin font has, and only the sequences with NO
    precomposed form (s̩, s͈, i̋, t̤ …) really depend on the font carrying a combining mark.
    """
    feats, _raw, all_ph = load(data_dir)
    out = defaultdict(set)
    for target, m in (("uni", uni_labels(all_ph, feats, data_dir)),
                      ("ipa", ipa_labels(all_ph, feats, data_dir))):
        for label, glyph in m.items():
            for ch in unicodedata.normalize("NFC", glyph):
                if ch != " ":
                    out[ch].add(f"{target}:{label}")
    return out


def font_files(extra):
    found = []
    for d in FONT_DIRS:
        for name in WANTED:
            p = os.path.join(d, name)
            if os.path.exists(p):
                found.append(p)
        found += [p for p in glob.glob(os.path.join(d, "SFNS*.ttf"))]
    return sorted(set(found)) + list(extra)


def covered(path):
    """The set of codepoints a font file can render (union over its faces, for .ttc)."""
    chars, i = set(), 0
    while True:
        try:
            f = TTFont(path, fontNumber=i, lazy=True)
        except Exception:
            break
        try:
            for table in f["cmap"].tables:
                chars |= {chr(c) for c in table.cmap}
        except Exception:
            pass
        f.close()
        i += 1
        if i > 32 or not path.endswith(".ttc"):
            break
    return chars


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fonts", nargs="*", help="extra font files to check")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if a BASELINE font is missing anything the target emits")
    ap.add_argument("--target", choices=("uni", "ipa", "both"), default="both",
                    help="which target to gate on (default both; `--strict --target uni` is the\n                          meaningful gate — the uni view is the one that promises to render bare)")
    args = ap.parse_args()

    emitted = emitted_chars()
    if args.target != "both":
        emitted = {c: {l for l in ls if l.startswith(args.target + ":")}
                   for c, ls in emitted.items()}
        emitted = {c: ls for c, ls in emitted.items() if ls}
    marks = {c for c in emitted if unicodedata.category(c) == "Mn"}
    scope = "the uni + ipa targets" if args.target == "both" else f"the {args.target} target"
    print(f"engine emits {len(emitted)} distinct codepoints "
          f"({len(marks)} combining marks) across {scope}\n")

    files = font_files(args.fonts)
    if not files:
        print("no fonts found to scan (pass paths explicitly)")
        return 0

    gaps_in_baseline = False
    worst = defaultdict(list)              # codepoint -> fonts missing it
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        have = covered(path)
        missing = sorted(c for c in emitted if c not in have)
        tag = "BASELINE" if name in BASELINE else "        "
        if not missing:
            print(f"  {tag} {name:24} complete")
            continue
        if name in BASELINE:
            gaps_in_baseline = True
        print(f"  {tag} {name:24} missing {len(missing)}")
        for c in missing:
            worst[c].append(name)

    if worst:
        print("\ncodepoints by exposure — how many scanned fonts lack them, and what breaks:")
        for c, fonts in sorted(worst.items(), key=lambda kv: (-len(kv[1]), ord(kv[0]))):
            labels = sorted(emitted[c])
            shown = ", ".join(labels[:6]) + (f" +{len(labels) - 6} more" if len(labels) > 6 else "")
            try:
                nm = unicodedata.name(c)
            except ValueError:
                nm = "?"
            print(f"  U+{ord(c):04X} {nm[:44]:44} {len(fonts):2} fonts · {len(labels):2} labels")
            print(f"         {shown}")

    # Per-target rollup: the whole point of the uni view is that it degrades better than IPA.
    # This is the number that justifies "ASCII letters + combining marks" over IPA codepoints.
    print("\nexposure by target (a label is exposed if ANY scanned font cannot render it):")
    for target in ("uni", "ipa"):
        cps = {c for c, f in worst.items() if any(l.startswith(target + ":") for l in emitted[c])}
        labels = {l for c in cps for l in emitted[c] if l.startswith(target + ":")}
        total = {l for c in emitted for l in emitted[c] if l.startswith(target + ":")}
        print(f"  {target:4} {len(cps):2} codepoints exposed · {len(labels):3}/{len(total):3} labels affected")

    if args.strict and gaps_in_baseline:
        print("\nFAIL: a baseline font cannot render everything the engine emits.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
