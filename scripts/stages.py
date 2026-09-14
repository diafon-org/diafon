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


def codes():
    return sorted(os.path.basename(p)[:-5]
                  for p in glob.glob(os.path.join(ROOT, 'data', 'stages', '*.yaml')))


def load(code):
    d = yaml.safe_load(open(os.path.join(ROOT, 'data', 'stages', f'{code}.yaml')))
    d['letters'] = d['letters'].split()
    d.setdefault('caps', {})
    d.setdefault('sample', '')
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
    print(render(' '.join(sys.argv[2:]), sys.argv[1]))
