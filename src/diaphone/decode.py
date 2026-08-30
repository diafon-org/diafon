"""Decode a notation string back into a language's orthography.

The notation is the language-neutral intermediate (base + one operator per point). Each language
carries a reverse map in `data/orth/<lang>.yaml` (label -> grapheme); the decoder tokenises a word
into labels by greedy longest-match against that language's own label set, maps each to its
grapheme, then applies the language's small assembly rules (glide spelling, Pinyin finals). The
assembly rules are DATA, not code: an ordered `_rules` list in the same orth file (first match wins,
schema documented there), interpreted generically by `_rule_grapheme` — so a new language target is
pure YAML. Only two things stay code: the notation-level `w`-gemination (language-independent) and
the Mandarin tone-digit machinery (data-driven via `_TONE_MARKS`).

Regular orthographies round-trip exactly (Hungarian) or up to finals+tone (Pinyin). English is
non-phonemic, so its target is a faithful *pronunciation spelling* (a respelling), nothing more.
"""
import os
import yaml

VOWELS = set("aeiou")

def _orth_file(lang, data_dir="data"):
    with open(os.path.join(data_dir, "orth", f"{lang}.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_lazy(lang, data_dir="data"):
    """The language's loose-input shortcuts (`_lazy` in its orth file; {} if none).

    DATA, not code: a language's whole target — canonical map, loose shortcuts, context rules,
    adoption groups — lives in one YAML file, so an expert can tweak the shortcuts without touching
    Python and the export carries them unchanged. They are opt-in overlays; the canonical map stays
    the source of truth and still decodes in loose mode.
    """
    return _orth_file(lang, data_dir).get("_lazy", {})


def load_groups(lang, data_dir="data"):
    """Adoption groups (`_groups`): {group name: [labels]}. A group is the set of native spellings a
    learner switches off together; switching every group off lands exactly on the universal view."""
    return _orth_file(lang, data_dir).get("_groups", {})


def load_orth(lang, data_dir="data", lazy=False):
    orth = {k: v for k, v in _orth_file(lang, data_dir).items() if not k.startswith("_")}  # _ = meta
    if lazy:
        orth = {**orth, **load_lazy(lang, data_dir)}    # lazy shortcuts win over canonical labels
    return orth


def load_rules(lang, data_dir="data"):
    """The language's ordered context rules (`_rules` in its orth file; [] if none — e.g. EN)."""
    return _orth_file(lang, data_dir).get("_rules", [])


def resolve_off(off, lang, data_dir="data"):
    """Expand a profile's switched-off names into the set of LABELS they cover.

    A name is either an adoption group (from `_groups`) or a bare label. This is the user's
    adoption state: everything named here reverts from the native spelling to the universal glyph.
    """
    groups = load_groups(lang, data_dir)
    out = set()
    for name in off or ():
        out |= set(groups.get(name, [name]))
    return out


def apply_profile(orth, off_labels, all_ph=None, features=None, data_dir="data"):
    """Replace each switched-off label's native grapheme with its UNIVERSAL glyph.

    The fallback is deliberately the uni glyph and not the bare label, so that switching every
    group off lands exactly on the uni view — adoption is one continuous scale from a language's
    own spelling to the universal one, with no third thing at the end.
    """
    if not off_labels:
        return orth
    from .uni import uni_labels                      # local: uni imports from this module
    from .loader import load
    if all_ph is None:
        features, _languages, all_ph = load(data_dir)
    glyphs = uni_labels(all_ph, features, data_dir)
    return {k: (glyphs.get(k, v) if k in off_labels else v) for k, v in orth.items()}


def _rule_grapheme(rules, t, prv, nxt, k):
    """First matching rule's grapheme, or None. A rule matches when its token equals `t` and every
    context field it names holds: next (nxt in list) · prev (prv in list) · next_vowel · first."""
    for r in rules:
        if r["t"] != t:
            continue
        if "next" in r and nxt not in r["next"]:
            continue
        if r.get("next_vowel") and not _is_vowel(nxt):
            continue
        if "prev" in r and prv not in r["prev"]:
            continue
        if r.get("first") and k != 0:
            continue
        return r["g"]
    return None



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
    """Capitalise a grapheme string: the first character that HAS a capital takes it, so a caseless
    lead passes it on — `'` /ʔ/ gives 'Alif, not 'alif. This is the Hawaiian ʻokina rule (ʻOahu),
    and the only sensible one: the apostrophe has no capital form but the word still needs one.
    Combining marks ride along with their base."""
    for i, ch in enumerate(g):
        if ch.upper() != ch:
            return g[:i] + ch.upper() + g[i + 1:]
    return g


def apply_cap(g, up):
    """Capitalise one grapheme; returns (glyph, unresolved). `unresolved` means the glyph has no
    capital form — the apostrophe /ʔ/ — so the caller carries the capital to the NEXT glyph: 'Alif,
    not 'alif. Same rule Hawaiian uses for the ʻokina (ʻOahu)."""
    capped = up(g)
    return capped, capped == g


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


def decode_word(word, orth, lang, rules=(), tones=True):
    tone = None
    if tones and lang == "zh" and len(word) > 1 and word[-1] in "012345":
        tone, word = int(word[-1]), word[:-1]          # trailing digit on a syllable = its tone
    toks, caps = tokenize_cased(word, orth.keys())
    shout = word.isupper()                            # ALL-CAPS uppercases whole graphemes (SZ, not Sz)
    up = str.upper if shout else _cap
    out, pending = [], False
    for k, t in enumerate(toks):
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        prv = toks[k - 1] if k else None
        if t == "w" and out:                          # long: geminate the previous grapheme.
            out[-1] = out[-1][0] + out[-1]            #   double its first letter — sz->ssz, t->tt (Hungarian rule)
            continue                                  #   (long *vowels* arrive as one label, aw=á, never a bare w)
        g = _rule_grapheme(rules, t, prv, nxt, k)     # the language's context rules (orth-file `_rules`)
        if g is None:
            g = orth.get(t, t)
        if caps[k] or pending:                        # a caseless glyph passes the capital along
            g, pending = apply_cap(g, up)
        out.append(g)
    result = "".join(out)
    return _apply_tone(result, tone) if tone is not None else result


def decode(text, lang, data_dir="data", lazy=False, off=()):
    """Notation -> a language's spelling, under the reader's own adoption profile.

    TWO INDEPENDENT DIALS, each defaulting to the opposite end:
      · INPUT  defaults to the UNIVERSAL notation. `lazy=True` layers on that language's opt-in
        typing shortcuts (`_lazy`) — a single runtime switch, for flipping while typing.
      · OUTPUT defaults to the language's OWN spelling, reached by simple rules and no dictionary.
        `off` names the adoption groups (or bare labels) the reader has switched off; those revert
        to the universal glyph. With every group off, the result IS the uni view.
    """
    off_labels = resolve_off(off, lang, data_dir)
    tones = "tones" not in (off or ())        # a group that switches a code path, not a label set
    orth = apply_profile(load_orth(lang, data_dir, lazy=lazy), off_labels, data_dir=data_dir)
    rules = [r for r in load_rules(lang, data_dir)
             if r.get("group") not in off and r.get("t") not in off_labels]
    words = []
    for w in text.split():
        if lang == "zh":
            piece, seg = "", ""
            for ch in w:                # any digit closes a syllable, mid-word too (zhong1guo2)
                if ch.isdigit():
                    piece += decode_word(seg + ch, orth, lang, rules, tones)
                    seg = ""
                else:
                    seg += ch
            words.append(piece + (decode_word(seg, orth, lang, rules, tones) if seg else ""))
        else:
            words.append(decode_word(w, orth, lang, rules, tones))
    return " ".join(words)
