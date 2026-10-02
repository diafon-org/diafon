#!/usr/bin/env python3
"""Spelling stages: the point stream rendered in a language's current
orthography, from data/stages/<code>.yaml.

A stage is a rendering, never an input convention: the tokenizer is the
universal one, a stage only chooses how each segment is written out. Forms
the stage does not list fall back to the script form, so a foreign name in
a Hungarian text still reads. Long consonants follow the stage's `long`
rule (first-letter: tt, ssz, ccs); vowel length is spelled per form.

validate(code) checks a stage against the language's own table: every form
the language uses is spelled, every spelling is a letter of the stated
alphabet, and no two of the language's forms share a spelling.

Reading back: table(stage) inverts a stage (its spellings, long forms,
capitals, the `read` aliases for the spellings a language keeps for
etymology, like Hungarian ly, and the script glyphs as fallback);
parse(text, source) reads a text in any source (transport, script, or
stage:<code>) back into transport form; convert(text, source, target)
re-renders it; detect(text) ranks the sources by how much of the text
each one reads.

Usage: stages.py <code> "input text"
       stages.py convert <source> <target> "text"
"""
import glob
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine
import gen_master
import lexicon


def codes():
    """Every language with a spelling: a letter stage (data/stages), a
    lexicon that is an output of its own (data/lexicon), or both."""
    stage = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'data', 'stages', '*.yaml'))}
    lexical = {c for c in lexicon.codes() if lexicon.lex(c).get('output', True)}
    return sorted(stage | lexical)


_LOADED = {}


def load(code):
    """A stage: the letter tables from its yaml, and `lexicon`, the code's
    lexicon when there is one. A language with a lexicon and no letters
    (English, Mandarin) is a lexical stage: no forms, letters fall to the
    script."""
    if code in _LOADED:
        return _LOADED[code]
    path = os.path.join(ROOT, 'data', 'stages', f'{code}.yaml')
    L = lexicon.lex(code)
    if os.path.exists(path):
        d = yaml.safe_load(open(path))
        d['letters'] = d['letters'].split()
    else:
        assert L is not None, f'{code}: neither a stage nor a lexicon'
        d = {'code': code, 'name': L['name'], 'state': 'lexical', 'letters': [], 'long': 'double',
             'forms': {}, 'sample': L.get('sample', '')}
    d.setdefault('caps', {})
    d.setdefault('sample', '')
    d.setdefault('read', {})
    d['lexical'] = not d['forms']
    d['lexicon'] = L
    _LOADED[code] = d
    return d


def language_forms(code):
    """-> {form: [ipa, ...]} for one language, from the mapping (X included)."""
    cons, vows, over, _, _, _ = gen_master.load_mapping()
    d = gen_master.load_languages()[code]
    byform = {}
    for sec, table in (('consonants', cons), ('vowels', vows)):
        for ipa, freq in d[sec].items():
            key = gen_master.nfd(ipa)
            form = over.get(code, {}).get(key) or table.get(key)
            byform.setdefault(form, []).append((ud.normalize('NFC', ipa), freq))
    return byform


def spell(stage, form):
    """Spelling of one form (base case kept), or None if the stage has none."""
    caps = form[0].isupper()
    low = form[0].lower() + form[1:]
    capmap = stage.get('caps') or {}
    sp, capsp = stage['forms'].get(low), capmap.get(low)
    if sp is None and low.endswith('w') and low[0] in engine.C_BASES:
        short = stage['forms'].get(low[:-1])
        if short is not None:
            if stage.get('long') == 'first-letter':
                sp = short[0] + short
            else:
                sp = short + short
                if capmap.get(low[:-1]):
                    capsp = capmap[low[:-1]] + short
    if sp is None:
        return None
    if not caps:
        return sp
    return capsp or ud.normalize('NFC', sp[0].upper() + sp[1:])


def render(text, code, strict=False):
    """Transport text in the stage's spelling: the lexicon first, word by
    word (a whole word, or a stem by prefix), then the letters."""
    stage = load(code) if isinstance(code, str) else code
    if not stage.get('lexicon'):
        return render_letters(text, stage, strict)
    out, i = [], 0
    for m in lexicon.WORD_T.finditer(text):
        out.append(render_letters(text[i:m.start()], stage, strict))
        w = m.group(0)
        hit = lexicon.write_word(w, stage['code'])
        if hit is None:
            sp = render_letters(w, stage, strict)
            out.append(lexicon.write_loan(w, stage['code'], sp) or sp)
        elif isinstance(hit, tuple):
            out.append(hit[0] + render_letters(hit[1], stage, strict))
        else:
            out.append(hit)
        i = m.end()
    out.append(render_letters(text[i:], stage, strict))
    return ''.join(out)


