// The Diafon typing in the browser and in Node: one compiled profile
// (spec/diafon-v1.json) in, script text out. No other table is needed: each
// key of the profile carries the letters it writes.
//
//   const keys = DiafonKeys.create(profile)
//   keys.render(typed, {join})   typed text -> script text
//   keys.stream(buffer)          -> [committed script text, pending keys]: what a
//                                keyboard commits, and the last letter still open
//   keys.segments(typed)         -> [{typed, script, letter}]: key by key, for a lesson
//
// The rules are the profile's (see its yaml): the text is cut by longest match
// over the key table; a doubled consonant key is the long letter, and an
// operator after it applies to both; a doubled operator, or one with nothing
// to apply to, is the plain letter; a digit after a letter is its tone, a
// doubled digit the plain digit.
(function (root) {
  'use strict';
  const isDigit = ch => /^\p{Nd}$/u.test(ch);
  const isUpper = ch => ch !== ch.toLowerCase() && ch === ch.toUpperCase();

  function create(profile) {
    const seg = profile.segment;
    const ops = new Set(seg.operators), bases = new Set(seg.bases), doubling = new Set(seg.doubling);
    const keys = profile.keys, tones = !!profile.tones, signs = profile.tone_signs || {};

    function cut(text) {
      const chars = Array.from(text), low = chars.map(c => c.toLowerCase()), n = chars.length, out = [];
      let i = 0;
      while (i < n) {
        const ch = low[i];
        if (!bases.has(ch)) { out.push({ typed: chars[i], raw: chars[i] }); i++; continue; }
        let j = i + 1;
        const double = doubling.has(ch) && j < n && low[j] === ch;
        if (double) j++;
        let key = ch, escaped = null;
        while (j < n && ops.has(low[j])) {
          if (j + 1 < n && low[j + 1] === low[j]) { escaped = chars[j]; break; }
          if (!(key + low[j] in keys)) break;
          key += low[j]; j++;
        }
        let tone = '';
        while (tones && escaped === null && j < n && isDigit(chars[j])) {
          if (j + 1 < n && chars[j + 1] === chars[j]) { escaped = chars[j]; break; }
          tone += chars[j]; j++;
        }
        out.push({ typed: chars.slice(i, j).join(''), key, long: keys[key].long || double, caps: isUpper(chars[i]), tones: tone });
        if (escaped !== null) { out.push({ typed: chars.slice(j, j + 2).join(''), raw: escaped }); j += 2; }
        i = j;
      }
      return out;
    }

    function glyph(s, join) {
      if (s.raw !== undefined) return s.raw;
      const w = keys[s.key].writes;
      let g;
      if (s.long && join && w.joined) g = s.caps ? w.joined_capital : w.joined;
      else if (s.long) g = s.caps ? w.long_capital : w.long;
      else g = s.caps ? w.capital : w.glyph;
      return g + Array.from(s.tones).map(d => (d in signs ? signs[d] : d)).join('');
    }

    const render = (text, opts) => cut(text).map(s => glyph(s, opts && opts.join)).join('');
    function stream(buffer) {
      const segs = cut(buffer);
      const open = segs.length && segs[segs.length - 1].raw === undefined;
      const head = open ? segs.slice(0, -1) : segs;
      return [head.map(s => glyph(s, false)).join(''), open ? segs[segs.length - 1].typed : ''];
    }
    const segments = text => cut(text).map(s => ({ typed: s.typed, script: glyph(s, false), letter: s.raw === undefined }));
    return { render, stream, segments, profile };
  }

  const api = { create };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.DiafonKeys = api;
})(typeof self !== 'undefined' ? self : this);
