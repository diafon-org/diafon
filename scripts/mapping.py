#!/usr/bin/env python3
"""The mapping: which point writes which sound of which language, from
data/mapping.yaml and data/languages/*.yaml.

A sound is written by one point or by a sequence of them (pʰ is p and h);
here always a tuple of points, each (composition, long).

  load()                  the mapping, the vowel areas applied
  language_points(code)   {points: [(ipa, frequency), ...]} for one language
  aggregate()             {points: {ipa: [languages, speakers, codes]}} over
                          every language; exits when the mapping is invalid
"""
import glob
import os
import sys
import unicodedata as ud

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import script


def nfd(s):
    return ud.normalize('NFD', s)


def nfc(s):
    return ud.normalize('NFC', s)


def seq(value):
    """A mapping value (a point name, or a list of them) -> a tuple of points."""
    names = value if isinstance(value, list) else [value]
    return tuple(script.point(str(n)) for n in names)


def name(points):
    """Points -> their names, joined (an open composition by its glyph)."""
    return ' '.join(script.NAME.get(c, script.compose(c)) + (script.LONG if long else '') for c, long in points)


def quality(ipa):
    """The vowel quality a symbol's area is decided by: length and nasality
    stripped, a sequence by its nucleus."""
    return ipa.replace('ː', '').replace('̃', '')[0]


def within(point, area):
    """Whether a point lies in an area: the area's letter, its marks among the point's."""
    return point[0][0] == area[0][0] and set(area[0][1]) <= set(point[0][1])


def resplit(points, area, split):
    """A vowel's points moved from an area's point to its split, through
    length, nasality and a following glide: the first point takes the
    split's marks beside its own."""
    (letter, marks), long = points[0]
    extra = [m for m in marks if m not in area[0][1]]
    marks = tuple(m for m in script.V_MARKS if m in split[0][1] or m in extra)
    return (((letter, marks), long),) + points[1:]


def load_languages():
    langs = {}
    for path in sorted(glob.glob(os.path.join(ROOT, 'data', 'languages', '*.yaml'))):
        d = yaml.safe_load(open(path, encoding='utf-8'))
        langs[d['code']] = d
    return langs


_LOADED = None
SPLITS = set()          # the split points the areas name, in use or not


def load():
    """-> (consonants, vowels, overrides, merges, review, shares): sounds
    (NFD) to points, per-language overrides, the reviewed merges, the review
    state, and for points that write more than one sound, each reading and
    its reason ('primary', or {language: why})."""
    global _LOADED
    if _LOADED is None:
        m = yaml.safe_load(open(os.path.join(ROOT, 'data', 'mapping.yaml'), encoding='utf-8'))
        cons = {nfd(k): seq(v) for k, v in m['consonants'].items()}
        vows = {nfd(k): seq(v) for k, v in m['vowels'].items()}
        over = {c: {nfd(k): seq(v) for k, v in d.items()} for c, d in m['overrides'].items()}
        merges = {c: [{nfd(a), nfd(b)} for a, b in pairs] for c, pairs in (m.get('merges') or {}).items()}
        review = m.get('review') or {}
        shares = {seq(f): {nfd(i): v for i, v in d.items()} for f, d in (m.get('shares') or {}).items()}
        areas = {seq(a)[0]: {'core': nfd(str(d['core'])),
                             'split': {seq(sf)[0]: [nfd(q) for q in qs] for sf, qs in (d.get('split') or {}).items()}}
                 for a, d in (m.get('areas') or {}).items()}
        _areas(areas, vows, over, merges, shares)
        SPLITS.update(sf for d in areas.values() for sf in d['split'])
        _LOADED = cons, vows, over, merges, review, shares
    return _LOADED


