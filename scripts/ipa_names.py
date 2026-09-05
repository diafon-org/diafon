"""Phonetic names for the IPA symbols the data uses.

name(sym) -> e.g. 'voiceless postalveolar fricative' for ʃ, composing
modifier prefixes (aspirated, palatalized, long, nasalized, ...) onto the
base description. Unknown symbols raise, so gaps surface at generation time.
"""
import unicodedata as ud

BASE = {
 'p': 'voiceless bilabial plosive', 'b': 'voiced bilabial plosive',
 't': 'voiceless alveolar plosive', 'd': 'voiced alveolar plosive',
 'k': 'voiceless velar plosive', 'g': 'voiced velar plosive',
 'q': 'voiceless uvular plosive', 'ʔ': 'glottal stop',
 'c': 'voiceless palatal plosive', 'ɟ': 'voiced palatal plosive',
 'ʈ': 'voiceless retroflex plosive', 'ɖ': 'voiced retroflex plosive',
 'ɓ': 'voiced bilabial implosive', 'ɗ': 'voiced alveolar implosive',
 'm': 'bilabial nasal', 'n': 'alveolar nasal', 'ɳ': 'retroflex nasal',
 'ɲ': 'palatal nasal', 'ŋ': 'velar nasal', 'ɴ': 'moraic (uvular) nasal',
 'f': 'voiceless labiodental fricative', 'v': 'voiced labiodental fricative',
 'θ': 'voiceless dental fricative', 'ð': 'voiced dental fricative',
 's': 'voiceless alveolar fricative', 'z': 'voiced alveolar fricative',
 'ʃ': 'voiceless postalveolar fricative', 'ʒ': 'voiced postalveolar fricative',
 'ʂ': 'voiceless retroflex fricative', 'ʐ': 'voiced retroflex fricative',
 'ɕ': 'voiceless alveolo-palatal fricative', 'ʑ': 'voiced alveolo-palatal fricative',
 'x': 'voiceless velar fricative', 'ɣ': 'voiced velar fricative',
 'χ': 'voiceless uvular fricative', 'ʁ': 'voiced uvular fricative',
 'ħ': 'voiceless pharyngeal fricative', 'ʕ': 'voiced pharyngeal fricative',
 'h': 'voiceless glottal fricative', 'ɦ': 'voiced glottal fricative',
 'ɸ': 'voiceless bilabial fricative', 'ʝ': 'voiced palatal fricative',
 'ʋ': 'labiodental approximant', 'ɹ': 'alveolar approximant',
 'ɻ': 'retroflex approximant', 'j': 'palatal approximant',
 'ɥ': 'labial-palatal approximant', 'w': 'labial-velar approximant',
 'l': 'alveolar lateral approximant', 'ɭ': 'retroflex lateral approximant',
 'ʎ': 'palatal lateral approximant',
 'r': 'alveolar trill', 'ɾ': 'alveolar tap', 'ɽ': 'retroflex flap',
 'ts': 'voiceless alveolar affricate', 'dz': 'voiced alveolar affricate',
 'tʃ': 'voiceless postalveolar affricate', 'dʒ': 'voiced postalveolar affricate',
 'tɕ': 'voiceless alveolo-palatal affricate', 'dʑ': 'voiced alveolo-palatal affricate',
 'tʂ': 'voiceless retroflex affricate', 'dʐ': 'voiced retroflex affricate',
 'pf': 'voiceless labial affricate',
 'i': 'close front unrounded vowel', 'y': 'close front rounded vowel',
 'ɨ': 'close central unrounded vowel', 'ɯ': 'close back unrounded vowel',
 'u': 'close back rounded vowel',
 'ɪ': 'near-close front unrounded vowel', 'ʏ': 'near-close front rounded vowel',
 'ʊ': 'near-close back rounded vowel',
 'e': 'close-mid front unrounded vowel', 'ø': 'close-mid front rounded vowel',
 'ɤ': 'close-mid back unrounded vowel', 'o': 'close-mid back rounded vowel',
 'ə': 'mid central vowel (schwa)',
 'ɚ': 'rhotacized schwa', 'ɝ': 'rhotacized mid central vowel',
 'ɛ': 'open-mid front unrounded vowel', 'œ': 'open-mid front rounded vowel',
 'ʌ': 'open-mid back unrounded vowel', 'ɔ': 'open-mid back rounded vowel',
 'æ': 'near-open front unrounded vowel', 'ɐ': 'near-open central vowel',
 'a': 'open central unrounded vowel', 'ɑ': 'open back unrounded vowel',
 'ɒ': 'open back rounded vowel',
 'r̝': 'raised alveolar trill (Czech ř)',
 't͈ɕ': 'fortis alveolo-palatal affricate',
}
MODS = {
 'ʰ': 'aspirated', 'ʱ': 'breathy-voiced', 'ʲ': 'palatalized',
 'ˤ': 'pharyngealized', 'ʼ': 'ejective', 'ː': 'long',
 '̃': 'nasalized', '̪': 'dental', '͈': 'fortis',
 '͡': '',  # tie bar: cosmetic
}
DIPH = {'aɪ', 'aʊ', 'ɔɪ', 'eɪ', 'oʊ', 'ɔʏ', 'ɛi', 'œy', 'ʌu'}


def name(sym):
    sym = ud.normalize('NFD', sym)
    if sym in DIPH or (len(sym) == 2 and sym[0] in BASE and sym[1] in BASE
                       and sym in DIPH):
        return 'diphthong'
    if ud.normalize('NFC', sym) in DIPH:
        return 'diphthong'
    prefixes, core = [], sym
    changed = True
    while changed and core not in BASE:
        changed = False
        for mod, label in MODS.items():
            if core.endswith(mod):
                if label:
                    prefixes.insert(0, label)
                core = core[:-len(mod)]
                changed = True
            elif mod in core and mod == '̪':   # dental sits mid-symbol (t̪ʰ)
                if label:
                    prefixes.insert(0, label)
                core = core.replace(mod, '', 1)
                changed = True
    if core not in BASE:
        raise KeyError(f'no IPA name for {sym!r} (core {core!r})')
    parts = prefixes + [BASE[core]]
    return ' '.join(parts)


_URL_SPECIAL = {
    'ə': 'Mid_central_vowel', 'ɚ': 'R-colored_vowel', 'ɝ': 'R-colored_vowel',
    'ɴ': 'Uvular_nasal', 'r̝': 'Voiced_dental,_alveolar_and_postalveolar_trills',
    't͈ɕ': 'Voiceless_alveolo-palatal_affricate', 'ʔ': 'Glottal_stop',
}


def url(sym):
    """Wikipedia article for the symbol's core sound."""
    n = ud.normalize('NFD', sym)
    if ud.normalize('NFC', n) in DIPH or n in DIPH:
        return 'https://en.wikipedia.org/wiki/Diphthong'
    nfc = ud.normalize('NFC', sym)
    if nfc in _URL_SPECIAL:
        return 'https://en.wikipedia.org/wiki/' + _URL_SPECIAL[nfc]
    core = n
    changed = True
    while changed and core not in BASE:
        changed = False
        for mod in MODS:
            if core.endswith(mod):
                core = core[:-len(mod)]; changed = True
            elif mod in core and mod == '̪':
                core = core.replace(mod, '', 1); changed = True
    if ud.normalize('NFC', core) in _URL_SPECIAL:
        return 'https://en.wikipedia.org/wiki/' + _URL_SPECIAL[ud.normalize('NFC', core)]
    title = BASE[core].split('(')[0].strip().replace(' ', '_')
    return 'https://en.wikipedia.org/wiki/' + title[0].upper() + title[1:]
