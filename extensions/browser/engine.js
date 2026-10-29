// The Diafon engine in JavaScript, rule for rule from scripts/engine.py and
// scripts/stages.py: tokenize, glyph, render; the stages; and reading back
// (inventory, scriptTable, read, parse, convert, detect). Needs DIA from
// play-data.js (generated). Loaded by the master tables page and bundled by the browser
// extension; tests/test_spec.py holds it to docs/spec.json's vectors.
'use strict';
const CB = new Set('bdfghklmnprstvz'), VB = new Set('aeiou'), OPS = new Set('cjqxwy');
const S = DIA.script, WHOLE = S.whole_letters, MARKS = S.marks,
      DESC = new Set(S.descenders), PARTNER = S.flip_partner;
const BELOWS = Object.values(MARKS).map(m => m.below).filter(Boolean);
const TONES = Object.fromEntries(Object.entries(S.tones).map(([d, t]) => [d, t.sign]));   // digit -> its sign after the syllable
const TONE_OF = Object.fromEntries(Object.entries(TONES).filter(([d, s]) => s).map(([d, s]) => [s, d]));   // and back
const toneSigns = digits => [...digits].map(d => d in TONES ? TONES[d] : d).join('');

function tokenize(text){
  const out = []; let i = 0;
  while (i < text.length){
    const raw = text[i], ch = text[i].toLowerCase();
    if (!CB.has(ch) && !VB.has(ch)){
      out.push({t: (OPS.has(ch) || /\d/.test(ch)) ? 'err' : 'raw', ch: text[i]});
      i++; continue;
    }
    let j = i + 1, ops = '';
    while (j < text.length && OPS.has(text[j].toLowerCase())){ ops += text[j].toLowerCase(); j++; }
    const w = ops.includes('w'), core = ops.replace(/w/g, '');
    let bad = core.length > 2 || (ops.match(/w/g) || []).length > 1 || (w && !ops.endsWith('w'));
    let tones = '';
    while (j < text.length && /\d/.test(text[j])){ tones += text[j]; j++; }
    const form = ch + core + (w ? 'w' : '');
    out.push(bad ? {t: 'err', ch: text.slice(i, j)}
                 : {t: 'form', form, tones, caps: raw !== ch});
    i = j;
  }
  return out;
}

function hasBelow(g){ return BELOWS.some(b => g.includes(b)); }

function mark(g, base, kind, caps){
  const m = MARKS[kind];
  if (m.below && (caps || !DESC.has(base)) && !hasBelow(g)) return g + m.below;
  if (m.above) return g + m.above;
  return g + (m.below || '');
}

function glyph(form, caps){
  const w = form.endsWith('w'), core = w ? form.slice(0, -1) : form;
  const base = core[0];
  const longVowel = w && VB.has(base) && WHOLE[core] === undefined;
  const compose = cap => {
    let g = composeCore(core, cap);
    if (g === null) return null;
    if (longVowel){
      g = g.includes(MARKS.flip.above)
        ? g.replace(MARKS.flip.above, MARKS.double_acute.above)
        : g + MARKS.acute.above;
    }
    return g.normalize('NFC');
  };
  let g = compose(caps);
  if (g === null) return null;
  if (w && !longVowel) g = g + g;         // long consonant doubles its letter
  return g.normalize('NFC');  // one codepoint per visual representation
}

function composeCore(core, caps){
  const base = core[0], ops = core.slice(1);
  if (WHOLE[core] !== undefined) return WHOLE[core];
  if (core.length === 3 && WHOLE[core.slice(0, 2)] !== undefined){
    let g = WHOLE[core.slice(0, 2)];
    const op2 = core[2];
    if (op2 === 'x'){
      if (hasBelow(g)) return null;                      // the dot never stacks
      return mark(g, g[0], 'dot', caps);
    }
    if (op2 === 'y' && g.includes(MARKS.anchor.below))   // y flips the anchored affricate
      return g.replace(MARKS.anchor.below, MARKS.reverse.below);
    return null;
  }
  if (VB.has(base)) return vowel(base, ops);
  return consonant(base, ops, caps);
}

