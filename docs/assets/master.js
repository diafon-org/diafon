// The Reference page: the table switch, the example and samples of the picked
// language, and the try-out. Needs DIA (play-data.js) and the engine (engine.js).
(function(){
'use strict';
const $ = id => document.getElementById(id);
const $table = $('mt-table'), $in = $('try-in'), $out = $('try-out'), $tones = $('try-tones'), $orig = $('try-orig'),
      $join = $('try-join');
const secs = [...document.querySelectorAll('section[id^=sec-]')];
const esc = s => s.replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));

// ---- state in the hash: #table=hu (a bare #hu still works)
function hashState(){
  const h = location.hash.slice(1);
  if (h && !h.includes('=')) return {table: h};
  return Object.fromEntries(new URLSearchParams(h));
}
function saveState(){
  const q = new URLSearchParams();
  if ($table.value !== 'universal') q.set('table', $table.value);
  const h = q.toString();
  history.replaceState(null, '', h ? '#' + h : location.pathname);
}

// ---- tables
$table.innerHTML = secs.map(x => `<option value="${x.id.slice(4)}">${esc(x.dataset.name)}</option>`).join('');
function current(){ return document.getElementById('sec-' + $table.value); }
function showTable(){
  for (const x of secs) x.hidden = x !== current();
  showOptions();
}

// ---- the try-out, below the tables: Diafon typed (or Diafon pasted) shown word by word, each word in
// the script with what was typed under it
const OWN_MARKS = /[̦̖̓̔]|[a-z]̣/;     // Diafon's own marks: the text is already script
const articles = [...document.querySelectorAll('.samples .sample')];
// the example, typed in the try-out: the first sentence of the picked language's text, read back from
// the Diafon the page was built with (English for the all-languages table). Text typed over it stays
const firstSentence = el => {
  const t = el.innerHTML.replace(/<br\s*\/?>/g, ' ').replace(/<[^>]+>/g, '');
  const box = document.createElement('div'); box.innerHTML = (t.match(/^.*?[.!?。](?=\s|$)/) || [t])[0];
  return box.textContent.trim();
};
let example = '';
function showSample(){
  const tops = articles.filter(x => x.hasAttribute('data-top'));
  const lang = $table.value === 'universal' ? 'en' : $table.value;
  const a = tops.find(x => x.dataset.lang === lang);
  if ($in.value && $in.value !== example) return;
  example = a ? parse(firstSentence(a.querySelector('.sample-text')).replace(/[.!?。]$/, ''), 'script') : '';   // no full stop
  $in.value = example;
  update();
}
// the sample texts: only the picked language's own (English for the Diafon table, as the site's language);
// a language without texts hides the section
function showSamples(){
  const lang = $table.value === 'universal' ? 'en' : $table.value;
  let any = false;
  for (const a of articles){ a.hidden = a.dataset.lang !== lang; any = any || !a.hidden; }
  $('mt-samples').hidden = !any;
}

// the result in the picked language's usual spelling, where the site has it (pinyin for Mandarin):
// the stage writes it, through the language's lexicon, fetched the first time. A Mandarin tone rides
// above the syllable as the fonts draw it, or, with that off, as pinyin's own mark on the vowel
const PINYIN_MARK = {1: '\u0304', 2: '\u0301', 3: '\u030C', 4: '\u0300'};
function pinyinMarks(text){
  return text.replace(/([A-Za-zÜü]+)([1-5])/g, (_, syl, d) => {
    const low = syl.toLowerCase();
    let i = low.search(/[ae]/);                                  // a or e takes it, then the o of ou,
    if (i < 0) i = low.indexOf('ou');                            //   else the last vowel
    if (i < 0) for (let j = low.length - 1; j >= 0 && i < 0; j--) if ('iouü'.includes(low[j])) i = j;
    if (i < 0 || !PINYIN_MARK[d]) return syl;
    return (syl.slice(0, i + 1) + PINYIN_MARK[d] + syl.slice(i + 1)).normalize('NFC');
  });
}
const stage = () => (DIA.stages || {})[$table.value] || null;
const lexReady = {};
function usual(t, st){
  const p = renderStage(t, st);
  if (st.code !== 'zh') return p;
  return $tones.checked ? p.replace(/\d+/g, toneSigns) : pinyinMarks(p);
}
// the options under the try-out follow the table: usual spelling where the language has one,
// tones where it has them (or all languages are shown)
function showOptions(){
  const st = stage(), L = DIA.langs[$table.value];
  $orig.closest('label').hidden = !st;
  $tones.closest('label').hidden = !(!L || L.tonal);
  if (st && st.lexicon && !lex(st.code) && !lexReady[st.code])
    lexReady[st.code] = fetch(`../lexicon/${st.code}.json`).then(r => r.json()).then(d => setLexicon(st.code, d)).then(update, update);
  update();
}

