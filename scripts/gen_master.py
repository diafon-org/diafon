#!/usr/bin/env python3
"""Generate the master tables: docs/.include/master-tables.html, the body of
the Reference page (docs/reference.md; docs/assets/master.js drives the
table switch).

The universal table: every letter in use, grouped by the mark it wears, with
its glyph and its readings from the most to the least used (languages ·
native speakers). Then one table per language (glyph, kind, IPA, frequency),
stamped with the mapping's review state (reviewed or not).

Validation is the mapping's (scripts/mapping.py): every non-X phoneme mapped;
no two sounds of a language on one point outside `merges`.
"""
import functools
import html
import os
import sys
import unicodedata as ud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import ipa_names
import mapping
import script
from mapping import load_languages, nfd
from script import Tok

STATES = {'reviewed': ('reviewed', 'st-rev'),
          None: ('not reviewed', 'st-non')}


def load_mapping():
    return mapping.load()


def fmt(m):
    """Speakers, in millions, as the rough figure it is: ~3.8B, ~13M, ~1.1M."""
    if not m:
        return 'none'
    if m >= 1000:
        return f'~{m/1000:.1f}B'
    return f'~{m:.1f}M' if m < 10 else f'~{m:.0f}M'


def facts(groups):
    """A row of small figure tiles in labelled groups: [(label, [(value, what), ...]), ...]."""
    out = ''.join(f'<div class="fgroup"><span class="flabel">{label}</span><div class="ftiles">'
                  + ''.join(f'<div class="ft"><b>{v}</b><span>{w}</span></div>' for v, w in tiles)
                  + '</div></div>' for label, tiles in groups)
    return f'<div class="facts">{out}</div>'


def lang_name(d, tag='span'):
    """A language by its own name, its English name small after it."""
    own, en = d.get('native_name') or d['name'], d['name']
    return own if own == en else f'{own} <{tag} class="en-name">{en}</{tag}>'


def plain_name(d):
    own, en = d.get('native_name') or d['name'], d['name']
    return own if own == en else f'{own} · {en}'


def kind(pts):
    """consonant, vowel or glide: the kind of sound, in plain words."""
    letter, marks = pts[0][0]
    if letter in 'jw':
        return 'glide'
    return 'vowel' if script.vocalic(pts[0][0]) else 'consonant'


def glyph(pts, caps=False):
    """The letters of a sound's points; capitalized, the first one."""
    return script.write([Tok(c, long, caps and k == 0) for k, (c, long) in enumerate(pts)])


MESSY = ('<b>Where it gets messy.</b> The reverse anchor marks a language\'s own further-back variant of a '
         'sound, and only languages that have both sounds write it: Hindi /t/ and /ʈ/ are '
         '<span class="ug">t</span> and <span class="ug">t̖</span>, Arabic /s/ and /sˤ/ are '
         '<span class="ug">s</span> and <span class="ug">s̖</span>.')


@functools.lru_cache(None)
def written_as():
    """{sound (NFD): {points: [language codes]}}: how each language writes each sound."""
    cons, vows, over, *_ = load_mapping()
    out = {}
    for code, d in load_languages().items():
        for sec, table in (('consonants', cons), ('vowels', vows)):
            for ipa, freq in d[sec].items():
                if freq == 'X':
                    continue
                key = nfd(ipa)
                pts = over.get(code, {}).get(key) or table.get(key)
                if pts:
                    out.setdefault(key, {}).setdefault(pts, []).append(code)
    return out


RULE_HUSH = {nfd(s) for s in ('ɕ', 'ʑ', 'tɕ', 'dʑ', 'ʂ', 'ʐ', 'tʂ', 'dʐ', 'ʃ', 'ʒ', 'tʃ', 'dʒ')}
RULE_MERGED = {nfd(s) for s in ('ə', 'ʌ')}


def rule_of(ipa):
    """Which spelling rule (reference.md, below the tables) gives a sound two letters: 1 the hush
    and the soft series, 3 one phoneme one letter, 2 the vowel areas' split."""
    key = nfd(ipa)
    return 1 if key in RULE_HUSH else 3 if key in RULE_MERGED else 2


