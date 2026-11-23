"""The typing engine: typed text -> points, by a compiled profile.

Engine(compiled) gives, for the profile kind `base-operators` (universal-v1):

  segments(text)    the typed text cut into segments: a base, the operators
                    after it, the length key, tone digits
  points(text)      -> the alphabet's tokens
  typed(tokens)     tokens -> the keys that type them
  render(text)      typed text -> script text
  stream(buffer)    the streaming commit rule -> (committed, pending)
  inventory()       every key sequence the profile types, short and long

strict=True raises ParseError on ill-formed input; strict=False passes it
through as typed, since a person may be typing a language the system does
not describe.
"""
from . import alphabet
from .alphabet import Tok


class ParseError(ValueError):
    pass


class Engine:
    def __init__(self, compiled):
        self.profile = compiled
        seg = compiled['segment']
        assert seg['kind'] == 'base-operators', seg['kind']
        self.bases = set(seg['bases'])
        self.length = seg['length']
        self.ops = set(seg['operators']) | {self.length}
        self.max_ops = seg['max_operators']
        self.keys = {k: ((v['to'][0], tuple(v['to'][1:])), v['long']) for k, v in compiled['keys'].items()}
        self._form = None

    def segments(self, text, strict=True):
        """-> list of segments, each a dict: kind 'form' | 'raw' | 'err', src
        (the typed characters), and for forms: form (base case kept) and tones."""
        out, i, n = [], 0, len(text)
        L = self.length
        while i < n:
            raw, ch = text[i], text[i].lower()
            if ch not in self.bases:
                if ch in self.ops or ch.isdigit():
                    if strict:
                        raise ParseError(f'position {i}: {text[i]!r} cannot start a segment')
                    out.append({'kind': 'err', 'src': text[i]})
                else:
                    out.append({'kind': 'raw', 'src': text[i]})
                i += 1
                continue
            j = i + 1
            ops = ''
            while j < n and text[j].lower() in self.ops:
                ops += text[j].lower()
                j += 1
            long = L in ops
            core = ops.replace(L, '')
            bad = None
            if len(core) > self.max_ops:
                bad = f'{text[i:j]}: more than {self.max_ops} operators'
            elif ops.count(L) > 1 or (long and not ops.endswith(L)):
                bad = f'{text[i:j]}: {L} must come last, once'
            tones = ''
            while j < n and text[j].isdigit():
                tones += text[j]
                j += 1
            if bad:
                if strict:
                    raise ParseError(bad)
                out.append({'kind': 'err', 'src': text[i:j]})
            else:
                out.append({'kind': 'form', 'src': text[i:j],
                            'form': raw + core + (L if long else ''), 'tones': tones})
            i = j
        return out

    def tokenize(self, text):
        return [('raw', s['src']) if s['kind'] == 'raw' else ('form', s['form'], s['tones'])
                for s in self.segments(text)]

    def comp(self, form):
        """A form -> (composition, long, caps); ParseError for one the profile does not type."""
        caps = form[0].isupper()
        form = form[0].lower() + form[1:]
        long = form.endswith(self.length) and len(form) > 1
        core = form[:-1] if long else form
        hit = self.keys.get(core)
        if hit is None:
            raise ParseError(f'{form}: no such form')
        if long and not hit[1]:
            raise ParseError(f'{form}: no long form')
        return hit[0], long, caps

    def points(self, text, strict=True):
        out = []
        for seg in self.segments(text, strict):
            if seg['kind'] != 'form':
                out += [Tok(raw=ch) for ch in seg['src']]
                continue
            try:
                c, long, caps = self.comp(seg['form'])
            except ParseError:
                if strict:
                    raise
                out += [Tok(raw=ch) for ch in seg['src']]
                continue
            out.append(Tok(c, long, caps, seg['tones'], src=seg['src']))
        return out

    def form(self, tok):
        """The keys that type a token (base case kept, tones after), or its raw character."""
        if tok.raw is not None:
            return tok.raw
        if self._form is None:
            self._form = {comp: key for key, (comp, _) in self.keys.items()}
        f = self._form[tok.comp] + (self.length if tok.long else '')
        return (f[0].upper() + f[1:] if tok.caps else f) + tok.tones

    def typed(self, tokens):
        return ''.join(self.form(t) for t in tokens)

    def glyph(self, form, join=False):
        c, long, caps = self.comp(form)
        return alphabet.glyph(c, long, caps, join)

    def render(self, text, strict=True, join=False):
        return alphabet.write(self.points(text, strict), join)

    def inventory(self):
        """Every form the profile types, lowercase, short then long, in key order."""
        out = []
        for key, (_, may_long) in sorted(self.keys.items()):
            out.append(key)
            if may_long:
                out.append(key + self.length)
        return out

    def stream(self, buffer):
        """The streaming commit rule: -> (committed, pending). Everything
        before the last segment is final, and so is a last segment that is
        not a form; a last form may still grow, so it stays pending."""
        segs = self.segments(buffer, strict=False)
        if not segs:
            return '', ''
        if segs[-1]['kind'] == 'form':
            head, tail = segs[:-1], segs[-1]['src']
        else:
            head, tail = segs, ''
        return self.render(''.join(s['src'] for s in head), strict=False), tail


