// Faithful port of src/diaphone/decode.py + render.py's batch conversion.
// Validated against the Python CLI by scripts/check_swift.py — do not "improve" without re-running it.
import Foundation

let VOWELS: Set<Character> = ["a", "e", "i", "o", "u"]

/// Capitalise the first character that HAS a capital (combining marks ride along). A glyph with
/// none — the apostrophe /ʔ/ — comes back unchanged, and the caller passes the capital to the next
/// glyph: 'Alif, not 'alif. Mirrors decode.py `_cap` / `apply_cap`.
func capFirst(_ s: String) -> String {
    for (i, ch) in s.enumerated() where String(ch).uppercased() != String(ch) {
        let idx = s.index(s.startIndex, offsetBy: i)
        return String(s[s.startIndex..<idx]) + String(ch).uppercased() + String(s[s.index(after: idx)...])
    }
    return s
}

/// Case-insensitive tokenize: (lowercase tokens, per-token was-capitalised flags).
func tokenizeCased(_ word: String, labels: [String]) -> ([String], [Bool]) {
    let toks = tokenize(word.lowercased(), labels: labels)
    var caps: [Bool] = []
    var i = word.startIndex
    for t in toks {
        caps.append(word[i].isUppercase)
        i = word.index(i, offsetBy: t.count)
    }
    return (toks, caps)
}

/// Greedy longest-match split of a word into known labels (labels must be sorted longest-first).
func tokenize(_ word: String, labels: [String]) -> [String] {
    var toks: [String] = []
    var s = Substring(word)
    while !s.isEmpty {
        var matched = false
        for L in labels where s.hasPrefix(L) {
            toks.append(L)
            s = s.dropFirst(L.count)
            matched = true
            break
        }
        if !matched {
            toks.append(String(s.first!))
            s = s.dropFirst()
        }
    }
    return toks
}

/// Pinyin tone placement: a > e > ou > last vowel. Tones 0/5 = neutral, no mark.
func applyTone(_ py: String, tone: Int, marks: [String: String]) -> String {
    if tone == 0 || tone == 5 { return py }
    let chars = Array(py)
    func put(_ i: Int) -> String {
        let marked = Array(marks[String(chars[i])]!)[tone - 1]
        return String(chars[0..<i]) + String(marked) + String(chars[(i + 1)...])
    }
    if let i = chars.firstIndex(of: "a") { return put(i) }
    if let i = chars.firstIndex(of: "e") { return put(i) }
    for i in 0..<max(chars.count - 1, 0) where chars[i] == "o" && chars[i + 1] == "u" { return put(i) }
    for i in stride(from: chars.count - 1, through: 0, by: -1) where marks[String(chars[i])] != nil {
        return put(i)
    }
    return py
}

/// decode.py `_rule_grapheme`: first matching context rule's grapheme, or nil.
func ruleGrapheme(_ rules: [Rule], t: String, prv: String?, nxt: String?, k: Int) -> String? {
    for r in rules {
        if r.t != t { continue }
        if let nx = r.next { guard let n = nxt, nx.contains(n) else { continue } }
        if r.next_vowel == true {
            guard let n = nxt, let f = n.first, VOWELS.contains(f) else { continue }
        }
        if let pv = r.prev { guard let p = prv, pv.contains(p) else { continue } }
        if r.first == true, k != 0 { continue }
        return r.g
    }
    return nil
}

/// decode.py `decode_word`: one word of notation -> one word of a language's spelling.
/// Assembly rules are DATA (eng.rules[lang]); only `w`-gemination and the tone digit stay code.
func decodeWord(_ word: String, orth: [String: String], orthKeys: [String], lang: String, eng: Engine) -> String {
    var w = word
    var tone: Int? = nil
    if lang == "zh", w.count > 1, let last = w.last, let d = last.wholeNumberValue, last.isNumber, d <= 5 {
        tone = d
        w = String(w.dropLast())
    }
    let rules = eng.rules[lang] ?? []
    let (toks, caps) = tokenizeCased(w, labels: orthKeys)
    let shout = w == w.uppercased() && w != w.lowercased()   // ALL-CAPS uppercases whole graphemes
    var out: [String] = []
    var pending = false                                   // a capital no caseless glyph could take
    for (k, t) in toks.enumerated() {
        let nxt: String? = k + 1 < toks.count ? toks[k + 1] : nil
        let prv: String? = k > 0 ? toks[k - 1] : nil
        if t == "w", !out.isEmpty {                       // long: geminate the previous grapheme
            out[out.count - 1] = String(out[out.count - 1].first!) + out[out.count - 1]
            continue
        }
        let g = ruleGrapheme(rules, t: t, prv: prv, nxt: nxt, k: k) ?? (orth[t] ?? t)
        if caps[k] || pending {
            let c = shout ? g.uppercased() : capFirst(g)
            pending = (c == g)
            out.append(c)
        } else {
            out.append(g)
        }
    }
    let res = out.joined()
    if let tn = tone { return applyTone(res, tone: tn, marks: eng.toneMarks) }
    return res
}

