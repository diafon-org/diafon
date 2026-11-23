#!/usr/bin/env python3
"""Generate web/lessons-data.js, the lessons of the Input page.

For every language of the alphabet, the typing one idea at a time, each
with that language's own sounds:

  letters   the letters typed as they are;
  op:y      the letters typed with y;
  op:q      the letters typed with q;
  two       the letters typed with two or three operator keys (yq, qy, qyq);
  seq       sounds written as two letters in a row (aspirates, nasal vowels,
            diphthongs).

Example words come from data/lessons.yaml's sources, read through the
language's spelling in the alphabet's reference; a word appears in the
first lesson by which every letter in it has been taught, and only if it
writes back to its own spelling. Needs the alphabet's scripts
(scripts/alphabet_ref.py) for the languages, the spellings and the word
lists.
"""
import json
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from engine import alphabet, profile
from engine.engine import make
import alphabet_ref           # noqa: E402  (puts the alphabet's scripts on the path)
import lexicon                # noqa: E402
import mapping                # noqa: E402
import script                 # noqa: E402
import stages                 # noqa: E402

PROFILE = 'diafon-v1'
LEX = os.path.join(alphabet_ref.PATH, 'data', 'lexicon')
OUT = os.path.join(ROOT, 'web', 'lessons-data.js')
TOP = 30000          # how deep into a frequency list examples may come from
N_SHOW, N_DRILL = 6, 8
RANK = {'L': 0, 'M': 1, 'S': 2, 'X': 3}

C = profile.compiled(PROFILE)
ENG = make(C)
KEY = {((v['to'][0], tuple(v['to'][1:])), v['long']): k for k, v in C['keys'].items()}
OPS = set(C['segment']['operators'])


def nfc(s):
    return ud.normalize('NFC', s)


def key_of(comp, long):
    """The keys that type one letter: its key, a long consonant with the base doubled."""
    if (comp, long) in KEY:
        return KEY[comp, long]
    k = KEY[comp, False]
    return k[0] * 2 + k[1:]


def typed(toks):
    """Script tokens -> the keys that type them, or None where a raw character would be read as a key."""
    out = ''
    for t in toks:
        if t.raw is not None:
            if t.raw.lower() in OPS or t.raw.isdigit():
                return None
            out += t.raw
            continue
        k = key_of(t.comp, t.long)
        out += (k[0].upper() + k[1:] if t.caps else k) + t.tones
    return out if ENG.render(out) == script.write(toks) else None


def kind(pts):
    if len(pts) > 1:
        return 'seq'
    k = key_of(*pts[0])
    ops = ''.join(ch for ch in k if ch in OPS)
    return 'letters' if not ops else 'op:' + ops if len(ops) == 1 else 'two'


def language_letters(code):
    """{points: {ipa: [...], freq}}: what the language writes, the marginal sounds left out."""
    out = {}
    for pts, reads in mapping.language_points(code).items():
        reads = [(i, f) for i, f in reads if f != 'X']
        if reads:
            out[pts] = {'ipa': [nfc(i) for i, _ in reads], 'freq': min((f for _, f in reads), key=RANK.get)}
    return out


def order(pts):
    comp = pts[0][0]
    return ('aeiou'.find(comp[0]) < 0, script.ORDER.index(comp[0]) if hasattr(script, 'ORDER') else comp[0], len(comp[1]), comp[1], pts[0][1], len(pts))


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
    """(spelling, script text, note) for each word the language's spelling reads and writes back."""
    st = stages.load(code)
    out, seen = [], set()
    for w in words:
        if w in avoid or w in seen:
            continue
        toks, how = stages.read_word(w, st)
        if how not in ('letters', 'lexicon'):
            continue
        t = script.write(toks)
        try:
            if nfc(stages.convert(t, 'script', 'stage:' + code)) != w:
                continue
        except Exception:
            continue
        seen.add(w)
        out.append((w, t, ''))
    return out


def zh_words():
    """Mandarin: its pinyin syllables with a tone, the commonest first, with the commonest character."""
    freq = {}
    path = os.path.join(LEX, 'sources', 'Unihan_DictionaryLikeData.txt')
    if not os.path.exists(path):
        return []
    for line in open(path, encoding='utf-8'):
        p = line.rstrip('\n').split('\t')
        if len(p) == 3 and p[1] == 'kFrequency':
            freq[chr(int(p[0][2:], 16))] = int(p[2])
    rows = []
    for t, chars in lexicon.lex('zh')['choices'].items():
        toks = script.read(t)
        if not chars or not toks or not toks[-1].tones:
            continue
        rows.append((freq.get(chars[0], 9), t, chars[0]))
    rows.sort()
    return [(stages.convert(t, 'script', 'stage:zh'), t, top) for _, t, top in rows]


