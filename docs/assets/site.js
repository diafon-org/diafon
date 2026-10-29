// The two site-wide switches in the header: the site's language (English for
// now) and the script its text is shown in: the usual spelling, Diafon, or,
// kept apart, another language's spelling. The text is converted in place from
// the English reading of each word (site-words.js); examples, glyphs, IPA,
// code and the tables stay as they are.
(function(){
'use strict';
const BASE = document.currentScript.src.replace(/assets\/site\.js.*$/, '');
const store = {
  get(k){ try { return localStorage.getItem('diafon-' + k); } catch (e) { return null; } },
  set(k, v){ try { localStorage.setItem('diafon-' + k, v); } catch (e) {} }
};
const SKIP = 'code, pre, kbd, script, style, textarea, select, option, svg, em, i, mark, .ug, .key, .md-search, ' +
  '.headerlink, .same-nat, .same-dia, .sample, .mt-sample, .tryout, .mt-wrap, section[id^="sec-"], .pt, .opx, ' +
  '.chips, .tile, .site-switch';
const ROOTS = '.md-content, .md-tabs, .md-sidebar--secondary';
const TOKEN = /\/[^\/\s][^\/]*?\/|[A-Za-z][A-Za-z']*[A-Za-z]/g;   // IPA between slashes stays; one letter is a letter named
const original = new WeakMap();
let mode = new URLSearchParams(location.search).get('script') || store.get('script') || 'latin';   // ?script=diafon links a view

function load(src){
  return new Promise((ok, fail) => {
    const s = document.createElement('script');
    s.src = BASE + src; s.onload = ok; s.onerror = fail;
    document.head.appendChild(s);
  });
}
let ready = null;
function needs(){
  if (!ready){
    const steps = [];
    if (typeof SITE_WORDS === 'undefined') steps.push(() => load('assets/site-words.js'));
    if (typeof DIA === 'undefined') steps.push(() => load('play-data.js'));
    if (typeof render === 'undefined') steps.push(() => load('engine.js'));
    ready = steps.reduce((p, f) => p.then(f), Promise.resolve());
  }
  return ready;
}

// a possessive the list lacks: the word's reading plus the s it adds (/ɪz/ after a hiss, /s/ after a voiceless sound)
function reading(k){
  if (SITE_WORDS[k] !== undefined) return SITE_WORDS[k];
  const m = k.match(/^(.+)'s$/), t = m && SITE_WORDS[m[1]];
  if (t === undefined || t === null) return undefined;
  return t + (/(s|z|sj|zj|tq|dq)$/.test(t) ? 'iz' : /(p|t|k|f|tx)$/.test(t) ? 's' : 'z');
}
function word(w){
  const t = reading(w.toLowerCase());
  if (t === undefined) return w;
  const cased = w[0] !== w[0].toLowerCase() ? t[0].toUpperCase() + t.slice(1) : t;
  return mode === 'diafon' ? render(cased) : renderStage(cased, DIA.stages[mode.slice(6)]);
}
function convertNode(n){
  if (!original.has(n)) original.set(n, n.nodeValue);
  const src = original.get(n);
  n.nodeValue = mode === 'latin' ? src : src.replace(TOKEN, m => m[0] === '/' ? m : word(m));
}
function walk(root){
  const it = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: n => !n.nodeValue.trim() || n.parentElement.closest(SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
  });
  const nodes = [];
  while (it.nextNode()) nodes.push(it.currentNode);
  nodes.forEach(convertNode);
}
function apply(){
  document.documentElement.dataset.script = mode;
  const go = () => document.querySelectorAll(ROOTS).forEach(walk);
  if (mode === 'latin') go(); else needs().then(go);
}
// pages that write text later (the lessons, the try-out) are followed
new MutationObserver(recs => {
  if (mode === 'latin') return;
  for (const r of recs) for (const n of r.addedNodes){
    if (n.nodeType === 1 && !n.closest(SKIP) && n.closest(ROOTS)) walk(n);
    else if (n.nodeType === 3 && n.parentElement && !n.parentElement.closest(SKIP) && n.parentElement.closest(ROOTS)) convertNode(n);
  }
}).observe(document.body, {childList: true, subtree: true});

// ---- the switches
function spellings(){
  return typeof SITE_SPELLINGS !== 'undefined' ? Promise.resolve() : load('assets/site-words.js');
}
const bar = document.createElement('div');
bar.className = 'site-switch';
bar.innerHTML =
  '<label><span>Language</span><select id="site-lang" autocomplete="off">' +
    '<option value="en" selected>English</option><option disabled>more soon</option></select></label>' +
  '<label><span>Script</span><select id="site-script" autocomplete="off">' +
    '<option value="latin">Usual spelling</option><option value="diafon">Diafon</option></select></label>';
const header = document.querySelector('.md-header__inner');
const before = header && (header.querySelector('.md-header__option') || header.querySelector('.md-search'));
if (header) header.insertBefore(bar, before || null);
const $script = bar.querySelector('#site-script');
spellings().then(() => {
  const g = document.createElement('optgroup');
  g.label = 'In another language\'s spelling';
  g.innerHTML = SITE_SPELLINGS.map(([c, n]) => `<option value="stage:${c}">${n.replace(/ spelling$/, '')}</option>`).join('');
  $script.appendChild(g);
  if (![...$script.options].some(o => o.value === mode)) mode = 'latin';
  $script.value = mode;
});
$script.value = mode === 'diafon' ? 'diafon' : 'latin';
$script.addEventListener('change', () => { mode = $script.value; store.set('script', mode); apply(); });
if (mode !== 'latin') apply();
})();
