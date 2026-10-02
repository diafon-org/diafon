// The page shown in Universal, in place, by the engine (engine.js + data.js,
// the same as the site's). Settings (chrome.storage.sync): on true|false,
// for every page; keepNames true|false, names left as written; langs
// {host: code}, a language picked by hand for a page
// whose language was not recognised. An element's own lang attribute
// overrides the page's for its text (a quote, a name), a language with no
// stage leaving it as written; every frame converts its own document;
// entries {code: {spelling: said}}, the
// reader's own readings (a name as it is said), laid over the lexicon. The page's language: its lang
// attribute when it names a stage, else detected from its text (the
// reader's languages breaking a tie), else the hand-picked one for its host. Every text node keeps its original in a
// map, so turning off restores the page. New content (a mutation) converts
// as it appears.
'use strict';

const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEXTAREA', 'INPUT', 'SELECT', 'OPTION', 'CODE', 'PRE', 'KBD', 'SAMP', 'SVG', 'MATH']);

/** The share of a sample's letters a stage reads with its own spellings,
 *  read aliases included (Czech y, ý, ě are Czech to a reader); a word counts
 *  when every letter of it reads. */
function coverage(sample, st, aliases = true) {
  let total = 0, covered = 0;
  const table = stageTable(st, false, aliases);
  for (const m of sample.matchAll(WORD_RE)) {
    const n = (m[0].match(/[\p{L}\p{M}]/gu) || []).length;
    total += n;
    if (!read(m[0], table).some(t => t.t === 'raw' && !/\d/.test(t.ch))) covered += n;
  }
  return total ? covered / total : 0;
}

const EN_WORDS = new Set(['the', 'and', 'of', 'to', 'that', 'for', 'with', 'are', 'this', 'was', 'you', 'have', 'from', 'not']);
/** English by its function words, the spelling whose letters say nothing (it reads by its lexicon, not loaded yet). */
function englishByWords(sample) {
  const words = sample.toLowerCase().match(/[a-z]+/g) || [];
  return words.length >= 20 && words.filter(w => EN_WORDS.has(w)).length / words.length >= 0.06;
}

/** Which stage a page is in: its lang attribute when it names a stage, else
 *  from a sample of its text (as written, before any conversion): English by
 *  its function words; else the stage that reads it in full, alone; among
 *  several (plain ASCII reads as many), the ones reading it without their
 *  aliases (Czech reads nyár by y = i, Hungarian by its own letters), then
 *  the first of the reader's languages (prefer) among them; else null, and
 *  the reader picks. */
function pageLanguage(doc, sample, prefer = []) {
  const attr = ((doc.documentElement.lang || '').slice(0, 2)).toLowerCase();
  if (DIA.stages[attr]) return attr;
  if (sample === undefined) sample = doc.body ? doc.body.innerText : '';
  sample = sample.slice(0, 4000).normalize('NFC');
  if (!sample.trim()) return null;
  if (DIA.stages.en && englishByWords(sample)) return 'en';
  const scores = Object.keys(DIA.stages).map(c => [c, coverage(sample, DIA.stages[c])]);
  const best = Math.max(...scores.map(([, c]) => c));
  if (best < 0.98) return null;
  let cands = scores.filter(([, c]) => c >= best - 0.01).map(([c]) => c);
  if (cands.length > 1) {
    const own = cands.filter(c => coverage(sample, DIA.stages[c], false) >= best - 0.01);
    if (own.length) cands = own;
  }
  if (cands.length === 1) return cands[0];
  for (const p of prefer) { const c = p.slice(0, 2).toLowerCase(); if (cands.includes(c)) return c; }
  return null;
}

/** A name, to a reader who keeps them: a word with a capital that does not
 *  open a sentence (the first word of the text, or the first after . ! ?,
 *  quotes and brackets skipped). */
