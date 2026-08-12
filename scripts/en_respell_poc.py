"""Proof of concept: real English spelling from notation, via a reverse CMUdict lookup.

CMUdict (BSD) maps 135k English words -> ARPAbet phonemes. ARPAbet maps ~1:1 onto our labels, so
inverting the dictionary gives notation -> real spelling ("dxax kat" -> "the cat") instead of the
letter-respelling ("thu kat"). Diphthongs key as label sequences; the glides Y/W (no points in the
inventory) key as their vocalic twins i/u. Homophones resolve to the shortest word (PoC heuristic —
a frequency list would do this properly).

Usage:  python3 scripts/en_respell_poc.py <cmudict.dict> "dxax kat sijts acn dxax mat"
"""
import sys

# ARPAbet -> our label(s). Stress digits are stripped first.
A2L = {
    # consonants
    "P": "p", "B": "b", "T": "t", "D": "d", "K": "k", "G": "g",
    "CH": "tq", "JH": "dq", "F": "f", "V": "v", "TH": "tx", "DH": "dx",
    "S": "s", "Z": "z", "SH": "sj", "ZH": "zj", "HH": "h",
    "M": "m", "N": "n", "NG": "nx", "L": "l", "R": "r",
    "Y": "i", "W": "u",                      # glides = nonsyllabic i/u (no glide points)
    # vowels
    "IY": "i", "IH": "ij", "EH": "ej", "AE": "a", "AA": "ac", "AO": "oj",
    "UH": "uj", "UW": "u", "AH": "ax", "ER": "aq",
    "EY": "e", "OW": "o",                    # FACE / GOAT nuclei
    "AY": "a i", "AW": "a u", "OY": "oj i",  # diphthongs = label sequences
}


def load_index(path):
    index = {}
    for line in open(path, encoding="utf-8"):
        line = line.split("#")[0].strip()
        if not line:
            continue
        word, *phones = line.split()
        if "(" in word:                       # alternate pronunciation of an earlier word
            word = word.split("(")[0]
        try:
            key = tuple(" ".join(A2L[p.rstrip("012")] for p in phones).split())
        except KeyError:
            continue
        best = index.get(key)
        if best is None or len(word) < len(best):   # homophones: shortest wins (PoC heuristic)
            index[key] = word
    return index


def tokenize(word, labels):
    toks, i = [], 0
    labs = sorted(labels, key=len, reverse=True)
    while i < len(word):
        for L in labs:
            if word.startswith(L, i):
                toks.append(L)
                i += len(L)
                break
        else:
            toks.append(word[i])
            i += 1
    return toks


def respell(text, index):
    labels = set(A2L.values()) | {l for v in A2L.values() for l in v.split()}
    out = []
    for w in text.split():
        key = tuple(tokenize(w, labels))
        out.append(index.get(key, f"[{w}]"))       # unknown word: keep notation, bracketed
    return " ".join(out)


if __name__ == "__main__":
    index = load_index(sys.argv[1])
    print(f"reverse index: {len(index)} distinct pronunciations")
    for text in sys.argv[2:]:
        print(f"  {text}\n  -> {respell(text, index)}")
