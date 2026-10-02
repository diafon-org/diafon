#!/usr/bin/env python3
"""Generate data/lexicon/<code>.json from the sources named in
data/lexicon/<code>.yaml (see data/lexicon/README.md).

  en  CMUdict -> read (word -> transport) and write (transport -> word, the
      commonest spelling of a homophone: no digits or apostrophes, shortest,
      then first in the dictionary)
  hu  Magyar Ispell stems that carry ly -> write entries by prefix
  zh  the pinyin syllables of Unihan -> read/write by rule, and choices:
      transport + tone -> characters, most frequent first
  la  the hand table, copied

Usage: gen_lexicon.py [code ...]   (all codes with a yaml by default)
"""
import glob
import json
import os
import re
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine

LEX = os.path.join(ROOT, 'data', 'lexicon')


def load_yaml(code):
    return yaml.safe_load(open(os.path.join(LEX, f'{code}.yaml')))


def out_path(code):
    return os.path.join(LEX, f'{code}.json')


def sample(cfg, read, kind):
    """The yaml's sample_text read through the lexicon -> transport."""
    import lexicon
    text = cfg.get('sample_text', '')
    out, i = [], 0
    for m in lexicon.WORD.finditer(text):
        out.append(text[i:m.start()])
        w, digits = m.group(0), ''
        while w and w[-1].isdigit():
            digits, w = w[-1] + digits, w[:-1]
        t = read.get(w.lower())
        assert t is not None, f'{cfg["code"]}: sample word {w!r} not in the lexicon'
        out.append(t + digits)
        i = m.end()
    out.append(text[i:])
    return ''.join(out)


def write(code, data):
    data = {'code': code, **data}
    cfg = load_yaml(code)
    if cfg.get('output') is False:
        data['output'] = False
    if cfg.get('sample_text'):
        data['sample'] = sample(cfg, data['read'], data['kind'])
    json.dump(data, open(out_path(code), 'w'), ensure_ascii=False, separators=(',', ':'))
    kb = os.path.getsize(out_path(code)) // 1024
    print(f'{out_path(code)}: ' + ', '.join(f'{k} {len(v)}' for k, v in data.items() if isinstance(v, dict)) + f' · {kb} KB')


# ---- en ----

def gen_en(cfg):
    arpa = cfg['arpabet']
    freq = {}
    if len(cfg['sources']) > 1:
        for line in open(os.path.join(LEX, cfg['sources'][1]), encoding='utf-8'):
            w, n = line.split()
            freq.setdefault(w, int(n))
    read, write_cands = {}, {}
    for n, line in enumerate(open(os.path.join(LEX, cfg['sources'][0]), encoding='utf-8')):
        line = line.split('#')[0].strip()
        if not line:
            continue
        word, *phones = line.split()
        m = re.match(r'^(.*)\((\d+)\)$', word)
        variant = 0
        if m:
            word, variant = m.group(1), int(m.group(2))
        try:
            t = ''.join(arpa[re.sub(r'\d', '', p)] for p in phones)
        except KeyError as e:
            continue
        engine.segments(t)                      # every entry must re-segment strictly
        if variant == 0:
            read[word] = t
        # the commonest spelling of a transport: no digits or apostrophes, shortest, first
        key = (bool(re.search(r"[\d']", word)), -freq.get(word, 0), len(word), n)
        if t not in write_cands or key < write_cands[t][0]:
            write_cands[t] = (key, word)
    # the words a host may borrow: the frequency list's, not CMUdict's names and rarities (Felker, traum)
    common = sorted(w for w in read if w in freq)
    return {'name': cfg['name'], 'kind': cfg['kind'], 'match': cfg['match'],
            'read': read, 'write': {t: w for t, (k, w) in write_cands.items()}, 'common': common}


# ---- hu ----

def gen_hu(cfg):
    import stages
    hu = stages.load('hu')
    stems = {}
    for line in open(os.path.join(LEX, cfg['sources'][0]), encoding='utf-8'):
        word = line.split('/')[0].split('\t')[0].strip()
        if not word or not re.fullmatch(r'[a-záéíóöőúüű]+', word) or 'ly' not in word:
            continue
        t = stages.parse(word, 'stage:hu')            # ly -> ix, lly -> ixw
        if 'ix' not in t:
            continue
        stems[t] = word
    # loans written back in their own spelling: the folded transport of each
    # common loan word (the English frequency list; every Latin entry) ->
    # the word, the commonest first where two fold alike
    import lexicon
    loanwrite = {}
    for lc in cfg.get('loans', []):
        LL = lexicon.lex(lc)
        entries = list(LL['write'].items())
        if lc == 'en':
            freq = {}
            for line in open(os.path.join(LEX, 'sources', 'en_50k.txt'), encoding='utf-8'):
                w, n = line.split()
                freq.setdefault(w, int(n))
            entries = sorted(((t, w) for t, w in entries if w in freq), key=lambda e: -freq[e[1]])
        for t, w in entries:
            loanwrite.setdefault(_fold_with(cfg.get('fold', {}), t), w)
    spoken = {}                                    # the hand entries (spoken, names), in Hungarian spelling -> transport, by the letters alone
    for sp, said in list((cfg.get('spoken') or {}).items()) + list((cfg.get('names') or {}).items()):
        spoken[sp.lower()] = stages.read_letters(said, stages.table(hu))
        stems.setdefault(spoken[sp.lower()], sp)
    native = set()
    if cfg.get('native'):
        for line in open(os.path.join(LEX, cfg['native']), encoding='utf-8'):
            word = line.split('/')[0].split('\t')[0].strip().lower()
            if re.fullmatch(r'[a-záéíóöőúüű]{2,}', word):
                native.add(word)
    return {'name': cfg['name'], 'kind': cfg['kind'], 'match': cfg['match'],
            'loans': cfg.get('loans', []), 'fold': cfg.get('fold', {}),
            'read': spoken, 'write': stems, 'loanwrite': loanwrite, 'native': sorted(native), 'foreign': cfg.get('foreign', ''),
            'lengthen': cfg.get('lengthen', {})}


