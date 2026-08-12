"""Validate the Swift engine port against the Python CLI over the shared corpus.

Usage:  PYTHONPATH=src python3 scripts/check_swift.py mac/build/diaphone-check mac/build/engine.json
(Normally via `make -C mac check`.) Both batch AND stream (char-by-char) modes must be
byte-identical to `render()` for every target, strict and loose.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from diaphone.engine import render

BIN, ENGINE = sys.argv[1], sys.argv[2]

CORPUS = [
    "sjok sewp njawr", "kecsecnecm sewpejn", "acswonj", "hoswuw", "ejdj nacdj kutjac",
    "ejdj kisj kutjac aclsik acz acstacl aclactt", "pjatj", "sjj zjj kc gc", "ty dy sy zy",
    "h hj hc hq", "baqd", "dxax kat sijts acn dxax mat", "sji sejlz fijsj",
    "sjan1 kxaxn3 kau1", "tqonx1 kuo2 tqha2 kxaxn3 kxau3", "tqi1 sji1 tquc1 sjuc4",
    "nic3", "de5", "raxn2", "alma kert", "ni3 hao3", "zhong1 guo2", "xiao3", "cai4",
]
UNIVERSAL = ["native", "ipa", "native-hu", "native-zh"]
LANGS = ["hu", "zh", "en"]

cases = []
for text in CORPUS:
    for tgt in UNIVERSAL:
        want = render(text, tgt, "data")
        for mode in ("batch", "stream"):
            cases.append((mode, tgt, "0", text, want))
    for lg in LANGS:
        for loose in ("0", "1"):
            want = render(text, lg, "data", lazy=loose == "1")
            for mode in ("batch", "stream"):
                cases.append((mode, lg, loose, text, want))

stdin = "\n".join("\t".join(c[:4]) for c in cases)
got = subprocess.run([BIN, ENGINE], input=stdin, capture_output=True, text=True, check=True)
outs = got.stdout.splitlines()
assert len(outs) == len(cases), f"line count mismatch: {len(outs)} vs {len(cases)}"

fail = 0
for (mode, tgt, loose, text, want), out in zip(cases, outs):
    if out != want:
        fail += 1
        print(f"  MISMATCH [{mode} {tgt} loose={loose}] {text!r}\n    swift : {out!r}\n    python: {want!r}")
print(f"{len(cases) - fail}/{len(cases)} swift==python" + ("" if fail else "  ✓"))
sys.exit(1 if fail else 0)
