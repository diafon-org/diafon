// The Input page: the try-out and the lessons. Needs DIAFON_PROFILE
// (input-data.js), DIAFON_LESSONS (lessons-data.js) and DiafonKeys
// (diafon-keys.js).
(function(){
'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const ug = s => `<span class="ug">${esc(s)}</span>`;
const code = s => `<code>${esc(s)}</code>`;
const keys = DiafonKeys.create(DIAFON_PROFILE);
const render = t => keys.render(t);
const store = {
  get(k){ try { return localStorage.getItem('diafon-input-' + k); } catch (e) { return null; } },
  set(k, v){ try { localStorage.setItem('diafon-input-' + k, v); } catch (e) {} }
};

// ---- the try-out: what is typed, as Diafon
const $in = $('keys-in'), $out = $('keys-out');
if ($in){
  const show = () => { $out.textContent = render($in.value); store.set('try', $in.value); };
  $in.value = store.get('try') || '';
  $in.addEventListener('input', show);
  show();
}

// ---- the lessons
const $lang = $('ln-lang'), $note = $('ln-note'), $steps = $('ln-steps'), $lesson = $('ln-lesson'),
      $prev = $('ln-prev'), $next = $('ln-next');
if (!$lang) return;
const LEARN = DIAFON_LESSONS;
const VOWEL = f => 'aeiou'.includes(f[0]);
const TITLE = {letters: 'The plain letters', 'op:y': 'The key y', 'op:q': 'The key q', two: 'Two keys after a letter',
               seq: 'Two letters for one sound', tones: 'Tones', caps: 'Capitals and plain text'};
const NAME = {letters: 'plain letters', 'op:y': 'y', 'op:q': 'q', two: 'yq · qy', seq: 'two letters', tones: 'tones', caps: 'capitals'};

let L = null, steps = [], at = 0;

function languages(){
  const codes = Object.keys(LEARN).sort((a, b) => LEARN[b].native - LEARN[a].native);
  $lang.innerHTML = codes.map(c => `<option value="${c}">${esc(LEARN[c].name)}</option>`).join('');
  return codes;
}

function build(c){
  L = LEARN[c];
  steps = L.lessons.map(l => l.key);
  if (Object.keys(L.tones).length) steps.push('tones');
  steps.push('caps');
  $note.innerHTML = `<span class="badge ${L.review === 'reviewed' ? 'st-rev' : 'st-non'}">${esc(L.review)}</span>` +
    (L.review === 'reviewed' ? ' Its sounds have been checked against published descriptions.'
      : ' Its sounds have not been reviewed yet and may change.') +
    (L.words ? '' : ` There are no example words for ${esc(L.name)} yet: the lessons show its letters.`);
}

function tiles(forms){
  return '<div class="ln-tiles">' + forms.map(f =>
    `<div class="pt k-${f.k}"><svg class="edge" aria-hidden="true"><rect width="100%" height="100%" rx="8"/></svg>` +
    `<span class="nat">${esc(f.g)}</span><span class="lab">${esc(f.f)}</span>` +
    `<span class="ipa">${f.ipa.map(i => '/' + esc(i) + '/').join(' ')}</span></div>`).join('') + '</div>';
}

function words(ws){
  if (!ws.length) return '';
  return '<h3>Words</h3><div class="ln-words">' + ws.map(w =>
    `<div class="ln-word"><span class="w">${esc(w.w)}${w.x ? ' <span class="x">' + esc(w.x) + '</span>' : ''}</span>` +
    `${code(w.t)}<span class="g ug">${esc(w.g)}</span></div>`).join('') + '</div>';
}

// the drill: a word (or a letter) to type; the answer is its keys
function drill(items){
  if (!items.length) return '';
  return `<h3>Practice</h3><div class="ln-drill"><p class="ln-ask"></p>` +
    `<div class="ln-row"><input type="text" class="ln-in" spellcheck="false" autocomplete="off" autocapitalize="off" placeholder="type it">` +
    `<button type="button" class="ln-check">check</button><button type="button" class="ln-show">show</button></div>` +
    `<p class="ln-said"></p><p class="ln-count"></p></div>`;
}
function wireDrill(items){
  const box = $lesson.querySelector('.ln-drill');
  if (!box) return;
  let i = 0, right = 0;
  const ask = box.querySelector('.ln-ask'), inp = box.querySelector('.ln-in'), said = box.querySelector('.ln-said'),
        count = box.querySelector('.ln-count');
  const answer = it => it.w ? it.t : it.f;
  function show(){
    const it = items[i];
    ask.innerHTML = it.w ? `Type <b class="ln-prompt">${esc(it.w)}</b>${it.x ? ' ' + esc(it.x) : ''}, written ${ug(it.g)}` :
      `Type the letter ${ug(it.g)} <b class="ln-prompt">${esc(it.ipa.map(x => '/' + x + '/').join(' or '))}</b>`;
    inp.value = ''; said.innerHTML = ''; inp.classList.remove('ok', 'no');
    count.textContent = `${i + 1} of ${items.length}` + (right ? ` · ${right} right` : '');
  }
  function check(){
    const it = items[i], got = inp.value.trim();
    if (!got) return;
    if (render(got) === it.g){             // any keys that write the same letters are right
      right++;
      inp.classList.add('ok'); inp.classList.remove('no');
      said.innerHTML = `Right: ${ug(it.g)}. ` + (i + 1 < items.length ? 'Press Enter for the next one.' : 'That was the last one.');
      inp.dataset.done = '1';
    } else {
      inp.classList.add('no');
      said.innerHTML = `That writes ${ug(render(got))}. Try again, or press show.`;
    }
  }
  function next(){ if (i + 1 < items.length){ i++; inp.dataset.done = ''; show(); inp.focus(); } }
  box.querySelector('.ln-check').addEventListener('click', check);
  box.querySelector('.ln-show').addEventListener('click', () => {
    const it = items[i];
    said.innerHTML = `It is ${code(answer(it))}, written ${ug(it.g)}.`;
    inp.dataset.done = '1';
  });
  inp.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    if (inp.dataset.done) next(); else check();
  });
  show();
}

