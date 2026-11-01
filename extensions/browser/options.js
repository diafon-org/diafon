// The options page: the reader's words (spelling -> Diafon input, one list for
// every language), listed, edited, added, exported in the shape of
// data/lexicon/origin.yaml, imported from it, and proposed to the commons (a
// prefilled issue on the repo once it has one; the yaml on the clipboard
// until then). diafonInput and migrateEntries come from content.js.
'use strict';
const REPO = null;                          // set at publish: 'https://github.com/<owner>/diafon'
const $words = document.getElementById('words'), $status = document.getElementById('status'), $yaml = document.getElementById('yaml');
const $addWord = document.getElementById('addWord'), $addSaid = document.getElementById('addSaid');
let words = {};

function save(next, note) {
  words = next;
  chrome.storage.sync.set({words}, () => { show(); $status.textContent = note || ''; });
}

/** Diafon input checked, or a note on the status line and null. */
function checked(said) {
  const t = diafonInput(said);
  if (!t) $status.textContent = `“${said}” is not Diafon input.`;
  return t;
}

function show() {
  $words.innerHTML = '';
  const list = Object.entries(words).sort();
  if (!list.length) { $words.innerHTML = '<p class="empty">No words yet.</p>'; return; }
  const t = document.createElement('table');
  t.innerHTML = '<tr><th>On the page</th><th>Diafon input</th><th>Shows</th><th></th></tr>';
  for (const [word, said] of list) {
    const tr = document.createElement('tr');
    const tdW = document.createElement('td'); tdW.textContent = word;
    const tdS = document.createElement('td'); const inp = document.createElement('input'); inp.type = 'text'; inp.value = said; tdS.appendChild(inp);
    const tdR = document.createElement('td'); tdR.className = 'lang'; tdR.textContent = render(said);
    inp.addEventListener('change', () => {
      const n = structuredClone(words);
      if (!inp.value.trim()) { delete n[word]; save(n, `${word} removed`); return; }
      const v = checked(inp.value); if (!v) { inp.value = said; return; }
      n[word] = v; save(n, `${word}: ${render(v)}`);
    });
    const tdX = document.createElement('td'); const del = document.createElement('button'); del.textContent = 'Remove'; tdX.appendChild(del);
    del.addEventListener('click', () => { const n = structuredClone(words); delete n[word]; save(n, `${word} removed`); });
    tr.append(tdW, tdS, tdR, tdX); t.appendChild(tr);
  }
  $words.appendChild(t);
}

document.getElementById('addBtn').addEventListener('click', () => {
  const w = $addWord.value.normalize('NFC').trim().toLowerCase(), said = $addSaid.value.trim();
  if (!w || !said) { $status.textContent = 'Both the spelling and its Diafon input are needed.'; return; }
  const t = checked(said); if (!t) return;
  const n = structuredClone(words); n[w] = t;
  $addWord.value = ''; $addSaid.value = '';
  save(n, `${w}: ${render(t)}`);
});

/** The words in the shape of data/lexicon/origin.yaml; the language of origin is the maintainer's to add. */
function toYaml() {
  const q = s => /[:#'"\s{}]/.test(s) || s === '' ? `'${s.replace(/'/g, "''")}'` : s;
  return Object.entries(words).sort().map(([w, t]) => `${q(w)}: {lang: ?, t: ${t}}`).join('\n') + '\n';
}
/** origin.yaml lines (word: {t: …}), plain word: input lines, or the old per-language shape (code: / names: / word: said). */
function fromYaml(text) {
  const out = {}, old = {}; let code = null;
  const unq = s => { s = s.trim(); return /^'.*'$/.test(s) ? s.slice(1, -1).replace(/''/g, "'") : /^".*"$/.test(s) ? s.slice(1, -1) : s; };
  for (const raw of text.split('\n')) {
    const line = raw.replace(/#.*$/, '').trimEnd();
    const m = /^(\s*)([^:]+):\s*(.*)$/.exec(line);
    if (!m) continue;
    const key = unq(m[2]), val = m[3].trim();
    if (!val) { if (key !== 'names' && key !== 'spoken') code = DIA.stages[key] ? key : null; continue; }
    const t = (/\bt:\s*([A-Za-z0-9]+)/.exec(val) || [])[1];
    if (t) { out[key.toLowerCase()] = t; continue; }
    if (code) { (old[code] = old[code] || {})[key.toLowerCase()] = unq(val); continue; }
    out[key.toLowerCase()] = unq(val);
  }
  return Object.assign(migrateEntries(old), out);
}

document.getElementById('exportBtn').addEventListener('click', () => { $yaml.value = toYaml(); $status.textContent = 'Shown below.'; });
document.getElementById('importBtn').addEventListener('click', () => {
  const next = structuredClone(words); let n = 0, bad = [];
  for (const [w, s] of Object.entries(fromYaml($yaml.value))) { const t = diafonInput(s); if (t) { next[w] = t; n++; } else bad.push(w); }
  save(next, `${n} words imported.` + (bad.length ? ` Not Diafon input: ${bad.join(', ')}.` : ''));
});
document.getElementById('proposeBtn').addEventListener('click', () => {
  const yaml = toYaml();
  const body = `Words from a reader, for data/lexicon/origin.yaml (fill in each word's language of origin):\n\n\`\`\`yaml\n${yaml}\`\`\`\n`;
  if (REPO) { window.open(`${REPO}/issues/new?title=${encodeURIComponent('Words: from a reader')}&body=${encodeURIComponent(body)}`); return; }
  $yaml.value = yaml;
  navigator.clipboard.writeText(body).then(() => { $status.textContent = 'Copied as a proposal; the repo is not public yet, so send it to the maintainer.'; }, () => { $status.textContent = 'Shown below; the repo is not public yet, so send it to the maintainer.'; });
});

const $keep = document.getElementById('keepNames'), $join = document.getElementById('join');
$keep.addEventListener('change', () => chrome.storage.sync.set({keepNames: $keep.checked}));
$join.addEventListener('change', () => chrome.storage.sync.set({join: $join.checked}));
chrome.storage.sync.get({words: {}, entries: {}, keepNames: false, join: false}, s => {
  words = Object.assign(migrateEntries(s.entries), s.words || {});
  if (Object.keys(s.entries || {}).length) chrome.storage.sync.set({words, entries: {}});
  $keep.checked = !!s.keepNames; $join.checked = !!s.join; show();
});
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'sync') return;
  if (changes.words) { words = changes.words.newValue || {}; show(); }
  if (changes.keepNames) $keep.checked = !!changes.keepNames.newValue;
  if (changes.join) $join.checked = !!changes.join.newValue;
});
