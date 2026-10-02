// The icon: a click turns the conversion on and off, for every page; it is
// grey while off and coloured while on (icons/off-*.png, on-*.png). The
// popup (a language picker) opens instead only on a tab whose language the
// page walker could not recognise; the content script reports that per tab.
// Settings (chrome.storage.sync): on true|false; langs {host: code}, the
// languages picked by hand for the pages that needed it; entries, the
// reader's own readings, made from the selection menu, kept on the options
// page. The icon's own menu opens that page.
'use strict';

function menus() {
  chrome.storage.sync.get({keepNames: false}, s => chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({id: 'say', title: 'Diafon: read “%s” as…', contexts: ['selection']});
    chrome.contextMenus.create({id: 'keepNames', type: 'checkbox', checked: s.keepNames, title: 'Keep names as written', contexts: ['action']});
    chrome.contextMenus.create({id: 'entries', title: 'My entries…', contexts: ['action']}, () => {
      if (chrome.runtime.lastError) console.error('Diafon menus:', chrome.runtime.lastError.message);
    });
  }));
}
menus();                                  // the worker starts often; removeAll keeps it idempotent
chrome.runtime.onInstalled.addListener(menus);
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'say' && tab) chrome.tabs.sendMessage(tab.id, {type: 'say'});
  if (info.menuItemId === 'keepNames') chrome.storage.sync.set({keepNames: !!info.checked});
  if (info.menuItemId === 'entries') chrome.runtime.openOptionsPage();
});
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'sync' && changes.keepNames) chrome.contextMenus.update('keepNames', {checked: !!changes.keepNames.newValue}, () => chrome.runtime.lastError);
});

const icons = state => Object.fromEntries([16, 32, 48, 128].map(sz => [sz, `icons/${state}-${sz}.png`]));

function showState(on) {
  chrome.action.setIcon({path: icons(on ? 'on' : 'off')});
  chrome.action.setTitle({title: on ? 'Diafon · reading in Universal (click to turn off)' : 'Diafon · off (click to read in Universal)'});
}

chrome.storage.sync.get({on: false}, s => showState(s.on));
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'sync' && changes.on) showState(changes.on.newValue);
});

// Fires only where no popup is set: the toggle.
chrome.action.onClicked.addListener(() => {
  chrome.storage.sync.get({on: false}, s => chrome.storage.sync.set({on: !s.on}));
});

// A page reports what it read: a recognised language gets the plain toggle,
// an unrecognised one the picker; the tab's tooltip names the language.
const native = code => { try { return new Intl.DisplayNames(['en'], {type: 'language'}).of(code); } catch (e) { return code; } };
chrome.runtime.onMessage.addListener((msg, sender) => {
  if (!msg || msg.type !== 'page' || !sender.tab) return;
  const tabId = sender.tab.id;
  chrome.action.setPopup({tabId, popup: msg.detected ? '' : 'popup.html'});
  chrome.action.setTitle({tabId, title: msg.detected ? `Diafon · ${native(msg.detected)}, from the page`
                                  : msg.lang ? `Diafon · ${native(msg.lang)}, picked for this site (click to change)`
                                  : 'Diafon · no language recognised on this page; click to pick one'});
});
