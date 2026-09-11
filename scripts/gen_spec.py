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
import stages

SENTENCES = [
    'sjok sewp njawr', 'Sjan1, sjok!', 'SJAN', 'Gj Pj Gxy Txy Ic Sjw Tqyh Aw',
    'ma1 ma2 ma3 ma4', 'hoswuw aclmac', 'tqi3 sjuc3 tquc1', 'Diafon: ix i ux.',
    'kxy gxy txy dxy sxy zxy', 'ty dy ny sjy zjy tqy dqy', 'tcy dcy tcx dcx',
    'aq r ix ux icx ucx', 'aj ej ij oj uj ay ey iy oy uy', 'tyh dyh rch pf th kh',
]
LENIENT = ['Sjan1, jok!', 'jok', '1ma', 'tqyx', 'tww', 'twx', 'lj rj fj', 'bq ax txx', 'qwerty',
           'Hello, world!', 'x-ray', 'sj+ok']
INVALID = ['jok', '1', 'tqyx', 'tww', 'twx', 'lj', 'rj', 'fj', 'bq', 'ax', 'txx',
           'tcq', 'yx', 'wa', 'ejx', 'txyx']


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

    spec = {
        'name': 'Diafon',
        'generated': dt.date.today().isoformat(),
        'source': git_sha(),
        'alphabet': {
            'consonant_bases': sorted(engine.C_BASES), 'vowel_bases': sorted(engine.V_BASES),
            'operators': sorted(engine.OPS - {'w'}), 'length': 'w',
            'tones': 'trailing digits after a segment',
        },
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
        },
    }
    out = os.path.join(ROOT, 'docs', 'spec.json')
    with open(out, 'w') as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)
    print(f'{out}: {len(forms)} forms, {len(languages)} languages, {len(stage_data)} stages, '
          f'{len(render_vec)} render vectors')


if __name__ == '__main__':
    main()
