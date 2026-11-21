// The Reference page: the table switch and the samples of the picked language.
(function(){
'use strict';
const $ = id => document.getElementById(id);
const $table = $('mt-table');
const secs = [...document.querySelectorAll('section[id^=sec-]')];
const esc = s => s.replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));

// ---- state in the address: ?table=hu, so the hash stays free for a section; an 'also written'
// link (#table=pl&letter=s̤), an older #table=hu and a bare #hu still read, and are written back as ?table=
function urlState(){
  const st = Object.fromEntries(new URLSearchParams(location.search));
  const h = location.hash.slice(1);
  if (h.includes('=')) Object.assign(st, Object.fromEntries(new URLSearchParams(h)));
  else if (h && $('sec-' + h)) st.table = h;
  return st;
}
function saveState(){
  const q = new URLSearchParams(location.search);
  if ($table.value !== 'universal') q.set('table', $table.value); else q.delete('table');
  const h = location.hash.slice(1);
  const anchor = h && !h.includes('=') && !$('sec-' + h) ? '#' + h : '';   // a section anchor stays
  const s = q.toString();
  history.replaceState(null, '', location.pathname + (s ? '?' + s : '') + anchor);
}

// ---- tables
$table.innerHTML = secs.map(x => `<option value="${x.id.slice(4)}">${esc(x.dataset.name)}</option>`).join('');
function current(){ return document.getElementById('sec-' + $table.value); }
function showTable(){ for (const x of secs) x.hidden = x !== current(); }

// the sample texts: only the picked language's own (English for the Diafon table, as the site's language);
// a language without texts hides the section
const articles = [...document.querySelectorAll('.samples .sample')];
function showSamples(){
  const lang = $table.value === 'universal' ? 'en' : $table.value;
  let any = false;
  for (const a of articles){ a.hidden = a.dataset.lang !== lang; any = any || !a.hidden; }
  $('mt-samples').hidden = !any;
}

// the languages overview: a row opens that language's table
document.getElementById('sec-universal').addEventListener('click', e => {
  const tr = e.target.closest('tr[data-goto]');
  if (!tr) return;
  $table.value = tr.dataset.goto;
  showTable(); showSamples(); saveState();
  $table.scrollIntoView({block: 'nearest'});
});

// ---- wiring
$table.addEventListener('change', () => { showTable(); showSamples(); saveState(); });

function fromHash(){             // all languages, unless the address names a language (?table=hu)
  const st = urlState();
  $table.value = st.table && $('sec-' + st.table) ? st.table : 'universal';
}
// an 'also written' link (#table=pl&letter=s̤): that language's table, at that row
function goRow(){
  const st = urlState();
  if (!st.table || !$('sec-' + st.table)) return;
  if ($table.value !== st.table){ $table.value = st.table; showTable(); showSamples(); }
  const tr = st.letter && [...document.querySelectorAll(`#sec-${st.table} tr[data-letter]`)]
    .find(r => r.dataset.letter.normalize('NFC') === st.letter.normalize('NFC'));
  saveState();
  if (!tr) return;
  tr.scrollIntoView({block: 'center'});
  tr.classList.remove('hit'); void tr.offsetWidth; tr.classList.add('hit');
}
window.addEventListener('hashchange', goRow);

fromHash();
showTable();
showSamples();
goRow();
})();
