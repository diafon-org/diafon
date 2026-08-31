"""export_data() must be SUFFICIENT for a port: a minimal consumer built from the exported dict
ALONE must reproduce render() byte-for-byte — including the per-language assembly rules, which the
export carries as data (`rules`), interpreted here by a ~10-line generic matcher. This mirrors how
the Swift/JS ports are validated — if this passes, a port has everything it needs, and a new
language target is pure data end to end."""
import os

from diaphone.engine import export_data, render

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

CORPUS = [
    "sjok sewp njawr", "kecsecnecm sewpejn", "acswonj", "hoswuw", "ejdj nacdj kutjac",
    "ejdj kisj kutjac aclsik acz acstacl aclactt", "pjatj", "sy zy py ky", "tx dx sy zy",
    "h hx hj hq", "r rc rj rx aq", "baqd", "dyax kat sijts acn dyax mat", "sji sejlz fijsj",
    "sjan1 kxaxn3 kau1", "tqony1 kuo2 tqya2 kxaxn3 kxau3", "tqi1 sji1 tquc1 sjuc4",
    "nic3", "de5", "de0", "raxn2", "alma kert", "ni3 hao3", "zhong1 guo2", "xiao3", "cai4",
    "tqony1kuo2 niu2nai3", "sji1kua1 tqoc4sjuc4",
    "iu3 ui4 un2 u3 i1 ican2 puo1 aq2 iny1 uny1",
    "tx nx lx rx", "pj kj bj sy", "tj dj nj lj",
    "hacix ixow fiuw", "ixejs uxejst", "ix ux icx ucx",
    "sjiau3 liu2 tou1", "berd werld show boy law", "dhuh kat sijts awn dhuh flawr",
]

VOWELS = set("aeiou")


def _tok(word, labels):
    labs = sorted(labels, key=len, reverse=True)
    toks, i = [], 0
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


def _tone_sign(glyphs, toks, digit, signs):
    """Tone-sign placement a port needs: within the LAST vowel group, first a-based token, else
    e-based, else o-based, else the LAST vowel (= Pinyin placement)."""
    import unicodedata
    if digit in ("0", "5"):
        return glyphs
    mark = signs.get(digit)
    if mark is None:
        return glyphs + [digit]
    group = []
    for i, t in enumerate(toks):
        if t and t[0] in VOWELS:
            group = group + [i] if group and group[-1] == i - 1 else [i]
    if not group:
        return glyphs + [digit]
    pick = next((i for b in "aeo" for i in group if toks[i][0] == b), group[-1])
    glyphs[pick] = unicodedata.normalize("NFC", glyphs[pick] + mark)
    return glyphs


def _uni(data, text, target, tones=False):
    m, sup = data["maps"][target], data["toneSup"]

    def seg_out(seg, digit=None):
        toks = _tok(seg, data["keys"])
        glyphs = [m.get(t, t) for t in toks]
        if digit is not None:
            if target == "ipa":
                glyphs.append(sup.get(digit, digit))            # superscript = IPA only (no sup 0)
            elif tones:
                glyphs = _tone_sign(glyphs, toks, digit, data["toneSigns"])
            else:
                glyphs.append(digit)                            # uni default: plain digit
        return "".join(glyphs)

    out = []
    for w in text.split():
        piece, seg = "", ""
        for ch in w:                     # a tone digit closes its segment anywhere in the word
            if ch in "012345":
                piece += seg_out(seg, digit=ch)
                seg = ""
            else:
                seg += ch
        out.append(piece + (seg_out(seg) if seg else ""))
    return " ".join(out)


def _apply_tone(py, tone, marks):
    if tone in (0, 5):
        return py
    put = lambda i: py[:i] + marks[py[i]][tone - 1] + py[i + 1:]
    if "a" in py:
        return put(py.index("a"))
    if "e" in py:
        return put(py.index("e"))
    if "ou" in py:
        return put(py.index("o"))
    for i in range(len(py) - 1, -1, -1):
        if py[i] in marks:
            return put(i)
    return py


