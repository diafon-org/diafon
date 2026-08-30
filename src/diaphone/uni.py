"""The `uni` target: notation → OUR universal view, Latin plus diacritics (see docs/uni-view.md).

Like `render.ipa_labels`, this is a language-independent label→glyph map, built from a hand-assigned
per-point base glyph plus generative modifier diacritics. All cells are decided (see the doc).

The mark grammar — MEANING = mark shape and count, SIDE = typography per letter; nothing ever
sits above a tall letter:
  one dot   = a derived point — the x-family ṭ ḍ ḳ ġ ṇ (θ ð x ɣ ŋ) · pf ṗ ·
              the schwa ạ (ax = a + the x-dot) · lowered vowels ị ẹ ụ ọ ·
              the tap ṛ (`rc`) · the pharyngeal ḥ (`hx`)
  two dots  = the second-degree mark — aspiration t̤ k̤ c̤ (p̈ above on the descender, c̦̈ above
              on the marked c̦; the vocalic r̈) ·
              FLIP front↔back on a vowel (ü ö · ï ë ä)
  tilde     = nasal above a vowel (ã) · below, the PHARYNGEALISED MODIFIER and nothing else —
              the emphatics t̰ d̰ s̰ z̰ (U+0330). A point never wears a modifier-only MARK
              (no point LABEL contains y, yy or w). The letters are a separate matter: w is
              the glyph for the /w/ glide — a glyph is not a label.
  comma     = the `j` mark — the hush points ș z̦ c̦ x̦, every soft consonant ț d̦ n̦ l̦ p̓ k̦ b̦ r̦ …
              and the glottal stop h̦ (U+0326 below / U+0313 above); doubled only where the single
              comma would already spell a point (sjj zjj → s͈ z͈; tcj → c͈, whose single-comma c̦
              is the tq point)
  "\\" tail  = retroflex (U+0316) — rides below (t̖ n̖ l̖ r̖; labels lx rx, doubled txx nxx
              where base+x is a point), replacing the j-comma rather than stacking on it

THE r BASE IS REGULAR. `c` gives the tap (`rc` → the dot, as `c`/`x` do everywhere) and `j` gives
the soft r (`rj` → the comma, as `j` does everywhere), so r carries five sounds on five marks with no
exception at all: r · ṛ · r̦ · r̖ · r̈. The soft r is a plain member of the soft series (k̦ b̦ m̦ r̦),
one j and one comma, and nothing on r doubles. What `c` MEANS is base-dependent, as every operator
is — affricate on t/d, pharyngeal on h, the second rhotic on r — but the MARK it draws never varies.

THE MARK ALWAYS FOLLOWS THE OPERATOR — no exceptions anywhere. `c`/`x` draw the dot, `j` draws the
comma, on every base. What an operator MEANS is base-dependent — `c` is affricate on t/d, the tap on
r, the pharyngeal on h; `j` is palatal everywhere except h, where it gives the glottal stop — but
what it DRAWS never varies. So ḥ = /ħ/ (`hx`, the dot — and `x` means here exactly what it means
everywhere, the fricative one step back, as in `tx`=θ and `kx`=x) and h̦ = /ʕ/ (`hj`, the comma):
the one comma in the view on a sound that is not palatal, and it is there because `j` put it there.
ḥ also happens to be how the world already writes Arabic ح (Muḥammad).

/ʔ/ IS THE APOSTROPHE. `q` = `c`+`j` and composes BOTH marks where it can (`iq`=ụ̈, `eq`=ọ̈: the
c-dot below, the j-mark above). On h it cannot: the dot is already ḥ, two below marks never stack,
and **nothing sits above a tall letter** — so `hq` has no glyph the grammar can build, and it takes
a whole character like the other overflow points (c=/ts/, x=/dz/, q=/q/). Which SOUND gets that
character is decided by precedent, because a whole character has no shape the grammar could derive:
it goes to /ʔ/, the glottal stop, written **'** in Hawaiian, Samoan, Tongan and Māori (the ʻokina),
across Mayan, in Tagalog and Guaraní, and as hamza in ASCII Arabic — and /ʔ/ is in five of the 23
languages against one for /ʕ/. U+0027 is also the only candidate every font and keyboard has (40/40
scanned fonts, against 27/40 for ʼ U+02BC and 18/40 for ʿ U+02BF). Two prices, both accepted
knowingly: it is punctuation, not a letter, so a word-break splits it off and some editors
autocorrect it to ’; and it has no capital form.
Side: below by default; ABOVE only on the descenders p g (ṗ ġ p̈ p̓ g̓) and on a glyph whose
below zone is already marked (c̦ → c̦̈). Generic mark placement varies by font; the bespoke font
fixes that. The soft coronals ARE the palatal sounds — /c ɟ ɲ ʎ/ and /tʲ dʲ nʲ lʲ/ are one point
each — so Hungarian ty, Spanish ñ and Russian ть нь all draw ț n̦: one j, one comma.

Vowels: `j` lowers (one dot below — ị ẹ ụ ọ), two dots flip front↔back (ü ö · ï ë ä), nasal
`y` is the tilde (ã ẽ õ), and long is the acute — except on a FLIPPED vowel, where the two dots
become the DOUBLE acute (ű ő i̋ e̋ a̋ · ụ̋ ọ̋), so marks never stack. GLIDES (nonsyllabic close vowels, labels ix ux icx ucx) get readable
letters: j w and — carrying their vowel's flip mark — j̈ ẅ for the rounded/unrounded pair; the vocalic r is r̈ —
the r-family: r trill · ṛ tap (rc) · r̦ soft (rj) · r̖ retroflex · r̈ vocalic. The view is strictly
universal — one glyph per label, no per-language flavours (a language's own orthography is its
language target).
"""
import unicodedata

