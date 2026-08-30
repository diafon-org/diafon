"""Proof of concept: SEAMLESS streaming conversion — commit-as-you-type, no manual commit.

The Mac input method wants each glyph emitted the moment the keystroke stream can no longer
change it, holding only the undecidable tail. This prototypes that committer per target and
validates it: feeding the corpus char-by-char must produce byte-identical output to the batch
renderer, while measuring the maximum number of cached (uncommitted) keystrokes.

Rules that force caching:
  · token ambiguity   — `s` may still become `sj`/`sjj`/`sw`/`sy`: hold while a longer label matches
  · HU/EN next-token  — HU i→j before a vowel; `w` doubles the previous grapheme: hold ONE token
  · ZH syllable       — the tone digit at syllable end marks an EARLIER vowel, and the retroflex
                        series spells j/q/x vs zh/ch/sh by the FOLLOWING vowel: hold the syllable

Usage:  PYTHONPATH=src python3 scripts/stream_poc.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from diaphone.loader import load
from diaphone.uni import uni_labels
from diaphone.render import _TONE_SUP
from diaphone.render import ipa_labels
from diaphone.decode import load_orth, load_rules, decode_word, decode
from diaphone.engine import render

DATA = "data"


class MapStreamer:
    """Universal targets (uni/ipa): greedy tokens over a label→glyph map, minimal hold."""

    def __init__(self, mapping, use_sup=False):
        self.map, self.labels = mapping, set(mapping)
        self.use_sup = use_sup                    # superscript tone digits: IPA only
        self.pending = ""
        self.max_cache = 0

    def feed(self, c):
        if c == " " or c in _TONE_SUP:
            out = self._drain(final=True) + (_TONE_SUP[c] if self.use_sup and c in _TONE_SUP else c)
            return out
        self.pending += c
        self.max_cache = max(self.max_cache, len(self.pending))
        return self._drain(final=False)

    def flush(self):
        return self._drain(final=True)

    def _drain(self, final):
        out = ""
        while self.pending:
            if not final and any(L != self.pending and L.startswith(self.pending) for L in self.labels):
                break                                   # could still grow into a longer label — hold
            for L in sorted(self.labels, key=len, reverse=True):
                if self.pending.startswith(L):
                    out += self.map[L]
                    self.pending = self.pending[len(L):]
                    break
            else:
                out += self.pending[0]
                self.pending = self.pending[1:]
        return out


class WordStreamer:
    """Language targets: same token stream, but hold ONE token for the next-token rules (HU i-glide,
    `w` gemination); ZH instead holds the whole syllable (tone digit + retroflex need it)."""

    def __init__(self, lang):
        self.lang = lang
        self.orth = load_orth(lang, DATA)
        self.rules = load_rules(lang, DATA)
        self.buf = ""
        self.max_cache = 0

    def feed(self, c):
        if c == " ":
            return self.flush() + " "
        self.buf += c
        self.max_cache = max(self.max_cache, len(self.buf))
        if self.lang == "zh":
            if c.isdigit():                              # tone digit closes the syllable
                out = decode_word(self.buf, self.orth, self.lang, self.rules)
                self.buf = ""
                return out
            return ""                                    # hold the open syllable
        # hu/en: commit the longest prefix whose decode can no longer change. Conservative and
        # simple: decode the whole buffer twice — once as-is, once with a probe vowel appended;
        # the common prefix of the two is safe to commit.
        as_is = decode_word(self.buf, self.orth, self.lang, self.rules)
        probed = decode_word(self.buf + "a", self.orth, self.lang, self.rules)
        safe = os.path.commonprefix([as_is, probed])
        # keep enough raw tail to regenerate the unsafe remainder: back off one token conservatively
        if safe and safe == as_is[:len(safe)]:
            # find the shortest raw suffix that still decodes to the unsafe tail
            for cut in range(len(self.buf)):
                if decode_word(self.buf[cut:], self.orth, self.lang, self.rules) == as_is[len(safe):] and \
                   decode_word(self.buf[cut:] + "a", self.orth, self.lang, self.rules) == probed[len(safe):]:
                    self.buf = self.buf[cut:]
                    return safe
        return ""

    def flush(self):
        out = decode_word(self.buf, self.orth, self.lang, self.rules) if self.buf else ""
        self.buf = ""
        return out


CORPUS = [
    "sjok sewp njawr", "kecsecnecm sewpejn", "acswonj", "hoswuw", "ejdj nacdj kutjac",
    "ejdj kisj kutjac aclsik acz acstacl aclactt", "pjatj", "sjj zjj kc gc", "tyy dyy syy zyy",
    "baqd", "dxax kat sijts acn dxax mat", "sji sejlz fijsj",
    "sjan1 kxaxn3 kau1", "tqonx1 kuo2 tqya2 kxaxn3 kxau3", "tqi1 sji1 tquc1 sjuc4", "nic3", "raxn2",
]


def run():
    features, _langs, all_ph = load(DATA)
    nat = uni_labels(all_ph, features, DATA)
    ipa = ipa_labels(all_ph, features, DATA)
    fail = total = 0
    report = {}
    for tgt, make, batch in [
        ("uni", lambda: MapStreamer(nat), lambda t: render(t, "uni", DATA)),
        ("ipa", lambda: MapStreamer(ipa, use_sup=True), lambda t: render(t, "ipa", DATA)),
        ("hu", lambda: WordStreamer("hu"), lambda t: decode(t, "hu", DATA)),
        ("en", lambda: WordStreamer("en"), lambda t: decode(t, "en", DATA)),
        ("zh", lambda: WordStreamer("zh"), lambda t: decode(t, "zh", DATA)),
    ]:
        worst = 0
        for text in CORPUS:
            s = make()
            got = "".join(s.feed(c) for c in text) + s.flush()
            want = batch(text)
            total += 1
            if got != want:
                fail += 1
                print(f"  MISMATCH [{tgt}] {text!r}\n    stream: {got!r}\n    batch : {want!r}")
            worst = max(worst, s.max_cache)
        report[tgt] = worst
    print(f"{total - fail}/{total} stream==batch" + ("" if fail else "  ✓"))
    print("max cached keystrokes:", " · ".join(f"{k}: {v}" for k, v in report.items()))
    return fail


if __name__ == "__main__":
    sys.exit(1 if run() else 0)
