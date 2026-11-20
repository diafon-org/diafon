// Input profiles: what keys produce which points (spec/<id>.json, compiled
// into SpecData.profiles). The core holds a text in universal-v1 forms, so a
// profile's work here is to turn what was typed into those forms; from there
// the engine, the stages and the lexicons go on as before.
//
// universal-v1 is the grammar the engine carries: its keys are the forms.
// A key-table profile (minimal-hu-v1) cuts the text by its key table:
//   - a doubled consonant key is the long point, and an operator after it
//     applies to both (ssy);
//   - a doubled operator is the plain letter (syy is sy), and so is an
//     operator with nothing to apply to (you, my, quick);
//   - a digit after a point is its tone, a doubled digit the plain digit (h22o);
//   - a segment commits when the next one starts.
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

    /// What was typed, cut by the key table: each segment as typed, in universal-v1
    /// forms (plain letters and digits escaped), and whether it is a point.
    static func segments(_ typed: String, _ p: ProfileData) -> [(src: String, out: String, point: Bool)] {
        let text = Array(typed)
        let low = text.map { $0.isASCII ? lower($0) : $0 }
        var out: [(src: String, out: String, point: Bool)] = []
        var i = 0
        let n = text.count
        while i < n {
            let ch = low[i]
            if !p.bases.contains(ch) {                      // an operator with nothing to apply to, a digit, anything else
                out.append((String(text[i]), alnum(text[i]) ? literal(text[i]) : String(text[i]), false))
                i += 1
                continue
            }
            var j = i + 1
            let double = p.doubling.contains(ch) && j < n && low[j] == ch
            if double { j += 1 }
            var key = String(ch)
            var escaped: Character? = nil
            while j < n, p.operators.contains(low[j]) {
                if j + 1 < n, low[j + 1] == low[j] { escaped = text[j]; break }   // a doubled operator: the plain letter
                if p.keys[key + String(low[j])] == nil { break }
                key.append(low[j])
                j += 1
            }
            var form = p.keys[key] ?? String(ch)
            if double { form += "w" }
            if text[i].isUppercase { form = cap(form) }
            while p.tones, escaped == nil, j < n, text[j].isASCII, text[j].isNumber {
                if j + 1 < n, text[j + 1] == text[j] { escaped = text[j]; break }     // a doubled digit: the plain digit
                form.append(text[j]); j += 1
            }
            out.append((String(text[i..<j]), form, true))
            if let e = escaped {
                out.append((String(text[j..<j + 2]), literal(e), false))
                j += 2
            }
            i = j
        }
        return out
    }

    /// What was typed, in universal-v1 forms (plain letters and digits escaped).
    static func transport(_ typed: String, _ p: ProfileData) -> String {
        guard p.table else { return typed }
        return segments(typed, p).map { $0.out }.joined()
    }

    /// One Mandarin syllable as typed, in universal-v1 forms (the candidate window's mode).
    static func syllable(_ typed: String, _ p: ProfileData) -> String { unescape(transport(typed, p)) }

    /// The streaming commit rule under a profile: (committed, pending). `renderer`
    /// takes what was typed (Prefs.renderer reads it through the profile). A last
    /// segment that is a point may still grow (a doubling, an operator, a tone), so
    /// it stays pending; wordwise, for a language's spelling, the whole word does.
    static func stream(_ buffer: String, _ p: ProfileData, renderer: (String) -> String, wordwise: Bool = false) -> (String, String) {
        guard p.table else { return Engine.stream(buffer, renderer: renderer, wordwise: wordwise) }
        if wordwise {
            let chars = Array(buffer)
            var i = chars.count
            while i > 0, alnum(chars[i - 1]) { i -= 1 }
            return (i == 0 ? "" : renderer(String(chars[..<i])), String(chars[i...]))
        }
        let segs = segments(buffer, p)
        guard let last = segs.last, last.point else { return (buffer.isEmpty ? "" : renderer(buffer), "") }
        let head = segs.dropLast().map { $0.src }.joined()
        return (head.isEmpty ? "" : renderer(head), last.src)
    }
}