def place_words(words, lesson_of, seqs, seq_at):
    """Each word into the first lesson that has taught all its letters; a word with a sequence
    (a diphthong, an aspirate, a nasal vowel) waits for the sequence lesson."""
    placed = {}
    for w, t, extra in words:
        toks = script.read(t)
        if not toks or any(tk.raw is not None for tk in toks):
            continue
        keys = typed(toks)
        if keys is None:
            continue
        pts = [(tk.comp, tk.long and tk.comp[0] in script.VOWELS) for tk in toks]      # a long consonant is its letter doubled
        if any(p not in lesson_of for p in pts):
            continue
        idx = max(lesson_of[p] for p in pts)
        if any(tuple(pts[i:i + len(s)]) == s for s in seqs for i in range(len(pts))):
            idx = max(idx, seq_at)
        new = sorted({key_of(*p) for p in pts if lesson_of[p] == idx})
        placed.setdefault(idx, []).append({'w': w, 't': keys, 'g': nfc(script.write(toks)), 'x': extra, 'new': new})
    return placed


def pick(words, n):
    """Up to n words, covering as many different new letters as possible first."""
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
    cfg = yaml.safe_load(open(os.path.join(ROOT, 'data', 'lessons.yaml'), encoding='utf-8'))
    langs = mapping.load_languages()
    review = mapping.load()[4] if len(mapping.load()) > 4 else {}
    out = {}
    for code, d in sorted(langs.items(), key=lambda kv: -kv[1]['speakers']['native']):
        letters = language_letters(code)
        groups = {}
        for pts in letters:
            groups.setdefault(kind(pts), []).append(pts)
        plan = [k for k in ('letters', 'op:y', 'op:q', 'two', 'seq') if k in groups]
        lessons = [(k, sorted(groups[k], key=lambda p: (p[0][0][0] not in 'aeiou', key_of(*p[0]), len(p)))) for k in plan]
        lesson_of = {}
        for i, (k, ps) in enumerate(lessons):
            for pts in ps:
                for p in (pts if k == 'seq' else pts[:1]):
                    lesson_of.setdefault(p, i)
        seq_at = next((i for i, (k, _) in enumerate(lessons) if k == 'seq'), -1)
        seqs = [pts for k, ps in lessons if k == 'seq' for pts in ps]
        src = (cfg.get('words') or {}).get(code)
        avoid = set((cfg.get('avoid') or {}).get(code) or [])
        words = []
        if code == 'zh':
            words = zh_words()
        elif src and os.path.exists(os.path.join(LEX, src)):
            words = stage_words(code, frequency_words(os.path.join(LEX, src)), avoid)
        placed = place_words(words, lesson_of, seqs, seq_at)
        les = []
        for i, (k, ps) in enumerate(lessons):
            ws = placed.get(i, [])
            forms = []
            for pts in ps:
                keys = ''.join(key_of(*p) for p in pts)
                marks = pts[0][0][1] if len(pts) == 1 else ()
                forms.append({'f': keys, 'g': nfc(script.write([script.Tok(c, l, False) for c, l in pts])),
                              'ipa': letters[pts]['ipa'], 'freq': letters[pts]['freq'],
                              'k': {'anchor': 'j', 'dot': 'x', 'twodots': 'y', 'flip': 'c', 'underdot': 'j'}.get(marks[0], 'base') if marks else 'base'})
            if k == 'seq':
                ws = [dict(w, new=[f['f'] for f in forms if f['f'] in w['t']]) for w in ws]
            shown = pick(ws, N_SHOW)
            rest = [w for w in ws if w not in shown]
            les.append({'key': k, 'forms': forms, 'words': shown, 'drill': (rest or shown)[:N_DRILL]})
        out[code] = {'name': d['name'], 'native': d['speakers']['native'],
                     'review': 'reviewed' if review.get(code) == 'reviewed' else 'not reviewed',
                     'tones': {str(k): v for k, v in (d.get('tones') or {}).items()},
                     'words': bool(words), 'lessons': les}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('// generated by scripts/gen_lessons.py; do not edit\n')
        fh.write('const DIAFON_LESSONS = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
    with_words = sorted(c for c, v in out.items() if v['words'])
    print(f'{os.path.relpath(OUT, ROOT)}: {len(out)} languages, example words for {" ".join(with_words)}, '
          f'{os.path.getsize(OUT) // 1024} KB')


if __name__ == '__main__':
    main()