def render_letters(text, stage, strict=False):
    out = []
    for seg in engine.segments(text, strict):
        if seg['kind'] != 'form':
            out.append(seg['src'])
            continue
        sp = spell(stage, seg['form'])
        if sp is None:
            if strict:
                raise engine.ParseError(f'{seg["form"]}: not spelled in the {stage["code"]} stage')
            try:
                sp = engine.glyph(seg['form'])
            except engine.ParseError:
                sp = seg['src']
        out.append(sp + seg['tones'])
    return ''.join(out)


_TABLES = {}


def table(stage, fallback=True, aliases=True):
    """The stage read back: {spelling: form}, longest match deciding. Every
    spelled form, its long form, the capitalized and the all-caps spelling,
    the `read` aliases (unless aliases is off); over the script glyphs, for
    the forms the stage does not spell (a foreign name in the text), unless
    fallback is off (the detector scores a stage by its own spellings alone)."""
    key = (stage['code'], fallback, aliases)
    if key in _TABLES:
        return _TABLES[key]
    t = dict(script_table()) if fallback else {}
    entries = []
    for form in stage['forms']:
        entries.append(form)
        if form[0] in engine.C_BASES:
            entries.append(form + 'w')
    for form in entries:
        sp = spell(stage, form)
        cap = spell(stage, form[0].upper() + form[1:])
        if sp:
            t[sp] = form
            if cap:
                t[cap] = form[0].upper() + form[1:]
            up = sp.upper()
            if up not in (sp, cap):
                t[up] = form[0].upper() + form[1:]
    for sp, form in (stage['read'].items() if aliases else ()):
        t[sp] = form
        t[sp[0].upper() + sp[1:]] = form[0].upper() + form[1:]
        t[sp.upper()] = form[0].upper() + form[1:]
    _TABLES[key] = t
    return t


_USED = None


def used_forms():
    """The forms the languages use (the master table), which decide the
    reading of a glyph two forms share."""
    global _USED
    if _USED is None:
        _USED = frozenset(gen_master.aggregate())
    return _USED


def script_table():
    return engine.script_table(used_forms())


def _source_table(source):
    if source == 'script':
        return script_table()
    if source.startswith('stage:'):
        return table(load(source[6:]))
    raise ValueError(f'no such source: {source}')


def read_letters(text, table):
    out = []
    for tok in engine.read(text, table):
        out.append(tok[0] == 'raw' and tok[1] or tok[1] + tok[2])
    return ''.join(out)


def _own(word, stage):
    """The word read by the stage's own spellings alone (no aliases, no
    script): its transport, or None if any letter is left over."""
    toks = engine.read(word, table(stage, fallback=False, aliases=False))
    if any(t[0] == 'raw' and not t[1].isdigit() for t in toks):
        return None
    return ''.join(t[1] if t[0] == 'raw' else t[1] + t[2] for t in toks)


