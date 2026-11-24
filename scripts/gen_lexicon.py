#!/usr/bin/env python3
"""Generate data/lexicon/<code>.json from the sources named in
data/lexicon/<code>.yaml (see data/lexicon/README.md).

  en  CMUdict -> read (word -> script text) and write (script text -> word, the
      commonest spelling of a homophone: no digits or apostrophes, shortest,
      then first in the dictionary)
  hu  Magyar Ispell stems that carry ly -> write entries by prefix
  zh  the pinyin syllables of Unihan -> read/write by rule, and choices:
      script text + tone -> characters, most frequent first
  la  the hand table, copied
  loans  the one loan dictionary: origin.yaml, Latin, English's common words

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
import script

LEX = os.path.join(ROOT, 'data', 'lexicon')


def check(text):
    """Every entry is script throughout."""
    assert script.is_script(text), f'{text!r}: not script'


def origin():
    """The hand entries of origin.yaml: spelling -> {lang, t, also, spell}, `t` filled from the
    origin language's lexicon where the entry leaves it out (meeting: English reads it)."""
    import lexicon
    out = {}
    for sp, e in (yaml.safe_load(open(os.path.join(LEX, 'origin.yaml'))) or {}).items():
        e = dict(e)
        if 't' not in e:
            LL = lexicon.lex(e['lang'])
            assert LL and sp.lower() in LL['read'], f'origin.yaml: {sp} needs a t ({e["lang"]} does not read it)'
            e['t'] = LL['read'][sp.lower()]
        check(e['t'])
        e['also'] = {h: [w] if isinstance(w, str) else list(w) for h, w in (e.get('also') or {}).items()}
        e['spell'] = dict(e.get('spell') or {})
        out[sp.lower()] = e
    return out


def hosts():
    """The lexicons that catch loans (`loans: true`)."""
    return [c for c in yaml_codes() if load_yaml(c).get('loans')]


# ---- loans: the one loan dictionary every host consults ----

LOAN_SOURCES = ['la', 'en']        # dictionary loans, in priority: a spelling two of them read is the first's


def gen_loans():
    """data/lexicon/loans.json: every word a host may hold as a loan, with the one Diafon form its
    language of origin gives it, the same in every host.
      hand   origin.yaml: spelling -> [script text, lang]; matched as a stem, ahead of a host's
             dictionary (jamaicai), like a host's own entries
      read   lang -> spelling -> script text: the dictionaries (Latin; English, its common words);
             a spelling is in one only, hand entries in none
      write  script text -> the origin spelling (a homophone: hand, then Latin, then the commonest English)
      hosts  code -> read (a host's own spelling of a loan, origin.yaml `also` and `spell`:
             spelling -> [script text, lang]) and write (script text -> how the host writes the
             loan: `spell`, the host's `borrowed`)"""
    import lexicon
    hand = origin()
    read, write_ = {}, {}
    for sp, e in hand.items():
        write_.setdefault(e['t'], sp)
    taken = set(hand)
    for lc in LOAN_SOURCES:
        LL = lexicon.lex(lc)
        words = [w for w in LL['read'] if not LL['common'] or w in LL['common']]
        entries = list(LL['write'].items())
        if lc == 'en':
            freq = {}
            for line in open(os.path.join(LEX, 'sources', 'en_50k.txt'), encoding='utf-8'):
                w, n = line.split()
                freq.setdefault(w, int(n))
            entries = sorted(((t, w) for t, w in entries if w in freq), key=lambda e: -freq[e[1]])
        read[lc] = {w: LL['read'][w] for w in words if w not in taken}
        taken |= set(read[lc])
        for t, w in entries:
            write_.setdefault(t, w)
    host = {}
    for code in hosts():
        cfg = load_yaml(code)
        r, w = {}, {}
        for sp, e in hand.items():
            for v in e['also'].get(code, []) + ([e['spell'][code]] if code in e['spell'] else []):
                r[v.lower()] = [e['t'], e['lang']]
            if code in e['spell']:
                w[e['t']] = e['spell'][code]
        for b in cfg.get('borrowed') or []:              # written back as the host writes them
            for lc in LOAN_SOURCES:
                t = lexicon.lex(lc)['read'].get(b.lower())
                if t:
                    w.setdefault(t, b)
                    break
        host[code] = {'read': r, 'write': w}
    return {'name': 'Loans', 'kind': 'loans', 'match': 'prefix', 'output': False,
            'hand': {sp: [e['t'], e['lang']] for sp, e in hand.items()},
            'read': read, 'write': write_, 'hosts': host}


