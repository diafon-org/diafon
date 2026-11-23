// What the Apple input methods ask of the alphabet (diafon-core.js) and the
// typing (diafon-keys.js), as plain functions on plain values, so the Swift
// side (Diafon.swift) passes strings in and takes strings out.
//
// An output is 'script' (Diafon), 'stage:<code>' (a language's spelling) or
// 'transport' (the keys as typed, the escape path).
(function (root) {
  'use strict';
  var core = null, keys = null, signs = [], spec = null;

  root.diafonInit = function (specJson, profileJson) {
    spec = JSON.parse(specJson);
    var profile = JSON.parse(profileJson);
    core = root.DiafonCore.create(spec);
    keys = root.DiafonKeys.create(profile);
    signs = Object.keys(profile.tone_signs || {}).map(function (d) { return profile.tone_signs[d]; }).filter(Boolean);
    return JSON.stringify({
      version: spec.version, typing: profile.id, operators: profile.segment.operators,
      stages: Object.keys(spec.stages).map(function (code) {
        var st = spec.stages[code], lexical = st.state === 'lexical';
        return { code: code, name: st.name, lexical: lexical, sample: st.sample || '' };
      }),
    });
  };

  function toneless(s) { return signs.reduce(function (t, g) { return t.split(g).join(''); }, s); }

  // script text written out: as it is, or in a language's spelling
  function out(script, target, tones) {
    if (!tones) script = toneless(script);
    return target === 'script' ? script : core.convert(script, 'script', target);
  }

  /* What was typed, written out. */
  root.diafonRender = function (typed, target, tones, join) {
    if (target === 'transport') return typed;
    return out(keys.render(typed, { join: join && target === 'script' }), target, tones);
  };

  /* The streaming rule: [what is final, written out; the keys still open].
     A letter stays open while the next key could still change it. Wordwise, for
     a language's spelling, the whole word being typed stays open: a spelling can
     depend on the letter that follows. */
  root.diafonStream = function (buffer, target, tones, join, wordwise) {
    var head, tail;
    if (wordwise) {
      var chars = Array.from(buffer), i = chars.length;
      while (i > 0 && /^[A-Za-z0-9]$/.test(chars[i - 1])) i--;
      head = chars.slice(0, i).join(''); tail = chars.slice(i).join('');
    } else {
      var segs = keys.segments(buffer), open = segs.length > 0 && segs[segs.length - 1].letter;
      head = (open ? segs.slice(0, -1) : segs).map(function (s) { return s.typed; }).join('');
      tail = open ? segs[segs.length - 1].typed : '';
    }
    return [head ? root.diafonRender(head, target, tones, join) : '', tail];
  };

  /* A text read in one source and written in a target ('transport' as a
     source: the keys as typed). */
  root.diafonConvert = function (text, source, target, tones, join) {
    if (source === 'transport') { text = keys.render(text); source = 'script'; }
    if (target === 'transport') target = 'script';
    var r = core.convert(text, source, target, { join: join && target === 'script' });
    return tones ? r : toneless(r);
  };

  /* The keys that type a Diafon text: what to press for it. A long consonant is its
     key with the first letter doubled; a plain y, q or digit after a letter is doubled. */
  var byGlyph = null, byLong = null, ops = null;
  root.diafonKeys = function (script) {
    if (!byGlyph) {
      byGlyph = {}; byLong = {}; ops = keys.profile.segment.operators;
      Object.keys(keys.profile.keys).forEach(function (k) {
        var v = keys.profile.keys[k], m = v.long ? byLong : byGlyph, g = v.long ? v.writes.long : v.writes.glyph;
        if (!(g in m) || k.length < m[g].length) m[g] = k;
      });
    }
    var out = '', letter = false;
    // a digit in a Diafon text is a plain digit (a tone is its sign): the first one after a letter is doubled
    script.split(/([0-9]+)/).forEach(function (part, n) {
      if (n % 2) { out += (letter ? part[0] : '') + part; letter = false; return; }
      core.read(part).forEach(function (t) {
        if (t.raw !== undefined && t.raw !== null) {
          out += letter && ops.indexOf(t.raw.toLowerCase()) >= 0 ? t.raw + t.raw : t.raw;
          letter = false;
          return;
        }
        var one = function (long) { return core.write([{ c: t.c, long: long, caps: false, tones: '' }]); };
        var k = t.long && byLong[one(true)];
        if (!k) { k = byGlyph[one(false)]; if (k && t.long) k = k[0] + k; }
        if (!k) { out += core.write([t]); letter = false; return; }
        out += (t.caps ? k[0].toUpperCase() + k.slice(1) : k) + (t.tones || '');
        letter = !t.tones;                              // after a tone digit, a y, q or digit is plain already
      });
    });
    return out;
  };

  /* The sources a text may be in, best first: [[source, share of its letters read], ...]. */
  root.diafonDetect = function (text, prefer) { return core.detect(text, { prefer: prefer }); };
  root.diafonSourceFor = function (text, target, prefer) { return core.sourceFor(text, target, { prefer: prefer }); };
})(typeof globalThis !== 'undefined' ? globalThis : this);
