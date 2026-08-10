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

# Mandarin retroflex/alveolo-palatal series: (spelling before non-front vowel, spelling before front i/ü).
# We merged Pinyin j/q/x into zh/ch/sh as allophones, so the following vowel decides the spelling.
_ZH_RETRO = {"tq": ("zh", "j"), "tqh": ("ch", "q"), "sj": ("sh", "x")}

# Lazy-mode shortcuts, per language: {alias_label: grapheme}. Applied (overriding the canonical map)
# only when decode(..., lazy=True). The canonical orth file stays the source of truth; lazy is an
# opt-in typing convenience layered on top.
#   HU: no cardinal /a/,/e/, so bare a,e are free to spell /ɒ/,/ɛ/.
#   ZH: "type Pinyin". The initials/finals below spell themselves literally, so `xiao`=xiǎo, `shi`=shì,
#       `zhong`=zhōng, `zao`=zǎo, `cai`=cài. The one Pinyin letter set NOT added is the aspirated stops
#       p/t/k — those clash with the notation (where p/t/k are the *lenis* series), so canonical still
#       works in lazy mode; for aspirated stops use the notation ph/th/kh. m/n/l/f/s/b/d/g coincide.
LAZY_ALIASES = {
    "hu": {"a": "a", "e": "e"},
    "zh": {"b": "b", "d": "d", "g": "g", "z": "z", "c": "c", "zh": "zh", "ch": "ch",
           "sh": "sh", "r": "r", "j": "j", "q": "q", "x": "x", "h": "h", "e": "e", "o": "o"},
}


def load_orth(lang, data_dir="data", lazy=False):
    with open(os.path.join(data_dir, "orth", f"{lang}.yaml"), encoding="utf-8") as f:
        orth = {k: v for k, v in yaml.safe_load(f).items()}
    if lazy:
        orth = {**orth, **LAZY_ALIASES.get(lang, {})}   # lazy shortcuts win over canonical labels
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


# Pinyin tone diacritics, indexed [tone-1]; placement is a>e>(ou→o)>last vowel (the standard rule).
_TONE_MARKS = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ"}


def _apply_tone(pinyin, tone):
    if tone in (0, 5):                                 # neutral tone — no diacritic
        return pinyin
    s = pinyin

    def put(i):
        return s[:i] + _TONE_MARKS[s[i]][tone - 1] + s[i + 1:]
    if "a" in s:
        return put(s.index("a"))
    if "e" in s:
        return put(s.index("e"))
    if "ou" in s:
        return put(s.index("o"))
    for i in range(len(s) - 1, -1, -1):                # otherwise the last vowel takes the tone
        if s[i] in _TONE_MARKS:
            return put(i)
    return s


def decode_word(word, orth, lang):
    tone = None
    if lang == "zh" and len(word) > 1 and word[-1] in "012345":
        tone, word = int(word[-1]), word[:-1]          # trailing digit on a syllable = its tone
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
            if t in _ZH_RETRO:
                # the merged retroflex/alveolo-palatal series spells j/q/x before a front vowel
                # (i or ü), zh/ch/sh otherwise — the Pinyin allophone split we folded away.
                g = _ZH_RETRO[t][nxt in ("i", "ic")]
            elif t == "ic" and prv in _ZH_RETRO:
                g = "u"                               # ü is written "u" after j/q/x (ju, qu, xu)
            elif t == "i" and k == 0 and _is_vowel(nxt):
                g = "y"                               # i-glide onset -> y-
            elif t == "u" and prv == "a":
                g = "o"                               # -u offglide spells "o" only after a: au->ao,
                                                      #   but ou stays "ou" and medial u (uo) stays "u"
                                                      # (apical vowel `uc` -> "i" comes from the orth map)
        out.append(g)
    result = "".join(out)
    return _apply_tone(result, tone) if tone is not None else result


def decode(text, lang, data_dir="data", lazy=False):
    orth = load_orth(lang, data_dir, lazy=lazy)
    return " ".join(decode_word(w, orth, lang) for w in text.split())