function consonant(base, ops, caps){
  let g = base;
  if (!ops) return g;
  const op1 = ops[0];
  if (op1 === 'y' && 'lrf'.includes(base)) return null;
  if (op1 === 'j') g = mark(g, base, 'anchor', caps);
  else if (op1 === 'x') g = mark(g, base, 'dot', caps);
  else if (op1 === 'y') g = mark(g, base, 'reverse', caps);
  else if (op1 === 'c') g = mark(g, base, 'dot', caps); // the tap rc
  else return null;                                      // bare q-forms are whole letters
  if (ops.length === 1) return g;
  const op2 = ops[1];
  if (op2 === 'x') return null;
  if (op2 === 'y' && op1 === 'j' && 'sz'.includes(base))  // y flips the anchored hush
    return g.replace(MARKS.anchor.below, MARKS.reverse.below);
  return null;
}

function vowel(base, ops){
  let g = base;
  for (const op of ops){
    if (op === 'c') g = PARTNER[base] + MARKS.flip.above;
    else if (op === 'j') g += MARKS.underdot.below;
    else if (op === 'q') g = PARTNER[base] + MARKS.flip.above + MARKS.underdot.below;
    else if (op === 'y') g += MARKS.grave.above;
    else return null;                                    // vowel x only in the glide whole letters
  }
  return g;
}


// ---- rendering with case, and the stages ----

/** Script glyph of a form with orthographic case (Sjw -> Șș), or null. */
function glyphCased(form){
  const caps = form[0] !== form[0].toLowerCase();
  const g = glyph(form[0].toLowerCase() + form.slice(1), caps);
  if (g === null) return null;
  return caps ? (g[0].toUpperCase() + g.slice(1)).normalize('NFC') : g;
}

/** Script form of a text; ill-formed input passes through as typed. */
function render(text){
  let out = '';
  for (const tok of tokenize(text)){
    if (tok.t !== 'form'){ out += tok.ch; continue; }
    const g = glyph(tok.form, tok.caps);
    if (g === null){ out += tok.form + tok.tones; continue; }
    out += (tok.caps ? (g[0].toUpperCase() + g.slice(1)).normalize('NFC') : g) + toneSigns(tok.tones);
  }
  return out;
}

function capFirst(s){ return (s[0].toUpperCase() + s.slice(1)).normalize('NFC'); }

/** Spelling of one form in a stage (base case kept), or null. */
function spell(st, form){
  const caps = form[0] !== form[0].toLowerCase();
  const low = form[0].toLowerCase() + form.slice(1);
  const capmap = st.caps || {};
  let sp = st.forms[low], capsp = capmap[low];
  if (sp === undefined && low.endsWith('w') && CB.has(low[0])){
    const short = st.forms[low.slice(0, -1)];
    if (short !== undefined){
      if (st.long === 'first-letter') sp = short[0] + short;
      else {
        sp = short + short;
        if (capmap[low.slice(0, -1)]) capsp = capmap[low.slice(0, -1)] + short;
      }
    }
  }
  if (sp === undefined) return null;
  if (!caps) return sp;
  return capsp || capFirst(sp);
}

/** A text in a stage's spelling: the lexicon word by word, then the letters. */
function renderStage(text, st){
  if (!st.lexicon || !lex(st.code)) return renderLetters(text, st);
  let out = '', i = 0;
  for (const m of text.matchAll(WORD_T_RE)){
    out += renderLetters(text.slice(i, m.index), st);
    const hit = writeWordLex(m[0], st.code);
    if (hit === null){ const sp = renderLetters(m[0], st); out += writeLoan(m[0], st.code, sp) || sp; }
    else if (Array.isArray(hit)) out += hit[0] + renderLetters(hit[1], st);
    else out += hit;
    i = m.index + m[0].length;
  }
  return out + renderLetters(text.slice(i), st);
}

function renderLetters(text, st){
  let out = '';
  for (const tok of tokenize(text)){
    if (tok.t !== 'form'){ out += tok.ch; continue; }
    const form = (tok.caps ? tok.form[0].toUpperCase() : tok.form[0]) + tok.form.slice(1);
    let sp = spell(st, form);
    if (sp === null) sp = glyphCased(form);
    if (sp === null) sp = form;
    out += sp + tok.tones;
  }
  return out;
}

// ---- the lexicon layer (data/lexicon): word-level tables, loaded by the host ----

