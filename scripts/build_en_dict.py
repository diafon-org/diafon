"""Build data/en_dict.json — the EN loose-view dictionary: notation word -> real English spelling.

Sources (both fetched separately, not vendored):
  · CMUdict (BSD, cmusphinx/cmudict): word -> ARPAbet pronunciation
  · Norvig count_1w.txt (Google Web Trillion Word Corpus counts): homophone ranking

ARPAbet maps ~1:1 onto our labels (diphthongs = label sequences; the glides Y/W, which have no
points, map to vocalic i/u). Keys are the notation exactly as typed (labels concatenated,
lowercase). Homophones resolve to the most frequent word; entries are pruned to the TOP most
frequent words so the index stays page-embeddable.

Usage:  python3 scripts/build_en_dict.py <cmudict.dict> <count_1w.txt> [TOP=30000]
"""
import json
import os
import sys

A2L = {
    "P": "p", "B": "b", "T": "t", "D": "d", "K": "k", "G": "g",
    "CH": "tq", "JH": "dq", "F": "f", "V": "v", "TH": "tx", "DH": "dx",
    "S": "s", "Z": "z", "SH": "sj", "ZH": "zj", "HH": "h",
    "M": "m", "N": "n", "NG": "nx", "L": "l", "R": "r",
    "Y": "i", "W": "u",                       # glides = nonsyllabic i/u (no glide points)
    "IY": "i", "IH": "ij", "EH": "ej", "AE": "a", "AA": "ac", "AO": "oj",
    "UH": "uj", "UW": "u", "AH": "ax", "ER": "aq",
    "EY": "e", "OW": "o",                     # FACE / GOAT nuclei
    "AY": "ai", "AW": "au", "OY": "oji",      # diphthongs = label sequences
}


def main(cmudict_path, freq_path, top=30000):
    rank = {}
    for i, line in enumerate(open(freq_path, encoding="utf-8")):
        w = line.split("\t")[0].strip()
        if w and w not in rank:
            rank[w] = i
        if i >= top:
            break

    best = {}                                  # key -> (rank, word)
    for line in open(cmudict_path, encoding="utf-8"):
        line = line.split("#")[0].strip()
        if not line:
            continue
        word, *phones = line.split()
        word = word.split("(")[0].lower()
        if word not in rank or any(ch not in "abcdefghijklmnopqrstuvwxyz'" for ch in word):
            continue
        try:
            key = "".join(A2L[p.rstrip("012")] for p in phones)
        except KeyError:
            continue
        r = rank[word]
        if key not in best or r < best[key][0]:
            best[key] = (r, word)

    out = {"__source": "CMUdict (BSD) x Norvig count_1w; scripts/build_en_dict.py; "
                       f"top {top} words by frequency"}
    out.update({k: w for k, (_r, w) in sorted(best.items())})
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "en_dict.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=0, sort_keys=True)
    size = os.path.getsize(path)
    print(f"wrote {path}: {len(best)} pronunciations · {size // 1024} KB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 30000)