from .decode import tokenize, tokenize_cased, _cap, apply_cap
from .notation import _label_maps, _mod_chars, full_label, doubles

# combining marks
_DB = "̣"                   # U+0323 one dot below (the derived-point dot)
_DDA, _DDB = "̈", "̤"      # U+0308 / U+0324 two dots above / below (the second-degree mark)
_TILDE_B = "̰"              # U+0330 tilde below (the emphatics — the dark colour)
_VLB = "̦"                  # U+0326 COMBINING COMMA BELOW — the j-mark (one j = one comma). Chosen over
                            #   the vertical line U+0329: better covered (9/10 common fonts vs 6/10), it
                            #   leans like the retroflex tail instead of standing vertical, and NFC folds
                            #   s/t into the PRECOMPOSED ș ț (U+0219/U+021B) that every Latin font has.
_VLA = "̓"                  # U+0313 combining comma above (the same mark on the descenders p g)
_DVLB = "͈"                 # U+0348 combining double vertical line below (two j's — sjj zjj,
                            #   i.e. wherever base+j is itself a point). NOTE: Unicode has NO double comma
                            #   below, so the doubled form cannot match the single one's shape — the pair
                            #   reads by count-and-weight, not by the same mark twice. It is also the
                            #   worst-covered mark we use (4/10 fonts), and only ET RU UK need it.
_DVLA = "̎"                 # U+030E combining double vertical line above (ditto on descenders)
_GRB = "̖"                  # U+0316 combining grave below — the "\" tail (retroflex; flips a "/" tail)
_TILDE, _ACUTE = "̃", "́"
_DACUTE = "̋"               # U+030B double acute — a flipped vowel's long form (ű ő i̋ e̋ a̋)

_DESCENDERS = "pg"          # letters whose below zone the letterform itself occupies


def _below_taken(g):
    """Side rule: a mark goes ABOVE when the letter's below zone is taken — a descender letter,
    or a glyph already wearing a below mark (c̦ → c̦̈). Meaning never rides on the side."""
    return g[0] in _DESCENDERS or any(m in g for m in (_VLB, _DVLB, _DB, _DDB))

# point label -> uni base glyph
_CONS = {
    "p": "p", "b": "b", "t": "t", "d": "d", "k": "k", "g": "g",
    "kq": "q",                                       # q = the uvular LETTER-point (see below)
    "m": "m", "n": "n", "nx": "ṇ",                                # ṇ (velar ŋ: x = dot)
    "tc": "c", "dc": "x", "pc": "ṗ",                            # the affricate LETTER-pair c /ts/ · x /dz/ · ṗ (pf)
    "tq": "c" + _VLB, "dq": "x" + _VLB,                            # c̦ x̦ (hush = affricate + the j-stroke)
    "f": "f", "v": "v", "tx": "ṭ", "dx": "ḍ",                  # ṭ ḍ (dental fricatives: x = dot below)
    "s": "s", "z": "z", "sj": "s" + _VLB, "zj": "z" + _VLB,        # ș z̦ (ʃ ʒ)
    "kx": "ḳ", "gx": "ġ", "hx": "h" + _DB, "hj": "h" + _VLB, "hq": "'", "h": "h",  # ḳ ġ (velar: x = dot; above on g) · ḥ=/ħ/ (x → the dot) · h̦=/ʕ/ (j → the comma) · '=/ʔ/ (see below) · h
    "l": "l", "r": "r", "rc": "r" + _DB,                          # r trill · ṛ=/ɾ/ tap (`c` → the dot, the general rule)
}
_VOW = {
    "i": "i", "e": "e", "a": "a", "o": "o", "u": "u",
    "ic": "ü", "ec": "ö", "uc": "ï", "oc": "ë",        # diaeresis = flip front↔back: ü ö (u/o → front y/ø) · ï ë (i/e → back ɯ/ɤ)
    "ij": "ị", "ej": "ẹ", "uj": "ụ", "oj": "ọ",     # j = lower one step = dot below (front & back uniform)
    "iq": "ụ̈", "eq": "ọ̈",                            # ụ̈ ọ̈ (q = c+j: below-dot + diaeresis)
    "ac": "ä", "ax": "ạ",                                        # ä = a flipped to the back = ɑ · ạ = schwa (a + the x-dot: the glyph spells the label)
}