const LEXICON = {};                 // code -> the parsed <code>.json; setLexicon() fills it
function setLexicon(code, data){
  data.read = data.read || {}; data.write = data.write || {}; data.choices = data.choices || {};
  data.loans = data.loans || []; data.fold = data.fold || {}; data.match = data.match || 'word'; data.loanwrite = data.loanwrite || {}; data.lengthen = data.lengthen || {};
  data.nativeSet = new Set(data.native || []);
  data.commonSet = new Set(data.common || []);
  data.foreignRe = data.foreign ? new RegExp(data.foreign, 'u') : null;
  data.syllables = data.kind === 'syllable' ? Object.keys(data.read).sort((a, b) => b.length - a.length) : null;
  LEXICON[code] = data;
}
function lex(code){ return LEXICON[code] || null; }
const WORD_RE = /[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*\d*/gu;   // a word of text: letters and marks, an apostrophe inside, tone digits after
const WORD_T_RE = /[A-Za-z]+\d*/g;                          // a word of transport text
function isUpper(ch){ return ch !== ch.toLowerCase() && ch === ch.toUpperCase(); }
function recase(out, original){
  if (!out || !original) return out;
  return isUpper(original[0]) ? (out[0].toUpperCase() + out.slice(1)).normalize('NFC') : out;
}

/** spelling (tone digits after it) -> transport, or null; a syllable lexicon reads runs (nihao, ni3hao3). */
function readWordLex(word, code){
  const L = lex(code);
  if (!L) return null;
  word = word.normalize('NFC');
  if (L.kind === 'syllable' && /\d\D/.test(word)){
    const outs = (word.match(/\D+\d*/g) || []).map(p => readWordLex(p, code));
    return outs.includes(null) ? null : outs.join('');
  }
  let digits = '';
  while (word && /\d/.test(word[word.length - 1])){ digits = word[word.length - 1] + digits; word = word.slice(0, -1); }
  const key = word.toLowerCase();
  let t = L.read[key];
  if (t === undefined && L.syllables && key){
    const out = []; let i = 0;
    while (i < key.length){
      const hit = L.syllables.find(k => key.startsWith(k, i));
      if (hit === undefined) return null;
      out.push(L.read[hit]); i += hit.length;
    }
    t = out.join('');
  }
  return t === undefined ? null : recase(t, word) + digits;
}

/** A word, or with match: prefix a stem, the host's lexicon reads its own way before the
 *  letters (Hungarian spoken: jamaica -> jamaika): [transport, the rest of the spelling]; else null. */
function spokenStem(key, L){
  if (!Object.keys(L.read).length || L.kind === 'syllable') return 0;
  if (L.match !== 'prefix') return key in L.read ? key.length : 0;
  for (let i = Math.min(key.length, 24); i > 2; i--){
    const pre = key.slice(0, i), last = pre[pre.length - 1];
    if (pre in L.read || (last in L.lengthen && (pre.slice(0, -1) + L.lengthen[last]) in L.read)) return i;
  }
  return 0;
}
function readStem(word, code){
  const L = lex(code);
  if (!L) return null;
  const w = word.normalize('NFC'), key = w.toLowerCase();
  const i = spokenStem(key, L);
  if (!i) return null;
  const pre = key.slice(0, i), last = pre[pre.length - 1];
  const t = pre in L.read ? L.read[pre] : L.read[pre.slice(0, -1) + L.lengthen[last]];
  return [recase(t, w), w.slice(i)];
}

/** transport -> spelling: a word, or for a prefix lexicon [stem spelling, rest of transport]; else null. */
function writeWordLex(t, code){
  const L = lex(code);
  if (!L) return null;
  let digits = '';
  while (t && /\d/.test(t[t.length - 1])){ digits = t[t.length - 1] + digits; t = t.slice(0, -1); }   // the tone rides along
  if (!t) return null;
  const key = t[0].toLowerCase() + t.slice(1);
  if (L.match === 'prefix'){
    let best = null;
    for (const stem in L.write) if (key.startsWith(stem) && (best === null || stem.length > best.length)) best = stem;
    return best === null ? null : [recase(L.write[best], t), t.slice(best.length) + digits];
  }
  const sp = L.write[key];
  return sp === undefined ? null : recase(sp, t) + digits;
}

/** A host's word written back as the loan it is, unless the letters' spelling is a host word. */
function writeLoan(t, code, lettersSpelling){
  const L = lex(code);
  if (!L || !Object.keys(L.loanwrite).length || L.nativeSet.has(lettersSpelling.toLowerCase())) return null;
  let digits = '';
  while (t && /\d/.test(t[t.length - 1])){ digits = t[t.length - 1] + digits; t = t.slice(0, -1); }
  const sp = t ? L.loanwrite[t[0].toLowerCase() + t.slice(1)] : undefined;
  return sp === undefined ? null : recase(sp, t) + digits;
}

/** A loan's transport rewritten in the host's sounds: the fold rules over the segment forms, longest first. */
function fold(t, code){
  const L = lex(code), rules = L ? L.fold : {};
  const keys = Object.keys(rules).sort((a, b) => b.length - a.length);
  if (!keys.length) return t;
  const segs = tokenize(t);
  const forms = segs.map(s => s.t === 'form' ? s.form : null);
  const parsed = {}; for (const k of keys) parsed[k] = tokenize(k).map(s => s.form);
  const out = []; let i = 0;
  while (i < segs.length){
    const hit = keys.find(k => parsed[k].every((f, j) => forms[i + j] === f));
    if (hit === undefined){ out.push(segs[i].t === 'form' ? (segs[i].caps ? segs[i].form[0].toUpperCase() + segs[i].form.slice(1) : segs[i].form) + segs[i].tones : segs[i].ch); i++; continue; }
    const n = parsed[hit].length, repl = rules[hit];
    const caps = segs[i].t === 'form' && segs[i].caps;
    const tones = segs.slice(i, i + n).map(s => s.tones || '').join('');
    out.push((caps ? repl[0].toUpperCase() + repl.slice(1) : repl) + tones);
    i += n;
  }
  return out.join('');
}

/** A host's word that is a loan: [transport folded, source code], or null. The longest stem a
 *  loan lexicon reads (among its common words where it has them) against the longest native stem,
 *  native on ties unless the stem has a foreign shape; a suffixed word whose stem has no shape is
 *  never a loan (akinek), with the shape the rest is read by the host's letters (streamingajánló);
 *  a stem whose final vowel the suffix lengthened (lengthen: pizzát) is looked up short too. */
function loan(word, code){
  const L = lex(code);
  if (!L || !L.loans.length) return null;
  const w = word.normalize('NFC'), key = w.toLowerCase();
  const stems = i => { const pre = key.slice(0, i), last = pre[pre.length - 1]; return last in L.lengthen ? [pre, pre.slice(0, -1) + L.lengthen[last]] : [pre]; };
  let nativeLen = 0;
  for (let i = Math.min(key.length, 24); i > 2; i--) if (stems(i).some(p => L.nativeSet.has(p))){ nativeLen = i; break; }
  const spokenLen = spokenStem(key, L);          // the host's own entry, if any: it wins unless a loan stem is longer
  let loanLen = 0, src = null, stem = null;
  outer: for (let i = Math.min(key.length, 24); i > 2; i--)
    for (const lc of L.loans){
      const LL = lex(lc);
      if (!LL) continue;
      stem = stems(i).find(p => p in LL.read && (!LL.commonSet.size || LL.commonSet.has(p)));
      if (stem !== undefined){ loanLen = i; src = lc; break outer; }
    }
  if (src === null || spokenLen >= loanLen) return null;
  const foreign = L.foreignRe ? L.foreignRe.test(key.slice(0, loanLen)) : false;
  if (!foreign && loanLen < key.length) return null;
  if (nativeLen > loanLen || (nativeLen === loanLen && !foreign)) return null;
  const t = recase(lex(src).read[stem], word);
  const rest = w.slice(loanLen);
  return [fold(t, code) + (rest ? readLetters(rest, stageTable(DIA.stages[code])) : ''), src];
}

function choices(key, code = 'zh'){ const L = lex(code); return (L && L.choices[key.toLowerCase()]) || []; }

// ---- reading back ----

/** Every valid single-segment form of the grammar, shorter forms first. */
function inventory(){
  const out = [], core = [...OPS].filter(o => o !== 'w').sort();
  const combos = [''].concat(core, core.flatMap(a => core.map(b => a + b)));
  for (const base of [...CB, ...VB].sort())
    for (const ops of combos)
      for (const w of ['', 'w']){
        const form = base + ops + w;
        if (glyph(form, false) !== null) out.push(form);
      }
  return out;
}

let SCRIPT_TABLE = null;
/** {glyph text: form}, the forms in use (DIA.used) deciding a shared glyph. */
function scriptTable(){
  if (SCRIPT_TABLE) return SCRIPT_TABLE;
  const used = new Set(DIA.used || []), inv = inventory();
  const table = {};
  for (const form of inv.filter(f => used.has(f)).concat(inv.filter(f => !used.has(f))))
    for (const f of [form, form[0].toUpperCase() + form.slice(1)]){
      const g = glyphCased(f);
      if (!(g in table)) table[g] = f;
    }
  SCRIPT_TABLE = table;
  return table;
}

const STAGE_TABLES = {};
/** A stage read back: its spellings, long forms, capitals, read aliases, over the script. */
function stageTable(st, fallback = true, aliases = true){
  const key = st.code + (fallback ? '+' : '-') + (aliases ? 'a' : '');
  if (STAGE_TABLES[key]) return STAGE_TABLES[key];
  const t = fallback ? Object.assign({}, scriptTable()) : {};
  const entries = [];
  for (const form of Object.keys(st.forms)){ entries.push(form); if (CB.has(form[0])) entries.push(form + 'w'); }
  for (const form of entries){
    const sp = spell(st, form), cap = spell(st, form[0].toUpperCase() + form.slice(1));
    if (sp){
      t[sp] = form;
      if (cap) t[cap] = form[0].toUpperCase() + form.slice(1);
      const up = sp.toUpperCase();
      if (up !== sp && up !== cap) t[up] = form[0].toUpperCase() + form.slice(1);
    }
  }
  for (const [sp, form] of Object.entries(aliases ? (st.read || {}) : {})){
    t[sp] = form;
    t[sp[0].toUpperCase() + sp.slice(1)] = form[0].toUpperCase() + form.slice(1);
    t[sp.toUpperCase()] = form[0].toUpperCase() + form.slice(1);
  }
  STAGE_TABLES[key] = t;
  return t;
}

/** Longest match over a table; -> [{t:'form', form, tones, src} | {t:'raw', ch}]. */
const MAXLEN = new WeakMap();
function read(text, table){
  text = text.normalize('NFC');
  let maxlen = MAXLEN.get(table);
  if (maxlen === undefined){
    const keys = Object.keys(table);
    maxlen = keys.length ? Math.max(...keys.map(k => k.length)) : 1;
    MAXLEN.set(table, maxlen);
  }
  const out = []; let i = 0;
  while (i < text.length){
    let hit = null;
    for (let L = Math.min(maxlen, text.length - i); L > 0; L--){
      const s = text.slice(i, i + L);
      if (s in table){ hit = [s, table[s]]; break; }
    }
    if (hit === null){ out.push({t: 'raw', ch: text[i]}); i++; continue; }
    i += hit[0].length;
    let tones = '';
    while (i < text.length && (/[0-9]/.test(text[i]) || text[i] in TONE_OF)){ tones += TONE_OF[text[i]] || text[i]; i++; }   // digits, or the script's tone signs
    out.push({t: 'form', form: hit[1], tones, src: hit[0]});
  }
  return out;
}

function sources(){ return ['transport', 'script'].concat(Object.keys(DIA.stages || {}).sort().map(c => 'stage:' + c)); }

function sourceTable(source){
  if (source === 'script') return scriptTable();
  if (source.startsWith('stage:')) return stageTable(DIA.stages[source.slice(6)]);
  throw new Error('no such source: ' + source);
}

function readLetters(text, table){ return read(text, table).map(tok => tok.t === 'raw' ? tok.ch : tok.form + tok.tones).join(''); }

/** The word by the stage's own spellings alone, or null when a letter is left over. */
function ownRead(word, st){
  const toks = read(word, stageTable(st, false, false));
  if (toks.some(t => t.t === 'raw' && !/\d/.test(t.ch))) return null;
  return toks.map(t => t.t === 'raw' ? t.ch : t.form + t.tones).join('');
}

/** One word of a stage's text -> [transport, how]. */
function stageReadWord(word, st){
  const L = st.lexicon ? lex(st.code) : null;
  if (!st.lexical){
    if (L){                                       // a host with a lexicon: the loan check (which yields to a spoken stem at least as long), then its own entries
      const h = loan(word, st.code); if (h) return [h[0], 'loan:' + h[1]];
      const s = readStem(word, st.code); if (s) return [s[0] + readLetters(s[1], stageTable(st)), 'lexicon'];
    }
    const t = ownRead(word, st);
    if (t !== null) return [t, 'letters'];
  }
  if (L){
    const h = loan(word, st.code);
    if (h) return [h[0], 'loan:' + h[1]];
    const t = readWordLex(word, st.code);
    if (t !== null) return [t, 'lexicon'];
  }
  return [readLetters(word, stageTable(st)), 'fallback'];
}

/** A text in a source read back as transport text. */
function parse(text, source){
  if (source === 'transport') return text;
  if (source === 'script') return readLetters(text, scriptTable());
  const st = DIA.stages[source.slice(6)];
  text = text.normalize('NFC');
  let out = '', i = 0;
  for (const m of text.matchAll(WORD_RE)){
    out += readLetters(text.slice(i, m.index), stageTable(st));
    out += stageReadWord(m[0], st)[0];
    i = m.index + m[0].length;
  }
  return out + readLetters(text.slice(i), stageTable(st));
}

/** A text from one source rendered in another; back into the same spelling, a
 *  word read as a loan goes out as it came (like stays like). */
function convert(text, source, target){
  if (source === target && source.startsWith('stage:')){
    const st = DIA.stages[source.slice(6)];
    text = text.normalize('NFC');
    let out = '', i = 0;
    for (const m of text.matchAll(WORD_RE)){
      out += renderStage(readLetters(text.slice(i, m.index), stageTable(st)), st);
      const [t, how] = stageReadWord(m[0], st);
      out += how.startsWith('loan:') ? m[0] : renderStage(t, st);
      i = m.index + m[0].length;
    }
    return out + renderStage(readLetters(text.slice(i), stageTable(st)), st);
  }
  const t = parse(text, source);
  if (target === 'transport') return t;
  if (target === 'script') return render(t);
  if (target.startsWith('stage:')) return renderStage(t, DIA.stages[target.slice(6)]);
  throw new Error('no such target: ' + target);
}

const MARK_CHARS = new Set(Object.values(MARKS).flatMap(m => [m.below, m.above]).filter(Boolean));

/** Which source a text is in: [[source, coverage]] best first. */
function detect(text, prefer = null){
  prefer = typeof prefer === 'string' ? [prefer] : (prefer || []);
  const letters = s => (s.match(/[\p{L}\p{M}]/gu) || []).length;
  const nfc = text.normalize('NFC');
  const total = letters(nfc) || 1;
  const hasMarks = [...nfc].some(ch => MARK_CHARS.has(ch));
  const srcs = sources(), rank = {};
  srcs.forEach((s, i) => rank[s] = i);
  let typed = false;      // the input form read in full, with operators in it: the system's own
  const lexicalFull = {};
  const scored = srcs.map(src => {
    let covered;
    if (src === 'transport'){
      const toks = tokenize(text).filter(t => t.t === 'form');
      covered = toks.reduce((n, t) => n + letters(t.form + t.tones), 0);
      typed = covered === total && toks.some(t => t.form.length > 1);
    }
    else if (src === 'script')
      covered = read(text, scriptTable()).filter(t => t.t === 'form').reduce((n, t) => n + letters(t.src), 0);
    else {
      const st = DIA.stages[src.slice(6)];
      covered = 0;
      const hows = [];
      for (const m of nfc.matchAll(WORD_RE)){
        const [, how] = stageReadWord(m[0], st);
        hows.push([how, m[0]]);
        if (how === 'letters' || how === 'lexicon' || how.startsWith('loan:')) covered += letters(m[0]);
      }
      if (hows.length && hows.every(([h]) => h === 'lexicon') && hows.some(([, w]) => w.length >= 3)){
        const L = lex(st.code);
        if (L && L.kind === 'syllable'){ if (hows.some(([, w]) => /\d$/.test(w))) lexicalFull[src] = 0; }
        else if (hows.length >= 2) lexicalFull[src] = 1;
      }
    }
    return [src, covered / total];
  });
  const tie = src => ((src === 'script' && hasMarks) || (src === 'transport' && typed)) ? 0
                     : src in lexicalFull ? lexicalFull[src]
                     : prefer.includes(src) ? 2 + prefer.indexOf(src)
                     : 2 + prefer.length + (src === 'transport' ? 0 : 1);
  const r6 = x => Math.round(x * 1e6) / 1e6;
  return scored.sort((a, b) => (r6(b[1]) - r6(a[1])) || (tie(a[0]) - tie(b[0])) || (rank[a[0]] - rank[b[0]]));
}

/** The source to convert from: the best-read source that is not the target itself. */
function sourceFor(text, target, prefer = null){
  const ranked = detect(text, prefer), r6 = x => Math.round(x * 1e6) / 1e6, best = r6(ranked[0][1]);
  for (const [src, cov] of ranked) if (src !== target && r6(cov) === best) return src;
  return ranked[0][0];
}

if (typeof module !== 'undefined') module.exports = {tokenize, glyph, glyphCased, render, spell, renderStage, inventory, scriptTable, stageTable, read, parse, convert, detect, sourceFor, sources, setLexicon, lex, readWordLex, writeWordLex, writeLoan, loan, fold, choices, stageReadWord, readStem};