class KeyEngine:
    """The engine for the profile kind `key-table` (minimal-hu-v1): the text
    is cut by longest match over the key table. A doubled consonant key is
    the long point, and an operator after it applies to both; a doubled
    operator, or one with nothing to apply to, is the plain letter; a digit
    after a point is its tone, a doubled digit the plain digit. A segment commits when the next one starts."""

    def __init__(self, compiled):
        self.profile = compiled
        seg = compiled['segment']
        assert seg['kind'] == 'key-table', seg['kind']
        self.ops = set(seg['operators'])
        self.bases = set(seg['bases'])
        self.doubling = set(seg['doubling'])
        self.tones = compiled.get('tones', False)
        self.keys = {k: ((v['to'][0], tuple(v['to'][1:])), v['long']) for k, v in compiled['keys'].items()}

    def segments(self, text):
        """-> [(typed, tokens, is a point)]: a point with the keys that typed
        it (base, doubling, operators, tone digits), or what passes as it is."""
        out, i, n = [], 0, len(text)
        low = text.lower()
        while i < n:
            ch = low[i]
            if ch not in self.bases:                       # an operator with nothing to apply to, a digit, anything else
                out.append((text[i], [Tok(raw=text[i])], False))
                i += 1
                continue
            j = i + 1
            double = ch in self.doubling and j < n and low[j] == ch
            if double:
                j += 1
            key, escaped = ch, None
            while j < n and low[j] in self.ops:
                if j + 1 < n and low[j + 1] == low[j]:     # a doubled operator: the plain letter
                    escaped = text[j]
                    break
                if key + low[j] not in self.keys:
                    break
                key += low[j]
                j += 1
            tones = ''
            while self.tones and not escaped and j < n and text[j].isdigit():
                if j + 1 < n and text[j + 1] == text[j]:   # a doubled digit: the plain digit
                    escaped = text[j]
                    break
                tones += text[j]
                j += 1
            comp, long = self.keys[key]
            out.append((text[i:j], [Tok(comp, long or double, text[i].isupper(), tones, src=text[i:j])], True))
            if escaped:
                out.append((text[j:j + 2], [Tok(raw=escaped)], False))
                j += 2
            i = j
        return out

    def points(self, text, strict=False):
        return [t for _, toks, _ in self.segments(text) for t in toks]

    def render(self, text, strict=False, join=False):
        return alphabet.write(self.points(text), join)

    def inventory(self):
        return sorted(self.keys)

    def stream(self, buffer):
        """-> (committed, pending): a last segment that is a point may still
        grow (a doubling, an operator, a tone), so it stays pending."""
        segs = self.segments(buffer)
        if segs and segs[-1][2]:
            head, tail = segs[:-1], segs[-1][0]
        else:
            head, tail = segs, ''
        return alphabet.write([t for _, toks, _ in head for t in toks]), tail


def make(compiled):
    return KeyEngine(compiled) if compiled['segment']['kind'] == 'key-table' else Engine(compiled)
