// The pinyin table's tools: its size (the table is sized in em, so its font size is its zoom),
// fitting it to the window, the full screen. The download is a plain link to pinyin.pdf.
(() => {
  const card = document.querySelector('.py-card');
  if (!card) return;
  const scroll = card.querySelector('.py-scroll'), table = card.querySelector('table'), shown = card.querySelector('.py-zoom');
  const BASE = 0.7, MIN = 0.3, MAX = 3;          // rem at 100%, and the limits of the zoom
  let zoom = 1;
  const set = z => {
    zoom = Math.min(MAX, Math.max(MIN, z));
    table.style.fontSize = (BASE * zoom) + 'rem';
    shown.textContent = Math.round(zoom * 100) + '%';
  };
  // the zoom at which the table is as wide as its frame; all of it, height too, in the full screen
  const fit = () => {
    set(1);
    const w = scroll.clientWidth / table.offsetWidth, h = scroll.clientHeight / table.offsetHeight;
    set(document.fullscreenElement === card ? Math.min(w, h) : w);
  };
  card.addEventListener('click', e => {
    const what = e.target.dataset && e.target.dataset.py;
    if (what === 'in') set(zoom * 1.15);
    else if (what === 'out') set(zoom / 1.15);
    else if (what === 'fit') fit();
    else if (what === 'full') document.fullscreenElement ? document.exitFullscreen() : card.requestFullscreen && card.requestFullscreen();
  });
  // a pinch on a trackpad, or the wheel with Ctrl or Command, zooms the table and not the page
  scroll.addEventListener('wheel', e => {
    if (!e.ctrlKey && !e.metaKey) return;
    e.preventDefault();
    set(zoom * Math.exp(-e.deltaY / 300));
  }, { passive: false });
  document.addEventListener('fullscreenchange', () => {
    card.querySelector('[data-py=full]').textContent = document.fullscreenElement === card ? 'leave full screen' : 'full screen';
    setTimeout(fit, 60);
  });
  if (!card.requestFullscreen) card.querySelector('[data-py=full]').hidden = true;
  const start = () => { set(1); if (table.offsetWidth > scroll.clientWidth) fit(); };
  (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(start);
})();
