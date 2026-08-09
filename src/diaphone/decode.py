"""Decode a notation string back into a language's orthography.

The notation is the language-neutral intermediate (base + one operator per point). Each language
carries a reverse map in `data/orth/<lang>.yaml` (label -> grapheme); the decoder tokenises a word
into labels by greedy longest-match against that language's own label set, maps each to its
grapheme, then applies the language's small assembly rules (glide spelling, Pinyin finals).

Regular orthographies round-trip exactly (Hungarian) or up to finals+tone (Pinyin). English is
non-phonemic, so it recovers a faithful *pronunciation spelling*, not the dictionary spelling.
"""
import os
import yaml

VOWELS = set("aeiou")

# Lazy-mode convenience shortcuts, per language: {alias_label: canonical_label}. Applied only when
# decode(..., lazy=True). Each alias is a base letter the language leaves free, standing in for a
# heavier canonical label — never introducing ambiguity because the letter is unused otherwise. The
# canonical orth file stays the source of truth; lazy is a typing convenience layered on top.
LAZY_ALIASES = {
    "hu": {"a": "ac", "e": "ej"},   # Hungarian has no cardinal /a/,/e/, so bare a,e are free for /ɒ/,/ɛ/
}


def load_orth(lang, data_dir="data", lazy=False):
    with open(os.path.join(data_dir, "orth", f"{lang}.yaml"), encoding="utf-8") as f:
        orth = {k: v for k, v in yaml.safe_load(f).items()}
    if lazy:
        for alias, canon in LAZY_ALIASES.get(lang, {}).items():
            if canon in orth and alias not in orth:
                orth[alias] = orth[canon]
    return orth


def tokenize(word, labels):
    """Greedy longest-match split of a word into known labels (operators never stand alone,
    so base+operator binds; longer vowel labels like `iyw` beat `iy`)."""
    labs = sorted(labels, key=len, reverse=True)
    toks, i = [], 0
    while i < len(word):
        for L in labs:
            if word.startswith(L, i):
                toks.append(L)
                i += len(L)
                break
        else:
            toks.append(word[i])   # unknown char passes through
            i += 1
    return toks


def _is_vowel(tok):
    return tok and tok[0] in VOWELS


def decode_word(word, orth, lang):
    toks = tokenize(word, orth.keys())
    out = []
    for k, t in enumerate(toks):
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        prv = toks[k - 1] if k else None
        if t == "w" and out:                          # long: geminate the previous grapheme.
            out[-1] = out[-1][0] + out[-1]            #   double its first letter — sz->ssz, t->tt (Hungarian rule)
            continue                                  #   (long *vowels* arrive as one label, aw=á, never a bare w)
        g = orth.get(t, t)
        if lang == "hu" and t == "i" and _is_vowel(nxt):
            g = "j"                                   # i-glide onset -> j  (iow -> jó)
        elif lang == "zh":
            if t == "i" and k == 0 and _is_vowel(nxt):
                g = "y"                               # i-glide onset -> y-
            elif t == "u" and _is_vowel(prv):
                g = "o"                               # final -u glide -> o  (kau -> gao)
        out.append(g)
    return "".join(out)


def decode(text, lang, data_dir="data", lazy=False):
    orth = load_orth(lang, data_dir, lazy=lazy)
    return " ".join(decode_word(w, orth, lang) for w in text.split())
