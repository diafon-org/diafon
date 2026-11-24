#!/usr/bin/env python3
"""Generate docs/alphabet-spec.json: the alphabet as one machine-readable
file (split.md, the alphabet's contract). It knows no keyboard: nothing in
it is a typed form.

  version    semver: major for a removed point, a changed glyph or a changed
             name; minor for an added point, language or stage
  script     the letters, the marks, the float rule's descenders, the tones
  points     every point by name (its canonical IPA value): letter, marks,
             glyphs, and the sounds it writes per language
  compositions  every letter with marks the script allows, with all its
             glyphs (small, capital, long, joined): the whole script as a
             table; `id` is the point's name, null for one no point names yet
  languages  each language's sounds -> the points that write them
  stages     each spelling: its tables by point name
  lexicons   the word lists, by reference (name, shape, size, sha256)
  vectors    points -> script, script -> points, a stage written and read,
             convert, detect, the lexicon: any implementation must reproduce
             them (tests/test_alphabet_spec.py does, for the reference)

A token in a vector is a point name ("ʃ", "ʃː"), or an object when it
carries more: {"p": name, "caps": true, "tones": "3"}, {"c": [letter,
mark, ...]} for an open composition (with "long" when long), {"raw": ","}.
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gen_points
import lexicon
import mapping
import script
import stages
from script import Tok

VERSION = '1.0.0-pre.1'         # 1.0.0 once the split is done and the names are frozen (split.md)
OUT = os.path.join(ROOT, 'docs', 'alphabet-spec.json')

CAPITALS = [('ig', 'NNE'), ('ig', 'NWANNE'), ('sw', 'MMOJA'), ('hu', 'SZÉP'),
            ('pl', 'DZIEŃ'), ('pl', 'SIĘ'), ('cs', 'CHLEBA'), ('fi', 'KUKKA'), ('hu', 'HOSSZÚ'), ('hu', 'KEDD'), ('hu', 'Kedd')]
SENTENCES = ['șok sép n̦ár', 'Șanˉ, șok!', 'ȘAN', 'G̦ P̦ G̤ T̤ Ü Șș C̤h Á', 'maˉ maˊ maˇ maˋ', 'hossú älmä',
             'c̦iˇ șïˇ c̦ïˉ', 'Diafon: j i w.', 'k̤ h̤ g̈ l̦ r̦ f̦ v̦ L̦ R̦', 't̤ d̤ n̤ s̤ z̤ c̤ x̤', 'c̣ x̣', 'r̈ r j w ẅ',
             'ạ ẹ ị ọ ụ aṃ eṃ', 't̤h d̤h ṛh pf th kh']
READ_ONLY = ['dd̦', 'kkk', 'tt', 't‍t', 'Șș', 'Ș‍ș', 'jj', 'x-ray: y', 'ma5 ma9', 'ǵ']    # read, not always written back the same
DETECT = ['Șok sép n̦ár, hossú älmä', 'sok szép nyár, hosszú alma', 'dobrý den, přátelé', 'hyvää yötä kaikille',
          'Dobra noc, kochani', 'günaydın', 'habari za asubuhi', 'ma1 ma2 ma3', 'K̤ Ẹ̀']
LEX_READ = {'en': ['the', 'quick', 'Shakespeare', 'meeting', 'facebook', 'nosuchword'],
            'zh': ['ni', 'hao3', 'Ni3hao3', 'nihao', 'you', 'lü4', 'zhong1', 'xi1', 'shi4', 'si1'],
            'la': ['hoc', 'vitae', 'quo'],
            'hu': ['jamaica', 'Bach', 'tea', 'Cudjoe', 'nosuchword']}
LEX_WRITE = {'en': ['ḍë', 'kwịk', 'rid', 'rẹd', 'Șejkspir', 'zzz'],
             'hu': ['fojók', 'gạjj', 'hẹjẹș', 'fọt', 'Hẹjẹs'],
             'zh': ['ni', 'ḳaw', 'c̤uṇ', 's̤ï']}
LEX_LOAN = {'hu': ['meeting', 'like', 'house', 'taxi', 'team', 'tagja', 'meetingen', 'Facebook', 'show', 'think', 'alma',
                   'hoc', 'sok', 'traumái', 'traumát', 'jamaicai', 'hazai', 'pizzát', 'Jamaicában', 'akinek', 'amiket',
                   'franchise', 'chat', 'technika', 'streamingajánlójában', 'meetingjén', 'Bela', 'felkerült', 'vele',
                   'teamek', 'teaház', 'onlinera', 'míting', 'Mítingen', 'lájk', 'lájkol', 'Bach', 'ocho']}
LEX_CHOICES = ['niˇ', 'ḳawˇ', 'c̤uṇˉ', 'kuoˊ', 's̤ïˋ', 'zzzˉ']
LEX_TEXTS = {'stage:hu': ['Sok szép nyár. Folyó, gally, hely; helyes.', 'Meeting, like, house, taxi, ad hoc, team, tagja, Facebook.',
                          'Jamaicai franchise-ba, akinek traumái; Bach, pech, technika, chat.',
                          'Streamingajánlójában online teaház, felkerült; tea, team.', 'Cudjoe East, Ocho Rios.',
                          'Míting és meeting; lájk, like, lájkol.'],
             'stage:en': ['The quick brown fox jumps over the lazy dog.', 'Shakespeare wrote Hamlet; Diafon reads it.'],
             'stage:zh': ['Ni3 hao3, shi4 jie4!', 'nihao ma']}


def plain(tok):
    """A token as the spec writes it."""
    if tok.raw is not None:
        return {'raw': tok.raw}
    name = tok.name
    if name and not tok.caps and not tok.tones:
        return name
    d = {'p': name} if name else {'c': [tok.comp[0], *tok.comp[1]]}
    if not name and tok.long:
        d['long'] = True
    if tok.caps:
        d['caps'] = True
    if tok.tones:
        d['tones'] = tok.tones
    return d


def token(x):
    """A token of the spec -> Tok."""
    if isinstance(x, str):
        return Tok(*script.point(x))
    if 'raw' in x:
        return Tok(raw=x['raw'])
    comp, long = script.point(x['p']) if 'p' in x else ((x['c'][0], tuple(x['c'][1:])), bool(x.get('long')))
    return Tok(comp, long, bool(x.get('caps')), x.get('tones', ''))


def plains(toks):
    return [plain(t) for t in toks]


def point_name(k):
    return script.NAME[k[0]] + (script.LONG if k[1] else '')


def build():
    S = script._S
    pts = gen_points.points()
    points = []
    for name, p in pts.items():
        e = {'id': name, 'letter': p['letter'], 'marks': p['marks'], 'long': p['long'],
             'glyph': p['glyph'], 'capital': p['capital'], 'readings': p['readings']}
        if p['long'] and p['letter'] not in script.VOWELS:
            e['joined'] = script.glyph(name, join=True)
        points.append(e)
    comps = []
    for c in script.compositions():
        e = {'letter': c[0], 'marks': list(c[1]), 'id': script.NAME.get(c),
             'glyph': script.compose(c), 'capital': script.compose(c, caps=True),
             'long': script.glyph(c, True), 'long_capital': script.glyph(c, True, caps=True)}
        if c[0] not in script.VOWELS:
            e['joined'] = script.glyph(c, True, join=True)
            e['joined_capital'] = script.glyph(c, True, caps=True, join=True)
        comps.append(e)

    languages = {}
    for code, d in mapping.load_languages().items():
        sounds = {}
        for seq, reads in mapping.language_points(code).items():
            for ipa, freq in reads:
                sounds[ipa] = {'points': [point_name(k) for k in seq], 'frequency': freq}
        languages[code] = {'name': d['name'], 'sounds': sounds}

    stage_data, stage_write, stage_read = {}, {}, {}
    for code in stages.codes():
        st = stages.load(code)
        errors = stages.validate(code)
        assert not errors, errors
        named = lambda table: {point_name(k): v for k, v in table.items()}
        stage_data[code] = {'name': st['name'], 'state': st['state'], 'letters': st['letters'], 'long': st['long'],
                            'points': named(st['spell']), 'caps': named(st['caps']), 'sample': st['sample'],
                            'read': dict(st['read']), 'before_i': named(st['before_i']), 'i_softens': st['i_softens'],
                            'before_vowel': named(st['before_vowel']),
                            # two letters of the script written as one of the language: {script text: spelling}
                            'pairs': {script.write([Tok(*k) for k in pair]): v for pair, v in st['pairs'].items()},
                            'lexical': st['lexical']}
        vec = []
        for k in st['spell']:
            for long in ((k[1],) if k[1] or script.vocalic(k[0]) else (False, True)):
                for caps in (False, True):
                    t = Tok(k[0], long, caps)
                    vec.append([plains([t]), stages.render([t], st)])
        vec += [[plains(script.read(s)), stages.render(s, st)] for s in SENTENCES + [st['sample']]]
        stage_write[code] = vec
        if not st['lexical']:
            texts = [stages.render(s, st) for s in SENTENCES + [st['sample']]] + list(st['read']) \
                + [sp.upper() for sp in list(st['points'].values())[:8]]
            stage_read[code] = [[t, plains(stages.parse(t, f'stage:{code}'))] for t in texts]

    write_vec = [[plains([Tok(*script.point(n), caps=caps)]), script.glyph(n, caps=caps)]
                 for n in pts for caps in (False, True)]
    write_vec += [[plains([Tok(c, caps=caps)]), script.compose(c, caps=caps)]
                  for c in script.compositions() if c not in script.NAME for caps in (False, True)]
    write_vec += [[plains(script.read(s)), s] for s in SENTENCES]
    joined_vec = [[plains([Tok(c, True, caps)]), script.glyph(c, True, caps, join=True)]
                  for c in script.compositions() if c[0] not in script.VOWELS for caps in (False, True)]
    read_vec = [[s, plains(script.read(s))] for s in SENTENCES + READ_ONLY]

    targets = ['script'] + [f'stage:{c}' for c in stages.codes()]
    convert_vec = []
    for code in stages.codes():
        st = stages.load(code)
        if st['lexical'] or not st['sample']:
            continue
        text = stages.render(st['sample'], st)
        convert_vec += [[text, f'stage:{code}', t, stages.convert(text, f'stage:{code}', t)] for t in targets]
    convert_vec += [[s, 'script', 'stage:hu', stages.convert(s, 'script', 'stage:hu')] for s in SENTENCES[:6]]
    # a word all in capitals: every point a capital, read and written back as it stood
    for code, word in CAPITALS:
        there = stages.convert(word, f'stage:{code}', 'script')
        assert stages.convert(there, 'script', f'stage:{code}') == word, (code, word, there)
        convert_vec += [[word, f'stage:{code}', 'script', there], [there, 'script', f'stage:{code}', word]]

    lexicons = {}
    for code in lexicon.codes():
        L = lexicon.lex(code)
        raw = open(os.path.join(lexicon.LEX, f'{code}.json'), 'rb').read()
        lexicons[code] = {k: L.get(k) for k in ('name', 'kind', 'match', 'loans', 'foreign', 'lengthen', 'sample')}
        lexicons[code]['output'] = L.get('output', True)
        lexicons[code]['sizes'] = {k: len(L[k]) for k in ('read', 'write', 'choices', 'native') if L.get(k)}
        lexicons[code]['file'] = f'data/lexicon/{code}.json'
        lexicons[code]['sha256'] = hashlib.sha256(raw).hexdigest()

    def written(c, s):
        hit = lexicon.write_word(script.read(s), c)
        return [hit[0], script.write(hit[1])] if isinstance(hit, tuple) else hit
    lex_vec = {
        'read': [[c, w, lexicon.read_word(w, c)] for c, ws in LEX_READ.items() for w in ws],
        'write': [[c, s, written(c, s)] for c, ss in LEX_WRITE.items() for s in ss],
        'loan': [[c, w, (lexicon.loan(w, c) or [None])[0]] for c, ws in LEX_LOAN.items() for w in ws],
        'choices': [[k, lexicon.choices(k)[:6]] for k in LEX_CHOICES],
        'parse': [[src, t, script.write(stages.parse(t, src))] for src, ts in LEX_TEXTS.items() for t in ts],
        'roundtrip': [[src, t, stages.convert(t, src, src)] for src, ts in LEX_TEXTS.items() for t in ts],
        'detect': [[t, stages.detect(t)[0][0]] for ts in LEX_TEXTS.values() for t in ts],
    }

    return {
        'name': 'Diafon alphabet',
        'version': VERSION,
        'script': {
            'letters': S['letters'], 'descenders': S['descenders'], 'marks': S['marks'],
            'tones': S['tones'], 'long': script.LONG, 'joiner': script.ZWJ,
            'rules': [
                'A point is a letter and its marks; its text is the composition, NFC.',
                'A consonant wears at most one of the anchor, the dot and the double dot below (twodots), below; above on a small letter that descends. No capital descends: a capital wears its mark below.',
                'No double dot on the thin stems l r f; only the dot on j w; the flip stands on w r m n, alone, and on the dotted r.',
                'A vowel wears the flip or the underdot, not both; long, the acute; the flip and the acute fuse into the double acute.',
                'A long consonant doubles its letter. A capital one capitalizes the first, and the second is the first one small; beside another capital, as in a word all in capitals, both are capitals (KUKKA). A joiner (U+200D) between the two marks the fused drawing and nothing else.',
                'Two equal consonant letters in a row are the long point. A nasal that is a syllable before its own letter wears the flip (m̈m, n̈n); a syllabic consonant anywhere else is unmarked.',
                'A tone is a sign after the syllable; the unmarked contour writes nothing. A digit after a point reads as a tone number.',
                'Reading: longest match, and a match never ends before a combining mark, so a letter takes its marks before a doubling.',
            ],
        },
        'points': points,
        'compositions': comps,
        'languages': languages,
        'stages': stage_data,
        'lexicons': lexicons,
        'vectors': {
            'write': write_vec,
            'joined': joined_vec,
            'read': read_vec,
            'stage_write': stage_write,
            'stage_read': stage_read,
            'convert': convert_vec,
            'detect': [[t, stages.detect(t)[0][0]] for t in DETECT],
            'lexicon': lex_vec,
        },
    }


def main():
    spec = build()
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    v = spec['vectors']
    print(f'{OUT}: version {spec["version"]}, {len(spec["points"])} points, {len(spec["compositions"])} compositions, '
          f'{len(spec["languages"])} languages, {len(spec["stages"])} stages, '
          f'{len(v["write"]) + len(v["joined"]) + len(v["read"])} script vectors')


if __name__ == '__main__':
    main()
