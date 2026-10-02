#!/usr/bin/env python3
"""The browser extension against the spec. Run: python3 tests/test_extension.py

1. content.js's convertText and pageLanguage, run in node over the bundled
   engine, agree with the Python engine on the stage samples and detect a
   page's language from its text.
2. Chrome for Testing (when present; Google Chrome itself dropped
   --load-extension in 137) loads the extension over a sample Hungarian
   page, driven over the DevTools protocol by tests/ext_driver.mjs: the
   page loads as it is; the setting the icon toggles, flipped in the
   background, converts the text to the script (inputs, code and svg
   untouched, the title and late content converted) and flipped back
   restores it; the reader's own entry reads a name as said.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import stages

EXT = os.path.join(ROOT, 'extensions', 'browser')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


def bundle():
    js = '\n'.join(open(os.path.join(EXT, f)).read() for f in ('data.js', 'engine.js', 'content.js'))
    lexdir = os.path.join(EXT, 'lexicon')
    load = ''.join(f"setLexicon({json.dumps(c)}, JSON.parse(require('fs').readFileSync({json.dumps(os.path.join(lexdir, c + '.json'))}, 'utf8')));\n"
                   for c in sorted(f[:-5] for f in os.listdir(lexdir) if f.endswith('.json')))
    return js + '\n' + load


def test_convert_text():
    node = shutil.which('node')
    assert node, 'node is required'
    cases = []
    for code in stages.codes():
        st = stages.load(code)
        spelled = stages.render(st['sample'], st)
        cases.append([spelled, code, stages.convert(spelled, f'stage:{code}', 'script')])
        cases.append([spelled, None, spelled])                       # no language recognised: the page stays
    prog = bundle() + r'''
const cases = JSON.parse(require('fs').readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(cases.map(([t, l]) => convertText(t, l))));
'''
    res = subprocess.run([node, '-e', prog], input=json.dumps(cases), text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    got = json.loads(res.stdout)
    bad = [(c, g) for c, g in zip(cases, got) if g != c[2]]
    assert not bad, bad[:5]
    print(f'convertText holds {len(cases)} cases')


def test_page_language():
    """pageLanguage from the text alone (no lang attribute): each stage's
    sample reads as its own language for a reader of that language (the
    short samples tie: dobra noc reads as Czech, Hungarian or Turkish too);
    text with a language's own letters needs no reader; English by its
    function words; plain ASCII that many spellings read goes to the
    reader's language, else to nobody."""
    node = shutil.which('node')
    cases = []
    for code in stages.codes():
        st = stages.load(code)
        if code in ('en', 'zh'):
            continue                                        # lexical: their letters say nothing without the lexicon
        cases.append([stages.render(st['sample'], st), [code], code])
    cases += [['Kedves vendégeink, a hőmérséklet ma húsz fok, a tavaszi szünet jövő héten kezdődik.', [], 'hu'],
              ['Čeština je západoslovanský jazyk, nejbližší slovenštině, poté polštině a lužické srbštině.', ['hu'], 'cs'],
              ['Suomen kieli on uralilaisen kielikunnan itämerensuomalaiseen ryhmään kuuluva kieli.', [], 'fi'],
              ['Türkçe, Türk dilleri ailesine ait bir dildir; Ankara ve Kıbrıs başta olmak üzere konuşulur.', [], 'tr'],
              ['Język polski należy do grupy języków zachodniosłowiańskich; posługuje się nim około czterdziestu milionów ludzi.', [], 'pl']]
    en = 'The quick brown fox jumps over the lazy dog, and the dog is not amused by this at all; that is the way of the world, for you and for me, with all of us in it.'
    cases.append([en, [], 'en'])
    cases.append([en, ['hu'], 'en'])
    ascii = 'lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua'
    cases.append([ascii, ['de-DE', 'hu'], 'hu'])
    cases.append([ascii, ['de-DE'], None])
    cases.append([ascii, [], None])
    cases.append(['', ['hu'], None])
    prog = bundle() + r'''
const cases = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const doc = {documentElement: {lang: ''}, body: null};
process.stdout.write(JSON.stringify(cases.map(([t, p]) => pageLanguage(doc, t, p))));
'''
    res = subprocess.run([node, '-e', prog], input=json.dumps(cases), text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    got = json.loads(res.stdout)
    bad = [(c[2], g, c[0][:40]) for c, g in zip(cases, got) if g != c[2]]
    assert not bad, bad
    print(f'pageLanguage holds {len(cases)} cases')


def test_keep_names():
    """convertText with keepNames: a capitalised word inside a sentence stays,
    the first word of the text or of a sentence reads, quotes and brackets
    before a name do not make it a sentence start."""
    node = shutil.which('node')
    c = lambda t: stages.convert(t, 'stage:hu', 'script')
    text = 'Sok szép nyár Budapesten. Kovács János ment „Bécsbe” (Ausztria). SZÉP.'
    want = c('Sok szép nyár ') + 'Budapesten' + c('. Kovács ') + 'János' + c(' ment „') + 'Bécsbe' + c('” (') + 'Ausztria' + c('). SZÉP.')
    prog = bundle() + r'''
process.stdout.write(JSON.stringify([convertText(%s, 'hu', true), convertText(%s, 'hu', false), convertText('Alma', 'hu', true)]));
''' % (json.dumps(text), json.dumps(text))
    res = subprocess.run([node, '-e', prog], text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    got = json.loads(res.stdout)
    assert got[0] == want, (got[0], want)
    assert got[1] == c(text)
    assert got[2] == c('Alma')
    print('keepNames holds')


def test_entries():
    """The reader's own entries (content.js entryTable, layEntries): laid over
    the Hungarian lexicon a name reads as said, competing with the loan stems
    by length; over a language with no lexicon (Czech) one is made; a removed
    entry goes."""
    node = shutil.which('node')
    hu = stages.load('hu')
    want = stages.convert('Trelóni', 'stage:hu', 'script')
    want_cs = stages.convert('Cadžou', 'stage:cs', 'script')
    prog = bundle() + r'''
const out = [];
layEntries('hu', {trelawny: 'trelóni', team: 'tím'});
out.push(convertText('Trelawny, team, teamek.', 'hu'));
layEntries('hu', {});
out.push(convertText('Trelawny, team.', 'hu'));
layEntries('cs', {cudjoe: 'Cadžou'});
out.push(convertText('Cudjoe', 'cs'));
process.stdout.write(JSON.stringify(out));
'''
    res = subprocess.run([node, '-e', prog], text=True, capture_output=True)
    assert res.returncode == 0, res.stderr
    got = json.loads(res.stdout)
    team = stages.convert('team', 'stage:hu', 'script')
    assert got[0] == f'{want}, {stages.convert("tím", "stage:hu", "script")}, {stages.convert("tímek", "stage:hu", "script")}.', got[0]
    assert got[1] == f'{stages.convert("Trelawny", "stage:hu", "script")}, {team}.', got[1]
    assert got[2] == want_cs, (got[2], want_cs)
    print('entries hold: laid, removed, and over a language with no lexicon')


def sample_page():
    hu = stages.load('hu')
    text = stages.render(hu['sample'], hu)
    return f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><title>Minta</title></head>
<body><h1 id="h">{text}</h1><p id="p">Folyó, lyuk; SZÉP.</p><p id="loan">Meeting, like, taxi.</p>
<input id="i" value="{text}"><code id="c">{text}</code><span translate="no" id="n">{text}</span>
<svg width="200" height="40"><text>{text}</text></svg>
<p id="name">Trelawny</p><p id="keep">Sok Trelawny</p><p id="late"></p>
<p id="mixed">Meeting <span lang="en">the quick brown fox</span> vége.</p><p id="de"><span lang="de-DE">Die Sprache</span></p>
<p id="mut">alma</p><iframe id="fr" src="frame.html"></iframe><p id="mirror" translate="no"></p>
<script>setTimeout(() => {{ document.getElementById('late').textContent = '{text} (később)'; }}, 400);
setTimeout(() => {{ document.getElementById('mut').firstChild.data = 'szép nyár'; }}, 600);
setInterval(() => {{ try {{ document.getElementById('mirror').textContent = document.getElementById('fr').contentDocument.body.textContent.trim(); }} catch (e) {{}} }}, 250);</script>
</body></html>'''


def late_page():
    """No lang attribute, no text at load: the text comes by script."""
    text = 'Kedves vendégeink, a hőmérséklet ma húsz fok, a tavaszi szünet jövő héten kezdődik. Sok szép nyár, hosszú alma.'
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>Late</title></head>
<body><p id="late"></p><script>setTimeout(() => {{ document.getElementById('late').textContent = '{text}'; }}, 500)</script>
</body></html>'''


def serve(pages):
    """The pages served on localhost: (port, shutdown)."""
    import http.server
    import socketserver
    import threading
    tmp = tempfile.mkdtemp(prefix='diafon-ext-')
    for name, html in pages.items():
        open(os.path.join(tmp, name), 'w').write(html)
    handler_cls = type('Quiet', (http.server.SimpleHTTPRequestHandler,), {'log_message': lambda *a: None})
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(('127.0.0.1', 0), lambda *a, **k: handler_cls(*a, directory=tmp, **k))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd.server_address[1], httpd.shutdown, tmp


def test_chrome_late():
    """A page with no lang attribute whose text comes by script: switched on
    it reads once the text is there, and reloaded while on it reads again,
    the language detected from the text that arrives after load."""
    chrome = chrome_for_testing()
    node = shutil.which('node')
    if not chrome or not node:
        return
    port, shutdown, tmp = serve({'late.html': late_page()})
    try:
        res = subprocess.run([node, os.path.join(ROOT, 'tests', 'ext_driver.mjs'), chrome, EXT,
                              f'http://127.0.0.1:{port}/late.html', '', '2500',
                              'chrome.storage.sync.set({on: true})',
                              'chrome.tabs.query({}).then(ts => chrome.tabs.reload(ts[0].id)).then(() => "reloaded")'],
                             capture_output=True, text=True, timeout=120)
        assert res.returncode == 0, res.stderr
        before, on, reloaded = res.stdout.split('\n<<<diafon-step>>>\n')
    finally:
        shutdown()
    want = stages.convert('Kedves vendégeink', 'stage:hu', 'script')
    assert 'data-diafon-state="off/hu"' in before, before[:300]           # detected from the late text, while off
    assert want in on and 'data-diafon-state="on/hu"' in on, on[:400]
    assert want in reloaded and 'data-diafon-state="on/hu"' in reloaded, reloaded[:400]
    print('Chrome for Testing: a page filled by script reads when switched on, and again after a reload')


def chrome_for_testing():
    """A Chrome that still takes --load-extension (Google Chrome dropped it in
    137): $DIAFON_CHROME, else Chrome for Testing in the puppeteer cache
    (npx @puppeteer/browsers install chrome@stable --path ~/.cache/puppeteer)."""
    import glob
    env = os.environ.get('DIAFON_CHROME')
    if env and os.path.exists(env):
        return env
    hits = sorted(glob.glob(os.path.expanduser(
        '~/.cache/puppeteer/chrome/*/chrome-mac-*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing')))
    return hits[-1] if hits else None


def test_chrome():
    """Chrome for Testing with the extension loaded, driven over the DevTools
    protocol (tests/ext_driver.mjs), over the sample page served on
    localhost: as it is at first; on (the setting the icon's click flips,
    set here in the background) the text converts to the script, code and
    no-translate spans stay, the title and late content convert too; off
    restores it."""
    chrome = chrome_for_testing()
    node = shutil.which('node')
    if not chrome or not node:
        print('SKIP: Chrome for Testing (or node) not installed; see chrome_for_testing()')
        return
    import http.server
    import socketserver
    import threading
    tmp = tempfile.mkdtemp(prefix='diafon-ext-')
    open(os.path.join(tmp, 'page.html'), 'w').write(sample_page())
    open(os.path.join(tmp, 'frame.html'), 'w').write('<!doctype html><html lang="hu"><meta charset="utf-8"><body>hosszú alma</body></html>')
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=tmp, **k)
    handler_cls = type('Quiet', (http.server.SimpleHTTPRequestHandler,), {'log_message': lambda *a: None})
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(('127.0.0.1', 0), lambda *a, **k: handler_cls(*a, directory=tmp, **k))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        res = subprocess.run([node, os.path.join(ROOT, 'tests', 'ext_driver.mjs'), chrome, EXT,
                              f'http://127.0.0.1:{port}/page.html',
                              os.path.join(tmp, 'page.png'), '3000',
                              'chrome.storage.sync.set({on: true, keepNames: true, entries: {hu: {trelawny: "trelóni"}}})', 'chrome.storage.sync.set({on: false})',
                              'new Promise(r => chrome.contextMenus.create({id: "say", title: "x", contexts: ["selection"]}, () => r(chrome.runtime.lastError ? chrome.runtime.lastError.message : "created")))'],
                             capture_output=True, text=True, timeout=120)
        assert res.returncode == 0, res.stderr
        before, dom, after, _ = res.stdout.split('\n<<<diafon-step>>>\n')
        assert 'duplicate id' in res.stderr, res.stderr[-400:]          # the selection menu item exists: a second "say" is refused
    finally:
        httpd.shutdown()
    hu = stages.load('hu')
    spelled = stages.render(hu['sample'], hu)
    uni = stages.convert(spelled, 'stage:hu', 'script')
    assert 'data-diafon="loaded"' in before, before[:300]
    assert 'data-diafon-state="off/hu"' in before and f'<h1 id="h">{spelled}</h1>' in before, before[:800]
    assert 'data-diafon-state="on/hu"' in dom, dom[:300]
    assert f'<h1 id="h">{uni}</h1>' in dom, dom[:800]
    assert 'Fojó' in dom and 'juk; SZÉP.' in dom, dom[:800]      # ly read; SZÉP kept as a name (keepNames is on in this step)
    assert f'<title>{stages.convert("Minta", "stage:hu", "script")}</title>' in dom, dom[:400]
    assert f'<code id="c">{spelled}</code>' in dom
    assert f'id="n">{spelled}</span>' in dom
    assert f'<text>{spelled}</text>' in dom or f'>{spelled}</text>' in dom      # svg text left alone
    assert f'<p id="late">{uni} (kéșőbb)</p>' in dom, dom[-600:]
    want = stages.convert('Meeting, like, taxi.', 'stage:hu', 'script')
    assert f'<p id="loan">{want}</p>' in dom, (want, dom[dom.find('id="loan"'):][:120])
    assert f'<p id="name">{stages.convert("Trelóni", "stage:hu", "script")}</p>' in dom, dom[dom.find('id="name"'):][:80]   # the reader's entry
    assert f'<p id="keep">{stages.convert("Sok ", "stage:hu", "script")}Trelawny</p>' in dom, dom[dom.find('id="keep"'):][:80]   # a name kept
    mixed = stages.convert('Meeting ', 'stage:hu', 'script') + '<span lang="en">' + stages.convert('the quick brown fox', 'stage:en', 'script') + '</span>' + stages.convert(' vége.', 'stage:hu', 'script')
    assert f'<p id="mixed">{mixed}</p>' in dom, dom[dom.find('id="mixed"'):][:160]                # an element's own language
    assert '<span lang="de-DE">Die Sprache</span>' in dom                                          # a language with no stage: as written
    assert f'<p id="mut">{stages.convert("szép nyár", "stage:hu", "script")}</p>' in dom, dom[dom.find('id="mut"'):][:80]   # a text node rewritten by script
    assert f'translate="no">{stages.convert("hosszú alma", "stage:hu", "script")}</p>' in dom, dom[dom.find('id="mirror"'):][:80]   # the frame's own document
    assert 'data-diafon-state="off/hu"' in after and f'<h1 id="h">{spelled}</h1>' in after and '<title>Minta</title>' in after, after[:800]
    assert f'<p id="late">{spelled} (később)</p>' in after, after[-600:]
    assert '<p id="name">Trelawny</p>' in after
    assert '<p id="mut">szép nyár</p>' in after and 'translate="no">hosszú alma</p>' in after      # off restores the rewritten node and the frame
    print('Chrome for Testing: off as loaded; on, the page reads in Universal, title and late content too, code, svg and no-translate untouched; off restores it')


if __name__ == '__main__':
    test_convert_text()
    test_page_language()
    test_keep_names()
    test_entries()
    test_chrome()
    test_chrome_late()
