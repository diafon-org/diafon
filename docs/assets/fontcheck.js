// The font check on the Tools page: every Diafon letter in use, small and capital, in a
// grid set in the chosen font, each probed for a missing mark or another font stepping
// in. Only the grid changes font. The letters come from the alphabet's spec (alphabet-spec.json).
(function(){
'use strict';
const $ = id => document.getElementById(id);
const $font = $('fc-font'), $custom = $('fc-custom'), $summary = $('fc-summary'), $grid = $('fc-grid');
const esc = s => s.replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));

let spans = [];

const GENERIC = /^(serif|sans-serif|monospace|system-ui)$/;
function family(){ return $custom.value.trim() || $font.value; }
function cssFamily(f){ return GENERIC.test(f) ? f : JSON.stringify(f); }
const cv = document.createElement('canvas');
cv.width = cv.height = 72;
const cx = cv.getContext('2d', {willReadFrequently: true});
function pixels(text, fam){
  cx.clearRect(0, 0, 72, 72);
  cx.font = '40px ' + fam;
  cx.textBaseline = 'middle';
  cx.fillText(text, 6, 40);
  return cx.getImageData(0, 0, 72, 72).data;
}
function same(a, b){
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}
// fell: another font stepped in for the letter or for its mark alone (the glyph
// draws differently over two different fallbacks); missing: the marked letter
// draws exactly like its bare base
function probe(g, fam){
  const q = cssFamily(fam);
  const fell = !same(pixels(g, q + ', monospace'), pixels(g, q + ', serif'));
  const bare = g.normalize('NFD').replace(/[̀-ͯ]/g, '');
  const missing = bare !== g.normalize('NFD') && same(pixels(g, q + ', serif'), pixels(bare, q + ', serif'));
  return {fell, missing};
}
let run = 0;
function check(){
  const fam = family(), mine = ++run;
  $grid.style.fontFamily = cssFamily(fam) + ', var(--serif)';
  const go = () => {
    if (mine !== run) return;
    let miss = 0, fall = 0;
    for (const s of spans){
      const p = probe(s.textContent, fam);
      s.classList.toggle('miss', p.missing);
      s.classList.toggle('fall', !p.missing && p.fell);
      if (p.missing) miss++; else if (p.fell) fall++;
    }
    $summary.innerHTML = `${spans.length} letters` +
      (miss ? ` · <span class="miss">${miss} marks missing</span>` : '') +
      (fall ? ` · <span class="fall">${fall} falling back</span>` : '') +
      (!miss && !fall ? ' · all drawn by this font' : '');
  };
  if (document.fonts && !GENERIC.test(fam)) document.fonts.load('40px ' + cssFamily(fam), 'aș').then(go, go);
  else go();
}
$font.addEventListener('change', () => { $custom.value = ''; check(); });
$custom.addEventListener('change', check);
// the letters: each point in use, small and capital, once each
fetch(new URL('../alphabet-spec.json', document.currentScript ? document.currentScript.src : location.href))
  .then(r => r.json()).then(spec => {
    const letters = [];
    for (const p of spec.points) if (!p.long) for (const g of [p.glyph, p.capital]) if (!letters.includes(g)) letters.push(g);
    $grid.innerHTML = letters.map(g => `<span>${esc(g)}</span>`).join('');
    spans = [...$grid.children];
    check();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(check);
  });
})();
