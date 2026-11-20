// Input profiles: what keys produce which points (spec/<id>.json, compiled
// into SpecData.profiles). The core holds a text in universal-v1 forms, so a
// profile's work here is to turn what was typed into those forms; from there
// the engine, the stages and the lexicons go on as before.
//
// universal-v1 is the grammar the engine carries: its keys are the forms.
// A key-table profile (minimal-hu-v1) cuts a word by its key table:
//   - a doubled consonant key is the long point, and an operator after it
//     applies to both (ssy);
//   - a doubled operator is the plain letter (syy is sy), and so is an
//     operator with nothing to apply to (you, my, quick);
//   - a word whose syllables each end in a tone digit is pinyin; any other
//     word with a digit stays as typed;
//   - the word stays composing until its end.
// A plain letter or digit must not be read again as a universal-v1 form, so
// it travels as a private-use character (U+E000 + its code) and comes back as
// itself once the text is rendered (unescape).
import Foundation

enum Profiles {
    static let fallback = "universal-v1"
    static var all: [ProfileData] { SpecData.profileOrder.compactMap { SpecData.profiles[$0] } }
    static func get(_ id: String) -> ProfileData { SpecData.profiles[id] ?? SpecData.profiles[fallback]! }

    private static let base: UInt32 = 0xE000
    private static func literal(_ c: Character) -> String {
        guard let a = c.asciiValue, let u = Unicode.Scalar(base + UInt32(a)) else { return String(c) }
        return String(Character(u))
    }
    /// The plain letters and digits back as themselves.
    static func unescape(_ s: String) -> String {
        guard s.unicodeScalars.contains(where: { $0.value >= base && $0.value < base + 128 }) else { return s }
        var v = String.UnicodeScalarView()
        for u in s.unicodeScalars {
            if u.value >= base, u.value < base + 128, let a = Unicode.Scalar(u.value - base) { v.append(a) } else { v.append(u) }
        }
        return String(v)
    }

    private static func alnum(_ c: Character) -> Bool { c.isASCII && (c.isLetter || c.isNumber) }
    private static func lower(_ c: Character) -> Character { Character(String(c).lowercased()) }
    private static func cap(_ form: String) -> String { form.prefix(1).uppercased() + form.dropFirst() }

    /// What was typed, in universal-v1 forms (plain letters escaped).
    static func transport(_ typed: String, _ p: ProfileData) -> String {
        guard p.table else { return typed }
        var out = "", word: [Character] = []
        func flush() {
            guard !word.isEmpty else { return }
            if word.contains(where: { $0.isNumber }) {
                out += pinyin(word, p) ?? word.map(literal).joined()
            } else {
                out += letters(word, p)
            }
            word = []
        }
        for ch in typed {
            if alnum(ch) { word.append(ch) } else { flush(); out.append(ch) }
        }
        flush()
        return out
    }

    /// A word without digits, by the key table.
    private static func letters(_ word: [Character], _ p: ProfileData) -> String {
        var out = ""
        let low = word.map(lower)
        var i = 0
        let n = word.count
        while i < n {
            let ch = low[i]
            if !p.bases.contains(ch) { out += literal(word[i]); i += 1; continue }   // an operator with nothing to apply to
            var j = i + 1
            let double = p.doubling.contains(ch) && j < n && low[j] == ch
            if double { j += 1 }
            var key = String(ch)
            var escaped: Character? = nil
            while j < n, p.operators.contains(low[j]) {
                if j + 1 < n, low[j + 1] == low[j] { escaped = word[j]; j += 2; break }   // a doubled operator: the plain letter
                if p.keys[key + String(low[j])] == nil { break }
                key.append(low[j])
                j += 1
            }
            var form = p.keys[key] ?? String(ch)
            if double { form += "w" }
            out += word[i].isUppercase ? cap(form) : form
            if let e = escaped { out += literal(e) }
            i = j
        }
        return out
    }

    /// A word of pinyin (every syllable ends in a tone digit), or nil when it is not one.
    private static func pinyin(_ word: [Character], _ p: ProfileData) -> String? {
        guard !p.syllables.isEmpty else { return nil }
        var out = ""
        var i = 0
        let n = word.count
        while i < n {
            var j = i
            while j < n, word[j].isLetter { j += 1 }
            guard j > i, j < n, p.pinyinTones.contains(word[j]) else { return nil }
            var syl = String(word[i..<j]).lowercased()
            if let v = p.uUmlaut { syl = syl.replacingOccurrences(of: String(v), with: "ü") }
            guard let form = p.syllables[syl] else { return nil }
            out += word[i].isUppercase ? cap(form) : form
            if word[j] != p.neutral { out.append(word[j]) }
            i = j + 1
        }
        return out
    }

    /// One Mandarin syllable as typed in the candidate window's mode: a key-table
    /// profile types it as pinyin, the tone digit optional (none is the neutral tone).
    static func syllable(_ typed: String, _ p: ProfileData) -> String {
        guard p.table else { return typed }
        guard let neutral = p.neutral else { return unescape(transport(typed, p)) }
        let toned = typed.last.map { $0.isNumber } ?? false
        return unescape(transport(toned ? typed : typed + String(neutral), p))
    }

    /// The streaming commit rule under a profile: (committed, pending). `renderer`
    /// takes what was typed (Prefs.renderer reads it through the profile). A profile
    /// that commits by the word keeps the word being typed pending.
    static func stream(_ buffer: String, _ p: ProfileData, renderer: (String) -> String, wordwise: Bool = false) -> (String, String) {
        guard p.table else { return Engine.stream(buffer, renderer: renderer, wordwise: wordwise) }
        let chars = Array(buffer)
        var i = chars.count
        while i > 0, alnum(chars[i - 1]) { i -= 1 }
        return (i == 0 ? "" : renderer(String(chars[..<i])), String(chars[i...]))
    }
}