def load_yaml(code):
    return yaml.safe_load(open(os.path.join(LEX, f'{code}.yaml')))


def out_path(code):
    return os.path.join(LEX, f'{code}.json')


def sample(cfg, read, kind):
    """The yaml's sample_text read through the lexicon -> script text."""
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
        out.append(t + script.tone_signs(digits))
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
    rules = cfg.get('assimilated') or {}

    def assimilated(p, nxt):
        r = rules.get(p)
        return r['as'] if r and nxt in r['before'] else None
    freq = {}
    if len(cfg['sources']) > 1:
        for line in open(os.path.join(LEX, cfg['sources'][1]), encoding='utf-8'):
            w, n = line.split()
            freq.setdefault(w, int(n))
    own = cfg.get('pron') or {}                 # en.yaml's own readings replace CMUdict's for these words
    lines = [f'{w} {ph}' for w, ph in own.items()]
    lines += open(os.path.join(LEX, cfg['sources'][0]), encoding='utf-8').read().splitlines()
    read, write_cands = {}, {}
    vowels = {'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW'}
    r_split = set()                             # words whose reading has an unstressed ER before a vowel
    for n, line in enumerate(lines):
        line = line.split('#')[0].strip()
        if not line:
            continue
        word, *phones = line.split()
        if n >= len(own) and re.sub(r'\(\d+\)$', '', word) in own:
            continue
        m = re.match(r'^(.*)\((\d+)\)$', word)
        variant = 0
        if m:
            word, variant = m.group(1), int(m.group(2))
        # an unstressed ER before a vowel is a schwa and an r that starts the next syllable:
        # around is ërawnd, not r̈awnd
        split = [i for i, p in enumerate(phones[:-1]) if p == 'ER0' and re.sub(r'\d', '', phones[i + 1]) in vowels]
        phones = [re.sub(r'\d', '', p) for p in phones]
        for i in reversed(split):
            phones[i:i + 1] = ['AH', 'R']
        try:
            t = ''.join(assimilated(p, phones[i + 1] if i + 1 < len(phones) else None) or arpa[p]
                        for i, p in enumerate(phones))
        except KeyError as e:
            continue
        check(t)                      # every entry must re-segment strictly
        prefer = (cfg.get('prefer') or {}).get(word, 0)
        if variant == prefer or (variant == 0 and word not in read) or \
                (word in r_split and not split and word not in (cfg.get('prefer') or {})):
            read[word] = t                      # the first reading, or the one en.yaml prefers, or one
            r_split.discard(word)               # without the split schwa (every: evrí, not evërí)
            if split and variant == 0:
                r_split.add(word)
        # the commonest spelling of a word: no digits or apostrophes, shortest, first
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
        if not word or not re.fullmatch(r'[a-záéíóöőúüű]+', word) or 'ly' not in word or len(word) < 4:   # a short stem (ly, oly) would prefix every j word: joga -> lyoga
            continue
        t = script.write(stages.parse(word, 'stage:hu'))            # ly -> j, lly -> jj
        if 'j' not in t:
            continue
        stems[t] = word
    spoken = {}                                    # the hand entries (spoken, names), in Hungarian spelling -> script text, by the letters alone
    for sp, said in list((cfg.get('spoken') or {}).items()) + list((cfg.get('names') or {}).items()):
        spoken[sp.lower()] = script.write(stages.read_letters(said, stages.table(hu)))
        stems.setdefault(spoken[sp.lower()], sp)
    for sp, e in origin().items():                 # the hand loans written back by stem (Jamaicában), as Hungarian writes them
        stems.setdefault(e['t'], e['spell'].get(cfg['code'], sp))
    native = set()
    if cfg.get('native'):
        for line in open(os.path.join(LEX, cfg['native']), encoding='utf-8'):
            word = line.split('/')[0].split('\t')[0].strip().lower()
            if re.fullmatch(r'[a-záéíóöőúüű]{2,}', word):
                native.add(word)
    native |= {w.lower() for w in cfg.get('own') or []}        # Hungarian forms the stems lack (add, the imperative)
    native -= {w.lower() for w in cfg.get('borrowed') or []}   # English words the dictionary lists as its own
    return {'name': cfg['name'], 'kind': cfg['kind'], 'match': cfg['match'],
            'loans': bool(cfg.get('loans')),
            'read': spoken, 'write': stems, 'native': sorted(native), 'foreign': cfg.get('foreign', ''),
            'lengthen': cfg.get('lengthen', {})}



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


