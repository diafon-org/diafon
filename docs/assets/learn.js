// The Learning page: one language's lessons, one at a time, with a drill
// each. Needs LEARN (learn-data.js, scripts/gen_learn.py) and the engine
// (play-data.js, engine.js) for rendering what the learner types.
(function(){
'use strict';
const $ = id => document.getElementById(id);
const $lang = $('ln-lang'), $note = $('ln-note'), $steps = $('ln-steps'), $lesson = $('ln-lesson'),
      $prev = $('ln-prev'), $next = $('ln-next');
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const ug = s => `<span class="ug">${esc(s)}</span>`;
const code = s => `<code>${esc(s)}</code>`;
const store = {
  get(k){ try { return localStorage.getItem('diafon-learn-' + k); } catch (e) { return null; } },
  set(k, v){ try { localStorage.setItem('diafon-learn-' + k, v); } catch (e) {} }
};

// what each operator does, on a consonant and on a vowel, and how it looks
const OPS = {
  j: {c: 'softens it toward the palate, and turns s and z into the hushing sounds',
      cm: 'the <b>anchor</b>, a comma-like stroke attached below the letter (above on g and p)',
      v: 'makes it lax, pulled toward the centre; on a it is the reduced vowel',
      vm: 'a dot below'},
  x: {c: 'shifts the manner: a stop becomes the fricative beside it, and h becomes the glottal stop',
      cm: 'a <b>dot</b> below the letter (above on g and p)',
      v: 'turns i and u into the glides', vm: 'the letters j and w'},
  c: {c: 'makes an affricate, t into ts and d into dz, and on r the tap',
      cm: 'the letters c and x for the affricates, a dot on r',
      v: 'flips the rounding: i rounded, u unrounded, and so on', vm: 'a <b>double dot</b> above'},
  q: {c: 'works as c and j at once: the hushing affricates, like the ch of church; on k it is the uvular q',
      cm: 'c and x with the anchor, and the letter q',
      v: 'flips the rounding and makes it lax; on a it is the vocalic r', vm: 'a double dot above, a dot below'},
  y: {c: 'leans it back: the retroflex sounds, said with the tongue curled back',
      cm: 'the <b>reversed anchor</b>', v: '', vm: ''},
};
const VOWEL = f => 'aeiou'.includes(f[0]);
const TITLE = {letters: 'The plain letters', long: 'Length', special: 'y', seq: 'Two sounds in a row',
               tones: 'Tones', caps: 'Capitals', card: 'Your card'};

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
  steps.push('caps', 'card');
  const words = L.words ? '' : ` No example words for ${esc(L.name)} yet: the lessons show its sounds.`;
  $note.innerHTML = `<span class="badge ${L.review === 'native-reviewed' ? 'st-nat' : L.review === 'reviewed' ? 'st-rev' : 'st-non'}">${esc(L.review)}</span>` +
    (L.review === 'non-reviewed' ? ` This mapping has not been reviewed yet; its readings may change.` : '') + words;
}

function stepTitle(k){ return k.startsWith('op:') ? `The operator ${k.slice(3)}` : TITLE[k]; }

function tiles(forms){
  return '<div class="ln-tiles">' + forms.map(f => {
    const core = f.f.replace(/w$/, ''), last = core.slice(-1);
    const k = core.length > 1 && 'jxcqy'.includes(last) ? last : 'base';     // coloured by its operator
    return `<div class="pt k-${k}">` +
      `<span class="nat">${esc(f.g)}</span><span class="lab">${esc(f.f)}</span>` +
      `<span class="ipa">${f.ipa.map(i => '/' + esc(i) + '/').join(' ')}</span></div>`;
  }).join('') + '</div>';
}

function words(ws){
  if (!ws.length) return '';
  return '<h3>Words</h3><div class="ln-words">' + ws.map(w =>
    `<div class="ln-word"><span class="w">${esc(w.w)}${w.x ? ' <span class="x">' + esc(w.x) + '</span>' : ''}</span>` +
    `${code(w.t)}<span class="g ug">${esc(w.g)}</span></div>`).join('') + '</div>';
}

// the drill: a word (or a sound) to type; the answer is its input form
function drill(items){
  if (!items.length) return '';
  return `<h3>Practice</h3><div class="ln-drill" data-i="0"><p class="ln-ask"></p>` +
    `<div class="ln-row"><input type="text" class="ln-in" spellcheck="false" autocomplete="off" autocapitalize="off" placeholder="type the input form">` +
    `<button type="button" class="ln-check">check</button><button type="button" class="ln-show">show</button></div>` +
    `<p class="ln-said"></p><p class="ln-count"></p></div>`;
}
function wireDrill(items){
  const box = $lesson.querySelector('.ln-drill');
  if (!box) return;
  let i = 0, right = 0;
  const ask = box.querySelector('.ln-ask'), inp = box.querySelector('.ln-in'), said = box.querySelector('.ln-said'),
        count = box.querySelector('.ln-count');
  function show(){
    const it = items[i];
    ask.innerHTML = it.w ? `Type <b class="ln-prompt">${esc(it.w)}</b>${it.x ? ' ' + esc(it.x) : ''}` :
      `Type the sound <b class="ln-prompt">${esc(it.ipa.map(x => '/' + x + '/').join(' or '))}</b>`;
    inp.value = ''; said.innerHTML = ''; inp.classList.remove('ok', 'no');
    count.textContent = `${i + 1} of ${items.length}` + (right ? ` · ${right} right` : '');
  }
  function answer(it){ return it.w ? it.t : it.f; }
  function check(){
    const it = items[i], want = answer(it), got = inp.value.trim().toLowerCase();
    if (!got) return;
    let out;
    try { out = render(got); } catch (e) { out = got; }
    if (got === want){
      right++;
      inp.classList.add('ok'); inp.classList.remove('no');
      said.innerHTML = `Right: ${ug(it.g)}. ` + (i + 1 < items.length ? 'Press Enter for the next one.' : 'That was the last one.');
      inp.dataset.done = '1';
    } else {
      inp.classList.add('no');
      said.innerHTML = `That reads ${ug(out)}. Try again, or press show.`;
    }
  }
  function next(){ if (i + 1 < items.length){ i++; inp.dataset.done = ''; show(); inp.focus(); } }
  box.querySelector('.ln-check').addEventListener('click', check);
  box.querySelector('.ln-show').addEventListener('click', () => {
    const it = items[i];
    said.innerHTML = `It is ${code(answer(it))}, read ${ug(it.g)}.`;
    inp.dataset.done = '1';
  });
  inp.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    if (inp.dataset.done) next(); else check();
  });
  show();
}

