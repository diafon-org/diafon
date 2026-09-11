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

Usage: stages.py <code> "input text"
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


MARKS = 'marks'     # the built-in universal stage: base letters plus combining marks


def codes():
    return sorted(os.path.basename(p)[:-5]
                  for p in glob.glob(os.path.join(ROOT, 'data', 'stages', '*.yaml'))) + [MARKS]


def _in_use_forms():
    """Every single-segment form in use, with its (small, capital) composition."""
    out = {}
    for form in sorted(gen_master.aggregate()):
        if form.endswith('w') and form[0] in engine.C_BASES:
            continue                     # length: derived from the short form
        try:
            if len(engine.tokenize(form)) != 1:
                continue                 # a sequence (th, aix): its segments are covered
            out[form] = engine.compositions(form)
        except engine.ParseError:
            continue
    return out


def marks_stage():
    """The composed spelling: every form written as its base letter plus
    combining marks, the shape the Diafon font draws. Derived from the
    engine, never a hand table, so it cannot drift from the script rules;
    the inverse of the web letters (normalise() maps it back). For surfaces
    that draw combining marks but never receive the font."""
    forms, caps = {}, {}
    for form, (small, cap) in _in_use_forms().items():
        forms[form] = small
        if cap != ud.normalize('NFC', small[0].upper() + small[1:]):
            caps[form] = cap             # the float rule reads the capital: g̓ -> G̦
    return {'code': MARKS, 'name': 'Composed marks (base letter + combining marks)',
            'state': 'reviewed', 'letters': [], 'long': 'double', 'forms': forms, 'caps': caps}


def load(code):
    if code == MARKS:
        return marks_stage()
    d = yaml.safe_load(open(os.path.join(ROOT, 'data', 'stages', f'{code}.yaml')))
    d['letters'] = d['letters'].split()
    d.setdefault('caps', {})
    return d


def normalise(text):
    """Composed spelling -> the canonical text (the web letters), lossless:
    both spellings are injective over the forms in use."""
    if not hasattr(normalise, '_map'):
        m = {}
        for form, (small, cap) in _in_use_forms().items():
            m[small] = engine.glyph(form)
            m[cap] = engine.glyph(form[0].upper() + form[1:])
        normalise._map = sorted(((k, v) for k, v in m.items() if k != v),
                                key=lambda kv: -len(kv[0]))
    text = ud.normalize('NFC', text)
    for comp, canon in normalise._map:
        text = text.replace(comp, canon)
    return text


def language_forms(code):
    """-> {form: [ipa, ...]} for one language, from the mapping (X included);
    for the marks stage, every form in use."""
    if code == MARKS:
        return {form: [] for form in _in_use_forms()}
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
    stage = load(code) if isinstance(code, str) else code
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


def validate(code):
    stage = load(code)
    if code == MARKS:
        errors = []
        for form in language_forms(code):
            cap = form[0].upper() + form[1:]
            longs = (form + 'w', cap + 'w') if form[0] in engine.C_BASES else ()
            for f in (form, cap) + longs:
                back = normalise(render(f, stage, strict=True))
                if back != engine.glyph(f):
                    errors.append(f'{MARKS}: {f} renders {render(f, stage)!r}, normalises to {back!r}')
        seen = {}
        for form, sp in stage['forms'].items():
            if sp in seen and not (form.endswith('w') or seen[sp].endswith('w')):
                errors.append(f'{MARKS}: {form} and {seen[sp]} both spelled {sp}')
            seen[sp] = form
        return errors
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
    for form in list(forms):
        if form[0] in engine.C_BASES and stage['forms'].get(form) is not None:
            long = spell(stage, form + 'w')
            if long in seen and seen[long] != form + 'w':
                errors.append(f'{code}: long {form}w spelled {long}, same as {seen[long]}')
    return errors


if __name__ == '__main__':
    print(render(' '.join(sys.argv[2:]), sys.argv[1]))
