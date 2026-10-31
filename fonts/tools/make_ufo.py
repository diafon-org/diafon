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
  writes it) and the dotless i/j under above marks; liga for fi fl ff; calt
  and dist for the tones above the syllable (calt off, the sign follows it); rlig
  for the long consonants (t ZWJ t -> t.long), the drawn ones only: a pair
  not drawn yet is dropped, and the text shows the plain double;
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


def drawn_long(ufo, key):
    """The long consonants that ship: <letter>.long drawn as an SVG override,
    and the marked pairs built from it (s_uni0326.long from s.long)."""
    d = os.path.join(ROOT, 'fonts', 'svg', key)
    stems = {f[:-4] for f in os.listdir(d) if f.endswith('.svg')} if os.path.isdir(d) else set()
    return {g.name for g in ufo if g.name.endswith('.long')
            and (g.name in stems or g.name.split('_uni')[0] + '.long' in stems)}


def reachable(ufo, key):
    keep = {'.notdef', 'space'} | {g.name for g in ufo if g.unicodes}
    keep |= drawn_long(ufo, key)                                         # the rlig targets
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
    keep |= {g.name for g in ufo if re.fullmatch(r'tone\d+\.w\d+n?', g.name)}     # the calt targets
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


def is_letter(g):
    """A letter of a syllable: a letter codepoint (not a modifier, which the
    tone signs are), a baked composition, a dotless form or a ligature."""
    if g.unicodes:
        return unicodedata.category(chr(g.unicodes[0])) in ('Lu', 'Ll', 'Lt', 'Lo')
    return bool(re.fullmatch(r'.+_uni[0-9A-F]{4}', g.name)) or g.name in (
        'dotlessi', 'uni0237', 'dotlessj') or g.name in LIGAS or g.name.endswith('.long')


TONE_REACH = 8              # letters a tone above is centred over, at most


def tone_rules(ufo):
    """The tones above the syllable. calt: a tone sign after the syllable's
    letters -> tone<d>.w2 (two letters wide) after two letters and more,
    tone<d>.w1 after one, tone<d>.w1n after one narrow letter (i l j: two
    such syllables in a row keep apart); the longer is tried first, and a space, a mark of punctuation or the
    previous tone sign ends it. dist: the tone, its advance only the small
    gap after the syllable, set back by half of each letter's advance, so it
    centres on the syllable.
    Marks are skipped, so a letter with its marks counts once. Switched off
    (calt), the sign follows the syllable."""
    import yaml
    tones = yaml.safe_load(open(os.path.join(ROOT, 'data', 'script.yaml')))['tones']
    by_cp = {u: g.name for g in ufo for u in g.unicodes}
    signs = [(by_cp[ord(t['sign'])], d) for d, t in tones.items()
             if t['sign'] and ord(t['sign']) in by_cp and f'tone{d}.w2' in ufo]
    if not signs:
        return []
    letters = sorted(g.name for g in ufo if is_letter(g) and not is_mark(g))
    variants = [v for v in ('w1', 'w2', 'w1n') if f'tone{signs[0][1]}.{v}' in ufo]
    unit = sum(ufo[by_cp[ord(c)]].width for c in 'abcdefghijklmnopqrstuvwxyz') / 26
    narrow = [n for n in letters if ufo[n].width < BF.TONE_NARROW * unit] if 'w1n' in variants else []
    fea = ['@letter = [' + ' '.join(letters) + '];',
           '@tone = [' + ' '.join(s for s, _ in signs) + '];']
    if narrow:
        fea.append('@narrow = [' + ' '.join(narrow) + '];')
    for v in variants:
        fea.append(f'@tone_{v} = [' + ' '.join(f'tone{d}.{v}' for _, d in signs) + '];')
    fea.append('@tone_above = [' + ' '.join(f'tone{d}.{v}' for _, d in signs for v in variants) + '];')
    fea += ['', 'feature calt {', '    lookupflag IgnoreMarks;',
            "    sub @letter @letter @tone' by @tone_w2;"]
    if narrow:
        fea.append("    sub @narrow @tone' by @tone_w1n;")
    fea += ["    sub @letter @tone' by @tone_w1;", '} calt;', '']
    advances = sorted({ufo[n].width for n in letters})
    for a in advances:
        fea.append(f'@adv{a} = [' + ' '.join(n for n in letters if ufo[n].width == a) + '];')
    for a in advances:
        fea.append(f'lookup tone_back{a} {{ pos @tone_above <{-round(a / 2)} 0 0 0>; }} tone_back{a};')
    for k in range(1, TONE_REACH + 1):
        fea += [f'lookup tone_centre{k} {{', '    lookupflag IgnoreMarks;']
        fea += [f'    pos @adv{a} ' + '@letter ' * (k - 1) + f"@tone_above' lookup tone_back{a};" for a in advances]
        fea.append(f'}} tone_centre{k};')
    fea += ['', 'feature dist {'] + [f'    lookup tone_centre{k};' for k in range(1, TONE_REACH + 1)] + ['} dist;', '']
    return fea


