// The Master tables page: the table switch, the font switch with its gap
// probes, and the try-out. Needs DIA (play-data.js) and the engine (engine.js).
(function(){
'use strict';
const $ = id => document.getElementById(id);
const $table = $('mt-table'), $font = $('mt-font'), $custom = $('mt-custom'), $summary = $('mt-summary'),
      $in = $('try-in'), $out = $('try-out');
const secs = [...document.querySelectorAll('section[id^=sec-]')];
const esc = s => s.replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));

// ---- state in the hash: #table=hu&font=Arial (a bare #hu still works)
function hashState(){
  const h = location.hash.slice(1);
  if (h && !h.includes('=')) return {table: h};
  return Object.fromEntries(new URLSearchParams(h));
}
function saveState(){
  const q = new URLSearchParams();
  if ($table.value !== 'universal') q.set('table', $table.value);
  const fam = family();
  if (fam !== 'Diafon') q.set('font', fam);
  const h = q.toString();
  history.replaceState(null, '', h ? '#' + h : location.pathname);
}

// ---- tables
$table.innerHTML = secs.map(x => `<option value="${x.id.slice(4)}">${esc(x.dataset.name)}</option>`).join('');
function current(){ return document.getElementById('sec-' + $table.value); }
function showTable(){
  for (const x of secs) x.hidden = x !== current();
  probeAll();
}

// ---- fonts: every glyph on the page follows the chosen family
const GENERIC = /^(serif|sans-serif|monospace|system-ui)$/;
function family(){ return $custom.value.trim() || $font.value; }
function cssFamily(f){ return GENERIC.test(f) ? f : JSON.stringify(f); }
const cv = document.createElement('canvas');
cv.width = cv.height = 72;
const cx = cv.getContext('2d', {willReadFrequently: true});
function pixels(text, fam){
  cx.clearRect(0, 0, 72, 72);
  cx.font = '40px ' + fam;
  cx.textBaseline = 'middle';
  cx.fillText(text, 6, 40);
  return cx.getImageData(0, 0, 72, 72).data;
}
function same(a, b){
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}
// fell: another font stepped in for the letter or for its mark alone (the glyph
// draws differently over two different fallbacks); missing: the marked letter
// draws exactly like its bare base
function probe(g, fam){
  const q = cssFamily(fam);
  const fell = !same(pixels(g, q + ', monospace'), pixels(g, q + ', serif'));
  const bare = g.normalize('NFD').replace(/[̀-ͯ]/g, '');
  const missing = bare !== g.normalize('NFD') && same(pixels(g, q + ', serif'), pixels(bare, q + ', serif'));
  return {fell, missing};
}
let probeRun = 0;
function probeAll(){
  const fam = family(), run = ++probeRun;
  const spans = [...current().querySelectorAll('td.g span')];
  const go = () => {
    if (run !== probeRun) return;
    if (!spans.length){ $summary.textContent = ''; return; }
    let miss = 0, fall = 0;
    const cache = {};
    for (const s of spans){
      const g = s.textContent;
      const p = cache[g] || (cache[g] = probe(g, fam));
      s.classList.toggle('miss', p.missing);
      s.classList.toggle('fall', !p.missing && p.fell);
      if (p.missing) miss++; else if (p.fell) fall++;
    }
    $summary.innerHTML = `${spans.length} glyphs` +
      (miss ? ` · <span class="miss">${miss} marks missing</span>` : '') +
      (fall ? ` · <span class="fall">${fall} falling back</span>` : '') +
      (!miss && !fall ? ' · all drawn by this font' : '');
  };
  if (document.fonts && !GENERIC.test(fam)) document.fonts.load('40px ' + cssFamily(fam), 'aș').then(go, go);
  else go();
}
function applyFont(){
  document.documentElement.style.setProperty('--glyph', cssFamily(family()) + ', var(--serif)');
  probeAll();
  saveState();
}

// ---- the try-out, below the tables: Diafon typed (or Diafon pasted) shown word by word, each word in
// the script with what was typed under it
const OWN_MARKS = /[̦̖̓̔]|[a-z]̣/;     // Diafon's own marks: the text is already script
const articles = [...document.querySelectorAll('.samples .sample')];
// the one example at the top: the first sentence of the picked language's text in Diafon, built with the page,
// its usual spelling small under it (Pinyin for Mandarin)
const firstSentence = el => {
  const t = el.innerHTML.replace(/<br\s*\/?>/g, ' ').replace(/<[^>]+>/g, '');
  const box = document.createElement('div'); box.innerHTML = (t.match(/^.*?[.!?。](?=\s|$)/) || [t])[0];
  return box.textContent.trim();
};
function showSample(){
  const tops = articles.filter(x => x.hasAttribute('data-top'));
  const lang = $table.value === 'universal' ? 'en' : $table.value;
  const a = tops.find(x => x.dataset.lang === lang);
  $('mt-sample').innerHTML = a ? `<p class="g">${esc(firstSentence(a.querySelector('.sample-text')))}</p>` +
    `<p class="orig">${esc(firstSentence(a.querySelector('.sample-orig')))}</p>` : '';
}
// the sample texts: only the picked language's own (English for the Diafon table, as the site's language);
// a language without texts hides the section
function showSamples(){
  const lang = $table.value === 'universal' ? 'en' : $table.value;
  let any = false;
  for (const a of articles){ a.hidden = a.dataset.lang !== lang; any = any || !a.hidden; }
  $('mt-samples').hidden = !any;
}

function update(){
  const typed = OWN_MARKS.test($in.value.normalize('NFD')) ? parse($in.value, 'script') : $in.value;
  let html = '', g = '', t = '';
  const flush = () => { if (g) html += `<span class="w"><span class="wg">${g}</span><code>${esc(t)}</code></span>`; g = t = ''; };
  for (const tok of tokenize(typed)){
    if (tok.t === 'raw'){ flush(); html += esc(tok.ch); continue; }
    const gl = tok.t === 'err' ? null : glyph(tok.form, tok.caps);
    if (gl === null){ g += `<span class="err">${esc(tok.t === 'err' ? tok.ch : tok.form)}</span>`; t += tok.t === 'err' ? tok.ch : tok.form; continue; }
    g += esc(tok.caps ? capFirst(gl) : gl) + tok.tones;
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
$table.addEventListener('change', () => {
  showTable(); showSample(); showSamples(); saveState();
  if ($table.value !== 'universal') try { localStorage.setItem('diafon-lang', $table.value); } catch (e) {}  // shared with Learning
});
$font.addEventListener('change', () => { $custom.value = ''; applyFont(); });
$custom.addEventListener('change', applyFont);

function fromHash(){
  const st = hashState();
  let picked = null;
  try { picked = localStorage.getItem('diafon-lang'); } catch (e) {}
  const want = st.table || picked;
  $table.value = want && $('sec-' + want) ? want : 'universal';
  if (st.font){
    if ([...$font.options].some(o => o.value === st.font)) { $font.value = st.font; $custom.value = ''; }
    else $custom.value = st.font;
  }
}
fromHash();
showTable();
showSample();
showSamples();
applyFont();
if (document.fonts && document.fonts.ready) document.fonts.ready.then(probeAll);
})();
