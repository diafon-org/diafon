// The Font page: the font try-out, the converter, the dictionaries and the
// loanword registry. Needs DiafonCore (diafon-core.js); the alphabet's spec
// and the dictionaries are fetched when first needed.
(function(){
'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const base = new URL('..', document.currentScript.src).href;       // the site's root, from assets/font.js
const store = {
  get(k){ try { return localStorage.getItem('diafon-font-' + k); } catch (e) { return null; } },
  set(k, v){ try { localStorage.setItem('diafon-font-' + k, v); } catch (e) {} }
};
const json = url => fetch(url).then(r => { if (!r.ok) throw new Error(url + ': ' + r.status); return r.json(); });

// ---- try a font
const $tfFont = $('tf-font'), $tfSize = $('tf-size'), $tfText = $('tf-text');
function tryFont(){
  $tfText.style.fontFamily = `"${$tfFont.value}", serif`;
  $tfText.style.fontSize = $tfSize.value + 'px';
}
$tfFont.addEventListener('change', tryFont);
$tfSize.addEventListener('input', tryFont);
tryFont();

// ---- the converter
const $from = $('cv-from'), $to = $('cv-to'), $in = $('cv-in'), $out = $('cv-out'), $note = $('cv-note');
let spec = null, core = null;
const loaded = {}, loading = {};

const lexiconsFor = side => side.startsWith('stage:') ? core.lexiconsFor(side) : [];   // a spelling's own dictionary, and the loanword registry where it borrows
function load(code){
  if (loaded[code]) return Promise.resolve();
  if (!loading[code]) loading[code] = json(base + 'assets/lexicon/' + code + '.json').then(d => { core.addLexicon(code, d); loaded[code] = true; });
  return loading[code];
}
const label = side => side === 'script' ? 'Diafon' : side === 'auto' ? 'detect' : spec.stages[side.slice(6)].name;

let turn = 0;
function convert(){
  const mine = ++turn, text = $in.value;
  store.set('from', $from.value); store.set('to', $to.value);
  if (!text.trim()){ $out.textContent = ''; $note.textContent = ''; return; }
  let from = $from.value;
  if (from === 'auto'){
    try { from = core.detect(text.slice(0, 4000))[0][0]; } catch (e) { from = 'script'; }      // the best-covered reading
  }
  const need = [...new Set([...lexiconsFor(from), ...lexiconsFor($to.value)])].filter(c => !loaded[c]);
  if (need.length) $note.textContent = 'loading the dictionary…';
  Promise.all(need.map(load)).then(() => {
    if (mine !== turn) return;
    let out;
    try { out = core.convert(text, from, $to.value); }
    catch (e) { $note.textContent = 'This text could not be converted: ' + e.message; return; }
    $out.textContent = out;
    $out.classList.toggle('ug', $to.value === 'script');
    $note.textContent = ($from.value === 'auto' ? 'read as ' + label(from) + ' · ' : '') + text.trim().split(/\s+/).length + ' words';
  }).catch(e => { if (mine === turn) $note.textContent = 'The dictionary did not load: ' + e.message; });
}
let timer = null;
const soon = () => { clearTimeout(timer); timer = setTimeout(convert, 200); };

function sides(){
  const stages = Object.keys(spec.stages).sort((a, b) => spec.stages[a].name.localeCompare(spec.stages[b].name)).map(c => 'stage:' + c);
  const opt = s => `<option value="${s}">${esc(label(s))}</option>`;
  $from.innerHTML = opt('auto') + opt('script') + stages.map(opt).join('');
  $to.innerHTML = opt('script') + stages.map(opt).join('');
  const f = store.get('from'), t = store.get('to');
  const mine = 'stage:' + (navigator.language || '').slice(0, 2).toLowerCase();      // the reader's own language, else English
  $from.value = [f, mine, 'stage:en'].find(v => v && [...$from.options].some(o => o.value === v));
  if (t && [...$to.options].some(o => o.value === t)) $to.value = t;
}

$('cv-swap').addEventListener('click', () => {
  const f = $from.value === 'auto' ? 'script' : $from.value, t = $to.value, out = $out.textContent;
  $from.value = t; $to.value = f;
  if (out) $in.value = out;
  convert();
});
$('cv-copy').addEventListener('click', () => { if (navigator.clipboard) navigator.clipboard.writeText($out.textContent); });
$('cv-show').addEventListener('click', () => {
  if (!$out.textContent) return;
  $tfText.textContent = $out.textContent;
  $tfText.scrollIntoView({block: 'center', behavior: 'smooth'});
});
$from.addEventListener('change', convert);
$to.addEventListener('change', convert);
$in.addEventListener('input', soon);

// ---- the dictionaries
function dictionaries(){
  const rows = Object.entries(spec.lexicons).filter(([c]) => c !== 'loans').map(([c, L]) => {
    const how = L.kind === 'syllable' ? 'every syllable of pinyin, with its tone' : L.match === 'prefix' ? 'word stems, beside the rules' : 'whole words';
    return `<tr><td>${esc(L.name)}</td><td>${how}</td><td class="num">${Math.max(L.sizes.read || 0, L.sizes.write || 0, L.sizes.native || 0).toLocaleString('en')}</td>` +
      `<td><span class="ug">${esc(L.sample || '')}</span></td></tr>`;
  }).join('');
  $('dicts').innerHTML = `<table><thead><tr><th>Language</th><th>What it holds</th><th>Entries</th><th>A sample</th></tr></thead><tbody>${rows}</tbody></table>`;
}

// ---- the loanword registry
const $find = $('lw-find'), $list = $('lw-list'), $lwNote = $('lw-note');
let registry = null;
function loanRows(L){
  const rows = [];
  for (const [w, v] of Object.entries(L.hand || {})) rows.push([w, v[0], v[1], true]);
  for (const [origin, words] of Object.entries(L.read || {}))
    for (const [w, t] of Object.entries(words)) rows.push([w, t, origin, false]);
  return rows;
}
function showLoans(){
  if (!registry) return;
  const q = $find.value.trim().toLowerCase();
  const hits = registry.filter(r => !q ? r[3] : r[0].toLowerCase().startsWith(q) || r[1].toLowerCase().startsWith(q));
  const name = c => (spec.languages[c] && spec.languages[c].name) || c;
  $lwNote.textContent = q ? `${hits.length.toLocaleString('en')} of ${registry.length.toLocaleString('en')} words` :
    `${registry.length.toLocaleString('en')} words; the hand-kept ones are shown, type to search the rest`;
  $list.innerHTML = '<table><thead><tr><th>Word</th><th>Diafon</th><th>From</th></tr></thead><tbody>' +
    hits.slice(0, 200).map(r => `<tr><td>${esc(r[0])}</td><td><span class="ug">${esc(r[1])}</span></td><td>${esc(name(r[2]))}</td></tr>`).join('') +
    '</tbody></table>' + (hits.length > 200 ? `<p class="tryout-help">The first 200 are shown.</p>` : '');
}
function loadLoans(){
  $lwNote.textContent = 'loading the registry…';
  return json(base + 'assets/lexicon/loans.json').then(L => {
    registry = loanRows(L);
    if (core && !loaded.loans){ core.addLexicon('loans', L); loaded.loans = true; }
    $('lw-load').hidden = true;
    showLoans();
  }).catch(e => { $lwNote.textContent = 'The registry did not load: ' + e.message; });
}
$('lw-load').addEventListener('click', loadLoans);
$find.addEventListener('input', () => { if (registry) showLoans(); else loadLoans(); });

// ---- start
json(base + 'alphabet-spec.json').then(s => {
  spec = s;
  core = DiafonCore.create(spec);
  sides();
  dictionaries();
  const kept = store.get('text');
  if (kept) { $in.value = kept; convert(); }
  $in.addEventListener('input', () => store.set('text', $in.value.slice(0, 20000)));
}).catch(e => { $note.textContent = 'The alphabet did not load: ' + e.message; });
})();
