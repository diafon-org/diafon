#!/usr/bin/env python3
"""What the Apple input methods bundle of the alphabet and the typing:
input_methods/apple/Resources/ (not committed, made by the builds).

  alphabet.json     the alphabet's spec without its vectors, its language
                    lists and its lexicons (the input methods carry no dictionary)
  lexicons.json     the one spelling that is a table and no dictionary: Mandarin's
                    pinyin syllables, read and written (12 KB), without the characters
  typing.json       the compiled profile without its vectors
  diafon-core.js    the alphabet in JavaScript, as the site runs it
  diafon-keys.js    the typing in JavaScript, as the Input page runs it
  diafon-glue.js    what the apps ask of the two (apple/Core)
  emoji.json        the word -> emoji choices (data/emoji.json); the iOS keyboard's
  DiafonSerif-Regular.ttf   the font the iOS screens show Diafon in

The apps run these two scripts as they are (apple/Core/Diafon.swift), so
they read and write exactly what the site does.
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, 'input_methods', 'apple', 'Resources')
PROFILE = 'diafon-v1'
# A spelling made by rule that the alphabet keeps as a table: bundled, so it is a keyboard like the
# lettered ones. Only the syllables: `choices` (the characters of each) stays out.
TABLES = {'zh': ('name', 'kind', 'match', 'read', 'write', 'sample')}


def main():
    os.makedirs(OUT, exist_ok=True)
    spec = json.load(open(os.path.join(REPO, 'docs', 'alphabet-spec.json'), encoding='utf-8'))
    spec = {k: v for k, v in spec.items() if k not in ('vectors', 'languages', 'lexicons')}
    profile = json.load(open(os.path.join(ROOT, 'spec', f'{PROFILE}.json'), encoding='utf-8'))
    profile = {k: v for k, v in profile.items() if k != 'vectors'}
    tables = {}
    for code, fields in TABLES.items():
        lex = json.load(open(os.path.join(REPO, 'data', 'lexicon', f'{code}.json'), encoding='utf-8'))
        tables[code] = {k: lex[k] for k in fields if k in lex}
    for name, data in (('alphabet.json', spec), ('typing.json', profile), ('lexicons.json', tables)):
        with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    shutil.copyfile(os.path.join(REPO, 'docs', 'assets', 'diafon-core.js'), os.path.join(OUT, 'diafon-core.js'))
    shutil.copyfile(os.path.join(ROOT, 'web', 'diafon-keys.js'), os.path.join(OUT, 'diafon-keys.js'))
    shutil.copyfile(os.path.join(ROOT, 'input_methods', 'apple', 'Core', 'diafon-glue.js'), os.path.join(OUT, 'diafon-glue.js'))
    shutil.copyfile(os.path.join(ROOT, 'data', 'emoji.json'), os.path.join(OUT, 'emoji.json'))
    shutil.copyfile(os.path.join(REPO, 'fonts', 'DiafonSerif-Regular.ttf'), os.path.join(OUT, 'DiafonSerif-Regular.ttf'))
    size = sum(os.path.getsize(os.path.join(OUT, n)) for n in os.listdir(OUT)) // 1024
    print(f'input_methods/apple/Resources: alphabet {spec["version"]}, typing {profile["id"]}, {size} KB')


if __name__ == '__main__':
    main()
