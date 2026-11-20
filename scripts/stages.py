#!/usr/bin/env python3
"""Spelling stages: Diafon text rendered in a language's current
orthography, from data/stages/<code>.yaml.

A stage is a rendering of the points: it only chooses how each point is
written out. Points the stage does not list fall back to the script, so a
foreign name in a Hungarian text still reads. Long consonants follow the
stage's `long` rule (first-letter: tt, ssz, ccs); vowel length is spelled
per point.

validate(code) checks a stage against the language's own table: every point
the language uses is spelled, every spelling is a letter of the stated
alphabet, and no two of the language's points share a spelling.

Reading back: table(stage) inverts a stage (its spellings, long points,
capitals, the `read` aliases for the spellings a language keeps for
etymology, like Hungarian ly, and the script glyphs as fallback);
parse(text, source) reads a text in any source (script, or stage:<code>)
into points (script.Tok); convert(text, source, target) re-renders it;
detect(text) ranks the sources by how much of the text each one reads.

Usage: stages.py <code> "script text"
       stages.py convert <source> <target> "text"
"""
import glob
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import lexicon
import mapping
import script
from script import Tok


class StageError(ValueError):
    pass


def codes():
    """Every language with a spelling: a letter stage (data/stages), a
    lexicon that is an output of its own (data/lexicon), or both."""
    stage = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'data', 'stages', '*.yaml'))}
    lexical = {c for c in lexicon.codes() if lexicon.lex(c).get('output', True)}
    return sorted(stage | lexical)


_LOADED = {}


def _keyed(d):
    """A table by point name -> the same by (composition, long)."""
    return {script.point(str(name)): v for name, v in (d or {}).items()}


def load(code):
    """A stage: the letter tables from its yaml, by point, and `lexicon`, the
    code's lexicon when there is one. A language with a lexicon and no
    letters (English, Mandarin) is a lexical stage: no points, letters fall
    to the script."""
    if code in _LOADED:
        return _LOADED[code]
    path = os.path.join(ROOT, 'data', 'stages', f'{code}.yaml')
    L = lexicon.lex(code)
    if os.path.exists(path):
        d = yaml.safe_load(open(path, encoding='utf-8'))
        d['letters'] = d['letters'].split()
    else:
        assert L is not None, f'{code}: neither a stage nor a lexicon'
        d = {'code': code, 'name': L['name'], 'state': 'lexical', 'letters': [], 'long': 'double',
             'points': {}, 'sample': L.get('sample', '')}
    d.setdefault('sample', '')
    d.setdefault('read', {})
    d['points'] = {str(k): v for k, v in (d.get('points') or {}).items()}
    d['spell'] = _keyed(d['points'])
    d['caps'] = _keyed(d.get('caps'))
    d['before_i'] = _keyed(d.get('before_i'))          # a soft consonant before i is written plain: Czech ti, Polish si
    d.setdefault('i_softens', False)                   # before another vowel it is written plain + i: Polish się, nie
    d['before_vowel'] = _keyed(d.get('before_vowel'))  # soft only before a vowel other than i, written plain + i: Polish bie
    d['lexical'] = not d['points']
    d['lexicon'] = L
    _LOADED[code] = d
    return d


def key(tok):
    return tok.comp, tok.long


def spell(stage, tok):
    """Spelling of one point (case kept), or None if the stage has none."""
    k = key(tok)
    sp, capsp = stage['spell'].get(k), stage['caps'].get(k)
    if sp is None and tok.long and not script.vocalic(tok.comp):
        short = stage['spell'].get((tok.comp, False))
        if short is not None:
            if stage.get('long') == 'first-letter':
                sp = short[0] + short
            else:
                sp = short + short
                if stage['caps'].get((tok.comp, False)):
                    capsp = stage['caps'][tok.comp, False] + short
    if sp is None:
        return None
    if not tok.caps:
        return sp
    return capsp or ud.normalize('NFC', sp[0].upper() + sp[1:])


I = ('i', ())


def soft_spelling(stage, tok, nxt):
    """The spelling of a soft consonant before a vowel (before_i, i_softens),
    or None: Polish ś + i is si, ś + e is sie; Czech ť + i is ti."""
    if nxt is None or nxt.raw is not None or not script.vocalic(nxt.comp):
        return None
    k = key(tok)
    plain = stage['before_i'].get(k)
    if plain is not None and nxt.comp == I:
        sp = plain
    elif plain is not None and stage['i_softens']:
        sp = plain + 'i'
    elif k in stage['before_vowel'] and nxt.comp != I:
        sp = stage['before_vowel'][k] + 'i'
    else:
        return None
    return sp[0].upper() + sp[1:] if tok.caps else sp


