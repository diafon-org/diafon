#!/usr/bin/env python3
"""Turn a derived font into editable sources: fonts/sources/<Family>-Regular.ufo.

The chain: build_font.py derives fonts/build/Diafon-derived.ttf from Noto Serif
(the surgery, the web letters); this script extracts a UFO from it, prunes it
to what the system reaches, and writes the feature code the font needs; then
fontmake compiles the UFO into the shipping fonts/Diafon-Regular.ttf, the
build Google Fonts expects (sources + fontmake), checked by FontBakery.

What the UFO carries:
- every glyph with a codepoint, plus the glyphs those reach through components
  and the ligatures; Noto's small caps, figure variants and other unreachable
  glyphs are dropped;
- kerning and groups, pruned to the kept glyphs (fontmake writes the kern feature);
- mark anchors as extracted from Noto's GPOS (fontmake writes mark and mkmk);
- our own features.fea: ccmp for the baked letter+mark pairs (a base plus a
  combining mark renders as its composition, as the composed-marks stage
  writes it) and the dotless i/j under above marks; liga for fi fl ff;
- font info to Google Fonts' rules, glyph categories for GDEF, the meta table.

    python3 fonts/tools/make_ufo.py [serif|sans|mono] [derived.ttf] [out.ufo]
"""
import os
import re
import sys
import unicodedata

import extractor
import ufoLib2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_font as BF

ROOT = BF.ROOT
VERSION = (1, 0)
LIGAS = {'fi': ('f', 'i'), 'fl': ('f', 'l'), 'f_f': ('f', 'f'),
         'f_f_i': ('f', 'f', 'i'), 'f_f_l': ('f', 'f', 'l')}


def reachable(ufo):
    keep = {'.notdef', 'space'} | {g.name for g in ufo if g.unicodes}
    keep |= {n for n in LIGAS if n in ufo}
    # the baked compositions (<base>_uniXXXX) of kept bases: the ccmp targets,
    # which need no codepoint of their own
    for g in ufo:
        m = re.fullmatch(r'(.+)_uni([0-9A-F]{4})', g.name)
        if m and m.group(1) in keep:
            keep.add(g.name)
    for dn in ('dotlessi', 'uni0237', 'dotlessj', 'uni25CC'):
        if dn in ufo:
            keep.add(dn)
    stack = list(keep)
    while stack:                       # components pull their parts along
        g = ufo[stack.pop()]
        for c in g.components:
            if c.baseGlyph in ufo and c.baseGlyph not in keep:
                keep.add(c.baseGlyph)
                stack.append(c.baseGlyph)
    return keep


def is_mark(g):
    return any(unicodedata.category(chr(u)) == 'Mn' for u in g.unicodes) or (
        g.width == 0 and any(a.name.startswith('_') for a in g.anchors))


def features(ufo):
    """ccmp: base + combining mark -> the baked composition; dotless i j under
    above marks; liga for the f ligatures."""
    names = {g.name for g in ufo}
    by_cp = {u: g.name for g in ufo for u in g.unicodes}   # the mark's real name
    subs = []                                                # (acutecomb, not uni0301)
    for g in ufo:
        m = re.fullmatch(r'(.+)_uni([0-9A-F]{4})', g.name)
        if not m:
            continue
        base, mark = m.group(1), f'uni{m.group(2)}'
        if mark not in names:
            mark = by_cp.get(int(m.group(2), 16), mark)
        if base in names and mark in names:
            subs.append(f'    sub {base} {mark} by {g.name};')
    above = sorted(g.name for g in ufo if is_mark(g) and g.unicodes
                   and unicodedata.combining(chr(g.unicodes[0])) == 230)
    dotless = []
    for base, dl in (('i', 'dotlessi'), ('j', 'uni0237')):
        if dl in names and base in names:
            dotless.append(f"    sub {base}' @above by {dl};")
    ligas = [f'    sub {" ".join(parts)} by {n};' for n, parts in LIGAS.items()
             if n in names and all(p in names for p in parts)]
    fea = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;', '']
    if above:
        fea += ['@above = [' + ' '.join(above) + '];', '']
    fea += ['feature ccmp {'] + subs + (['    lookup dotless {'] + dotless + ['    } dotless;'] if dotless and above else []) + ['} ccmp;', '']
    if ligas:
        fea += ['feature liga {'] + ligas + ['} liga;', '']
    return '\n'.join(fea), len(subs)