def _fold_with(rules, t):
    """lexicon.fold with the yaml's rules (the json is being generated)."""
    import lexicon
    lexicon._CACHE['_gen'] = {'read': {}, 'write': {}, 'loans': [], 'fold': rules, 'choices': {}, 'match': 'word', 'native': set()}
    return lexicon.fold(t, '_gen')


# ---- zh ----

TONE_MARKS = {'̄': '1', '́': '2', '̌': '3', '̀': '4'}


def split_pinyin(syl):
    """toned pinyin -> (bare syllable with ü, tone digit or '')."""
    tone = ''
    out = ''
    for ch in ud.normalize('NFD', syl.lower()):
        if ch in TONE_MARKS:
            tone = TONE_MARKS[ch]
        elif ch == '̈':
            out += '̈'
        else:
            out += ch
    out = ud.normalize('NFC', out).replace('v', 'ü')
    m = re.match(r'^([a-zü]+?)([0-5])?$', out)
    if not m:
        return None, ''
    bare, d = m.group(1), m.group(2)
    if d and d in '1234':
        tone = d
    return bare, tone


def pinyin_to_transport(syl, cfg):
    """bare pinyin syllable -> transport, by the tables, or None."""
    ini_map, fin_map = cfg['initials'], cfg['finals']
    apical, palatal = set(cfg['apical']), set(cfg['palatal'])
    ini = ''
    for cand in sorted(ini_map, key=len, reverse=True):
        if syl.startswith(cand):
            ini, rest = cand, syl[len(cand):]
            break
    else:
        rest = syl
    if not ini:                                     # zero initial: undo y/w
        if rest.startswith('yu'):
            rest = 'ü' + rest[2:]
        elif rest.startswith('y'):
            rest = ('i' + rest[1:]) if not rest[1:].startswith('i') else rest[1:]
        elif rest.startswith('w'):
            rest = ('u' + rest[1:]) if not rest[1:].startswith('u') else rest[1:]
    if ini in palatal and rest.startswith('u'):
        rest = 'ü' + rest[1:]
    if rest not in fin_map:
        return None
    t = fin_map[rest]
    if ini in apical and rest == 'i':
        t = 'uc'
    return ini_map.get(ini, '') + t


def gen_zh(cfg):
    src = os.path.join(LEX, cfg['sources'][0])
    mandarin, pinlu, tghz = {}, {}, {}
    for line in open(src, encoding='utf-8'):
        if line.startswith('#') or not line.strip():
            continue
        cp, field, val = line.rstrip('\n').split('\t')
        ch = chr(int(cp[2:], 16))
        if field == 'kMandarin':
            mandarin[ch] = val.split()
        elif field == 'kHanyuPinlu':
            pinlu[ch] = {re.sub(r'\(\d+\)', '', v): int(re.search(r'\((\d+)\)', v).group(1)) for v in val.split()}
        elif field == 'kTGHZ2013':
            tghz[ch] = min(float(x) for v in val.split() for x in v.split(':')[0].split(','))
    standard = set(tghz) | set(pinlu)
    read, write, choices, unknown = {}, {}, {}, set()
    scored = []                                     # (transport+tone, char, -freq, order)
    for ch in standard:
        readings = {}
        for r, f in pinlu.get(ch, {}).items():
            readings[r] = max(readings.get(r, 0), f)
        for r in mandarin.get(ch, []):
            readings.setdefault(r, 0)
        for r, f in readings.items():
            bare, tone = split_pinyin(r)
            if bare is None:
                continue
            t = pinyin_to_transport(bare, cfg)
            if t is None:
                unknown.add(bare)
                continue
            engine.segments(t + tone)
            read.setdefault(bare, t)
            write.setdefault(t, bare)
            scored.append((t + tone, ch, -f, tghz.get(ch, 1e9), ord(ch)))
    for key, ch, *_ in sorted(scored, key=lambda s: (s[0], s[2], s[3], s[4])):
        lst = choices.setdefault(key, [])
        if ch not in lst:
            lst.append(ch)
    if unknown:
        print('  pinyin syllables without a rule:', ' '.join(sorted(unknown)))
    return {'name': cfg['name'], 'kind': cfg['kind'], 'match': cfg['match'],
            'read': read, 'write': write, 'choices': choices}


def gen_la(cfg):
    read = cfg['read']
    for t in read.values():
        engine.segments(t)
    return {'name': cfg['name'], 'kind': cfg['kind'], 'match': cfg['match'],
            'read': read, 'write': {v: k for k, v in read.items()}}


GEN = {'en': gen_en, 'hu': gen_hu, 'zh': gen_zh, 'la': gen_la}


def codes():
    return sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(LEX, '*.yaml')))


if __name__ == '__main__':
    for code in sys.argv[1:] or codes():
        cfg = load_yaml(code)
        for s in cfg.get('sources', []):
            if not os.path.exists(os.path.join(LEX, s)):
                sys.exit(f'{code}: missing source {s} (see data/lexicon/README.md)')
        write(code, GEN[code](cfg))