function isName(text, m) {
  if (!/^\p{Lu}/u.test(m[0])) return false;
  const before = text.slice(0, m.index).replace(/[\s"'„“”‘’(\[«»]+$/u, '');
  return before !== '' && !/[.!?…]$/.test(before);
}

/** One text, in a language's spelling, read into Universal; the text itself
 *  without a language; with keepNames, the names left as written. */
function convertText(text, lang, keepNames = false) {
  if (!lang) return text;
  const to = t => t ? convert(t, 'stage:' + lang, 'script') : '';
  if (!keepNames) return to(text);
  let out = '', i = 0;
  for (const m of text.matchAll(WORD_RE)) {
    if (!isName(text, m)) continue;
    out += to(text.slice(i, m.index)) + m[0];
    i = m.index + m[0].length;
  }
  return out + to(text.slice(i));
}

/** The reader's own entries for a language ({spelling: how it is said, in the
 *  language's letters}) as a read table, spelling -> transport, read by the
 *  letters alone; a stage without letters takes none. */
function entryTable(entries, st) {
  const out = {};
  if (!st || st.lexical) return out;
  for (const [sp, said] of Object.entries(entries || {})) {
    const key = sp.normalize('NFC').toLowerCase().trim();
    if (key && said && said.trim()) out[key] = readLetters(said.normalize('NFC').trim(), stageTable(st));
  }
  return out;
}

/** The reader's entries laid over a language's lexicon (made on the spot when
 *  the language has none), the earlier ones of the reader lifted first, so a
 *  removed entry goes; they compete with the loan stems like spoken entries. */
const laid = {};                            // code -> the keys laid last time
function layEntries(code, entries) {
  const st = DIA.stages[code];
  if (!st || st.lexical) return;
  const table = entryTable(entries, st);
  if (!lex(code)) {
    if (st.lexicon) return;                                    // its own lexicon is still to come; laid when it arrives
    if (!Object.keys(table).length) return;
    setLexicon(code, {kind: 'word', match: 'prefix', read: {}}); st.lexicon = true; st.own = true;   // a lexicon of the reader's own
  }
  const L = lex(code);
  for (const k of laid[code] || []) if (!(k in table)) delete L.read[k];
  Object.assign(L.read, table);
  laid[code] = Object.keys(table);
}

if (typeof document !== 'undefined') document.documentElement.dataset.diafon = (typeof chrome !== 'undefined' && chrome.storage) ? 'loaded' : 'no-storage';
if (typeof document !== 'undefined' && typeof chrome !== 'undefined' && chrome.storage) {
  const originals = new WeakMap();          // text node -> its text before conversion
  const host = location.hostname;
  let settings = {on: false, keepNames: false, langs: {}, entries: {}};   // entries: {lang: {spelling: said}}
  let detected = null;                      // from the page itself
  let lang = null;                          // detected, else picked for the host
  let pending = null;

  /** A text node's language: null when it is not to be touched (code,
   *  inputs, editors, translate="no"); the nearest ancestor's lang attribute
   *  when it names a stage; '' when it names a language with none (left as
   *  written); undefined for the page's own. */
  function nodeLang(node) {
    let found;
    for (let el = node.parentElement; el; el = el.parentElement) {
      if (SKIP.has(el.tagName.toUpperCase()) || el.isContentEditable || el.getAttribute('translate') === 'no') return null;
      if (found === undefined && el.hasAttribute('lang')) {
        const code = el.getAttribute('lang').slice(0, 2).toLowerCase();
        found = DIA.stages[code] ? code : '';
        if (el === document.documentElement) found = undefined;     // the page's own, detected or picked
      }
    }
    return found;
  }

  /** A language an element asked for besides the page's: its entries laid and its lexicon fetched once. */
  const wanted = new Set();
  function want(code) {
    if (wanted.has(code)) return;
    wanted.add(code);
    layEntries(code, settings.entries[code]);
    if (!lex(code)) ensureLexicon(code).then(loaded => { if (loaded && settings.on) apply(document.documentElement); });
  }

  const seen = [];                          // the original text, sampled for detection

  const written = new WeakMap();           // text node -> the value the walker wrote last, to know its own writes from the page's
  function apply(root) {
    const on = settings.on;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (!node.nodeValue.trim()) continue;
      const own = nodeLang(node);
      if (own === null) continue;
      if (!originals.has(node)) {
        originals.set(node, node.nodeValue);
        if (own === undefined && seen.length < 400) seen.push(node.nodeValue);
      }
      const code = own === undefined ? lang : own;
      if (code && code !== lang) want(code);
      const src = originals.get(node);
      const out = on && code ? convertText(src, code, settings.keepNames) : src;
      if (node.nodeValue !== out) { node.nodeValue = out; written.set(node, out); }
    }
  }

  /** The lexicons a language needs (its own and its loans'), fetched from the
   *  extension once; the page converts letter by letter until they arrive,
   *  then again with the words. */
  const loading = {};
  function ensureLexicon(code) {
    const st = DIA.stages[code];
    if (!st || !st.lexicon || st.own) return Promise.resolve(false);     // own: a lexicon made for the reader's entries, nothing to fetch
    const fetchOne = c => {
      if (lex(c)) return Promise.resolve(true);
      if (!loading[c]) loading[c] = fetch(chrome.runtime.getURL(`lexicon/${c}.json`)).then(r => r.json())
        .then(d => { setLexicon(c, d); layEntries(c, settings.entries[c]); return d; }).catch(() => null);
      return loading[c];
    };
    return fetchOne(code).then(d => Promise.all((d && d.loans || []).map(fetchOne))).then(() => true);
  }

  function run() {
    if (!seen.length) apply(document.documentElement);          // collects the originals (the title too)
    if (detected === null) detected = pageLanguage(document, seen.join(' '), navigator.languages || []);
    lang = detected || settings.langs[host] || null;
    if (lang) layEntries(lang, settings.entries[lang]);
    apply(document.documentElement);
    if (lang && settings.on && !lex(lang)) ensureLexicon(lang).then(loaded => { if (loaded) apply(document.documentElement); });
    document.documentElement.dataset.diafonState = (settings.on ? 'on' : 'off') + '/' + (lang || '-');
    if (window === window.top) { try { chrome.runtime.sendMessage({type: 'page', detected, lang}); } catch (e) { /* no background (a test bundle) */ } }
  }

  /** New content: queued across batches, applied after a pause. While the page
   *  has no language yet, the text that arrives is sampled and detection runs
   *  again (a page filled by script has little text at load). */
  let queued = new Set();
  const observer = new MutationObserver(records => {
    for (const r of records) {
      if (r.type === 'characterData') {                           // the page rewrote a text node: a new original
        const n = r.target;
        if (written.get(n) === n.nodeValue || !n.parentNode) continue;
        originals.set(n, n.nodeValue);
        queued.add(n.parentNode);
        continue;
      }
      for (const n of r.addedNodes) {
        if (n.nodeType === Node.TEXT_NODE) { if (n.parentNode) queued.add(n.parentNode); }
        else if (n.nodeType === Node.ELEMENT_NODE) queued.add(n);
      }
    }
    clearTimeout(pending);
    pending = setTimeout(() => {
      const nodes = queued; queued = new Set();
      if (!lang) {
        for (const n of nodes) apply(n);                          // collects the originals into the sample
        const d = pageLanguage(document, seen.join(' '), navigator.languages || []);
        if (d) { detected = d; run(); }
        return;
      }
      if (!settings.on) return;
      for (const n of nodes) apply(n);
    }, 150);
  });

  chrome.storage.sync.get({on: false, keepNames: false, langs: {}, entries: {}}, s => {
    settings = s;
    // a debugging aid: #diafon=on on a page turns it on without the icon
    const m = /diafon=(on|off)/.exec(location.hash);
    if (m) settings.on = m[1] === 'on';
    try { run(); } catch (e) { console.error('Diafon:', e); document.documentElement.dataset.diafon = 'error: ' + e.message; }
    observer.observe(document.documentElement, {childList: true, characterData: true, subtree: true});
  });
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'sync') return;
    if (changes.on) settings.on = changes.on.newValue;
    if (changes.keepNames) settings.keepNames = !!changes.keepNames.newValue;
    if (changes.langs) settings.langs = changes.langs.newValue || {};
    if (changes.entries) settings.entries = changes.entries.newValue || {};
    run();
  });

  /** The word the reader selected, as written on the page: the selection's
   *  text node keeps its original; the word of the original that converts
   *  to the selected one, else the selection itself. */
  function selectedWord() {
    const sel = window.getSelection();
    const text = (sel && sel.toString() || '').trim();
    const word = (text.match(WORD_RE) || [''])[0];
    if (!word || !sel.anchorNode) return word;
    const node = sel.anchorNode.nodeType === Node.TEXT_NODE ? sel.anchorNode : null;
    const orig = node && originals.get(node);
    if (!orig || orig === node.nodeValue) return word;
    for (const m of orig.matchAll(WORD_RE)) if (convertText(m[0], lang) === word) return m[0];
    return word;
  }

  chrome.runtime.onMessage.addListener((msg, sender, reply) => {
    if (!msg) return;
    if (msg.type === 'status' && window === window.top) reply({detected, lang, host, on: settings.on, title: document.title});
    if (msg.type === 'say') {                                    // the icon's menu: read this word as…
      const st = lang && DIA.stages[lang];
      if (!st) { alert('Diafon: no language recognised on this page; pick one from the icon first.'); return; }
      if (st.lexical) { alert(`Diafon: ${st.name} reads by its dictionary, not by letters; no entry can be made for it.`); return; }
      const word = selectedWord();
      if (!word) return;
      const key = word.normalize('NFC').toLowerCase();
      const have = (settings.entries[lang] || {})[key] || '';
      const said = prompt(`Diafon: how is “${word}” said? Write it in ${st.name.replace(' spelling', '')} letters.`, have || word);
      if (said === null) return;
      chrome.storage.sync.get({entries: {}}, s => {
        const entries = s.entries;
        entries[lang] = entries[lang] || {};
        if (said.trim()) entries[lang][key] = said.trim(); else delete entries[lang][key];
        chrome.storage.sync.set({entries});
      });
    }
  });
}

if (typeof module !== 'undefined') module.exports = {convertText, isName, pageLanguage, coverage, entryTable, layEntries, SKIP};
