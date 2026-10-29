#!/usr/bin/env python3
"""Generate docs/learn-data.js, the lessons of the Learning page (docs/learn.md).

For every language, the concepts one at a time, each with that language's
own sounds:

  1. the plain letters: the sounds written with a bare base;
  2. one lesson per operator, in the order of how many of the language's
     sounds use it (a form with two operators comes with the later one);
  3. length (w), the special, sequences (two sounds in a row), tones;
  4. capitals; then the card, every form of the language on one sheet.

Example words come from data/learn.yaml's sources, read through the
language's spelling stage; a word appears in the first lesson by which every
sound in it has been taught, and only if it reads back to its own spelling.
The forms and readings are the master tables' (gen_master.load_mapping).
"""
import glob
import json
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine
import gen_master
import stages

LEX = os.path.join(ROOT, 'data', 'lexicon')
OUT = os.path.join(ROOT, 'docs', 'learn-data.js')
OP_ORDER = 'jxcqy'
TOP = 30000          # how deep into a frequency list examples may come from
N_SHOW, N_DRILL = 6, 8


def nfc(s):
    return ud.normalize('NFC', s)


def kind(form):
    """base, op (an operator lesson), long, special, seq."""
    if form in gen_master.SEQ:
        return 'seq'
    if len(form) == 1:
        return 'base'
    if 'w' in form:
        return 'long'
    if form.endswith('xy') or form in gen_master.SPECIAL2 or (form[0] in 'aeiou' and 'y' in form):
        return 'special'
    return 'op'


def language_forms(code, d, mapping):
    """form -> {ipa: [...], freq}, the language's forms in use (X excluded)."""
    cons, vows, over = mapping[:3]
    forms = {}
    rank = {'L': 0, 'M': 1, 'S': 2, 'X': 3}
    for sec, table in (('consonants', cons), ('vowels', vows)):
        for ipa, freq in d[sec].items():
            key = gen_master.nfd(ipa)
            f = over.get(code, {}).get(key) or table.get(key)
            if not f or freq == 'X':
                continue
            e = forms.setdefault(f, {'ipa': [], 'freq': freq})
            e['ipa'].append(nfc(ipa))
            if rank[freq] < rank[e['freq']]:
                e['freq'] = freq
    return forms


def plan_lessons(forms):
    """[(key, [forms])] in teaching order."""
    ops = [f for f in forms if kind(f) == 'op']
    count = {o: sum(1 for f in ops if o in f[1:]) for o in OP_ORDER}
    order = sorted((o for o in OP_ORDER if count[o]), key=lambda o: (-count[o], OP_ORDER.index(o)))
    lessons = [('letters', sorted((f for f in forms if kind(f) == 'base'), key=gen_master._order_key))]
    taken = set()
    for i, o in enumerate(order):
        known = set(order[:i + 1])
        new = [f for f in ops if f not in taken and set(f[1:]) <= known]
        taken.update(new)
        lessons.append(('op:' + o, sorted(new, key=gen_master._order_key)))
    for k in ('long', 'special', 'seq'):
        fs = [f for f in forms if kind(f) == k]
        if fs:
            lessons.append((k, sorted(fs, key=gen_master._order_key)))
    return lessons


# ---- the words

def frequency_words(path):
    out = []
    for i, line in enumerate(open(path, encoding='utf-8')):
        if i >= TOP:
            break
        w = line.split()[0] if line.strip() else ''
        if 2 <= len(w) <= 10 and w.isalpha() and w == w.lower():
            out.append(nfc(w))
    return out


def stage_words(code, words, avoid):
    """(spelling, transport) for each word the stage reads and writes back."""
    st = stages.load(code)
    out, seen = [], set()
    for w in words:
        if w in avoid or w in seen:
            continue
        t, how = stages.read_word(w, st)
        if how not in ('letters', 'lexicon'):
            continue
        try:
            if nfc(stages.convert(t, 'transport', 'stage:' + code)) != w:
                continue
        except Exception:
            continue
        seen.add(w)
        out.append((w, t, ''))
    return out