def pinyin_to_script(syl, cfg):
    """bare pinyin syllable -> script text, by the tables, or None."""
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
        t = cfg['apical_vowel']
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
    scored = []                                     # (script text + tone, char, -freq, order)
    for ch in sorted(standard):                     # in order: the same file on every run
        readings = {}
        for r, f in pinlu.get(ch, {}).items():
            readings[r] = max(readings.get(r, 0), f)
        for r in mandarin.get(ch, []):
            readings.setdefault(r, 0)
        for r, f in readings.items():
            bare, tone = split_pinyin(r)
            if bare is None:
                continue
            t = pinyin_to_script(bare, cfg)
            if t is None:
                unknown.add(bare)
                continue
            check(t + script.tone_signs(tone))
            read.setdefault(bare, t)
            if t not in write or len(bare) > len(write[t]):    # uo is wo, not the interjection o
                write[t] = bare
            scored.append((t + script.tone_signs(tone), ch, -f, tghz.get(ch, 1e9), ord(ch)))
    for key, ch, *_ in sorted(scored, key=lambda s: (s[0], s[2], s[3], s[4])):
        lst = choices.setdefault(key, [])
        if ch not in lst:
            lst.append(ch)
    if unknown:
        print('  pinyin syllables without a rule:', ' '.join(sorted(unknown)))
    return {'name': cfg['name'], 'kind': cfg['kind'], 'match': cfg['match'], 'tones': cfg.get('tones', 'numbers'),
            'read': read, 'write': write, 'choices': choices}


def gen_la(cfg):
    read = cfg['read']
    for t in read.values():
        check(t)
    return {'name': cfg['name'], 'kind': cfg['kind'], 'match': cfg['match'],
            'read': read, 'write': {v: k for k, v in read.items()}}


GEN = {'en': gen_en, 'hu': gen_hu, 'zh': gen_zh, 'la': gen_la}


def yaml_codes():
    return sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(LEX, '*.yaml')) if not p.endswith('origin.yaml'))


def codes():
    """Every lexicon, the loan dictionary after its sources (it reads their fresh json)."""
    return yaml_codes() + ['loans']


if __name__ == '__main__':
    for code in sys.argv[1:] or codes():
        if code == 'loans':
            data = {'code': 'loans', **gen_loans()}
            json.dump(data, open(out_path('loans'), 'w'), ensure_ascii=False, separators=(',', ':'))
            print(f"{out_path('loans')}: hand {len(data['hand'])}, " + ', '.join(f'{k} {len(v)}' for k, v in data['read'].items())
                  + f", write {len(data['write'])} · {os.path.getsize(out_path('loans')) // 1024} KB")
            continue
        cfg = load_yaml(code)
        for s in cfg.get('sources', []):
            if not os.path.exists(os.path.join(LEX, s)):
                sys.exit(f'{code}: missing source {s} (see data/lexicon/README.md)')
        write(code, GEN[code](cfg))
