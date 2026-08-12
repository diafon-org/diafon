"""export_data() must be SUFFICIENT for a port: a minimal consumer built from the exported dict
alone (plus the small documented rules in decode.py) must reproduce render() byte-for-byte.
This mirrors how the Swift/JS ports are validated — if this passes, a port has everything it needs."""
import os

from diaphone.engine import export_data, render

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

CORPUS = [
    "sjok sewp njawr", "kecsecnecm sewpejn", "acswonj", "hoswuw", "ejdj nacdj kutjac",
    "ejdj kisj kutjac aclsik acz acstacl aclactt", "pjatj", "sjj zjj kc gc", "ty dy sy zy",
    "h hj hc hq", "baqd", "dxax kat sijts acn dxax mat", "sji sejlz fijsj",
    "sjan1 kxaxn3 kau1", "tqonx1 kuo2 tqha2 kxaxn3 kxau3", "tqi1 sji1 tquc1 sjuc4",
    "nic3", "de5", "raxn2", "alma kert", "ni3 hao3", "zhong1 guo2", "xiao3", "cai4",
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


def _uni(data, text, target):
    m, sup = data["maps"][target], data["toneSup"]
    out = []
    for w in text.split():
        tone = ""
        if len(w) > 1 and w[-1] in sup:
            tone, w = sup[w[-1]], w[:-1]
        out.append("".join(m.get(t, t) for t in _tok(w, data["keys"])) + tone)
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


def _lang(data, text, lang, lazy=False):
    orth = dict(data["orth"][lang])
    if lazy:
        orth.update(data["lazy"].get(lang, {}))
    retro, marks = data["zhRetro"], data["toneMarks"]
    words = []
    for w in text.split():
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
            g = orth.get(t, t)
            if lang == "hu" and t == "i" and nxt and nxt[0] in VOWELS:
                g = "j"
            elif lang == "zh":
                if t in retro:
                    g = retro[t][nxt in ("i", "ic")]
                elif t == "ic" and prv in retro:
                    g = "u"
                elif t == "i" and k == 0 and nxt and nxt[0] in VOWELS:
                    g = "y"
                elif t == "u" and prv == "a":
                    g = "o"
            out.append(g)
        res = "".join(out)
        words.append(_apply_tone(res, tone, marks) if tone is not None else res)
    return " ".join(words)


def test_export_data_is_sufficient_for_a_port():
    data = export_data(DATA)
    for text in CORPUS:
        for tgt in ("native", "ipa", "native-hu", "native-zh"):
            assert _uni(data, text, tgt) == render(text, tgt, DATA), (tgt, text)
        for lg in ("hu", "zh", "en"):
            assert _lang(data, text, lg) == render(text, lg, DATA), (lg, text)
            assert _lang(data, text, lg, lazy=True) == render(text, lg, DATA, lazy=True), (lg, "lazy", text)


def test_export_json_cli_writes_valid_json(tmp_path):
    import json
    from diaphone.cli import main
    out = tmp_path / "engine.json"
    main(["export-json", "--data", DATA, "--out", str(out)])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert set(data["maps"]) == {"native", "ipa", "native-hu", "native-zh"}
    assert data["maps"]["native"]["sj"] == "s̩" and data["maps"]["native-hu"]["ac"] == "a"
    assert data["keys"] == sorted(data["keys"], key=len, reverse=True)[:len(data["keys"])]
    assert set(data["orth"]) == {"en", "hu", "zh"}
