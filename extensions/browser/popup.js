// The picker, opened by the icon only on a page whose language was not
// recognised: the on/off switch (the click could not toggle it here) and the
// language for this host, remembered in settings.langs.
'use strict';
const $on = document.getElementById('on'), $lang = document.getElementById('lang'), $status = document.getElementById('status');
const native = code => { try { return new Intl.DisplayNames([code], {type: 'language'}).of(code); } catch (e) { return code; } };
const stages = Object.keys(DIA.stages).sort((a, b) => DIA.stages[a].name.localeCompare(DIA.stages[b].name));
const none = document.createElement('option');
none.value = ''; none.textContent = 'Not recognised · pick one';
$lang.appendChild(none);
for (const c of stages) {
  const o = document.createElement('option');
  o.value = c; o.textContent = `${native(c)} · ${DIA.stages[c].name.replace(' spelling', '')} (${c})`;
  $lang.appendChild(o);
}
let host = null;
chrome.storage.sync.get({on: false, langs: {}}, s => {
  $on.checked = s.on;
  chrome.tabs.query({active: true, currentWindow: true}, tabs => {
    if (!tabs[0]) return;
    chrome.tabs.sendMessage(tabs[0].id, {type: 'status'}, r => {
      if (chrome.runtime.lastError || !r) { $status.textContent = 'Diafon does not run on this page.'; $lang.disabled = true; return; }
      host = r.host;
      $lang.value = s.langs[host] || '';
      $status.textContent = $lang.value ? `Kept for ${host}.` : `No language with a spelling recognised on ${host}; the page stays as it is until one is picked.`;
    });
  });
});
$on.addEventListener('change', () => chrome.storage.sync.set({on: $on.checked}));
$lang.addEventListener('change', () => {
  if (host === null) return;
  chrome.storage.sync.get({langs: {}}, s => {
    const langs = s.langs;
    if ($lang.value) langs[host] = $lang.value; else delete langs[host];
    chrome.storage.sync.set({langs});
    $status.textContent = $lang.value ? `Kept for ${host}.` : `No language picked for ${host}.`;
  });
});