def tokens(text):
    return script.read(text) if isinstance(text, str) else text


def render_letters(text, stage, strict=False):
    """Points (or script text) in the stage's letters, a point the stage does
    not spell in the script; the tone as its number."""
    toks = tokens(text)
    out = []
    for k, t in enumerate(toks):
        if t.raw is not None:
            out.append(t.raw)
            continue
        sp = soft_spelling(stage, t, toks[k + 1] if k + 1 < len(toks) else None) or spell(stage, t)
        if sp is None:
            if strict:
                raise StageError(f'{script.write([t])}: not spelled in the {stage["code"]} stage')
            sp = script.glyph(t.comp, t.long, t.caps)
        out.append(sp + t.tones)
    return ''.join(out)


def words(toks):
    """A run of points split into words and what lies between: [(is word,
    tokens)]. A word is points and plain letters; a tone ends it."""
    out, cur = [], []
    letter = lambda t: t.raw is None or (t.raw.isascii() and t.raw.isalpha())

    def flush():
        if cur:
            out.append((True, list(cur)))
            cur.clear()
    for t in toks:
        if letter(t):
            cur.append(t)
            if t.raw is None and t.tones:
                flush()
        else:
            flush()
            if out and not out[-1][0]:
                out[-1][1].append(t)
            else:
                out.append((False, [t]))
    flush()
    return out


def render(text, code, strict=False):
    """Points (or script text) in the stage's spelling: the lexicon first,
    word by word (a whole word, or a stem by prefix), then the letters."""
    stage = load(code) if isinstance(code, str) else code
    toks = tokens(text)
    if not stage.get('lexicon'):
        return render_letters(toks, stage, strict)
    out = []
    for is_word, w in words(toks):
        if not is_word:
            out.append(render_letters(w, stage, strict))
            continue
        hit = lexicon.write_word(w, stage['code'])
        if hit is None:
            sp = render_letters(w, stage, strict)
            out.append(lexicon.write_loan(w, stage['code'], sp) or sp)
        elif isinstance(hit, tuple):
            out.append(hit[0] + render_letters(hit[1], stage, strict))
        else:
            out.append(hit)
    return ''.join(out)


_TABLES = {}


def _entry(text, caps=False):
    """Script text as a table entry: its points, the first one capitalized or not."""
    toks = script.read(text)
    assert toks and all(t.point for t in toks), f'{text!r}: not script'
    return tuple((t.comp, t.long, caps if k == 0 else t.caps) for k, t in enumerate(toks))


def table(stage, fallback=True, aliases=True):
    """The stage read back: {spelling: points}, longest match deciding. Every
    spelled point, its long partner, the capitalized and the all-caps
    spelling, the `read` aliases (unless aliases is off); over the script
    glyphs, for the points the stage does not spell (a foreign name in the
    text), unless fallback is off (the detector scores a stage by its own
    spellings alone). An entry is a tuple of (composition, long, caps)."""
    k = (stage['code'], fallback, aliases)
    if k in _TABLES:
        return _TABLES[k]
    t = {g: (v,) for g, v in script.table().items()} if fallback else {}
    entries = []
    for comp, long in stage['spell']:
        entries.append((comp, long))
        if not long and not script.vocalic(comp):
            entries.append((comp, True))
    for comp, long in entries:
        sp = spell(stage, Tok(comp, long))
        cap = spell(stage, Tok(comp, long, caps=True))
        if sp:
            t[sp] = ((comp, long, False),)
            if cap:
                t[cap] = ((comp, long, True),)
            up = sp.upper()
            if up not in (sp, cap):
                t[up] = ((comp, long, True),)
    for sp, toks in (dict(soft_reads(stage), **{s: _entry(v) for s, v in stage['read'].items()}).items()
                     if aliases else ()):
        up = (toks[0][:2] + (True,),) + toks[1:]
        t[sp] = toks
        t[sp[0].upper() + sp[1:]] = up
        t[sp.upper()] = up
    _TABLES[k] = t
    return t


def soft_reads(stage):
    """The spellings before_i, i_softens and before_vowel imply, read back:
    Polish si -> ś i, sie -> ś e, się -> ś ę, bie -> b̦ e; Czech ti -> ť i, tí -> ť í."""
    out = {}
    e = lambda k: (k[0], k[1], False)
    i_keys = [(I, False), (I, True)]
    vowels = [(k, sp) for k, sp in stage['spell'].items() if script.vocalic(k[0]) and k[0] != I]
    for soft, plain in stage['before_i'].items():
        for v in i_keys:
            if stage['spell'].get(v):
                out[plain + stage['spell'][v]] = (e(soft), e(v))
        if stage['i_softens']:
            for v, sp in vowels:
                out[plain + 'i' + sp] = (e(soft), e(v))
    for soft, plain in stage['before_vowel'].items():
        for v, sp in vowels:
            out[plain + 'i' + sp] = (e(soft), e(v))
    return out


