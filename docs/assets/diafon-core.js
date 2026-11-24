/* Diafon core: the script, the spelling stages and the lexicon layer in the
   browser and in Node, a port of scripts/script.py, scripts/stages.py and
   scripts/lexicon.py. It reads no file: it is handed the alphabet's contract
   (docs/alphabet-spec.json) and, when wanted, the lexicons (data/lexicon/*.json).

     const core = DiafonCore.create(spec);
     core.addLexicon('hu', huJson);            // optional, at any time
     core.read(text)                           // script text -> tokens
     core.write(tokens, {join})                // tokens -> script text
     core.convert(text, source, target, {join})  // 'script' | 'stage:<code>'
     core.detect(text, {prefer})               // [[source, coverage], ...] best first
     core.sources()
     core.lexRead(word, code), core.lexWrite(scriptText, code)

   A token is a point {c: [letter, mark, ...], long, caps, tones, src} or a raw
   character {raw}. core.plain(token) is the form the spec's vectors use ("ʃ",
   {p: "ʃ", caps: true}, {c: [...]}, {raw: " "}); core.token(x) reads it back.
   Every function that takes tokens takes either form.

   A plain <script> defines window.DiafonCore; require() returns the same object. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else if (root) root.DiafonCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : (typeof self !== 'undefined' ? self : this), function () {
  'use strict';

  // ---- Unicode helpers (Python's str methods and re classes, matched) ----
  const nfc = (s) => s.normalize('NFC');
  const nfd = (s) => s.normalize('NFD');
  const RE_MN = /^\p{Mn}$/u;
  // str.isdigit(): the decimal digits and the other digit characters (superscripts, circled digits)
  const DIGIT = '\\p{Nd}\\u{B2}-\\u{B3}\\u{B9}\\u{1369}-\\u{1371}\\u{19DA}\\u{2070}\\u{2074}-\\u{2079}\\u{2080}-\\u{2089}' +
    '\\u{2460}-\\u{2468}\\u{2474}-\\u{247C}\\u{2488}-\\u{2490}\\u{24EA}\\u{24F5}-\\u{24FD}\\u{24FF}\\u{2776}-\\u{277E}' +
    '\\u{2780}-\\u{2788}\\u{278A}-\\u{2792}\\u{10A40}-\\u{10A43}\\u{10E60}-\\u{10E68}\\u{11052}-\\u{1105A}\\u{1F100}-\\u{1F10A}';
  const RE_DIGIT = new RegExp('^[' + DIGIT + ']$', 'u');
  const RE_UPPER = /^\p{Uppercase}$/u;
  const RE_ASCII_ALPHA = /^[A-Za-z]$/;
  const RE_LM = /[\p{L}\p{M}]/gu;
  // a word of text: letters and combining marks (U+0300-036F), an apostrophe inside, tone digits after.
  // Python's [^\W\d_] is the letters and the numbers that are not decimal digits (L, Nl, No).
  const LETTER = '(?:[\\p{L}\\p{Nl}\\p{No}]|[\\u0300-\\u036f])';
  const WORD_SRC = LETTER + "+(?:['’]" + LETTER + '+)*\\p{Nd}*';
  const RE_DIGIT_NONDIGIT = /\p{Nd}\P{Nd}/u;
  const RE_SYLLABLES = /\P{Nd}+\p{Nd}*/gu;
  const RE_ELIDED = /['’]d$/u;

  const own = (o, k) => (o != null && Object.prototype.hasOwnProperty.call(o, k) ? o[k] : undefined);
  const chAt = (s, i) => (i < s.length ? String.fromCodePoint(s.codePointAt(i)) : undefined);   // the character at a unit index
  const isMark = (ch) => ch !== undefined && RE_MN.test(ch);
  const isDigit = (ch) => ch !== undefined && RE_DIGIT.test(ch);
  const lastCh = (s) => {
    if (!s) return undefined;
    const c = s.charCodeAt(s.length - 1);
    return c >= 0xdc00 && c <= 0xdfff && s.length > 1 ? s.slice(-2) : s.slice(-1);
  };
  const upFirst = (s) => { if (!s) return s; const f = chAt(s, 0); return f.toUpperCase() + s.slice(f.length); };
  const lowFirst = (s) => { if (!s) return s; const f = chAt(s, 0); return f.toLowerCase() + s.slice(f.length); };
  const letters = (s) => { const m = s.match(RE_LM); return m ? m.length : 0; };
  const round6 = (x) => Math.round(x * 1e6) / 1e6;
  const isRaw = (t) => t.raw !== undefined && t.raw !== null;

  function create(spec) {
    if (!spec || !spec.script || !spec.compositions) throw new Error('DiafonCore.create: the parsed alphabet-spec.json is needed');

    // ================= the script (scripts/script.py) =================
    const S = spec.script;
    const CONSONANTS = new Set(S.letters.consonants);
    const VOWELS = new Set(S.letters.vowels);
    const DESC = new Set(S.descenders);
    const MARKS = S.marks;
    const ZWJ = S.joiner || '‍';
    const LONG = S.long || 'ː';
    const TONES = new Map();                 // tone number -> its sign
    const TONE_OF = new Map();               // and back (the unmarked reads as none)
    for (const t of Object.values(S.tones)) TONES.set(String(t.number), t.sign);
    for (const [n, sign] of TONES) if (sign) TONE_OF.set(sign, n);

    const ckey = (comp) => comp.join(' ');
    const COMPS = [];                        // every composition the script allows: [letter, mark, ...]
    const COMP = new Map();                  // key -> the one array of a composition
    const NAME = new Map();                  // composition key -> point name
    const POINTS = new Map();                // point name -> composition
    const intern = (arr) => {
      const k = arr.join(' ');
      let c = COMP.get(k);
      if (!c) { c = Object.freeze(arr.slice()); COMP.set(k, c); }
      return c;
    };
    for (const p of spec.points || []) {
      if (p.long) continue;
      const c = intern([p.letter].concat(p.marks || []));
      POINTS.set(p.id, c);
      NAME.set(ckey(c), p.id);
    }
    for (const e of spec.compositions) {
      const c = intern([e.letter].concat(e.marks || []));
      COMPS.push(c);
      if (e.id != null && !POINTS.has(e.id)) { POINTS.set(e.id, c); NAME.set(ckey(c), e.id); }
    }

    const hasMark = (comp, m) => comp.indexOf(m, 1) > 0;

    /* The vowels, and the points that stand with them: the glides on j and w, the vocalic r, the syllabic nasals (m̈ n̈). */
    function vocalic(comp) {
      const letter = comp[0];
      return VOWELS.has(letter) || letter === 'j' || letter === 'w' || ((letter === 'r' || letter === 'm' || letter === 'n') && hasMark(comp, 'flip'));
    }

    /* A point by name -> [composition, long]. */
    function point(name) {
      const long = name.endsWith(LONG);
      const comp = POINTS.get(long ? name.slice(0, -LONG.length) : name);
      if (!comp) throw new Error('no such point: ' + name);
      return [comp, long];
    }

    /* One letter of a composition: the glyph, without a consonant's doubling. */
    function compose(comp, long, caps) {
      const letter = comp[0];
      let g = letter;
      if (VOWELS.has(letter)) {
        if (hasMark(comp, 'flip')) g += MARKS[long ? 'double_acute' : 'flip'].above;
        if (hasMark(comp, 'underdot')) g += MARKS.underdot.below;
        if (long && !hasMark(comp, 'flip')) g += MARKS.acute.above;
      } else {
        for (let k = 1; k < comp.length; k++) {
          if (comp[k] !== 'flip') g += MARKS[comp[k]][DESC.has(letter) && !caps ? 'above' : 'below'];
        }
        if (hasMark(comp, 'flip')) g += MARKS.flip.above;
      }
      g = nfc(g);
      return caps ? nfc(upFirst(g)) : g;
    }

    /* The glyph of a composition (or of a point, by name). */
    function glyph(comp, long, caps, join, allCaps) {
      if (typeof comp === 'string') {
        const p = point(comp);
        comp = p[0];
        long = long || p[1];
      }
      if (long && !VOWELS.has(comp[0])) {
        const first = compose(comp, false, caps);
        // beside another capital both letters are capitals (KUKKA); otherwise the first (Kk)
        return first + (join ? ZWJ : '') + (caps && allCaps ? first : nfc(lowFirst(first)));
      }
      return compose(comp, !!long, !!caps);
    }

    /* The signs of a run of tone numbers (one outside the vocabulary stays a digit). */
    function toneSigns(numbers) {
      let out = '';
      for (const d of numbers || '') out += TONES.has(d) ? TONES.get(d) : d;
      return out;
    }

    /* A token of the spec's vectors (or a token already) -> a token. */
    function token(x) {
      if (typeof x === 'string') { const p = point(x); return { c: p[0], long: p[1], caps: false, tones: '' }; }
      if (isRaw(x)) return x;
      if (x.p != null) {
        const p = point(x.p);
        return { c: p[0], long: p[1], caps: !!x.caps, tones: x.tones || '', src: x.src };
      }
      if (!x.c) throw new Error('not a token: ' + JSON.stringify(x));
      return { c: intern(Array.from(x.c)), long: !!x.long, caps: !!x.caps, tones: x.tones || '', src: x.src };
    }
    const tokens = (xs) => (typeof xs === 'string' ? read(xs) : Array.from(xs, token));

    /* The point's name (ʃ, ʃː), or null for an open composition or a raw character. */
    function name(tok) {
      tok = token(tok);
      if (isRaw(tok)) return null;
      const n = NAME.get(ckey(tok.c));
      return n ? n + (tok.long ? LONG : '') : null;
    }

    /* A token as the spec writes it. */
    function plain(tok) {
      tok = token(tok);
      if (isRaw(tok)) return { raw: tok.raw };
      const n = name(tok);
      if (n && !tok.caps && !tok.tones) return n;
      const d = n ? { p: n } : { c: Array.from(tok.c) };
      if (!n && tok.long) d.long = true;
      if (tok.caps) d.caps = true;
      if (tok.tones) d.tones = tok.tones;
      return d;
    }
    const plains = (toks) => tokens(toks).map(plain);

    function writeToks(toks, join) {
      let out = '';
      const cap = (n) => !!n && !isRaw(n) && n.caps;
      for (let k = 0; k < toks.length; k++) {
        const t = toks[k];
        if (isRaw(t)) { out += t.raw; continue; }
        // a long capital consonant beside another capital: both its letters capitals
        const beside = t.caps && t.long && (cap(toks[k - 1]) || cap(toks[k + 1]));
        out += glyph(t.c, t.long, t.caps, join, beside) + toneSigns(t.tones);
      }
      return out;
    }

    /* tokens -> script text. */
    function write(toks, opts) {
      return writeToks(tokens(toks), !!(opts && opts.join));
    }

    let SCRIPT_TABLE = null;
    /* The script read back: glyph -> [[comp, long, caps]] over every composition. */
    function scriptTable() {
      if (!SCRIPT_TABLE) {
        const t = new Map();
        for (const comp of COMPS) {
          for (const long of [false, true]) {
            for (const caps of [false, true]) {
              for (const join of (long && !VOWELS.has(comp[0]) ? [false, true] : [false])) {
                for (const g of [glyph(comp, long, caps, join), glyph(comp, long, caps, join, true)]) {
                  if (!t.has(g)) t.set(g, [[comp, long, caps]]);
                }
              }
            }
          }
        }
        SCRIPT_TABLE = t;
      }
      return SCRIPT_TABLE;
    }

    const MAXLEN = new WeakMap();
    function maxlen(table) {
      let m = MAXLEN.get(table);
      if (m === undefined) {
        m = 0;
        for (const k of table.keys()) if (k.length > m) m = k.length;
        if (!table.size) m = 1;
        MAXLEN.set(table, m);
      }
      return m;
    }

    /* The longest key of a table at text[i:] that takes its marks with it. */
    function match(text, i, table, max) {
      const n = text.length;
      for (let L = Math.min(max, n - i); L > 0; L--) {
        const s = text.substr(i, L);
        if (table.has(s) && !(i + L < n && isMark(chAt(text, i + L)))) return s;
      }
      return null;
    }

    /* The tone numbers at text[i:] (signs, or digits) -> [numbers, next i]. */
    function readTones(text, i) {
      let tones = '';
      const n = text.length;
      while (i < n) {
        const ch = chAt(text, i);
        if (!(isDigit(ch) || TONE_OF.has(ch))) break;
        tones += TONE_OF.has(ch) ? TONE_OF.get(ch) : ch;
        i += ch.length;
      }
      return [tones, i];
    }

    /* A text read through a table -> tokens, longest match first, the tones
       after a spelling on its last point; anything the table does not cover is raw. */
    function readLetters(text, table) {
      text = nfc(text);
      const max = maxlen(table);
      const out = [];
      const n = text.length;
      let i = 0;
      while (i < n) {
        const s = match(text, i, table, max);
        if (s === null) {
          const ch = chAt(text, i);
          out.push({ raw: ch });
          i += ch.length;
          continue;
        }
        const r = readTones(text, i + s.length);
        const entry = table.get(s);
        // one capital letter that is several points (Ę): all of them capitals beside another capital (SIĘ)
        const isUp = (ch) => !!ch && ch !== ch.toLowerCase() && ch === ch.toUpperCase();
        const shout = entry.length > 1 && s === s.toUpperCase() && s === upFirst(s) && s !== s.toLowerCase()
          && (isUp(i > 0 ? text[i - 1] : '') || isUp(r[1] < n ? text[r[1]] : ''));
        for (let k = 0; k < entry.length; k++) {
          const e = entry[k];
          out.push({ c: e[0], long: e[1], caps: e[2] || shout, tones: k === entry.length - 1 ? r[0] : '',
                     src: entry.length === 1 || k === 0 ? s : '' });
        }
        i = r[1];
      }
      return out;
    }

    /* script text -> tokens: the points it writes, anything else raw. */
    function read(text) {
      return readLetters(String(text), scriptTable());
    }

    /* A text with its first point capitalized. */
    function capital(text) {
      const toks = read(text);
      for (const t of toks) if (!isRaw(t)) { t.caps = true; break; }
      return writeToks(toks, text.includes(ZWJ));
    }

    /* Whether a text is points throughout (tones allowed). */
    function isScript(text) {
      return !!text && read(text).every((t) => !isRaw(t));
    }

    // ================= the lexicons (scripts/lexicon.py) =================
    const LEX = new Map();

    /* Hand the core a lexicon: the parsed data/lexicon/<code>.json. */
    function addLexicon(code, data) {
      if (!data) { LEX.delete(code); return api; }
      const L = {
        code: code, name: data.name, kind: data.kind, output: data.output === undefined ? true : data.output,
        read: data.read || {}, write: data.write || {}, loans: data.loans || false, choices: data.choices || {},
        match: data.match || 'word', lengthen: data.lengthen || {}, foreign: data.foreign || null,
        native: new Set(data.native || []), sample: data.sample,
        hand: data.hand || {}, hosts: data.hosts || {},
        foreignRe: null, sortedKeys: null,
      };
      L.hasRead = false;
      for (const k in L.read) if (own(L.read, k) !== undefined) { L.hasRead = true; break; }
      LEX.set(code, L);
      return api;
    }
    const lex = (code) => LEX.get(code) || null;
    const hasLexicon = (code) => LEX.has(code);

    /* The lexicons a source or target (or a stage code) makes use of, those loaded or not. */
    function lexiconsFor(source) {
      const code = String(source).startsWith('stage:') ? String(source).slice(6) : String(source);
      const meta = own(spec.lexicons || {}, code);
      if (!meta) return [];
      return meta.loans ? [code, 'loans'] : [code];
    }

    function recase(out, original) {
      if (!out || !original) return out;
      if (original.length > 1 && original === original.toUpperCase() && original !== original.toLowerCase()) {
        const toks = read(out);                              // all in capitals: every point up
        for (const t of toks) if (!isRaw(t)) t.caps = true;
        return writeToks(toks, out.includes(ZWJ));
      }
      return RE_UPPER.test(chAt(original, 0)) ? capital(out) : out;
    }

    function splitTones(word) {
      let digits = '';
      while (word && isDigit(lastCh(word))) {
        const d = lastCh(word);
        digits = d + digits;
        word = word.slice(0, -d.length);
      }
      return [word, digits];
    }

    /* spelling (tone digits allowed after it) -> script text, the tone as its sign, or null. */
    function lexRead(word, code) {
      const L = lex(code);
      if (!L) return null;
      word = nfc(String(word));
      if (L.kind === 'syllable' && RE_DIGIT_NONDIGIT.test(word)) {      // ni3hao3: syllable by syllable
        let out = '';
        for (const p of word.match(RE_SYLLABLES) || []) {
          const o = lexRead(p, code);
          if (o === null) return null;
          out += o;
        }
        return out;
      }
      const st = splitTones(word);
      word = st[0];
      const key = word.toLowerCase();
      let t = own(L.read, key);
      if (t === undefined && RE_ELIDED.test(key)) t = own(L.read, key.slice(0, -2) + 'ed');
      if (t === undefined && L.kind === 'syllable' && key) {
        if (!L.sortedKeys) L.sortedKeys = Object.keys(L.read).sort((a, b) => b.length - a.length);
        let out = '';
        let i = 0;
        while (i < key.length) {
          let hit = null;
          for (const k of L.sortedKeys) if (key.startsWith(k, i)) { hit = k; break; }
          if (hit === null || !hit.length) return null;
          out += L.read[hit];
          i += hit.length;
        }
        t = out;
      }
      return t !== undefined ? recase(t, word) + toneSigns(st[1]) : null;
    }

    /* A word's points -> [its lexicon key, the tone numbers it ends in, whether it began with a capital]. */
    function wordKey(toks) {
      if (!toks.length) return ['', '', false];
      const first = toks[0];
      const last = toks[toks.length - 1];
      const head = isRaw(first) ? { raw: first.raw.toLowerCase() } : { c: first.c, long: first.long, caps: false, tones: '' };
      const up = (t) => (isRaw(t) ? t.raw !== t.raw.toLowerCase() && t.raw === t.raw.toUpperCase() : !!t.caps);
      const shout = toks.length > 1 && toks.every(up);       // all in capitals: the key is all small
      const body = toks.slice(1).map((t) => (isRaw(t) ? { raw: shout ? t.raw.toLowerCase() : t.raw }
        : { c: t.c, long: t.long, caps: t.caps && !shout, tones: '' }));
      return [writeToks([head].concat(body), false), isRaw(last) ? '' : (last.tones || ''), shout ? 'all' : up(first)];
    }
    const cased = (sp, caps) => (!caps || !sp ? sp : caps === 'all' ? nfc(sp.toUpperCase()) : nfc(upFirst(sp)));

    /* A word's points -> spelling: a string (an exact lexicon), [stem spelling,
       the remaining tokens] (a prefix lexicon), or null. */
    function writeWord(toks, code) {
      const L = lex(code);
      if (!L) return null;
      const wk = wordKey(toks);
      const key = wk[0];
      if (!key) return null;
      if (L.match === 'prefix') {
        let best = null;
        for (const stem in L.write) {
          if (own(L.write, stem) === undefined) continue;
          if (key.startsWith(stem) && (best === null || stem.length > best.length) &&
              !(key.length > stem.length && isMark(chAt(key, stem.length)))) best = stem;      // never inside a letter
        }
        if (best === null) return null;
        let rest = read(key.slice(best.length));
        if (wk[2] === 'all') {                               // the key was all small: the rest takes its capitals back
          rest = rest.map((t) => (isRaw(t) ? { raw: t.raw.toUpperCase() } : { c: t.c, long: t.long, caps: true, tones: '' }));
        }
        if (rest.length) {
          rest[rest.length - 1].tones = wk[1];
          return [cased(L.write[best], wk[2]), rest];
        }
        return [cased(L.write[best], wk[2]), Array.from(wk[1], (d) => ({ raw: d }))];
      }
      const sp = own(L.write, key);
      return sp !== undefined ? cased(sp, wk[2]) + wk[1] : null;
    }

    /* script text (or tokens) of one word -> spelling: a string, [stem spelling,
       the rest as script text] for a prefix lexicon (hu), or null. */
    function lexWrite(text, code) {
      const hit = writeWord(tokens(text), code);
      return Array.isArray(hit) ? [hit[0], writeToks(hit[1], false)] : hit;
    }

    /* The length of the longest of the host's own entries that the lowercased word is, or starts with. */
    function spokenStem(key, L) {
      if (!L.hasRead || L.kind === 'syllable') return 0;
      if (L.match !== 'prefix') return own(L.read, key) !== undefined ? key.length : 0;
      for (let i = Math.min(key.length, 24); i > 2; i--) {
        const pre = key.slice(0, i);
        const longer = own(L.lengthen, pre[pre.length - 1]);
        if (own(L.read, pre) !== undefined || (longer !== undefined && own(L.read, pre.slice(0, -1) + longer) !== undefined)) return i;
      }
      return 0;
    }

    /* A word, or with `match: prefix` a stem, the host's lexicon reads its own
       way: [script text, the rest of the spelling], or null. */
    function readStem(word, code) {
      const L = lex(code);
      if (!L) return null;
      const w = nfc(String(word));
      const key = w.toLowerCase();
      const i = spokenStem(key, L);
      if (!i) return null;
      const pre = key.slice(0, i);
      let t = own(L.read, pre);
      if (t === undefined) t = L.read[pre.slice(0, -1) + L.lengthen[pre[pre.length - 1]]];
      return [recase(t, w), w.slice(i)];
    }

    /* A host's word that is a loan: [script text in its own sounds, origin code], or null. */
    function loan(word, code) {
      const L = lex(code);
      const D = lex('loans');
      if (!L || !L.loans || !D) return null;
      const w = nfc(String(word));
      const key = w.toLowerCase();
      const top = Math.min(key.length, 24);
      const stems = (i) => {
        const pre = key.slice(0, i);
        const longer = own(L.lengthen, pre[pre.length - 1]);
        return longer !== undefined ? [pre, pre.slice(0, -1) + longer] : [pre];
      };
      const withRest = (t, n) => {
        let rest = w.slice(n);
        if (rest) rest = writeToks(readLetters(rest, table(loadStage(code), true, true)), false);   // the rest by the host's letters
        return recase(t, word) + rest;
      };
      const host = own(D.hosts, code) || {};
      const ownRead = host.read || {};
      let nativeLen = 0;
      for (let i = top; i > 2 && !nativeLen; i--) if (stems(i).some((p) => L.native.has(p))) nativeLen = i;
      const spokenLen = spokenStem(key, L);              // the host's own entry, if any
      let handLen = 0;
      let hand = null;                                   // a hand loan, the host's spelling of it first
      for (let i = top; i > 2; i--) {
        const p = stems(i).find((q) => own(ownRead, q) !== undefined || own(D.hand, q) !== undefined);
        if (p !== undefined) {
          handLen = i;
          hand = own(ownRead, p) || D.hand[p];
          break;
        }
      }
      let loanLen = 0;
      let src = null;
      let stem;
      for (let i = top; i > 2 && src === null; i--) {
        const cands = stems(i);
        for (const lc in D.read) {
          if (lc === code || own(D.read, lc) === undefined) continue;
          const tbl = D.read[lc];
          stem = cands.find((p) => own(tbl, p) !== undefined);
          if (stem !== undefined) { loanLen = i; src = lc; break; }
        }
      }
      if (src !== null && loanLen > Math.max(spokenLen, handLen)) {
        if (L.foreign && !L.foreignRe) L.foreignRe = new RegExp(L.foreign, 'u');
        const foreign = !!L.foreign && L.foreignRe.test(key.slice(0, loanLen));
        if ((foreign || loanLen === key.length) && !(nativeLen > loanLen || (nativeLen === loanLen && !foreign))) {
          return [withRest(D.read[src][stem], loanLen), src];
        }
      }
      if (hand !== null && handLen > spokenLen) return [withRest(hand[0], handLen), hand[1]];
      return null;
    }

    /* A host's word written back as the loan it is, or null. */
    function writeLoan(toks, code, lettersSpelling) {
      const L = lex(code);
      const D = lex('loans');
      if (!L || !L.loans || !D || lettersSpelling.length < 3) return null;
      if (L.native.has(lettersSpelling.toLowerCase())) return null;
      const wk = wordKey(toks);
      if (!wk[0]) return null;
      const host = own(D.hosts, code) || {};
      const sp = own(host.write || {}, wk[0]) || own(D.write, wk[0]);
      return sp !== undefined && sp !== null ? cased(sp, wk[2]) + wk[1] : null;
    }

    /* The characters of a syllable in script text, its tone sign after it. */
    function choices(syllable, code) {
      const L = lex(code || 'zh');
      const toks = read(syllable);
      for (const t of toks) if (!isRaw(t)) t.caps = false;
      return (L && own(L.choices, writeToks(toks, false))) || [];
    }

    // ================= the stages (scripts/stages.py) =================
    const STAGE_CODES = Object.keys(spec.stages || {});
    const LOADED = new Map();
    const pk = (comp, long) => ckey(comp) + (long ? '|1' : '|0');

    function keyed(d) {
      const m = new Map();
      for (const n of Object.keys(d || {})) {
        const p = point(n);
        m.set(pk(p[0], p[1]), { comp: p[0], long: p[1], v: d[n] });
      }
      return m;
    }
    const at = (m, comp, long) => { const e = m.get(pk(comp, long)); return e === undefined ? undefined : e.v; };

    function loadStage(code) {
      if (typeof code !== 'string') return code;
      let st = LOADED.get(code);
      if (st) return st;
      const d = own(spec.stages || {}, code);
      if (!d) throw new Error('no such stage: ' + code);
      st = {
        code: code, name: d.name, state: d.state, letters: d.letters || [], long: d.long, sample: d.sample || '',
        read: d.read || {}, spell: keyed(d.points), caps: keyed(d.caps), before_i: keyed(d.before_i),
        i_softens: !!d.i_softens, before_vowel: keyed(d.before_vowel), pairs: new Map(),
        lexical: !Object.keys(d.points || {}).length, tables: new Map(),
      };
      for (const k of Object.keys(d.pairs || {})) {
        const pair = read(k).map((t) => [t.c, t.long]);
        st.pairs.set(pair.map((p) => pk(p[0], p[1])).join('+'), { pair: pair, v: d.pairs[k] });
      }
      LOADED.set(code, st);
      return st;
    }

    /* Spelling of one point (case kept), or null if the stage has none. */
    function spell(stage, comp, long, caps) {
      let sp = at(stage.spell, comp, long);
      let capsp = at(stage.caps, comp, long);
      if (sp === undefined && long && !vocalic(comp)) {
        const short = at(stage.spell, comp, false);
        if (short !== undefined) {
          if (stage.long === 'first-letter') sp = chAt(short, 0) + short;
          else {
            sp = short + short;
            const c = at(stage.caps, comp, false);
            if (c) capsp = c + short;
          }
        }
      }
      if (sp === undefined || sp === null) return null;
      if (!caps) return sp;
      return capsp || nfc(upFirst(sp));
    }

    const isI = (comp) => comp.length === 1 && comp[0] === 'i';

    /* The spelling of a soft consonant before a vowel (before_i, i_softens), or null. */
    function softSpelling(stage, tok, nxt) {
      if (!nxt || isRaw(nxt) || !vocalic(nxt.c)) return null;
      const plainSp = at(stage.before_i, tok.c, tok.long);
      let sp;
      if (plainSp !== undefined && isI(nxt.c)) sp = plainSp;
      else if (plainSp !== undefined && stage.i_softens) sp = plainSp + 'i';
      else if (stage.before_vowel.has(pk(tok.c, tok.long)) && !isI(nxt.c)) sp = at(stage.before_vowel, tok.c, tok.long) + 'i';
      else return null;
      return tok.caps ? upFirst(sp) : sp;
    }

    /* Points in the stage's letters, a point the stage does not spell in the script; the tone as its number. */
    function renderLetters(toks, stage) {
      let out = '';
      for (let k = 0; k < toks.length; k++) {
        const t = toks[k];
        if (isRaw(t)) { out += t.raw; continue; }
        const nxt = k + 1 < toks.length ? toks[k + 1] : null;
        const pair = nxt && !isRaw(nxt) && stage.pairs.size
          ? stage.pairs.get(pk(t.c, t.long) + '+' + pk(nxt.c, nxt.long)) : undefined;
        if (pair !== undefined) {                          // the pair as one letter; the tones of both after it
          // capitals as the points have them: both in capitals writes the pair in capitals (NNE)
          out += (t.caps && nxt.caps ? pair.v.toUpperCase() : t.caps ? upFirst(pair.v) : pair.v) + (t.tones || '') + (nxt.tones || '');
          k++;
          continue;
        }
        let sp = softSpelling(stage, t, nxt) || spell(stage, t.c, t.long, t.caps);
        if (sp === null) sp = glyph(t.c, t.long, t.caps, false);
        else if (t.caps && [nxt, k ? toks[k - 1] : null].some((n) => n && !isRaw(n) && n.caps)) {
          sp = nfc(sp.toUpperCase());                      // a capital beside a capital: all its letters (SZÉP, not SzÉP)
        }
        out += sp + (t.tones || '');
      }
      return out;
    }

    /* A run of tokens split into words and what lies between: [[is word, tokens]]. */
    function words(toks) {
      const out = [];
      let cur = [];
      const flush = () => { if (cur.length) { out.push([true, cur]); cur = []; } };
      for (const t of toks) {
        if (!isRaw(t) || RE_ASCII_ALPHA.test(t.raw)) {
          cur.push(t);
          if (!isRaw(t) && t.tones) flush();
        } else {
          flush();
          if (out.length && !out[out.length - 1][0]) out[out.length - 1][1].push(t);
          else out.push([false, [t]]);
        }
      }
      flush();
      return out;
    }

    /* Tokens (or script text) in the stage's spelling: the lexicon first, word by word, then the letters. */
    function render(text, code) {
      const stage = loadStage(code);
      const toks = tokens(text);
      if (!lex(stage.code)) return renderLetters(toks, stage);
      let out = '';
      for (const part of words(toks)) {
        const w = part[1];
        if (!part[0]) { out += renderLetters(w, stage); continue; }
        const hit = writeWord(w, stage.code);
        if (hit === null) {
          const sp = renderLetters(w, stage);
          out += writeLoan(w, stage.code, sp) || sp;
        } else if (Array.isArray(hit)) out += hit[0] + renderLetters(hit[1], stage);
        else out += hit;
      }
      return out;
    }

    /* Script text as a table entry: its points, the first one small. */
    function entry(text) {
      const toks = read(text);
      if (!toks.length || toks.some(isRaw)) throw new Error(JSON.stringify(text) + ': not script');
      return toks.map((t, k) => [t.c, t.long, k === 0 ? false : t.caps]);
    }

    /* The spellings before_i, i_softens and before_vowel imply, read back. */
    function softReads(stage) {
      const out = new Map();
      const e = (x) => [x.comp, x.long, false];
      const I = POINTS.get('i') || intern(['i']);
      const iKeys = [{ comp: I, long: false }, { comp: I, long: true }];
      const vowels = [];
      for (const x of stage.spell.values()) if (vocalic(x.comp) && !isI(x.comp)) vowels.push(x);
      for (const soft of stage.before_i.values()) {
        for (const v of iKeys) {
          const sp = at(stage.spell, v.comp, v.long);
          if (sp) out.set(soft.v + sp, [e(soft), e(v)]);
        }
        if (stage.i_softens) for (const v of vowels) out.set(soft.v + 'i' + v.v, [e(soft), e(v)]);
      }
      for (const soft of stage.before_vowel.values()) {
        for (const v of vowels) out.set(soft.v + 'i' + v.v, [e(soft), e(v)]);
      }
      return out;
    }

    /* The stage read back: spelling -> [[comp, long, caps], ...], longest match deciding. */
    function table(stage, fallback, aliases) {
      const k = (fallback ? 'f' : '-') + (aliases ? 'a' : '-');
      let t = stage.tables.get(k);
      if (t) return t;
      t = fallback ? new Map(scriptTable()) : new Map();
      const entries = [];
      for (const x of stage.spell.values()) {
        entries.push([x.comp, x.long]);
        if (!x.long && !vocalic(x.comp)) entries.push([x.comp, true]);
      }
      for (const en of entries) {
        const sp = spell(stage, en[0], en[1], false);
        const cap = spell(stage, en[0], en[1], true);
        if (sp) {
          t.set(sp, [[en[0], en[1], false]]);
          if (cap) t.set(cap, [[en[0], en[1], true]]);
          const up = sp.toUpperCase();
          if (up !== sp && up !== cap) t.set(up, [[en[0], en[1], true]]);
        }
      }
      for (const p of stage.pairs.values()) {
        t.set(p.v, p.pair.map((x) => [x[0], x[1], false]));
        // all in capitals reads every point a capital (NNE is N̈NE, not N̈nE); a capital first, the first
        t.set(nfc(p.v.toUpperCase()), p.pair.map((x) => [x[0], x[1], true]));
        t.set(nfc(upFirst(p.v)), p.pair.map((x, n) => [x[0], x[1], n === 0]));
      }
      if (aliases) {
        const al = softReads(stage);
        for (const s of Object.keys(stage.read)) al.set(s, entry(stage.read[s]));
        for (const [sp, toks] of al) {
          t.set(sp, toks);
          t.set(sp.toUpperCase(), toks.map((x) => [x[0], x[1], true]));   // all in capitals: every point (DZIE)
          t.set(upFirst(sp), [[toks[0][0], toks[0][1], true]].concat(toks.slice(1)));
        }
      }
      stage.tables.set(k, t);
      return t;
    }

    /* The word read by the stage's own spellings alone: its tokens, or null if any letter is left over. */
    function ownLetters(word, stage) {
      const toks = readLetters(word, table(stage, false, false));
      return toks.some((t) => isRaw(t) && !isDigit(t.raw)) ? null : toks;
    }

    /* One word of a stage's text -> [tokens, how] (how: 'loan:<code>', 'lexicon', 'letters', 'fallback'). */
    function readWordIn(word, stage) {
      const L = lex(stage.code);
      let hit;
      if (!stage.lexical) {
        if (L) {
          hit = loan(word, stage.code);
          if (hit !== null) return [read(hit[0]), 'loan:' + hit[1]];
          hit = readStem(word, stage.code);
          if (hit !== null) return [read(hit[0]).concat(readLetters(hit[1], table(stage, true, true))), 'lexicon'];
        }
        if (ownLetters(word, stage) !== null) return [readLetters(word, table(stage, false, true)), 'letters'];
      }
      if (L) {
        hit = loan(word, stage.code);
        if (hit !== null) return [read(hit[0]), 'loan:' + hit[1]];
        const t = lexRead(word, stage.code);
        if (t !== null) return [read(t), 'lexicon'];
      }
      return [readLetters(word, table(stage, true, true)), 'fallback'];
    }

    function readWord(word, code) {
      const r = readWordIn(String(word), loadStage(code));
      return { tokens: r[0], how: r[1] };
    }

    const stageOf = (name, what) => {
      if (typeof name !== 'string' || !name.startsWith('stage:')) throw new Error('no such ' + what + ': ' + name);
      return loadStage(name.slice(6));
    };
    const wordMatches = (text) => text.matchAll(new RegExp(WORD_SRC, 'gu'));

    /* A text in `source` (script | stage:<code>) read into tokens, everything else raw. */
    function parse(text, source) {
      text = String(text);
      if (source === 'script') return read(text);
      const stage = stageOf(source, 'source');
      text = nfc(text);
      const tbl = table(stage, true, true);
      let out = [];
      let i = 0;
      for (const m of wordMatches(text)) {
        out = out.concat(readLetters(text.slice(i, m.index), tbl), readWordIn(m[0], stage)[0]);
        i = m.index + m[0].length;
      }
      return out.concat(readLetters(text.slice(i), tbl));
    }

    /* Tokens in a target (script | stage:<code>). */
    function writeTo(toks, target, opts) {
      if (target === 'script') return write(toks, opts);
      return render(tokens(toks), stageOf(target, 'target'));
    }

    /* A text from one source rendered in another target. Back into the same
       spelling, a word that came in as a loan goes out as it came. */
    function convert(text, source, target, opts) {
      text = String(text);
      if (source === target && typeof source === 'string' && source.startsWith('stage:')) {
        const stage = stageOf(source, 'source');
        text = nfc(text);
        const tbl = table(stage, true, true);
        let out = '';
        let i = 0;
        for (const m of wordMatches(text)) {
          out += render(readLetters(text.slice(i, m.index), tbl), stage);
          const r = readWordIn(m[0], stage);
          out += r[1].startsWith('loan:') ? m[0] : render(r[0], stage);
          i = m.index + m[0].length;
        }
        return out + render(readLetters(text.slice(i), tbl), stage);
      }
      if (target !== 'script') stageOf(target, 'target');
      return writeTo(parse(text, source), target, opts);
    }

    function sources() {
      return ['script'].concat(STAGE_CODES.map((c) => 'stage:' + c));
    }

    /* Which source a text is in: [[source, coverage], ...] best first. */
    function detect(text, opts) {
      text = String(text);
      opts = opts || {};
      const prefer = typeof opts.prefer === 'string' ? [opts.prefer] : Array.from(opts.prefer || []);
      const other = opts.other || [];
      const textC = nfc(text);
      const textD = nfd(text);
      const total = letters(textC) || 1;
      const marks = new Set();
      for (const v of Object.values(MARKS)) for (const side of ['below', 'above']) if (v[side]) marks.add(v[side]);
      let hasMarks = false;
      for (const m of marks) if (textD.includes(m)) { hasMarks = true; break; }
      if (hasMarks) {
        hasMarks = false;
        for (const m of marks) if (textC.includes(m)) { hasMarks = true; break; }
      }
      const scored = other.map((o) => [o[0], o[1]]);
      const first = new Set(other.filter((o) => o[2]).map((o) => o[0]));
      if (hasMarks) first.add('script');
      const front = other.map((o) => o[0]);
      const lexicalFull = new Map();
      const all = sources();
      for (const src of all) {
        let covered = 0;
        if (src === 'script') {
          for (const t of read(text)) if (!isRaw(t)) covered += letters(t.src || '');
        } else {
          const stage = loadStage(src.slice(6));
          const hows = [];
          for (const m of wordMatches(textC)) {
            const how = readWordIn(m[0], stage)[1];
            hows.push([how, m[0]]);
            if (how === 'letters' || how === 'lexicon' || how.startsWith('loan:')) covered += letters(m[0]);
          }
          // the lexicon read every word: a syllable lexicon with a tone digit
          // somewhere is the strongest sign, a word lexicon the next
          if (hows.length && hows.every((h) => h[0] === 'lexicon') && hows.some((h) => h[1].length >= 3)) {
            if (lex(stage.code).kind === 'syllable') {
              if (hows.some((h) => isDigit(lastCh(h[1])))) lexicalFull.set(src, 0);
            } else if (hows.length >= 2) lexicalFull.set(src, 1);
          }
        }
        scored.push([src, covered / total]);
      }
      const rank = new Map();
      front.concat(all).forEach((s, i) => rank.set(s, i));
      const sortKey = (item) => {
        const src = item[0];
        const tie = first.has(src) ? 0
          : lexicalFull.has(src) ? lexicalFull.get(src)
          : prefer.includes(src) ? 2 + prefer.indexOf(src)
          : 2 + prefer.length + (front.includes(src) ? 0 : 1);
        return [-round6(item[1]), tie, rank.get(src)];
      };
      return scored.map((item) => [item, sortKey(item)])
        .sort((a, b) => (a[1][0] - b[1][0]) || (a[1][1] - b[1][1]) || (a[1][2] - b[1][2]))
        .map((x) => x[0]);
    }

    /* The source to convert a text from: the best-read source that is not the target itself. */
    function sourceFor(text, target, opts) {
      const ranked = detect(text, opts);
      const best = round6(ranked[0][1]);
      for (const r of ranked) if (r[0] !== target && round6(r[1]) === best) return r[0];
      return ranked[0][0];
    }

    const api = {
      spec: spec,
      version: spec.version,
      // the script
      read: read, write: write, glyph: glyph, capital: capital, isScript: isScript, toneSigns: toneSigns,
      token: token, tokens: tokens, plain: plain, plains: plains, name: name,
      // the stages
      sources: sources, stages: () => STAGE_CODES.slice(), parse: parse, writeTo: writeTo, render: (t, code) => render(t, code),
      convert: convert, detect: detect, sourceFor: sourceFor, readWord: readWord,
      // the lexicons
      addLexicon: addLexicon, hasLexicon: hasLexicon, lexiconsFor: lexiconsFor,
      lexRead: lexRead, lexWrite: lexWrite, loan: loan, choices: choices,
    };
    return api;
  }

  return { create: create };
});
