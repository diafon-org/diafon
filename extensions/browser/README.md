# Diafon browser extension

Reads any page in Universal. Chrome, Edge, Brave (Manifest V3) and Firefox.

- **Click the icon** to turn it on, and again to turn it off; the setting
  holds for every page, and the icon is grey while off, coloured while on.
  A page's text, in the
  language's spelling, is read back and rendered in the script: sok szép
  nyár → șok sép n̦ár. Off restores every text node.
- **The language** comes from the page: its `lang` attribute when it names
  a spelling the engine has, else the text: the one spelling that reads it
  in full, or, when several do (plain ASCII reads as many), English by its
  function words, else the first of the browser's languages among them.
  The icon's tooltip names the language found. Only on a page where none
  of this says does the icon open a picker instead, with the switch and a
  language for that site, remembered for it.

- **Keep names as written.** In the icon's right-click menu (and on the
  options page): a capitalised word inside a sentence stays in its own
  spelling; the first word of a sentence still reads, since it cannot be
  told from a name.
- **Your own entries.** A name no dictionary knows, a loan the letters
  misread: select the word, right-click, “Diafon: read … as…”, and write it
  as it is said in the language's letters (Cudjoe → kadzsó). The page
  re-reads at once. Right-click the icon for “My entries”: the list per
  language, editable, exported as the lexicon's yaml (the `names` section
  of data/lexicon/<code>.yaml), imported from it, and proposed to the
  commons, so a good entry reaches every reader through the repo. Entries
  compete with the loan stems by length like the lexicon's own spoken
  entries, and follow the browser profile.

Text in inputs, editors, code and anything marked `translate="no"` is left
alone. An element's own `lang` attribute overrides the page's for its text
(a quote, a name), and a language with no spelling in the engine leaves
it as written. Every frame converts its own document. Content that
arrives later converts as it appears, and text a script rewrites in place
is read anew. Words go through
the lexicon where the language has one (data/lexicon): Hungarian ly stems,
English and Latin loans in a Hungarian page (meeting → mítiŋg), English
pages by the pronunciation dictionary, pinyin by syllable.

## Try it

Chrome: chrome://extensions → Developer mode → Load unpacked → this
directory. Firefox takes a background script where Chrome takes a worker,
so it loads a copy with its own manifest: scripts/build.sh writes
extensions/firefox (manifest.firefox.json in place of manifest.json); then
about:debugging → This Firefox → Load Temporary Add-on → that manifest.json.
Open a Hungarian page and click the icon. After a change, reload the
extension on its card, then reload the page: a page open from before keeps
the old content script.

## Layout

    manifest.json     Manifest V3 (Chrome); manifest.firefox.json, the same with a background script
    background.js     the icon: the click toggles; the picker is set on a tab only when its page reports no language
    engine.js         the engine, a copy of docs/engine.js (scripts/build.sh keeps it fresh)
    data.js           the data, a copy of docs/play-data.js
    content.js        the page walker: convertText, pageLanguage, the observer; reports the page's language
    popup.html/js     the picker: the switch and the language for this site
    options.html/js   my entries: list, edit, add, export and import as yaml, propose to the commons
    lexicon/          the lexicons (data/lexicon/*.json), fetched on demand for the page's language and its loans
    icons/            the round icon in its two states, on-*.png and off-*.png, from fonts/tools/logo.py

Settings live in chrome.storage.sync: `on`; `keepNames`; `langs`, host → code for the
sites picked by hand; `entries`, code → {spelling: said}, the reader's own. `#diafon=on` on a URL turns it on without the icon
(for tests); the root element carries `data-diafon` (loaded) and
`data-diafon-state` (on|off/language) for the same reason.
tests/test_extension.py holds convertText to the spec in node, and loads the
extension in **Chrome for Testing** over a sample page, driven over the
DevTools protocol (tests/ext_driver.mjs). Google Chrome itself no longer
takes `--load-extension` (since 137); install the test browser once with
`npx @puppeteer/browsers install chrome@stable --path ~/.cache/puppeteer`,
or point `DIAFON_CHROME` at any Chromium.

Known limits, from the engine: digraphs across a compound boundary read by
longest match (házszám → ház̦zám), and all-caps re-renders capitalized.