def read_letters(text, table):
    """A text read through a table -> points, longest match first (a letter
    takes its marks with it), the tones after a spelling on its last point;
    anything the table does not cover is raw."""
    text = ud.normalize('NFC', text)
    maxlen = max((len(k) for k in table), default=1)
    out, i, n = [], 0, len(text)
    while i < n:
        s = script.match(text, i, table, maxlen)
        if s is None:
            out.append(Tok(raw=text[i]))
            i += 1
            continue
        tones, j = script.read_tones(text, i + len(s))
        entry = table[s]
        for k, (comp, long, caps) in enumerate(entry):
            out.append(Tok(comp, long, caps, tones if k == len(entry) - 1 else '', src=s if k == 0 else ''))
        i = j
    return out


def _own(word, stage):
    """The word read by the stage's own spellings alone (no aliases, no
    script): its points, or None if any letter is left over."""
    toks = read_letters(word, table(stage, fallback=False, aliases=False))
    if any(t.raw is not None and not t.raw.isdigit() for t in toks):
        return None
    return toks


def read_word(word, stage):
    """One word of a stage's text -> (points, how): for a host with
    letters, a loan ('loan:<code>'), else its own entries (a stem it reads its
    own way, 'lexicon'), else the letters when they read it in full
    ('letters'); for a lexical stage, a loan, else its lexicon
    ('lexicon'), else a loan lexicon, folded ('loan:<code>'), else the
    letters with aliases and the script as fallback ('fallback')."""
    L = stage.get('lexicon')
    if not stage['lexical']:
        if L:                                      # a host with a lexicon: the loan check (which yields to a
            hit = lexicon.loan(word, stage['code'])  # spoken stem at least as long), then its own entries
            if hit is not None:
                return script.read(hit[0]), f'loan:{hit[1]}'
            hit = lexicon.read_stem(word, stage['code'])
            if hit is not None:
                return script.read(hit[0]) + read_letters(hit[1], table(stage)), 'lexicon'
        if _own(word, stage) is not None:            # the stage's own letters cover it: read them with its
            return read_letters(word, table(stage, fallback=False)), 'letters'   # read spellings (rz, si, ti)
    if L:
        hit = lexicon.loan(word, stage['code'])
        if hit is not None:
            return script.read(hit[0]), f'loan:{hit[1]}'
        t = lexicon.read_word(word, stage['code'])
        if t is not None:
            return script.read(t), 'lexicon'
    return read_letters(word, table(stage)), 'fallback'


def parse(text, source):
    """A text in `source` (script | stage:<code>) read into points, everything
    else raw. A stage reads word by word (read_word); the script letter by
    letter."""
    if source == 'script':
        return script.read(text)
    if not source.startswith('stage:'):
        raise ValueError(f'no such source: {source}')
    stage = load(source[6:])
    text = ud.normalize('NFC', text)
    out, i = [], 0
    for m in lexicon.WORD.finditer(text):
        out += read_letters(text[i:m.start()], table(stage))
        out += read_word(m.group(0), stage)[0]
        i = m.end()
    out += read_letters(text[i:], table(stage))
    return out


def write(toks, target, join=False):
    """Points in a target (script | stage:<code>)."""
    if target == 'script':
        return script.write(toks, join)
    if target.startswith('stage:'):
        return render(toks, target[6:], strict=False)
    raise ValueError(f'no such target: {target}')


def convert(text, source, target):
    """A text from one source rendered in another target (the same names).
    Back into the same spelling, a word that came in as a loan goes out as it
    came (like stays like), which its points alone could not tell (șó is
    só as much as show); everything else re-renders from the points."""
    if source == target and source.startswith('stage:'):
        stage = load(source[6:])
        text = ud.normalize('NFC', text)
        out, i = [], 0
        for m in lexicon.WORD.finditer(text):
            out.append(render(read_letters(text[i:m.start()], table(stage)), stage))
            t, how = read_word(m.group(0), stage)
            out.append(m.group(0) if how.startswith('loan:') else render(t, stage))
            i = m.end()
        out.append(render(read_letters(text[i:], table(stage)), stage))
        return ''.join(out)
    return write(parse(text, source), target)


def sources():
    return ['script'] + [f'stage:{c}' for c in codes()]


