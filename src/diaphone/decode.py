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
    # EN simplified input: the familiar digraphs (+ bare j/y/w — all free letters in English, which
    # has no length, nasal vowels or emphatics), and the orthographic vowel digraphs (ee see, er bird,
    # ay day, ow show, aw law, oy boy, oo moon, uh the). Values are the respell graphemes; EN_CANON
    # below maps the same aliases to canonical labels so the dictionary can look up either spelling.
    "en": {"sh": "sh", "ch": "ch", "zh": "zh", "ng": "ng", "th": "th", "dh": "th",
           "j": "j", "y": "y", "w": "w",
           "ee": "ee", "oo": "oo", "er": "er", "ay": "ay", "ow": "ow", "aw": "aw",
           "oy": "oy", "uh": "u"},
}

# alias -> canonical label(s), for normalising loosely-typed EN before a dictionary lookup
EN_CANON = {"sh": "sj", "ch": "tq", "zh": "zj", "ng": "nx", "th": "tx", "dh": "dx",
            "j": "dq", "y": "i", "w": "u",
            "ee": "i", "oo": "u", "er": "aq", "ay": "e", "ow": "o", "aw": "oj",
            "oy": "oji", "uh": "ax"}


def load_orth(lang, data_dir="data", lazy=False):
    with open(os.path.join(data_dir, "orth", f"{lang}.yaml"), encoding="utf-8") as f:
        orth = {k: v for k, v in yaml.safe_load(f).items()}
    if lazy:
        orth = {**orth, **LAZY_ALIASES.get(lang, {})}   # lazy shortcuts win over canonical labels
    return orth


_EN_DICT_CACHE = {}


def en_dict(data_dir="data"):
    """The EN loose-view dictionary: notation word -> real English spelling (data/en_dict.json,
    built by scripts/build_en_dict.py from CMUdict x word frequency). Keys are notation as typed."""
    if data_dir not in _EN_DICT_CACHE:
        import json
        with open(os.path.join(data_dir, "en_dict.json"), encoding="utf-8") as f:
            d = json.load(f)
        _EN_DICT_CACHE[data_dir] = {k: v for k, v in d.items() if not k.startswith("__")}
    return _EN_DICT_CACHE[data_dir]


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


def _cap(g):
    """Capitalise the first character of a grapheme string (combining marks ride along)."""
    return g[:1].upper() + g[1:] if g else g


def tokenize_cased(word, labels):
    """Case-insensitive tokenize: (lowercase tokens, per-token was-capitalised flags)."""
    low = word.lower()
    toks = tokenize(low, labels)
    caps, i = [], 0
    for t in toks:
        caps.append(word[i].isupper())
        i += len(t)
    return toks, caps


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
    toks, caps = tokenize_cased(word, orth.keys())
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
        out.append(_cap(g) if caps[k] else g)
    result = "".join(out)
    return _apply_tone(result, tone) if tone is not None else result


# Unified-mode accent combos (Hungarian typed TRADITIONALLY — sz/ny/gy literal — plus these) and
# their doubling escapes for English words that contain a combo (neww -> new, musicc -> music).
_AUTO_ACC = {"ecw": "ő", "icw": "ű", "aw": "á", "ew": "é", "iw": "í", "ow": "ó", "uw": "ú",
             "ec": "ö", "ic": "ü"}
_AUTO_ESC = {"aww": "aw", "eww": "ew", "iww": "iw", "oww": "ow", "uww": "uw",
             "icc": "ic", "ecc": "ec"}
_AUTO_KEYS = sorted({**_AUTO_ACC, **_AUTO_ESC}, key=len, reverse=True)


def _auto_accents(seg):
    """Apply the accent combos (case-carrying) to a letter run; everything else passes."""
    out, i = "", 0
    while i < len(seg):
        low = seg.lower()
        for k in _AUTO_KEYS:
            if low.startswith(k, i):
                g = _AUTO_ESC.get(k) or _AUTO_ACC[k]
                out += _cap(g) if seg[i].isupper() else g
                i += len(k)
                break
        else:
            out += seg[i]
            i += 1
    return out


def decode_auto(text, data_dir="data"):
    """The UNIFIED mode — English, traditional Hungarian and Pinyin in one stream, no wordlist:
      · everything passes through as typed, EXCEPT
      · the accent combos aw ew iw ow uw ec ic (+ w for the long ő ű) -> á é í ó ú ö ü ő ű,
        escaped by doubling the operator where English collides (neww -> new, musicc -> music);
      · a chunk closed by a tone digit (1-5) is REAL Pinyin (p/t/k literal) if it reads as one
        (has a vowel, all tokens known) — ma1 -> mā; a doubled digit escapes (item22 -> item2).
    Hungarian consonants are typed traditionally (sz ny gy ...); the phonemic notation lives in
    the dedicated HU mode."""
    zh = {**load_orth("zh", data_dir, lazy=True),
          "p": "p", "t": "t", "k": "k", "w": "w", "y": "y"}   # + the Pinyin glide letters
    out, buf = [], ""

    def flush():
        nonlocal buf
        if buf:
            out.append(_auto_word(buf, zh))
            buf = ""
    for ch in text:
        if ch.isalnum():
            buf += ch
        else:                                   # space & punctuation are boundaries
            flush()
            out.append(ch)
    flush()
    return "".join(out)


def _auto_word(buf, zh):
    out, seg, i = "", "", 0
    while i < len(buf):
        ch = buf[i]
        if ch in "12345":
            if i + 1 < len(buf) and buf[i + 1] == ch:       # doubled digit = escape, keep raw
                out += seg + ch
                i += 2
            elif seg and any(c in VOWELS for c in seg.lower())                     and all(t in zh for t in tokenize(seg.lower(), zh.keys())):
                out += decode_word(seg + ch, zh, "zh")      # reads as Pinyin: convert
                i += 1
            else:
                out += seg + ch                             # v2, x1, plain numbers: keep raw
                i += 1
            seg = ""
        else:
            seg += ch
            i += 1
    return out + _auto_accents(seg)


def decode(text, lang, data_dir="data", lazy=False, endict=False):
    """lazy = the language's loose INPUT (typing shortcuts). endict (EN only) = the dictionary
    view: real spelling where known, respelling otherwise; typed aliases are canonicalised first,
    so `shijp` and `sjijp` both find "ship"."""
    use_aliases = lazy or (endict and lang == "en")
    orth = load_orth(lang, data_dir, lazy=use_aliases)
    d = en_dict(data_dir) if (endict and lang == "en") else None
    words = []
    for w in text.split():
        if d is not None:
            key = "".join(EN_CANON.get(t, t) for t in tokenize(w.lower(), orth.keys()))
            if key in d:
                words.append(_cap(d[key]) if w[:1].isupper() else d[key])   # Dhuh -> The
                continue
        if lang == "zh":
            piece, seg = "", ""
            for ch in w:                # any digit closes a syllable, mid-word too (zhong1guo2)
                if ch.isdigit():
                    piece += decode_word(seg + ch, orth, lang)
                    seg = ""
                else:
                    seg += ch
            words.append(piece + (decode_word(seg, orth, lang) if seg else ""))
        else:
            words.append(decode_word(w, orth, lang))
    return " ".join(words)
