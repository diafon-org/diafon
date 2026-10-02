// The Master tables page: the table switch, the font switch with its gap
// probes, and the try-out. Needs DIA (play-data.js) and the engine (engine.js).
(function(){
'use strict';
const $ = id => document.getElementById(id);
const $table = $('mt-table'), $font = $('mt-font'), $custom = $('mt-custom'), $summary = $('mt-summary'),
      $from = $('try-from'), $in = $('try-in'), $out = $('try-out'), $back = $('try-back'),
      $chips = $('try-chips'), $words = $('try-words'), $wordsWrap = $('try-words-wrap'), $status = $('try-status');
const secs = [...document.querySelectorAll('section[id^=sec-]')];
const esc = s => s.replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));

// ---- state in the hash: #table=hu&font=Arial&from=stage:hu (a bare #hu still works)
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
  if ($from.value !== 'transport') q.set('from', $from.value);
  const h = q.toString();
  history.replaceState(null, '', h ? '#' + h : location.pathname);
}

// ---- tables
$table.innerHTML = secs.map(x => `<option value="${x.id.slice(4)}">${esc(x.dataset.name)}</option>`).join('');
function current(){ return document.getElementById('sec-' + $table.value); }
function showTable(){
  for (const x of secs) x.hidden = x !== current();
  markHits();
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

// ---- the try-out
const stageCodes = Object.keys(DIA.stages).sort((a, b) => DIA.stages[a].name.localeCompare(DIA.stages[b].name));
$from.innerHTML = '<option value="transport">input form</option><option value="script">universal script</option>' +
  stageCodes.map(c => `<option value="stage:${c}">${esc(DIA.stages[c].name)}</option>`).join('');
const SAMPLES = {
  transport: 'sji sejlz si sjejlz', script: 'și sẹlz si șẹlz',
  'stage:hu': 'Sok szép nyár, hosszú alma. Folyó, gally, hely, helyes, lyuk. Meeting, like, house, taxi, team, tagja, Facebook, show, think; ad hoc, de facto. Só, sok.',
  'stage:en': 'The quick brown fox jumps over the lazy dog. Read, lead, live; Shakespeare wrote Hamlet. Diafon reads it.',
  'stage:zh': 'Ni3 hao3, shi4 jie4! Zhong1 guo2, nihao ma.',
  'stage:cs': 'Dobrý den, přátelé. Děkuji, měsíc, tělo.', 'stage:fi': 'Hyvää yötä kaikille.', 'stage:pl': 'Dobra noc, kochani; rzeka, morze.',
  'stage:sw': 'Habari za asubuhi.', 'stage:tr': 'Günaydın, iyi günler.'
};

// the lexicons a spelling needs (its own and its loans'), fetched once from lexicon/
const loading = {};
function ensure(code){
  const st = DIA.stages[code];
  if (!st || !st.lexicon) return Promise.resolve();
  $status.textContent = 'loading the lexicon…';
  const one = c => lex(c) ? Promise.resolve() : (loading[c] = loading[c] || fetch('lexicon/' + c + '.json').then(r => r.json())
    .then(d => { setLexicon(c, d); return Promise.all((d.loans || []).map(one)); }));
  return one(code).then(() => { $status.textContent = ''; },
    () => { $status.textContent = 'the lexicon did not load: serve the site over http'; });
}

let typed = new Set();
function update(){
  const lang = DIA.langs[$table.value] ? $table.value : '', source = $from.value;
  const stage = source.startsWith('stage:') ? DIA.stages[source.slice(6)] : null;
  const text = source === 'transport' ? $in.value : parse($in.value, source);
  let outHtml = '', chipsHtml = '';
  typed = new Set();
  for (const tok of tokenize(text)){
    if (tok.t === 'raw'){ outHtml += esc(tok.ch); continue; }
    if (tok.t === 'err'){
      outHtml += `<span class="err">${esc(tok.ch)}</span>`;
      chipsHtml += `<div class="chip err"><span class="g">${esc(tok.ch)}</span><span class="f">?</span><span class="r">not a segment</span></div>`;
      continue;
    }
    const g = glyph(tok.form, tok.caps);
    if (g === null){
      outHtml += `<span class="err">${esc(tok.form + tok.tones)}</span>`;
      chipsHtml += `<div class="chip err"><span class="g">${esc(tok.form)}</span><span class="f">${esc(tok.form)}</span><span class="r">no such form</span></div>`;
      continue;
    }
    const shown = tok.caps ? capFirst(g) : g;
    outHtml += esc(shown) + tok.tones;
    const core = tok.form.replace(/w$/, '');
    typed.add(core);
    let reading = lang ? DIA.langs[lang].readings[tok.form] : DIA.default[tok.form], absent = false;
    if (reading === undefined){ reading = DIA.default[tok.form]; absent = !!lang; }
    chipsHtml += `<button type="button" class="chip${absent ? ' absent' : ''}" data-form="${esc(core)}">` +
      `<span class="g">${esc(shown)}</span><span class="f">${esc(tok.form + tok.tones)}</span>` +
      `<span class="r">${reading ? '/' + esc(reading) + '/' : '·'}</span></button>`;
  }
  // Mandarin: the characters of each toned syllable, as the input method offers them
  if (stage && stage.code === 'zh' && lex('zh')){
    for (const m of text.matchAll(/[A-Za-z]+\d*/g))
      chipsHtml += choices(m[0]).slice(0, 6).map(c => `<div class="chip"><span class="c">${c}</span><span class="f">${esc(m[0])}</span></div>`).join('');
  }
  $out.innerHTML = outHtml || '<span class="muted">·</span>';
  $chips.innerHTML = chipsHtml;
  $back.hidden = $wordsWrap.hidden = !stage;
  if (stage){
    $back.innerHTML = '<small>written back in ' + esc(stage.name) + '</small>' + esc(convert($in.value, source, source));
    let rows = '';
    for (const m of $in.value.normalize('NFC').matchAll(/[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*\d*/gu)){
      const [tt, how] = stageReadWord(m[0], stage);
      const written = how.startsWith('loan:') ? m[0] : renderStage(tt, stage), cls = how.split(':')[0];
      const diff = written.normalize('NFC') !== m[0].normalize('NFC');
      rows += `<tr class="${diff ? 'diff' : ''}"><td>${esc(m[0])}</td><td><span class="how ${cls}">${how}</span></td>` +
        `<td><code>${esc(tt)}</code></td><td class="g">${esc(render(tt))}</td><td class="back">${esc(written)}</td></tr>`;
    }
    $words.querySelector('tbody').innerHTML = rows;
  }
  markHits();
}
function markHits(){
  for (const tr of current().querySelectorAll('tr[data-form]')) tr.classList.toggle('hit', typed.has(tr.dataset.form));
}
function go(){
  const source = $from.value;
  if (source.startsWith('stage:')) ensure(source.slice(6)).then(update);
  update();
}
$chips.addEventListener('click', e => {
  const chip = e.target.closest('.chip[data-form]');
  const row = chip && current().querySelector(`tr[data-form="${CSS.escape(chip.dataset.form)}"]`);
  if (!row) return;
  row.scrollIntoView({behavior: 'smooth', block: 'center'});
  row.classList.remove('flash'); void row.offsetWidth; row.classList.add('flash');
});

// the languages overview: a row opens that language's table
document.getElementById('sec-languages').addEventListener('click', e => {
  const tr = e.target.closest('tr[data-goto]');
  if (!tr) return;
  $table.value = tr.dataset.goto;
  showTable(); update(); saveState();
  $table.scrollIntoView({block: 'nearest'});
});

// ---- wiring
$in.addEventListener('input', update);
$table.addEventListener('change', () => { showTable(); update(); saveState(); });
$font.addEventListener('change', () => { $custom.value = ''; applyFont(); });
$custom.addEventListener('change', applyFont);
$from.addEventListener('change', () => { $in.value = SAMPLES[$from.value] || $in.value; saveState(); go(); });
$('try-sample').addEventListener('click', () => { $in.value = SAMPLES[$from.value] || ''; go(); });

function fromHash(){
  const st = hashState();
  $table.value = st.table && $('sec-' + st.table) ? st.table : 'universal';
  if (st.font){
    if ([...$font.options].some(o => o.value === st.font)) { $font.value = st.font; $custom.value = ''; }
    else $custom.value = st.font;
  }
  if (st.from && [...$from.options].some(o => o.value === st.from) && st.from !== $from.value){
    $from.value = st.from;
    $in.value = SAMPLES[st.from] || $in.value;
  }
}
fromHash();
showTable();
applyFont();
go();
if (document.fonts && document.fonts.ready) document.fonts.ready.then(probeAll);
})();