def long_sources(ufo, stem, by_cp):
    """The glyphs a long consonant's letter reaches in text: for b_uni0323,
    the font's precomposed ḅ (the text is NFC) and the baked composition."""
    plain, *marks = stem.split('_uni')
    if plain not in ufo or not ufo[plain].unicodes:
        return []
    text = unicodedata.normalize('NFC', chr(ufo[plain].unicodes[0]) + ''.join(chr(int(m, 16)) for m in marks))
    out = [by_cp[ord(text)]] if len(text) == 1 and ord(text) in by_cp else []
    return out + [stem] * (stem in ufo and stem not in out)


def features(ufo):
    """ccmp: base + combining mark -> the baked composition; dotless i j under
    above marks; liga for the f ligatures; calt and dist for the tones above."""
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
    zwj = by_cp.get(0x200D)
    longs = [f'    sub {src} {zwj} {src} by {n};' for n in sorted(names)
             if zwj and n.endswith('.long') for src in long_sources(ufo, n[:-5], by_cp)]
    fea = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;', '']
    if above:
        fea += ['@above = [' + ' '.join(above) + '];', '']
    fea += ['feature ccmp {'] + subs + (['    lookup dotless {'] + dotless + ['    } dotless;'] if dotless and above else []) + ['} ccmp;', '']
    if longs:       # required, so letter-spacing does not undo a long consonant; before liga,
        fea += ['feature rlig {'] + longs + ['} rlig;', '']   # which HarfBuzz lets take f ZWJ f
    if ligas:
        fea += ['feature liga {'] + ligas + ['} liga;', '']
    fea += tone_rules(ufo)
    return '\n'.join(fea), len(subs)


def main(argv):
    fam = BF.family(argv[0] if argv else 'serif')
    src = argv[1] if len(argv) > 1 else fam['derived']
    out = argv[2] if len(argv) > 2 else fam['ufo']
    ufo = ufoLib2.Font()
    extractor.extractUFO(src, ufo, doGlyphs=True, doInfo=True, doKerning=True, doFeatures=False)
    keep = reachable(ufo, fam['key'])
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
    widths = {g.width for g in ufo if g.width and not g.name.endswith('.long')}   # a monospaced family says so (a long pair is two cells)
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
    # Windows clips ink above the win ascent: the tones above reach over it
    from fontTools.pens.boundsPen import BoundsPen
    top = 0
    for g in ufo:
        bp = BoundsPen(ufo)
        g.draw(bp)
        if bp.bounds:
            top = max(top, bp.bounds[3])
    info.openTypeOS2WinAscent = max(info.openTypeOS2WinAscent or 0, int(top + 0.999))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.isdir(out):
        import shutil
        shutil.rmtree(out)
    ufo.save(out)
    print(f'{os.path.relpath(out, ROOT)}: {len(ufo)} glyphs, {len(ufo.kerning)} kerning pairs, '
          f'{n_ccmp} ccmp compositions, {sum(1 for g in ufo if is_mark(g))} marks')


if __name__ == '__main__':
    main(sys.argv[1:])