const lessonOf = k => L.lessons.find(l => l.key === k);
const split = l => [l.forms.filter(f => VOWEL(f.f)), l.forms.filter(f => !VOWEL(f.f))];
const groups = (v, c) => (v.length ? '<h3>Vowels</h3>' + tiles(v) : '') + (c.length ? '<h3>Consonants</h3>' + tiles(c) : '');

function body(k){
  const name = esc(L.name);
  if (k === 'letters'){
    const l = lessonOf(k), [v, c] = split(l);
    const odd = l.forms.filter(f => !f.ipa.includes(f.f));
    return [`<p>${l.forms.length} of ${name}'s sounds are one plain letter, typed as it is. The table gives
      ${name}'s own reading of each, and a letter reads the same in every word.</p>` +
      (odd.length ? `<p>Watch ${odd.map(f => code(f.f)).join(', ')}: in Diafon ${odd.length > 1 ? 'they read' : 'it reads'} as shown below.</p>` : '') +
      groups(v, c), l];
  }
  if (k === 'op:y' || k === 'op:q'){
    const o = k.slice(3), l = lessonOf(k), [v, c] = split(l);
    const first = L.lessons.find(x => x.key.startsWith('op:')) === l;
    let t = first ? `<p>${code('y')} and ${code('q')} are the two keys that are not letters of Diafon. Typed after a letter, they change it.</p>` : '';
    t += '<ul>';
    if (o === 'y'){
      if (c.some(f => !'rw'.includes(f.f[0]))) t += `<li>After a consonant ${code('y')} adds the <b>anchor</b>, the comma-like stroke below the letter (above on g and p): the hushed and the soft sounds.</li>`;
      if (c.some(f => 'rw'.includes(f.f[0]))) t += `<li>After r and w it adds the double dot above: ${code('ry')} is ${ug('r̈')}, ${code('wy')} is ${ug('ẅ')}.</li>`;
      if (v.some(f => f.f[0] !== 'a')) t += `<li>After a vowel ${code('y')} adds the <b>double dot</b>: the lip rounding swapped.</li>`;
      if (v.some(f => f.f[0] === 'a')) t += `<li>After a it gives the schwa: ${code('ay')} is ${ug('ạ')}.</li>`;
    } else {
      if (c.length) t += `<li>After a consonant ${code('q')} adds the <b>dot</b> below the letter (above on g and p): a fixed nearby sound.</li>`;
      if (v.length) t += `<li>After a vowel ${code('q')} makes it <b>long</b>, written with the acute.</li>`;
    }
    return [t + '</ul>' + groups(v, c), l];
  }
  if (k === 'two'){
    const l = lessonOf(k), [v, c] = split(l);
    let t = '<p>Some letters take two keys after them, and a few take three.</p><ul>';
    if (c.some(f => f.k === 'y')) t += `<li>After a consonant ${code('yq')} adds the <b>double dot below</b>: ${name}'s own sound, made further back.</li>`;
    if (c.some(f => f.f === 'ryq')) t += `<li>${code('ryq')} is the soft ${ug('r̦')}, since ${code('ry')} is taken by ${ug('r̈')}.</li>`;
    if (v.some(f => /yq$/.test(f.f) && !/qyq$/.test(f.f))) t += `<li>After a vowel ${code('yq')} is the double dot and length together: ${code('oyq')} is ${ug('ő')}.</li>`;
    if (v.some(f => /qy$/.test(f.f) && f.f[0] !== 'a')) t += `<li>After a vowel ${code('qy')} adds the <b>dot below</b>: the more open vowel. With one more ${code('q')} it is long.</li>`;
    if (v.some(f => f.f.startsWith('aqy'))) t += `<li>After a, ${code('qy')} gives the front ${ug('ä')}, and ${code('aqyq')} its long ${ug('a̋')}.</li>`;
    return [t + '</ul>' + groups(v, c), l];
  }
  if (k === 'seq'){
    const l = lessonOf(k);
    const asp = l.forms.filter(f => f.f.endsWith('h')), nas = l.forms.filter(f => f.f.endsWith('mq')),
          dip = l.forms.filter(f => !f.f.endsWith('h') && !f.f.endsWith('mq'));
    let t = '<p>Some sounds are written with two letters in a row, each typed as itself.</p><ul>';
    if (asp.length) t += `<li>Aspiration is the letter followed by h: ${code(asp[0].f)} is ${ug(asp[0].g)}.</li>`;
    if (nas.length) t += `<li>A nasal vowel is the vowel followed by the nasal letter ${ug('ṃ')}, typed ${code('mq')}: ${code(nas[0].f)} is ${ug(nas[0].g)}.</li>`;
    if (dip.length) t += `<li>A diphthong is a vowel followed by a glide: ${code(dip[0].f)} is ${ug(dip[0].g)}.</li>`;
    t += '</ul>';
    if ($lang.value === 'en' && dip.length)
      t += `<p>In Diafon ${ug('now')} is English <i>no</i> and ${ug('awt')} is English <i>out</i>: w is always the glide.</p>`;
    return [t + tiles(l.forms), l];
  }
  if (k === 'tones'){
    const ts = Object.entries(L.tones);
    const ex = L.lessons.flatMap(l => l.words).find(w => /\d$/.test(w.t));
    return [`<p>${name} has ${ts.length} tones. Type each as a digit after its syllable; Diafon writes it as a small sign:
      ${ts.map(([n, t]) => `<b>${n}</b> ${esc(t)}`).join(', ')}.` + (ex ? ` So ${code(ex.t)} is ${ug(ex.g)}.` : '') + '</p>' +
      `<p>A doubled digit is the plain digit: ${code('h22o')} is ${ug(render('h22o'))}.</p>`, null];
  }
  if (k === 'caps'){
    const w = L.lessons.flatMap(l => l.words).find(w => /^[a-z][yq]/.test(w.t));
    const f = L.lessons.flatMap(l => l.forms).find(f => /^[b-df-hj-np-tv-xz][yq]+$/.test(f.f));
    const t = w ? w.t : f ? f.f : '';
    let ex = '';
    if (t){
      const cap = t[0].toUpperCase() + t.slice(1);
      ex = `<p>${code(cap)} is ${ug(render(cap))}.</p>`;
    }
    return [`<p>A capital is the letter typed in upper case; ${code('y')} and ${code('q')} after it work in either case. A long
      consonant capitalises only its first letter. A mark that floats above g or p goes below on the capital.</p>` + ex +
      `<p>To type a plain y or q after a letter, type it twice: ${code('cityy')} is ${ug(render('cityy'))}, ${code('iraqq')} is
      ${ug(render('iraqq'))}. Where there is no letter before it, it is plain already: ${code('you')}, ${code('quick')}.</p>`, null];
  }
  return ['', null];
}