def also(ipa, pts, here=None):
    """'rule 1 · s̖ in Polish, Russian': the rule that gives this sound another letter elsewhere,
    and that letter with its languages, each a link to its own table at that row."""
    langs = load_languages()
    parts = []
    for other, codes in sorted(written_as().get(nfd(ipa), {}).items(), key=lambda kv: -len(kv[1])):
        codes = [c for c in codes if c != here]
        if other == pts or not codes:
            continue
        g = html.escape(glyph(other))
        names = ', '.join(f'<a href="#table={c}&amp;letter={g}">{html.escape(langs[c]["name"])}</a>'
                          for c in sorted(codes, key=lambda c: langs[c]['name']))
        parts.append(f'<span class="ug">{g}</span> in {names}')
    if not parts:
        return ''
    n = rule_of(ipa)
    return f'<span class="also"><a class="rtag" href="#rule-{n}">rule {n}</a> {"; ".join(parts)}</span>'


def note_row(pts, state, cols):
    """The reverse anchor's explanation, once a table, above its first reverse-anchor row."""
    if state.get('noted') or 'reverse' not in pts[0][0][1]:
        return []
    state['noted'] = True
    return [f'<tr class="note"><td colspan="{cols}">{MESSY}</td></tr>']


# the groups of a table, in order: what kind of letter, and the mark it wears
GROUPS = [
    ((False, ()), 'consonants', 'plain letters'),
    ((False, ('anchor',)), 'consonants', 'the anchor: hushed or soft'),
    ((False, ('dot',)), 'consonants', 'the dot: a fixed nearby sound; on s z c x, the soft one'),
    ((False, ('reverse',)), 'consonants', "the reverse anchor: the language's own variant, further back"),
    ((False, ('flip',)), 'consonants', 'the double dot: the rounded glide, the vocalic r'),
    ((True, ()), 'vowels', 'plain letters'),
    ((True, ('flip',)), 'vowels', 'the double dot: lip rounding swapped; on a, the front a'),
    ((True, ('underdot',)), 'vowels', 'the dot below: more open, only in languages with both; on a, the schwa'),
    ((True, ('flip', 'underdot')), 'vowels', 'the double dot and the dot below'),
    ((True, ('grave',)), 'vowels', 'the grave: nasal'),
    ((True, ('underdot', 'grave')), 'vowels', 'the dot below and the grave: nasal and more open'),
    ((True, ('flip', 'grave')), 'vowels', 'the double dot and the grave'),
]
_GROUP = {k: i for i, (k, _, _) in enumerate(GROUPS)}
_LETTERS = 'ptkbdgfvszcxqmnlrhjw' + 'aeiou'
SEQUENCES = len(GROUPS)


def group_of(pts):
    if len(pts) > 1:
        return SEQUENCES
    letter, marks = pts[0][0]
    return _GROUP[(letter in script.VOWELS, marks)]


def order_key(pts):
    (letter, marks), long = pts[0]
    return (group_of(pts), _LETTERS.index(letter), long, len(pts), [(_LETTERS.index(c[0]), c[1], l) for c, l in pts[1:]])


def group_rows(pts, state, cols):
    """The group headers a row opens: consonants or vowels, then the mark."""
    g = group_of(pts)
    if g == state.get('group'):
        return []
    state['group'] = g
    out = []
    if g == SEQUENCES:
        return [f'<tr class="grp"><th colspan="{cols}">sequences</th></tr>',
                f'<tr class="sub"><th colspan="{cols}">a sound written with two letters in a row</th></tr>']
    _, top, sub = GROUPS[g]
    if top != state.get('top'):
        state['top'] = top
        out.append(f'<tr class="grp"><th colspan="{cols}">{top}</th></tr>')
    out.append(f'<tr class="sub"><th colspan="{cols}">{sub}</th></tr>')
    return out


