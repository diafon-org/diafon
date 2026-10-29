#!/usr/bin/env python3
"""Generate docs/spec.json: the system as machine-readable data, with the
test vectors every implementation must reproduce.

One file for implementers of the input methods, the browser extension, the
fonts and the language stages: the alphabet and the grammar, the script
rules (data/script.yaml), every form in use with its glyph and readings, each
language's table and review state, the spelling stages, and the vectors:
strict renders, lenient renders (ill-formed input passes through), inputs
that must be rejected, streaming traces (the commit rule keystroke by
keystroke) and stage renders. tests/test_spec.py holds the Python engine and
the playground's JS engine to these vectors.
"""
import datetime as dt
import json
import os
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import engine
import gen_master
import lexicon
import stages

SENTENCES = [
    'sjok sewp njawr', 'Sjan1, sjok!', 'SJAN', 'Gj Pj Gy Ty Ic Sjw Tqyh Aw',
    'ma1 ma2 ma3 ma4', 'hoswuw aclmac', 'tqi3 sjuc3 tquc1', 'Diafon: ix i ux.',
    'ky gy lj rj fj vj Lj Rj', 'ty dy ny sjy zjy tqy dqy', 'tcx dcx',
    'aq r ix ux icx ucx', 'aj ej ij oj uj ay ey iy oy uy', 'tyh dyh rch pf th kh',
]
LENIENT = ['Sjan1, jok!', 'jok', '1ma', 'tqyx', 'tww', 'twx', 'ly ry fy txy', 'bq ax txx', 'qwerty',
           'Hello, world!', 'x-ray', 'sj+ok']
DETECT = ['sjok sewp njawr', 'Șok sép n̦ár, hossú älmä', 'sok szép nyár, hosszú alma', 'dobrý den, přátelé',
          'hyvää yötä kaikille', 'Dobra noc, kochani', 'günaydın', 'habari za asubuhi', 'ma1 ma2 ma3', 'K̖ Ẹ̀']
LEX_READ = {'en': ['the', 'quick', 'Shakespeare', 'meeting', 'facebook', 'nosuchword'],
            'zh': ['ni', 'hao3', 'Ni3hao3', 'nihao', 'you', 'lü4', 'zhong1', 'xi1', 'shi4', 'si1'],
            'la': ['hoc', 'vitae', 'quo'],
            'hu': ['jamaica', 'Bach', 'tea', 'Cudjoe', 'nosuchword']}
LEX_WRITE = {'en': ['dxaj', 'kuxijk', 'rid', 'rejd', 'Sjeixkspir', 'zzz'],
             'hu': ['foixowk', 'gacixw', 'hejixejsj', 'fojt', 'Hejixejs'],
             'zh': ['ni', 'kxaux', 'tqyunx', 'sjyuc']}
LEX_LOAN = {'hu': ['meeting', 'like', 'house', 'taxi', 'team', 'tagja', 'meetingen', 'Facebook', 'show', 'think', 'alma', 'hoc', 'sok',
                   'traumái', 'traumát', 'jamaicai', 'hazai', 'pizzát', 'Jamaicában', 'akinek', 'amiket', 'meetingen', 'franchise', 'chat', 'technika',
                   'streamingajánlójában', 'meetingjén', 'Bela', 'felkerült', 'vele', 'teamek', 'teaház', 'onlinera']}
LEX_CHOICES = ['ni3', 'kxaux3', 'tqyunx1', 'kuoc2', 'sjyuc4', 'zzz1']
LEX_TEXTS = {'stage:hu': ['Sok szép nyár. Folyó, gally, hely; helyes.', 'Meeting, like, house, taxi, ad hoc, team, tagja, Facebook.',
                          'Jamaicai franchise-ba, akinek traumái; Bach, pech, technika, chat.',
                          'Streamingajánlójában online teaház, felkerült; tea, team.', 'Cudjoe East, Ocho Rios.'],
             'stage:en': ['The quick brown fox jumps over the lazy dog.', 'Shakespeare wrote Hamlet; Diafon reads it.'],
             'stage:zh': ['Ni3 hao3, shi4 jie4!', 'nihao ma']}
INVALID = ['jok', '1', 'tqyx', 'tww', 'twx', 'ly', 'ry', 'fy', 'bq', 'ax', 'txx',
           'tcq', 'yx', 'wa', 'ejx', 'txyx', 'txy', 'sxy', 'lxy', 'tcy', 'dcy', 'kqy']


def trace(text):
    """Keystroke-by-keystroke streaming trace: [[buffer, committed, pending], ...]."""
    out, buf = [], ''
    for ch in text:
        buf += ch
        committed, pending = engine.stream(buf)
        out.append([buf, committed, pending])
        buf = pending
    return out


