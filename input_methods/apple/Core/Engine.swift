// The engine, ported rule for rule from scripts/engine.py (and the Kotlin
// port); tables come from SpecData.swift (generated from docs/spec.json).
// tests/test_swift.py replays every spec vector through this file; run it
// after any change here.
//
// Strings are handled as sequences of Unicode scalars, not Swift Characters:
// a letter plus its combining mark is one Character to Swift but two code
// points to the engine, and the engine's rules speak in code points.
import Foundation

struct ParseError: Error { let message: String }

/// One segment of typed text: a form (base letter + operators + tones), a
/// raw character outside the alphabet, or an ill-formed chunk.
enum Seg {
    case raw(String)
    case err(String)
    case form(src: String, form: String, tones: String)

    var src: String {
        switch self {
        case .raw(let s), .err(let s): return s
        case .form(let s, _, _): return s
        }
    }
    var isForm: Bool { if case .form = self { return true } else { return false } }
}

enum Engine {
    static let cBases: Set<Character> = Set("bdfghklmnprstvz")
    static let vBases: Set<Character> = Set("aeiou")
    static let bases: Set<Character> = cBases.union(vBases)
    static let ops: Set<Character> = Set("cjqxwy")

    private static let whole = SpecData.whole
    private static let marks = SpecData.marks
    private static let desc = SpecData.descenders
    private static let partner = SpecData.partner
    private static let belows: [Unicode.Scalar] = marks.values.compactMap { $0.below?.unicodeScalars.first }

    static func nfc(_ s: String) -> String { s.precomposedStringWithCanonicalMapping }

    // scalar helpers: the engine's view of a string
    private static func scalars(_ s: String) -> [Unicode.Scalar] { Array(s.unicodeScalars) }
    private static func string(_ u: [Unicode.Scalar]) -> String { var v = String.UnicodeScalarView(); v.append(contentsOf: u); return String(v) }
    private static func has(_ g: String, _ m: String?) -> Bool {
        guard let m = m, let u = m.unicodeScalars.first else { return false }
        return g.unicodeScalars.contains(u)
    }
    private static func replace(_ g: String, _ a: String, _ b: String) -> String {
        guard let ua = a.unicodeScalars.first, let ub = b.unicodeScalars.first else { return g }
        return string(scalars(g).map { $0 == ua ? ub : $0 })
    }
    private static func lower(_ c: Character) -> Character { Character(String(c).lowercased()) }
    private static func isDigit(_ c: Character) -> Bool { c.isASCII && c.isNumber }
    /// the script's tone signs for a run of tone digits (a digit outside the table stays a digit)
    static func toneSigns(_ digits: String) -> String { digits.map { SpecData.tones[$0] ?? String($0) }.joined() }

    /// Segmentation: greedy, left to right. strict throws on ill-formed input
    /// (the reference reading); lenient marks it .err and goes on (the
    /// input-method reading: such text passes through as typed).
    static func segments(_ text: String, strict: Bool = true) throws -> [Seg] {
        // code points, not grapheme clusters: a stray combining mark is one raw segment
        let chars: [Character] = text.unicodeScalars.map { Character($0) }
        var out: [Seg] = []
        var i = 0
        let n = chars.count
        while i < n {
            let raw = chars[i]
            let ch = lower(raw)
            if !bases.contains(ch) {
                if ops.contains(ch) || isDigit(ch) {
                    if strict { throw ParseError(message: "position \(i): '\(raw)' cannot start a segment") }
                    out.append(.err(String(raw)))
                } else { out.append(.raw(String(raw))) }
                i += 1
                continue
            }
            var j = i + 1
            var opsS = ""
            while j < n, ops.contains(lower(chars[j])) { opsS.append(lower(chars[j])); j += 1 }
            let w = opsS.contains("w")
            let core = opsS.replacingOccurrences(of: "w", with: "")
            var bad: String? = nil
            let srcSoFar = String(chars[i..<j])
            if core.count > 2 { bad = "\(srcSoFar): more than two operators" }
            else if opsS.filter({ $0 == "w" }).count > 1 || (w && !opsS.hasSuffix("w")) { bad = "\(srcSoFar): w must come last, once" }
            var tones = ""
            while j < n, isDigit(chars[j]) { tones.append(chars[j]); j += 1 }
            let src = String(chars[i..<j])
            if let bad = bad {
                if strict { throw ParseError(message: bad) }
                out.append(.err(src))
            } else {
                out.append(.form(src: src, form: String(raw) + core + (w ? "w" : ""), tones: tones))
            }
            i = j
        }
        return out
    }

    private static func hasBelow(_ g: String) -> Bool { g.unicodeScalars.contains { belows.contains($0) } }

    /// Attach a mark by the float rule and one-per-side: below unless the
    /// rendered letter has a descender (capitals never do).
    private static func mark(_ g: String, _ base: Character, _ kind: String, _ caps: Bool) -> String {
        let m = marks[kind]!
        if let below = m.below, caps || !desc.contains(base), !hasBelow(g) { return g + below }
        if let above = m.above { return g + above }
        return g + (m.below ?? "")
    }