function show(){
  at = Math.max(0, Math.min(at, steps.length - 1));
  const k = steps[at];
  $steps.innerHTML = steps.map((s, i) =>
    `<button type="button" data-i="${i}" class="${i === at ? 'here' : i < at ? 'done' : ''}">` +
    `<span class="n">${i + 1}</span> ${esc(NAME[s])}</button>`).join('');
  let [html, l] = body(k);
  if (l && l.forms.some(f => f.ipa.length > 1))
    html += `<p>A letter shown with two sounds stands for one sound of ${esc(L.name)}, said two ways.</p>`;
  if (at === steps.length - 1)
    html += `<p class="ln-end">That is all of the typing for ${esc(L.name)}. Every sound, with its readings and the spelling
      rules, is in <a href="../reference/?table=${$lang.value}">its table on the Reference page</a>.</p>`;
  const items = l ? (l.drill.length ? l.drill : l.forms) : [];
  $lesson.innerHTML = `<h3 class="ln-title">${at + 1}. ${esc(TITLE[k])}</h3>${html}${l ? words(l.words) : ''}${drill(items)}`;
  wireDrill(items);
  $prev.disabled = at === 0;
  $next.disabled = at === steps.length - 1;
  store.set('lang', $lang.value); try { localStorage.setItem('diafon-lang', $lang.value); } catch (e) {}
  store.set('lesson-' + $lang.value, String(at));
}

function go(i){ at = i; show(); $lesson.scrollIntoView({block: 'start', behavior: 'smooth'}); }
$steps.addEventListener('click', e => { const b = e.target.closest('button[data-i]'); if (b) go(+b.dataset.i); });
$prev.addEventListener('click', () => go(at - 1));
$next.addEventListener('click', () => go(at + 1));
$lang.addEventListener('change', () => { build($lang.value); at = +(store.get('lesson-' + $lang.value) || 0); show(); });

// the language: the last one used, else the one picked on another page, else the browser's, else English
const shared = () => { try { return localStorage.getItem('diafon-lang'); } catch (e) { return null; } };
languages();
const nav = (navigator.language || '').slice(0, 2).toLowerCase();
const start = [store.get('lang'), shared(), nav, 'en'].find(c => c && LEARN[c]);
$lang.value = start;
build(start);
at = +(store.get('lesson-' + start) || 0);
show();
})();