function lessonOf(k){ return L.lessons.find(l => l.key === k); }
function allForms(){ return L.lessons.flatMap(l => l.forms.map(f => Object.assign({kind: l.key}, f))); }

function body(k){
  const name = esc(L.name);
  if (k === 'letters'){
    const l = lessonOf(k), v = l.forms.filter(f => VOWEL(f.f)), c = l.forms.filter(f => !VOWEL(f.f));
    const odd = l.forms.filter(f => !f.ipa.includes(f.f));
    return [`<p>${l.forms.length} of ${name}'s sounds are written with one letter, exactly as you type it.
      Read them by this table, not by habit: these are ${name}'s own readings, and they stay the same in every word.</p>` +
      (odd.length ? `<p>Watch ${odd.map(f => code(f.f)).join(', ')}: in ${name} ${odd.length > 1 ? 'they read' : 'it reads'} as shown below.</p>` : '') +
      (v.length ? '<h3>Vowels</h3>' + tiles(v) : '') + (c.length ? '<h3>Consonants</h3>' + tiles(c) : ''), l];
  }
  if (k.startsWith('op:')){
    const o = k.slice(3), l = lessonOf(k), op = OPS[o];
    const c = l.forms.filter(f => !VOWEL(f.f)), v = l.forms.filter(f => VOWEL(f.f));
    let t = `<p><b class="ln-op op-${o}">${o}</b> is an operator: it never stands alone, it changes the letter before it.</p><ul>`;
    if (c.length) t += `<li>On a consonant it ${op.c}. In the script: ${op.cm}.</li>`;
    if (v.length && op.v) t += `<li>On a vowel it ${op.v}. In the script: ${op.vm}.</li>`;
    t += '</ul>';
    const two = l.forms.find(f => f.f.length > 2);
    if (two){
      const first = two.f.slice(0, -1);
      let g1 = first; try { g1 = render(first); } catch (e) {}
      t += `<p>A second operator works on the result of the first: ${code(first)} is ${ug(g1)}, and ${code(two.f)} is ${ug(two.g)}.</p>`;
    }
    return [t + (c.length ? '<h3>Consonants</h3>' + tiles(c) : '') + (v.length ? '<h3>Vowels</h3>' + tiles(v) : ''), l];
  }
  if (k === 'long'){
    const l = lessonOf(k), v = l.forms.filter(f => VOWEL(f.f)), c = l.forms.filter(f => !VOWEL(f.f));
    let t = `<p><code>w</code> after a sound makes it long. It comes last, after any operator, and it is free: it never counts as one of the two.</p><ul>`;
    if (v.length) t += `<li>A long vowel takes an acute: ${code(v[0].f)} is ${ug(v[0].g)}.</li>`;
    t += `<li>A long consonant doubles its letter in the script: ${code('sw')} is ${ug('ss')}.</li></ul>`;
    return [t + tiles(l.forms), l];
  }
  if (k === 'special'){
    const l = lessonOf(k);
    return [`<p>${code('y')} marks ${name}'s own variant of a sound, close to its plain letter. On a consonant it is
      drawn as the reverse anchor; on a vowel as a grave, which is nasal. For ${name} they read as below.</p>` + tiles(l.forms), l];
  }
  if (k === 'seq'){
    const l = lessonOf(k), asp = l.forms.filter(f => f.f.endsWith('h')), dip = l.forms.filter(f => !f.f.endsWith('h'));
    let t = '<p>Some sounds are written as two in a row, each typed as itself; nothing new to learn, only to notice.</p><ul>';
    if (asp.length) t += `<li>Aspiration is the letter followed by h, as it sounds: ${code(asp[0].f)} is ${ug(asp[0].g)}.</li>`;
    if (dip.length) t += `<li>A diphthong is a vowel followed by a glide: ${code(dip[0].f)} is ${ug(dip[0].g)}.</li>`;
    return [t + '</ul>' + tiles(l.forms), l];
  }
  if (k === 'tones'){
    const ts = Object.entries(L.tones);
    const ex = L.lessons.flatMap(l => l.words).find(w => /\d$/.test(w.t));
    return [`<p>${name} has ${ts.length} tones. Write each as a digit after its syllable, in the input and in the
      script alike: ${ts.map(([n, t]) => `<b>${n}</b> ${esc(t)}`).join(', ')}.` +
      (ex ? ` So ${code(ex.t)} is ${ug(ex.g)}.` : '') + '</p>', null];
  }
  if (k === 'caps'){
    const w = L.lessons.flatMap(l => l.words).find(w => w.t.length > w.w.length - 1 && /[a-z]/.test(w.t[0]) && w.t !== w.w);
    let ex = '';
    if (w){
      const cap = w.t[0].toUpperCase() + w.t.slice(1);
      let g = cap; try { g = render(cap); } catch (e) {}
      let G = w.t.toUpperCase(); try { G = render(G); } catch (e) {}
      ex = `<p>${code(cap)} is ${ug(g)}; ${code(w.t.toUpperCase())} is ${ug(G)}.</p>`;
    }
    return [`<p>Case is spelling, not sound. Capitalize a sound by typing its base letter uppercase. The operators
      read the same in either case, so all-caps text works sound by sound. A long consonant capitalizes only its first
      letter. A mark that floats above g or p goes below on the capital, since capitals have no descenders.</p>` + ex, null];
  }
  if (k === 'card'){
    const fs = allForms();
    return [`<p>Every sound of ${name} on one sheet, in the order of the lessons. Print it and keep it by the keyboard.</p>
      <p><button type="button" class="ln-print">print the card</button></p>
      <div class="ln-card"><h3>Diafon for ${name}</h3>${tiles(fs)}</div>`, null];
  }
  return ['', null];
}

