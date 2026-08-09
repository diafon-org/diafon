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


def load_orth(lang, data_dir="data"):
    with open(os.path.join(data_dir, "orth", f"{lang}.yaml"), encoding="utf-8") as f:
        return {k: v for k, v in yaml.safe_load(f).items()}


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
        g = orth.get(t, t)
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        prv = toks[k - 1] if k else None
        if lang == "hu" and t == "i" and _is_vowel(nxt):
            g = "j"                                   # i-glide onset -> j  (iow -> jó)
        elif lang == "zh":
            if t == "i" and k == 0 and _is_vowel(nxt):
                g = "y"                               # i-glide onset -> y-
            elif t == "u" and _is_vowel(prv):
                g = "o"                               # final -u glide -> o  (kau -> gao)
        out.append(g)
    return "".join(out)


def decode(text, lang, data_dir="data"):
    orth = load_orth(lang, data_dir)
    return " ".join(decode_word(w, orth, lang) for w in text.split())