# Every point's glyph, NFC — the input to the glyph-level doubling guard below.
_POINT_GLYPHS = frozenset(unicodedata.normalize("NFC", v) for v in {**_CONS, **_VOW}.values())


def _doubles_glyph(g):
    """True when this glyph plus ONE j-mark would already spell a point's glyph, so the mark must
    double to stay distinct. The glyph-level cousin of `notation.doubles` (which guards labels)."""
    one = _VLA if _below_taken(g) else _VLB
    return unicodedata.normalize("NFC", g + one) in _POINT_GLYPHS


def _apply(base, label, mods, is_vowel, data_dir="data"):
    g = base
    for m in sorted(mods, key=lambda m: (m == "long", m)):   # long LAST: it doubles the finished glyph
        if m == "long":
            if is_vowel:
                # FLIP + long = the DOUBLE ACUTE — one mark, never dots+acute stacked:
                #   ü→ű ö→ő · ï→i̋ ë→e̋ ä→a̋ · ụ̈→ụ̋ ọ̈→ọ̋ ; every other vowel just takes the acute
                nfd = unicodedata.normalize("NFD", g)
                g = nfd.replace(_DDA, _DACUTE) if (_DDA in nfd and nfd[0] in "aeiou") \
                    else g + _ACUTE
            else:
                g = g + g          # geminate: double the WHOLE glyph (ș→șș — g[0] would drop the mark;
                                   #   first-letter doubling is an orthography rule, decode.py only)
        elif m == "nasal":
            g = g + _TILDE
        elif m == "aspirated":
            g = g + (_DDA if _below_taken(g) else _DDB)    # two dots: t̤ k̤ c̤ · p̈ above · c̦̈ above
        elif m == "pharyngealized":
            g = g + _TILDE_B                               # tilde below (emphatics t̰ d̰ s̰ z̰)
        elif m == "palatalized":
            # One j = one mark (ț d̦ n̦ l̦ p̓ k̦ b̦ …), doubled only where the SINGLE mark would
            # already spell a point: ș z̦ (the hush pair), c̦ x̦ (their affricates), h̦ (/ħ/).
            # This is a GLYPH constraint and is deliberately separate from the label rule — see
            # notation.doubles. Hence `tcj` (a 3-char label, nothing collides) still draws c͈.
            dbl = _doubles_glyph(g)
            if _below_taken(g):
                g = g + (_DVLA if dbl else _VLA)
            else:
                g = g + (_DVLB if dbl else _VLB)
        elif m == "retroflex":
            # the "\" tail: replaces the j-comma rather than stacking on it; else rides below (t̖ n̖ l̖ r̖)
            g = g.replace(_VLB, _GRB) if _VLB in g else g + _GRB
        elif m == "rhotic":
            g = "r" + _DDA              # the r-coloured vowel = the vocalic r̈ (r trill · r̦ tap · r̈ vocalic)
        elif m == "nonsyllabic":
            # glides: readable letters, each inheriting its vowel's flip mark (ɥ = rounded j, ɰ = unrounded w)
            g = {"i": "j", "u": "w", "ü": "j" + _DDA, "ï": "w" + _DDA}.get(g, g + "̯")
    return unicodedata.normalize("NFC", g)   # precompose where possible (a+́ → á)


