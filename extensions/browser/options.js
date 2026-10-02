// The options page: the reader's entries per language, listed, edited, added,
// exported as the lexicon's yaml, imported from it, and proposed to the
// commons (a prefilled issue on the repo once it has one; the yaml on the
// clipboard until then).
'use strict';
const REPO = null;                          // set at publish: 'https://github.com/<owner>/diafon'
const $langs = document.getElementById('langs'), $status = document.getElementById('status'), $yaml = document.getElementById('yaml');
const $addLang = document.getElementById('addLang'), $addWord = document.getElementById('addWord'), $addSaid = document.getElementById('addSaid');
const native = code => { try { return new Intl.DisplayNames(['en'], {type: 'language'}).of(code); } catch (e) { return code; } };
const lettered = Object.keys(DIA.stages).filter(c => !DIA.stages[c].lexical).sort((a, b) => native(a).localeCompare(native(b)));
for (const c of lettered) { const o = document.createElement('option'); o.value = c; o.textContent = native(c); $addLang.appendChild(o); }
let entries = {};

function save(next, note) {
  entries = next;
  chrome.storage.sync.set({entries}, () => { render(); $status.textContent = note || ''; });
}

function render() {
  $langs.innerHTML = '';
  const codes = Object.keys(entries).filter(c => Object.keys(entries[c] || {}).length).sort();
  if (!codes.length) { $langs.innerHTML = '<p class="empty">No entries yet.</p>'; return; }
  for (const c of codes) {
    const h = document.createElement('h2'); h.innerHTML = `<span class="lang">${native(c)}</span> <span class="note">(${c})</span>`;
    $langs.appendChild(h);
    const t = document.createElement('table');
    t.innerHTML = '<tr><th>On the page</th><th>As it is said</th><th></th></tr>';
    for (const [word, said] of Object.entries(entries[c]).sort()) {
      const tr = document.createElement('tr');
      const tdW = document.createElement('td'); tdW.textContent = word;
      const tdS = document.createElement('td'); const inp = document.createElement('input'); inp.type = 'text'; inp.value = said; tdS.appendChild(inp);
      inp.addEventListener('change', () => { const n = structuredClone(entries); if (inp.value.trim()) n[c][word] = inp.value.trim(); else delete n[c][word]; save(n, `${word}: ${inp.value.trim() || 'removed'}`); });
      const tdX = document.createElement('td'); const del = document.createElement('button'); del.textContent = 'Remove'; tdX.appendChild(del);
      del.addEventListener('click', () => { const n = structuredClone(entries); delete n[c][word]; save(n, `${word} removed`); });
      tr.append(tdW, tdS, tdX); t.appendChild(tr);
    }
    $langs.appendChild(t);
  }
}

document.getElementById('addBtn').addEventListener('click', () => {
  const c = $addLang.value, w = $addWord.value.normalize('NFC').trim().toLowerCase(), said = $addSaid.value.normalize('NFC').trim();
  if (!w || !said) { $status.textContent = 'Both the spelling and how it is said are needed.'; return; }
  const n = structuredClone(entries); n[c] = n[c] || {}; n[c][w] = said;
  $addWord.value = ''; $addSaid.value = '';
  save(n, `${w}: ${said}`);
});

/** The entries in the lexicon's yaml: one language, its names section. */
function toYaml(codes = null) {
  const q = s => /[:#'"\s]/.test(s) || s === '' ? `'${s.replace(/'/g, "''")}'` : s;
  return (codes || Object.keys(entries)).filter(c => Object.keys(entries[c] || {}).length).sort()
    .map(c => `${c}:\n  names:\n` + Object.entries(entries[c]).sort().map(([w, s]) => `    ${q(w)}: ${q(s)}`).join('\n')).join('\n') + '\n';
}
/** The same shape read back: code: / names: / word: said; a bare word: said line goes to the last language seen. */
function fromYaml(text) {
  const out = {}; let code = null;
  const unq = s => { s = s.trim(); return /^'.*'$/.test(s) ? s.slice(1, -1).replace(/''/g, "'") : /^".*"$/.test(s) ? s.slice(1, -1) : s; };
  for (const raw of text.split('\n')) {
    const line = raw.replace(/#.*$/, '').trimEnd();
    if (!line.trim()) continue;
    const m = /^(\s*)([^:]+):\s*(.*)$/.exec(line);
    if (!m) continue;
    const key = unq(m[2]), val = unq(m[3]);
    if (!val) { if (key !== 'names' && key !== 'spoken') code = key; continue; }
    if (!code) continue;
    out[code] = out[code] || {}; out[code][key.toLowerCase()] = val;
  }
  return out;
}

document.getElementById('exportBtn').addEventListener('click', () => { $yaml.value = toYaml(); $status.textContent = 'Shown below.'; });
document.getElementById('importBtn').addEventListener('click', () => {
  const got = fromYaml($yaml.value); let n = 0;
  const next = structuredClone(entries);
  for (const [c, words] of Object.entries(got)) { if (!DIA.stages[c]) continue; next[c] = next[c] || {}; for (const [w, s] of Object.entries(words)) { next[c][w] = s; n++; } }
  save(next, `${n} entries imported.`);
});
document.getElementById('proposeBtn').addEventListener('click', () => {
  const yaml = toYaml();
  const body = `Entries from a reader, for data/lexicon/<code>.yaml, the names section:\n\n\`\`\`yaml\n${yaml}\`\`\`\n`;
  if (REPO) { window.open(`${REPO}/issues/new?title=${encodeURIComponent('Names: entries from a reader')}&body=${encodeURIComponent(body)}`); return; }
  $yaml.value = yaml;
  navigator.clipboard.writeText(body).then(() => { $status.textContent = 'Copied as a proposal; the repo is not public yet, so send it to the maintainer.'; }, () => { $status.textContent = 'Shown below; the repo is not public yet, so send it to the maintainer.'; });
});

const $keep = document.getElementById('keepNames');
$keep.addEventListener('change', () => chrome.storage.sync.set({keepNames: $keep.checked}));
chrome.storage.sync.get({entries: {}, keepNames: false}, s => { entries = s.entries || {}; $keep.checked = !!s.keepNames; render(); });
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'sync') return;
  if (changes.entries) { entries = changes.entries.newValue || {}; render(); }
  if (changes.keepNames) $keep.checked = !!changes.keepNames.newValue;
});