/// Tone-sign placement (native.py `_tone_sign`): within the LAST vowel group, mark the first
/// a-based token, else the first e-based, else the first o-based, else the LAST vowel (= Pinyin
/// placement); 0/5 = neutral (digit consumed); vowelless segment / unmapped digit keeps the digit.
/// Returns the trailing string to append after the glyphs ("" when the sign landed or was neutral).
func applyToneSign(_ glyphs: inout [String], toks: [String], digit: String,
                   signs: [String: String]) -> String {
    if digit == "0" || digit == "5" { return "" }
    guard let mark = signs[digit] else { return digit }
    func isV(_ t: String) -> Bool { t.first.map { "aeiou".contains($0) } ?? false }
    var group: [Int] = []                                    // indices of the LAST vowel group
    for (i, t) in toks.enumerated() where isV(t) {
        if let last = group.last, last == i - 1 { group.append(i) } else { group = [i] }
    }
    guard var pick = group.last else { return digit }
    outer: for base in ["a", "e", "o"] {
        for i in group where toks[i].hasPrefix(base) { pick = i; break outer }
    }
    glyphs[pick] = (glyphs[pick] + mark).precomposedStringWithCanonicalMapping
    return ""
}

/// render.py universal render: notation -> uni/ipa glyphs. Tone digits go superscript in IPA
/// ONLY; uni keeps the plain digit — or, with tone signs on (opt-in), the digit becomes a tone
/// sign on the vowel (never an upper-index character).
func renderUniversal(_ text: String, target: String, eng: Engine, tones: Bool = false) -> String {
    let m = eng.maps[target] ?? [:]
    let labels = eng.labels(for: target)
    let useCaps = target != "ipa"                        // IPA has no capitals
    let useSup = target == "ipa"
    let useTones = tones && !useSup
    let signs = eng.toneSigns
    func segParts(_ seg: String) -> (toks: [String], glyphs: [String]) {
        let (toks, caps) = tokenizeCased(seg, labels: labels)
        // an ALL-CAPS segment uppercases whole glyphs (TW -> TT, not Tt)
        let shout = seg == seg.uppercased() && seg != seg.lowercased()
        var pending = false                              // a caseless glyph passes the capital along
        let glyphs = zip(toks, caps).map { t, c -> String in
            let g = m[t] ?? t
            guard useCaps, c || pending else { return g }
            let cap = shout ? g.uppercased() : capFirst(g)
            pending = (cap == g)
            return cap
        }
        return (toks, glyphs)
    }
    return text.split(separator: " ").map { sub -> String in
        var piece = "", seg = ""
        for ch in sub {                 // a tone digit closes its segment anywhere in the word
            if ch == "0" || eng.toneSup[String(ch)] != nil {
                var (toks, glyphs) = segParts(seg)
                if useSup {
                    piece += glyphs.joined() + (eng.toneSup[String(ch)] ?? String(ch))
                } else if useTones {
                    let trail = applyToneSign(&glyphs, toks: toks, digit: String(ch), signs: signs)
                    piece += glyphs.joined() + trail
                } else {
                    piece += glyphs.joined() + String(ch)
                }
                seg = ""
            } else {
                seg.append(ch)
            }
        }
        return piece + segParts(seg).glyphs.joined()
    }.joined(separator: " ")
}

/// decode.py `decode`: whole text -> a language's spelling.
func decodeText(_ text: String, lang: String, loose: Bool, eng: Engine) -> String {
    let (o, keys) = eng.orthLabels(for: lang, loose: loose)
    return text.split(separator: " ").map { sub -> String in
        let w = String(sub)
        if lang == "zh" {               // any digit closes a syllable, mid-word too (zhong1guo2)
            var piece = "", seg = ""
            for ch in w {
                if ch.isNumber {
                    piece += decodeWord(seg + String(ch), orth: o, orthKeys: keys, lang: lang, eng: eng)
                    seg = ""
                } else {
                    seg.append(ch)
                }
            }
            return piece + (seg.isEmpty ? "" : decodeWord(seg, orth: o, orthKeys: keys, lang: lang, eng: eng))
        }
        return decodeWord(w, orth: o, orthKeys: keys, lang: lang, eng: eng)
    }.joined(separator: " ")
}