def zh_words():
    """Mandarin: its pinyin syllables with a tone, the commonest first."""
    freq = {}
    for line in open(os.path.join(LEX, 'sources', 'Unihan_DictionaryLikeData.txt'), encoding='utf-8'):
        p = line.rstrip('\n').split('\t')
        if len(p) == 3 and p[1] == 'kFrequency':
            freq[chr(int(p[0][2:], 16))] = int(p[2])
    lex = json.load(open(os.path.join(LEX, 'zh.json')))
    rows = []
    for key, chars in lex['choices'].items():
        if not key[-1].isdigit() or not chars:
            continue
        top = chars[0]
        rows.append((freq.get(top, 9), key, top))
    rows.sort()
    out = []
    for _, key, top in rows:
        spelled = stages.convert(key, 'transport', 'stage:zh')
        out.append((spelled, key, top))
    return out


def place_words(words, lesson_of, forms):
    """Each word into the first lesson that has taught all its sounds."""
    placed = {}
    for w, t, extra in words:
        try:
            segs = engine.segments(t)
        except Exception:
            continue
        idx, new = -1, set()
        ok = True
        for s in segs:
            if s['kind'] != 'form':
                ok = False
                break
            f = s['form'].lower()
            if f not in lesson_of:
                ok = False
                break
            idx = max(idx, lesson_of[f])
        if not ok or idx < 0:
            continue
        new = {s['form'].lower() for s in segs if lesson_of.get(s['form'].lower()) == idx}
        placed.setdefault(idx, []).append({'w': w, 't': t, 'g': nfc(engine.render(t)), 'x': extra,
                                           'new': sorted(new)})
    return placed


def pick(words, n):
    """Up to n words, covering as many different new forms as possible first."""
    chosen, seen = [], set()
    for w in words:
        if len(chosen) >= n:
            break
        if not set(w['new']) <= seen:
            chosen.append(w)
            seen.update(w['new'])
    for w in words:
        if len(chosen) >= n:
            break
        if w not in chosen:
            chosen.append(w)
    return chosen


def main():
    cfg = yaml.safe_load(open(os.path.join(ROOT, 'data', 'learn.yaml')))
    mapping = gen_master.load_mapping()
    review = mapping[4]
    langs = gen_master.load_languages()
    out = {}
    for code, d in sorted(langs.items(), key=lambda kv: -kv[1]['speakers']['native']):
        forms = language_forms(code, d, mapping)
        lessons = plan_lessons(forms)
        lesson_of = {f: i for i, (_, fs) in enumerate(lessons) for f in fs}
        for i, (key, fs) in enumerate(lessons):
            if key == 'seq':        # a sequence is its parts in a row
                for f in fs:
                    for s in engine.segments(f):
                        lesson_of.setdefault(s['form'], i)
        src = (cfg.get('words') or {}).get(code)
        avoid = set((cfg.get('avoid') or {}).get(code) or [])
        words = []
        if code == 'zh':
            words = zh_words()
        elif src and os.path.exists(os.path.join(LEX, src)):
            words = stage_words(code, frequency_words(os.path.join(LEX, src)), avoid)
        placed = place_words(words, lesson_of, forms)
        les = []
        for i, (key, fs) in enumerate(lessons):
            ws = placed.get(i, [])
            if key == 'seq':        # its words were placed by their parts: gather them back
                every = [w for j in sorted(placed) if j <= i for w in placed[j]]
                ws = [dict(w, new=[f for f in fs if f in w['t']]) for w in every if any(f in w['t'] for f in fs)]
            shown = pick(ws, N_SHOW)
            rest = [w for w in ws if w not in shown]
            les.append({'key': key,
                        'forms': [{'f': f, 'g': nfc(engine.render(f)), 'ipa': forms[f]['ipa'],
                                   'freq': forms[f]['freq']} for f in fs],
                        'words': shown, 'drill': (rest or shown)[:N_DRILL]})
        label = gen_master.STATES.get(review.get(code), gen_master.STATES[None])[0]
        out[code] = {'name': d['name'], 'native': d['speakers']['native'], 'review': label,
                     'tones': {str(k): v for k, v in (d.get('tones') or {}).items()},
                     'stage': code in stages.codes() or code == 'en', 'words': bool(words),
                     'lessons': les}
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('// generated by scripts/gen_learn.py; do not edit\n')
        fh.write('const LEARN = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
    with_words = sorted(c for c, v in out.items() if v['words'])
    print(f'{os.path.relpath(OUT, ROOT)}: {len(out)} languages, example words for {" ".join(with_words)}, '
          f'{os.path.getsize(OUT) // 1024} KB')


if __name__ == '__main__':
    main()