def _areas(areas, vows, over, merges, shares):
    """The vowel areas (mapping.yaml `areas`): a vowel is written with its
    area's point unless its language contrasts it with another vowel on that
    same point; then the one listed under the area's `split` takes the split
    point, through length and nasality. Fills `over`, and the readings each
    area point and split point carries into `shares`."""
    split = {}                                  # quality -> (area point, split point)
    for area, a in areas.items():
        for sf, qs in a['split'].items():
            for q in qs:
                split[q] = (area, sf)

    def area_of(q):
        pts = vows.get(q)
        return pts[0] if pts and len(pts) == 1 else None

    def primary(points, ipa):
        reads = shares.setdefault(points, {})
        if not any(v == 'primary' for v in reads.values()):
            reads[ipa] = 'primary'
    for ipa, pts in vows.items():
        q = quality(ipa)
        if areas.get(area_of(q), {}).get('core') == q:
            primary(pts, ipa)
        if q in split:
            area, sf = split[q]
            if areas[area]['split'][sf][0] == q and within(pts[0], area):   # the split's reference value (œ̃, written
                primary(resplit(pts, area, sf), ipa)                         # in another area, names nothing here)

    for code, d in load_languages().items():
        lang = over.setdefault(code, {})
        by = {}
        for ipa, freq in d['vowels'].items():
            k = nfd(ipa)
            pts = lang.get(k) or vows.get(k)
            if pts and freq != 'X':
                by.setdefault(pts, []).append(k)
        for pts, ks in by.items():
            if len(ks) < 2 or (len(ks) == 2 and set(ks) in merges.get(code, [])):
                continue
            for k in ks:
                if k in lang or quality(k) not in split:
                    continue
                area, sf = split[quality(k)]
                assert within(pts[0], area), f'{code}: {k} on {name(pts)}, outside its area {name((area,))}'
                lang[k] = resplit(pts, area, sf)
        # a split, once the language makes it, is how it writes that vowel
        # everywhere: German ɔ is ọ in Gott and in Leute (ọj̈) alike
        splitq = {quality(k) for k, pts in lang.items() if quality(k) in split
                  and within(pts[0], split[quality(k)][1])}
        for ipa in d['vowels']:
            k = nfd(ipa)
            if k in lang or quality(k) not in splitq:
                continue
            area, sf = split[quality(k)]
            pts = vows.get(k)
            if pts and within(pts[0], area):
                lang[k] = resplit(pts, area, sf)
        for ipa in d['vowels']:
            k = nfd(ipa)
            pts = lang.get(k) or vows.get(k)
            reads = shares.get(pts, {})
            if pts and reads.get(k) != 'primary':
                area = area_of(quality(k))
                shares.setdefault(pts, {}).setdefault(k, {}).setdefault(
                    code, f'the {name((area,)) if area else quality(k)} area')


def language_points(code):
    """-> {points: [(ipa, frequency), ...]} for one language (marginal sounds included)."""
    cons, vows, over, _, _, _ = load()
    d = load_languages()[code]
    out = {}
    for sec, table in (('consonants', cons), ('vowels', vows)):
        for ipa, freq in d[sec].items():
            k = nfd(ipa)
            pts = over.get(code, {}).get(k) or table.get(k)
            out.setdefault(pts, []).append((nfc(ipa), freq))
    return out


def special(points):
    """The points that carry a reading per language by design: the double dot below
    and the vowel grave."""
    return len(points) == 1 and not points[0][1] and \
        ('twodots' in points[0][0][1] or 'grave' in points[0][0][1])


_AGG = None


def aggregate():
    global _AGG
    if _AGG is not None:
        return _AGG
    cons, vows, over, merges, _, shares = load()
    agg, errors = {}, []
    for code, d in load_languages().items():
        native = d['speakers']['native']
        taken = {}
        for sec, table in (('consonants', cons), ('vowels', vows)):
            for ipa, freq in d[sec].items():
                k = nfd(ipa)
                pts = over.get(code, {}).get(k) or table.get(k)
                if not pts:
                    errors.append(f'{code}: unmapped {ipa}')
                    continue
                if freq == 'X':
                    continue    # writable, but out of the stats and the injectivity check
                if pts in taken:
                    pair = {k, nfd(taken[pts])}
                    if pair not in merges.get(code, []):
                        errors.append(f'{code}: {ipa} and {taken[pts]} both on {name(pts)}')
                        continue
                taken[pts] = ipa
                e = agg.setdefault(pts, {}).setdefault(nfc(ipa), [0, 0.0, []])
                e[0] += 1
                e[1] += native
                e[2].append(code)
    # one reading per regular point: more belong to the double dot below and the grave
    for pts, reads in agg.items():
        if len(reads) < 2 or special(pts) or len(pts) > 1:
            continue
        allowed = set(shares.get(pts, {}))
        extra = {i for i in map(nfd, reads) if i not in allowed}
        if extra or not allowed:
            errors.append(f'unlisted share on {name(pts)}: {sorted(reads)}')
    if errors:
        print('MAPPING INVALID:', *errors, sep='\n  ')
        sys.exit(1)
    _AGG = agg
    return agg


if __name__ == '__main__':
    for pts, reads in aggregate().items():
        print(name(pts), ' '.join(reads))
