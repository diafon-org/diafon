// Faithful port of src/diaphone/decode.py + render.py's batch conversion.
// Validated against the Python CLI by scripts/check_swift.py — do not "improve" without re-running it.
import Foundation

let VOWELS: Set<Character> = ["a", "e", "i", "o", "u"]

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
    let toks = tokenize(w, labels: orthKeys)
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
        out.append(g)
    }
    let res = out.joined()
    if let tn = tone { return applyTone(res, tone: tn, marks: eng.toneMarks) }
    return res
}

/// render.py universal render: notation -> native/ipa glyphs (trailing digit = tone superscript).
func renderUniversal(_ text: String, target: String, eng: Engine) -> String {
    let m = eng.maps[target] ?? [:]
    let labels = eng.labels(for: target)
    return text.split(separator: " ").map { sub -> String in
        var w = String(sub)
        var tone = ""
        if w.count > 1, let last = w.last, let sup = eng.toneSup[String(last)] {
            tone = sup
            w = String(w.dropLast())
        }
        return tokenize(w, labels: labels).map { m[$0] ?? $0 }.joined() + tone
    }.joined(separator: " ")
}

/// decode.py `decode`: whole text -> a language's spelling.
func decodeText(_ text: String, lang: String, loose: Bool, eng: Engine) -> String {
    let (o, keys) = eng.orthLabels(for: lang, loose: loose)
    return text.split(separator: " ").map {
        decodeWord(String($0), orth: o, orthKeys: keys, lang: lang, eng: eng)
    }.joined(separator: " ")
}