def glyph_cell(pts):
    return (f'<td class="g"><span>{html.escape(glyph(pts))}</span> '
            f'<span>{html.escape(glyph(pts, caps=True))}</span></td>')


def universal_table(agg, shares):
    rows = []
    for pts, reads in agg.items():
        if len(pts) > 1 or pts[0][1]:
            continue    # a sequence is two letters in a row; a long sound is its short one, long
        sh = shares.get(pts, {})
        prim = next((i for i, v in sh.items() if v == 'primary'), None)
        rd = sorted(reads.items(),
                    key=lambda kv: (0 if nfd(kv[0]) == prim else 1, -kv[1][1]))
        rows.append((order_key(pts), pts, rd))
    rows.sort(key=lambda r: r[0])
    langs = load_languages()
    name = lambda c: lang_name(langs[c]) if c in langs else c
    english = lambda codes: ', '.join(sorted(langs[c]['name'] if c in langs else c for c in codes))   # the hover list
    total = sum(d['speakers']['native'] for d in langs.values())
    out = ['<section id="sec-universal" data-name="All languages supported by Diafon">', '<h2 id="universal">Diafon: every letter in use</h2>',
           facts([('covers', [(len(langs), 'languages'), (fmt(total), 'native speakers')]),
                  ('letters in use', [(len(rows), 'letters')])]),
           '<p class="lede">Every letter any language uses, consonants then vowels, grouped by the mark '
           'the letter wears. Long sounds and diphthongs are not listed: a long vowel takes the acute, '
           'a long consonant is written double, and a diphthong is two letters in a row.</p>',
           '<div class="mt-wrap"><table class="mt">',
           '<tr><th>Diafon</th><th>kind</th>'
           '<th>main reading</th><th>other readings</th></tr>']
    state = {}
    for key, pts, rd in rows:
        out += group_rows(pts, state, 4) + note_row(pts, state, 4)
        ipa, (n, s, codes) = rd[0]
        primary = (f'<a class="wref ug" href="{ipa_names.url(ipa)}" target="_blank">/{ipa}/</a>'
                   f'<a class="rname" href="{ipa_names.url(ipa)}" target="_blank">{ipa_names.name(ipa)}</a>'
                   f'<span class="st"><span class="who" title="{html.escape(english(codes))}">{n} language{"s" if n > 1 else ""}</span>'
                   f' · {fmt(s)} native speakers</span>' + also(ipa, pts))
        groups = ''
        for ipa, (n, s, codes) in rd[1:]:
            lines = f'<span class="just">{", ".join(name(c) for c in sorted(codes, key=lambda c: langs[c]["name"] if c in langs else c))}</span>'
            groups += (f'<div class="rgroup">'
                       f'<a class="wref ug" href="{ipa_names.url(ipa)}" target="_blank">/{ipa}/</a>'
                       f'<a class="rname" href="{ipa_names.url(ipa)}" target="_blank">{ipa_names.name(ipa)}</a>{lines}{also(ipa, pts)}</div>')
        out.append(f'<tr data-letter="{html.escape(glyph(pts))}">{glyph_cell(pts)}'
                   f'<td class="tt">{kind(pts)}</td><td>{primary}</td><td>{groups}</td></tr>')
    out.append('</table></div>')
    out.append(overview())
    out.append('</section>')
    return '\n'.join(out)


