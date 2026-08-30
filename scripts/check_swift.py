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
    "ejdj kisj kutjac aclsik acz acstacl aclactt", "pjatj", "sjj zjj py ky", "tyy dyy syy zyy", "tqonx1kuo2 niu2nai3", "txx nxx lx rx tj dj nj lj pj kj", "TW Tw SJOKK h hx hj hq ax", "SJOK SEWP NJAWR HOSWUW DXAX", "iu3 ui4 un2 u3 i1 ican2 puo1 aq2",
    "h hx hj hq", "Hqalif hqalif HQALIF", "r rc rj rx aq", "baqd", "dxax kat sijts acn dxax mat", "sji sejlz fijsj",
    "sjan1 kxaxn3 kau1", "tqonx1 kuo2 tqya2 kxaxn3 kxau3", "tqi1 sji1 tquc1 sjuc4",
    "nic3", "de5", "de0", "raxn2", "hacix ixow fiuw", "ixejs uxejst", "ix ux icx ucx", "sjiau3 liu2 tou1", "alma kert", "ni3 hao3", "zhong1 guo2", "xiao3", "cai4",
    "berd werld show boy law", "dhuh kat sijts awn dhuh flawr",
    "Sjok Sewp Njawr", "Acswonj SJOK", "Dhuh kat Sijts", "Sjan1 kxaxn3",
    "wo3 xi3huan1 pin1yin1, ni3 ne5?", "the kisj kutjac aclsik and zhong1 guo2",
    "Hello vilawg! ta1 kan4 v2 x1 item stays",
]
UNIVERSAL = ["uni", "ipa"]
LANGS = ["hu", "zh", "en"]

cases = []
for text in CORPUS:
    for tgt in UNIVERSAL:
        # level 0 = plain · 1 = tone signs on (uni only; a no-op level is skipped for ipa)
        for level in (("0", "1") if tgt == "uni" else ("0",)):
            want = render(text, tgt, "data", tones=level == "1")
            for mode in ("batch", "stream"):
                cases.append((mode, tgt, level, text, want))
    for lg in LANGS:
        # level 0 = strict · 1 = loose input
        for level in ("0", "1"):
            want = render(text, lg, "data", lazy=level == "1")
            for mode in ("batch", "stream"):
                cases.append((mode, lg, level, text, want))

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