def main(argv):
    fam = BF.family(argv[0] if argv else 'serif')
    src = argv[1] if len(argv) > 1 else fam['derived']
    out = argv[2] if len(argv) > 2 else fam['ufo']
    ufo = ufoLib2.Font()
    extractor.extractUFO(src, ufo, doGlyphs=True, doInfo=True, doKerning=True, doFeatures=False)
    keep = reachable(ufo)
    for name in [g.name for g in ufo]:
        if name not in keep:
            del ufo[name]
    # kerning and groups only over kept glyphs
    for gname, members in list(ufo.groups.items()):
        kept = [m for m in members if m in ufo]
        if kept:
            ufo.groups[gname] = kept
        else:
            del ufo.groups[gname]
    def alive(k):
        return k in ufo or k in ufo.groups
    for pair in [p for p in ufo.kerning if not (alive(p[0]) and alive(p[1]))]:
        del ufo.kerning[pair]
    # no inherited TrueType instructions: the shipping font is built unhinted
    ufo.lib.pop('public.truetype.instructions', None)
    for g in ufo:
        g.lib.pop('public.truetype.instructions', None)
    ufo.lib['public.openTypeCategories'] = {g.name: ('mark' if is_mark(g) else 'base') for g in ufo}
    ufo.lib['public.openTypeMeta'] = {'dlng': ['Latn'], 'slng': ['Latn']}
    ufo.lib['public.glyphOrder'] = sorted(g.name for g in ufo)
    ufo.features.text, n_ccmp = features(ufo)
    info = ufo.info
    info.familyName, info.styleName = fam['family'], 'Regular'
    info.versionMajor, info.versionMinor = VERSION
    info.copyright = BF.COPYRIGHT
    info.openTypeNameLicense = BF.LICENSE_TEXT
    info.openTypeNameLicenseURL = 'https://openfontlicense.org'
    info.openTypeNameDesigner = 'The Diafon Project Authors, after ' + fam['after']
    info.openTypeNameManufacturer = 'The Diafon Project'
    info.openTypeNameManufacturerURL = BF.REPO
    info.openTypeNameDescription = None
    info.openTypeNameSampleText = None
    info.openTypeNameUniqueID = None
    info.openTypeNameVersion = None                # fontmake writes it from versionMajor.Minor
    info.openTypeNameRecords = None                # no raw Noto name records: fontmake builds the table from the fields
    info.trademark = None
    info.openTypeNamePreferredFamilyName = None
    info.openTypeNamePreferredSubfamilyName = None
    info.openTypeNameCompatibleFullName = None
    info.openTypeNameWWSFamilyName = None
    info.openTypeNameWWSSubfamilyName = None
    info.openTypeOS2Type = []                      # installable embedding
    widths = {g.width for g in ufo if g.width}      # a monospaced family says so
    if len(widths) == 1:
        info.postscriptIsFixedPitch = True
        panose = list(info.openTypeOS2Panose or [0] * 10)
        panose[3] = 9                               # bProportion: monospaced
        info.openTypeOS2Panose = panose
    info.openTypeOS2VendorID = 'DIAF'
    sel = set(info.openTypeOS2Selection or [])
    sel.add(7)                                     # USE_TYPO_METRICS
    info.openTypeOS2Selection = sorted(sel)
    info.openTypeHeadCreated = None
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.isdir(out):
        import shutil
        shutil.rmtree(out)
    ufo.save(out)
    print(f'{os.path.relpath(out, ROOT)}: {len(ufo)} glyphs, {len(ufo.kerning)} kerning pairs, '
          f'{n_ccmp} ccmp compositions, {sum(1 for g in ufo if is_mark(g))} marks')


if __name__ == '__main__':
    main(sys.argv[1:])