def overview():
    """The languages at a glance, inside the Diafon view: a row opens that language."""
    review = load_mapping()[4]
    langs = load_languages()
    rows = []
    for code in sorted(langs, key=lambda c: -langs[c]['speakers']['native']):
        d = langs[code]
        n_c = sum(1 for v in d['consonants'].values() if v != 'X')
        n_v = sum(1 for v in d['vowels'].values() if v != 'X')
        tag = ' <span class="rev">reviewed</span>' if review.get(code) else ''
        rows.append(f'<tr data-goto="{code}"><td><b>{lang_name(d)}</b>{tag}</td>'
                    f'<td class="tt">{fmt(d["speakers"]["native"])}</td><td class="tt">{fmt(d["speakers"]["total"])}</td>'
                    f'<td class="tt">{n_c}</td><td class="tt">{n_v}</td></tr>')
    return ('<h2 id="languages">The languages</h2>\n'
            f'<p class="lede">{len(langs)} languages so far. Pick one for its own table. A mapping marked '
            '<span class="rev">reviewed</span> has been checked against the literature.</p>\n'
            '<div class="mt-wrap"><table class="mt langs">'
            '<tr><th rowspan="2">language</th><th colspan="2">speakers</th><th colspan="2">phonemes used</th></tr>'
            '<tr><th>native</th><th>overall</th><th>consonants</th><th>vowels</th></tr>' + ''.join(rows) + '</table></div>')


FREQ = {'L': 'frequent', 'M': 'ordinary', 'S': 'infrequent', 'X': 'marginal or in loans'}


FREQ = {'L': 'frequent', 'M': 'ordinary', 'S': 'infrequent', 'X': 'marginal or in loans'}


def language_tables():
    cons, vows, over, merges, review, _ = load_mapping()
    langs = load_languages()
    order = sorted(langs, key=lambda c: -langs[c]['speakers']['native'])
    secs = []
    for code in order:
        d = langs[code]
        by = {}
        for sec, table in (('consonants', cons), ('vowels', vows)):
            for ipa, freq in d[sec].items():
                key = nfd(ipa)
                pts = over.get(code, {}).get(key) or table.get(key)
                by.setdefault(pts, []).append((ipa, freq))
        rows, state = [], {}
        rank = {'L': 0, 'M': 1, 'S': 2, 'X': 3}
        for pts in sorted(by, key=order_key):
            rows += group_rows(pts, state, 4) + note_row(pts, state, 4)
            pairs = sorted(by[pts], key=lambda p: rank[p[1]])
            reading = ' = '.join(
                f'<a class="wref ug" href="{ipa_names.url(i)}" target="_blank">'
                f'/{ud.normalize("NFC", i)}/</a>' for i, _ in pairs)
            reading += (f'<a class="rname" href="{ipa_names.url(pairs[0][0])}"'
                        f' target="_blank">{ipa_names.name(pairs[0][0])}</a>')
            if len(pairs) > 1:
                reading += '<span class="rname">one phoneme, merged</span>'
            reading += ''.join(also(i, pts, code) for i, freq in pairs if freq != 'X')
            rows.append(f'<tr data-letter="{html.escape(glyph(pts))}">{glyph_cell(pts)}'
                        f'<td class="tt">{kind(pts)}</td>'
                        f'<td>{reading}</td>'
                        f'<td class="tt">{FREQ.get(pairs[0][1], "")}</td></tr>')
        n_c = sum(1 for v in d['consonants'].values() if v != 'X')
        n_v = sum(1 for v in d['vowels'].values() if v != 'X')
        secs.append(
            f'<section id="sec-{code}" hidden data-name="{plain_name(d)}">'
            f'<h2 id="{code}">{lang_name(d)}</h2>\n'
            + facts([('speakers', [(fmt(d["speakers"]["native"]), 'native'), (fmt(d["speakers"]["total"]), 'overall')]),
                     ('phonemes used', [(n_c, 'consonants'), (n_v, 'vowels')])]) + '\n'
            '<div class="mt-wrap"><table class="mt">'
            '<tr><th>Diafon</th><th>kind</th><th>reading</th><th>how common</th></tr>'
            + ''.join(rows) + '</table></div></section>')
    return '\n'.join(secs)


def main():
    agg = mapping.aggregate()  # validates
    shares = load_mapping()[5]
    page = universal_table(agg, shares) + '\n' + language_tables() + '\n'
    out = os.path.join(ROOT, 'docs', '.include', 'master-tables.html')
    open(out, 'w').write(page)
    print(f'mapping valid · {out}: {len(agg)} letters and sequences, {len(load_languages())} languages')


if __name__ == '__main__':
    main()
