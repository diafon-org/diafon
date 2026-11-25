#!/usr/bin/env python3
"""The Mac input method's Info.plist with its input modes, and their names.

Each output is an input mode of its own, so the system's keyboard switching
(the input menu, the Globe key, Control-Space) chooses it: Diafon (the
script), one per language written by its letters alone (Diafon – Magyar), and
Mandarin's pinyin, a table of syllables the app carries (Diafon – Pinyin).
The list is fixed at build time, from the alphabet's spec; a mode is switched on
in System Settings → Keyboard → Input Sources.

Each mode has its own icon, drawn whole by tools/badge.swift (the system draws
nothing around an input method's icon): a filled frame with Diafon's mark cut
out of it, and for a language the mark's two dots over its code (HU), one
colour, which the system tints for the highlight and the dark menu bar.

Usage: modes.py <Info.plist template> <the app's Contents directory>
"""
import json
import os
import plistlib
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = 'org.diafon.inputmethod.Diafon'
TABLES = {'zh': 'zh-Hans'}      # scripts/gen_apple.py TABLES: the language the system files the keyboard under
LABEL = {'zh': 'PY'}             # the icon's letters where the language code is not what people know it by
NATIVE = {'zh': 'Pinyin', 'cs': 'Čeština', 'fi': 'Suomi', 'hu': 'Magyar', 'ig': 'Igbo', 'pl': 'Polski', 'sw': 'Kiswahili', 'tr': 'Türkçe'}


def modes():
    """-> [(mode id, name, language)]: Universal first, then the languages by name."""
    spec = json.load(open(os.path.join(os.path.dirname(ROOT), 'docs', 'alphabet-spec.json'), encoding='utf-8'))
    langs = sorted((c for c, st in spec['stages'].items() if st['state'] != 'lexical' or c in TABLES), key=lambda c: spec['stages'][c]['name'])
    # Diafon itself belongs to no one language: 'mul' (ISO 639, multiple languages), so the system
    # does not file it under English
    return [(f'{BASE}.universal', 'Diafon', 'mul')] + \
        [(f'{BASE}.{c}', f'Diafon – {NATIVE.get(c, spec["stages"][c]["name"])}', TABLES.get(c, c)) for c in langs]


def main():
    template, contents = sys.argv[1], sys.argv[2]
    plist = plistlib.load(open(template, 'rb'))
    listed, icons = {}, []
    for k, (mid, name, lang) in enumerate(modes()):
        code = mid.rsplit('.', 1)[1]
        icon = f'Diafon-{code}'
        icons.append(icon + '=' + ('' if k == 0 else LABEL.get(code, code.upper())))
        listed[mid] = {
            'TISInputSourceID': mid, 'TISIntendedLanguage': lang, 'TISIconIsTemplate': True,
            'tsInputModeDefaultStateKey': k == 0, 'tsInputModeIsVisibleKey': True,
            'tsInputModePrimaryInScriptKey': k == 0, 'tsInputModeScriptKey': 'smRoman',
            'tsInputModeCharacterRepertoireKey': ['Latn'],
            'tsInputModeMenuIconFileKey': icon + '.pdf', 'tsInputModeAlternateMenuIconFileKey': icon + '.pdf',
            'tsInputModePaletteIconFileKey': icon + '.pdf',
        }
    plist['tsInputMethodIconFileKey'] = 'Diafon-universal.pdf'
    plist.pop('TISIconLabels', None)
    subprocess.run(['swift', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'badge.swift'),
                    os.path.join(contents, 'Resources')] + icons, check=True)
    plist['ComponentInputModeDict'] = {'tsInputModeListKey': listed,
                                       'tsVisibleInputModeOrderedArrayKey': [m[0] for m in modes()]}
    plistlib.dump(plist, open(os.path.join(contents, 'Info.plist'), 'wb'))
    lproj = os.path.join(contents, 'Resources', 'en.lproj')
    os.makedirs(lproj, exist_ok=True)
    with open(os.path.join(lproj, 'InfoPlist.strings'), 'w', encoding='utf-16') as f:
        f.write('"CFBundleName" = "Diafon";\n"CFBundleDisplayName" = "Diafon";\n')
        for mid, name, _ in modes():
            f.write(f'"{mid}" = "{name}";\n')
    print(f'{len(modes())} input modes: ' + ', '.join(m[1] for m in modes()))


if __name__ == '__main__':
    main()