def read_word(word, stage):
    """One word of a stage's text -> (transport, how): for a host with
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
                return hit[0], f'loan:{hit[1]}'
            hit = lexicon.read_stem(word, stage['code'])
            if hit is not None:
                return hit[0] + read_letters(hit[1], table(stage)), 'lexicon'
        t = _own(word, stage)
        if t is not None:
            return t, 'letters'
    if L:
        hit = lexicon.loan(word, stage['code'])
        if hit is not None:
            return hit[0], f'loan:{hit[1]}'
        t = lexicon.read_word(word, stage['code'])
        if t is not None:
            return t, 'lexicon'
    return read_letters(word, table(stage)), 'fallback'


def parse(text, source):
    """A text in `source` (transport | script | stage:<code>) read back as
    transport text: forms joined, tones kept, everything else as it was.
    A stage reads word by word (read_word); the script letter by letter.
    Transport re-segments exactly, so the round trip is stable."""
    if source == 'transport':
        return text
    if source == 'script':
        return read_letters(text, script_table())
    stage = load(source[6:])
    text = ud.normalize('NFC', text)
    out, i = [], 0
    for m in lexicon.WORD.finditer(text):
        out.append(read_letters(text[i:m.start()], table(stage)))
        out.append(read_word(m.group(0), stage)[0])
        i = m.end()
    out.append(read_letters(text[i:], table(stage)))
    return ''.join(out)


def convert(text, source, target):
    """A text from one source rendered in another target (the same names).
    Back into the same spelling, a word that came in as a loan goes out as it
    came (like stays like), which its transport alone could not tell (sjow is
    só as much as show); everything else re-renders from the transport."""
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
    t = parse(text, source)
    if target == 'transport':
        return t
    if target == 'script':
        return engine.render(t, strict=False)
    if target.startswith('stage:'):
        return render(t, target[6:], strict=False)
    raise ValueError(f'no such target: {target}')


def sources():
    return ['transport', 'script'] + [f'stage:{c}' for c in codes()]


def detect(text, prefer=None):
    """Which source a text is in: [(source, coverage)] best first, coverage
    the share of the text's letters (and marks) that the source reads as
    forms. Ties: the script when the text carries any of its marks, the
    input form when it reads the whole text and operators occur in it, then
    the preferred sources in their order (the mode in use, the person's
    languages), then transport, then the stages as listed."""
    prefer = [prefer] if isinstance(prefer, str) else list(prefer or [])
    letters = lambda s: sum(1 for ch in s if ud.category(ch)[0] in 'LM')
    total = letters(ud.normalize('NFC', text)) or 1
    marks = {v[k] for v in engine.MARKS.values() if isinstance(v, dict)
             for k in ('below', 'above') if v.get(k)}
    has_marks = any(m in ud.normalize('NFD', text) for m in marks) and \
        any(m in ud.normalize('NFC', text) for m in marks)
    scored = []
    lexical_full = {}
    typed = False       # the input form read in full, with operators in it: the system's own
    for src in sources():
        if src == 'transport':
            segs = engine.segments(text, strict=False)
            covered = sum(letters(s['src']) for s in segs if s['kind'] == 'form')
            typed = covered == total and any(s['kind'] == 'form' and len(s['form']) > 1 for s in segs)
        elif src == 'script':
            covered = sum(letters(tok[3]) for tok in engine.read(text, script_table()) if tok[0] == 'form')
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
    rank = {s: i for i, s in enumerate(sources())}
    def key(item):
        src, cov = item
        tie = (0 if (src == 'script' and has_marks) or (src == 'transport' and typed)
               else lexical_full[src] if src in lexical_full
               else 2 + prefer.index(src) if src in prefer
               else 2 + len(prefer) + (0 if src == 'transport' else 1))
        return (-round(cov, 6), tie, rank[src])
    return sorted(scored, key=key)


def source_for(text, target, prefer=None):
    """The source to convert a text from: the best-read source that is not
    the target itself (a conversion into the source is no conversion), the
    target only when nothing else reads the text as well."""
    ranked = detect(text, prefer)
    best = ranked[0][1]
    for src, cov in ranked:
        if src != target and round(cov, 6) == round(best, 6):
            return src
    return ranked[0][0]


def validate(code):
    stage = load(code)
    if stage['lexical']:
        return []                       # no letters to check; the lexicon generator checks its entries
    letters = set(stage['letters'])
    errors = []
    forms = language_forms(code)
    for form, reads in forms.items():
        if stage['forms'].get(form) is None:
            errors.append(f'{code}: {form} ({", ".join(i for i, _ in reads)}) not spelled')
    for form, sp in stage['forms'].items():
        if sp not in letters:
            errors.append(f'{code}: {form} spelled {sp!r}, not a letter of the stage')
    seen = {}
    for form in forms:
        sp = stage['forms'].get(form)
        if sp in seen:
            errors.append(f'{code}: {form} and {seen[sp]} both spelled {sp}')
        seen[sp] = form
    if stage.get('sample'):
        # the sample sentence must be spelled in full by the stage itself
        for seg in engine.segments(stage['sample']):
            if seg['kind'] == 'form' and spell(stage, seg['form']) is None:
                errors.append(f'{code}: the sample uses {seg["form"]}, which the stage does not spell')
    for form in list(forms):
        if form[0] in engine.C_BASES and stage['forms'].get(form) is not None:
            long = spell(stage, form + 'w')
            if long in seen and seen[long] != form + 'w':
                errors.append(f'{code}: long {form}w spelled {long}, same as {seen[long]}')
    return errors


if __name__ == '__main__':
    if sys.argv[1] == 'convert':
        print(convert(' '.join(sys.argv[4:]), sys.argv[2], sys.argv[3]))
    else:
        print(render(' '.join(sys.argv[2:]), sys.argv[1]))