def uni_labels(all_ph, features, data_dir="data"):
    """{notation_label: uni glyph} — point base glyph + modifier diacritics."""
    label_of_base, mod_map = _label_maps(all_ph, features, data_dir)
    base_of = {**_CONS, **_VOW}
    out = {lab: unicodedata.normalize("NFC", g) for lab, g in base_of.items()}  # bare points first — always win
    seen_mods = set()                       # (point label, modifiers) actually attested
    for phs in all_ph.values():
        for ph in phs:
            pl = label_of_base.get(ph["base"])
            if pl is None or pl not in base_of:
                continue
            if ph["mods"]:
                seen_mods.add((pl, frozenset(ph["mods"])))
            full = full_label(pl, ph["mods"], mod_map, data_dir)
            # bare points were seeded above and always win (setdefault)
            out.setdefault(full, _apply(base_of[pl], pl, ph["mods"], pl in _VOW, data_dir))
    # Systematic long forms, so an unattested length still composes its diacritic instead of leaking
    # a literal `w`: for every point (`ojw`=ʊː) and for every attested point+modifier (`tjw` = a long
    # soft t = țț). `w` is never a base, so no label collides.
    for pl, mods in [(p, frozenset()) for p in base_of] + sorted(seen_mods):
        full = full_label(pl, mods | {"long"}, mod_map, data_dir)
        out.setdefault(full, _apply(base_of[pl], pl, mods | {"long"}, pl in _VOW, data_dir))
    # Same for the four glides, so an unattested one (ucx=ẅ) still renders.
    for pl in ("i", "u", "ic", "uc"):
        full = pl + _mod_chars({"nonsyllabic"}, pl, mod_map, data_dir)
        out.setdefault(full, _apply(_VOW[pl], pl, {"nonsyllabic"}, True, data_dir))
    return out


# TONE SIGNS — the opt-in marked rendering of tone digits (`tones` on the uni target; off by
# default — the zh spelling target carries real Pinyin diacritics inherently). Signs 1-4 are the
# Pinyin four; 0/5 = neutral (digit consumed, no mark). Placement is one language-blind PRIORITY
# rule over the LAST vowel group of the syllable (the segment its digit closes): mark the first
# a-based token, else the first e-based, else the first o-based, else the LAST vowel token — which
# reproduces Pinyin placement exactly (ao/ia/iao→a; e/ei/ie/üe→e; ou/uo/ong→o; iu→u, ui→i).
# A vowelless segment or an unmapped digit keeps the plain digit. Licence note: the acute doubles
# as the long-vowel mark; opting in accepts that reading within the user's text.
TONE_SIGNS = {"1": "̄", "2": "́", "3": "̌", "4": "̀"}   # ◌̄ ◌́ ◌̌ ◌̀
TONE_NEUTRAL = {"0", "5"}


def _is_vowel_tok(t):
    return bool(t) and t[0] in "aeiou"


def _tone_sign(glyphs, toks, digit):
    """Apply the tone sign for `digit` by the priority rule above; fallbacks keep the digit."""
    if digit in TONE_NEUTRAL:
        return glyphs
    mark = TONE_SIGNS.get(digit)
    if mark is None:
        return glyphs + [digit]
    group = []                                              # indices of the LAST vowel group
    for i, t in enumerate(toks):
        if _is_vowel_tok(t):
            group = group + [i] if group and group[-1] == i - 1 else [i]
    if not group:
        return glyphs + [digit]
    pick = next((i for b in "aeo" for i in group if toks[i][0] == b), group[-1])
    glyphs[pick] = unicodedata.normalize("NFC", glyphs[pick] + mark)
    return glyphs


def to_uni(text, all_ph, features, data_dir="data", tones=False):
    """Uni keeps tone digits PLAIN (șan1) unless `tones` is on: superscripts are an IPA device,
    and the marked alternative is the tone SIGN on the vowel (șān) — never an upper-index char."""
    labs = uni_labels(all_ph, features, data_dir)

    def seg_out(seg, digit=None):
        toks, caps = tokenize_cased(seg, labs.keys())
        shout = seg.isupper()          # an ALL-CAPS segment uppercases whole glyphs (TW -> TT, not Tt)
        up = (lambda g: g.upper()) if shout else _cap
        glyphs, pending = [], False
        for t, c in zip(toks, caps):
            g = labs.get(t, t)
            if c or pending:                    # a caseless glyph (') passes the capital along
                g, pending = apply_cap(g, up)
            glyphs.append(g)
        if digit is not None:
            glyphs = _tone_sign(glyphs, toks, digit) if tones else glyphs + [digit]
        return "".join(glyphs)
    out = []
    for w in text.split():
        piece, seg = "", ""
        for ch in w:                    # a tone digit closes its segment anywhere in the word
            if ch in "012345":
                piece += seg_out(seg, digit=ch)
                seg = ""
            else:
                seg += ch
        out.append(piece + seg_out(seg))
    return " ".join(out)