function show(){
  at = Math.max(0, Math.min(at, steps.length - 1));
  const k = steps[at];
  $steps.innerHTML = steps.map((s, i) =>
    `<button type="button" data-i="${i}" class="${i === at ? 'here' : i < at ? 'done' : ''}">` +
    `<span class="n">${i + 1}</span> ${esc(s.startsWith('op:') ? s.slice(3) : TITLE[s])}</button>`).join('');
  const [html, l] = body(k);
  const items = l ? (l.drill.length ? l.drill : l.forms) : [];
  $lesson.innerHTML = `<h2>${at + 1}. ${esc(stepTitle(k))}</h2>${html}${l ? words(l.words) : ''}${drill(items)}`;
  wireDrill(items);
  const p = $lesson.querySelector('.ln-print');
  if (p) p.addEventListener('click', () => window.print());
  $prev.disabled = at === 0;
  $next.disabled = at === steps.length - 1;
  history.replaceState(null, '', `#lang=${$lang.value}&lesson=${at + 1}`);
  store.set('lang', $lang.value); try { localStorage.setItem('diafon-lang', $lang.value); } catch (e) {}
  store.set('lesson-' + $lang.value, String(at));
}

function go(i){ at = i; show(); $lesson.scrollIntoView({block: 'start', behavior: 'smooth'}); }
$steps.addEventListener('click', e => { const b = e.target.closest('button[data-i]'); if (b) go(+b.dataset.i); });
$prev.addEventListener('click', () => go(at - 1));
$next.addEventListener('click', () => go(at + 1));
$lang.addEventListener('change', () => { build($lang.value); at = +(store.get('lesson-' + $lang.value) || 0); show(); });

// the language: from the link, else the last one used, else the browser's, else English
const shared = () => { try { return localStorage.getItem('diafon-lang'); } catch (e) { return null; } };  // the language picked on any page
const codes = languages();
const q = new URLSearchParams(location.hash.slice(1));
const nav = (navigator.language || '').slice(0, 2).toLowerCase();
const start = [q.get('lang'), shared(), store.get('lang'), nav, 'en'].find(c => c && LEARN[c]);
$lang.value = start;
build(start);
at = q.get('lang') === start && q.get('lesson') ? +q.get('lesson') - 1 : +(store.get('lesson-' + start) || 0);
show();
})();
