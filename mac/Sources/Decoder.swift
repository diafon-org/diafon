// Faithful port of src/diaphone/decode.py + render.py's batch conversion.
// Validated against the Python CLI by scripts/check_swift.py — do not "improve" without re-running it.
import Foundation

let VOWELS: Set<Character> = ["a", "e", "i", "o", "u"]

/// Capitalise the first character (combining marks ride along).
func capFirst(_ s: String) -> String {
    guard let f = s.first else { return s }
    return String(f).uppercased() + s.dropFirst()
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

/// decode.py `decode_word`: one word of notation -> one word of a language's spelling.
func decodeWord(_ word: String, orth: [String: String], orthKeys: [String], lang: String, eng: Engine) -> String {
    var w = word
    var tone: Int? = nil
    if lang == "zh", w.count > 1, let last = w.last, let d = last.wholeNumberValue, last.isNumber, d <= 5 {
        tone = d
        w = String(w.dropLast())
    }
    let (toks, caps) = tokenizeCased(w, labels: orthKeys)
    var out: [String] = []
    for (k, t) in toks.enumerated() {
        let nxt: String? = k + 1 < toks.count ? toks[k + 1] : nil
        let prv: String? = k > 0 ? toks[k - 1] : nil
        if t == "w", !out.isEmpty {                       // long: geminate the previous grapheme
            out[out.count - 1] = String(out[out.count - 1].first!) + out[out.count - 1]
            continue
        }
        var g = orth[t] ?? t
        if lang == "hu", t == "i", let n = nxt, let f = n.first, VOWELS.contains(f) {
            g = "j"                                       // i-glide onset -> j (iow -> jó)
        } else if lang == "zh" {
            if let pair = eng.zhRetro[t] {
                g = (nxt == "i" || nxt == "ic") ? pair[1] : pair[0]   // j/q/x before front i/ü, else zh/ch/sh
            } else if t == "ic", let p = prv, eng.zhRetro[p] != nil {
                g = "u"                                   // ü written u after j/q/x
            } else if t == "i", k == 0, let n = nxt, let f = n.first, VOWELS.contains(f) {
                g = "y"                                   // i-glide onset -> y-
            } else if t == "u", prv == "a" {
                g = "o"                                   // -u offglide spells o only after a (au -> ao)
            }
        }
        out.append(caps[k] ? capFirst(g) : g)
    }
    let res = out.joined()
    if let tn = tone { return applyTone(res, tone: tn, marks: eng.toneMarks) }
    return res
}

/// render.py universal render: notation -> native/ipa glyphs (trailing digit = tone superscript).
func renderUniversal(_ text: String, target: String, eng: Engine) -> String {
    let m = eng.maps[target] ?? [:]
    let labels = eng.labels(for: target)
    let useCaps = target != "ipa"                        // IPA has no capitals
    return text.split(separator: " ").map { sub -> String in
        var w = String(sub)
        var tone = ""
        if w.count > 1, let last = w.last, let sup = eng.toneSup[String(last)] {
            tone = sup
            w = String(w.dropLast())
        }
        let (toks, caps) = tokenizeCased(w, labels: labels)
        return zip(toks, caps).map { t, c in
            let g = m[t] ?? t
            return (useCaps && c) ? capFirst(g) : g
        }.joined() + tone
    }.joined(separator: " ")
}

/// The EN dictionary view: canonicalise the typed word (aliases -> labels), look it up.
func enDictLookup(_ word: String, orthKeys: [String], eng: Engine) -> String? {
    let key = tokenize(word.lowercased(), labels: orthKeys).map { eng.enCanon[$0] ?? $0 }.joined()
    return eng.enDict[key]
}

/// decode.py `decode`: whole text -> a language's spelling. endict (EN only) = the dictionary view.
func decodeText(_ text: String, lang: String, loose: Bool, endict: Bool = false, eng: Engine) -> String {
    let useDict = endict && lang == "en"
    let (o, keys) = eng.orthLabels(for: lang, loose: loose || useDict)
    return text.split(separator: " ").map { sub -> String in
        let w = String(sub)
        if useDict, let real = enDictLookup(w, orthKeys: keys, eng: eng) {
            return (w.first?.isUppercase ?? false) ? capFirst(real) : real
        }
        return decodeWord(w, orth: o, orthKeys: keys, lang: lang, eng: eng)
    }.joined(separator: " ")
}
