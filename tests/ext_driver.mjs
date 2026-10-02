// Drive a headless Chrome that has the extension loaded, over the DevTools
// protocol (no dependencies: Node's own WebSocket). Usage:
//   node tests/ext_driver.mjs <chrome binary> <extension dir> <url> <out.png> [wait ms] [worker expr...]
// Prints the page's outerHTML after the wait; writes the screenshot. Each
// further argument is evaluated in the extension's service worker (its
// background.js), followed by the same wait and the outerHTML again, the
// documents joined by the SEP line.
import {spawn} from 'node:child_process';
import {writeFileSync, readFileSync, mkdtempSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const [chrome, ext, url, png, waitArg, ...steps] = process.argv.slice(2);
export const SEP = '\n<<<diafon-step>>>\n';
const wait = Number(waitArg || 1500);
const port = 9222 + Math.floor(Math.random() * 1000);
const profile = mkdtempSync(join(tmpdir(), 'diafon-ext-'));
const proc = spawn(chrome, ['--headless=new', '--disable-gpu', '--no-first-run', `--user-data-dir=${profile}`,
  `--load-extension=${ext}`, `--remote-debugging-port=${port}`, '--window-size=900,480', 'about:blank'], {stdio: 'ignore'});
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function targets(type){
  for (let i = 0; i < 100; i++){
    try {
      const list = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).filter(t => t.type === type);
      if (list.length) return list;
    } catch {}
    await sleep(200);
  }
  throw new Error(`no ${type} target`);
}
async function connect(t){
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise(r => ws.onopen = r);
  let id = 0; const pend = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m.result || m.error); delete pend[m.id]; } };
  const send = (method, params = {}) => new Promise(r => { pend[++id] = r; ws.send(JSON.stringify({id, method, params})); });
  return {ws, send};
}
const page = await connect((await targets('page'))[0]);
await page.send('Page.enable'); await page.send('Runtime.enable');
await page.send('Page.navigate', {url});
await sleep(wait);
const html = async () => (await page.send('Runtime.evaluate', {expression: 'document.documentElement.outerHTML', returnByValue: true})).result.value;
const out = [await html()];
if (steps.length){
  // the extension's own worker, among Chrome's built-in extensions' workers: the one whose manifest is ours
  const manifest = JSON.parse(readFileSync(join(ext, 'manifest.json'), 'utf8'));
  let worker = null;
  for (const t of await targets('service_worker')){
    const w = await connect(t);
    const r = await w.send('Runtime.evaluate', {expression: 'chrome.runtime.getManifest().name', returnByValue: true});
    if (r.result && r.result.value === manifest.name){ worker = w; break; }
    w.ws.close();
  }
  if (!worker) throw new Error('the extension has no service worker running');
  for (const expr of steps){
    const r = await worker.send('Runtime.evaluate', {expression: expr, awaitPromise: true});
    console.error('step', JSON.stringify(r.result && r.result.value !== undefined ? r.result.value : r));
    await sleep(wait);
    out.push(await html());
  }
  worker.ws.close();
}
const shot = await page.send('Page.captureScreenshot', {format: 'png'});
if (png && shot.data) writeFileSync(png, Buffer.from(shot.data, 'base64'));
process.stdout.write(out.join(SEP));
page.ws.close(); proc.kill();