def git_sha():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return None


def main():
    script = yaml.safe_load(open(os.path.join(ROOT, 'data', 'script.yaml')))
    agg = gen_master.aggregate()
    cons, vows, over, merges, review, shares = gen_master.load_mapping()
    langs = gen_master.load_languages()

    forms = []
    for form in sorted(agg, key=gen_master._order_key):
        reads = {ipa: {'languages': sorted(e[2]), 'native': round(e[1], 1)}
                 for ipa, e in agg[form].items()}
        cap = form[0].upper() + form[1:]
        forms.append({
            'form': form, 'glyph': engine.render(form), 'capital': engine.render(cap),
            'type': gen_master.form_type(form),
            'segments': len(engine.tokenize(form)),
            'readings': reads,
            'primary': next((i for i, v in shares.get(form, {}).items() if v == 'primary'), None),
        })

    languages = {}
    for code, d in langs.items():
        byform = stages.language_forms(code)
        languages[code] = {
            'name': d['name'], 'native': d['speakers']['native'],
            'review': review.get(code, 'non-reviewed'),
            'geminates': bool(d.get('geminates')),
            'tones': d.get('tones'),
            'forms': {f: [{'ipa': i, 'freq': q} for i, q in v] for f, v in sorted(byform.items())},
        }

    stage_data, stage_vectors = {}, {}
    for code in stages.codes():
        errors = stages.validate(code)
        if errors:
            print('STAGE INVALID:', *errors, sep='\n  ')
            sys.exit(1)
        st = stages.load(code)
        stage_data[code] = {k: st[k] for k in ('name', 'state', 'letters', 'long', 'forms')}
        stage_data[code]['caps'] = st.get('caps') or {}
        stage_data[code]['sample'] = st.get('sample') or ''
        stage_data[code]['read'] = st.get('read') or {}
        stage_data[code]['lexical'] = st['lexical']
        stage_data[code]['lexicon'] = bool(st.get('lexicon'))
        vec = [[f, stages.render(f, st)] for f in sorted(stages.language_forms(code))]
        vec += [[f + 'w', stages.render(f + 'w', st)] for f in sorted(st['forms']) if f[0] in engine.C_BASES]
        vec += [[s, stages.render(s, st)] for s in SENTENCES]
        stage_vectors[code] = vec

    single = [f['form'] for f in forms if f['segments'] == 1]
    render_vec = []
    for f in single:
        render_vec.append([f, engine.render(f)])
        render_vec.append([f[0].upper() + f[1:], engine.render(f[0].upper() + f[1:])])
        render_vec.append([f.upper(), engine.render(f.upper())])
    render_vec += [[f['form'], f['glyph']] for f in forms if f['segments'] > 1]
    render_vec += [[s, engine.render(s)] for s in SENTENCES]
    for s in INVALID:
        try:
            engine.render(s)
        except engine.ParseError:
            continue
        sys.exit(f'{s!r} should be invalid but renders')

    # reading back: the script and each stage parsed to transport, and
    # conversions between sources; every implementation reproduces these
    parse_script = []
    for f in single:
        for form in (f, f[0].upper() + f[1:]):
            parse_script.append([engine.render(form), form])
    parse_script += [[engine.render(s), stages.parse(engine.render(s), 'script')] for s in SENTENCES]
    parse_stages = {}
    for code in stages.codes():
        st = stages.load(code)
        vec = [[stages.render(f, st), stages.parse(stages.render(f, st), f'stage:{code}')]
               for f in sorted(st['forms'])]
        vec += [[stages.render(s, st), stages.parse(stages.render(s, st), f'stage:{code}')]
                for s in SENTENCES + [st['sample']]]
        vec += [[sp, stages.parse(sp, f'stage:{code}')] for sp in st['read']]
        vec += [[sp.upper(), stages.parse(sp.upper(), f'stage:{code}')] for sp in list(st['forms'].values())[:8]]
        parse_stages[code] = vec
    convert_vec = []
    for code in stages.codes():
        st = stages.load(code)
        spelled = stages.render(st['sample'], st)
        for target in ['script', 'transport'] + [f'stage:{c}' for c in stages.codes() if c != code]:
            convert_vec.append([spelled, f'stage:{code}', target, stages.convert(spelled, f'stage:{code}', target)])
    for s in SENTENCES[:4]:
        convert_vec.append([engine.render(s), 'script', 'stage:hu', stages.convert(engine.render(s), 'script', 'stage:hu')])
    detect_vec = [[t, stages.detect(t)[0][0]] for t in DETECT]

    # the lexicon layer: its shape per code (the tables live in
    # data/lexicon/<code>.json, copied to docs/lexicon/ for the web) and
    # vectors: words read and written, loans folded, characters chosen
    lexicon_meta = {}
    for code in lexicon.codes():
        L = lexicon.lex(code)
        lexicon_meta[code] = {k: L.get(k) for k in ('name', 'kind', 'match', 'loans', 'fold', 'foreign', 'lengthen', 'sample')}
        lexicon_meta[code]['output'] = L.get('output', True)
        lexicon_meta[code]['sizes'] = {k: len(L[k]) for k in ('read', 'write', 'choices', 'native') if L.get(k)}
    lex_vec = {
        'read': [[c, w, lexicon.read_word(w, c)] for c, ws in LEX_READ.items() for w in ws],
        'write': [[c, t, lexicon.write_word(t, c)] for c, ts in LEX_WRITE.items() for t in ts],
        'loan': [[c, w, (lexicon.loan(w, c) or [None])[0]] for c, ws in LEX_LOAN.items() for w in ws],
        'choices': [[k, lexicon.choices(k)[:6]] for k in LEX_CHOICES],
        'parse': [[src, t, stages.parse(t, src)] for src, ts in LEX_TEXTS.items() for t in ts],
        'render': [[src, stages.parse(t, src), stages.render(stages.parse(t, src), src[6:])]
                   for src, ts in LEX_TEXTS.items() for t in ts],
        'detect': [[t, stages.detect(t)[0][0]] for ts in LEX_TEXTS.values() for t in ts],
        'roundtrip': [[src, t, stages.convert(t, src, src)] for src, ts in LEX_TEXTS.items() for t in ts],
    }

    spec = {
        'name': 'Diafon',
        'generated': dt.date.today().isoformat(),
        'source': git_sha(),
        'alphabet': {
            'consonant_bases': sorted(engine.C_BASES), 'vowel_bases': sorted(engine.V_BASES),
            'operators': sorted(engine.OPS - {'w'}), 'length': 'w',
            'tones': 'trailing digits after a segment',
        },
        'reading': [
            'Reading back inverts the rendering: longest match over a table of spellings, tone digits attached to the form before them, anything unmatched raw.',
            'The script table is the whole inventory of the grammar, small and capitalized; a repeated vowel operator (acc) reads as the shorter form (ac).',
            'A stage table is its spellings, long forms, capitalized and all-caps spellings and its read aliases (etymological spellings the stage never writes), over the script table as fallback.',
            'All-caps reads as capitalized: SZÉP -> SEwP -> SzÉP; the transport form carries no case beyond the first letter.',
            'Digraph boundaries inside compounds (házszám) read by longest match and can mislead; no dictionary is consulted.',
            'detect ranks the sources by coverage: the share of letters and marks a source reads with its own spellings; ties go to the script when its marks are present, to a syllable lexicon that read every word with a tone digit, to a word lexicon that read every word, then the preferred sources, then transport.',
            'The lexicon (data/lexicon) reads and writes word by word above the letters: a host with letters reads a word as a loan (the longest stem a loan lexicon reads among its common words, against the host dictionary stem and its own entries: the longest wins, the host on ties unless the stem has a foreign shape, the rest by the letters), else by its own entries (spoken stems), else by its letters when they read it in full, else by the letters with aliases and the script; a lexical stage reads by its lexicon; a word is written by the lexicon (the word, or a stem by prefix), else by the letters.',
        ],
        'grammar': [
            'A segment is one base letter followed by at most two operators (c j q x y), then w at most once and last, then tone digits.',
            'An operator or a digit never starts a segment; strictly, such input is an error; leniently, it passes through as typed.',
            'Case is orthographic: an uppercase base capitalizes its point, operators fold case, a long consonant capitalizes its first letter only.',
            'Segmentation is greedy left to right and unique: no two forms concatenated ever re-read as anything else.',
            'Streaming: everything before the last segment is final; a last segment that is a form may still grow, so it stays pending.',
            'Any character outside the 26 letters and the digits is raw and passes through.',
        ],
        'script': script,
        'forms': forms,
        'languages': languages,
        'stages': stage_data,
        'vectors': {
            'render': render_vec,
            'lenient': [[s, engine.render(s, strict=False)] for s in LENIENT],
            'invalid': INVALID,
            'stream': {s: trace(s) for s in SENTENCES[:3]},
            'stages': stage_vectors,
            'parse': {'script': parse_script, 'stages': parse_stages},
            'convert': convert_vec,
            'detect': detect_vec,
            'lexicon': lex_vec,
        },
        'lexicon': lexicon_meta,
    }
    out = os.path.join(ROOT, 'docs', 'spec.json')
    with open(out, 'w') as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)
    print(f'{out}: {len(forms)} forms, {len(languages)} languages, {len(stage_data)} stages, '
          f'{len(render_vec)} render vectors')


if __name__ == '__main__':
    main()