    /// Script glyph of one form; an uppercase base letter capitalizes it, and
    /// the float rule reads the capital's own shape.
    static func glyph(_ formIn: String) throws -> String {
        let first = formIn.first!
        let caps = first.isUppercase
        let form = caps ? String(lower(first)) + String(formIn.dropFirst()) : formIn
        let w = form.hasSuffix("w")
        let core = w ? String(form.dropLast()) : form
        let base = core.first!
        let longVowel = w && vBases.contains(base) && whole[core] == nil
        func compose(_ cap: Bool) throws -> String {
            var g = try composeCore(core, cap)
            if longVowel {
                let flip = marks["flip"]!.above!
                g = has(g, flip) ? replace(g, flip, marks["double_acute"]!.above!) : g + marks["acute"]!.above!
            }
            return nfc(g)
        }
        var g = try compose(caps)
        if w && !longVowel { g += g }                         // long consonant doubles its letter
        g = nfc(g)
        if caps {
            let u = scalars(g)
            g = nfc(string([u[0]]).uppercased() + string(Array(u.dropFirst())))
        }
        return g
    }

    /// The composed glyph of a core form (no length): marks as combining characters.
    private static func composeCore(_ core: String, _ caps: Bool) throws -> String {
        let base = core.first!
        let opsS = String(core.dropFirst())
        if let g = whole[core] { return g }
        if core.count == 3, let g0 = whole[String(core.prefix(2))] {
            var g = g0
            let gBase = g.first!
            switch Array(core)[2] {
            case "x":                                         // the dot on an unmarked whole letter
                if hasBelow(g) { throw ParseError(message: "\(core): the dot cannot stack on a marked form") }
                g = mark(g, gBase, "dot", caps)
            case "y":
                let a = marks["anchor"]!.below!
                if has(g, a) { g = replace(g, a, marks["reverse"]!.below!) }   // y flips the anchored affricate
                else { throw ParseError(message: "\(core): y flips only an anchor") }
            default:
                throw ParseError(message: "\(core): \(Array(core)[2]) cannot be secondary")
            }
            return g
        }
        if vBases.contains(base) { return try vowel(base, opsS) }
        return try consonant(base, opsS, caps)
    }

    private static func consonant(_ base: Character, _ opsS: String, _ caps: Bool) throws -> String {
        var g = String(base)
        if opsS.isEmpty { return g }
        let o = Array(opsS)
        let op1 = o[0]
        if op1 == "y" && "lrf".contains(base) { throw ParseError(message: "\(base)\(opsS): no reverse anchor on the thin stems l r f") }
        switch op1 {
        case "j": g = mark(g, base, "anchor", caps)
        case "x": g = mark(g, base, "dot", caps)
        case "y": g = mark(g, base, "reverse", caps)
        case "c": g = mark(g, base, "dot", caps)             // the tap rc; other affricates are whole letters
        case "q": throw ParseError(message: "\(base)\(opsS): no such form")
        default: break
        }
        if o.count == 1 { return g }
        let op2 = o[1]
        if op2 == "x" { throw ParseError(message: "\(base)\(opsS): x cannot follow \(op1)") }
        if op2 == "y" {
            if op1 == "j" && "sz".contains(base) {                        // y flips the anchored hush
                return replace(g, marks["anchor"]!.below!, marks["reverse"]!.below!)
            }
            throw ParseError(message: "\(base)\(opsS): y flips only the anchor on s z")
        }
        throw ParseError(message: "\(base)\(opsS): \(op2) cannot be secondary")
    }

    private static func vowel(_ base: Character, _ opsS: String) throws -> String {
        var g = String(base)
        for op in opsS {
            switch op {
            case "c": g = String(partner[base]!) + marks["flip"]!.above!
            case "j": g += marks["underdot"]!.below!
            case "q": g = String(partner[base]!) + marks["flip"]!.above! + marks["underdot"]!.below!
            case "y": g += marks["grave"]!.above!
            case "x": throw ParseError(message: "\(base)\(opsS): x composes only in the glides")
            default: throw ParseError(message: "\(base)\(opsS): bad vowel operator \(op)")
            }
        }
        return g
    }

    /// Script form of a text. Lenient passes ill-formed characters and
    /// formless segments through as typed; tones=false drops tone digits.
    static func render(_ text: String, strict: Bool = true, tones: Bool = true) throws -> String {
        var out = ""
        for seg in try segments(text, strict: strict) {
            guard case .form(let src, let form, let t) = seg else { out += seg.src; continue }
            do { out += try glyph(form) + (tones ? toneSigns(t) : "") }
            catch { if strict { throw error }; out += src }
        }
        return out
    }

    /// Lenient render, never throws.
    static func lenient(_ text: String, tones: Bool = true) -> String { (try? render(text, strict: false, tones: tones)) ?? text }

    /// The streaming commit rule: everything before the last segment is
    /// final; a last segment that is a form may still grow, so it stays
    /// pending. Returns (committed, pending).
    static func stream(_ buffer: String, renderer: (String) -> String = { lenient($0) }) -> (String, String) {
        let segs = (try? segments(buffer, strict: false)) ?? []
        guard let last = segs.last else { return ("", "") }
        let head = last.isForm ? Array(segs.dropLast()) : segs
        let tail = last.isForm ? last.src : ""
        return (renderer(head.map { $0.src }.joined()), tail)
    }
}