function update(){
  const typed = OWN_MARKS.test($in.value.normalize('NFD')) ? parse($in.value, 'script') : $in.value;
  let html = '', g = '', t = '';
  const st = $orig.checked ? stage() : null;
  const flush = () => {
    if (g) html += `<span class="w"><span class="wg">${st && !g.includes('class="err"') ? esc(usual(t, st)) : g}</span><code>${esc(t)}</code></span>`;
    g = t = '';
  };
  for (const tok of tokenize(typed)){
    if (tok.t === 'raw'){ flush(); html += esc(tok.ch); continue; }
    const gl = tok.t === 'err' ? null : glyph(tok.form, tok.caps, $join.checked);
    if (gl === null){ g += `<span class="err">${esc(tok.t === 'err' ? tok.ch : tok.form)}</span>`; t += tok.t === 'err' ? tok.ch : tok.form; continue; }
    g += esc(tok.caps ? capFirst(gl) : gl) + toneSigns(tok.tones);
    t += (tok.caps ? tok.form[0].toUpperCase() + tok.form.slice(1) : tok.form) + tok.tones;
  }
  flush();
  $out.innerHTML = html;
}

// the languages overview: a row opens that language's table
document.getElementById('sec-universal').addEventListener('click', e => {
  const tr = e.target.closest('tr[data-goto]');
  if (!tr) return;
  $table.value = tr.dataset.goto;
  showTable(); showSample(); showSamples(); saveState();
  $table.scrollIntoView({block: 'nearest'});
});

// ---- wiring
$in.addEventListener('input', update);
// tones above the syllable (the fonts' calt), on by default; off, the sign follows it (site.js applies it)
try { $tones.checked = localStorage.getItem('diafon-tones') !== 'after'; } catch (e) {}
$tones.addEventListener('change', () => {
  const v = $tones.checked ? 'above' : 'after';
  document.documentElement.dataset.tones = v;
  try { localStorage.setItem('diafon-tones', v); } catch (e) {}
  update();
});
$orig.addEventListener('change', update);
// long consonants joined (t ZWJ t), which the Diafon fonts draw as one; off by default, kept per reader
try { $join.checked = localStorage.getItem('diafon-join') === 'on'; } catch (e) {}
$join.addEventListener('change', () => {
  try { localStorage.setItem('diafon-join', $join.checked ? 'on' : 'off'); } catch (e) {}
  update();
});
$table.addEventListener('change', () => {
  showTable(); showSample(); showSamples(); saveState();
  if ($table.value !== 'universal') try { localStorage.setItem('diafon-lang', $table.value); } catch (e) {}  // shared with Learning
});

function fromHash(){
  const st = hashState();
  let picked = null;
  try { picked = localStorage.getItem('diafon-lang'); } catch (e) {}
  const want = st.table && $('sec-' + st.table) ? st.table : picked;   // a section anchor (#try-it) is no table
  $table.value = want && $('sec-' + want) ? want : 'universal';
}
fromHash();
showTable();
showSample();
showSamples();
})();