def detect(text, prefer=None, other=()):
    """Which source a text is in: [(source, coverage)] best first, coverage
    the share of the text's letters (and marks) that the source reads as
    points. Ties: the script when the text carries any of its marks, then
    the preferred sources in their order (the mode in use, the person's
    languages), then the stages as listed. `other` adds sources of the
    caller's own, ranked ahead of the script: (name, coverage, wins ties)."""
    prefer = [prefer] if isinstance(prefer, str) else list(prefer or [])
    letters = lambda s: sum(1 for ch in s if ud.category(ch)[0] in 'LM')
    total = letters(ud.normalize('NFC', text)) or 1
    marks = {v[k] for v in script.MARKS.values() for k in ('below', 'above') if v.get(k)}
    has_marks = any(m in ud.normalize('NFD', text) for m in marks) and \
        any(m in ud.normalize('NFC', text) for m in marks)
    scored = [(name, cov) for name, cov, _ in other]
    first = {name for name, _, wins in other if wins} | ({'script'} if has_marks else set())
    front = [name for name, _, _ in other]
    lexical_full = {}
    for src in sources():
        if src == 'script':
            covered = sum(letters(t.src) for t in script.read(text) if t.point)
        else:
            stage = load(src[6:])
            covered, hows = 0, []
            for m in lexicon.WORD.finditer(ud.normalize('NFC', text)):
                t, how = read_word(m.group(0), stage)
                hows.append((how, m.group(0)))
                if how in ('letters', 'lexicon') or how.startswith('loan:'):
                    covered += letters(m.group(0))
            # the lexicon read every word: a syllable lexicon with a tone digit
            # somewhere is the strongest sign, a word lexicon the next
            if hows and all(h == 'lexicon' for h, _ in hows) and any(len(w) >= 3 for _, w in hows):
                if stage['lexicon']['kind'] == 'syllable':
                    if any(w[-1].isdigit() for _, w in hows):
                        lexical_full[src] = 0
                elif len(hows) >= 2:
                    lexical_full[src] = 1
        scored.append((src, covered / total))
    order = front + sources()
    rank = {s: i for i, s in enumerate(order)}

    def sort_key(item):
        src, cov = item
        tie = (0 if src in first
               else lexical_full[src] if src in lexical_full
               else 2 + prefer.index(src) if src in prefer
               else 2 + len(prefer) + (0 if src in front else 1))
        return (-round(cov, 6), tie, rank[src])
    return sorted(scored, key=sort_key)


def source_for(text, target, prefer=None, other=()):
    """The source to convert a text from: the best-read source that is not
    the target itself (a conversion into the source is no conversion), the
    target only when nothing else reads the text as well."""
    ranked = detect(text, prefer, other)
    best = ranked[0][1]
    for src, cov in ranked:
        if src != target and round(cov, 6) == round(best, 6):
            return src
    return ranked[0][0]


def name(k):
    return script.NAME.get(k[0], script.compose(k[0])) + (script.LONG if k[1] else '')


def validate(code):
    stage = load(code)
    if stage['lexical']:
        return []                       # no letters to check; the lexicon generator checks its entries
    letters = set(stage['letters'])
    errors = []
    pts = mapping.language_points(code)
    single = {seq[0]: reads for seq, reads in pts.items() if len(seq) == 1}
    for seq, reads in pts.items():
        for k in seq:
            if stage['spell'].get(k) is None and k not in stage['before_vowel'] \
                    and (len(seq) == 1 or spell(stage, Tok(*k)) is None):   # pl b̦: only bie, bia…
                errors.append(f'{code}: {name(k)} ({", ".join(i for i, _ in reads)}) not spelled')
    for k, sp in stage['spell'].items():
        if sp not in letters:
            errors.append(f'{code}: {name(k)} spelled {sp!r}, not a letter of the stage')
    seen = {}
    for k in single:
        sp = stage['spell'].get(k)
        if sp is None:
            continue
        if sp in seen:
            errors.append(f'{code}: {name(k)} and {name(seen[sp])} both spelled {sp}')
        seen[sp] = k
    if stage.get('sample'):
        # the sample sentence must be spelled in full by the stage itself
        for t in script.read(stage['sample']):
            if t.point and spell(stage, t) is None:
                errors.append(f'{code}: the sample uses {script.write([t])}, which the stage does not spell')
    for k in list(single):
        if not k[1] and not script.vocalic(k[0]) and stage['spell'].get(k) is not None:
            lk = (k[0], True)
            long = spell(stage, Tok(*lk))
            if long in seen and seen[long] != lk and lk not in stage['spell']:   # spelled on purpose
                errors.append(f'{code}: long {name(lk)} spelled {long}, same as {name(seen[long])}')
    return errors


if __name__ == '__main__':
    if sys.argv[1] == 'convert':
        print(convert(' '.join(sys.argv[4:]), sys.argv[2], sys.argv[3]))
    else:
        print(render(' '.join(sys.argv[2:]), sys.argv[1]))