def _rule_g(rules, t, prv, nxt, k):
    """The generic rule interpreter a port needs — first matching rule's grapheme, or None."""
    for r in rules:
        if r["t"] != t:
            continue
        if "next" in r and nxt not in r["next"]:
            continue
        if r.get("next_vowel") and not (nxt and nxt[0] in VOWELS):
            continue
        if "prev" in r and prv not in r["prev"]:
            continue
        if r.get("first") and k != 0:
            continue
        return r["g"]
    return None


def _lang(data, text, lang, lazy=False):
    orth = dict(data["orth"][lang])
    if lazy:
        orth.update(data["lazy"].get(lang, {}))
    rules, marks = data["rules"][lang], data["toneMarks"]
    words = []
    for w in text.split():
        if lang == "zh" and any(c.isdigit() for c in w[:-1]):   # syllables joined in one word
            piece, seg = "", ""
            for ch in w:
                if ch.isdigit():
                    piece += _lang(data, seg + ch, lang, lazy)
                    seg = ""
                else:
                    seg += ch
            words.append(piece + (_lang(data, seg, lang, lazy) if seg else ""))
            continue
        tone = None
        if lang == "zh" and len(w) > 1 and w[-1] in "012345":
            tone, w = int(w[-1]), w[:-1]
        toks = _tok(w, orth.keys())
        out = []
        for k, t in enumerate(toks):
            nxt = toks[k + 1] if k + 1 < len(toks) else None
            prv = toks[k - 1] if k else None
            if t == "w" and out:
                out[-1] = out[-1][0] + out[-1]
                continue
            g = _rule_g(rules, t, prv, nxt, k)
            if g is None:
                g = orth.get(t, t)
            out.append(g)
        res = "".join(out)
        words.append(_apply_tone(res, tone, marks) if tone is not None else res)
    return " ".join(words)


def test_export_data_is_sufficient_for_a_port():
    data = export_data(DATA)
    for text in CORPUS:
        for tgt in ("uni", "ipa"):
            assert _uni(data, text, tgt) == render(text, tgt, DATA), (tgt, text)
        assert _uni(data, text, "uni", tones=True) == \
            render(text, "uni", DATA, tones=True), ("uni tones", text)
        for lg in ("hu", "zh", "en"):
            assert _lang(data, text, lg) == render(text, lg, DATA), (lg, text)
            assert _lang(data, text, lg, lazy=True) == render(text, lg, DATA, lazy=True), (lg, "lazy", text)


def test_universal_maps_invert_for_recompose():
    """Backspace-to-recompose (Mac) reverse-maps glyph -> label. Both universal maps must be
    perfectly injective — the view is strictly universal, no flavour licences."""
    data = export_data(DATA)
    for tgt, m in data["maps"].items():
        seen = {}
        for lab, g in sorted(m.items()):
            assert g not in seen, (tgt, g, seen.get(g), lab)
            seen[g] = lab


def test_export_json_cli_writes_valid_json(tmp_path):
    import json
    from diaphone.cli import main
    out = tmp_path / "engine.json"
    main(["export-json", "--data", DATA, "--out", str(out)])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["version"] == 2
    assert set(data["maps"]) == {"uni", "ipa"}
    assert data["maps"]["uni"]["sj"] == "ș"
    assert data["keys"] == sorted(data["keys"], key=len, reverse=True)[:len(data["keys"])]
    assert set(data["orth"]) == {"en", "hu", "zh"}
    assert set(data["rules"]) == {"en", "hu", "zh"}     # assembly rules travel as data
    assert data["rules"]["en"] == [] and len(data["rules"]["zh"]) == 14
    assert set(data["toneSigns"]) == {"1", "2", "3", "4"}
    for gone in ("enDict", "enCanon", "tonesOn", "zhRetro"):
        assert gone not in data
